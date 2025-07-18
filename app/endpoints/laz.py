"""
LAZ/LAS File Processing API
Handles LAZ and LAS point cloud file upload and processing operations.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any, Optional
import os
import shutil
from pathlib import Path
import logging
from datetime import datetime
import subprocess
import json
import tempfile
import asyncio
import osgeo # Add osgeo import

# Import coordinate transformation utilities
import sys
sys.path.append(str(Path(__file__).parent.parent))
from geo_utils import get_image_bounds_from_world_file
from osgeo import osr, ogr

# Import LAZ metadata caching
from services.laz_metadata_cache import get_metadata_cache



# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/laz", tags=["laz"])

# Configuration - Use absolute paths to avoid security issues
BASE_DIR = Path(__file__).parent.parent.parent  # Go up to project root
LAZ_INPUT_DIR = BASE_DIR / "input" / "LAZ"
LAZ_OUTPUT_DIR = BASE_DIR / "output" / "LAZ"
LAZ_INPUT_DIR.mkdir(parents=True, exist_ok=True)
LAZ_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _create_laz_metadata_file(file_name: str, response_data: Dict[str, Any], source_crs_info: str = None, ndvi_enabled: bool = False) -> bool:
    """Create metadata.txt file for LAZ region with coordinate information.
    
    Args:
        file_name: Name of the LAZ file
        response_data: Response data containing bounds and center
        source_crs_info: Source CRS information from PDAL
        ndvi_enabled: Whether NDVI processing is enabled for this region
        
    Returns:
        True if metadata file was created successfully, False otherwise
    """
    try:
        from datetime import datetime
        
        # Create region name from file name (remove extension)
        region_name = Path(file_name).stem
        
        # Create output directory
        output_dir = BASE_DIR / "output" / region_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract coordinate information
        bounds = response_data.get("bounds", {})
        center = response_data.get("center", {})
        debug_info = response_data.get("_debug_info", {})
        
        # Create metadata content
        metadata_content = f"""# LAZ Region Metadata
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Source: LAZ file coordinate extraction

Region Name: {region_name}
Source: LAZ
File Path: {file_name}

# Coordinate Information (WGS84 - EPSG:4326)
Center Latitude: {center.get('lat', 'N/A')}
Center Longitude: {center.get('lng', 'N/A')}

# Bounds Information (WGS84 - EPSG:4326)
North Bound: {bounds.get('max_lat', 'N/A')}
South Bound: {bounds.get('min_lat', 'N/A')}
East Bound: {bounds.get('max_lng', 'N/A')}
West Bound: {bounds.get('min_lng', 'N/A')}

# Source CRS Information
Source CRS: {source_crs_info or debug_info.get('source_crs_wkt', 'N/A')}

# Native Bounds (Original CRS)
Native Bounds: {debug_info.get('native_bounds', 'N/A')}

# Processing Information
NDVI Enabled: {str(ndvi_enabled).lower()}
PDAL Command: {debug_info.get('pdal_command', 'N/A')}
Extraction Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Write metadata file
        metadata_path = output_dir / "metadata.txt"
        with open(metadata_path, 'w') as f:
            f.write(metadata_content)
        
        logger.info(f"Created LAZ metadata file: {metadata_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create LAZ metadata file for {file_name}: {e}")
        return False


def get_crs_from_pdal_info(pdal_data: Dict[str, Any], file_path_logging: str = "") -> Optional[osr.SpatialReference]:
    """
    Extracts and creates an OSR SpatialReference object from PDAL info data.
    Tries various common locations for CRS information within the PDAL JSON output.
    """
    srs = osr.SpatialReference()
    crs_found = False
    context_log = f"for file {file_path_logging} " if file_path_logging else ""

    # Option 1: Try 'comp_spatialreference' from metadata (often EPSG:XXXX or WKT)
    metadata = pdal_data.get('metadata', {})
    if 'comp_spatialreference' in metadata:
        comp_srs_str = metadata['comp_spatialreference']
        if comp_srs_str:
            logger.debug(f"Attempting to import CRS {context_log}from metadata.comp_spatialreference: {comp_srs_str}")
            # SetFromUserInput is robust and can handle WKT, EPSG:CODE, PROJ strings etc.
            if srs.SetFromUserInput(comp_srs_str) == ogr.OGRERR_NONE:
                crs_found = True
                logger.info(f"Successfully imported CRS {context_log}from metadata.comp_spatialreference: {comp_srs_str}")
            else:
                logger.warning(f"Failed to import CRS {context_log}from metadata.comp_spatialreference: {comp_srs_str}")

    # Option 2: Try 'srs' dictionary from metadata (common in PDAL output)
    if not crs_found and 'srs' in metadata and isinstance(metadata['srs'], dict):
        srs_dict = metadata['srs']
        srs_wkt = srs_dict.get('wkt')
        srs_proj4 = srs_dict.get('proj4')
        srs_authority = srs_dict.get('authority', '').upper()
        srs_horizontal_code = srs_dict.get('horizontal')

        if srs_wkt:
            logger.debug(f"Attempting to import CRS {context_log}from metadata.srs.wkt")
            if srs.ImportFromWkt(srs_wkt) == ogr.OGRERR_NONE:
                crs_found = True
                logger.info(f"Successfully imported CRS {context_log}from metadata.srs.wkt")
            else:
                logger.warning(f"Failed to import CRS {context_log}from metadata.srs.wkt: {srs_wkt[:100]}...")
        elif srs_authority == 'EPSG' and srs_horizontal_code:
            try:
                epsg_code = int(srs_horizontal_code)
                logger.debug(f"Attempting to import CRS {context_log}from EPSG code: {epsg_code}")
                if srs.ImportFromEPSG(epsg_code) == ogr.OGRERR_NONE:
                    crs_found = True
                    logger.info(f"Successfully imported CRS {context_log}from EPSG code: {epsg_code}")
                else:
                    logger.warning(f"Failed to import CRS {context_log}from EPSG code: {epsg_code}")
            except ValueError:
                logger.warning(f"Invalid EPSG code format {context_log}in metadata.srs.horizontal: {srs_horizontal_code}")
        elif srs_proj4:
            logger.debug(f"Attempting to import CRS {context_log}from metadata.srs.proj4: {srs_proj4}")
            if srs.ImportFromProj4(srs_proj4) == ogr.OGRERR_NONE:
                crs_found = True
                logger.info(f"Successfully imported CRS {context_log}from metadata.srs.proj4: {srs_proj4}")
            else:
                logger.warning(f"Failed to import CRS {context_log}from metadata.srs.proj4: {srs_proj4}")

    # Option 3: Try 'spatialreference' directly from metadata (common in LAZ/LAS files)
    if not crs_found and 'spatialreference' in metadata:
        spatial_ref_str = metadata['spatialreference']
        if spatial_ref_str:
            logger.debug(f"Attempting to import CRS {context_log}from metadata.spatialreference")
            if srs.SetFromUserInput(spatial_ref_str) == ogr.OGRERR_NONE:
                crs_found = True
                logger.info(f"Successfully imported CRS {context_log}from metadata.spatialreference")
            else:
                logger.warning(f"Failed to import CRS {context_log}from metadata.spatialreference: {spatial_ref_str[:100]}...")

    # Option 4: Look in nested metadata.las.srs (less common but possible)
    if not crs_found:
        las_metadata = metadata.get('las', {})
        if isinstance(las_metadata, dict):
            las_srs_metadata = las_metadata.get('srs', {})
            if isinstance(las_srs_metadata, dict):
                srs_wkt_meta = las_srs_metadata.get('spatialreference')
                if srs_wkt_meta and isinstance(srs_wkt_meta, str):
                    logger.debug(f"Attempting to import CRS {context_log}from metadata.las.srs.spatialreference")
                    if srs.ImportFromWkt(srs_wkt_meta) == ogr.OGRERR_NONE:
                        crs_found = True
                        logger.info(f"Successfully imported CRS {context_log}from metadata.las.srs.spatialreference")
                    else:
                        logger.warning(f"Failed to import CRS {context_log}from metadata.las.srs.spatialreference: {srs_wkt_meta[:100]}...")
    
    if crs_found:
        # For GDAL 3+, ensure traditional GIS axis order (Lon/Lat) for geographic CRS.
        # This helps ensure consistency with TransformPoint expecting (x,y) as (lon,lat).
        if srs.IsGeographic() and hasattr(osr, 'OAMS_TRADITIONAL_GIS_ORDER') and int(osgeo.__version__[0]) >= 3:
            srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        logger.info(f"Final CRS determined {context_log}- WKT: {srs.ExportToWkt()[:150]}...")
        return srs
    else:
        logger.warning(f"Could not determine CRS from PDAL metadata {context_log}. Attempting coordinate-based detection...")
        return None


