"""Base class for all data sources."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import os
import asyncio
from pathlib import Path

class DataType(Enum):
    """Supported data types."""
    ELEVATION = "elevation"
    IMAGERY = "imagery"
    LAZ = "laz"
    RADAR = "radar"

class DataResolution(Enum):
    """Common data resolutions."""
    HIGH = "high"      # < 1m
    MEDIUM = "medium"  # 1-10m
    LOW = "low"        # > 10m

@dataclass
class DataSourceCapability:
    """Defines what a data source can provide."""
    data_types: List[DataType]
    resolutions: List[DataResolution]
    coverage_areas: List[str]  # Geographic regions supported
    max_area_km2: float  # Maximum area that can be requested
    requires_api_key: bool = False

@dataclass
class DownloadRequest:
    """Request for data download."""
    bbox: 'BoundingBox'  # From coordinates.py
    data_type: DataType
    resolution: Optional[DataResolution] = None
    output_format: str = "tiff"
    max_file_size_mb: float = 500.0
    region_name: Optional[str] = None

@dataclass
class DownloadResult:
    """Result of data download."""
    success: bool
    file_path: Optional[str] = None
    file_size_mb: float = 0.0
    resolution_m: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class BaseDataSource(ABC):
    """Base class for all data acquisition sources."""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache"):
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        # Note: Cache directory will be created only when actually needed
        
    def get_capabilities(self) -> DataSourceCapability:
        """Get the capabilities of this data source."""
        return self.capabilities
    
    @property
    @abstractmethod
    def capabilities(self) -> DataSourceCapability:
        """Return the capabilities of this data source."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this data source."""
        pass
    
    @abstractmethod
    async def check_availability(self, request: DownloadRequest) -> bool:
        """Check if data is available for the given request."""
        pass
    
    @abstractmethod
    async def estimate_size(self, request: DownloadRequest) -> float:
        """Estimate download size in MB."""
        pass
    
    @abstractmethod
    async def download(self, request: DownloadRequest, progress_callback=None) -> DownloadResult:
        """Download data for the given request."""
        pass
    
    def _validate_request(self, request: DownloadRequest) -> bool:
        """Validate if this source can handle the request."""
        capabilities = self.capabilities
        
        # Check data type
        if request.data_type not in capabilities.data_types:
            return False
            
        # Check resolution if specified
        if request.resolution and request.resolution not in capabilities.resolutions:
            return False
            
        # Check area size
        bbox_area = request.bbox.area_km2()
        if bbox_area > capabilities.max_area_km2:
            return False
            
        return True
    
    def _get_cache_path(self, request: DownloadRequest) -> Path:
        """Generate cache file path for request."""
        bbox = request.bbox
        filename = (
            f"{self.name}_{request.data_type.value}_"
            f"{bbox.west}_{bbox.south}_{bbox.east}_{bbox.north}_"
            f"{request.resolution.value if request.resolution else 'default'}"
            f".{request.output_format}"
        )
        return self.cache_dir / filename
