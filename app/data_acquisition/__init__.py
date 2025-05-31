"""
Data Acquisition Module

This module handles downloading and processing of geospatial data from various sources
including LiDAR/LAZ files and satellite imagery (Sentinel-2).

Submodules:
- sources: Data source implementations (OpenTopography, ORNL DAAC, Sentinel-2, etc.)
- utils: Utility functions for coordinate handling, caching, validation
- manager: Main orchestration class for data acquisition workflows
"""

from .manager import DataAcquisitionManager
from .utils.coordinates import CoordinateValidator, CoordinateConverter, BoundingBox
from .utils.cache import DataCache
from .utils.file_manager import FileManager, FileInfo

__all__ = [
    'DataAcquisitionManager',
    'CoordinateValidator',
    'CoordinateConverter', 
    'BoundingBox',
    'DataCache',
    'FileManager',
    'FileInfo'
]
