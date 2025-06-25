from fastapi import FastAPI, Request, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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
from .processing import laz_to_dem, dtm, dsm, chm, hillshade, hillshade_315_45_08, hillshade_225_45_08, slope, aspect, color_relief, tpi, roughness
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
    buffer_km: float = 12.5
    data_types: Optional[List[str]] = None
    region_name: Optional[str] = None

class DataAcquisitionRequest(BaseModel):
    lat: float
    lng: float
    buffer_km: float = 12.5
    data_sources: Optional[List[str]] = None
    max_file_size_mb: float = 500.0
    region_name: Optional[str] = None

class Sentinel2Request(BaseModel):
    lat: float
    lng: float
    buffer_km: float = 12.5  # 12.5km radius = 25km x 25km box (optimal for Copernicus)
    bands: Optional[List[str]] = ["B04", "B08"]  # Sentinel-2 red and NIR bands
    region_name: Optional[str] = None

class RasterGenerationRequest(BaseModel):
    region_name: str

app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001", "http://127.0.0.1:8001"],  # Frontend server URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/output", StaticFiles(directory="output"), name="output")
app.mount("/llm", StaticFiles(directory="llm"), name="llm")

# Include routers from endpoint modules
from .endpoints.core import router as core_router
from .endpoints.chat import router as chat_router
from .endpoints.json_pipelines import router as json_pipelines_router
from .endpoints.laz_processing import router as laz_router
from .endpoints.overlays import router as overlays_router
from .endpoints.prompts import router as prompts_router
from .endpoints.openai_interaction import router as openai_router
from .endpoints.density_processing import router as density_router
# from .endpoints.lidar_acquisition import router as lidar_router
# from .endpoints.data_acquisition import router as data_router
from .endpoints.elevation_api import router as elevation_router
from .endpoints.region_management import router as region_router
from .endpoints.saved_places import router as saved_places_router
from .endpoints.sentinel2 import router as sentinel2_router
from .endpoints.geotiff import router as geotiff_router
from .endpoints.laz import router as laz_file_router
from .endpoints.cache_management import router as cache_router
from .endpoints.visual_lexicon import router as visual_lexicon_router
from .endpoints.copernicus_dsm import router as copernicus_dsm_router
from .endpoints.true_dsm import router as true_dsm_router
from .endpoints.anomaly_reports import router as anomaly_reports_router
from .endpoints import results # Import the new results router

app.include_router(core_router)
app.include_router(chat_router)
app.include_router(json_pipelines_router)
app.include_router(laz_router)
app.include_router(overlays_router)
app.include_router(density_router)
# app.include_router(lidar_router)
# app.include_router(data_router)
app.include_router(elevation_router)
app.include_router(region_router)
app.include_router(saved_places_router)
app.include_router(sentinel2_router)
app.include_router(geotiff_router)
app.include_router(laz_file_router)
app.include_router(cache_router)
app.include_router(visual_lexicon_router)
app.include_router(copernicus_dsm_router)
app.include_router(true_dsm_router)
app.include_router(anomaly_reports_router)
app.include_router(prompts_router)
app.include_router(openai_router)
app.include_router(results.router) # Include the results router

# Global exception handlers to ensure proper JSON responses
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Convert ValueError to proper HTTP 400 response with JSON"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    """Convert FileNotFoundError to proper HTTP 404 response with JSON"""
    return JSONResponse(
        status_code=404,
        content={"detail": f"File not found: {str(exc)}"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Convert unhandled exceptions to proper HTTP 500 response with JSON"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )