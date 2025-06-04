"""Geographic routing system for automatic data source selection."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .sources import (
    OpenTopographySource, 
    BrazilianElevationSource, 
    BaseDataSource
)
from .sources.base import DownloadRequest, DownloadResult, DataType
from .utils.coordinates import BoundingBox


class GeographicRegion(Enum):
    """Geographic regions for data source routing."""
    UNITED_STATES = "united_states"
    BRAZIL = "brazil"
    AMAZON = "amazon"
    SOUTH_AMERICA = "south_america"
    GLOBAL = "global"


@dataclass
class RegionBounds:
    """Geographic bounds for a region."""
    west: float
    east: float
    south: float
    north: float
    name: str


class GeographicRouter:
    """Routes data requests to optimal sources based on geographic location."""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache"):
        self.api_key = api_key
        self.cache_dir = cache_dir
        
        # Initialize data sources
        self.sources = {
            'opentopography': OpenTopographySource(api_key, cache_dir),
            'brazilian_elevation': BrazilianElevationSource(api_key, cache_dir)
        }
        
        # Define regional bounds
        self.regions = {
            GeographicRegion.UNITED_STATES: RegionBounds(
                west=-180.0, east=-60.0, south=15.0, north=72.0,
                name="United States and territories"
            ),
            GeographicRegion.BRAZIL: RegionBounds(
                west=-74.0, east=-30.0, south=-34.0, north=5.0,
                name="Brazil"
            ),
            GeographicRegion.AMAZON: RegionBounds(
                west=-80.0, east=-45.0, south=-20.0, north=10.0,
                name="Amazon Basin"
            ),
            GeographicRegion.SOUTH_AMERICA: RegionBounds(
                west=-85.0, east=-30.0, south=-60.0, north=15.0,
                name="South America"
            )
        }
        
        # Define routing priority by region and data type
        self.routing_priority = {
            GeographicRegion.UNITED_STATES: {
                DataType.ELEVATION: ['opentopography'],
                DataType.LAZ: ['opentopography']
            },
            GeographicRegion.BRAZIL: {
                DataType.ELEVATION: ['brazilian_elevation', 'opentopography']
            },
            GeographicRegion.AMAZON: {
                DataType.ELEVATION: ['brazilian_elevation']
            },
            GeographicRegion.SOUTH_AMERICA: {
                DataType.ELEVATION: ['brazilian_elevation']
            },
            GeographicRegion.GLOBAL: {
                DataType.ELEVATION: ['brazilian_elevation', 'opentopography']
            }
        }
    
    def detect_region(self, bbox: BoundingBox) -> GeographicRegion:
        """Detect the primary geographic region for a bounding box."""
        center_lat = (bbox.north + bbox.south) / 2
        center_lng = (bbox.east + bbox.west) / 2
        
        # Check each region for coverage
        for region, bounds in self.regions.items():
            if (bounds.west <= center_lng <= bounds.east and
                bounds.south <= center_lat <= bounds.north):
                
                # Return most specific region first
                if region == GeographicRegion.AMAZON:
                    return region
                elif region == GeographicRegion.BRAZIL:
                    return region
                elif region == GeographicRegion.UNITED_STATES:
                    return region
                elif region == GeographicRegion.SOUTH_AMERICA:
                    return region
        
        return GeographicRegion.GLOBAL
    
    def get_optimal_sources(self, bbox: BoundingBox, data_type: DataType) -> List[str]:
        """Get ordered list of optimal data sources for a request."""
        region = self.detect_region(bbox)
        
        # Get priority list for region and data type
        if region in self.routing_priority and data_type in self.routing_priority[region]:
            return self.routing_priority[region][data_type]
        
        # Fallback to global routing
        if data_type in self.routing_priority[GeographicRegion.GLOBAL]:
            return self.routing_priority[GeographicRegion.GLOBAL][data_type]
        
        # Ultimate fallback - try all available sources
        return list(self.sources.keys())
    
    async def download_with_routing(self, request: DownloadRequest, progress_callback=None) -> DownloadResult:
        """Download data using geographic routing to optimal sources."""
        
        # Get optimal sources in priority order
        source_names = self.get_optimal_sources(request.bbox, request.data_type)
        region = self.detect_region(request.bbox)
        
        if progress_callback:
            await progress_callback({
                "type": "routing_info",
                "region": region.value,
                "sources": source_names,
                "message": f"Detected region: {region.value}, trying sources: {', '.join(source_names)}"
            })
        
        last_error = None
        
        # Try each source in priority order
        for i, source_name in enumerate(source_names):
            if source_name not in self.sources:
                continue
                
            source = self.sources[source_name]
            
            try:
                # Check availability first
                if not await source.check_availability(request):
                    if progress_callback:
                        await progress_callback({
                            "type": "source_unavailable",
                            "source": source_name,
                            "message": f"{source_name} not available for this area"
                        })
                    continue
                
                if progress_callback:
                    await progress_callback({
                        "type": "source_selected",
                        "source": source_name,
                        "priority": i + 1,
                        "message": f"Trying {source_name} (priority {i + 1})"
                    })
                
                # Attempt download
                result = await source.download(request, progress_callback)
                
                if result.success:
                    # Add routing metadata
                    if result.metadata is None:
                        result.metadata = {}
                    result.metadata.update({
                        "routing_region": region.value,
                        "selected_source": source_name,
                        "source_priority": i + 1,
                        "tried_sources": source_names[:i+1]
                    })
                    
                    if progress_callback:
                        await progress_callback({
                            "type": "routing_success",
                            "source": source_name,
                            "message": f"Successfully downloaded from {source_name}"
                        })
                    
                    return result
                else:
                    last_error = result.error_message
                    if progress_callback:
                        await progress_callback({
                            "type": "source_failed",
                            "source": source_name,
                            "error": result.error_message,
                            "message": f"{source_name} failed: {result.error_message}"
                        })
                    
            except Exception as e:
                last_error = str(e)
                if progress_callback:
                    await progress_callback({
                        "type": "source_error",
                        "source": source_name,
                        "error": str(e),
                        "message": f"{source_name} error: {str(e)}"
                    })
        
        # All sources failed
        return DownloadResult(
            success=False,
            error_message=f"All sources failed for region {region.value}. Last error: {last_error}",
            metadata={
                "routing_region": region.value,
                "tried_sources": source_names,
                "all_failed": True
            }
        )
    
    async def check_availability_all(self, request: DownloadRequest) -> Dict[str, bool]:
        """Check availability across all relevant sources."""
        source_names = self.get_optimal_sources(request.bbox, request.data_type)
        availability = {}
        
        for source_name in source_names:
            if source_name in self.sources:
                try:
                    available = await self.sources[source_name].check_availability(request)
                    availability[source_name] = available
                except Exception:
                    availability[source_name] = False
            else:
                availability[source_name] = False
        
        return availability
    
    def get_region_info(self, bbox: BoundingBox) -> Dict[str, Any]:
        """Get detailed information about the detected region."""
        region = self.detect_region(bbox)
        
        return {
            "region": region.value,
            "region_name": self.regions[region].name if region in self.regions else "Global",
            "optimal_sources": self.get_optimal_sources(bbox, DataType.ELEVATION),
            "center_lat": (bbox.north + bbox.south) / 2,
            "center_lng": (bbox.east + bbox.west) / 2,
            "area_km2": bbox.area_km2()
        }


# Convenience function for easy usage
async def download_elevation_data(bbox: BoundingBox, resolution=None, api_key=None, cache_dir="data/cache", progress_callback=None) -> DownloadResult:
    """Convenience function to download elevation data with automatic routing."""
    
    from .sources.base import DataResolution
    
    # Create download request
    request = DownloadRequest(
        bbox=bbox,
        data_type=DataType.ELEVATION,
        resolution=resolution or DataResolution.MEDIUM
    )
    
    # Create router and download
    router = GeographicRouter(api_key=api_key, cache_dir=cache_dir)
    return await router.download_with_routing(request, progress_callback)
