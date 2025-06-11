"""
Service Factory

Provides convenient factory methods for creating and managing API services.
"""

from typing import Dict, Any, Optional
from .base_service import BaseService
from .region_service import RegionService
from .geotiff_service import GeotiffService
from .processing_service import ProcessingService
from .overlay_service import OverlayService
from .saved_places_service import SavedPlacesService
from .satellite_service import SatelliteService
from .elevation_service import ElevationService
from .region_analysis_service import RegionAnalysisService
from .laz_service import LAZService
from .cache_service import CacheService
from .data_acquisition_service import DataAcquisitionService
from .lidar_acquisition_service import LidarAcquisitionService
from .pipeline_service import PipelineService
from .chat_service import ChatService
from .core_service import CoreService


class ServiceFactory:
    """Factory class for creating and managing API services"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self._services: Dict[str, BaseService] = {}
    
    def get_region_service(self) -> RegionService:
        """Get or create RegionService instance"""
        if 'region' not in self._services:
            self._services['region'] = RegionService(self.base_url)
        return self._services['region']
    
    def get_geotiff_service(self) -> GeotiffService:
        """Get or create GeotiffService instance"""
        if 'geotiff' not in self._services:
            self._services['geotiff'] = GeotiffService(self.base_url)
        return self._services['geotiff']
    
    def get_processing_service(self) -> ProcessingService:
        """Get or create ProcessingService instance"""
        if 'processing' not in self._services:
            self._services['processing'] = ProcessingService(self.base_url)
        return self._services['processing']
    
    def get_overlay_service(self) -> OverlayService:
        """Get or create OverlayService instance"""
        if 'overlay' not in self._services:
            self._services['overlay'] = OverlayService(self.base_url)
        return self._services['overlay']
    
    def get_saved_places_service(self) -> SavedPlacesService:
        """Get or create SavedPlacesService instance"""
        if 'saved_places' not in self._services:
            self._services['saved_places'] = SavedPlacesService(self.base_url)
        return self._services['saved_places']
    
    def get_satellite_service(self) -> SatelliteService:
        """Get or create SatelliteService instance"""
        if 'satellite' not in self._services:
            self._services['satellite'] = SatelliteService(self.base_url)
        return self._services['satellite']
    
    def get_elevation_service(self) -> ElevationService:
        """Get or create ElevationService instance"""
        if 'elevation' not in self._services:
            self._services['elevation'] = ElevationService(self.base_url)
        return self._services['elevation']
    
    def get_region_analysis_service(self) -> RegionAnalysisService:
        """Get or create RegionAnalysisService instance"""
        if 'region_analysis' not in self._services:
            self._services['region_analysis'] = RegionAnalysisService(self.base_url)
        return self._services['region_analysis']
    
    def get_laz_service(self) -> LAZService:
        """Get or create LAZService instance"""
        if 'laz' not in self._services:
            self._services['laz'] = LAZService(self.base_url)
        return self._services['laz']
    
    def get_cache_service(self) -> CacheService:
        """Get or create CacheService instance"""
        if 'cache' not in self._services:
            self._services['cache'] = CacheService(self.base_url)
        return self._services['cache']
    
    def get_data_acquisition_service(self) -> DataAcquisitionService:
        """Get or create DataAcquisitionService instance"""
        if 'data_acquisition' not in self._services:
            self._services['data_acquisition'] = DataAcquisitionService(self.base_url)
        return self._services['data_acquisition']
    
    def get_lidar_acquisition_service(self) -> LidarAcquisitionService:
        """Get or create LidarAcquisitionService instance"""
        if 'lidar_acquisition' not in self._services:
            self._services['lidar_acquisition'] = LidarAcquisitionService(self.base_url)
        return self._services['lidar_acquisition']
    
    def get_pipeline_service(self) -> PipelineService:
        """Get or create PipelineService instance"""
        if 'pipeline' not in self._services:
            self._services['pipeline'] = PipelineService(self.base_url)
        return self._services['pipeline']
    
    def get_chat_service(self) -> ChatService:
        """Get or create ChatService instance"""
        if 'chat' not in self._services:
            self._services['chat'] = ChatService(self.base_url)
        return self._services['chat']
    
    def get_core_service(self) -> CoreService:
        """Get or create CoreService instance"""
        if 'core' not in self._services:
            self._services['core'] = CoreService(self.base_url)
        return self._services['core']

    async def close_all(self):
        """Close all service connections"""
        for service in self._services.values():
            await service.close()
        self._services.clear()
    
    def close_all_sync(self):
        """Close all service connections synchronously"""
        for service in self._services.values():
            service.close_sync()
        self._services.clear()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_all_sync()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_all()


# Convenience functions for quick service access
def create_region_service(base_url: str = "http://localhost:8000") -> RegionService:
    """Create a RegionService instance"""
    return RegionService(base_url)

def create_processing_service(base_url: str = "http://localhost:8000") -> ProcessingService:
    """Create a ProcessingService instance"""
    return ProcessingService(base_url)

def create_elevation_service(base_url: str = "http://localhost:8000") -> ElevationService:
    """Create an ElevationService instance"""
    return ElevationService(base_url)

def create_satellite_service(base_url: str = "http://localhost:8000") -> SatelliteService:
    """Create a SatelliteService instance"""
    return SatelliteService(base_url)

def create_overlay_service(base_url: str = "http://localhost:8000") -> OverlayService:
    """Create an OverlayService instance"""
    return OverlayService(base_url)

def create_saved_places_service(base_url: str = "http://localhost:8000") -> SavedPlacesService:
    """Create a SavedPlacesService instance"""
    return SavedPlacesService(base_url)

def create_geotiff_service(base_url: str = "http://localhost:8000") -> GeotiffService:
    """Create a GeotiffService instance"""
    return GeotiffService(base_url)

def create_region_analysis_service(base_url: str = "http://localhost:8000") -> RegionAnalysisService:
    """Create a RegionAnalysisService instance"""
    return RegionAnalysisService(base_url)

def create_laz_service(base_url: str = "http://localhost:8000") -> LAZService:
    """Create a LAZService instance"""
    return LAZService(base_url)

def create_cache_service(base_url: str = "http://localhost:8000") -> CacheService:
    """Create a CacheService instance"""
    return CacheService(base_url)

def create_data_acquisition_service(base_url: str = "http://localhost:8000") -> DataAcquisitionService:
    """Create a DataAcquisitionService instance"""
    return DataAcquisitionService(base_url)

def create_lidar_acquisition_service(base_url: str = "http://localhost:8000") -> LidarAcquisitionService:
    """Create a LidarAcquisitionService instance"""
    return LidarAcquisitionService(base_url)

def create_pipeline_service(base_url: str = "http://localhost:8000") -> PipelineService:
    """Create a PipelineService instance"""
    return PipelineService(base_url)

def create_chat_service(base_url: str = "http://localhost:8000") -> ChatService:
    """Create a ChatService instance"""
    return ChatService(base_url)

def create_core_service(base_url: str = "http://localhost:8000") -> CoreService:
    """Create a CoreService instance"""
    return CoreService(base_url)


# Global service factory instance
default_factory = ServiceFactory()

# Convenience aliases
regions = default_factory.get_region_service
processing = default_factory.get_processing_service
elevation = default_factory.get_elevation_service
satellite = default_factory.get_satellite_service
overlays = default_factory.get_overlay_service
saved_places = default_factory.get_saved_places_service
geotiff = default_factory.get_geotiff_service
analysis = default_factory.get_region_analysis_service
laz = default_factory.get_laz_service
cache = default_factory.get_cache_service
data_acquisition = default_factory.get_data_acquisition_service
lidar_acquisition = default_factory.get_lidar_acquisition_service
pipelines = default_factory.get_pipeline_service
chat = default_factory.get_chat_service
core = default_factory.get_core_service
laz = default_factory.get_laz_service
