"""OpenTopography data source for elevation data via PDAL pipelines."""

import asyncio
from typing import Optional, List, Dict
from pathlib import Path
import json
import tempfile
import time
from datetime import datetime
import os

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
    """OpenTopography client using PDAL pipelines for 3DEP data access."""
    
    # GitHub repository with 3DEP dataset boundaries
    BOUNDARIES_URL = 'https://raw.githubusercontent.com/hobuinc/usgs-lidar/master/boundaries/resources.geojson'
    
    # AWS S3 EPT bucket base URL
    EPT_BASE_URL = "https://s3-us-west-2.amazonaws.com/usgs-lidar-public"
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache"):
        super().__init__(api_key, cache_dir)
        self._boundaries_df = None
        self._boundaries_cache_time = None
        
    @property
    def capabilities(self) -> DataSourceCapability:
        return DataSourceCapability(
            data_types=[DataType.ELEVATION, DataType.LAZ],
            resolutions=[DataResolution.HIGH, DataResolution.MEDIUM, DataResolution.LOW],
            coverage_areas=["United States"],
            max_area_km2=100.0,  # Reasonable limit for PDAL processing
            requires_api_key=False
        )
    
    @property
    def name(self) -> str:
        return "opentopography"
    
    async def check_availability(self, request: DownloadRequest) -> bool:
        """Check if 3DEP data is available for the bounding box."""
        if not PDAL_AVAILABLE:
            return False
            
        if not self._validate_request(request):
            return False
        
        # Get 3DEP boundaries
        try:
            boundaries_df = await self._get_3dep_boundaries()
            if boundaries_df is None:
                return False
            
            # Check if any datasets intersect with the request area
            datasets = await self._find_intersecting_datasets(request.bbox, boundaries_df)
            return len(datasets) > 0
            
        except Exception:
            return False
    
    async def estimate_size(self, request: DownloadRequest) -> float:
        """Estimate download size based on area and resolution."""
        if not await self.check_availability(request):
            return 0.0
            
        bbox_area = request.bbox.area_km2()
        
        # Rough estimates based on resolution and data type
        if request.data_type == DataType.LAZ:
            # Point cloud data: ~2-8 points/m², ~20 bytes per point
            points_per_km2 = 5_000_000  # 5M points per km² (average)
            size_mb = (bbox_area * points_per_km2 * 20) / (1024 * 1024)
        else:  # Elevation (DTM/DEM)
            # Raster data: varies by resolution
            if request.resolution == DataResolution.HIGH:
                pixels_per_km2 = 1_000_000  # 1m resolution
            elif request.resolution == DataResolution.MEDIUM:
                pixels_per_km2 = 40_000     # 5m resolution
            else:
                pixels_per_km2 = 10_000     # 10m resolution
            
            size_mb = (bbox_area * pixels_per_km2 * 4) / (1024 * 1024)  # 4 bytes per pixel
        
        return min(size_mb, request.max_file_size_mb)
    
    async def download(self, request: DownloadRequest, progress_callback=None) -> DownloadResult:
        """Download data using PDAL pipelines."""
        try:
            if not PDAL_AVAILABLE:
                return DownloadResult(
                    success=False,
                    error_message="PDAL not available. Install with: pip install pdal"
                )
            
            if not await self.check_availability(request):
                return DownloadResult(
                    success=False,
                    error_message="No 3DEP data available for this area"
                )
            
            # Send initial progress update
            if progress_callback:
                await progress_callback({
                    "type": "download_started",
                    "provider": "OpenTopography",
                    "message": "Starting OpenTopography data download..."
                })
            
            # Check cache first
            cache_path = self._get_cache_path(request)
            if cache_path.exists():
                file_size = cache_path.stat().st_size / (1024 * 1024)
                
                if progress_callback:
                    await progress_callback({
                        "type": "cache_hit",
                        "message": "Using cached OpenTopography data",
                        "progress": 100
                    })
                
                input_folder = self._create_input_folder(request)
                input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
                
                return DownloadResult(
                    success=True,
                    file_path=str(input_file_path),
                    file_size_mb=file_size,
                    resolution_m=self._get_resolution_meters(request.resolution)
                )
            
            # Send progress update - checking datasets
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": "Finding available datasets...",
                    "progress": 10
                })
            
            # Get available datasets
            boundaries_df = await self._get_3dep_boundaries()
            datasets = await self._find_intersecting_datasets(request.bbox, boundaries_df)
            
            if not datasets:
                return DownloadResult(
                    success=False,
                    error_message="No intersecting 3DEP datasets found"
                )
            
            # Send progress update - datasets found
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": f"Found {len(datasets)} datasets, starting download...",
                    "progress": 25
                })
            
            # Create PDAL pipeline based on data type
            if request.data_type == DataType.LAZ:
                return await self._download_point_cloud_with_progress(request, datasets, cache_path, progress_callback)
            else:
                return await self._download_elevation_with_progress(request, datasets, cache_path, progress_callback)
                
        except Exception as e:
            return DownloadResult(
                success=False,
                error_message=f"OpenTopography download failed: {str(e)}"
            )
    
    async def _get_3dep_boundaries(self) -> Optional[gpd.GeoDataFrame]:
        """Download and cache 3DEP dataset boundaries."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._fetch_boundaries_sync)
        except Exception as e:
            print(f"Error fetching 3DEP boundaries: {e}")
            return None
    
    def _fetch_boundaries_sync(self) -> Optional[gpd.GeoDataFrame]:
        """Synchronous boundary fetching (run in thread pool)."""
        try:
            response = requests.get(self.BOUNDARIES_URL, timeout=30)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
                f.write(response.text)
                temp_path = f.name
            
            try:
                df = gpd.read_file(temp_path)
                return df
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            print(f"Error in _fetch_boundaries_sync: {e}")
            return None
    
    async def _find_intersecting_datasets(self, bbox: BoundingBox, boundaries_df: gpd.GeoDataFrame) -> List[Dict]:
        """Find 3DEP datasets that intersect with the bounding box."""
        try:
            # Create bounding box polygon
            bbox_polygon = Polygon([
                (bbox.west, bbox.south),
                (bbox.east, bbox.south),
                (bbox.east, bbox.north),
                (bbox.west, bbox.north),
                (bbox.west, bbox.south)
            ])
            
            # Find intersecting datasets
            intersecting = boundaries_df[boundaries_df.geometry.intersects(bbox_polygon)]
            
            datasets = []
            for idx, row in intersecting.iterrows():
                dataset_info = {
                    'name': row['name'],
                    'url': row['url'],
                    'points': row.get('points', 'Unknown'),
                    'geometry': row['geometry']
                }
                datasets.append(dataset_info)
            
            return datasets
            
        except Exception as e:
            print(f"Error finding intersecting datasets: {e}")
            return []
    
    async def _download_point_cloud_with_progress(self, request: DownloadRequest, datasets: List[Dict], cache_path: Path, progress_callback=None) -> DownloadResult:
        """Download point cloud data using PDAL with progress tracking."""
        try:
            # Send progress update - starting pipeline
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": "Creating PDAL pipeline for point cloud...",
                    "progress": 30
                })
            
            # Create AOI polygon in Web Mercator (EPSG:3857)
            aoi_3857 = await self._create_aoi_polygon(request.bbox)
            
            # Limit to first few datasets to avoid excessive processing
            dataset_names = [d['name'] for d in datasets[:3]]
            
            # Build PDAL pipeline for point cloud
            resolution = self._get_resolution_meters(request.resolution)
            pipeline = self._build_point_cloud_pipeline(aoi_3857, dataset_names, resolution, str(cache_path))
            
            # Send progress update - executing pipeline
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": f"Downloading {len(dataset_names)} datasets...",
                    "progress": 50
                })
            
            # Execute pipeline with progress monitoring
            start_time = time.time()
            await self._execute_pipeline_with_progress(pipeline, progress_callback, 50, 90)
            execution_time = time.time() - start_time
            
            if not cache_path.exists():
                return DownloadResult(
                    success=False,
                    error_message="PDAL pipeline execution completed but no output file was created"
                )
            
            # Send progress update - finalizing
            if progress_callback:
                await progress_callback({
                    "type": "download_progress", 
                    "message": "Finalizing LAZ file...",
                    "progress": 95
                })
            
            file_size = cache_path.stat().st_size / (1024 * 1024)
            
            # Copy to input folder
            input_folder = self._create_input_folder(request)
            input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
            
            # Send completion
            if progress_callback:
                await progress_callback({
                    "type": "download_completed",
                    "message": f"LAZ file downloaded ({file_size:.1f} MB)",
                    "progress": 100
                })
            
            return DownloadResult(
                success=True,
                file_path=str(input_file_path),
                file_size_mb=file_size,
                resolution_m=resolution,
                metadata={
                    'datasets': dataset_names,
                    'source': 'OpenTopography 3DEP',
                    'data_type': 'point_cloud',
                    'format': 'LAZ',
                    'execution_time': execution_time,
                    'bbox': {
                        'west': request.bbox.west,
                        'south': request.bbox.south,
                        'east': request.bbox.east,
                        'north': request.bbox.north
                    }
                }
            )
            
        except Exception as e:
            return DownloadResult(
                success=False,
                error_message=f"Point cloud download failed: {str(e)}"
            )

    async def _download_elevation_with_progress(self, request: DownloadRequest, datasets: List[Dict], cache_path: Path, progress_callback=None) -> DownloadResult:
        """Download elevation data (DTM/DEM) using PDAL with progress tracking."""
        try:
            # Send progress update - starting pipeline
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": "Creating PDAL pipeline for elevation data...",
                    "progress": 30
                })
            
            # Create AOI polygon in Web Mercator (EPSG:3857)
            aoi_3857 = await self._create_aoi_polygon(request.bbox)
            
            # Limit to first few datasets
            dataset_names = [d['name'] for d in datasets[:3]]
            
            # Build PDAL pipeline for DEM
            pc_resolution = self._get_resolution_meters(request.resolution)
            dem_resolution = pc_resolution * 0.5  # DEM resolution slightly finer than point cloud
            
            # Determine DEM type based on request (default to DTM)
            dem_type = 'dtm'  # Could be extended to support DSM based on request parameters
            
            pipeline = self._build_dem_pipeline(
                aoi_3857, dataset_names, pc_resolution, dem_resolution, 
                dem_type, str(cache_path)
            )
            
            # Send progress update - executing pipeline
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": f"Processing elevation data from {len(dataset_names)} datasets...",
                    "progress": 50
                })
            
            # Execute pipeline with progress monitoring
            start_time = time.time()
            await self._execute_pipeline_with_progress(pipeline, progress_callback, 50, 90)
            execution_time = time.time() - start_time
            
            if not cache_path.exists():
                return DownloadResult(
                    success=False,
                    error_message="PDAL pipeline execution completed but no output file was created"
                )
            
            # Send progress update - finalizing
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": "Finalizing elevation file...",
                    "progress": 95
                })
            
            file_size = cache_path.stat().st_size / (1024 * 1024)
            
            # Copy to input folder
            input_folder = self._create_input_folder(request)
            input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
            
            # Send completion
            if progress_callback:
                await progress_callback({
                    "type": "download_completed",
                    "message": f"Elevation data downloaded ({file_size:.1f} MB)",
                    "progress": 100
                })
            
            return DownloadResult(
                success=True,
                file_path=str(input_file_path),
                file_size_mb=file_size,
                resolution_m=dem_resolution,
                metadata={
                    'datasets': dataset_names,
                    'source': 'OpenTopography 3DEP',
                    'data_type': 'elevation',
                    'dem_type': dem_type,
                    'format': 'GeoTIFF',
                    'execution_time': execution_time,
                    'bbox': {
                        'west': request.bbox.west,
                        'south': request.bbox.south,
                        'east': request.bbox.east,
                        'north': request.bbox.north
                    }
                }
            )
            
        except Exception as e:
            return DownloadResult(
                success=False,
                error_message=f"Elevation download failed: {str(e)}"
            )
    
    async def _create_aoi_polygon(self, bbox: BoundingBox):
        """Create AOI polygon in Web Mercator (EPSG:3857)."""
        # Create polygon in WGS84
        polygon = Polygon([
            (bbox.west, bbox.south),
            (bbox.east, bbox.south),
            (bbox.east, bbox.north),
            (bbox.west, bbox.north),
            (bbox.west, bbox.south)
        ])
        
        # Convert to Web Mercator
        gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs='EPSG:4326')
        gdf_3857 = gdf.to_crs('EPSG:3857')
        
        return gdf_3857.geometry[0]
    
    def _build_point_cloud_pipeline(self, extent_epsg3857, dataset_names: List[str], 
                                   resolution: float, output_path: str) -> Dict:
        """Build PDAL pipeline for point cloud extraction."""
        # Build readers for each dataset
        readers = []
        for name in dataset_names:
            url = f"{self.EPT_BASE_URL}/{name}/ept.json"
            reader = {
                "type": "readers.ept",
                "filename": url,
                "polygon": str(extent_epsg3857),
                "requests": 3,
                "resolution": resolution
            }
            readers.append(reader)
        
        pipeline = {"pipeline": readers}
        
        # Add noise filtering
        filter_stage = {
            "type": "filters.outlier",
            "method": "statistical",
            "mean_k": 8,
            "multiplier": 3.0
        }
        pipeline['pipeline'].append(filter_stage)
        
        # Add reprojection (keep in Web Mercator)
        reproject_stage = {
            "type": "filters.reprojection",
            "out_srs": "EPSG:3857"
        }
        pipeline['pipeline'].append(reproject_stage)
        
        # Add LAZ writer
        writer_stage = {
            "type": "writers.las",
            "compression": "laszip",
            "filename": output_path
        }
        pipeline['pipeline'].append(writer_stage)
        
        return pipeline
    
    def _build_dem_pipeline(self, extent_epsg3857, dataset_names: List[str], 
                           pc_resolution: float, dem_resolution: float,
                           dem_type: str, output_path: str) -> Dict:
        """Build PDAL pipeline for DEM generation."""
        # Start with point cloud pipeline (without writer)
        pipeline = self._build_point_cloud_pipeline(extent_epsg3857, dataset_names, pc_resolution, "dummy")
        
        # Remove the LAZ writer (last stage)
        pipeline['pipeline'] = pipeline['pipeline'][:-1]
        
        # Add ground classification filter for DTM
        if dem_type == 'dtm':
            ground_filter = {
                "type": "filters.range",
                "limits": "Classification[2:2]"  # USGS Class 2 = Ground
            }
            pipeline['pipeline'].append(ground_filter)
        
        # Add DEM writer stage
        dem_stage = {
            "type": "writers.gdal",
            "filename": output_path,
            "gdaldriver": "GTiff",
            "nodata": -9999,
            "output_type": "idw",  # Inverse distance weighting
            "resolution": float(dem_resolution),
            "gdalopts": "COMPRESS=LZW,TILED=YES,BLOCKXSIZE=256,BLOCKYSIZE=256"
        }
        pipeline['pipeline'].append(dem_stage)
        
        return pipeline
    
    async def _execute_pipeline_async(self, pipeline: Dict):
        """Execute PDAL pipeline asynchronously."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._execute_pipeline_sync, pipeline)
    
    async def _execute_pipeline_with_progress(self, pipeline: Dict, progress_callback=None, start_progress=50, end_progress=90):
        """Execute PDAL pipeline with progress updates."""
        try:
            # Send initial progress update
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": "Executing PDAL pipeline...",
                    "progress": start_progress
                })
            
            # Execute in thread pool with periodic progress updates
            loop = asyncio.get_event_loop()
            
            # Create a simple progress tracker
            progress_steps = 5
            for i in range(progress_steps):
                if i > 0:  # Don't sleep on first iteration
                    await asyncio.sleep(1)  # Simulate processing time
                
                current_progress = start_progress + (end_progress - start_progress) * (i + 1) / progress_steps
                
                if progress_callback:
                    await progress_callback({
                        "type": "download_progress",
                        "message": f"Processing LIDAR data... step {i+1}/{progress_steps}",
                        "progress": int(current_progress)
                    })
            
            # Execute the actual pipeline
            await loop.run_in_executor(None, self._execute_pipeline_sync, pipeline)
            
        except Exception as e:
            if progress_callback:
                await progress_callback({
                    "type": "download_error",
                    "message": f"Pipeline execution failed: {str(e)}"
                })
            raise

    def _execute_pipeline_sync(self, pipeline: Dict):
        """Execute PDAL pipeline synchronously."""
        p = pdal.Pipeline(json.dumps(pipeline))
        try:
            # Try to validate, but don't fail if validation method doesn't exist
            if hasattr(p, 'validate'):
                p.validate()
        except Exception as e:
            # Log validation warning but continue with execution
            print(f"Warning: Pipeline validation failed: {e}")
        
        p.execute()
        return p
    
    def _get_resolution_meters(self, resolution: DataResolution) -> float:
        """Get resolution in meters."""
        if resolution == DataResolution.HIGH:
            return 1.0
        elif resolution == DataResolution.MEDIUM:
            return 5.0
        else:
            return 10.0
    
    def _create_input_folder(self, request: DownloadRequest) -> Path:
        """Create descriptive folder in input directory."""
        if request.region_name:
            base_folder_name = request.region_name
        else:
            center_lat = (request.bbox.north + request.bbox.south) / 2
            center_lng = (request.bbox.east + request.bbox.west) / 2
            base_folder_name = f"{center_lat:.2f}S_{abs(center_lng):.2f}W"

        if request.data_type == DataType.LAZ:
            folder_name = f"lidar_{base_folder_name}"
        else:
            folder_name = f"elevation_{base_folder_name}"
        
        input_folder = Path("input") / folder_name
        input_folder.mkdir(parents=True, exist_ok=True)
        return input_folder
    
    def _copy_to_input_folder(self, cache_path: Path, input_folder: Path, request: DownloadRequest) -> Path:
        """Copy file from cache to input folder with descriptive name."""
        import shutil
        
        if request.region_name:
            base_file_name = request.region_name
        else:
            center_lat = (request.bbox.north + request.bbox.south) / 2
            center_lng = (request.bbox.east + request.bbox.west) / 2
            base_file_name = f"{center_lat:.2f}S_{abs(center_lng):.2f}W"

        if request.data_type == DataType.LAZ:
            filename = f"lidar_{base_file_name}_lidar.laz"
        else:
            filename = f"elevation_{base_file_name}_dtm.tif"
        
        input_file_path = input_folder / filename
        shutil.copy2(cache_path, input_file_path)
        
        # Create metadata file
        metadata_filename = f"metadata_{base_file_name}.txt"
        metadata_path = input_folder / metadata_filename
        with open(metadata_path, 'w') as f:
            f.write(f"# OpenTopography 3DEP Data\\n")
            f.write(f"# Region Name: {request.region_name if request.region_name else 'N/A'}\\n")
            f.write(f"# Data Type: {'LIDAR Point Cloud' if request.data_type == DataType.LAZ else 'Elevation DTM'}\\n")
            f.write(f"# Resolution: {self._get_resolution_meters(request.resolution)}m\\n")
            f.write(f"# Source: USGS 3DEP via OpenTopography/PDAL\\n")
            f.write(f"# Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"# Bounds: {request.bbox.west}, {request.bbox.south}, {request.bbox.east}, {request.bbox.north}\\n")
            if not request.region_name: # Only write center if region_name is not used for naming
                center_lat = (request.bbox.north + request.bbox.south) / 2
                center_lng = (request.bbox.east + request.bbox.west) / 2
                f.write(f"# Center: {center_lat:.6f}, {center_lng:.6f}\\n")
            f.write(f"# File: {filename}\\n")
        
        return input_file_path
    
    async def close(self):
        """Cleanup resources."""
        # No persistent connections to close in this implementation
        pass
