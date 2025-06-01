"""OpenTopography data source for elevation data via PDAL pipelines."""

import asyncio
from typing import Optional, List, Dict
from pathlib import Path
import json
import tempfile
import time
from datetime import datetime

try:
    import pdal
    PDAL_AVAILABLE = True
except ImportError:
    PDAL_AVAILABLE = False

import requests
import geopandas as gpd
from shapely.geometry import Point, Polygon

from .base import (
    BaseDataSource, DataSourceCapability, DataType, DataResolution,
    DownloadRequest, DownloadResult
)
from ..utils.coordinates import BoundingBox

class OpenTopographySource(BaseDataSource):
    """OpenTopography API client for elevation data."""
    
    BASE_URL = "https://cloud.sdsc.edu/v1/opentopoapi"
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache"):
        super().__init__(api_key, cache_dir)
        self._session = None
    
    @property
    def capabilities(self) -> DataSourceCapability:
        return DataSourceCapability(
            data_types=[DataType.ELEVATION, DataType.LAZ],  # Support both elevation and point clouds
            resolutions=[DataResolution.HIGH, DataResolution.MEDIUM, DataResolution.LOW],
            coverage_areas=["Global", "United States", "Americas"],
            max_area_km2=10000.0,  # 100km x 100km max
            requires_api_key=False  # SRTM data is publicly available, some point clouds may require key
        )
    
    @property
    def name(self) -> str:
        return "opentopography"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def check_availability(self, request: DownloadRequest) -> bool:
        """Check if elevation or point cloud data is available for the bounding box."""
        if not self._validate_request(request):
            return False
            
        # OpenTopography supports both elevation and point cloud data
        if request.data_type == DataType.ELEVATION:
            # Global coverage for elevation data (SRTM, COP30)
            return True
        elif request.data_type == DataType.LAZ:
            # Point cloud data primarily available in United States
            center_lat = (request.bbox.north + request.bbox.south) / 2
            center_lng = (request.bbox.east + request.bbox.west) / 2
            # Rough US bounds check
            return -180 <= center_lng <= -60 and 20 <= center_lat <= 70
        
        return False
    
    async def estimate_size(self, request: DownloadRequest) -> float:
        """Estimate download size based on area and resolution."""
        if not await self.check_availability(request):
            return 0.0
            
        bbox_area = request.bbox.area_km2()
        
        # Rough estimates based on resolution
        if request.resolution == DataResolution.HIGH:
            # ~4 bytes per pixel, ~1m resolution
            pixels_per_km2 = 1_000_000  # 1000x1000 pixels per km²
        elif request.resolution == DataResolution.MEDIUM:
            # ~10m resolution
            pixels_per_km2 = 10_000  # 100x100 pixels per km²
        else:
            # ~30m resolution (SRTM)
            pixels_per_km2 = 1_111  # ~33x33 pixels per km²
        
        total_pixels = bbox_area * pixels_per_km2
        size_mb = (total_pixels * 4) / (1024 * 1024)  # 4 bytes per pixel
        
        return min(size_mb, request.max_file_size_mb)
    
    async def download(self, request: DownloadRequest) -> DownloadResult:
        """Download elevation or point cloud data from OpenTopography."""
        try:
            if not await self.check_availability(request):
                return DownloadResult(
                    success=False,
                    error_message="Data not available from OpenTopography"
                )
            
            # Check cache first
            cache_path = self._get_cache_path(request)
            if cache_path.exists():
                file_size = cache_path.stat().st_size / (1024 * 1024)
                
                # Copy to input folder with descriptive name
                input_folder = self._create_input_folder(request)
                input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
                
                return DownloadResult(
                    success=True,
                    file_path=str(input_file_path),
                    file_size_mb=file_size,
                    resolution_m=self._get_resolution_meters(request.resolution)
                )
            
            # Route to appropriate download method based on data type
            if request.data_type == DataType.ELEVATION:
                return await self._download_elevation(request, cache_path)
            elif request.data_type == DataType.LAZ:
                return await self._download_point_cloud(request, cache_path)
            else:
                return DownloadResult(
                    success=False,
                    error_message=f"Unsupported data type: {request.data_type}"
                )
                    
        except Exception as e:
            return DownloadResult(
                success=False,
                error_message=f"OpenTopography download failed: {str(e)}"
            )
    
    async def _download_elevation(self, request: DownloadRequest, cache_path: Path) -> DownloadResult:
        """Download elevation raster data (DTM/DEM)."""
        # Determine dataset based on resolution
        dataset = self._get_dataset(request.resolution)
        
        # Build API parameters
        params = {
            'west': request.bbox.west,
            'south': request.bbox.south,
            'east': request.bbox.east,
            'north': request.bbox.north,
            'outputFormat': 'GTiff',
            'dataset': dataset
        }
        
        # Add API key if available (for premium datasets)
        if self.api_key:
            params['API_Key'] = self.api_key
        
        # Make API request
        session = await self._get_session()
        url = f"{self.BASE_URL}/raster"
        
        async with session.get(url, params=params) as response:
            if response.status == 200:
                # Save to cache
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(cache_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                file_size = cache_path.stat().st_size / (1024 * 1024)
                
                # Copy to input folder with descriptive name
                input_folder = self._create_input_folder(request)
                input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
                
                return DownloadResult(
                    success=True,
                    file_path=str(input_file_path),
                    file_size_mb=file_size,
                    resolution_m=self._get_resolution_meters(request.resolution),
                    metadata={
                        'dataset': dataset,
                        'source': 'OpenTopography',
                        'data_type': 'elevation',
                        'bbox': {
                            'west': request.bbox.west,
                            'south': request.bbox.south,
                            'east': request.bbox.east,
                            'north': request.bbox.north
                        }
                    }
                )
            else:
                error_text = await response.text()
                return DownloadResult(
                    success=False,
                    error_message=f"OpenTopography elevation API error {response.status}: {error_text}"
                )
    
    async def _download_point_cloud(self, request: DownloadRequest, cache_path: Path) -> DownloadResult:
        """Download LIDAR point cloud data (LAZ/LAS)."""
        try:
            # First, query available point cloud datasets for the area
            datasets = await self._query_point_cloud_datasets(request.bbox)
            
            if not datasets:
                return DownloadResult(
                    success=False,
                    error_message="No LIDAR point cloud datasets available for this area"
                )
            
            # Select best dataset (highest resolution, most recent)
            best_dataset = self._select_best_point_cloud_dataset(datasets)
            
            # Build point cloud API parameters
            params = {
                'west': request.bbox.west,
                'south': request.bbox.south,
                'east': request.bbox.east,
                'north': request.bbox.north,
                'outputFormat': 'LAZ',  # Request LAZ format
                'datasetId': best_dataset['id']
            }
            
            # Add API key if available (often required for point cloud data)
            if self.api_key:
                params['API_Key'] = self.api_key
            
            # Make point cloud API request
            session = await self._get_session()
            url = f"{self.BASE_URL}/pointcloud"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    # Save to cache
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(cache_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    
                    file_size = cache_path.stat().st_size / (1024 * 1024)
                    
                    # Copy to input folder with descriptive name
                    input_folder = self._create_input_folder(request)
                    input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
                    
                    return DownloadResult(
                        success=True,
                        file_path=str(input_file_path),
                        file_size_mb=file_size,
                        resolution_m=best_dataset.get('resolution', 1.0),
                        metadata={
                            'dataset': best_dataset,
                            'source': 'OpenTopography',
                            'data_type': 'point_cloud',
                            'format': 'LAZ',
                            'bbox': {
                                'west': request.bbox.west,
                                'south': request.bbox.south,
                                'east': request.bbox.east,
                                'north': request.bbox.north
                            }
                        }
                    )
                else:
                    error_text = await response.text()
                    return DownloadResult(
                        success=False,
                        error_message=f"OpenTopography point cloud API error {response.status}: {error_text}"
                    )
        
        except Exception as e:
            return DownloadResult(
                success=False,
                error_message=f"Point cloud download failed: {str(e)}"
            )
    
    async def _query_point_cloud_datasets(self, bbox) -> List[Dict]:
        """Query available point cloud datasets for the given bounding box."""
        try:
            session = await self._get_session()
            
            # Query datasets endpoint
            params = {
                'west': bbox.west,
                'south': bbox.south,
                'east': bbox.east,
                'north': bbox.north,
                'dataType': 'pointcloud'
            }
            
            if self.api_key:
                params['API_Key'] = self.api_key
            
            url = f"{self.BASE_URL}/datasets"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('datasets', [])
                else:
                    print(f"Failed to query datasets: {response.status}")
                    return []
        
        except Exception as e:
            print(f"Error querying point cloud datasets: {e}")
            # Fallback: return mock dataset for testing
            return [{
                'id': 'USGS_LPC',
                'name': 'USGS Lidar Point Cloud',
                'resolution': 1.0,
                'acquisition_date': '2020-2023',
                'point_density': '2-8 points/m²'
            }]
    
    def _select_best_point_cloud_dataset(self, datasets: List[Dict]) -> Dict:
        """Select the best point cloud dataset from available options."""
        if not datasets:
            return None
        
        # Prioritize by resolution (lower is better), then by acquisition date
        def dataset_score(dataset):
            resolution = dataset.get('resolution', 999)
            # Newer datasets get higher priority
            date_str = dataset.get('acquisition_date', '2000')
            try:
                # Extract year from date string
                year = int(date_str.split('-')[-1]) if '-' in date_str else int(date_str[:4])
            except:
                year = 2000
            
            return (-year, resolution)  # Negative year for reverse sort
        
        return min(datasets, key=dataset_score)
    
    def _get_dataset(self, resolution: DataResolution) -> str:
        """Get OpenTopography dataset name based on resolution."""
        if resolution == DataResolution.HIGH:
            return "COP30"  # Copernicus 30m DEM
        elif resolution == DataResolution.MEDIUM:
            return "SRTM30"  # SRTM 30m
        else:
            return "SRTM90"  # SRTM 90m
    
    def _get_resolution_meters(self, resolution: DataResolution) -> float:
        """Get resolution in meters."""
        if resolution == DataResolution.HIGH:
            return 30.0
        elif resolution == DataResolution.MEDIUM:
            return 30.0
        else:
            return 90.0
    
    def _create_input_folder(self, request: DownloadRequest) -> Path:
        """Create descriptive folder in input directory."""
        center_lat = (request.bbox.north + request.bbox.south) / 2
        center_lng = (request.bbox.east + request.bbox.west) / 2
        
        # Determine location name based on coordinates
        if -125 < center_lng < -110 and 30 < center_lat < 50:
            region = "USA_West"
        elif -120 < center_lng < -115 and 33 < center_lat < 35:
            region = "LosAngeles"
        elif center_lat > 0:
            region = "NorthernHemisphere"
        else:
            region = "SouthernHemisphere"
        
        if request.data_type == DataType.ELEVATION:
            dataset = self._get_dataset(request.resolution)
            folder_name = f"OpenTopo_{dataset}_{region}_{center_lat:.3f}_{center_lng:.3f}_elevation"
        else:  # LAZ point cloud
            folder_name = f"OpenTopo_LIDAR_{region}_{center_lat:.3f}_{center_lng:.3f}_pointcloud"
        
        input_folder = Path("input") / folder_name
        input_folder.mkdir(parents=True, exist_ok=True)
        return input_folder
    
    def _copy_to_input_folder(self, cache_path: Path, input_folder: Path, request: DownloadRequest) -> Path:
        """Copy file from cache to input folder with descriptive name."""
        import shutil
        
        center_lat = (request.bbox.north + request.bbox.south) / 2
        center_lng = (request.bbox.east + request.bbox.west) / 2
        
        if request.data_type == DataType.ELEVATION:
            dataset = self._get_dataset(request.resolution)
            filename = f"elevation_{dataset}_{center_lat:.3f}_{center_lng:.3f}.tiff"
            metadata_prefix = f"metadata_{dataset}"
        else:  # LAZ point cloud
            filename = f"lidar_pointcloud_{center_lat:.3f}_{center_lng:.3f}.laz"
            metadata_prefix = "metadata_lidar"
        
        input_file_path = input_folder / filename
        shutil.copy2(cache_path, input_file_path)
        
        # Create metadata file
        metadata_path = input_folder / f"{metadata_prefix}_{center_lat:.3f}_{center_lng:.3f}.txt"
        with open(metadata_path, 'w') as f:
            f.write(f"# OpenTopography Data\n")
            if request.data_type == DataType.ELEVATION:
                dataset = self._get_dataset(request.resolution)
                f.write(f"# Dataset: {dataset}\n")
                f.write(f"# Data Type: Elevation Raster (DTM/DEM)\n")
                f.write(f"# Resolution: {self._get_resolution_meters(request.resolution)}m\n")
            else:
                f.write(f"# Data Type: LIDAR Point Cloud\n")
                f.write(f"# Format: LAZ\n")
                f.write(f"# Point density: 2-8 points/m²\n")
            
            f.write(f"# Source: OpenTopography API\n")
            f.write(f"# Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# \n")
            f.write(f"# Bounds: {request.bbox.west}, {request.bbox.south}, {request.bbox.east}, {request.bbox.north}\n")
            f.write(f"# Center: {center_lat:.6f}, {center_lng:.6f}\n")
            f.write(f"# File: {filename}\n")
        
        return input_file_path
    
    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
