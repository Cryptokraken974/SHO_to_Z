from fastapi import APIRouter, HTTPException, Form
from .core import Sentinel2Request
from fastapi.responses import JSONResponse
import math

router = APIRouter()

@router.post("/api/download-sentinel2")
async def download_sentinel2(request: Sentinel2Request):
    """Download Sentinel-2 red and NIR bands for given coordinates using Copernicus CDSE"""
    # Import here to avoid circular imports
    from ..main import manager, settings
    
    try:
        # Initialize lat/lng as None - they will be set later if needed
        lat = None
        lng = None
        
        # First check if we have bounding box coordinates (priority over lat/lng)
        has_bbox = all([
            request.north_bound is not None,
            request.south_bound is not None,
            request.east_bound is not None,
            request.west_bound is not None
        ])
        
        # If no bounding box, try to get coordinates using the helper methods
        if not has_bbox:
            try:
                lat = request.get_latitude()
                lng = request.get_longitude()
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            
            # Validate coordinates
            if not (-90 <= lat <= 90):
                raise HTTPException(status_code=400, detail=f"Invalid latitude: {lat}. Must be between -90 and 90.")
            if not (-180 <= lng <= 180):
                raise HTTPException(status_code=400, detail=f"Invalid longitude: {lng}. Must be between -180 and 180.")
            
            # Check if coordinates are over land (basic validation)
            # Reject obvious ocean areas where no meaningful data exists
            if abs(lat) > 80:  # Arctic/Antarctic regions with limited coverage
                raise HTTPException(status_code=400, detail=f"Coordinates {lat}, {lng} are in polar regions with limited Sentinel-2 coverage.")
        
        import uuid
        from ..data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
        from ..data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
        from ..data_acquisition.utils.coordinates import BoundingBox
        
        # Generate unique download ID
        download_id = str(uuid.uuid4())
        
        # Create progress callback that sends updates via WebSocket
        async def progress_callback(update):
            coordinates = {}
            if lat is not None and lng is not None:
                coordinates = {"lat": lat, "lng": lng}
            elif has_bbox:
                coordinates = {
                    "north": request.north_bound,
                    "south": request.south_bound,
                    "east": request.east_bound,
                    "west": request.west_bound
                }
            
            await manager.send_progress_update({
                "source": "copernicus_sentinel2",
                "coordinates": coordinates,
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

        query_bbox: BoundingBox

        if has_bbox:
            if request.north_bound <= request.south_bound or \
               request.east_bound <= request.west_bound:
                raise HTTPException(status_code=400, detail="Invalid bounding box: North must be > South and East must be > West.")

            query_bbox = BoundingBox(
                north=request.north_bound,
                south=request.south_bound,
                east=request.east_bound,
                west=request.west_bound
            )
            print(f"🗺️ Sentinel-2 Request (using provided BBox):")
            print(f"🔲 BBox: West={query_bbox.west:.4f}, South={query_bbox.south:.4f}, East={query_bbox.east:.4f}, North={query_bbox.north:.4f}")

        elif lat is not None and lng is not None:
            buffer_km = request.buffer_km # buffer_km has a default in Sentinel2Request

            # Calculate bounding box from center point and buffer (existing logic)
            # Ensure CoordinateConverter is available or calculations are direct
            # Using direct calculation as before:
            lat_delta = buffer_km / 111.0  # Rough conversion: 1 degree ≈ 111 km
            lng_delta = buffer_km / (111.0 * abs(math.cos(math.radians(lat)))) if abs(math.cos(math.radians(lat))) > 1e-9 else buffer_km / 111.0 # Avoid division by zero near poles

            query_bbox = BoundingBox(
                west=lng - lng_delta,
                south=lat - lat_delta,
                east=lng + lng_delta,
                north=lat + lat_delta
            )
            print(f"🗺️ Sentinel-2 Request (using Lat/Lng/Buffer):")
            print(f"📍 Center: {lat}, {lng}")
            print(f"📏 Buffer: {buffer_km}km")
            print(f"🔲 BBox: West={query_bbox.west:.4f}, South={query_bbox.south:.4f}, East={query_bbox.east:.4f}, North={query_bbox.north:.4f}")
        else:
            # This case should ideally be caught by Pydantic model validation if lat/lng were required when bounds are not set.
            # Or by the get_latitude/get_longitude calls if they were made mandatory always.
            # For now, the Pydantic model makes lat/lng optional, so this check is important.
            raise HTTPException(status_code=400, detail="Either full bounding box (north_bound, south_bound, east_bound, west_bound) or latitude/longitude must be provided.")
        
        print(f"📐 Approx. Size: {(query_bbox.east-query_bbox.west)*111*math.cos(math.radians((query_bbox.north+query_bbox.south)/2)):.2f}km x {(query_bbox.north-query_bbox.south)*111:.2f}km")
        
        # Create download request
        download_request = DownloadRequest(
            bbox=query_bbox,
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
            # Automatically trigger conversion after successful download
            print(f"✅ Sentinel-2 download successful, starting automatic conversion...")
            
            try:
                # Get region name from metadata or download_request
                region_name_for_conversion = result.metadata.get('region_name') if result.metadata else download_request.region_name
                
                if region_name_for_conversion:
                    from ..convert import convert_sentinel2_to_png
                    from pathlib import Path
                    
                    # Convert the downloaded TIF to individual bands and PNG
                    data_dir = Path("input") / region_name_for_conversion
                    conversion_result = convert_sentinel2_to_png(str(data_dir), region_name_for_conversion)
                    
                    if conversion_result['success']:
                        print(f"✅ Automatic Sentinel-2 conversion completed: {len(conversion_result['files'])} files generated")
                    else:
                        print(f"⚠️ Automatic Sentinel-2 conversion had issues: {conversion_result['errors']}")
                        
                else:
                    print(f"⚠️ No region name available for automatic conversion")
                    
            except Exception as conversion_error:
                print(f"⚠️ Automatic conversion failed (download still successful): {conversion_error}")
                # Don't fail the overall download if conversion fails
            
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
