from fastapi import FastAPI, Request, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import glob
import base64
import asyncio
import json
import math
from typing import Optional, List, Dict, Any

from .convert import convert_geotiff_to_png_base64
from .processing import laz_to_dem, dtm, dsm, chm, hillshade, hillshade_315_45_08, hillshade_225_45_08, slope, aspect, color_relief, tri, tpi, roughness
from .data_acquisition import DataAcquisitionManager
from .config import get_settings, validate_api_keys, get_data_source_config

# Get application settings
settings = get_settings()

# Initialize data acquisition manager with settings
data_manager = DataAcquisitionManager(
    cache_dir=settings.cache_dir,
    output_dir=settings.output_dir,
    settings=settings
)

# WebSocket connection manager for progress updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.active_downloads: Dict[str, Any] = {}  # Store active download tasks

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_progress_update(self, message: dict):
        """Send progress update to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove disconnected clients
                try:
                    self.active_connections.remove(connection)
                except ValueError:
                    pass
    
    def add_download_task(self, download_id: str, source_instance):
        """Add a download task that can be cancelled."""
        self.active_downloads[download_id] = source_instance
    
    def cancel_download(self, download_id: str):
        """Cancel a specific download task."""
        if download_id in self.active_downloads:
            source_instance = self.active_downloads[download_id]
            if hasattr(source_instance, 'cancel'):
                source_instance.cancel()
            del self.active_downloads[download_id]
            return True
        return False

manager = ConnectionManager()

# Pydantic models for API requests
class CoordinateRequest(BaseModel):
    lat: float
    lng: float
    buffer_km: float = 1.0
    data_types: Optional[List[str]] = None

class DataAcquisitionRequest(BaseModel):
    lat: float
    lng: float
    buffer_km: float = 1.0
    data_sources: Optional[List[str]] = None
    max_file_size_mb: float = 500.0

class Sentinel2Request(BaseModel):
    lat: float
    lng: float
    buffer_km: float = 2.0  # 2km radius = 4km x 4km box (smaller for better processing)
    bands: Optional[List[str]] = ["B04", "B08"]  # Sentinel-2 red and NIR bands

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/output", StaticFiles(directory="output"), name="output")

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates and cancellation commands."""
    await manager.connect(websocket)
    try:
        while True:
            # Listen for messages from client
            message = await websocket.receive_text()
            try:
                data = json.loads(message)
                
                # Handle cancellation messages
                if data.get("type") == "cancel_download":
                    download_id = data.get("download_id")
                    if download_id:
                        success = manager.cancel_download(download_id)
                        await websocket.send_text(json.dumps({
                            "type": "cancellation_response",
                            "download_id": download_id,
                            "success": success
                        }))
                        
                        # Broadcast cancellation to all clients
                        await manager.send_progress_update({
                            "type": "download_cancelled",
                            "message": "Download cancelled by user",
                            "download_id": download_id,
                            "band": "Cancelled"
                        })
                        
            except json.JSONDecodeError:
                # Ignore malformed messages - might be keepalive
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
def index():
    with open("frontend/index.html") as f:
        return f.read()

@app.get("/api/list-laz-files")
async def list_laz_files():
    """List all LAZ files in the input directory"""
    input_dir = "input"
    
    # Create input directory if it doesn't exist
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        return {"files": []}
    
    # Find all LAZ files (including .laz and .copc.laz)
    laz_patterns = [
        os.path.join(input_dir, "**/*.laz"),
        os.path.join(input_dir, "**/*.LAZ"),
        os.path.join(input_dir, "**/*.copc.laz")
    ]
    
    files = []
    for pattern in laz_patterns:
        files.extend(glob.glob(pattern, recursive=True))
    
    # Convert to relative paths and remove duplicates
    relative_files = list(set([os.path.relpath(f) for f in files]))
    relative_files.sort()
    
    return {"files": relative_files}

