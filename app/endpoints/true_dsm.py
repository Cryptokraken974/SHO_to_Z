"""
True DSM API endpoint for downloading proper surface elevation data
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import asyncio
import logging
from pathlib import Path

from ..services.true_dsm_service import true_dsm_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/download-srtm-dsm")
async def download_srtm_dsm(
    background_tasks: BackgroundTasks,
    data: dict
):
    """
    Download SRTM data as true DSM for proper CHM calculation
    
    SRTM provides actual surface elevation (includes vegetation in forests)
    unlike Copernicus DEM which provides terrain elevation (bare earth)
    
    Expected data format:
    {
        "region_name": "MyRegion",
        "latitude": -14.87,
        "longitude": -39.38,
        "buffer_km": 12.5  # optional, default 12.5
    }
    """
    try:
        logger.info(f"🌲 API CALL: POST /api/download-srtm-dsm")
        logger.info(f"📊 Request data: {data}")
        
        # Validate required fields
        region_name = data.get('region_name')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not region_name:
            raise HTTPException(status_code=400, detail="region_name is required")
        
        if latitude is None or longitude is None:
            raise HTTPException(status_code=400, detail="latitude and longitude are required")
        
        # Validate coordinate ranges
        if not (-90 <= latitude <= 90):
            raise HTTPException(status_code=400, detail="latitude must be between -90 and 90")
        
        if not (-180 <= longitude <= 180):
            raise HTTPException(status_code=400, detail="longitude must be between -180 and 180")
        
        # Optional parameters
        buffer_km = data.get('buffer_km', 12.5)
        
        # Validate buffer
        if not (0.1 <= buffer_km <= 50.0):
            raise HTTPException(status_code=400, detail="buffer_km must be between 0.1 and 50.0")
        
        logger.info(f"🚀 Starting SRTM DSM download for region: {region_name}")
        logger.info(f"📍 Coordinates: ({latitude}, {longitude})")
        logger.info(f"📏 Buffer: {buffer_km} km")
        logger.info(f"🎯 Data Type: True DSM (surface elevation including vegetation)")
        
        # Start the download process
        result = await true_dsm_service.get_srtm_dsm_for_region(
            lat=latitude,
            lng=longitude,
            region_name=region_name,
            buffer_km=buffer_km
        )
        
        if result.get('success'):
            logger.info(f"✅ Successfully downloaded SRTM DSM for region: {region_name}")
            logger.info(f"📁 File saved to: {result.get('file_path')}")
            
            return JSONResponse(content={
                "success": True,
                "message": f"SRTM DSM downloaded successfully for region '{region_name}'",
                "region_name": region_name,
                "file_path": result.get('file_path'),
                "method": result.get('method'),
                "data_type": result.get('data_type'),
                "source": result.get('source'),
                "metadata": result.get('metadata'),
                "file_size_mb": result.get('file_size_mb'),
                "buffer_km": buffer_km,
                "note": "SRTM provides true surface elevation (DSM) including vegetation in forested areas"
            })
        else:
            logger.error(f"❌ Failed to download SRTM DSM for region: {region_name}")
            logger.error(f"🔍 Error details: {result.get('error')}")
            
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to download SRTM DSM: {result.get('error', 'Unknown error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in download_srtm_dsm: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/api/srtm-dsm/info")
async def get_srtm_dsm_info():
    """
    Get information about SRTM as a DSM source
    """
    try:
        return JSONResponse(content={
            "success": True,
            "dataset": {
                "name": "SRTM GL1 (30m)",
                "data_type": "Digital Surface Model (DSM)",
                "resolution": "30 meters",
                "coverage": "Global (60°N to 60°S)",
                "description": "C-band radar elevation data that provides surface elevation including vegetation in forested areas",
                "recommended_for": "CHM calculation, forest analysis, surface elevation modeling"
            },
            "radar_characteristics": {
                "band": "C-band (5.6 cm wavelength)",
                "penetration": "Minimal in dense forests - reflects off canopy",
                "behavior": {
                    "forests": "Surface elevation (includes vegetation height)",
                    "open_areas": "Terrain elevation (penetrates to ground)",
                    "urban_areas": "Building/structure heights included"
                }
            },
            "advantages_for_chm": [
                "Provides actual surface elevation in forests",
                "Global coverage and free access",
                "Well-established and validated dataset",
                "Suitable for vegetation height estimation when combined with DTM"
            ],
            "limitations": [
                "Mixed behavior in different land cover types",
                "30m resolution may miss small vegetation features", 
                "Some data voids in mountainous areas",
                "Acquired in year 2000 - may not reflect current vegetation"
            ],
            "vertical_reference": "EGM96 geoid",
            "horizontal_reference": "WGS84",
            "data_format": "GeoTIFF",
            "source": "NASA/USGS via OpenTopography API",
            "license": "Public domain"
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting SRTM DSM info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting SRTM DSM info: {str(e)}")

@router.post("/api/generate-proper-chm")
async def generate_proper_chm(data: dict):
    """
    Generate CHM using proper DSM (SRTM) and DTM (Copernicus) sources
    
    This endpoint automatically uses:
    - SRTM GL1 as DSM (surface elevation including vegetation)
    - Copernicus DEM as DTM (terrain elevation, bare earth)
    - Proper CHM = SRTM DSM - Copernicus DTM
    
    Expected data format:
    {
        "region_name": "MyRegion",
        "latitude": -14.87,
        "longitude": -39.38
    }
    """
    try:
        logger.info(f"🌳 API CALL: POST /api/generate-proper-chm")
        logger.info(f"📊 Request data: {data}")
        
        # Validate required fields
        region_name = data.get('region_name')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not region_name:
            raise HTTPException(status_code=400, detail="region_name is required")
        
        if latitude is None or longitude is None:
            raise HTTPException(status_code=400, detail="latitude and longitude are required")
        
        # Validate coordinate ranges
        if not (-90 <= latitude <= 90):
            raise HTTPException(status_code=400, detail="latitude must be between -90 and 90")
        
        if not (-180 <= longitude <= 180):
            raise HTTPException(status_code=400, detail="longitude must be between -180 and 180")
        
        logger.info(f"🚀 Starting proper CHM generation for region: {region_name}")
        logger.info(f"📍 Coordinates: ({latitude}, {longitude})")
        logger.info(f"🎯 Method: SRTM DSM - Copernicus DTM")
        
        # Check if files exist and guide user
        region_dir = Path("output") / region_name / "lidar"
        srtm_dsm_dir = region_dir / "DSM"
        copernicus_dtm_dir = region_dir / "DTM" / "filled"
        
        # Check for SRTM DSM
        srtm_files = list(srtm_dsm_dir.glob(f"*srtm*dsm*.tif")) if srtm_dsm_dir.exists() else []
        if not srtm_files:
            return JSONResponse(content={
                "success": False,
                "error": "SRTM DSM not found",
                "message": f"Please download SRTM DSM first using /api/download-srtm-dsm",
                "next_step": {
                    "endpoint": "/api/download-srtm-dsm",
                    "data": {
                        "region_name": region_name,
                        "latitude": latitude,
                        "longitude": longitude,
                        "buffer_km": 12.5
                    }
                }
            })
        
        # Check for Copernicus DTM
        dtm_files = list(copernicus_dtm_dir.glob(f"*{region_name}*DTM*.tif")) if copernicus_dtm_dir.exists() else []
        if not dtm_files:
            # Also check input directory for coordinate-based elevation data
            input_region_dir = Path("input") / region_name
            if input_region_dir.exists():
                elevation_dirs = list(input_region_dir.glob("*_elevation"))
                for elev_dir in elevation_dirs:
                    original_dir = elev_dir / "Original"
                    if original_dir.exists():
                        elevation_files = list(original_dir.glob("*.tiff")) + list(original_dir.glob("*.tif"))
                        if elevation_files:
                            dtm_files.extend(elevation_files)
                            break
        
        if not dtm_files:
            return JSONResponse(content={
                "success": False,
                "error": "DTM not found", 
                "message": f"Please download elevation data (DTM) first",
                "next_step": {
                    "endpoint": "/api/elevation/download-coordinates",
                    "data": {
                        "lat": latitude,
                        "lng": longitude,
                        "region_name": region_name,
                        "buffer_km": 12.5
                    }
                }
            })
        
        srtm_dsm_file = srtm_files[0]
        dtm_file = dtm_files[0]
        
        logger.info(f"📁 Found SRTM DSM: {srtm_dsm_file}")
        logger.info(f"📁 Found DTM: {dtm_file}")
        
        # Use the tiff_processing CHM function with proper source labeling
        from ..processing.tiff_processing import process_chm_tiff
        
        # Create CHM output directory
        chm_dir = region_dir / "CHM"
        chm_dir.mkdir(parents=True, exist_ok=True)
        
        # Set parameters for proper CHM processing
        chm_parameters = {
            "dsm_path": str(srtm_dsm_file),
            "output_filename": f"{region_name}_proper_CHM.tif"
        }
        
        # Process CHM with enhanced source detection
        result = await process_chm_tiff(str(dtm_file), str(chm_dir), chm_parameters)
        
        if result.get("status") == "success":
            chm_output_file = result.get("output_file")
            processing_time = result.get("processing_time", 0)
            statistics = result.get("statistics", {})
            
            logger.info(f"✅ Proper CHM generated successfully: {chm_output_file}")
            
            # Generate PNG visualization with viridis colormap
            try:
                from ..convert import convert_chm_to_viridis_png, convert_chm_to_viridis_png_clean
                
                # Create png_outputs directory
                png_output_dir = region_dir / "png_outputs"
                png_output_dir.mkdir(parents=True, exist_ok=True)
                
                # Create matplotlib subdirectory for decorated PNGs
                matplotlib_dir = png_output_dir / "matplotlib"
                matplotlib_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate matplotlib CHM PNG with decorations (legends, scales)
                matplotlib_png_path = matplotlib_dir / "CHM_matplot.png"
                convert_chm_to_viridis_png(
                    chm_output_file,
                    str(matplotlib_png_path),
                    enhanced_resolution=True,
                    save_to_consolidated=False
                )
                logger.info(f"🖼️ Matplotlib CHM PNG created: {matplotlib_png_path}")
                
                # Generate clean CHM PNG (no decorations) as main CHM.png
                clean_png_path = png_output_dir / "CHM.png"
                convert_chm_to_viridis_png_clean(
                    chm_output_file,
                    str(clean_png_path),
                    enhanced_resolution=True,
                    save_to_consolidated=False
                )
                logger.info(f"🎯 Clean CHM PNG created as main overlay: {clean_png_path}")
                
            except Exception as png_error:
                logger.warning(f"⚠️ CHM PNG generation failed: {png_error}")
                # Continue anyway since CHM TIF was created successfully
            
            # Enhanced result with source information
            enhanced_result = {
                **result,
                "success": True,
                "method": "Proper CHM calculation",
                "dsm_source": "SRTM GL1 (true surface elevation)",
                "dtm_source": "Copernicus DEM or coordinate elevation data (terrain elevation)",
                "calculation": "CHM = SRTM DSM - DTM",
                "note": "Using proper DSM-DTM combination for accurate vegetation height",
                "region_name": region_name,
                "chm_file": chm_output_file,
                "processing_time": processing_time,
                "statistics": statistics,
                "dsm_file": str(srtm_dsm_file),
                "dtm_file": str(dtm_file)
            }
            
            return JSONResponse(content=enhanced_result)
        else:
            raise HTTPException(
                status_code=500,
                detail=f"CHM generation failed: {result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in generate_proper_chm: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