def guess_crs_from_coordinates(minx: float, miny: float, maxx: float, maxy: float, file_path_logging: str = "") -> Optional[osr.SpatialReference]:
    """
    Attempt to guess the CRS based on coordinate ranges when metadata is missing.
    This is a fallback method for LAZ files without proper CRS information.
    """
    context_log = f"for file {file_path_logging} " if file_path_logging else ""
    logger.info(f"Attempting CRS detection {context_log}from coordinate bounds: X({minx}, {maxx}), Y({miny}, {maxy})")
    
    # Calculate coordinate ranges
    x_range = maxx - minx
    y_range = maxy - miny
    
    # Check if coordinates look like geographic (lat/lng)
    if -180 <= minx <= 180 and -180 <= maxx <= 180 and -90 <= miny <= 90 and -90 <= maxy <= 90:
        logger.info(f"Coordinates {context_log}appear to be geographic (WGS84)")
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)  # WGS84
        return srs
    
    # Check for UTM-like coordinates (typically 6-7 digit X, 7-8 digit Y)
    if 100000 <= minx <= 900000 and 100000 <= maxx <= 900000:
        # Determine hemisphere and zone based on Y coordinate and context
        if miny > 1000000:
            # Very large Y coordinates indicate Southern Hemisphere UTM
            logger.info(f"Coordinates {context_log}appear to be UTM Southern hemisphere (Y > 1M)")
            # For southern hemisphere, estimate zone from X coordinate
            center_x = (minx + maxx) / 2
            if 800000 <= center_x <= 900000:
                zone = 18  # Common for eastern Brazil
            elif 700000 <= center_x <= 800000:
                zone = 19
            elif 600000 <= center_x <= 700000:
                zone = 20
            elif 500000 <= center_x <= 600000:
                zone = 21
            else:
                zone = 18  # Default
            epsg_code = 32700 + zone  # UTM South zones
        elif miny >= 0 and miny < 1000000:
            # Northern hemisphere
            logger.info(f"Coordinates {context_log}appear to be UTM Northern hemisphere")
            # Estimate zone from X coordinate
            center_x = (minx + maxx) / 2
            zone = max(1, min(60, int(center_x / 1000000) + 31))
            epsg_code = 32600 + zone  # UTM North zones
        else:
            # Negative Y coordinates - could be southern hemisphere with different datum
            logger.info(f"Coordinates {context_log}may be SIRGAS 2000 UTM (negative Y)")
            # Based on X coordinate range, guess UTM zone for SIRGAS 2000
            center_x = (minx + maxx) / 2
            if 800000 <= center_x <= 900000:
                epsg_code = 31978  # SIRGAS 2000 / UTM zone 18S (common in Brazil)
            elif 700000 <= center_x <= 800000:
                epsg_code = 31979  # SIRGAS 2000 / UTM zone 19S
            elif 600000 <= center_x <= 700000:
                epsg_code = 31980  # SIRGAS 2000 / UTM zone 20S
            elif 500000 <= center_x <= 600000:
                epsg_code = 31981  # SIRGAS 2000 / UTM zone 21S
            else:
                epsg_code = 31978  # Default to zone 18S
        
        try:
            srs = osr.SpatialReference()
            if srs.ImportFromEPSG(epsg_code) == ogr.OGRERR_NONE:
                logger.info(f"Guessed CRS {context_log}as EPSG:{epsg_code}")
                return srs
            else:
                logger.warning(f"Failed to import guessed EPSG:{epsg_code} {context_log}")
        except Exception as e:
            logger.warning(f"Error importing guessed EPSG:{epsg_code} {context_log}: {e}")
    
    # Check for Web Mercator-like coordinates (very large numbers)
    if abs(minx) > 1000000 and abs(maxx) > 1000000 and abs(miny) > 1000000 and abs(maxy) > 1000000:
        logger.info(f"Coordinates {context_log}appear to be Web Mercator (EPSG:3857)")
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3857)  # Web Mercator
        return srs
    
    logger.warning(f"Could not guess CRS {context_log}from coordinate bounds")
    return None


@router.post("/load")
async def load_laz_file(file: UploadFile = File(...)):
    """Load a LAZ/LAS file into input/LAZ and create output directory"""
    try:
        # Ensure LAZ input directory exists
        LAZ_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"LAZ input directory ensured: {LAZ_INPUT_DIR}")
        
        # Validate file type
        allowed_extensions = ['.laz', '.las']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create unique filename if file already exists
        input_path = LAZ_INPUT_DIR / file.filename
        counter = 1
        while input_path.exists():
            name_part = Path(file.filename).stem
            ext_part = Path(file.filename).suffix
            input_path = LAZ_INPUT_DIR / f"{name_part}_{counter}{ext_part}"
            counter += 1

        # Save uploaded file to input/LAZ
        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"LAZ file loaded: {input_path}")
        
        # Create output directory for this file using new unified structure
        file_stem = input_path.stem
        # Use unified structure: output/<file_stem>/lidar/<processing_type>/
        output_dir = BASE_DIR / "output" / file_stem / "lidar"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Output directory created: {output_dir}")
        
        return {
            "message": "File loaded successfully",
            "inputFile": input_path.name,
            "outputDirectory": str(output_dir.relative_to(BASE_DIR)),
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading LAZ file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Loading failed: {str(e)}")

@router.post("/upload-and-process")
async def upload_and_process_laz(
    file: UploadFile = File(...),
    processingType: str = Form("dem"),
    resolution: float = Form(1.0)
):
    """Upload and process a LAZ/LAS file"""
    try:
        # Ensure LAZ input directory exists
        LAZ_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"LAZ input directory ensured: {LAZ_INPUT_DIR}")
        
        # Validate file type
        allowed_extensions = ['.laz', '.las']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create unique filename if file already exists
        upload_path = LAZ_INPUT_DIR / file.filename
        counter = 1
        while upload_path.exists():
            name_part = Path(file.filename).stem
            ext_part = Path(file.filename).suffix
            upload_path = LAZ_INPUT_DIR / f"{name_part}_{counter}{ext_part}"
            counter += 1
        
        # Save uploaded file
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"LAZ file uploaded: {upload_path}")
        
        # Process the file (mock processing for now)
        processed_file = await process_laz_file(
            upload_path, 
            processingType, 
            resolution
        )
        
        return {
            "message": "File uploaded and processed successfully",
            "originalFile": upload_path.name,
            "processedFile": processed_file,
            "processingType": processingType,
            "resolution": resolution,
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing LAZ file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

async def process_laz_file(input_path: Path, processing_type: str, resolution: float) -> str:
    """
    Process LAZ file to generate raster products using unified directory structure
    This is a mock implementation - in production, this would use actual LAZ processing tools
    """
    try:
        # Generate output filename using new naming convention
        output_name = f"{input_path.stem}_{processing_type.upper()}_{resolution}m.tif"
        
        # Use unified directory structure: output/<file_stem>/lidar/<processing_type>/
        file_stem = input_path.stem
        output_dir = BASE_DIR / "output" / file_stem / "lidar" / processing_type.upper()
        output_path = output_dir / output_name
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock processing - in production, this would use:
        # - PDAL for LAZ/LAS processing
        # - GDAL for raster generation
        # - Actual elevation model generation algorithms
        
        logger.info(f"Mock processing LAZ file: {input_path} -> {output_path}")
        logger.info(f"Processing type: {processing_type}, Resolution: {resolution}m")
        
        # Simulate processing time
        import asyncio
        await asyncio.sleep(1)
        
        # Create a mock output file
        output_path.touch()
        
        # In a real implementation, you would:
        # 1. Use PDAL to read and filter point cloud data
        # 2. Generate raster grids based on processing type:
        #    - DEM: Digital Elevation Model from ground points
        #    - DSM: Digital Surface Model from all points
        #    - DTM: Digital Terrain Model from filtered ground points  
        #    - CHM: Canopy Height Model (DSM - DTM)
        # 3. Use GDAL to write the output raster
        
        return output_name
        
    except Exception as e:
        logger.error(f"Error in LAZ processing: {str(e)}")
        raise

@router.get("/files")
async def get_laz_files():
    """Get list of available LAZ files"""
    try:
        files = []
        
        # Get input files
        if LAZ_INPUT_DIR.exists():
            for file_path in LAZ_INPUT_DIR.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.laz', '.las']:
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(LAZ_INPUT_DIR)),
                        "size": file_path.stat().st_size,
                        "type": "source",
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
        
        # Get processed files from unified output directories
        output_base_dir = BASE_DIR / "output"
        if output_base_dir.exists():
            for file_stem_dir in output_base_dir.iterdir():
                if file_stem_dir.is_dir():
                    # Look for lidar subdirectory
                    lidar_dir = file_stem_dir / "lidar"
                    if lidar_dir.exists() and lidar_dir.is_dir():
                        # Recursively find all TIF files in lidar subdirectories
                        for tif_file in lidar_dir.glob("**/*.tif"):
                            if tif_file.is_file():
                                # Calculate relative path from output base
                                relative_path = tif_file.relative_to(output_base_dir)
                                files.append({
                                    "name": tif_file.name,
                                    "path": str(relative_path),
                                    "size": tif_file.stat().st_size,
                                    "type": "processed",
                                    "modified": datetime.fromtimestamp(tif_file.stat().st_mtime).isoformat()
                                })
        
        return sorted(files, key=lambda x: x["modified"], reverse=True)
        
    except Exception as e:
        logger.error(f"Error scanning LAZ directory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scanning files: {str(e)}")

