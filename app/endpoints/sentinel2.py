from fastapi import APIRouter, HTTPException, Form
from ..main import manager, settings, Sentinel2Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/api/download-sentinel2")
async def download_sentinel2(request: Sentinel2Request):
    """Download Sentinel-2 red and NIR bands for given coordinates using Copernicus CDSE"""
    try:
        # Validate coordinates
        if not (-90 <= request.lat <= 90):
            raise HTTPException(status_code=400, detail=f"Invalid latitude: {request.lat}. Must be between -90 and 90.")
        if not (-180 <= request.lng <= 180):
            raise HTTPException(status_code=400, detail=f"Invalid longitude: {request.lng}. Must be between -180 and 180.")
        
        # Check if coordinates are over land (basic validation)
        # Reject obvious ocean areas where no meaningful data exists
        if abs(request.lat) > 80:  # Arctic/Antarctic regions with limited coverage
            raise HTTPException(status_code=400, detail=f"Coordinates {request.lat}, {request.lng} are in polar regions with limited Sentinel-2 coverage.")
        
        import uuid
        from ..data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
        from ..data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
        from ..data_acquisition.utils.coordinates import BoundingBox
        
        # Generate unique download ID
        download_id = str(uuid.uuid4())
        
        # Create progress callback that sends updates via WebSocket
        async def progress_callback(update):
            await manager.send_progress_update({
                "source": "copernicus_sentinel2",
                "coordinates": {"lat": request.lat, "lng": request.lng},
                "download_id": download_id,
                **update
            })
        
        # Create Copernicus Sentinel-2 data source with progress callback
        sentinel2_source = CopernicusSentinel2Source(
            token=settings.cdse_token,
            client_id=settings.cdse_client_id,
            client_secret=settings.cdse_client_secret,
            progress_callback=progress_callback
        )
        
        # Register this download task for cancellation
        manager.add_download_task(download_id, sentinel2_source)
        
        # Calculate bounding box from center point and buffer
        lat_delta = request.buffer_km / 111.0  # Rough conversion: 1 degree ≈ 111 km
        # For longitude, adjust for latitude (longitude lines get closer at higher latitudes)
        lng_delta = request.buffer_km / (111.0 * abs(math.cos(math.radians(request.lat))))
        
        bbox = BoundingBox(
            west=request.lng - lng_delta,
            south=request.lat - lat_delta,
            east=request.lng + lng_delta,
            north=request.lat + lat_delta
        )
        
        print(f"🗺️ Sentinel-2 Request:")
        print(f"📍 Center: {request.lat}, {request.lng}")
        print(f"📏 Buffer: {request.buffer_km}km")
        print(f"🔲 BBox: West={bbox.west:.4f}, South={bbox.south:.4f}, East={bbox.east:.4f}, North={bbox.north:.4f}")
        print(f"📐 Size: {(bbox.east-bbox.west)*111:.2f}km x {(bbox.north-bbox.south)*111:.2f}km")
        
        # Create download request
        download_request = DownloadRequest(
            bbox=bbox,
            data_type=DataType.IMAGERY,
            resolution=DataResolution.HIGH,
            max_file_size_mb=100.0,
            output_format="GeoTIFF",
            region_name=request.region_name
        )
        
        # Check availability first
        available = await sentinel2_source.check_availability(download_request)
        if not available:
            # Clean up download registration
            manager.cancel_download(download_id)
            return {
                "success": False,
                "error_message": "No Sentinel-2 data available for the requested area and time period"
            }
        
        # Download the data
        result = await sentinel2_source.download(download_request)
        
        # Clean up and close
        manager.cancel_download(download_id)  # Remove from active downloads
        await sentinel2_source.close()
        
        if result.success:
            return {
                "success": True,
                "file_path": result.file_path,
                "file_size_mb": result.file_size_mb,
                "resolution_m": result.resolution_m,
                "metadata": result.metadata
            }
        else:
            return {
                "success": False,
                "error_message": result.error_message
            }
            
    except Exception as e:
        # Clean up download registration on error
        if 'download_id' in locals():
            manager.cancel_download(download_id)
        
        import traceback
        error_details = f"Sentinel-2 download failed: {str(e)}\n{traceback.format_exc()}"
        print(error_details)  # Log to console for debugging
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/convert-sentinel2")
async def convert_sentinel2_images(region_name: str = Form(...)):
    """Convert downloaded Sentinel-2 TIF files to PNG for display"""
    print(f"\n🛰️ API CALL: /api/convert-sentinel2")
    print(f"🏷️ Region name: {region_name}")
    
    try:
        from ..convert import convert_sentinel2_to_png
        from pathlib import Path
        
        # Find the data directory for this region - now reading from input folder
        # If region_name ends with _elevation, remove it for Sentinel-2 processing
        processed_region_name = region_name
        if region_name.endswith("_elevation"):
            processed_region_name = region_name[:-len("_elevation")]

        data_dir = Path("input") / processed_region_name
        
        if not data_dir.exists():
            return {
                "success": False,
                "error_message": f"Sentinel-2 input directory not found: {data_dir}",
                "files": [],
                "errors": []
            }
            
        # Check if sentinel2 subfolder exists
        sentinel2_subfolder = data_dir / "sentinel2"
        if sentinel2_subfolder.exists():
            print(f"✅ Found Sentinel-2 subfolder: {sentinel2_subfolder}")
        else:
            print(f"⚠️ Sentinel-2 subfolder not found, will check directly in input folder")
        
        # Convert TIF files to PNG
        conversion_result = convert_sentinel2_to_png(str(data_dir), processed_region_name)
        
        if conversion_result['success']:
            # Generate base64 encoded images for immediate display
            display_files = []
            for file_info in conversion_result['files']:
                try:
                    from ..convert import convert_geotiff_to_png_base64
                    # Use the original TIF for base64 conversion to get the best quality
                    image_b64 = convert_geotiff_to_png_base64(file_info['tif_path'])
                    
                    display_files.append({
                        'band': file_info['band'],
                        'png_path': file_info['png_path'],
                        'image': image_b64,
                        'size_mb': file_info['size_mb']
                    })
                except Exception as e:
                    print(f"❌ Error generating base64 for {file_info['band']}: {e}")
            
            return {
                "success": True,
                "region_name": region_name,
                "files": display_files,
                "total_files": len(display_files),
                "errors": conversion_result['errors']
            }
        else:
            return {
                "success": False,
                "error_message": "Conversion failed",
                "files": [],
                "errors": conversion_result['errors']
            }
            
    except Exception as e:
        print(f"❌ Error in convert_sentinel2_images: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error_message": str(e),
            "files": [],
            "errors": []
        }
