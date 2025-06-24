"""ORNL DAAC data source for environmental datasets."""

import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

from .base import (
    BaseDataSource, DataSourceCapability, DataType, DataResolution,
    DownloadRequest, DownloadResult
)
from ..utils.coordinates import BoundingBox

class ORNLDAACSource(BaseDataSource):
    """ORNL DAAC (Oak Ridge National Laboratory Distributed Active Archive Center) data source."""
    
    BASE_URL = "https://thredds.daac.ornl.gov"
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache"):
        super().__init__(api_key, cache_dir)
        self._session = None
    
    @property
    def capabilities(self) -> DataSourceCapability:
        return DataSourceCapability(
            data_types=[DataType.ELEVATION, DataType.IMAGERY, DataType.RADAR],
            resolutions=[DataResolution.HIGH, DataResolution.MEDIUM, DataResolution.LOW],
            coverage_areas=["Global", "Brazil", "Americas", "Tropical"],
            max_area_km2=25000.0,  # Large area support
            requires_api_key=False
        )
    
    @property
    def name(self) -> str:
        return "ornl_daac"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def check_availability(self, request: DownloadRequest) -> bool:
        """Check if data is available from ORNL DAAC."""
        if not self._validate_request(request):
            return False
        
        # ORNL DAAC has extensive global coverage, especially for environmental data
        # For Brazil, they have good coverage through various programs
        return True
    
    async def estimate_size(self, request: DownloadRequest) -> float:
        """Estimate download size from ORNL DAAC."""
        if not await self.check_availability(request):
            return 0.0
        
        bbox_area = request.bbox.area_km2()
        
        # Estimate based on data type and resolution
        if request.data_type == DataType.ELEVATION:
            if request.resolution == DataResolution.HIGH:
                size_per_km2 = 5.0  # MB per km²
            else:
                size_per_km2 = 1.0
        elif request.data_type == DataType.IMAGERY:
            if request.resolution == DataResolution.HIGH:
                size_per_km2 = 20.0
            else:
                size_per_km2 = 5.0
        else:  # RADAR
            size_per_km2 = 10.0
        
        estimated_size = bbox_area * size_per_km2
        return min(estimated_size, request.max_file_size_mb)
    
    async def download(self, request: DownloadRequest, progress_callback=None) -> DownloadResult:
        """Download data from ORNL DAAC."""
        try:
            if not await self.check_availability(request):
                return DownloadResult(
                    success=False,
                    error_message="Data not available from ORNL DAAC"
                )
            
            # Check cache first
            cache_path = self._get_cache_path(request)
            if cache_path.exists():
                file_size = cache_path.stat().st_size / (1024 * 1024)
                return DownloadResult(
                    success=True,
                    file_path=str(cache_path),
                    file_size_mb=file_size,
                    resolution_m=self._get_resolution_meters(request.resolution, request.data_type)
                )
            
            # Determine dataset based on data type and region
            dataset_info = self._get_dataset_info(request)
            
            if not dataset_info:
                return DownloadResult(
                    success=False,
                    error_message="No suitable dataset found for request"
                )
            
            # Download the data
            session = await self._get_session()
            download_url = self._build_download_url(dataset_info, request.bbox)
            
            async with session.get(download_url) as response:
                if response.status == 200:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(cache_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    
                    file_size = cache_path.stat().st_size / (1024 * 1024)
                    
                    return DownloadResult(
                        success=True,
                        file_path=str(cache_path),
                        file_size_mb=file_size,
                        resolution_m=self._get_resolution_meters(request.resolution, request.data_type),
                        metadata={
                            'dataset': dataset_info['name'],
                            'source': 'ORNL DAAC',
                            'description': dataset_info.get('description', ''),
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
                        error_message=f"ORNL DAAC API error {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            return DownloadResult(
                success=False,
                error_message=f"ORNL DAAC download failed: {str(e)}"
            )
    
    def _get_dataset_info(self, request: DownloadRequest) -> Optional[Dict[str, Any]]:
        """Get appropriate dataset information based on request."""
        # Brazil-specific datasets
        if self._is_brazil_region(request.bbox):
            if request.data_type == DataType.ELEVATION:
                return {
                    'name': 'SRTM_GL1',
                    'description': 'Shuttle Radar Topography Mission Global 1 arc second',
                    'resolution': 30,
                    'format': 'GeoTIFF'
                }
            elif request.data_type == DataType.IMAGERY:
                return {
                    'name': 'MODIS_Terra',
                    'description': 'MODIS/Terra Surface Reflectance',
                    'resolution': 250,
                    'format': 'HDF'
                }
            elif request.data_type == DataType.RADAR:
                return {
                    'name': 'JERS_SAR',
                    'description': 'JERS-1 SAR Global Rain Forest Mapping',
                    'resolution': 100,
                    'format': 'GeoTIFF'
                }
        
        # Global datasets
        if request.data_type == DataType.ELEVATION:
            return {
                'name': 'ASTER_GDEM',
                'description': 'ASTER Global Digital Elevation Model',
                'resolution': 30,
                'format': 'GeoTIFF'
            }
        
        return None
    
    def _is_brazil_region(self, bbox: BoundingBox) -> bool:
        """Check if bounding box is within Brazil."""
        # Approximate Brazil bounds
        brazil_bounds = {
            'west': -74.0,
            'east': -28.85,
            'south': -33.75,
            'north': 5.27
        }
        
        return (bbox.west >= brazil_bounds['west'] and
                bbox.east <= brazil_bounds['east'] and
                bbox.south >= brazil_bounds['south'] and
                bbox.north <= brazil_bounds['north'])
    
    def _build_download_url(self, dataset_info: Dict[str, Any], bbox: BoundingBox) -> str:
        """Build download URL for ORNL DAAC dataset."""
        # This is a simplified example - actual implementation would depend on
        # specific ORNL DAAC APIs and data access protocols
        dataset_name = dataset_info['name']
        
        # Example URL structure (would need to be adapted for real datasets)
        url = (
            f"{self.BASE_URL}/dodsC/{dataset_name}/"
            f"subset?lat[{bbox.south}:{bbox.north}]&"
            f"lon[{bbox.west}:{bbox.east}]"
        )
        
        return url
    
    def _get_resolution_meters(self, resolution: DataResolution, data_type: DataType) -> float:
        """Get resolution in meters based on data type and resolution level."""
        if data_type == DataType.ELEVATION:
            if resolution == DataResolution.HIGH:
                return 30.0  # SRTM 1 arc-second
            elif resolution == DataResolution.MEDIUM:
                return 90.0  # SRTM 3 arc-second
            else:
                return 1000.0  # Coarse elevation data
        elif data_type == DataType.IMAGERY:
            if resolution == DataResolution.HIGH:
                return 250.0  # MODIS high resolution
            elif resolution == DataResolution.MEDIUM:
                return 500.0  # MODIS medium resolution
            else:
                return 1000.0  # MODIS coarse resolution
        else:  # RADAR
            return 100.0  # Typical SAR resolution
    
    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