# Utility to handle image generation endpoints
def handle_generation(generator):
    tif_path = generator.generate()
    image_b64 = convert_geotiff_to_png_base64(tif_path)
    return {"image": image_b64}

@app.post("/api/laz_to_dem")
async def api_laz_to_dem(input_file: str = Form(...)):
    """Convert LAZ to DEM"""
    print(f"\n🎯 API CALL: /api/laz_to_dem")
    print(f"📥 Input file: {input_file}")
    
    try:
        # Import the synchronous function
        from .processing.laz_to_dem import laz_to_dem
        
        # Call the synchronous function directly
        tif_path = laz_to_dem(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
            
    except Exception as e:
        print(f"❌ Error in api_laz_to_dem: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/dtm")
async def api_dtm(input_file: str = Form(...)):
    """Convert LAZ to DTM (ground points only)"""
    print(f"\n🎯 API CALL: /api/dtm")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = dtm(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_dtm: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/dsm")
async def api_dsm(input_file: str = Form(...)):
    """Convert LAZ to DSM (surface points)"""
    print(f"\n🎯 API CALL: /api/dsm")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = dsm(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_dsm: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/chm")
async def api_chm(input_file: str = Form(...)):
    """Generate CHM (Canopy Height Model) from LAZ file"""
    print(f"\n🎯 API CALL: /api/chm")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = chm(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_chm: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/hillshade")
async def api_hillshade(input_file: str = Form(...)):
    """Generate hillshade from LAZ file"""
    print(f"\n🎯 API CALL: /api/hillshade")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = hillshade(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_hillshade: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/hillshade_315_45_08")
async def api_hillshade_315_45_08(input_file: str = Form(...)):
    """Generate hillshade with 315° azimuth, 45° altitude, 0.8 z-factor"""
    print(f"\n🎯 API CALL: /api/hillshade_315_45_08")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = hillshade_315_45_08(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_hillshade_315_45_08: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/hillshade_225_45_08")
async def api_hillshade_225_45_08(input_file: str = Form(...)):
    """Generate hillshade with 225° azimuth, 45° altitude, 0.8 z-factor"""
    print(f"\n🎯 API CALL: /api/hillshade_225_45_08")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = hillshade_225_45_08(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_hillshade_225_45_08: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/slope")
async def api_slope(input_file: str = Form(...)):
    """Generate slope from LAZ file"""
    print(f"\n🎯 API CALL: /api/slope")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = slope(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_slope: {str(e)}")
        raise

@app.post("/api/aspect")
async def api_aspect(input_file: str = Form(...)):
    """Generate aspect from LAZ file"""
    print(f"\n🎯 API CALL: /api/aspect")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = aspect(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_aspect: {str(e)}")
        raise

@app.post("/api/color_relief")
async def api_color_relief(input_file: str = Form(...)):
    """Generate color relief from LAZ file"""
    print(f"\n🎯 API CALL: /api/color_relief")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = color_relief(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_color_relief: {str(e)}")
        raise

@app.post("/api/tri")
async def api_tri(input_file: str = Form(...)):
    """Generate TRI from LAZ file"""
    print(f"\n🎯 API CALL: /api/tri")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = tri(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_tri: {str(e)}")
        raise

@app.post("/api/tpi")
async def api_tpi(input_file: str = Form(...)):
    """Generate TPI from LAZ file"""
    print(f"\n🎯 API CALL: /api/tpi")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = tpi(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_tpi: {str(e)}")
        raise

@app.post("/api/roughness")
async def api_roughness(input_file: str = Form(...)):
    """Generate roughness from LAZ file"""
    print(f"\n🎯 API CALL: /api/roughness")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = roughness(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_roughness: {str(e)}")
        raise

@app.post("/api/chat")
async def api_chat(data: dict):
    prompt = data.get("prompt", "")
    model = data.get("model", "")
    # Placeholder response; integrate with real LLM here
    response = f"Model {model} says: {prompt}"
    return {"response": response}

@app.get("/api/overlay/{processing_type}/{filename}")
async def get_overlay_data(processing_type: str, filename: str):
    """Get overlay data for a processed image including bounds and base64 encoded image"""
    print(f"\n🗺️  API CALL: /api/overlay/{processing_type}/{filename}")
    
    try:
        from .geo_utils import get_image_overlay_data
        
        # Extract base filename (remove path and extension)
        base_filename = os.path.splitext(os.path.basename(filename))[0]
        if base_filename.endswith('.copc'):
            base_filename = base_filename[:-5]  # Remove .copc suffix
            
        print(f"📂 Base filename: {base_filename}")
        print(f"🔄 Processing type: {processing_type}")
        
        # Map API processing types to actual folder names
        type_mapping = {
            'laz_to_dem': 'DEM',
            'dtm': 'DTM',
            'dsm': 'DSM',
            'chm': 'CHM',
            'hillshade': 'Hillshade',
            'hillshade_315_45_08': 'Hillshade',
            'hillshade_225_45_08': 'Hillshade',
            'slope': 'Slope',
            'aspect': 'Aspect',
            'color_relief': 'ColorRelief',
            'tri': 'TRI',
            'tpi': 'TPI',
            'roughness': 'Roughness'
        }
        
        # Get the actual folder name
        actual_processing_type = type_mapping.get(processing_type, processing_type.title())
        print(f"📁 Mapped processing type: {processing_type} -> {actual_processing_type}")
        
        # For hillshade variants, pass the original processing type for filename mapping
        filename_processing_type = processing_type if processing_type.startswith('hillshade_') else actual_processing_type
        
        overlay_data = get_image_overlay_data(base_filename, actual_processing_type, filename_processing_type)
        
        if not overlay_data:
            print(f"❌ No overlay data found for {base_filename}/{actual_processing_type}")
            # Debug: List available directories
            output_base = f"output/{base_filename}"
            if os.path.exists(output_base):
                available_dirs = [d for d in os.listdir(output_base) if os.path.isdir(os.path.join(output_base, d))]
                print(f"🔍 Available directories: {available_dirs}")
            else:
                print(f"🔍 Output directory doesn't exist: {output_base}")
            
            return JSONResponse(
                status_code=404, 
                content={"error": "Overlay data not found or could not extract coordinates"}
            )
            
        print(f"✅ Overlay data retrieved successfully")
        print(f"📍 Bounds: {overlay_data['bounds']}")
        
        return overlay_data
        
    except Exception as e:
        print(f"❌ Error getting overlay data: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get overlay data: {str(e)}"}
        )

@app.get("/api/test-overlay/{filename}")
async def get_test_overlay(filename: str):
    """Create a simple black overlay at the LAZ file coordinates for testing"""
    print(f"\n🧪 TEST OVERLAY: /api/test-overlay/{filename}")
    
    try:
        from PIL import Image, ImageDraw
        import io
        
        # Map known LAZ files to their approximate coordinates in WGS84
        laz_coordinates = {
            'FoxIsland.laz': {
                'center_lat': 44.4268,
                'center_lng': -68.2048,
                'size_deg': 0.01  # ~1km at this latitude
            },
            'OR_WizardIsland.laz': {
                'center_lat': 42.9446,
                'center_lng': -122.1090,
                'size_deg': 0.01  # ~1km at this latitude
            }
        }
        
        # Extract base filename
        base_filename = os.path.splitext(os.path.basename(filename))[0]
        if base_filename.endswith('.copc'):
            base_filename = base_filename[:-5]
            
        print(f"📂 Base filename: {base_filename}")
        
        # Find matching LAZ file
        matching_coords = None
        for laz_file, coords in laz_coordinates.items():
            if base_filename in laz_file or laz_file.replace('.laz', '') in base_filename:
                matching_coords = coords
                break
                
        if not matching_coords:
            print(f"❌ No coordinates found for {base_filename}")
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "No test coordinates available for this file"}
            )
            
        print(f"📍 Using coordinates: {matching_coords}")
        
        # Calculate bounds
        half_size = matching_coords['size_deg'] / 2
        bounds = {
            'north': matching_coords['center_lat'] + half_size,
            'south': matching_coords['center_lat'] - half_size,
            'east': matching_coords['center_lng'] + half_size,
            'west': matching_coords['center_lng'] - half_size,
            'center_lat': matching_coords['center_lat'],
            'center_lng': matching_coords['center_lng']
        }
        
        print(f"🗺️  Test bounds: {bounds}")
        
        # Create a simple black square image
        img_size = 200
        img = Image.new('RGBA', (img_size, img_size), (0, 0, 0, 128))  # Semi-transparent black
        
        # Add a red border for visibility
        draw = ImageDraw.Draw(img)
        border_width = 5
        draw.rectangle([0, 0, img_size-1, img_size-1], outline=(255, 0, 0, 255), width=border_width)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        print(f"✅ Created test overlay image ({len(image_data)} chars)")
        
        return {
            'success': True,
            'bounds': bounds,
            'image_data': image_data,
            'processing_type': 'test',
            'filename': base_filename
        }
        
    except Exception as e:
        print(f"❌ Error creating test overlay: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to create test overlay: {str(e)}"}
        )

@app.get("/api/pipelines/json")
async def list_json_pipelines():
    """List all available JSON pipelines"""
    print(f"\n🔧 API CALL: /api/pipelines/json")
    
    try:
        from .processing.json_processor import get_processor
        
        processor = get_processor()
        pipelines = processor.list_available_json_pipelines()
        
        print(f"✅ Found {len(pipelines)} JSON pipelines")
        
        return {
            "success": True,
            "pipelines": pipelines,
            "count": len(pipelines)
        }
        
    except Exception as e:
        print(f"❌ Error listing JSON pipelines: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "pipelines": []
        }

@app.get("/api/pipelines/json/{pipeline_name}")
async def get_json_pipeline_info(pipeline_name: str):
    """Get information about a specific JSON pipeline"""
    print(f"\n🔧 API CALL: /api/pipelines/json/{pipeline_name}")
    
    try:
        from .processing.json_processor import get_processor
        
        processor = get_processor()
        pipeline_info = processor.get_pipeline_info(pipeline_name)
        
        if pipeline_info:
            print(f"✅ Pipeline info retrieved for: {pipeline_name}")
            return {
                "success": True,
                "pipeline_name": pipeline_name,
                "pipeline": pipeline_info
            }
        else:
            print(f"❌ Pipeline not found: {pipeline_name}")
            return {
                "success": False,
                "error": f"Pipeline '{pipeline_name}' not found"
            }
        
    except Exception as e:
        print(f"❌ Error getting pipeline info: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/pipelines/toggle-json")
async def toggle_json_pipelines(data: dict):
    """Toggle JSON pipeline usage on/off"""
    print(f"\n🔧 API CALL: /api/pipelines/toggle-json")
    
    try:
        use_json = data.get("use_json", True)
        
        from .processing.json_processor import set_use_json_pipelines
        set_use_json_pipelines(use_json)
        
        print(f"✅ JSON pipeline usage set to: {use_json}")
        
        return {
            "success": True,
            "use_json_pipelines": use_json,
            "message": f"JSON pipelines {'enabled' if use_json else 'disabled'}"
        }
        
    except Exception as e:
        print(f"❌ Error toggling JSON pipelines: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Data Acquisition Endpoints

@app.get("/api/config")
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

@app.post("/api/check-data-availability")
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

@app.post("/api/acquire-data")
async def acquire_data(request: DataAcquisitionRequest):
    """Acquire data for given coordinates"""
    try:
        # Run data acquisition 
        result = await data_manager.acquire_data_for_coordinates(
            request.lat,
            request.lng,
            request.buffer_km,
            request.data_sources
        )
        
        return {
            "success": result.success,
            "files": result.files,
            "metadata": result.metadata,
            "errors": result.errors,
            "source_used": result.source_used,
            "download_size_mb": result.download_size_mb,
            "processing_time_seconds": result.processing_time_seconds,
            "roi": {
                "center_lat": result.roi.center_lat,
                "center_lng": result.roi.center_lng,
                "buffer_km": result.roi.buffer_km,
                "name": result.roi.name
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/estimate-download-size")
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

@app.get("/api/acquisition-history")
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

@app.post("/api/cleanup-cache")
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

@app.get("/api/storage-stats")
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

@app.post("/api/download-sentinel2")
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
        from .data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
        from .data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
        from .data_acquisition.utils.coordinates import BoundingBox
        
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
            output_format="GeoTIFF"
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

@app.post("/api/convert-sentinel2")
async def convert_sentinel2_images(region_name: str = Form(...)):
    """Convert downloaded Sentinel-2 TIF files to PNG for display"""
    print(f"\n🛰️ API CALL: /api/convert-sentinel2")
    print(f"🏷️ Region name: {region_name}")
    
    try:
        from .convert import convert_sentinel2_to_png
        from pathlib import Path
        
        # Find the data directory for this region
        data_dir = Path("data/acquired") / region_name / "sentinel-2"
        
        if not data_dir.exists():        return {
            "success": False,
            "error_message": f"Sentinel-2 data directory not found: {data_dir}",
            "files": [],
            "errors": []
        }
        
        # Convert TIF files to PNG
        conversion_result = convert_sentinel2_to_png(str(data_dir), region_name)
        
        if conversion_result['success']:
            # Generate base64 encoded images for immediate display
            display_files = []
            for file_info in conversion_result['files']:
                try:
                    from .convert import convert_geotiff_to_png_base64
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

@app.get("/api/overlay/sentinel2/{region_band}")
async def get_sentinel2_overlay_data(region_band: str):
    """Get overlay data for a Sentinel-2 image including bounds and base64 encoded image"""
    print(f"\n🛰️ API CALL: /api/overlay/sentinel2/{region_band}")
    
    try:
        # Parse region_band format: "region_name_band" (e.g., "Portland_Oregon_45.515_-122.678_Red")
        parts = region_band.split('_')
        if len(parts) < 2:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid region_band format. Expected: region_name_band"}
            )
        
        # Extract band (last part) and region name (everything else)
        band_name = parts[-1]  # Red or NIR
        region_name = '_'.join(parts[:-1])
        
        print(f"🏷️ Region: {region_name}")
        print(f"📻 Band: {band_name}")
        
        # Use the existing geo_utils function - treat each sentinel-2 band as a separate "base filename"
        from .geo_utils import get_image_overlay_data
        
        # The geo_utils function expects: base_filename, processing_type, filename_processing_type
        # For Sentinel-2: base_filename = region_name, processing_type = "sentinel-2", filename = band
        overlay_data = get_image_overlay_data(region_name, "sentinel-2", band_name)
        
        if not overlay_data:
            print(f"❌ No overlay data found for Sentinel-2 {band_name} in region {region_name}")
            # Debug: Check what files exist
            from pathlib import Path
            s2_dir = Path("output") / region_name / "sentinel-2"
            if s2_dir.exists():
                files = list(s2_dir.glob("*"))
                print(f"🔍 Files in Sentinel-2 directory: {[f.name for f in files]}")
            else:
                print(f"🔍 Sentinel-2 directory doesn't exist: {s2_dir}")
            
            return JSONResponse(
                status_code=404,
                content={"error": f"Sentinel-2 {band_name} overlay data not found for region {region_name}"}
            )
        
        # Add Sentinel-2 specific metadata
        overlay_data.update({
            "band": band_name,
            "region": region_name,
            "source": "Sentinel-2"
        })
        
        print(f"✅ Sentinel-2 overlay data retrieved successfully")
        print(f"📍 Bounds: {overlay_data['bounds']}")
        
        return overlay_data
        
    except Exception as e:
        print(f"❌ Error in get_sentinel2_overlay_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


