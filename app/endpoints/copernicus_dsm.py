"""
Copernicus DSM API endpoint for downloading Digital Surface Model data
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import asyncio
import logging
from pathlib import Path

from ..services.copernicus_dsm_service import copernicus_dsm_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/download-copernicus-dsm")
async def download_copernicus_dsm(
    background_tasks: BackgroundTasks,
    data: dict
):
    """
    Download Copernicus DSM data for a coordinate-based region
    
    Expected data format:
    {
        "region_name": "MyRegion",
        "latitude": -14.87,
        "longitude": -39.38,
        "buffer_km": 5.0,  # optional, default 5.0
        "resolution": "30m"  # optional, "30m" or "90m", default "30m"
    }
    """
    try:
        logger.info(f"🌍 API CALL: POST /api/download-copernicus-dsm")
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
        buffer_km = data.get('buffer_km', 5.0)
        resolution = data.get('resolution', '30m')
        
        # Validate resolution
        if resolution not in ['30m', '90m']:
            raise HTTPException(status_code=400, detail="resolution must be '30m' or '90m'")
        
        # Validate buffer
        if not (0.1 <= buffer_km <= 50.0):
            raise HTTPException(status_code=400, detail="buffer_km must be between 0.1 and 50.0")
        
        logger.info(f"🚀 Starting DSM download for region: {region_name}")
        logger.info(f"📍 Coordinates: ({latitude}, {longitude})")
        logger.info(f"📏 Buffer: {buffer_km} km")
        logger.info(f"🔍 Resolution: {resolution}")
        
        # Start the download process
        result = await copernicus_dsm_service.get_dsm_for_region(
            lat=latitude,
            lng=longitude,
            region_name=region_name,
            buffer_km=buffer_km,
            resolution=resolution
        )
        
        if result.get('success'):
            logger.info(f"✅ Successfully downloaded DSM for region: {region_name}")
            logger.info(f"📁 File saved to: {result.get('file_path')}")
            
            return JSONResponse(content={
                "success": True,
                "message": f"Copernicus DSM downloaded successfully for region '{region_name}'",
                "region_name": region_name,
                "file_path": result.get('file_path'),
                "method": result.get('method'),
                "tiles_downloaded": result.get('tiles_downloaded'),
                "metadata": result.get('metadata'),
                "resolution": resolution,
                "buffer_km": buffer_km
            })
        else:
            logger.error(f"❌ Failed to download DSM for region: {region_name}")
            logger.error(f"🔍 Error details: {result.get('error')}")
            
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to download DSM: {result.get('error', 'Unknown error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in download_copernicus_dsm: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/api/regions/{region_name}/dsm-status")
async def get_dsm_status(region_name: str):
    """
    Check if DSM data exists for a region and get its metadata
    """
    try:
        logger.info(f"🔍 API CALL: GET /api/regions/{region_name}/dsm-status")
        
        # Check for DSM files in the region directory
        region_dsm_dir = Path("output") / region_name / "dsm"
        
        if not region_dsm_dir.exists():
            return JSONResponse(content={
                "success": True,
                "region_name": region_name,
                "dsm_available": False,
                "message": "No DSM data found for this region"
            })
        
        # Look for DSM files
        dsm_files = []
        for dsm_file in region_dsm_dir.glob("*.tif"):
            try:
                import rasterio
                with rasterio.open(dsm_file) as src:
                    file_info = {
                        "file_name": dsm_file.name,
                        "file_path": str(dsm_file),
                        "size_mb": round(dsm_file.stat().st_size / (1024 * 1024), 2),
                        "shape": [src.height, src.width],
                        "crs": src.crs.to_string() if src.crs else None,
                        "bounds": list(src.bounds),
                        "resolution": [abs(src.transform[0]), abs(src.transform[4])]
                    }
                    dsm_files.append(file_info)
            except Exception as e:
                logger.warning(f"Could not read DSM file {dsm_file}: {e}")
        
        return JSONResponse(content={
            "success": True,
            "region_name": region_name,
            "dsm_available": len(dsm_files) > 0,
            "dsm_files": dsm_files,
            "total_files": len(dsm_files)
        })
        
    except Exception as e:
        logger.error(f"❌ Error checking DSM status for region {region_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking DSM status: {str(e)}")

@router.get("/api/copernicus-dsm/info")
async def get_copernicus_dsm_info():
    """
    Get information about available Copernicus DSM datasets
    """
    try:
        return JSONResponse(content={
            "success": True,
            "datasets": {
                "GLO-30": {
                    "resolution": "30 meters",
                    "coverage": "Limited worldwide (some countries excluded)",
                    "description": "Higher resolution DSM with 30m pixel size",
                    "recommended_for": "Detailed analysis, small to medium areas"
                },
                "GLO-90": {
                    "resolution": "90 meters", 
                    "coverage": "Complete worldwide",
                    "description": "Global DSM with 90m pixel size",
                    "recommended_for": "Large area analysis, global studies"
                }
            },
            "data_type": "Digital Surface Model (DSM)",
            "vertical_reference": "EGM2008 geoid",
            "horizontal_reference": "WGS84",
            "data_format": "GeoTIFF (Cloud Optimized)",
            "source": "Copernicus Programme",
            "access_methods": [
                "Microsoft Planetary Computer STAC API",
                "Direct STAC API",
                "AWS S3 (no authentication required)"
            ],
            "license": "Free for general public use",
            "update_frequency": "Static dataset (2021 release)"
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting DSM info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting DSM info: {str(e)}")
