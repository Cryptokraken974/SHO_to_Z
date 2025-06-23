"""
LAZ Density Processing API Endpoints
Provides REST API for density analysis of loaded LAZ files
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging

from ..processing.laz_density_service import LAZDensityService, process_all_loaded_laz_density
from ..processing.laz_classifier import find_loaded_laz_files
from ..processing.raster_cleaning import RasterCleaner, clean_rasters_with_mask

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/density", tags=["density"])

class DensityProcessingRequest(BaseModel):
    resolution: Optional[float] = 1.0
    mask_threshold: Optional[float] = 2.0
    generate_mask: Optional[bool] = True
    search_directory: Optional[str] = "input"
    output_directory: Optional[str] = "output"

class SingleDensityRequest(BaseModel):
    laz_file_path: str
    region_name: Optional[str] = None
    resolution: Optional[float] = 1.0
    mask_threshold: Optional[float] = 2.0
    generate_mask: Optional[bool] = True

class RasterCleaningRequest(BaseModel):
    """Request model for raster cleaning"""
    region_directory: str = Field(..., description="Path to region directory containing rasters")
    mask_file_path: str = Field(..., description="Path to binary mask file")
    raster_types: Optional[List[str]] = Field(None, description="List of raster types to clean (None = all)")
    method: str = Field("auto", description="Cleaning method: 'auto', 'python', or 'gdal'")

class SingleRasterCleaningRequest(BaseModel):
    """Request model for single raster cleaning"""
    raster_file_path: str = Field(..., description="Path to raster file to clean")
    mask_file_path: str = Field(..., description="Path to binary mask file") 
    output_file_path: str = Field(..., description="Path for cleaned output raster")
    method: str = Field("auto", description="Cleaning method: 'auto', 'python', or 'gdal'")

@router.get("/check-loaded-laz")
async def check_loaded_laz_files():
    """
    Check for loaded LAZ files in the system
    Returns list of loaded LAZ files found
    """
    try:
        print(f"\n🔍 API: Checking for loaded LAZ files...")
        
        loaded_files = find_loaded_laz_files()
        
        return {
            "success": True,
            "loaded_files_count": len(loaded_files),
            "loaded_files": loaded_files,
            "message": f"Found {len(loaded_files)} loaded LAZ files"
        }
        
    except Exception as e:
        error_msg = f"Failed to check loaded LAZ files: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/check-requirements")
async def check_density_requirements():
    """
    Check system requirements for density processing
    """
    try:
        print(f"\n🔧 API: Checking density processing requirements...")
        
        service = LAZDensityService()
        requirements = service.check_density_requirements()
        
        if requirements["system_ready"]:
            status_code = 200
            message = "System ready for density processing"
        else:
            status_code = 200  # Don't error, just inform
            message = f"Missing tools: {', '.join(requirements['missing_tools'])}"
        
        return {
            "success": requirements["system_ready"],
            "requirements": requirements,
            "message": message
        }
        
    except Exception as e:
        error_msg = f"Failed to check requirements: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/process-all")
async def process_all_density(
    background_tasks: BackgroundTasks,
    request: DensityProcessingRequest = DensityProcessingRequest()
):
    """
    Process density analysis for all loaded LAZ files
    Runs in background for large processing jobs
    """
    try:
        print(f"\n🚀 API: Starting density processing for all loaded LAZ files...")
        print(f"   Resolution: {request.resolution}m")
        print(f"   Mask threshold: {request.mask_threshold} points/cell")
        print(f"   Generate mask: {request.generate_mask}")
        print(f"   Search directory: {request.search_directory}")
        print(f"   Output directory: {request.output_directory}")
        
        # Check requirements first
        service = LAZDensityService(
            resolution=request.resolution,
            mask_threshold=request.mask_threshold
        )
        requirements = service.check_density_requirements()
        
        if not requirements["system_ready"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required tools: {', '.join(requirements['missing_tools'])}"
            )
        
        # Check for loaded files first
        loaded_files = find_loaded_laz_files(request.search_directory)
        
        if not loaded_files:
            return {
                "success": True,
                "message": "No loaded LAZ files found to process",
                "files_found": 0,
                "files_processed": 0
            }
        
        # For small numbers of files, process synchronously
        if len(loaded_files) <= 3:
            print(f"   📊 Processing {len(loaded_files)} files synchronously...")
            
            result = service.process_loaded_laz_files(
                search_directory=request.search_directory,
                output_base_dir=request.output_directory
            )
            
            return {
                "success": result["success"],
                "message": f"Processed {result['successful_count']} of {result['files_found']} files",
                "files_found": result["files_found"],
                "files_processed": result["files_processed"],
                "successful_count": result["successful_count"],
                "failed_count": result["failed_count"],
                "results": result["results"],
                "processing_mode": "synchronous"
            }
        else:
            # For larger numbers, use background processing
            print(f"   🔄 Processing {len(loaded_files)} files in background...")
            
            background_tasks.add_task(
                _background_density_processing,
                request.resolution,
                request.mask_threshold,
                request.search_directory,
                request.output_directory
            )
            
            return {
                "success": True,
                "message": f"Started background processing of {len(loaded_files)} LAZ files",
                "files_found": len(loaded_files),
                "processing_mode": "background",
                "note": "Processing continues in background. Check logs for progress."
            }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to start density processing: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/process-single")
async def process_single_density(request: SingleDensityRequest):
    """
    Process density analysis for a single LAZ file
    """
    try:
        print(f"\n🔄 API: Processing single LAZ file density...")
        print(f"   File: {request.laz_file_path}")
        print(f"   Region: {request.region_name}")
        print(f"   Resolution: {request.resolution}m")
        
        # Check requirements
        service = LAZDensityService(
            resolution=request.resolution,
            mask_threshold=request.mask_threshold
        )
        requirements = service.check_density_requirements()
        
        if not requirements["system_ready"]:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required tools: {', '.join(requirements['missing_tools'])}"
            )
        
        # Extract region name if not provided
        if not request.region_name:
            from pathlib import Path
            request.region_name = Path(request.laz_file_path).stem
        
        # Process the file
        result = service.process_single_laz(
            laz_file_path=request.laz_file_path,
            output_base_dir="output",
            region_name=request.region_name
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Density analysis completed for {request.region_name}",
                "result": result
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Density processing failed: {result.get('error', 'Unknown error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to process single LAZ density: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/analyze")
async def analyze_single_density(request: SingleDensityRequest):
    """
    Analyze density and generate binary mask for a single LAZ file
    This is the main endpoint for density analysis with mask generation
    """
    try:
        print(f"\n🔍 API: Analyzing single LAZ file density...")
        print(f"   File: {request.laz_file_path}")
        print(f"   Region: {request.region_name}")
        print(f"   Resolution: {request.resolution}m")
        print(f"   Mask threshold: {request.mask_threshold} points/cell")
        print(f"   Generate mask: {request.generate_mask}")
        
        # Import the direct analyzer for more control
        from ..processing.density_analysis import DensityAnalyzer
        
        # Create analyzer with specified parameters
        analyzer = DensityAnalyzer(
            resolution=request.resolution,
            mask_threshold=request.mask_threshold
        )
        
        # Extract region name if not provided
        if not request.region_name:
            from pathlib import Path
            request.region_name = Path(request.laz_file_path).stem
        
        # Determine output directory
        output_dir = f"output/{request.region_name}/lidar"
        
        # Run analysis
        result = analyzer.generate_density_raster(
            laz_file_path=request.laz_file_path,
            output_dir=output_dir,
            region_name=request.region_name,
            generate_mask=request.generate_mask
        )
        
        if result["success"]:
            # Copy to gallery if successful
            if request.generate_mask and result.get('mask_results'):
                try:
                    from pathlib import Path
                    import shutil
                    
                    region_output_dir = Path(output_dir)
                    png_outputs_dir = region_output_dir / "png_outputs"
                    png_outputs_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Copy density PNG
                    if result.get('png_path'):
                        source_png = Path(result['png_path'])
                        if source_png.exists():
                            dest_png = png_outputs_dir / "Density.png"
                            shutil.copy2(source_png, dest_png)
                    
                    # Copy mask PNG
                    mask_results = result['mask_results']
                    if mask_results.get('png_path'):
                        source_mask = Path(mask_results['png_path'])
                        if source_mask.exists():
                            dest_mask = png_outputs_dir / "ValidMask.png"
                            shutil.copy2(source_mask, dest_mask)
                            
                except Exception as e:
                    print(f"⚠️ Could not copy files to gallery: {e}")
            
            return {
                "success": True,
                "message": f"Density analysis completed for {request.region_name}",
                "tiff_path": result.get("tiff_path"),
                "png_path": result.get("png_path"),
                "metadata_path": result.get("metadata_path"),
                "metadata": result.get("metadata"),
                "mask_results": result.get("mask_results", {}),
                "region_name": result.get("region_name")
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Density analysis failed: {result.get('error', 'Unknown error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to analyze LAZ density: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/status")
async def get_density_status():
    """
    Get status of density processing capabilities
    """
    try:
        service = LAZDensityService()
        requirements = service.check_density_requirements()
        loaded_files = find_loaded_laz_files()
        
        return {
            "success": True,
            "system_ready": requirements["system_ready"],
            "requirements": requirements,
            "loaded_files_count": len(loaded_files),
            "loaded_files": [f["file_name"] for f in loaded_files],
            "message": "Density processing status retrieved"
        }
        
    except Exception as e:
        error_msg = f"Failed to get density status: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/clean-rasters")
async def clean_region_rasters(request: RasterCleaningRequest):
    """
    Clean all rasters in a region using a binary mask
    Removes artifacts and edge bands from LAZ-derived rasters
    """
    try:
        print(f"\n🧹 API: Cleaning region rasters...")
        print(f"   Region: {Path(request.region_directory).name}")
        print(f"   Mask: {Path(request.mask_file_path).name}")
        print(f"   Method: {request.method}")
        
        # Validate inputs
        region_dir = Path(request.region_directory)
        mask_file = Path(request.mask_file_path)
        
        if not region_dir.exists() or not region_dir.is_dir():
            raise HTTPException(
                status_code=400,
                detail=f"Region directory not found: {request.region_directory}"
            )
        
        if not mask_file.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Mask file not found: {request.mask_file_path}"
            )
        
        # Process raster cleaning
        result = clean_rasters_with_mask(
            region_dir=str(region_dir),
            mask_path=str(mask_file),
            raster_types=request.raster_types,
            method=request.method
        )
        
        return {
            "success": result["success"],
            "message": f"Cleaned {result.get('successful_count', 0)} of {result.get('total_rasters', 0)} rasters",
            "region_directory": request.region_directory,
            "mask_file": request.mask_file_path,
            "method": request.method,
            "results": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to clean region rasters: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/clean-single-raster")
async def clean_single_raster(request: SingleRasterCleaningRequest):
    """
    Clean a single raster file using a binary mask
    """
    try:
        print(f"\n🧹 API: Cleaning single raster...")
        print(f"   Raster: {Path(request.raster_file_path).name}")
        print(f"   Mask: {Path(request.mask_file_path).name}")
        print(f"   Method: {request.method}")
        
        # Validate inputs
        raster_file = Path(request.raster_file_path)
        mask_file = Path(request.mask_file_path)
        output_file = Path(request.output_file_path)
        
        if not raster_file.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Raster file not found: {request.raster_file_path}"
            )
        
        if not mask_file.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Mask file not found: {request.mask_file_path}"
            )
        
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean the raster
        cleaner = RasterCleaner(method=request.method)
        result = cleaner.clean_raster_with_mask(
            raster_path=str(raster_file),
            mask_path=str(mask_file),
            output_path=str(output_file)
        )
        
        return {
            "success": result["success"],
            "message": "Raster cleaning completed" if result["success"] else "Raster cleaning failed",
            "input_raster": request.raster_file_path,
            "mask_file": request.mask_file_path,
            "output_raster": request.output_file_path,
            "method": request.method,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to clean single raster: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

async def _background_density_processing(
    resolution: float,
    mask_threshold: float,
    search_directory: str,
    output_directory: str
):
    """
    Background task for processing density analysis
    """
    try:
        print(f"\n🔄 BACKGROUND: Starting density processing...")
        
        service = LAZDensityService(
            resolution=resolution,
            mask_threshold=mask_threshold
        )
        result = service.process_loaded_laz_files(
            search_directory=search_directory,
            output_base_dir=output_directory
        )
        
        print(f"🎉 BACKGROUND: Density processing completed")
        print(f"   Successful: {result['successful_count']}")
        print(f"   Failed: {result['failed_count']}")
        
    except Exception as e:
        error_msg = f"Background density processing failed: {str(e)}"
        print(f"❌ BACKGROUND: {error_msg}")
        logger.error(error_msg, exc_info=True)
