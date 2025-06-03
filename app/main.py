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
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .convert import convert_geotiff_to_png_base64
from .processing import laz_to_dem, dtm, dsm, chm, hillshade, hillshade_315_45_08, hillshade_225_45_08, slope, aspect, color_relief, tri, tpi, roughness
from .data_acquisition import DataAcquisitionManager
from .lidar_acquisition import LidarAcquisitionManager
from .config import get_settings, validate_api_keys, get_data_source_config

# Get application settings
settings = get_settings()

# Initialize data acquisition manager with settings
data_manager = DataAcquisitionManager(
    cache_dir=settings.cache_dir,
    output_dir=settings.output_dir,
    settings=settings
)

# Initialize LIDAR acquisition manager
lidar_manager = LidarAcquisitionManager(
    cache_dir=settings.cache_dir,
    output_dir=settings.output_dir,
    generate_rasters=True,
    raster_dir=Path(settings.output_dir) / "raster_products"
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
    region_name: Optional[str] = None

class DataAcquisitionRequest(BaseModel):
    lat: float
    lng: float
    buffer_km: float = 1.0
    data_sources: Optional[List[str]] = None
    max_file_size_mb: float = 500.0
    region_name: Optional[str] = None

class Sentinel2Request(BaseModel):
    lat: float
    lng: float
    buffer_km: float = 2.0  # 2km radius = 4km x 4km box (smaller for better processing)
    bands: Optional[List[str]] = ["B04", "B08"]  # Sentinel-2 red and NIR bands
    region_name: Optional[str] = None

class RasterGenerationRequest(BaseModel):
    region_name: str

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
    """List all LAZ files in the input directory with coordinate metadata"""
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
    
    # Extract coordinate metadata for each file
    files_with_metadata = []
    for file_path in relative_files:
        file_info = {"path": file_path}
        
        # Check for OpenTopography metadata file
        file_dir = os.path.dirname(file_path)
        metadata_files = glob.glob(os.path.join(file_dir, "metadata_*.txt"))
        
        if metadata_files:
            try:
                with open(metadata_files[0], 'r') as f:
                    content = f.read()
                    # Extract center coordinates from metadata
                    for line in content.split('\n'):
                        if line.startswith('# Center:'):
                            coords_str = line.split('# Center:')[1].strip()
                            lat, lng = coords_str.split(', ')
                            file_info["center_lat"] = float(lat)
                            file_info["center_lng"] = float(lng)
                            break
            except Exception as e:
                print(f"Error reading metadata for {file_path}: {e}")
        
        # Add hardcoded coordinates for demo files
        filename = os.path.basename(file_path).lower()
        if "foxisland" in filename:
            file_info["center_lat"] = 44.4268
            file_info["center_lng"] = -68.2048
        elif "wizardisland" in filename or "or_wizardisland" in filename:
            file_info["center_lat"] = 42.9446
            file_info["center_lng"] = -122.1090
        else:
            # Try to extract coordinates from filename pattern like "lidar_14.87S_39.38W" or "lidar_23.46S_45.99W_lidar.laz"
            import re
            coord_pattern = r'lidar_(\d+\.\d+)([ns])_(\d+\.\d+)([ew])'
            print(f"Trying to extract coordinates from filename: '{filename}'")
            match = re.search(coord_pattern, filename, re.IGNORECASE)
            if match:
                lat_val, lat_dir, lng_val, lng_dir = match.groups()
                lat = float(lat_val) * (-1 if lat_dir.lower() == 's' else 1)
                lng = float(lng_val) * (-1 if lng_dir.lower() == 'w' else 1)
                file_info["center_lat"] = lat
                file_info["center_lng"] = lng
                print(f"Extracted coordinates from filename '{filename}': {lat}, {lng}")
            else:
                print(f"No coordinate match found for filename: '{filename}'")
        
        files_with_metadata.append(file_info)
    
    return {"files": files_with_metadata}

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
async def api_dtm(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Convert LAZ to DTM (ground points only) - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/dtm")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

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
async def api_dsm(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Convert LAZ to DSM (surface points) - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/dsm")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
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
async def api_chm(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Generate CHM (Canopy Height Model) from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/chm")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
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
async def api_hillshade(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Generate hillshade from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/hillshade")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
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
async def api_hillshade_315_45_08(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Generate hillshade with 315° azimuth, 45° altitude, 0.8 z-factor - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/hillshade_315_45_08")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
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
async def api_hillshade_225_45_08(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Generate hillshade with 225° azimuth, 45° altitude, 0.8 z-factor - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/hillshade_225_45_08")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
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
async def api_slope(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Generate slope from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/slope")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        tif_path = slope(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_slope: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/aspect")
async def api_aspect(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Generate aspect from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/aspect")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        tif_path = aspect(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_aspect: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/color_relief")
async def api_color_relief(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Generate color relief from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/color_relief")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        tif_path = color_relief(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_color_relief: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/tri")
async def api_tri(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Generate TRI from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/tri")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        tif_path = tri(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_tri: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/tpi")
async def api_tpi(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Generate TPI from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/tpi")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        tif_path = tpi(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_tpi: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/roughness")
async def api_roughness(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Generate roughness from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/roughness")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        
        laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")
        
        # Use the first LAZ file found
        input_file = laz_files[0]
        print(f"📥 Using LAZ file: {input_file}")
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        tif_path = roughness(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_roughness: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/chat")
async def api_chat(data: dict):
    prompt = data.get("prompt", "")
    model = data.get("model", "")
    # Placeholder response; integrate with real LLM here
    response = f"Model {model} says: {prompt}"
    return {"response": response}

# Sentinel-2 specific overlay endpoint (must come before general overlay endpoint)
@app.get("/api/overlay/sentinel2/{region_band}")
async def get_sentinel2_overlay_data(region_band: str):
    """Get overlay data for a Sentinel-2 image including bounds and base64 encoded image"""
    print(f"\n🛰️ API CALL: /api/overlay/sentinel2/{region_band}")
    
    try:
        # Parse region_band format: "region_xxx_BAND_BXX" or "region_xxx_NDVI"
        # Examples: "region_10_12S_42_23W_RED_B04", "region_3_13S_58_29W_NIR_B08", "3.10S_57.70W_NDVI"
        # Strategy: Handle NDVI as special case (single part), otherwise split on last 2 parts for band
        parts = region_band.split('_')
        if len(parts) < 2:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid region_band format. Expected: region_xxx_BAND_BXX or region_xxx_NDVI"}
            )
        
        # Check if last part is NDVI (special case)
        if parts[-1] == 'NDVI':
            band_info = 'NDVI'
            region_name = '_'.join(parts[:-1])  # Everything except NDVI
        else:
            # Standard case: take last 2 parts as band_info (RED_B04, NIR_B08)
            if len(parts) < 3:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid region_band format. Expected: region_xxx_BAND_BXX or region_xxx_NDVI"}
                )
            band_info = '_'.join(parts[-2:])  # RED_B04 or NIR_B08
            region_name = '_'.join(parts[:-2])  # region_10_12S_42_23W
        
        print(f"🏷️ Region: {region_name}")
        print(f"📻 Band Info: {band_info}")
        
        # Use the new Sentinel-2 specific function
        from .geo_utils import get_sentinel2_overlay_data_util
        
        # Call Sentinel-2 specific function with region_name and band_info
        overlay_data = get_sentinel2_overlay_data_util(region_name, band_info)
        
        if not overlay_data:
            print(f"❌ No overlay data found for Sentinel-2 {band_info} in region {region_name}")
            # Debug: Check what files exist and suggest alternatives
            from pathlib import Path
            s2_dir = Path("output") / region_name / "sentinel2"
            if s2_dir.exists():
                files = list(s2_dir.glob("*sentinel2*.png")) + list(s2_dir.glob("*NDVI*.png"))
                print(f"🔍 PNG files in Sentinel-2 directory: {[f.name for f in files]}")
                
                # Extract available bands for user guidance
                available_bands = set()
                for f in files:
                    if 'NDVI' in f.name:
                        available_bands.add('NDVI')
                    else:
                        parts = f.name.split('_')
                        if len(parts) >= 2:
                            band = '_'.join(parts[-2:]).replace('.png', '')
                            available_bands.add(band)
                
                error_msg = f"Sentinel2 {band_info} overlay data not found for region {region_name}"
                if available_bands:
                    error_msg += f". Available bands: {sorted(available_bands)}"
                    
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": error_msg,
                        "available_bands": sorted(available_bands),
                        "region": region_name,
                        "requested_band": band_info
                    }
                )
            else:
                print(f"🔍 Sentinel-2 directory doesn't exist: {s2_dir}")
            
            return JSONResponse(
                status_code=404,
                content={"error": f"Sentinel-2 {band_info} overlay data not found for region {region_name}"}
            )
        
        # Add Sentinel-2 specific metadata
        overlay_data.update({
            "band": band_info,
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

@app.get("/api/overlay/{processing_type}/{filename}")
async def get_overlay_data(processing_type: str, filename: str):
    """Get overlay data for a processed image including bounds and base64 encoded image"""
    print(f"\n🗺️  API CALL: /api/overlay/{processing_type}/{filename}")
    
    try:
        from .geo_utils import get_laz_overlay_data
        
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
        
        overlay_data = get_laz_overlay_data(base_filename, actual_processing_type, filename_processing_type)
        
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

@app.get("/api/overlay/raster/{region_name}/{processing_type}")
async def get_raster_overlay_data(region_name: str, processing_type: str):
    """Get overlay data for raster-processed images from regions including bounds and base64 encoded image"""
    print(f"\n🗺️  API CALL: /api/overlay/raster/{region_name}/{processing_type}")
    
    try:
        from .geo_utils import get_image_bounds_from_geotiff, get_image_bounds_from_world_file
        import base64
        import glob
        
        print(f"📂 Region name: {region_name}")
        print(f"🔄 Processing type: {processing_type}")
        
        # Construct path to PNG outputs directory
        png_outputs_dir = f"output/{region_name}/lidar/png_outputs"
        
        if not os.path.exists(png_outputs_dir):
            print(f"❌ PNG outputs directory not found: {png_outputs_dir}")
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"PNG outputs directory not found for region {region_name}"}
            )
        
        # Map processing type to the actual filename pattern
        # Files are named like: 5.988S_36.145W_elevation_hillshade.png
        type_mapping = {
            'hillshade': 'hillshade', 
            'slope': 'slope',
            'aspect': 'aspect',
            'color_relief': 'color_relief',
            'tri': 'TRI',
            'tpi': 'TPI',
            'roughness': 'TRI'  # Default to TRI for roughness, but could also be TPI
        }
        
        filename_pattern = type_mapping.get(processing_type, processing_type)
        
        # Find PNG files matching the pattern: *_elevation_{pattern}.png
        png_pattern = f"{png_outputs_dir}/*_elevation_{filename_pattern}.png"
        png_files = glob.glob(png_pattern)
        
        print(f"🔍 PNG pattern: {png_pattern}")
        print(f"📁 Found PNG files: {png_files}")
        
        if not png_files:
            print(f"❌ No PNG files found matching pattern: {png_pattern}")
            # Debug: List what files actually exist
            if os.path.exists(png_outputs_dir):
                files = os.listdir(png_outputs_dir)
                png_files_available = [f for f in files if f.endswith('.png')]
                print(f"🔍 Available PNG files: {png_files_available}")
            
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"No PNG files found for {processing_type} in region {region_name}"}
            )
        
        # Use the most recent file if multiple exist
        png_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        png_path = png_files[0]
        
        # Derive world file and tiff paths
        base_path = png_path.replace('.png', '')
        world_path = f"{base_path}.wld"
        tiff_path = f"{base_path}.tif"
        
        print(f"🖼️  PNG path: {png_path}")
        print(f"🗺️  TIFF path: {tiff_path}")
        print(f"🌍 World file path: {world_path}")
        
        # Check if files exist
        print(f"📁 PNG exists: {os.path.exists(png_path)}")
        print(f"🗺️  TIFF exists: {os.path.exists(tiff_path)}")
        print(f"🌍 World file exists: {os.path.exists(world_path)}")
        
        if not os.path.exists(png_path):
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"PNG file not found: {png_path}"}
            )
        
        # Try to get bounds from GeoTIFF first, then world file
        bounds = None
        
        if os.path.exists(tiff_path):
            print("🗺️  Trying to extract bounds from GeoTIFF...")
            bounds = get_image_bounds_from_geotiff(tiff_path)
            if bounds:
                print(f"✅ Bounds from GeoTIFF: {bounds}")
            else:
                print("❌ Failed to extract bounds from GeoTIFF")
        
        if not bounds and os.path.exists(world_path):
            print("🌍 Trying to extract bounds from world file...")
            # Get image dimensions from PNG
            from PIL import Image
            with Image.open(png_path) as img:
                width, height = img.size
            print(f"📏 Image dimensions: {width}x{height}")
            
            bounds = get_image_bounds_from_world_file(world_path, width, height, None)
            if bounds:
                print(f"✅ Bounds from world file: {bounds}")
            else:
                print("❌ Failed to extract bounds from world file")
        
        if not bounds:
            print("❌ No coordinate information found")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Could not extract coordinate information from files"}
            )
        
        # Read and encode PNG image
        print("🖼️  Reading and encoding PNG image...")
        with open(png_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        print(f"✅ Successfully prepared raster overlay data")
        overlay_data = {
            'success': True,
            'bounds': bounds,
            'image_data': image_data,
            'processing_type': processing_type,
            'region_name': region_name,
            'filename': os.path.basename(png_path)
        }
        
        return overlay_data
        
    except Exception as e:
        print(f"❌ Error getting raster overlay data: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to get raster overlay data: {str(e)}"}
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

# LIDAR Data Acquisition Endpoints

@app.post("/api/acquire-lidar")
async def acquire_lidar_data(request: dict):
    """Acquire LIDAR data from external providers"""
    print(f"\n📡 API CALL: /api/acquire-lidar")
    
    try:
        lat = request.get("lat")
        lng = request.get("lng")
        buffer_km = request.get("buffer_km", 2.0)
        provider = request.get("provider", "auto")
        
        print(f"📍 Coordinates: {lat}, {lng}")
        print(f"📏 Buffer: {buffer_km} km")
        print(f"🏢 Provider: {provider}")
        
        # Validate coordinates
        if not lat or not lng:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Latitude and longitude are required"
                }
            )
        
        # Use the LIDAR acquisition manager
        result = await lidar_manager.acquire_lidar_data(
            lat=float(lat),
            lng=float(lng),
            buffer_km=float(buffer_km),
            provider=provider,
            progress_callback=manager.send_progress_update
        )
        
        print(f"✅ LIDAR acquisition completed successfully")
        return result
        
    except Exception as e:
        print(f"❌ Error in acquire_lidar_data: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Send error update
        await manager.send_progress_update({
            "type": "lidar_acquisition_error",
            "message": f"Error acquiring LIDAR data: {str(e)}",
            "error": str(e)
        })
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/lidar/providers")
async def list_lidar_providers():
    """List available LIDAR data providers"""
    print(f"\n📋 API CALL: /api/lidar/providers")
    
    try:
        from .lidar_acquisition.providers import get_available_providers, get_provider
        
        providers = get_available_providers()
        provider_info = []
        
        for provider_name in providers:
            provider = get_provider(provider_name)
            if provider:
                # Get sample coverage info (using Portland, OR as example)
                coverage = provider.get_coverage_info(45.5152, -122.6784)
                provider_info.append({
                    "name": provider.name,
                    "id": provider_name,
                    "coverage_info": coverage
                })
        
        return {
            "success": True,
            "providers": provider_info,
            "count": len(provider_info)
        }
        
    except Exception as e:
        print(f"❌ Error listing LIDAR providers: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.post("/api/process-lidar")
async def process_lidar_data(region_name: str = Form(...)):
    """Process acquired LIDAR data into LAZ format"""
    print(f"\n🔄 API CALL: /api/process-lidar")
    print(f"🏷️ Region: {region_name}")
    
    try:
        # Extract coordinates from region name (format: lidar_LAT_LNG)
        # Example: "lidar_23.46S_45.99W" -> lat=-23.46, lng=-45.99
        try:
            parts = region_name.replace("lidar_", "").split("_")
            if len(parts) >= 2:
                lat_str = parts[0]
                lng_str = parts[1]
                
                # Parse latitude
                if lat_str.endswith('S'):
                    lat = -float(lat_str[:-1])
                elif lat_str.endswith('N'):
                    lat = float(lat_str[:-1])
                else:
                    lat = float(lat_str)
                
                # Parse longitude
                if lng_str.endswith('W'):
                    lng = -float(lng_str[:-1])
                elif lng_str.endswith('E'):
                    lng = float(lng_str[:-1])
                else:
                    lng = float(lng_str)
                
                print(f"📍 Parsed coordinates from region name: {lat}, {lng}")
                
                # Use the LIDAR acquisition manager to download real data
                print(f"🔄 Downloading real LIDAR data for coordinates {lat}, {lng}")
                
                async def progress_callback(data):
                    """Forward progress updates to WebSocket clients"""
                    await manager.send_progress_update(data)
                
                result = await lidar_manager.acquire_lidar_data(
                    lat=lat,
                    lng=lng,
                    buffer_km=2.0,
                    provider="auto",
                    progress_callback=progress_callback
                )
                
                print(f"✅ Real LIDAR data acquisition completed successfully")
                return result
                
            else:
                print(f"⚠️ Unable to parse coordinates from region name: {region_name}")
                
        except Exception as coord_error:
            print(f"⚠️ Error parsing coordinates from region name {region_name}: {coord_error}")
        
        # Fallback: Create mock LAZ files if coordinate parsing fails
        print(f"🔄 Falling back to mock LIDAR data creation")
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Create mock LAZ files in the input directory
        input_dir = "input"
        region_dir = os.path.join(input_dir, region_name)
        os.makedirs(region_dir, exist_ok=True)
        
        # Create a placeholder LAZ file (this would be real LIDAR data in production)
        laz_filename = f"{region_name}_lidar.laz"
        laz_filepath = os.path.join(region_dir, laz_filename)
        
        # Create an empty file as placeholder
        with open(laz_filepath, 'w') as f:
            f.write("# Placeholder LAZ file - would contain actual LIDAR point cloud data\n")
        
        result = {
            "success": True,
            "files": [laz_filename],
            "region_name": region_name,
            "processing_summary": {
                "points_processed": 2500000,
                "files_merged": 1,
                "coordinate_system": "WGS84",
                "compression_ratio": "85%"
            }
        }
        
        print(f"✅ LIDAR processing (mock) completed successfully")
        return result
        
    except Exception as e:
        print(f"❌ Error in process_lidar_data: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
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

# ============================================================================
# OPTIMAL ELEVATION DATA API ENDPOINTS
# ============================================================================

# Import optimal elevation downloader
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from optimal_elevation_downloader import OptimalElevationDownloader, DatasetType, TerrainType
    OPTIMAL_ELEVATION_AVAILABLE = True
except ImportError:
    OPTIMAL_ELEVATION_AVAILABLE = False
    print("Warning: optimal_elevation_downloader not available")

# Initialize optimal elevation downloader if available
if OPTIMAL_ELEVATION_AVAILABLE:
    try:
        optimal_elevation_downloader = OptimalElevationDownloader()
    except Exception as e:
        print(f"Warning: Could not initialize optimal elevation downloader: {e}")
        OPTIMAL_ELEVATION_AVAILABLE = False

class ElevationRequest(BaseModel):
    region_key: str
    force_dataset: Optional[str] = None

@app.get("/api/elevation/regions")
async def get_elevation_regions():
    """Get list of Brazilian regions with terrain classification and optimal datasets"""
    if not OPTIMAL_ELEVATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Optimal elevation service not available")
    
    try:
        regions = {}
        for region_key, region_info in optimal_elevation_downloader.brazilian_regions.items():
            optimal_dataset = optimal_elevation_downloader.get_optimal_dataset(region_key)
            dataset_info = optimal_elevation_downloader.datasets[optimal_dataset]
            
            regions[region_key] = {
                "name": region_info["name"],
                "state": region_info["state"],
                "coordinates": {
                    "lat": region_info["lat"],
                    "lng": region_info["lng"]
                },
                "terrain": region_info["terrain"].value,
                "optimal_dataset": {
                    "type": optimal_dataset.value,
                    "name": dataset_info.name,
                    "resolution": dataset_info.resolution,
                    "priority": dataset_info.priority,
                    "requires_auth": dataset_info.requires_auth
                }
            }
        
        return {
            "success": True,
            "regions": regions,
            "total_regions": len(regions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/elevation/datasets")
async def get_elevation_datasets():
    """Get information about available elevation datasets"""
    if not OPTIMAL_ELEVATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Optimal elevation service not available")
    
    try:
        datasets = {}
        for dataset_type, dataset_info in optimal_elevation_downloader.datasets.items():
            datasets[dataset_type.value] = {
                "name": dataset_info.name,
                "opentopo_name": dataset_info.opentopo_name,
                "resolution": dataset_info.resolution,
                "coverage": dataset_info.coverage,
                "priority": dataset_info.priority,
                "requires_auth": dataset_info.requires_auth,
                "best_for": [terrain.value for terrain in dataset_info.best_for]
            }
        
        return {
            "success": True,
            "datasets": datasets,
            "total_datasets": len(datasets)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/elevation/terrain-recommendations")
async def get_terrain_recommendations():
    """Get terrain-based dataset recommendations"""
    if not OPTIMAL_ELEVATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Optimal elevation service not available")
    
    try:
        recommendations = optimal_elevation_downloader.get_terrain_recommendations()
        return {
            "success": True,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/elevation/status")
async def get_elevation_status():
    """Get optimal elevation system status and configuration"""
    if not OPTIMAL_ELEVATION_AVAILABLE:
        return {
            "success": False,
            "available": False,
            "error": "Optimal elevation downloader not available"
        }
    
    try:
        # Check authentication status
        api_key = optimal_elevation_downloader.config.get('opentopography', 'api_key', fallback='')
        username = optimal_elevation_downloader.config.get('opentopography', 'username', fallback='')
        password = optimal_elevation_downloader.config.get('opentopography', 'password', fallback='')
        
        auth_configured = bool(api_key or (username and password))
        
        return {
            "success": True,
            "available": True,
            "configuration": {
                "auth_configured": auth_configured,
                "regions_configured": len(optimal_elevation_downloader.brazilian_regions),
                "datasets_available": len(optimal_elevation_downloader.datasets),
                "terrain_types_supported": len(TerrainType),
                "config_file": str(optimal_elevation_downloader.base_path / "elevation_config.ini")
            },
            "auth_status": "configured" if auth_configured else "not_configured",
            "setup_url": "https://portal.opentopography.org/"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/elevation/download")
async def download_elevation_data(request: ElevationRequest):
    """Download optimal elevation data for a Brazilian region"""
    if not OPTIMAL_ELEVATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Optimal elevation service not available")
    
    try:
        # Validate region
        if request.region_key not in optimal_elevation_downloader.brazilian_regions:
            available_regions = list(optimal_elevation_downloader.brazilian_regions.keys())
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown region: {request.region_key}. Available regions: {available_regions}"
            )
        
        # Parse force_dataset if provided
        force_dataset = None
        if request.force_dataset:
            try:
                force_dataset = DatasetType(request.force_dataset)
            except ValueError:
                valid_datasets = [dt.value for dt in DatasetType]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid dataset: {request.force_dataset}. Valid datasets: {valid_datasets}"
                )
        
        # Download elevation data
        result = optimal_elevation_downloader.download_elevation_data(
            request.region_key, 
            force_dataset=force_dataset
        )
        
        if result["success"]:
            return {
                "success": True,
                "region": request.region_key,
                "dataset": result.get("dataset"),
                "file_path": result.get("file_path"),
                "file_size_mb": result.get("file_size_mb"),
                "resolution": result.get("resolution"),
                "source": result.get("source"),
                "bbox": result.get("bbox")
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Download failed")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/elevation/download-all")
async def download_all_elevation_data():
    """Download optimal elevation data for all Brazilian regions"""
    if not OPTIMAL_ELEVATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Optimal elevation service not available")
    
    try:
        results = optimal_elevation_downloader.download_all_regions()
        
        return {
            "success": True,
            "results": results,
            "summary": results["summary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# END OPTIMAL ELEVATION DATA API ENDPOINTS  
# ============================================================================

# ============================================================================
# RASTER GENERATION API ENDPOINTS
# ============================================================================

@app.post("/api/generate-rasters")
async def generate_rasters(request: RasterGenerationRequest):
    """Generate raster products from elevation TIFF files in a region"""
    try:
        print(f"\n🎨 API CALL: /api/generate-rasters")
        print(f"🏷️ Region: {request.region_name}")
        
        # Import the raster generation service
        from .api_raster_generation import generate_rasters_for_region
        
        # Create progress callback that sends updates via WebSocket
        async def progress_callback(update):
            await manager.send_progress_update({
                "source": "raster_generation",
                "region_name": request.region_name,
                **update
            })
        
        # Send initial progress update
        await progress_callback({
            "type": "raster_generation_started",
            "message": f"Starting raster generation for region: {request.region_name}",
            "progress": 0
        })
        
        # Generate raster products
        result = await generate_rasters_for_region(request.region_name)
        
        if result['success']:
            # Send completion update
            await progress_callback({
                "type": "raster_generation_completed",
                "message": f"Raster generation completed successfully for {request.region_name}",
                "progress": 100,
                "products_generated": result['products_generated'],
                "total_products": result['total_products']
            })
            
            return {
                "success": True,
                "region_name": request.region_name,
                "products_generated": result['products_generated'],
                "png_outputs": result['png_outputs'],
                "total_products": result['total_products'],
                "processing_time": result['processing_time'],
                "message": f"Generated {result['total_products']} raster products for region {request.region_name}",
                "errors": result.get('errors', [])
            }
        else:
            # Send error update
            error_messages = result.get('errors', ['Unknown error'])
            error_text = '; '.join(error_messages)
            await progress_callback({
                "type": "raster_generation_error",
                "message": f"Raster generation failed: {error_text}",
                "progress": 0
            })
            
            raise HTTPException(
                status_code=400,
                detail=error_text
            )
    
    except HTTPException:
        raise
    except Exception as e:
        # Send error update via WebSocket if possible
        try:
            await manager.send_progress_update({
                "source": "raster_generation",
                "region_name": request.region_name,
                "type": "raster_generation_error",
                "message": f"Raster generation error: {str(e)}"
            })
        except:
            pass
        
        print(f"❌ Error in generate_rasters: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Raster generation failed: {str(e)}")

# ============================================================================
# END RASTER GENERATION API ENDPOINTS
# ============================================================================

@app.post("/api/elevation/download-coordinates")
async def download_elevation_coordinates(request: CoordinateRequest):
    """Download elevation data (GeoTIFF) for specific coordinates using optimal source"""
    try:
        # Validate coordinates
        if not (-90 <= request.lat <= 90):
            raise HTTPException(status_code=400, detail=f"Invalid latitude: {request.lat}. Must be between -90 and 90.")
        if not (-180 <= request.lng <= 180):
            raise HTTPException(status_code=400, detail=f"Invalid longitude: {request.lng}. Must be between -180 and 180.")
        
        # Import required modules
        import uuid
        from .data_acquisition.sources.opentopography import OpenTopographySource
        from .data_acquisition.sources.brazilian_elevation import BrazilianElevationSource
        from .data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
        from .data_acquisition.utils.coordinates import BoundingBox
        
        # Generate unique download ID
        download_id = str(uuid.uuid4())
        
        # Create bounding box with buffer
        buffer_deg = request.buffer_km / 111  # Rough conversion: 1 degree ≈ 111 km
        bbox = BoundingBox(
            west=request.lng - buffer_deg,
            south=request.lat - buffer_deg,
            east=request.lng + buffer_deg,
            north=request.lat + buffer_deg
        )
        
        print(f"🌍 Downloading elevation data for coordinates: {request.lat:.4f}, {request.lng:.4f}")
        print(f"🔲 BBox: West={bbox.west:.4f}, South={bbox.south:.4f}, East={bbox.east:.4f}, North={bbox.north:.4f}")
        print(f"📐 Size: {(bbox.east-bbox.west)*111:.2f}km x {(bbox.north-bbox.south)*111:.2f}km")
        
        # Create download request for elevation data
        download_request = DownloadRequest(
            bbox=bbox,
            data_type=DataType.ELEVATION,  # Request elevation instead of LAZ
            resolution=DataResolution.HIGH,
            max_file_size_mb=100.0,
            output_format="GeoTIFF",
            region_name=request.region_name
        )
        
        # Choose optimal source based on coordinates
        brazilian_source = BrazilianElevationSource()
        is_brazilian_coords = brazilian_source.is_in_brazil(request.lat, request.lng)
        
        if is_brazilian_coords:
            # Use Brazilian elevation source for Brazilian coordinates
            elevation_source = brazilian_source
            source_name = "Brazilian Elevation"
            terrain_type = elevation_source.classify_terrain(request.lat, request.lng)
            optimal_dataset = elevation_source.get_optimal_dataset(request.lat, request.lng)
            print(f"🇧🇷 Using Brazilian elevation source - Terrain: {terrain_type.value}, Dataset: {optimal_dataset.value}")
        else:
            # Use OpenTopography for US/other coordinates
            elevation_source = OpenTopographySource()
            source_name = "OpenTopography 3DEP"
            print(f"🇺🇸 Using OpenTopography source for non-Brazilian coordinates")
        
        # Create progress callback that sends updates via WebSocket
        async def progress_callback(update):
            await manager.send_progress_update({
                "source": "elevation_data",
                "coordinates": {"lat": request.lat, "lng": request.lng},
                "download_id": download_id,
                "data_source": source_name,
                **update
            })
        
        # Register download task for potential cancellation
        manager.add_download_task(download_id, elevation_source)
        
        # Check availability first
        available = await elevation_source.check_availability(download_request)
        if not available:
            # Clean up download registration
            manager.cancel_download(download_id)
            
            if is_brazilian_coords:
                error_msg = f"No Brazilian elevation data available for coordinates {request.lat:.4f}, {request.lng:.4f}"
            else:
                error_msg = f"No elevation data available for coordinates {request.lat:.4f}, {request.lng:.4f}"
            
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Send initial progress
        await progress_callback({
            "type": "download_started",
            "message": f"Starting {source_name} elevation data download...",
            "progress": 0
        })
        
        # Download elevation data
        result = await elevation_source.download(download_request, progress_callback)
        
        # Clean up download registration
        manager.cancel_download(download_id)
        
        if result.success:
            # Send final success message
            await progress_callback({
                "type": "download_completed",
                "message": f"Elevation data downloaded successfully ({result.file_size_mb:.1f} MB)",
                "progress": 100,
                "file_path": result.file_path
            })
            
            # Generate raster products automatically
            if result.success and result.file_path:
                try:
                    from .processing.raster_generation import RasterGenerator
                    from pathlib import Path
                    
                    # Initialize raster generator
                    output_dir = Path(result.file_path).parent.parent
                    raster_generator = RasterGenerator(output_base_dir=str(output_dir))
                    
                    # Send raster generation started message
                    await progress_callback({
                        "type": "raster_generation_started",
                        "message": "Generating raster products automatically...",
                        "progress": 0
                    })
                    
                    # Process the elevation TIFF file
                    raster_result = await raster_generator.process_single_tiff(
                        Path(result.file_path),
                        progress_callback=progress_callback
                    )
                    
                    if raster_result and raster_result.get("success", False):
                        await progress_callback({
                            "type": "raster_generation_completed",
                            "message": f"Raster products generated successfully",
                            "progress": 100,
                            "products": raster_result.get("products", []),
                            "png_outputs": raster_result.get("png_outputs", [])
                        })
                    
                except Exception as e:
                    print(f"⚠️ Automatic raster generation failed: {str(e)}")
                    # Log the error but don't fail the overall request
                    await progress_callback({
                        "type": "raster_generation_error",
                        "message": f"Automatic raster generation failed: {str(e)}",
                        "error": str(e)
                    })
            
            # Prepare response with source-specific information
            response_data = {
                "success": True,
                "coordinates": {"lat": request.lat, "lng": request.lng},
                "file_path": result.file_path,
                "file_size_mb": round(result.file_size_mb, 2),
                "resolution_m": result.resolution_m or 30.0,
                "data_type": "elevation",
                "format": "GeoTIFF",
                "source": source_name,
                "download_id": download_id,
                "region_name": request.region_name
            }
            
            # Add Brazilian-specific metadata if applicable
            if is_brazilian_coords and result.metadata:
                response_data.update({
                    "terrain_type": result.metadata.get("terrain_type"),
                    "dataset": result.metadata.get("dataset"),
                    "dataset_name": result.metadata.get("dataset_name")
                })
            
            return response_data
        else:
            await progress_callback({
                "type": "download_error",
                "message": f"Elevation download failed: {result.error_message}",
                "progress": 0
            })
            raise HTTPException(status_code=500, detail=result.error_message)
    
    except HTTPException:
        raise
    except Exception as e:
        # Send error message via WebSocket if possible
        try:
            await manager.send_progress_update({
                "source": "elevation_data", 
                "coordinates": {"lat": request.lat, "lng": request.lng},
                "download_id": download_id,
                "type": "download_error",
                "message": f"Elevation download error: {str(e)}"
            })
        except:
            pass
        
        # Clean up download registration
        try:
            manager.cancel_download(download_id)
        except:
            pass
            
        raise HTTPException(status_code=500, detail=f"Elevation download failed: {str(e)}")

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

@app.post("/api/convert-sentinel2")
async def convert_sentinel2_images(region_name: str = Form(...)):
    """Convert downloaded Sentinel-2 TIF files to PNG for display"""
    print(f"\n🛰️ API CALL: /api/convert-sentinel2")
    print(f"🏷️ Region name: {region_name}")
    
    try:
        from .convert import convert_sentinel2_to_png
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

@app.get("/api/list-regions")
async def list_regions():
    """List all region subdirectories in the output directory and LAZ files from the input directory with coordinate metadata"""
    output_dir = settings.output_dir  # Use output_dir from settings
    input_dir = "input"
    
    regions_with_metadata = []
    
    # First, check output directory for processed regions
    if os.path.exists(output_dir):
        region_folders = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
        
        for region_name in region_folders:
            region_info = {"name": region_name, "source": "output"}
            
            # Attempt to find metadata for center coordinates
            # Check for Sentinel-2 metadata first (more likely to have it from recent downloads)
            sentinel_metadata_path = os.path.join(output_dir, region_name, "sentinel2", "metadata.json")
            lidar_metadata_path_ot = os.path.join(output_dir, region_name, "lidar", f"metadata_{region_name}.txt") # OpenTopography
            lidar_metadata_path_usgs = os.path.join(output_dir, region_name, "lidar", f"info_{region_name}.json") # USGS

            try:
                if os.path.exists(sentinel_metadata_path):
                    with open(sentinel_metadata_path, 'r') as f:
                        metadata = json.load(f)
                        if "bbox" in metadata and len(metadata["bbox"]) == 4:
                            # Calculate center from bbox [west, south, east, north]
                            west, south, east, north = metadata["bbox"]
                            region_info["center_lat"] = (south + north) / 2
                            region_info["center_lng"] = (west + east) / 2
                elif os.path.exists(lidar_metadata_path_ot):
                    with open(lidar_metadata_path_ot, 'r') as f:
                        content = f.read()
                        for line in content.split('\\n'):
                            if line.startswith('# Center:'):
                                coords_str = line.split('# Center:')[1].strip()
                                lat, lng = coords_str.split(', ')
                                region_info["center_lat"] = float(lat)
                                region_info["center_lng"] = float(lng)
                                break
                elif os.path.exists(lidar_metadata_path_usgs):
                     with open(lidar_metadata_path_usgs, 'r') as f:
                        metadata = json.load(f)
                        if "center_lat" in metadata and "center_lon" in metadata:
                            region_info["center_lat"] = metadata["center_lat"]
                            region_info["center_lng"] = metadata["center_lon"]
                        elif "bbox" in metadata and len(metadata["bbox"]) == 4: # Assuming [minx, miny, maxx, maxy]
                            minx, miny, maxx, maxy = metadata["bbox"]
                            region_info["center_lat"] = (miny + maxy) / 2
                            region_info["center_lng"] = (minx + maxx) / 2

            except Exception as e:
                print(f"Error reading metadata for region {region_name}: {e}")

            regions_with_metadata.append(region_info)
    
    # Second, check input directory for LAZ files and Sentinel-2 folders
    if os.path.exists(input_dir):
        # First, find Sentinel-2 download folders (folders with coordinate patterns in their names)
        import re
        coord_folder_pattern = r'(\d+\.\d+)([ns])_(\d+\.\d+)([ew])'
        
        for item in os.listdir(input_dir):
            item_path = os.path.join(input_dir, item)
            if os.path.isdir(item_path):
                # Check if folder name matches coordinate pattern (e.g., "11.31S_44.06W")
                match = re.search(coord_folder_pattern, item, re.IGNORECASE)
                if match:
                    lat_val, lat_dir, lng_val, lng_dir = match.groups()
                    lat = float(lat_val) * (-1 if lat_dir.lower() == 's' else 1)
                    lng = float(lng_val) * (-1 if lng_dir.lower() == 'w' else 1)
                    
                    region_info = {
                        "name": item,
                        "source": "input", 
                        "folder_path": os.path.relpath(item_path),
                        "center_lat": lat,
                        "center_lng": lng
                    }
                    regions_with_metadata.append(region_info)
                    print(f"Found Sentinel-2 folder '{item}' with coordinates: {lat}, {lng}")
        
        # Then, find all LAZ files (including .laz and .copc.laz)
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
        
        # Extract coordinate metadata for each file
        for file_path in relative_files:
            region_name = os.path.splitext(os.path.basename(file_path))[0]
            region_info = {"name": region_name, "source": "input", "file_path": file_path}
            
            # Check for OpenTopography metadata file
            file_dir = os.path.dirname(file_path)
            metadata_files = glob.glob(os.path.join(file_dir, "metadata_*.txt"))
            
            if metadata_files:
                try:
                    with open(metadata_files[0], 'r') as f:
                        content = f.read()
                        # Extract center coordinates from metadata
                        for line in content.split('\n'):
                            if line.startswith('# Center:'):
                                coords_str = line.split('# Center:')[1].strip()
                                lat, lng = coords_str.split(', ')
                                region_info["center_lat"] = float(lat)
                                region_info["center_lng"] = float(lng)
                                break
                except Exception as e:
                    print(f"Error reading metadata for {file_path}: {e}")
            
            # Add hardcoded coordinates for demo files
            filename = os.path.basename(file_path).lower()
            if "foxisland" in filename:
                region_info["center_lat"] = 44.4268
                region_info["center_lng"] = -68.2048
            elif "wizardisland" in filename or "or_wizardisland" in filename:
                region_info["center_lat"] = 42.9446
                region_info["center_lng"] = -122.1090
            else:
                # Try to extract coordinates from filename pattern like "lidar_14.87S_39.38W" or "lidar_23.46S_45.99W_lidar.laz"
                coord_pattern = r'lidar_(\d+\.\d+)([ns])_(\d+\.\d+)([ew])'
                print(f"Trying to extract coordinates from filename: '{filename}'")
                match = re.search(coord_pattern, filename, re.IGNORECASE)
                if match:
                    lat_val, lat_dir, lng_val, lng_dir = match.groups()
                    lat = float(lat_val) * (-1 if lat_dir.lower() == 's' else 1)
                    lng = float(lng_val) * (-1 if lng_dir.lower() == 'w' else 1)
                    region_info["center_lat"] = lat
                    region_info["center_lng"] = lng
                    print(f"Extracted coordinates from filename '{filename}': {lat}, {lng}")
                else:
                    print(f"No coordinate match found for filename: '{filename}'")
            
            regions_with_metadata.append(region_info)
        
    regions_with_metadata.sort(key=lambda x: x["name"])
    return {"regions": regions_with_metadata}

@app.delete("/api/delete-region/{region_name}")
async def delete_region(region_name: str):
    """Delete a region by removing its input and output folders"""
    try:
        import shutil
        from pathlib import Path
        
        # Define the paths to the region folders
        input_folder = Path("input") / region_name
        output_folder = Path("output") / region_name
        
        deleted_folders = []
        
        # Delete input folder if it exists
        if input_folder.exists() and input_folder.is_dir():
            shutil.rmtree(input_folder)
            deleted_folders.append(str(input_folder))
        
        # Delete output folder if it exists
        if output_folder.exists() and output_folder.is_dir():
            shutil.rmtree(output_folder)
            deleted_folders.append(str(output_folder))
        
        if deleted_folders:
            return {
                "success": True,
                "message": f"Region '{region_name}' deleted successfully",
                "deleted_folders": deleted_folders
            }
        else:
            return {
                "success": False,
                "message": f"Region '{region_name}' not found",
                "deleted_folders": []
            }
    except Exception as e:
        import traceback
        print(f"Error deleting region {region_name}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to delete region: {str(e)}")

async def progress_callback_wrapper(progress_data: dict, region_name: Optional[str] = None):
    """Wraps the progress callback to include region_name if available."""
    if region_name:
        progress_data['region_name'] = region_name
    await manager.send_progress_update(progress_data)

# ============================================================================
# REGION IMAGES API ENDPOINT
# ============================================================================

@app.get("/api/regions/{region_name}/images")
async def get_region_images(region_name: str):
    """Get list of available PNG images for a region"""
    print(f"\n🖼️ API CALL: /api/regions/{region_name}/images")
    
    try:
        images = []
        
        # Check LiDAR raster products directory
        lidar_png_dir = f"output/{region_name}/lidar/png_outputs"
        if os.path.exists(lidar_png_dir):
            print(f"📂 Checking LiDAR PNG directory: {lidar_png_dir}")
            
            for png_file in glob.glob(f"{lidar_png_dir}/*.png"):
                file_name = os.path.basename(png_file)
                file_size = os.path.getsize(png_file)
                
                # Extract processing type from filename
                # Pattern: region_name_elevation_processing_type.png
                processing_type = "Unknown"
                if "_elevation_" in file_name:
                    parts = file_name.split("_elevation_")
                    if len(parts) > 1:
                        processing_type = parts[1].replace(".png", "")
                        processing_type = processing_type.replace("_", " ").title()
                
                images.append({
                    "name": file_name,
                    "path": png_file,
                    "type": "lidar",
                    "processing_type": processing_type,
                    "size": f"{file_size / (1024*1024):.1f} MB" if file_size > 1024*1024 else f"{file_size / 1024:.1f} KB"
                })
        
        # Check Sentinel-2 directory
        sentinel2_dir = f"output/{region_name}/sentinel2"
        if os.path.exists(sentinel2_dir):
            print(f"📂 Checking Sentinel-2 directory: {sentinel2_dir}")
            
            for png_file in glob.glob(f"{sentinel2_dir}/*.png"):
                file_name = os.path.basename(png_file)
                file_size = os.path.getsize(png_file)
                
                # Extract band type from filename
                # Pattern: region_name_timestamp_sentinel2_BAND.png or region_name_timestamp_NDVI.png
                band_type = "Unknown"
                if "_sentinel2_" in file_name:
                    parts = file_name.split("_sentinel2_")
                    if len(parts) > 1:
                        band_type = parts[1].replace(".png", "")
                elif "_NDVI.png" in file_name:
                    band_type = "NDVI"
                
                images.append({
                    "name": file_name,
                    "path": png_file,
                    "type": "sentinel2",
                    "processing_type": band_type,
                    "size": f"{file_size / (1024*1024):.1f} MB" if file_size > 1024*1024 else f"{file_size / 1024:.1f} KB"
                })
        
        # Sort images by type and name
        images.sort(key=lambda x: (x["type"], x["name"]))
        
        print(f"✅ Found {len(images)} images for region {region_name}")
        return {"images": images, "region_name": region_name, "total_images": len(images)}
        
    except Exception as e:
        print(f"❌ Error getting region images: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get region images: {str(e)}"}
        )

# ============================================================================
# END REGION IMAGES API ENDPOINT
# ============================================================================


