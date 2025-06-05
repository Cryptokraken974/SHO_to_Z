# Data Acquisition Endpoints
from fastapi import APIRouter, HTTPException, Form, Request
from fastapi.responses import JSONResponse
from ..main import manager, settings, data_manager, CoordinateRequest, DataAcquisitionRequest
from ..config import validate_api_keys, get_data_source_config

router = APIRouter()

@router.get("/api/config")
async def get_configuration():
    """Get current configuration and API key status"""
    try:
        api_keys = validate_api_keys()
        
        return {
            "success": True,
            "config": {
                "cache_dir": settings.cache_dir,
                "output_dir": settings.output_dir,
                "default_buffer_km": settings.default_buffer_km,
                "max_file_size_mb": settings.max_file_size_mb,
                "cache_expiry_days": settings.cache_expiry_days,
                "source_priorities": settings.source_priorities
            },
            "api_keys": api_keys,
            "data_sources": {
                "opentopography": get_data_source_config("opentopography"),
                "sentinel2": get_data_source_config("sentinel2"),
                "ornl_daac": get_data_source_config("ornl_daac")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/check-data-availability")
async def check_data_availability(request: CoordinateRequest):
    """Check what data is available for given coordinates"""
    try:
        availability = await data_manager.check_availability(request.lat, request.lng)
        
        return {
            "success": True,
            "availability": {
                "high_res_lidar": availability.high_res_lidar,
                "srtm_dem": availability.srtm_dem,
                "sentinel2": availability.sentinel2,
                "landsat": availability.landsat,
                "source_priorities": availability.source_priorities
            },
            "coordinates": {
                "lat": request.lat,
                "lng": request.lng
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/acquire-data")
async def acquire_data(request: DataAcquisitionRequest):
    """Acquire data for given coordinates"""
    try:
        # Create progress callback to send updates via WebSocket
        async def progress_callback(data):
            """Forward progress updates to WebSocket clients"""
            await manager.send_progress_update(data)
        
        # Run data acquisition with progress tracking
        results = await data_manager.acquire_data_for_coordinates(
            request.lat, request.lng, request.buffer_km,
            data_sources=request.data_sources,
            max_file_size_mb=request.max_file_size_mb,
            progress_callback=lambda p: progress_callback_wrapper(p, request.region_name),
            region_name=request.region_name
        )
        
        return {
            "success": results.success,
            "files": results.files,
            "metadata": results.metadata,
            "errors": results.errors,
            "source_used": results.source_used,
            "download_size_mb": results.download_size_mb,
            "processing_time_seconds": results.processing_time_seconds,
            "roi": {
                "center_lat": results.roi.center_lat,
                "center_lng": results.roi.center_lng,
                "buffer_km": results.roi.buffer_km,
                "name": results.roi.name
            }
        }
    except Exception as e:
        # Send error update via WebSocket
        await manager.send_progress_update({
            "type": "data_acquisition_error",
            "message": f"Error acquiring data: {str(e)}",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/estimate-download-size")
async def estimate_download_size(request: CoordinateRequest):
    """Estimate download size for different data types"""
    try:
        estimates = data_manager.estimate_download_size(
            request.lat, 
            request.lng, 
            request.buffer_km
        )
        
        return {
            "success": True,
            "estimates_mb": estimates,
            "coordinates": {
                "lat": request.lat,
                "lng": request.lng,
                "buffer_km": request.buffer_km
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/acquisition-history")
async def get_acquisition_history():
    """Get history of data acquisitions"""
    try:
        history = data_manager.get_acquisition_history()
        return {
            "success": True,
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/cleanup-cache")
async def cleanup_cache(older_than_days: int = 30):
    """Clean up cached data older than specified days"""
    try:
        data_manager.cleanup_cache(older_than_days)
        return {
            "success": True,
            "message": f"Cache cleanup completed for files older than {older_than_days} days"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/storage-stats")
async def get_storage_stats():
    """Get storage statistics"""
    try:
        stats = data_manager.file_manager.get_storage_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
