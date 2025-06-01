"""
LIDAR Data Providers

This module contains implementations for various LIDAR data providers.
"""

from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from pathlib import Path

from ..data_acquisition.sources.opentopography import OpenTopographySource
from ..data_acquisition.sources.usgs_3dep import USGS3DEPSource
from ..data_acquisition.sources.base import DataType, DataResolution, DownloadRequest
from ..data_acquisition.utils.coordinates import BoundingBox


class LidarProvider(ABC):
    """Base class for LIDAR data providers."""
    
    def __init__(self, name: str):
        self.name = name
        self.api_key = None
        self.base_url = None
    
    @abstractmethod
    async def download_lidar(
        self,
        lat: float,
        lng: float,
        buffer_km: float,
        output_dir: str,
        progress_callback=None
    ) -> Dict:
        """Download LIDAR data for the specified area."""
        pass
    
    @abstractmethod
    def check_availability(self, lat: float, lng: float) -> bool:
        """Check if data is available for the specified location."""
        pass
    
    @abstractmethod
    def get_coverage_info(self, lat: float, lng: float) -> Dict:
        """Get information about data coverage for the location."""
        pass


class OpenTopographyProvider(LidarProvider):
    """
    OpenTopography LIDAR data provider.
    
    Provides access to high-resolution topographic data including:
    - Airborne LIDAR point clouds
    - Digital elevation models
    - Global datasets
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("OpenTopography")
        self.base_url = "https://cloud.sdsc.edu/v1/opentopoapi"
        self.api_key = api_key
        self._source = OpenTopographySource(api_key)
    
    async def download_lidar(
        self,
        lat: float,
        lng: float,
        buffer_km: float,
        output_dir: str,
        progress_callback=None
    ) -> Dict:
        """Download LIDAR data from OpenTopography."""
        
        if progress_callback:
            await progress_callback({
                "type": "download_started",
                "message": "Starting OpenTopography LIDAR download...",
                "provider": self.name
            })
        
        try:
            # Calculate bounding box from center point and buffer
            bbox = self._calculate_bbox(lat, lng, buffer_km)
            
            # Create download request for LAZ point cloud data
            request = DownloadRequest(
                bbox=bbox,
                data_type=DataType.LAZ,
                resolution=DataResolution.HIGH,
                max_file_size_mb=500.0
            )
            
            # Check availability first
            if not await self._source.check_availability(request):
                return {
                    "success": False,
                    "error": "No LIDAR data available for this location from OpenTopography"
                }
            
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": "Downloading LIDAR point cloud data...",
                    "progress": 50
                })
            
            # Download the data
            result = await self._source.download(request)
            
            if result.success:
                files = [Path(result.file_path).name] if result.file_path else []
                
                download_result = {
                    "success": True,
                    "files": files,
                    "metadata": {
                        "provider": self.name,
                        "resolution": f"{result.resolution_m}m" if result.resolution_m else "1m",
                        "point_density": "2-8 points/m²",
                        "coordinate_system": "WGS84",
                        "file_path": result.file_path,
                        "bbox": {
                            "west": bbox.west,
                            "south": bbox.south,
                            "east": bbox.east,
                            "north": bbox.north
                        }
                    },
                    "file_size_mb": result.file_size_mb or 0.0
                }
                
                if result.metadata:
                    download_result["metadata"].update(result.metadata)
                
                if progress_callback:
                    await progress_callback({
                        "type": "download_completed",
                        "message": "OpenTopography download completed",
                        "files": files
                    })
                
                return download_result
            else:
                return {
                    "success": False,
                    "error": result.error_message or "Download failed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenTopography download error: {str(e)}"
            }
    
    def check_availability(self, lat: float, lng: float) -> bool:
        """Check if OpenTopography has LIDAR data for this location."""
        # OpenTopography LIDAR data is primarily available in the United States
        return -180 <= lng <= -60 and 20 <= lat <= 70
    
    def get_coverage_info(self, lat: float, lng: float) -> Dict:
        """Get coverage information for the location."""
        return {
            "available": self.check_availability(lat, lng),
            "resolution": "0.5-2m",
            "typical_point_density": "2-8 points/m²",
            "coverage_area": "United States, some international",
            "data_format": "LAZ (compressed LAS)"
        }
    
    def _calculate_bbox(self, lat: float, lng: float, buffer_km: float) -> BoundingBox:
        """Calculate bounding box from center point and buffer radius."""
        # Rough conversion: 1 degree ≈ 111 km at equator
        # Adjust for latitude
        import math
        lat_buffer = buffer_km / 111.0
        lng_buffer = buffer_km / (111.0 * math.cos(math.radians(lat)))
        
        return BoundingBox(
            west=lng - lng_buffer,
            south=lat - lat_buffer,
            east=lng + lng_buffer,
            north=lat + lat_buffer
        )


class USGS3DEPProvider(LidarProvider):
    """
    USGS 3D Elevation Program (3DEP) LIDAR data provider.
    
    Provides access to:
    - High-resolution LIDAR point clouds
    - Digital elevation models
    - US-focused coverage
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("USGS_3DEP")
        self.base_url = "https://tnmaccess.nationalmap.gov/api/v1/"
        self.api_key = api_key
        self._source = USGS3DEPSource(api_key)
    
    async def download_lidar(
        self,
        lat: float,
        lng: float,
        buffer_km: float,
        output_dir: str,
        progress_callback=None
    ) -> Dict:
        """Download LIDAR data from USGS 3DEP."""
        
        if progress_callback:
            await progress_callback({
                "type": "download_started", 
                "message": "Starting USGS 3DEP LIDAR download...",
                "provider": self.name
            })
        
        try:
            # Calculate bounding box from center point and buffer
            bbox = self._calculate_bbox(lat, lng, buffer_km)
            
            # Create download request for LAZ point cloud data
            request = DownloadRequest(
                bbox=bbox,
                data_type=DataType.LAZ,
                resolution=DataResolution.HIGH,
                max_file_size_mb=500.0
            )
            
            # Check availability first
            if not await self._source.check_availability(request):
                return {
                    "success": False,
                    "error": "No LIDAR data available for this location from USGS 3DEP"
                }
            
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": "Downloading USGS 3DEP LIDAR data...",
                    "progress": 50
                })
            
            # Download the data
            result = await self._source.download(request)
            
            if result.success:
                files = [Path(result.file_path).name] if result.file_path else []
                
                download_result = {
                    "success": True,
                    "files": files,
                    "metadata": {
                        "provider": self.name,
                        "resolution": f"{result.resolution_m}m" if result.resolution_m else "1m",
                        "point_density": "2-8 points/m²",
                        "coordinate_system": "WGS84",
                        "file_path": result.file_path,
                        "bbox": {
                            "west": bbox.west,
                            "south": bbox.south,
                            "east": bbox.east,
                            "north": bbox.north
                        }
                    },
                    "file_size_mb": result.file_size_mb or 0.0
                }
                
                if result.metadata:
                    download_result["metadata"].update(result.metadata)
                
                if progress_callback:
                    await progress_callback({
                        "type": "download_completed",
                        "message": "USGS 3DEP download completed",
                        "files": files
                    })
                
                return download_result
            else:
                return {
                    "success": False,
                    "error": result.error_message or "Download failed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"USGS 3DEP download error: {str(e)}"
            }
    
    def check_availability(self, lat: float, lng: float) -> bool:
        """Check if USGS 3DEP has data for this location."""
        # USGS 3DEP data is available for US territories only
        return -180 <= lng <= -60 and 20 <= lat <= 70
    
    def get_coverage_info(self, lat: float, lng: float) -> Dict:
        """Get coverage information for the location."""
        return {
            "available": self.check_availability(lat, lng),
            "resolution": "1-2m",
            "typical_point_density": "2-8 points/m²",
            "coverage_area": "United States only",
            "data_format": "LAZ (compressed LAS)"
        }
    
    def _calculate_bbox(self, lat: float, lng: float, buffer_km: float) -> BoundingBox:
        """Calculate bounding box from center point and buffer radius."""
        # Rough conversion: 1 degree ≈ 111 km at equator
        # Adjust for latitude
        import math
        lat_buffer = buffer_km / 111.0
        lng_buffer = buffer_km / (111.0 * math.cos(math.radians(lat)))
        
        return BoundingBox(
            west=lng - lng_buffer,
            south=lat - lat_buffer,
            east=lng + lng_buffer,
            north=lat + lat_buffer
        )


# Provider registry
_PROVIDERS = {
    "opentopography": OpenTopographyProvider,
    "usgs_3dep": USGS3DEPProvider,
}


def get_available_providers() -> List[str]:
    """Get list of available provider names."""
    return list(_PROVIDERS.keys())


def get_provider(name: str, api_key: Optional[str] = None) -> Optional[LidarProvider]:
    """Get a provider instance by name."""
    provider_class = _PROVIDERS.get(name.lower())
    if provider_class:
        return provider_class(api_key)
    return None


def register_provider(name: str, provider_class):
    """Register a new provider class."""
    _PROVIDERS[name.lower()] = provider_class
