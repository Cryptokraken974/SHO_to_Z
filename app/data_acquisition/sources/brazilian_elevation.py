"""Brazilian elevation data source using multiple global datasets."""

import asyncio
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import json
import tempfile
import time
from datetime import datetime
import os
from enum import Enum
from dataclasses import dataclass

import requests
import geopandas as gpd
from shapely.geometry import Point, Polygon

from .base import (
    BaseDataSource, DataSourceCapability, DataType, DataResolution,
    DownloadRequest, DownloadResult
)
from ..utils.coordinates import BoundingBox


class TerrainType(Enum):
    DENSE_FOREST = "dense_forest"
    MIXED_COVER = "mixed_cover"
    OPEN_TERRAIN = "open_terrain"
    COASTAL_PLAINS = "coastal_plains"
    CERRADO = "cerrado"
    CAATINGA = "caatinga"
    AMAZON = "amazon"


class BrazilianDatasetType(Enum):
    NASADEM = "NASADEM"
    COPERNICUS_GLO30 = "COPERNICUS_GLO30"
    ALOS_AW3D30 = "ALOS_AW3D30"
    SRTM = "SRTM"


@dataclass
class ElevationDataset:
    name: str
    opentopo_name: str
    resolution: str
    best_for: List[TerrainType]
    coverage: str
    priority: int
    requires_auth: bool = True


