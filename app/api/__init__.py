"""
API Service Layer

This module provides an implementation-agnostic service layer for the frontend
to interact with backend endpoints. It acts as middleware for better flexibility
and maintainability.

Services:
- region_service: Region management operations
- geotiff_service: GeoTIFF file operations
- processing_service: LIDAR processing operations
- overlay_service: Overlay and image operations
- saved_places_service: Saved places management
- satellite_service: Satellite data operations
- elevation_service: Elevation data operations
- region_analysis_service: Region analysis operations
- laz_service: LAZ file operations and analysis
- cache_service: Cache management operations
- data_acquisition_service: Data acquisition workflow operations
- lidar_acquisition_service: LIDAR data acquisition operations
- pipeline_service: Pipeline management operations
- chat_service: Chat and AI interaction operations
- core_service: Core application operations

Factory:
- factory: ServiceFactory for managing service instances
"""

from .base_service import BaseService, ServiceError, SyncServiceMixin
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
from .openai_service import OpenAIService
from .factory import ServiceFactory, default_factory

__all__ = [
    'BaseService',
    'ServiceError',
    'SyncServiceMixin',
    'RegionService',
    'GeotiffService', 
    'ProcessingService',
    'OverlayService',
    'SavedPlacesService',
    'SatelliteService',
    'ElevationService',
    'RegionAnalysisService',
    'LAZService',
    'CacheService',
    'DataAcquisitionService',
    'LidarAcquisitionService',
    'PipelineService',
    'ChatService',
    'CoreService',
    'OpenAIService',
    'ServiceFactory',
    'default_factory'
]
