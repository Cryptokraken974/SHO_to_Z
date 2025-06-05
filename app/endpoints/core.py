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
from datetime import datetime
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