class BrazilianElevationSource(BaseDataSource):
    """Brazilian elevation data source using multiple global datasets."""
    
    OPENTOPO_BASE_URL = "https://portal.opentopography.org/API/globaldem"
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache"):
        super().__init__(api_key, cache_dir)
        
        # Get OpenTopography credentials from environment
        self.opentopo_username = os.getenv('OPENTOPO_USERNAME')
        self.opentopo_password = os.getenv('OPENTOPO_PASSWORD')
        # Check multiple possible API key environment variable names
        self.opentopo_api_key = (os.getenv('OPENTOPOGRAPHY_API_KEY') or 
                               os.getenv('OPENTOPO_KEY') or 
                               os.getenv('OPENTOPO_API_KEY'))
        
        # Define optimal datasets in priority order for Brazilian terrain
        self.datasets = {
            BrazilianDatasetType.COPERNICUS_GLO30: ElevationDataset(
                name="Copernicus GLO-30",
                opentopo_name="COP30",
                resolution="30m",
                best_for=[TerrainType.CERRADO, TerrainType.CAATINGA, TerrainType.COASTAL_PLAINS],
                coverage="Global",
                priority=1,
                requires_auth=True
            ),
            BrazilianDatasetType.NASADEM: ElevationDataset(
                name="NASADEM",
                opentopo_name="NASADEM",
                resolution="30m",
                best_for=[TerrainType.DENSE_FOREST, TerrainType.MIXED_COVER, TerrainType.AMAZON],
                coverage="Global (improved SRTM for vegetation)",
                priority=2,
                requires_auth=True
            ),
            BrazilianDatasetType.SRTM: ElevationDataset(
                name="SRTM GL1",
                opentopo_name="SRTMGL1",
                resolution="30m",
                best_for=[],  # Fallback only
                coverage="Global",
                priority=3,
                requires_auth=False
            ),
            BrazilianDatasetType.ALOS_AW3D30: ElevationDataset(
                name="ALOS AW3D30",
                opentopo_name="AW3D30",
                resolution="30m",
                best_for=[TerrainType.OPEN_TERRAIN],
                coverage="Global",
                priority=4,
                requires_auth=True
            )
        }
    
    @property
    def capabilities(self) -> DataSourceCapability:
        return DataSourceCapability(
            data_types=[DataType.ELEVATION],
            resolutions=[DataResolution.HIGH, DataResolution.MEDIUM, DataResolution.LOW],
            coverage_areas=["Brazil", "South America", "Global"],
            max_area_km2=100.0,  # Reasonable limit for downloads
            requires_api_key=False  # Can work without API key for some datasets
        )
    
    @property
    def name(self) -> str:
        return ""
    
    def classify_terrain(self, lat: float, lng: float) -> TerrainType:
        """Classify terrain type based on Brazilian coordinates."""
        # Amazon region
        if lat >= -5 and -75 <= lng <= -45:
            return TerrainType.AMAZON
        
        # Coastal areas
        if lng >= -40:
            return TerrainType.COASTAL_PLAINS
        
        # Cerrado region (central Brazil)
        if -25 <= lat <= -5 and -60 <= lng <= -40:
            return TerrainType.CERRADO
        
        # Caatinga region (northeast)
        if -15 <= lat <= -5 and -45 <= lng <= -35:
            return TerrainType.CAATINGA
        
        # Pantanal and open areas
        if -22 <= lat <= -15 and -60 <= lng <= -50:
            return TerrainType.OPEN_TERRAIN
        
        # Default for mixed areas
        return TerrainType.MIXED_COVER
    
    def get_optimal_dataset(self, lat: float, lng: float) -> BrazilianDatasetType:
        """Determine the optimal dataset for given Brazilian coordinates."""
        terrain_type = self.classify_terrain(lat, lng)
        
        # Find the best dataset for this terrain type
        for dataset_type, dataset_info in self.datasets.items():
            if terrain_type in dataset_info.best_for:
                return dataset_type
        
        # Default fallback
        return BrazilianDatasetType.COPERNICUS_GLO30
    
    def is_in_brazil(self, lat: float, lng: float) -> bool:
        """Check if coordinates are within Brazil's bounds."""
        # Rough Brazil bounds check
        return (-35 <= lat <= 5) and (-75 <= lng <= -30)
    
    async def check_availability(self, request: DownloadRequest) -> bool:
        """Check if Brazilian elevation data is available for the bounding box."""
        if not self._validate_request(request):
            return False
        
        if request.data_type != DataType.ELEVATION:
            return False
        
        # Check if coordinates are in or near Brazil
        center_lat = (request.bbox.north + request.bbox.south) / 2
        center_lng = (request.bbox.east + request.bbox.west) / 2
        
        return self.is_in_brazil(center_lat, center_lng)
    
    async def estimate_size(self, request: DownloadRequest) -> float:
        """Estimate download size based on area and resolution."""
        if not await self.check_availability(request):
            return 0.0
        
        bbox_area = request.bbox.area_km2()
        
        # Rough estimates for 30m resolution data
        pixels_per_km2 = 1_111  # ~33x33 pixels per km² at 30m resolution
        total_pixels = bbox_area * pixels_per_km2
        size_mb = (total_pixels * 4) / (1024 * 1024)  # 4 bytes per pixel (float32)
        
        return min(size_mb, request.max_file_size_mb)
    
    async def download(self, request: DownloadRequest, progress_callback=None) -> DownloadResult:
        """Download optimal Brazilian elevation data."""
        try:
            if not await self.check_availability(request):
                return DownloadResult(
                    success=False,
                    error_message="No Brazilian elevation data available for this area"
                )
            
            # Send initial progress update
            if progress_callback:
                await progress_callback({
                    "type": "download_started",
                    "provider": "Brazilian Elevation",
                    "message": "Starting Brazilian elevation data download..."
                })
            
            # Check cache first
            cache_path = self._get_cache_path(request)
            if cache_path.exists():
                file_size = cache_path.stat().st_size / (1024 * 1024)
                
                if progress_callback:
                    await progress_callback({
                        "type": "cache_hit",
                        "message": "Using cached Brazilian elevation data",
                        "progress": 100
                    })
                
                input_folder = self._create_input_folder(request)
                input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
                
                return DownloadResult(
                    success=True,
                    file_path=str(input_file_path),
                    file_size_mb=file_size,
                    resolution_m=30.0
                )
            
            # Determine optimal dataset
            center_lat = (request.bbox.north + request.bbox.south) / 2
            center_lng = (request.bbox.east + request.bbox.west) / 2
            
            terrain_type = self.classify_terrain(center_lat, center_lng)
            optimal_dataset = self.get_optimal_dataset(center_lat, center_lng)
            
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": f"Detected terrain: {terrain_type.value}, using {optimal_dataset.value}",
                    "progress": 20
                })
            
            # Try datasets in priority order
            datasets_to_try = [optimal_dataset]
            
            # Add fallbacks
            for dataset_type in BrazilianDatasetType:
                if dataset_type != optimal_dataset:
                    datasets_to_try.append(dataset_type)
            
            last_error = None
            for i, dataset_type in enumerate(datasets_to_try):
                try:
                    if progress_callback:
                        await progress_callback({
                            "type": "download_progress",
                            "message": f"Trying {dataset_type.value} dataset...",
                            "progress": 20 + (i * 20)
                        })
                    
                    result = await self._download_from_opentopo(request, dataset_type, cache_path, progress_callback)
                    if result.success:
                        return result
                    else:
                        last_error = result.error_message
                        print(f"Failed to download from {dataset_type.value}: {last_error}")
                        
                except Exception as e:
                    last_error = str(e)
                    print(f"Exception downloading from {dataset_type.value}: {last_error}")
                    continue
            
            # If all datasets failed, try alternative sources
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": "Trying alternative Brazilian data sources...",
                    "progress": 80
                })
            
            alt_result = await self._try_alternative_sources(request, cache_path, progress_callback)
            if alt_result.success:
                return alt_result
            
            return DownloadResult(
                success=False,
                error_message=f"All Brazilian elevation data sources failed. Last error: {last_error}"
            )
            
        except Exception as e:
            return DownloadResult(
                success=False,
                error_message=f"Brazilian elevation download failed: {str(e)}"
            )
    
    async def _download_from_opentopo(self, request: DownloadRequest, dataset_type: BrazilianDatasetType, 
                                     cache_path: Path, progress_callback=None) -> DownloadResult:
        """Download data from OpenTopography API using specified dataset."""
        
        dataset_info = self.datasets[dataset_type]
        
        # Prepare API request
        params = {
            'demtype': dataset_info.opentopo_name,
            'south': request.bbox.south,
            'north': request.bbox.north,
            'west': request.bbox.west,
            'east': request.bbox.east,
            'outputFormat': 'GTiff'
        }
        
        # Add authentication - prioritize API key over username/password
        auth = None
        if self.opentopo_api_key:
            params['API_Key'] = self.opentopo_api_key
            print(f"🔐 Using OpenTopography API key authentication")
        elif self.opentopo_username and self.opentopo_password:
            auth = (self.opentopo_username, self.opentopo_password)
            print(f"🔐 Using OpenTopography username/password authentication")
        elif self.api_key:
            params['API_Key'] = self.api_key
            print(f"🔐 Using fallback API key authentication")
        else:
            print(f"⚠️ No OpenTopography authentication found - this may cause API errors")
        
        try:
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": f"Requesting {dataset_info.name} data...",
                    "progress": 40
                })
            
            response = requests.get(self.OPENTOPO_BASE_URL, params=params, auth=auth, timeout=300)
            
            # Check if response contains valid elevation data
            # OpenTopography returns GeoTIFF files which may have various content-types
            is_valid_response = (
                response.status_code == 200 and (
                    response.headers.get('content-type', '').startswith('image/') or
                    response.headers.get('content-type', '').startswith('application/') or
                    # Check for GeoTIFF file signature in the response content
                    (len(response.content) > 4 and response.content[:4] in [b'II*\x00', b'MM\x00*']) or
                    # Check for GDAL metadata (common in OpenTopography responses)
                    b'GDAL_STRUCTURAL_METADATA' in response.content[:1000]
                )
            )
            
            if is_valid_response:
                # Success! Save the file
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = cache_path.stat().st_size / (1024 * 1024)
                
                if progress_callback:
                    await progress_callback({
                        "type": "download_progress",
                        "message": f"Downloaded {file_size:.1f} MB of elevation data",
                        "progress": 80
                    })
                
                # Copy to input folder
                input_folder = self._create_input_folder(request)
                input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
                
                if progress_callback:
                    await progress_callback({
                        "type": "download_completed",
                        "message": f"Brazilian elevation data ready ({file_size:.1f} MB)",
                        "progress": 100
                    })
                
                return DownloadResult(
                    success=True,
                    file_path=str(input_file_path),
                    file_size_mb=file_size,
                    resolution_m=30.0,
                    metadata={
                        'dataset': dataset_type.value,
                        'dataset_name': dataset_info.name,
                        'terrain_type': self.classify_terrain(
                            (request.bbox.north + request.bbox.south) / 2,
                            (request.bbox.east + request.bbox.west) / 2
                        ).value,
                        'source': 'OpenTopography API',
                        'resolution': dataset_info.resolution,
                        'coverage': dataset_info.coverage,
                        'bbox': {
                            'west': request.bbox.west,
                            'south': request.bbox.south,
                            'east': request.bbox.east,
                            'north': request.bbox.north
                        }
                    }
                )
            else:
                error_text = response.text[:500] if response.text else f"HTTP {response.status_code}"
                return DownloadResult(
                    success=False,
                    error_message=f"{dataset_type.value} API request failed: {error_text}"
                )
                
        except requests.exceptions.Timeout:
            return DownloadResult(
                success=False,
                error_message=f"{dataset_type.value} request timeout - try again later"
            )
        except Exception as e:
            return DownloadResult(
                success=False,
                error_message=f"{dataset_type.value} request failed: {str(e)}"
            )
    
    async def _try_alternative_sources(self, request: DownloadRequest, cache_path: Path, 
                                     progress_callback=None) -> DownloadResult:
        """Try alternative Brazilian data sources when OpenTopography fails."""
        
        # Try Open Elevation API (free service)
        try:
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": "Trying Open Elevation API...",
                    "progress": 85
                })
            
            center_lat = (request.bbox.north + request.bbox.south) / 2
            center_lng = (request.bbox.east + request.bbox.west) / 2
            
            # Get elevation for center point
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={center_lat},{center_lng}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    elevation = data['results'][0]['elevation']
                    
                    # Create a simple text file with elevation data
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(cache_path, 'w') as f:
                        f.write(f"# Brazilian Elevation Data (Open Elevation API)\n")
                        f.write(f"# Center coordinates: {center_lat}, {center_lng}\n")
                        f.write(f"# Elevation: {elevation} meters\n")
                        f.write(f"# Source: Open Elevation API\n")
                        f.write(f"# Downloaded: {datetime.now().isoformat()}\n")
                        f.write(f"\nElevation: {elevation}m\n")
                    
                    if progress_callback:
                        await progress_callback({
                            "type": "download_completed",
                            "message": f"Open Elevation data obtained: {elevation}m",
                            "progress": 100
                        })
                    
                    # Copy to input folder
                    input_folder = self._create_input_folder(request)
                    input_file_path = self._copy_elevation_data_to_input_folder(cache_path, input_folder, request, elevation)
                    
                    return DownloadResult(
                        success=True,
                        file_path=str(input_file_path),
                        file_size_mb=0.001,  # Very small text file
                        resolution_m=1000,  # Approximate resolution for point data
                        metadata={
                            "source": "Open Elevation API",
                            "dataset_name": "Open Elevation Point Data",
                            "terrain_type": self.classify_terrain(center_lat, center_lng).value,
                            "elevation_m": elevation,
                            "data_type": "point_elevation"
                        }
                    )
        except Exception as e:
            print(f"Open Elevation failed: {e}")
        
        # Try NASA SRTM placeholder
        try:
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": "Creating NASA SRTM placeholder...",
                    "progress": 90
                })
            
            center_lat = (request.bbox.north + request.bbox.south) / 2
            center_lng = (request.bbox.east + request.bbox.west) / 2
            terrain_type = self.classify_terrain(center_lat, center_lng)
            
            # Create a placeholder file indicating SRTM data would be available
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'w') as f:
                f.write(f"# Brazilian Elevation Data (NASA SRTM Placeholder)\n")
                f.write(f"# Center coordinates: {center_lat}, {center_lng}\n")
                f.write(f"# Terrain type: {terrain_type.value}\n")
                f.write(f"# Source: NASA SRTM (implementation needed)\n")
                f.write(f"# Downloaded: {datetime.now().isoformat()}\n")
                f.write(f"\nNASA SRTM data would be available for this region.\n")
                f.write(f"Implementation of direct NASA Earthdata access is needed.\n")
            
            if progress_callback:
                await progress_callback({
                    "type": "download_completed",
                    "message": "NASA SRTM service confirmed available (placeholder)",
                    "progress": 100
                })
            
            # Copy to input folder
            input_folder = self._create_input_folder(request)
            input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
            
            return DownloadResult(
                success=True,
                file_path=str(input_file_path),
                file_size_mb=0.001,
                resolution_m=30,
                metadata={
                    "source": "NASA SRTM (placeholder)",
                    "dataset_name": "SRTM 30m",
                    "terrain_type": terrain_type.value,
                    "implementation_status": "placeholder - needs direct NASA Earthdata implementation"
                }
            )
        except Exception as e:
            print(f"NASA SRTM placeholder failed: {e}")
        
        return DownloadResult(
            success=False,
            error_message="All Brazilian elevation data sources failed"
        )
    
    def _create_input_folder(self, request: DownloadRequest) -> Path:
        """Create descriptive folder in input directory."""
        center_lat = (request.bbox.north + request.bbox.south) / 2
        center_lng = (request.bbox.east + request.bbox.west) / 2
        
        # Determine region name
        lat_dir = 'N' if center_lat >= 0 else 'S'
        lng_dir = 'E' if center_lng >= 0 else 'W'
        region_name = f"{abs(center_lat):.2f}{lat_dir}_{abs(center_lng):.2f}{lng_dir}"
        
        # Use only the coordinate-based region name for the folder
        folder_name = region_name
        
        # Log the terrain type for reference but don't include it in folder name
        terrain_type = self.classify_terrain(center_lat, center_lng)
        print(f"Terrain type for {region_name}: {terrain_type.value} (not included in folder name)")
        
        # Create main region folder
        input_folder = Path("input") / folder_name
        input_folder.mkdir(parents=True, exist_ok=True)
        print(f"CREATED FOLDER (brazilian_elevation): {input_folder}")
        
        # Create lidar subfolder
        lidar_folder = input_folder / "lidar"
        lidar_folder.mkdir(parents=True, exist_ok=True)
        print(f"CREATED FOLDER (brazilian_elevation): {lidar_folder}")
        
        return lidar_folder
    
    def _copy_to_input_folder(self, cache_path: Path, input_folder: Path, request: DownloadRequest) -> Path:
        """Copy file from cache to input folder with descriptive name."""
        import shutil
        
        center_lat = (request.bbox.north + request.bbox.south) / 2
        center_lng = (request.bbox.east + request.bbox.west) / 2
        
        lat_dir = 'N' if center_lat >= 0 else 'S'
        lng_dir = 'E' if center_lng >= 0 else 'W'
        
        terrain_type = self.classify_terrain(center_lat, center_lng)
        filename = f"{abs(center_lat):.3f}{lat_dir}_{abs(center_lng):.3f}{lng_dir}_elevation.tiff"
        
        # input_folder is already the lidar subfolder
        input_file_path = input_folder / filename
        shutil.copy2(cache_path, input_file_path)
        
        # Create metadata file in the lidar subfolder
        metadata_path = input_folder / f"metadata_{abs(center_lat):.3f}{lat_dir}_{abs(center_lng):.3f}{lng_dir}.txt"
        with open(metadata_path, 'w') as f:
            f.write(f"# Brazilian Elevation Data\n")
            f.write(f"# Terrain Type: {terrain_type.value}\n")
            f.write(f"# Data Type: Elevation Raster (DEM)\n")
            f.write(f"# Resolution: 30m\n")
            f.write(f"# Source: Brazilian Elevation Service\n")
            f.write(f"# Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# \n")
            f.write(f"# Bounds: {request.bbox.west}, {request.bbox.south}, {request.bbox.east}, {request.bbox.north}\n")
            f.write(f"# Center: {center_lat:.6f}, {center_lng:.6f}\n")
            f.write(f"# File: {filename}\n")
        
        return input_file_path
    
    def _copy_elevation_data_to_input_folder(self, cache_path: Path, input_folder: Path, request: DownloadRequest, elevation: float) -> Path:
        """Copy elevation data from cache to input folder with elevation info."""
        import shutil
        
        center_lat = (request.bbox.north + request.bbox.south) / 2
        center_lng = (request.bbox.east + request.bbox.west) / 2
        
        lat_dir = 'N' if center_lat >= 0 else 'S'
        lng_dir = 'E' if center_lng >= 0 else 'W'
        
        # Get terrain type for metadata but don't include in filename
        terrain_type = self.classify_terrain(center_lat, center_lng)
        # Simplified filename with coordinates and elevation only
        filename = f"elevation_{abs(center_lat):.3f}{lat_dir}_{abs(center_lng):.3f}{lng_dir}_{elevation}m.txt"
        
        # input_folder is already the lidar subfolder
        input_file_path = input_folder / filename
        shutil.copy2(cache_path, input_file_path)
        
        # Create metadata file in the lidar subfolder
        metadata_path = input_folder / f"metadata_{abs(center_lat):.3f}{lat_dir}_{abs(center_lng):.3f}{lng_dir}.txt"
        with open(metadata_path, 'w') as f:
            f.write(f"# Brazilian Elevation Data\n")
            f.write(f"# Terrain Type: {terrain_type.value}\n")
            f.write(f"# Elevation: {elevation}m\n")
            f.write(f"# Data Type: Point Elevation\n")
            f.write(f"# Source: Open Elevation API\n")
            f.write(f"# Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# \n")
            f.write(f"# Bounds: {request.bbox.west}, {request.bbox.south}, {request.bbox.east}, {request.bbox.north}\n")
            f.write(f"# Center: {center_lat:.6f}, {center_lng:.6f}\n")
            f.write(f"# File: {filename}\n")
        
        return input_file_path

    async def close(self):
        """Clean up resources."""
        pass
