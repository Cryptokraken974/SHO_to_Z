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
    'ServiceFactory',
    'default_factory'
]