@router.get("/download/{file_path:path}")
async def download_laz_file(file_path: str):
    """Download a LAZ file or processed result"""
    try:
        # Try input directory first
        full_path = LAZ_INPUT_DIR / file_path
        if not full_path.exists():
            # Try unified output directory structure
            output_base_dir = BASE_DIR / "output"
            full_path = output_base_dir / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Ensure the path is absolute and within our allowed directories
        full_path = full_path.resolve()
        
        # Security check - ensure file is within our allowed directories
        input_dir_resolved = LAZ_INPUT_DIR.resolve()
        output_dir_resolved = (BASE_DIR / "output").resolve()
        
        if not (str(full_path).startswith(str(input_dir_resolved)) or 
                str(full_path).startswith(str(output_dir_resolved))):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return FileResponse(
            path=str(full_path),
            filename=full_path.name,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.delete("/files/{file_path:path}")
async def delete_laz_file(file_path: str):
    """Delete a LAZ file"""
    try:
        # Try input directory first
        full_path = LAZ_INPUT_DIR / file_path
        if not full_path.exists():
            # Try unified output directory structure
            output_base_dir = BASE_DIR / "output"
            full_path = output_base_dir / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        full_path.unlink()
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.get("/processing-status/{file_name}")
async def get_processing_status(file_name: str):
    """Get processing status for a LAZ file"""
    try:
        # This would typically track actual processing jobs
        # For now, return a mock status
        return {
            "status": "completed",
            "progress": 100,
            "message": "Processing completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/bounds-wgs84/{file_name:path}")
async def get_laz_bounds_wgs84(file_name: str):
    """
    Get LAZ file bounds and center point in WGS84 (EPSG:4326) coordinates.
    The file_name is relative to the LAZ_INPUT_DIR.
    Creates processing metadata file after successful coordinate extraction.
    """
    try:
        # Use the internal function to get the data
        response_data = await _get_laz_bounds_data_internal(file_name)
        
        # Create metadata file for the LAZ region
        _create_laz_metadata_file(file_name, response_data, response_data.get("_debug_info", {}).get("source_crs_wkt"))
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_laz_bounds_wgs84: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# Helper functions for LAZ file analysis

async def _get_comprehensive_laz_info(file_path: Path) -> Dict[str, Any]:
    """Get comprehensive information about a LAZ file using PDAL"""
    try:
        # Use PDAL info command for comprehensive analysis
        result = subprocess.run([
            'pdal', 'info', '--all', '--stats', str(file_path)
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Parse JSON output from PDAL
            info_data = json.loads(result.stdout)
            
            # Extract key information
            comprehensive_info = {
                "file_size_bytes": file_path.stat().st_size,
                "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2)
            }
            
            # Add PDAL info if available
            if isinstance(info_data, dict):
                comprehensive_info.update(info_data)
            
            return comprehensive_info
        else:
            logger.error(f"PDAL info failed: {result.stderr}")
            # Fallback to basic file info
            return _get_basic_file_stats(file_path)
            
    except subprocess.TimeoutExpired:
        logger.error("PDAL info timed out")
        return {"error": "Analysis timed out", **_get_basic_file_stats(file_path)}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse PDAL JSON output: {str(e)}")
        return {"error": "Failed to parse analysis output", **_get_basic_file_stats(file_path)}
    except Exception as e:
        logger.error(f"Error in comprehensive LAZ analysis: {str(e)}")
        return {"error": f"Analysis failed: {str(e)}", **_get_basic_file_stats(file_path)}

async def _get_laz_bounds(file_path: Path) -> Dict[str, Any]:
    """Get spatial bounds of LAZ file"""
    try:
        result = subprocess.run([
            'pdal', 'info', '--boundary', str(file_path)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            info_data = json.loads(result.stdout)
            
            # Extract bounds from PDAL output
            if 'boundary' in info_data:
                return {"bounds": info_data['boundary']}
            elif 'stats' in info_data:
                # Try to extract from stats
                stats = info_data['stats']
                if isinstance(stats, dict) and 'bbox' in stats:
                    return {"bounds": stats['bbox']}
            
            return {"error": "No boundary information found"}
        else:
            return {"error": f"Failed to get bounds: {result.stderr}"}
            
    except Exception as e:
        logger.error(f"Error getting LAZ bounds: {str(e)}")
        return {"error": f"Failed to get bounds: {str(e)}"}

async def _get_laz_point_info(file_path: Path) -> Dict[str, Any]:
    """Get point count and density information"""
    try:
        result = subprocess.run([
            'pdal', 'info', '--stats', str(file_path)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            info_data = json.loads(result.stdout)
            
            point_info = {}
            
            # Extract point count
            if 'stats' in info_data and 'statistic' in info_data['stats']:
                stats = info_data['stats']['statistic']
                for stat in stats:
                    if stat.get('name') == 'count':
                        point_info['point_count'] = stat.get('count', 0)
                        break
            
            # Calculate density if we have bounds and point count
            if 'point_count' in point_info:
                bounds_info = await _get_laz_bounds(file_path)
                if 'bounds' in bounds_info and not isinstance(bounds_info['bounds'], str):
                    # Calculate area and density (simplified)
                    point_info['has_density_calculation'] = True
            
            return point_info
        else:
            return {"error": f"Failed to get point info: {result.stderr}"}
            
    except Exception as e:
        logger.error(f"Error getting point info: {str(e)}")
        return {"error": f"Failed to get point info: {str(e)}"}

async def _get_laz_classification_stats(file_path: Path) -> Dict[str, Any]:
    """Get point classification statistics"""
    try:
        # Create a PDAL pipeline to get classification stats
        pipeline = {
            "pipeline": [
                str(file_path),
                {
                    "type": "filters.stats",
                    "dimensions": "Classification"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(pipeline, f)
            pipeline_file = f.name
        
        try:
            result = subprocess.run([
                'pdal', 'pipeline', pipeline_file, '--stream'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse classification statistics
                return {"classification_stats": "Analysis completed"}
            else:
                return {"error": f"Classification analysis failed: {result.stderr}"}
                
        finally:
            Path(pipeline_file).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"Error getting classification stats: {str(e)}")
        return {"error": f"Failed to get classification stats: {str(e)}"}

async def _get_laz_crs_info(file_path: Path) -> Dict[str, Any]:
    """Get coordinate reference system information"""
    try:
        result = subprocess.run([
            'pdal', 'info', '--metadata', str(file_path)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            info_data = json.loads(result.stdout)
            
            crs_info = {}
            
            # Extract CRS information from metadata
            if 'metadata' in info_data:
                metadata = info_data['metadata']
                for key, value in metadata.items():
                    if 'srs' in key.lower() or 'crs' in key.lower() or 'proj' in key.lower():
                        crs_info[key] = value
            
            return crs_info if crs_info else {"message": "No CRS information found"}
        else:
            return {"error": f"Failed to get CRS info: {result.stderr}"}
            
    except Exception as e:
        logger.error(f"Error getting CRS info: {str(e)}")
        return {"error": f"Failed to get CRS info: {str(e)}"}

async def _get_laz_elevation_stats(file_path: Path) -> Dict[str, Any]:
    """Get elevation statistics"""
    try:
        # Create pipeline to get Z dimension statistics
        pipeline = {
            "pipeline": [
                str(file_path),
                {
                    "type": "filters.stats",
                    "dimensions": "Z"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(pipeline, f)
            pipeline_file = f.name
        
        try:
            result = subprocess.run([
                'pdal', 'pipeline', pipeline_file
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {"elevation_stats": "Analysis completed"}
            else:
                return {"error": f"Elevation analysis failed: {result.stderr}"}
                
        finally:
            Path(pipeline_file).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"Error getting elevation stats: {str(e)}")
        return {"error": f"Failed to get elevation stats: {str(e)}"}

async def _get_laz_metadata(file_path: Path) -> Dict[str, Any]:
    """Get general file metadata"""
    try:
        result = subprocess.run([
            'pdal', 'info', '--metadata', str(file_path)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            info_data = json.loads(result.stdout)
            
            metadata = {
                "file_info": _get_basic_file_stats(file_path)
            }
            
            if 'metadata' in info_data:
                metadata["pdal_metadata"] = info_data['metadata']
            
            return metadata
        else:
            return {
                "file_info": _get_basic_file_stats(file_path),
                "error": f"Failed to get PDAL metadata: {result.stderr}"
            }
            
    except Exception as e:
        logger.error(f"Error getting metadata: {str(e)}")
        return {
            "file_info": _get_basic_file_stats(file_path),
            "error": f"Failed to get metadata: {str(e)}"
        }

async def _validate_laz_file(file_path: Path) -> Dict[str, Any]:
    """Validate LAZ file integrity"""
    try:
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {}
        }
        
        # Basic file checks
        if not file_path.exists():
            validation["valid"] = False
            validation["errors"].append("File does not exist")
            return validation
        
        if file_path.stat().st_size == 0:
            validation["valid"] = False
            validation["errors"].append("File is empty")
            return validation
        
        validation["checks"]["file_exists"] = True
        validation["checks"]["file_not_empty"] = True
        
        # Check file extension
        if file_path.suffix.lower() not in ['.laz', '.las']:
            validation["warnings"].append("Unexpected file extension")
        else:
            validation["checks"]["valid_extension"] = True
        
        # Try to read file with PDAL
        try:
            result = subprocess.run([
                'pdal', 'info', '--stats', str(file_path)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                validation["checks"]["pdal_readable"] = True
                info_data = json.loads(result.stdout)
                
                # Check if we got valid statistics
                if 'stats' in info_data:
                    validation["checks"]["has_statistics"] = True
                else:
                    validation["warnings"].append("No statistics available")
            else:
                validation["valid"] = False
                validation["errors"].append(f"PDAL cannot read file: {result.stderr}")
                validation["checks"]["pdal_readable"] = False
                
        except subprocess.TimeoutExpired:
            validation["warnings"].append("File validation timed out")
        except json.JSONDecodeError:
            validation["warnings"].append("PDAL output is not valid JSON")
        
        return validation
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation failed: {str(e)}"],
            "warnings": [],
            "checks": {}
        }

async def _get_laz_intensity_stats(file_path: Path) -> Dict[str, Any]:
    """Get intensity value statistics"""
    try:
        pipeline = {
            "pipeline": [
                str(file_path),
                {
                    "type": "filters.stats",
                    "dimensions": "Intensity"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(pipeline, f)
            pipeline_file = f.name
        
        try:
            result = subprocess.run([
                'pdal', 'pipeline', pipeline_file
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {"intensity_stats": "Analysis completed"}
            else:
                return {"error": f"Intensity analysis failed: {result.stderr}"}
                
        finally:
            Path(pipeline_file).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"Error getting intensity stats: {str(e)}")
        return {"error": f"Failed to get intensity stats: {str(e)}"}

async def _get_laz_return_stats(file_path: Path) -> Dict[str, Any]:
    """Get return number statistics"""
    try:
        pipeline = {
            "pipeline": [
                str(file_path),
                {
                    "type": "filters.stats",
                    "dimensions": "ReturnNumber,NumberOfReturns"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(pipeline, f)
            pipeline_file = f.name
        
        try:
            result = subprocess.run([
                'pdal', 'pipeline', pipeline_file
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {"return_stats": "Analysis completed"}
            else:
                return {"error": f"Return analysis failed: {result.stderr}"}
                
        finally:
            Path(pipeline_file).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"Error getting return stats: {str(e)}")
        return {"error": f"Failed to get return stats: {str(e)}"}

async def _get_basic_laz_info(file_path: Path) -> Dict[str, Any]:
    """Get basic LAZ file information"""
    try:
        result = subprocess.run([
            'pdal', 'info', str(file_path)
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            info_data = json.loads(result.stdout)
            
            basic_info = {
                "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2)
            }
            
            # Extract basic information
            if 'filename' in info_data:
                basic_info['filename'] = info_data['filename']
            if 'version' in info_data:
                basic_info['version'] = info_data['version']
            if 'dataformat_id' in info_data:
                basic_info['dataformat_id'] = info_data['dataformat_id']
            
            return basic_info
        else:
            return {
                "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                "error": "Could not analyze with PDAL"
            }
            
    except Exception as e:
        return {
            "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
            "error": f"Analysis failed: {str(e)}"
        }

async def _compare_laz_files(file1_path: Path, file2_path: Path) -> Dict[str, Any]:
    """Compare two LAZ files"""
    try:
        # Get basic info for both files
        info1 = await _get_basic_laz_info(file1_path)
        info2 = await _get_basic_laz_info(file2_path)
        
        comparison = {
            "file1": {
                "name": file1_path.name,
                "info": info1
            },
            "file2": {
                "name": file2_path.name,
                "info": info2
            },
            "differences": [],
            "similarities": []
        }
        
        # Compare file sizes
        size1 = file1_path.stat().st_size
        size2 = file2_path.stat().st_size
        
        if abs(size1 - size2) / max(size1, size2) > 0.1:  # 10% difference
            comparison["differences"].append(f"File size difference: {size1} vs {size2} bytes")
        else:
            comparison["similarities"].append("Similar file sizes")
        
        # Compare other attributes if available
        for key in info1:
            if key in info2 and key != 'error':
                if info1[key] == info2[key]:
                    comparison["similarities"].append(f"Same {key}: {info1[key]}")
                else:
                    comparison["differences"].append(f"Different {key}: {info1[key]} vs {info2[key]}")
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing files: {str(e)}")
        return {"error": f"Comparison failed: {str(e)}"}

async def _get_laz_quality_metrics(file_path: Path) -> Dict[str, Any]:
    """Get data quality metrics"""
    try:
        quality_metrics = {
            "file_integrity": {},
            "data_completeness": {},
            "spatial_quality": {}
        }
        
        # File integrity check
        validation = await _validate_laz_file(file_path)
        quality_metrics["file_integrity"] = {
            "valid": validation.get("valid", False),
            "error_count": len(validation.get("errors", [])),
            "warning_count": len(validation.get("warnings", []))
        }
        
        # Basic file statistics
        file_stats = _get_basic_file_stats(file_path)
        quality_metrics["file_info"] = file_stats
        
        # Try to get point density and coverage metrics
        try:
            result = subprocess.run([
                'pdal', 'info', '--stats', str(file_path)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                info_data = json.loads(result.stdout)
                quality_metrics["has_detailed_stats"] = True
                
                # Add summary metrics
                if 'stats' in info_data:
                    quality_metrics["data_completeness"]["has_statistics"] = True
                else:
                    quality_metrics["data_completeness"]["has_statistics"] = False
            else:
                quality_metrics["has_detailed_stats"] = False
                
        except Exception as e:
            quality_metrics["analysis_error"] = str(e)
        
        return quality_metrics
        
    except Exception as e:
        logger.error(f"Error getting quality metrics: {str(e)}")
        return {"error": f"Failed to get quality metrics: {str(e)}"}

def _get_basic_file_stats(file_path: Path) -> Dict[str, Any]:
    """Get basic file system statistics"""
    try:
        stat = file_path.stat()
        return {
            "file_size_bytes": stat.st_size,
            "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "extension": file_path.suffix.lower()
        }
    except Exception as e:
        logger.error(f"Error getting file stats: {str(e)}")
        return {"error": f"Failed to get file stats: {str(e)}"}

# ============================================================================
# LAZ INFORMATION ENDPOINTS - Comprehensive LAZ File Analysis
# ============================================================================

@router.get("/info")
async def get_laz_file_info(file_path: str):
    """Get comprehensive LAZ file information"""
    try:
        # Convert file path to absolute path
        full_path = LAZ_INPUT_DIR / file_path
        if not full_path.exists():
            # Try output directory
            output_base_dir = BASE_DIR / "output"
            full_path = output_base_dir / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        info = await _get_comprehensive_laz_info(full_path)
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting LAZ file info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Info analysis failed: {str(e)}")

@router.get("/bounds")
async def get_laz_file_bounds(file_path: str):
    """Get LAZ file spatial bounds"""
    try:
        full_path = LAZ_INPUT_DIR / file_path
        if not full_path.exists():
            output_base_dir = BASE_DIR / "output"
            full_path = output_base_dir / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        bounds = await _get_laz_bounds(full_path)
        return bounds
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting LAZ bounds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bounds analysis failed: {str(e)}")

def _transform_bounds_to_wgs84(bounds, src_epsg: int = 31978) -> Dict[str, Any]:
    """Transform LAZ bounds from UTM to WGS84 coordinates"""
    try:
        # Handle different boundary formats from PDAL
        coords = []
        
        if isinstance(bounds, dict):
            if 'coordinates' in bounds and isinstance(bounds['coordinates'], list):
                # GeoJSON-like format
                coords_list = bounds['coordinates']
                if len(coords_list) > 0 and isinstance(coords_list[0], list):
                    coords = coords_list[0]  # Exterior ring
                else:
                    coords = coords_list
            elif isinstance(bounds, list):
                coords = bounds
        elif isinstance(bounds, list):
            coords = bounds
        else:
            logger.error(f"Unrecognized bounds format: {bounds}")
            return {"error": "Unrecognized bounds format"}
        
        if not coords or len(coords) < 4:
            return {"error": "Insufficient coordinate data"}
        
        # Extract min/max coordinates from polygon
        x_coords = [coord[0] for coord in coords if len(coord) >= 2]
        y_coords = [coord[1] for coord in coords if len(coord) >= 2]
        
        if not x_coords or not y_coords:
            return {"error": "Invalid coordinate data"}
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        logger.info(f"Original UTM bounds - X: {min_x} to {max_x}, Y: {min_y} to {max_y}")
        
        # Create coordinate transformation
        source_srs = osr.SpatialReference()
        source_srs.ImportFromEPSG(src_epsg)
        
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(4326)  # WGS84
        
        transform = osr.CoordinateTransformation(source_srs, target_srs)
        
        # Transform corner points
        sw_result = transform.TransformPoint(min_x, min_y)
        ne_result = transform.TransformPoint(max_x, max_y)
        nw_result = transform.TransformPoint(min_x, max_y)
        se_result = transform.TransformPoint(max_x, min_y)
        
        # Extract transformed coordinates
        sw_lon, sw_lat = sw_result[0], sw_result[1]
        ne_lon, ne_lat = ne_result[0], ne_result[1]
        nw_lon, nw_lat = nw_result[0], nw_result[1]
        se_lon, se_lat = se_result[0], se_result[1]
        
        # Calculate final bounds
        final_west = min(sw_lon, nw_lon, se_lon, ne_lon)
        final_east = max(sw_lon, nw_lon, se_lon, ne_lon)
        final_south = min(sw_lat, nw_lat, se_lat, ne_lat)
        final_north = max(sw_lat, nw_lat, se_lat, ne_lat)

        # Calculate center coordinates
        center_lat = (final_north + final_south) / 2
        center_lng = (final_east + final_west) / 2
        
        logger.info(f"Transformed WGS84 bounds - Lat: {final_south} to {final_north}, Lng: {final_west} to {final_east}")
        logger.info(f"Center coordinates: {center_lat}, {center_lng}")
        
        return {
            "bounds": {
                "north": final_north,
                "south": final_south,
                "east": final_east,
                "west": final_west
            },
            "center": {
                "lat": center_lat,
                "lng": center_lng
            },
            "original_epsg": src_epsg,
            "target_epsg": 4326
        }
        
    except Exception as e:
        logger.error(f"Error transforming coordinates: {str(e)}")
        return {"error": f"Coordinate transformation failed: {str(e)}"}

@router.get("/bounds-wgs84")
async def get_laz_file_bounds_wgs84(file_path: str, src_epsg: int = 31978):
    """Get LAZ file spatial bounds transformed to WGS84 coordinates"""
    try:
        # First get the raw bounds
        full_path = LAZ_INPUT_DIR / file_path
        if not full_path.exists():
            output_base_dir = BASE_DIR / "output"
            full_path = output_base_dir / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        bounds_result = await _get_laz_bounds(full_path)
        
        if "error" in bounds_result:
            return bounds_result
        
        if "bounds" not in bounds_result:
            return {"error": "No bounds data found"}
        
        # Transform the bounds to WGS84
        transformed = _transform_bounds_to_wgs84(bounds_result["bounds"], src_epsg)
        
        return transformed
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transformed LAZ bounds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bounds transformation failed: {str(e)}")

@router.get("/debug-coordinates/{file_path:path}")
async def debug_laz_coordinates(file_path: str, src_epsg: int = 31978):
    """Debug endpoint to show coordinate transformation details for LAZ files"""
    try:
        # Find the file
        full_path = LAZ_INPUT_DIR / file_path
        if not full_path.exists():
            output_base_dir = BASE_DIR / "output"
            full_path = output_base_dir / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        debug_info = {
            "file_info": {
                "name": full_path.name,
                "path": str(full_path),
                "size_mb": round(full_path.stat().st_size / (1024 * 1024), 2)
            },
            "coordinate_analysis": {}
        }
        
        # Get raw bounds from PDAL
        logger.info(f"Getting bounds for file: {full_path}")
        bounds_result = await _get_laz_bounds(full_path)
        debug_info["raw_bounds_result"] = bounds_result
        
        if "error" in bounds_result:
            debug_info["coordinate_analysis"]["error"] = bounds_result["error"]
            return debug_info
        
        if "bounds" not in bounds_result:
            debug_info["coordinate_analysis"]["error"] = "No bounds data found"
            return debug_info
        
        raw_bounds = bounds_result["bounds"]
        debug_info["coordinate_analysis"]["raw_bounds"] = raw_bounds
        debug_info["coordinate_analysis"]["raw_bounds_type"] = str(type(raw_bounds))
        
        # Extract coordinates from raw bounds
        coords = []
        if isinstance(raw_bounds, dict):
            if 'coordinates' in raw_bounds and isinstance(raw_bounds['coordinates'], list):
                coords_list = raw_bounds['coordinates']
                if len(coords_list) > 0 and isinstance(coords_list[0], list):
                    coords = coords_list[0]  # Exterior ring
                else:
                    coords = coords_list
                debug_info["coordinate_analysis"]["coordinate_extraction"] = "From GeoJSON-like format"
            elif isinstance(raw_bounds, list):
                coords = raw_bounds
                debug_info["coordinate_analysis"]["coordinate_extraction"] = "From list format"
        elif isinstance(raw_bounds, list):
            coords = raw_bounds
            debug_info["coordinate_analysis"]["coordinate_extraction"] = "Direct list format"
        
        debug_info["coordinate_analysis"]["extracted_coords"] = coords
        debug_info["coordinate_analysis"]["coords_count"] = len(coords) if coords else 0
        
        if not coords or len(coords) < 4:
            debug_info["coordinate_analysis"]["error"] = f"Insufficient coordinate data: {len(coords) if coords else 0} points"
            return debug_info
        
        # Calculate original bounds
        x_coords = [coord[0] for coord in coords if len(coord) >= 2]
        y_coords = [coord[1] for coord in coords if len(coord) >= 2]
        
        if not x_coords or not y_coords:
            debug_info["coordinate_analysis"]["error"] = "Invalid coordinate data"
            return debug_info
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        debug_info["coordinate_analysis"]["original_bounds"] = {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
            "center_x": (min_x + max_x) / 2,
            "center_y": (min_y + max_y) / 2,
            "width": max_x - min_x,
            "height": max_y - min_y,
            "coordinate_system": f"EPSG:{src_epsg}"
        }
        
        # Transform to WGS84
        try:
            source_srs = osr.SpatialReference()
            source_srs.ImportFromEPSG(src_epsg)
            
            target_srs = osr.SpatialReference()
            target_srs.ImportFromEPSG(4326)  # WGS84
            
            transform = osr.CoordinateTransformation(source_srs, target_srs)
            
            # Transform corner points
            sw_result = transform.TransformPoint(min_x, min_y)
            ne_result = transform.TransformPoint(max_x, max_y)
            nw_result = transform.TransformPoint(min_x, max_y)
            se_result = transform.TransformPoint(max_x, min_y)
            center_result = transform.TransformPoint((min_x + max_x) / 2, (min_y + max_y) / 2)
            
            # Extract transformed coordinates
            sw_lon, sw_lat = sw_result[0], sw_result[1]
            ne_lon, ne_lat = ne_result[0], ne_result[1]
            nw_lon, nw_lat = nw_result[0], nw_result[1]
            se_lon, se_lat = se_result[0], se_result[1]
            center_lon, center_lat = center_result[0], center_result[1]
            
            # Calculate final bounds
            final_west = min(sw_lon, nw_lon, se_lon, ne_lon)
            final_east = max(sw_lon, nw_lon, se_lon, ne_lon)
            final_south = min(sw_lat, nw_lat, se_lat, ne_lat)
            final_north = max(sw_lat, nw_lat, se_lat, ne_lat)
            
            debug_info["coordinate_analysis"]["transformed_bounds"] = {
                "corners": {
                    "southwest": {"lat": sw_lat, "lon": sw_lon},
                    "northeast": {"lat": ne_lat, "lon": ne_lon},
                    "northwest": {"lat": nw_lat, "lon": nw_lon},
                    "southeast": {"lat": se_lat, "lon": se_lon}
                },
                "bounding_box": {
                    "north": final_north,
                    "south": final_south,
                    "east": final_east,
                    "west": final_west
                },
                "center": {
                    "lat": center_lat,
                    "lng": center_lon
                },
                "center_calculated": {
                    "lat": (final_north + final_south) / 2,
                    "lng": (final_east + final_west) / 2
                },
                "coordinate_system": "EPSG:4326 (WGS84)"
            }
            
            debug_info["coordinate_analysis"]["transformation_success"] = True
            
        except Exception as transform_error:
            debug_info["coordinate_analysis"]["transformation_error"] = str(transform_error)
            debug_info["coordinate_analysis"]["transformation_success"] = False
        
        return debug_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in coordinate debug: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

@router.get("/debug-tool")
async def serve_debug_tool():
    """Serve the LAZ coordinate debug tool HTML page"""
    from fastapi.responses import FileResponse
    import os
    
    # Get the path to the debug HTML file
    debug_file_path = BASE_DIR / "frontend" / "laz-debug.html"
    
    if not debug_file_path.exists():
        raise HTTPException(status_code=404, detail="Debug tool not found")
    
    return FileResponse(
        path=str(debug_file_path),
        media_type='text/html',
        filename='laz-debug.html'
    )

@router.post("/upload")
async def upload_multiple_laz_files(
    files: List[UploadFile] = File(...),
    ndvi_enabled: bool = Form(False)
):
    """Upload multiple LAZ/LAS files"""
    try:
        # Ensure LAZ input directory exists
        LAZ_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"LAZ input directory ensured: {LAZ_INPUT_DIR}")
        
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        uploaded_files = []
        
        for file in files:
            # Extract just the filename, removing any path components (e.g., "Load_1/file.laz" -> "file.laz")
            clean_filename = Path(file.filename).name
            
            # Validate file type
            allowed_extensions = ['.laz', '.las']
            file_ext = Path(clean_filename).suffix.lower()
            
            if file_ext not in allowed_extensions:
                logger.warning(f"Skipping invalid file type: {clean_filename}")
                continue
            
            # Read file content
            content = await file.read()
            
            if not content:
                logger.warning(f"Skipping empty file: {clean_filename}")
                continue
            
            # Create unique filename if file already exists
            upload_path = LAZ_INPUT_DIR / clean_filename
            counter = 1
            original_stem = Path(clean_filename).stem
            original_suffix = Path(clean_filename).suffix
            
            while upload_path.exists():
                new_name = f"{original_stem}_{counter}{original_suffix}"
                upload_path = LAZ_INPUT_DIR / new_name
                counter += 1
            
            # Save file
            with open(upload_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Uploaded LAZ file: {upload_path}")
            
            # Store NDVI setting in .settings.json file alongside the LAZ file
            settings_file = upload_path.with_suffix('.settings.json')
            settings_data = {
                "ndvi_enabled": ndvi_enabled,
                "upload_timestamp": datetime.now().isoformat(),
                "filename": upload_path.name
            }
            
            try:
                with open(settings_file, 'w') as sf:
                    json.dump(settings_data, sf, indent=2)
                logger.info(f"Created settings file: {settings_file} with NDVI enabled: {ndvi_enabled}")
            except Exception as e:
                logger.warning(f"Failed to create settings file for {upload_path.name}: {e}")
            
            # Create output directory structure
            file_stem = upload_path.stem
            output_dir = BASE_DIR / "output" / file_stem / "lidar"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            uploaded_files.append({
                "inputFile": upload_path.name,
                "outputDirectory": str(output_dir.relative_to(BASE_DIR)),
                "size": len(content)
            })
        
        if not uploaded_files:
            raise HTTPException(status_code=400, detail="No valid LAZ/LAS files were uploaded")
        
        return {
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "files": uploaded_files
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading LAZ files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def _get_laz_bounds_data_internal(file_name: str) -> Dict[str, Any]:
    """Internal function to get LAZ bounds data without JSONResponse wrapper"""
    logger.info(f"Processing LAZ bounds for {file_name}")
    
    # Check for cached metadata first
    try:
        cache = get_metadata_cache()
        cached_metadata = cache.get_cached_metadata(file_name)
        if cached_metadata and not cached_metadata.get("error"):
            logger.info(f"Using cached LAZ metadata for {file_name}")
            
            # Convert cached format to response format
            center = cached_metadata.get("center", {})
            bounds = cached_metadata.get("bounds", {})
            
            response_data = {
                "bounds": {
                    "min_lng": bounds.get("west", 0),
                    "min_lat": bounds.get("south", 0),
                    "max_lng": bounds.get("east", 0),
                    "max_lat": bounds.get("north", 0),
                },
                "center": {
                    "lat": center.get("lat", 0),
                    "lng": center.get("lng", 0)
                },
                "file_name": file_name,
                "_cached": True  # Indicate this was from cache
            }
            
            return response_data
            
    except Exception as cache_error:
        logger.warning(f"Error checking cache for {file_name}: {cache_error}")
    
    full_file_path = (LAZ_INPUT_DIR / file_name).resolve()
    pdal_output_str = "" # Initialize for potential use in error logging

    if not full_file_path.is_file():
        error_msg = f"LAZ file not found: {file_name}"
        logger.error(f"LAZ file not found for WGS84 bounds: {full_file_path}")
        raise HTTPException(status_code=404, detail=error_msg)

    try:
        pdal_command = ['pdal', 'info', '--all', '--stats', str(full_file_path)]
        logger.info(f"Executing PDAL command for WGS84 bounds: {' '.join(pdal_command)}")
        
        process = await asyncio.create_subprocess_exec(
            *pdal_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            err_msg = stderr.decode().strip() if stderr else "Unknown PDAL error"
            logger.error(f"PDAL info command failed for {full_file_path}. Return code: {process.returncode}. Error: {err_msg}")
            raise HTTPException(status_code=500, detail=f"PDAL analysis failed: {err_msg}")

        pdal_output_str = stdout.decode()
        if not pdal_output_str.strip(): # Check if output is empty or just whitespace
            logger.error(f"PDAL info command returned empty output for {full_file_path}.")
            raise HTTPException(status_code=500, detail="PDAL analysis returned empty output.")
            
        pdal_data = json.loads(pdal_output_str)

        native_bbox = None
        try:
            # Try extracting bounds from multiple possible locations in PDAL output
            if ('stats' in pdal_data and isinstance(pdal_data['stats'], dict) and 
                'bbox' in pdal_data['stats'] and isinstance(pdal_data['stats']['bbox'], dict) and 
                'native' in pdal_data['stats']['bbox'] and isinstance(pdal_data['stats']['bbox']['native'], dict) and 
                'bbox' in pdal_data['stats']['bbox']['native']):
                native_bbox = pdal_data['stats']['bbox']['native']['bbox']
                logger.debug(f"Extracted bounds from stats.bbox.native.bbox for {full_file_path}")
            elif ('metadata' in pdal_data and isinstance(pdal_data['metadata'], dict)):
                # Try to extract from metadata section
                metadata = pdal_data['metadata']
                if all(k in metadata for k in ['minx', 'miny', 'maxx', 'maxy']):
                    native_bbox = {
                        'minx': metadata['minx'],
                        'miny': metadata['miny'], 
                        'maxx': metadata['maxx'],
                        'maxy': metadata['maxy']
                    }
                    logger.debug(f"Extracted bounds from metadata for {full_file_path}")
            elif ('summary' in pdal_data and isinstance(pdal_data['summary'], dict) and 
                  'bounds' in pdal_data['summary'] and isinstance(pdal_data['summary']['bounds'], dict) and 
                  'native' in pdal_data['summary']['bounds']):
                 native_bbox = pdal_data['summary']['bounds']['native']
                 logger.debug(f"Extracted bounds from summary.bounds.native for {full_file_path}")

            if not isinstance(native_bbox, dict) or not all(k in native_bbox for k in ['minx', 'miny', 'maxx', 'maxy']):
                logger.error(f"Could not extract valid native bounding box from PDAL info for {full_file_path}. Available keys in PDAL data: {list(pdal_data.keys())}")
                raise HTTPException(status_code=500, detail="Could not extract native bounding box from LAZ file.")
        except KeyError as e:
            logger.error(f"KeyError while extracting native bounding box for {full_file_path}: {e}. Available keys in PDAL data: {list(pdal_data.keys())}")
            raise HTTPException(status_code=500, detail=f"Error parsing native bounds: {e}")

        minx, miny, maxx, maxy = native_bbox['minx'], native_bbox['miny'], native_bbox['maxx'], native_bbox['maxy']

        source_srs = get_crs_from_pdal_info(pdal_data, file_path_logging=str(full_file_path))
        if source_srs is None:
            logger.warning(f"CRS metadata missing for {full_file_path}. Attempting coordinate-based detection...")
            source_srs = guess_crs_from_coordinates(minx, miny, maxx, maxy, file_path_logging=str(full_file_path))
            
            if source_srs is None:
                logger.error(f"Could not determine or guess source CRS for LAZ file: {full_file_path}")
                raise HTTPException(status_code=500, detail="Could not determine source CRS of LAZ file. Please ensure the file has proper spatial reference information.")
            else:
                logger.info(f"Successfully guessed CRS for {full_file_path}")
        
        source_srs_wkt = source_srs.ExportToWkt()
        logger.info(f"Source CRS for {full_file_path}: {source_srs_wkt}")

        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(4326) # WGS84
        if hasattr(osr, 'OAMS_TRADITIONAL_GIS_ORDER') and int(osgeo.__version__[0]) >= 3:
            target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        transform = osr.CoordinateTransformation(source_srs, target_srs)
        if not transform: # Should not happen if SRS objects are valid
             logger.error(f"Failed to create coordinate transformation from {source_srs.GetName()} to WGS84 for {full_file_path}.")
             raise HTTPException(status_code=500, detail="Failed to create coordinate transformation.")

        wgs84_min_lon, wgs84_min_lat, _ = transform.TransformPoint(minx, miny)
        wgs84_max_lon, wgs84_max_lat, _ = transform.TransformPoint(maxx, maxy)
        
        final_min_lon = min(wgs84_min_lon, wgs84_max_lon)
        final_max_lon = max(wgs84_min_lon, wgs84_max_lon)
        final_min_lat = min(wgs84_min_lat, wgs84_max_lat)
        final_max_lat = max(wgs84_min_lat, wgs84_max_lat)

        center_lon = (final_min_lon + final_max_lon) / 2
        center_lat = (final_min_lat + final_max_lat) / 2

        response_data = {
            "bounds": {
                "min_lng": final_min_lon, "min_lat": final_min_lat,
                "max_lng": final_max_lon, "max_lat": final_max_lat,
            },
            "center": {"lat": center_lat, "lng": center_lon},
            "file_name": file_name,
            "_debug_info": { # Adding debug info, prefixed with underscore
                "source_crs_wkt": source_srs_wkt,
                "native_bounds": native_bbox,
                "pdal_command": ' '.join(pdal_command)
            }
        }
        
        logger.info(f"Successfully calculated WGS84 bounds for {full_file_path}: center {response_data['center']}")
        
        # Cache the metadata for future use
        try:
            cache = get_metadata_cache()
            metadata_for_cache = {
                "center": response_data["center"],
                "bounds": {
                    "north": final_max_lat,
                    "south": final_min_lat,
                    "east": final_max_lon,
                    "west": final_min_lon
                },
                "source_epsg": getattr(source_srs, 'GetAuthorityCode', lambda x: None)('PROJCS') or 
                              getattr(source_srs, 'GetAuthorityCode', lambda x: None)('GEOGCS') or 
                              "Unknown"
            }
            
            cache_success = cache.cache_metadata(file_name, metadata_for_cache)
            if cache_success:
                logger.info(f"Successfully cached LAZ metadata for {file_name}")
            else:
                logger.warning(f"Failed to cache LAZ metadata for {file_name}")
                
        except Exception as cache_error:
            logger.warning(f"Error caching LAZ metadata for {file_name}: {cache_error}")
        
        return response_data

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse PDAL output: {e}"
        logger.error(f"JSONDecodeError processing PDAL output for {full_file_path}: {e}. Output: {pdal_output_str[:1000]}") # Log more of the output
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        logger.exception(f"Unexpected error getting WGS84 bounds for {full_file_path}: {e}")
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/generate-metadata")
async def generate_laz_metadata(
    region_name: str = Form(...),
    file_name: str = Form(...),
    ndvi_enabled: bool = Form(False)
):
    """Generate metadata.txt file for a LAZ region after raster processing is complete"""
    try:
        logger.info(f"Generating metadata for region: {region_name}, file: {file_name}")
        
        # Try to read NDVI setting from stored settings file first
        laz_file_path = LAZ_INPUT_DIR / file_name
        settings_file = laz_file_path.with_suffix('.settings.json')
        
        final_ndvi_enabled = ndvi_enabled  # Default to form parameter
        
        if settings_file.exists():
            try:
                import json
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    stored_ndvi = settings.get('ndvi_enabled', False)
                    final_ndvi_enabled = stored_ndvi
                    logger.info(f"Retrieved stored NDVI setting: {stored_ndvi} for {file_name}")
            except Exception as e:
                logger.warning(f"Could not read settings file for {file_name}: {e}")
        else:
            logger.info(f"No settings file found for {file_name}, using form parameter: {ndvi_enabled}")
        
        logger.info(f"Final NDVI enabled setting: {final_ndvi_enabled}")
        
        # Get LAZ file bounds and coordinates using internal function
        response_data = await _get_laz_bounds_data_internal(file_name)
        
        if not response_data:
            raise HTTPException(status_code=500, detail="Failed to get LAZ coordinates")
        
        # Create metadata file
        success = _create_laz_metadata_file(file_name, response_data, response_data.get("_debug_info", {}).get("source_crs_wkt"), final_ndvi_enabled)
        
        if success:
            # Get the metadata file path for response
            region_output_dir = BASE_DIR / "output" / region_name
            metadata_path = region_output_dir / "metadata.txt"
            
            # 🛰️ SENTINEL-2 ACQUISITION INTEGRATION
            # After successful metadata creation, conditionally acquire Sentinel-2 imagery based on NDVI setting
            sentinel2_result = None
            
            if final_ndvi_enabled:
                logger.info(f"🛰️ NDVI is enabled - Starting automatic Sentinel-2 acquisition for region: {region_name}")
                try:
                    # Extract coordinates from LAZ bounds
                    bounds = response_data.get("bounds", {})
                    center = response_data.get("center", {})
                    
                    if center.get("lat") and center.get("lng"):
                        # Import satellite service dependencies
                        from ..api.satellite_service import SatelliteService
                        from datetime import datetime, timedelta
                        
                        # Create satellite service instance
                        satellite_service = SatelliteService()
                        
                        # Calculate date range (last 2 years for better scene availability)
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=730)  # 2 years back
                        
                        # Prepare Sentinel-2 request
                        satellite_request = {
                            "lat": center["lat"],
                            "lng": center["lng"], 
                            "buffer_km": 12.5,  # 12.5km buffer around center point
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "end_date": end_date.strftime("%Y-%m-%d"),
                            "bands": ["B04", "B08"],  # Red and NIR bands
                            "region_name": region_name,
                            "cloud_cover_max": 30
                        }
                        
                        logger.info(f"🛰️ Sentinel-2 request: center=({center['lat']:.6f}, {center['lng']:.6f}), buffer=5km")
                        
                        # Extract the WGS84 bounds for Sentinel-2 request
                        laz_wgs84_bounds_dict = response_data.get("bounds", {}) # This is {"min_lng": ..., "min_lat": ..., ...}

                        from app.data_acquisition.utils.coordinates import BoundingBox # Ensure import
                        laz_bbox_obj = BoundingBox(
                            north=laz_wgs84_bounds_dict.get("max_lat"),
                            south=laz_wgs84_bounds_dict.get("min_lat"),
                            east=laz_wgs84_bounds_dict.get("max_lng"),
                            west=laz_wgs84_bounds_dict.get("min_lng")
                        )

                        if not all([laz_bbox_obj.north, laz_bbox_obj.south, laz_bbox_obj.east, laz_bbox_obj.west]):
                            logger.error(f"⚠️ Could not extract valid WGS84 bounding box from LAZ metadata for Sentinel-2. Data: {laz_wgs84_bounds_dict}")
                            raise ValueError("Invalid WGS84 bounding box extracted from LAZ metadata.")

                        laz_area_sq_km = laz_bbox_obj.get_area_sq_km()
                        MAX_RECOMMENDED_S2_AREA_SQ_KM = 625.0 # approx 25km x 25km

                        if laz_area_sq_km > MAX_RECOMMENDED_S2_AREA_SQ_KM:
                            logger.warning(f"LAZ file {file_name} has a large bounding box ({laz_area_sq_km:.2f} sq km), which exceeds the recommended max area of {MAX_RECOMMENDED_S2_AREA_SQ_KM:.2f} sq km for Sentinel-2 acquisition. Proceeding with full LAZ extent.")

                        sentinel2_request_bbox_dict = {
                            "north": laz_bbox_obj.north,
                            "south": laz_bbox_obj.south,
                            "east": laz_bbox_obj.east,
                            "west": laz_bbox_obj.west
                        }
                        logger.info(f"🛰️ Sentinel-2 request (using LAZ BBox): North={laz_bbox_obj.north:.4f}, South={laz_bbox_obj.south:.4f}, East={laz_bbox_obj.east:.4f}, West={laz_bbox_obj.west:.4f}")

                        # Download Sentinel-2 data with LAZ bounding box
                        sentinel2_result = await satellite_service.download_sentinel2_data(
                            bounding_box=sentinel2_request_bbox_dict, # Pass the LAZ BBox
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            bands=satellite_request.get("bands", ["B04", "B08"]), # Use bands from previous dict or default
                            cloud_cover_max=satellite_request.get("cloud_cover_max", 30), # Use cloud cover from previous dict or default
                            region_name=region_name
                        )
                        
                        if sentinel2_result and sentinel2_result.get("success"):
                            logger.info(f"✅ Sentinel-2 acquisition completed successfully")
                            
                            # Auto-convert to PNG if we have a region name
                            try:
                                conversion_result = await satellite_service.convert_sentinel2_images(region_name)
                                if conversion_result and conversion_result.get("success"):
                                    logger.info(f"✅ Sentinel-2 PNG conversion completed")
                                else:
                                    logger.warning(f"⚠️ Sentinel-2 PNG conversion failed: {conversion_result}")
                            except Exception as conv_error:
                                logger.warning(f"⚠️ Sentinel-2 PNG conversion error: {conv_error}")
                                # Don't fail the entire process for conversion errors
                            
                        else:
                            logger.warning(f"⚠️ Sentinel-2 acquisition failed: {sentinel2_result}")
                            
                    else:
                        logger.warning(f"⚠️ No valid coordinates found for Sentinel-2 acquisition")
                        sentinel2_result = {"success": False, "error": "No valid coordinates found"}
                        
                except Exception as satellite_error:
                    logger.error(f"❌ Sentinel-2 acquisition error: {satellite_error}")
                    # Don't fail the metadata generation for satellite acquisition errors
                    sentinel2_result = {"success": False, "error": str(satellite_error)}
            else:
                logger.info(f"🚫 NDVI is disabled - Skipping Sentinel-2 acquisition for region: {region_name}")
                sentinel2_result = {"success": False, "skipped": True, "reason": "NDVI disabled"}
            
            # Return comprehensive response including satellite acquisition status
            response = {
                "message": "Metadata file generated successfully",
                "region": region_name,
                "file": file_name,
                "metadata_path": str(metadata_path.relative_to(BASE_DIR)),
                "coordinates": {
                    "bounds_wgs84": response_data.get("bounds"),
                    "center_wgs84": response_data.get("center"),
                    "source_crs": response_data.get("_debug_info", {}).get("source_crs_wkt")
                },
                "sentinel2_acquisition": {
                    "attempted": True,
                    "success": sentinel2_result.get("success", False) if sentinel2_result else False,
                    "result": sentinel2_result
                }
            }
            
            return response
        else:
            raise HTTPException(status_code=500, detail="Failed to create metadata file")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating LAZ metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metadata generation failed: {str(e)}")

@router.post("/process-all-rasters")
async def process_all_laz_rasters(
    region_name: str = Form(...),
    file_name: str = Form(...),
    display_region_name: str = Form(None)
):
    """
    Process all raster products for a LAZ region using the unified processing system
    
    Args:
        region_name: Name of the region (e.g. "FoxIsland")
        file_name: Name of the LAZ file (e.g. "FoxIsland.laz")
        
    Returns:
        Processing results for all raster products
    """
    try:
        logger.info(f"🚀 Processing all rasters for LAZ region: {region_name}, file: {file_name}")
        
        # Build the path to the elevation TIFF that should have been created from the LAZ
        # Expected structure: output/<region>/lidar/DTM/filled/<file_stem>_DTM_<resolution>m_csf<csf_res>m_filled.tif
        file_stem = Path(file_name).stem
        dtm_tiff_path = BASE_DIR / "output" / region_name / "lidar" / "DTM" / "filled" / f"{file_stem}_DTM_1.0m_csf1.0m_filled.tif"
        
        if not dtm_tiff_path.exists():
            # Try alternative naming conventions and locations
            alt_paths = [
                # Try different resolution patterns
                BASE_DIR / "output" / region_name / "lidar" / "DTM" / "filled" / f"{file_stem}_DTM_1.0m_csf1.0m_filled.tif",
                BASE_DIR / "output" / region_name / "lidar" / "DTM" / "raw" / f"{file_stem}_DTM_1.0m_csf1.0m_raw.tif",
                # Try any DTM file in the DTM directories
                *list((BASE_DIR / "output" / region_name / "lidar" / "DTM" / "filled").glob("*_DTM_*.tif")),
                *list((BASE_DIR / "output" / region_name / "lidar" / "DTM" / "raw").glob("*_DTM_*.tif")),
                # Legacy patterns
                BASE_DIR / "output" / region_name / "lidar" / "DTM" / f"{region_name}_DTM.tiff",
                BASE_DIR / "output" / region_name / "lidar" / f"{region_name}_DTM.tiff",
                BASE_DIR / "output" / region_name / f"{region_name}_DTM.tiff",
                BASE_DIR / "input" / region_name / "lidar" / f"{region_name}_DTM.tiff"
            ]
            
            for alt_path in alt_paths:
                if alt_path.exists():
                    dtm_tiff_path = alt_path
                    break
            else:
                raise HTTPException(
                    status_code=404, 
                    detail=f"DTM TIFF not found for region {region_name}. Please generate DTM first."
                )
        
        logger.info(f"Using DTM TIFF: {dtm_tiff_path}")
        
        # Import the unified processing function
        from app.processing.tiff_processing import process_all_raster_products
        
        # Create a progress callback for WebSocket updates (optional)
        async def progress_callback(progress_data):
            # This could be enhanced to send WebSocket updates to the frontend
            logger.info(f"Processing progress: {progress_data}")
        
        # Create a simple request object with region name to ensure proper output folder structure
        class SimpleRequest:
            def __init__(self, region_name, display_region_name=None):
                self.region_name = region_name
                self.display_region_name = display_region_name
        
        request_obj = SimpleRequest(region_name, display_region_name)
        
        # Process all raster products
        processing_results = await process_all_raster_products(
            str(dtm_tiff_path), 
            progress_callback=progress_callback,
            request=request_obj
        )
        
        logger.info(f"✅ Completed processing all rasters for {region_name}")
        
        return {
            "success": True,
            "region_name": region_name,
            "file_name": file_name,
            "dtm_tiff_path": str(dtm_tiff_path),
            "processing_results": processing_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing all LAZ rasters for {region_name}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process rasters: {str(e)}"
        )
