"""
Data Acquisition Manager

Main orchestration class that coordinates data acquisition from multiple sources
based on user-provided coordinates and preferences.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from .sources.opentopography import OpenTopographySource
from .sources.ornl_daac import ORNLDAACSource
from .sources.sentinel2 import Sentinel2Source
from .sources.usgs_3dep import USGS3DEPSource
from .utils.coordinates import CoordinateValidator, CoordinateConverter
from .utils.cache import DataCache
from .utils.file_manager import FileManager
from .utils.errors import (
    DataAcquisitionError, CoordinateError, DataNotAvailableError,
    setup_logging, log_error, log_acquisition_attempt, log_acquisition_success,
    error_tracker
)

# Setup logging
logger = setup_logging()

@dataclass
class RegionOfInterest:
    """Represents a region of interest defined by coordinates and buffer"""
    center_lat: float
    center_lng: float
    buffer_km: float
    name: Optional[str] = None
    
    def __post_init__(self):
        if self.name is None:
            self.name = f"ROI_{self.center_lat:.4f}_{self.center_lng:.4f}"

@dataclass
class DataAvailability:
    """Information about data availability for a region"""
    high_res_lidar: bool = False
    srtm_dem: bool = True
    sentinel2: bool = True
    landsat: bool = True
    source_priorities: Dict[str, int] = None
    
    def __post_init__(self):
        if self.source_priorities is None:
            self.source_priorities = {
                'high_res_lidar': 1,
                'srtm_30m': 2,
                'srtm_90m': 3,
                'aster_gdem': 4
            }

@dataclass
class AcquisitionResult:
    """Result of a data acquisition operation"""
    success: bool
    roi: RegionOfInterest
    files: Dict[str, str]  # data_type -> file_path
    metadata: Dict[str, Any]
    errors: List[str]
    source_used: str
    download_size_mb: float = 0.0
    processing_time_seconds: float = 0.0

class DataAcquisitionManager:
    """
    Main class for coordinating data acquisition from multiple sources
    """
    
    def __init__(
        self, 
        cache_dir: str = "./data_cache", 
        output_dir: str = "./acquired_data",
        settings: Optional[Any] = None
    ):
        """
        Initialize the Data Acquisition Manager
        
        Args:
            cache_dir: Directory for caching downloaded data
            output_dir: Directory for storing processed output files
            settings: Application settings object
        """
        self.cache_dir = cache_dir
        self.output_dir = output_dir
        self.settings = settings
        
        # Initialize components
        self.coordinate_validator = CoordinateValidator()
        self.coordinate_converter = CoordinateConverter()
        self.cache = DataCache(cache_dir)
        self.file_manager = FileManager(output_dir)
        
        # Initialize data sources with API keys from settings
        self.sources = {}
        try:
            if settings:
                opentopo_key = getattr(settings, 'opentopography_api_key', None)
                copernicus_user = getattr(settings, 'copernicus_username', None)
                copernicus_pass = getattr(settings, 'copernicus_password', None)
                earthdata_key = getattr(settings, 'earthdata_username', None)
                
                self.sources['opentopography'] = OpenTopographySource(
                    api_key=opentopo_key, 
                    cache_dir=cache_dir
                )
                self.sources['sentinel2'] = Sentinel2Source()
                self.sources['ornl_daac'] = ORNLDAACSource(
                    api_key=earthdata_key,
                    cache_dir=cache_dir
                )
            else:
                # Initialize without API keys
                self.sources['opentopography'] = OpenTopographySource(cache_dir=cache_dir)
                self.sources['usgs_3dep'] = USGS3DEPSource(cache_dir=cache_dir)
                self.sources['sentinel2'] = Sentinel2Source()
                self.sources['ornl_daac'] = ORNLDAACSource(cache_dir=cache_dir)
                
        except Exception as e:
            log_error(logger, e, "Failed to initialize data sources")
            # Fallback initialization
            self.sources = {
                'opentopography': OpenTopographySource(cache_dir=cache_dir),
                'usgs_3dep': USGS3DEPSource(cache_dir=cache_dir),
                'sentinel2': Sentinel2Source(),
                'ornl_daac': ORNLDAACSource(cache_dir=cache_dir)
            }
        
        # Ensure directories exist
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"DataAcquisitionManager initialized with cache: {cache_dir}, output: {output_dir}")
    
    async def check_availability(self, lat: float, lng: float) -> DataAvailability:
        """
        Check what data is available for a given location
        
        Args:
            lat: Latitude in decimal degrees
            lng: Longitude in decimal degrees
            
        Returns:
            DataAvailability object with information about available datasets
        """
        from .sources.base import DownloadRequest, DataType, DataResolution
        
        # Validate coordinates
        if not self.coordinate_validator.validate_coordinates(lat, lng):
            raise ValueError(f"Invalid coordinates: {lat}, {lng}")
        
        availability = DataAvailability()
        
        # Check if coordinates are in Brazil (for specialized handling)
        is_brazil = self.coordinate_validator.is_in_brazil(lat, lng)
        
        # Create bounding box for availability check
        bbox = self.coordinate_converter.create_bounding_box(lat, lng, 1.0)
        
        # Check each source for availability
        for source_name, source in self.sources.items():
            try:
                if source_name == 'opentopography':
                    request = DownloadRequest(bbox=bbox, data_type=DataType.ELEVATION)
                    source_availability = await source.check_availability(request)
                    if source_availability:
                        availability.srtm_dem = True
                        
                elif source_name == 'usgs_3dep':
                    # Check for both LAZ and elevation data
                    request = DownloadRequest(bbox=bbox, data_type=DataType.LAZ)
                    if await source.check_availability(request):
                        availability.high_res_lidar = True
                    
                    request = DownloadRequest(bbox=bbox, data_type=DataType.ELEVATION)
                    if await source.check_availability(request):
                        availability.srtm_dem = True
                        
                elif source_name == 'sentinel2':
                    request = DownloadRequest(bbox=bbox, data_type=DataType.IMAGERY)
                    source_availability = await source.check_availability(request)
                    if source_availability:
                        availability.sentinel2 = True
                        
            except Exception as e:
                logger.warning(f"Error checking availability for {source_name}: {e}")
        
        # Special handling for Brazil
        if is_brazil:
            # Add Brazil-specific data sources
            availability.source_priorities.update({
                'ibge_lidar': 1,
                'inpe_data': 2
            })
        
        return availability
    
    async def acquire_data_for_coordinates(self, lat: float, lng: float, buffer_km: float = 1.0, 
                                   data_sources: Optional[List[str]] = None, progress_callback=None) -> AcquisitionResult:
        """
        Acquire data for a specific coordinate location
        
        Args:
            lat: Latitude in decimal degrees
            lng: Longitude in decimal degrees
            buffer_km: Buffer distance in kilometers around the point
            data_sources: List of preferred data sources, if None uses default hierarchy
            progress_callback: Optional callback for progress updates
            
        Returns:
            AcquisitionResult with information about acquired data
        """
        start_time = datetime.now()
        
        # Create region of interest
        roi = RegionOfInterest(lat, lng, buffer_km)
        
        # Initialize result
        result = AcquisitionResult(
            success=False,
            roi=roi,
            files={},
            metadata={},
            errors=[],
            source_used=""
        )
        
        try:
            # Validate coordinates
            if not self.coordinate_validator.validate_coordinates(lat, lng):
                result.errors.append(f"Invalid coordinates: {lat}, {lng}")
                return result
            
            # Check availability
            availability = await self.check_availability(lat, lng)
            
            # Determine source priority
            if data_sources is None:
                # Default priority order - prioritize USGS 3DEP for LAZ data
                data_sources = ['usgs_3dep', 'opentopography', 'sentinel2', 'ornl_daac']
            
            if progress_callback:
                await progress_callback({
                    "type": "acquisition_started",
                    "message": f"Starting data acquisition for coordinates {lat}, {lng}",
                    "coordinates": {"lat": lat, "lng": lng},
                    "sources": data_sources
                })
            
            # Try each source in order of preference
            for source_name in data_sources:
                if source_name in self.sources:
                    try:
                        logger.info(f"Attempting data acquisition from {source_name}")
                        
                        if progress_callback:
                            await progress_callback({
                                "type": "trying_source",
                                "message": f"Trying data source: {source_name}",
                                "source": source_name
                            })
                        
                        source_result = await self._acquire_from_source(source_name, roi, progress_callback)
                        
                        if source_result['success']:
                            result.success = True
                            result.files.update(source_result['files'])
                            result.metadata.update(source_result['metadata'])
                            result.source_used = source_name
                            result.download_size_mb = source_result.get('size_mb', 0.0)
                            break
                            
                    except Exception as e:
                        error_msg = f"Error with {source_name}: {str(e)}"
                        result.errors.append(error_msg)
                        logger.error(error_msg)
                        
                        if progress_callback:
                            await progress_callback({
                                "type": "source_error",
                                "message": error_msg,
                                "source": source_name,
                                "error": str(e)
                            })
                        continue
            
            # Calculate processing time
            end_time = datetime.now()
            result.processing_time_seconds = (end_time - start_time).total_seconds()
            
            if not result.success:
                result.errors.append("No data sources were able to provide data for this location")
                
                if progress_callback:
                    await progress_callback({
                        "type": "acquisition_failed",
                        "message": "All data sources failed to provide data",
                        "errors": result.errors
                    })
            else:
                if progress_callback:
                    await progress_callback({
                        "type": "acquisition_success",
                        "message": f"Data acquisition completed successfully using {result.source_used}",
                        "source": result.source_used,
                        "files": result.files,
                        "size_mb": result.download_size_mb,
                        "time_seconds": result.processing_time_seconds
                    })
            
        except Exception as e:
            result.errors.append(f"Unexpected error: {str(e)}")
            logger.error(f"Unexpected error in acquire_data_for_coordinates: {e}")
            
            if progress_callback:
                await progress_callback({
                    "type": "unexpected_error",
                    "message": f"Unexpected error: {str(e)}",
                    "error": str(e)
                })
        
        return result
    
    async def _acquire_from_source(self, source_name: str, roi: RegionOfInterest, progress_callback=None) -> Dict[str, Any]:
        """
        Acquire data from a specific source
        
        Args:
            source_name: Name of the data source
            roi: Region of interest
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with acquisition results
        """
        from .sources.base import DownloadRequest, DataType, DataResolution
        
        source = self.sources[source_name]
        
        # Check cache first
        cache_key = f"{source_name}_{roi.center_lat:.4f}_{roi.center_lng:.4f}_{roi.buffer_km}"
        cached_result = self.cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Using cached data for {source_name}")
            if progress_callback:
                await progress_callback({
                    "type": "cache_hit",
                    "message": f"Using cached data from {source_name}",
                    "source": source_name,
                    "progress": 100
                })
            return cached_result
        
        # Create bounding box from ROI
        bbox = self.coordinate_converter.create_bounding_box(
            roi.center_lat, roi.center_lng, roi.buffer_km
        )
        
        # Create download request based on source capabilities
        if source_name == 'usgs_3dep':
            # USGS 3DEP can provide LAZ files - prioritize those
            request = DownloadRequest(
                bbox=bbox,
                data_type=DataType.LAZ,
                resolution=DataResolution.HIGH,
                output_format="laz"
            )
        elif source_name == 'opentopography':
            request = DownloadRequest(
                bbox=bbox,
                data_type=DataType.ELEVATION,
                resolution=DataResolution.MEDIUM,
                output_format="tiff"
            )
        else:
            # Sentinel2, ORNL DAAC, etc. - imagery sources
            request = DownloadRequest(
                bbox=bbox,
                data_type=DataType.IMAGERY,
                resolution=DataResolution.MEDIUM,
                output_format="tiff"
            )
        
        try:
            # Use the new source interface with progress callback
            download_result = await source.download(request, progress_callback=progress_callback)
            
            if download_result.success:
                # Determine file type based on data type
                if request.data_type == DataType.LAZ:
                    file_type = 'laz'
                elif request.data_type == DataType.ELEVATION:
                    file_type = 'elevation'
                else:
                    file_type = 'imagery'
                
                result = {
                    'success': True,
                    'files': {file_type: download_result.file_path},
                    'metadata': download_result.metadata or {},
                    'size_mb': download_result.file_size_mb
                }
                
                # Cache the result
                self.cache.put(cache_key, result)
                
                if progress_callback:
                    await progress_callback({
                        "type": "acquisition_completed",
                        "message": f"Data acquisition completed from {source_name}",
                        "source": source_name,
                        "progress": 100,
                        "file_size_mb": download_result.file_size_mb
                    })
                
                return result
            else:
                if progress_callback:
                    await progress_callback({
                        "type": "acquisition_error",
                        "message": f"Download failed from {source_name}: {download_result.error_message}",
                        "source": source_name,
                        "error": download_result.error_message
                    })
                
                return {
                    'success': False,
                    'error': download_result.error_message,
                    'files': {},
                    'metadata': {},
                    'size_mb': 0.0
                }
                
        except Exception as e:
            logger.error(f"Error acquiring data from {source_name}: {e}")
            
            if progress_callback:
                await progress_callback({
                    "type": "acquisition_error",
                    "message": f"Error acquiring data from {source_name}: {str(e)}",
                    "source": source_name,
                    "error": str(e)
                })
            
            return {
                'success': False,
                'error': str(e),
                'files': {},
                'metadata': {},
                'size_mb': 0.0
            }
    
    def estimate_download_size(self, lat: float, lng: float, buffer_km: float = 1.0) -> Dict[str, float]:
        """
        Estimate download size for different data types
        
        Args:
            lat: Latitude
            lng: Longitude
            buffer_km: Buffer distance in kilometers
            
        Returns:
            Dictionary with estimated sizes in MB for each data type
        """
        area_sq_km = (buffer_km * 2) ** 2
        
        estimates = {
            'srtm_30m': self._estimate_raster_size(area_sq_km, 30, 4),  # 4 bytes per pixel
            'sentinel2': self._estimate_raster_size(area_sq_km, 10, 13 * 2),  # 13 bands, 2 bytes each
            'high_res_lidar': self._estimate_lidar_size(area_sq_km),
        }
        
        return estimates
    
    def _estimate_raster_size(self, area_sq_km: float, resolution_m: int, bytes_per_pixel: int) -> float:
        """Estimate raster data size"""
        pixels_per_sq_km = (1000 / resolution_m) ** 2
        total_bytes = area_sq_km * pixels_per_sq_km * bytes_per_pixel
        return total_bytes / (1024 ** 2)  # Convert to MB
    
    def _estimate_lidar_size(self, area_sq_km: float) -> float:
        """Estimate LiDAR data size (rough approximation)"""
        # Rough estimate: 1-10 MB per square km for LiDAR
        return area_sq_km * 5  # 5 MB per sq km average
    
    def get_acquisition_history(self) -> List[Dict[str, Any]]:
        """
        Get history of all data acquisitions
        
        Returns:
            List of acquisition records
        """
        return self.cache.get_history()
    
    def cleanup_cache(self, older_than_days: int = 30):
        """
        Clean up cache files older than specified days
        
        Args:
            older_than_days: Remove files older than this many days
        """
        self.cache.cleanup(older_than_days)
        logger.info(f"Cache cleanup completed for files older than {older_than_days} days")
