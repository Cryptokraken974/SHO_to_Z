# API Service Layer Documentation

## Overview

The API Service Layer provides an implementation-agnostic middleware between the frontend and backend endpoints. This layer offers better flexibility, maintainability, and a consistent interface for all API operations.

## Architecture

```
Frontend ←→ Service Layer ←→ Backend API Endpoints
```

### Key Components

1. **BaseService**: Abstract base class with common HTTP functionality
2. **Service Classes**: Specific implementations for different domains
3. **ServiceFactory**: Centralized service management and creation
4. **SyncServiceMixin**: Provides synchronous versions of async methods

## Service Classes

### 1. RegionService
Manages region operations including listing, searching, and deleting regions.

```python
from app.api import RegionService

# Async usage
region_service = RegionService()
regions = await region_service.list_regions()
await region_service.close()

# Sync usage
regions = region_service.list_regions_sync()
region_service.close_sync()
```

**Methods:**
- `list_regions(source=None)` - List all regions with optional source filter
- `delete_region(region_name)` - Delete a specific region
- `get_region_info(region_name)` - Get detailed region information
- `search_regions(query, source=None)` - Search regions by query

### 2. ProcessingService
Handles LIDAR processing operations including LAZ file processing and terrain analysis.

```python
from app.api import ProcessingService

processing_service = ProcessingService()

# List LAZ files
laz_files = await processing_service.list_laz_files()

# Generate terrain products
dtm_result = await processing_service.generate_dtm(region_name="test_region")
dsm_result = await processing_service.generate_dsm(region_name="test_region")
hillshade_result = await processing_service.generate_hillshade(region_name="test_region")

# Generate all rasters at once
all_rasters = await processing_service.generate_all_rasters(
    region_name="test_region",
    batch_size=4
)

await processing_service.close()
```

**Key Methods:**
- `list_laz_files()` - List available LAZ files
- `generate_dtm()`, `generate_dsm()`, `generate_chm()` - Generate elevation models
- `generate_hillshade()`, `generate_slope()`, `generate_aspect()` - Terrain analysis
- `generate_all_rasters()` - Unified raster generation

### 3. ElevationService
Manages elevation data acquisition and processing with optimal quality settings.

```python
from app.api import ElevationService

elevation_service = ElevationService()

# Get optimal elevation data
elevation_data = await elevation_service.get_optimal_elevation_data(
    latitude=-9.38,
    longitude=-62.67,
    area_km=25.0
)

# Brazilian-optimized elevation
brazilian_data = await elevation_service.get_brazilian_elevation_data(
    latitude=-9.38,
    longitude=-62.67
)

# Check availability
availability = await elevation_service.check_elevation_availability(
    latitude=-9.38,
    longitude=-62.67
)

await elevation_service.close()
```

**Key Methods:**
- `get_optimal_elevation_data()` - Get best quality elevation data
- `get_brazilian_elevation_data()` - Brazilian Amazon optimized data
- `download_elevation_data()` - Download elevation data
- `get_elevation_status()` - System status with quality info

### 4. SatelliteService
Handles satellite data operations including Sentinel-2 acquisition and processing.

```python
from app.api import SatelliteService

satellite_service = SatelliteService()

# Search for Sentinel-2 scenes
scenes = await satellite_service.search_sentinel2_scenes(
    latitude=-9.38,
    longitude=-62.67,
    start_date="2023-01-01",
    end_date="2023-12-31",
    cloud_cover_max=30.0
)

# Download Sentinel-2 data
download_result = await satellite_service.download_sentinel2_data(
    latitude=-9.38,
    longitude=-62.67,
    start_date="2023-06-01",
    end_date="2023-06-30",
    bands=["B04", "B08"]  # Red and NIR
)

# Calculate vegetation indices
ndvi_result = await satellite_service.calculate_ndvi(
    region_name="test_region",
    red_band_path="path/to/red.tif",
    nir_band_path="path/to/nir.tif"
)

await satellite_service.close()
```

### 5. OverlayService
Manages overlay data for visualization and mapping.

```python
from app.api import OverlayService

overlay_service = OverlayService()

# Get overlay data
overlay_data = await overlay_service.get_raster_overlay_data(
    region_name="test_region",
    processing_type="hillshade"
)

# List available overlays
overlays = await overlay_service.list_available_overlays()

await overlay_service.close()
```

### 6. SavedPlacesService
Handles saved places management.

```python
from app.api import SavedPlacesService

places_service = SavedPlacesService()

# Get all saved places
places = await places_service.get_saved_places()

# Save a new place
new_place = await places_service.save_place({
    "name": "Amazon Research Site",
    "latitude": -9.38,
    "longitude": -62.67,
    "description": "Research location in Amazon"
})

# Search nearby places
nearby = await places_service.get_places_near_coordinates(
    latitude=-9.38,
    longitude=-62.67,
    radius_km=50.0
)

await places_service.close()
```

### 7. GeotiffService
Handles GeoTIFF file operations and conversions.

```python
from app.api import GeotiffService

geotiff_service = GeotiffService()

# List GeoTIFF files
files = await geotiff_service.list_geotiff_files()

# Convert to PNG
png_result = await geotiff_service.convert_geotiff_to_png(
    file_path="path/to/file.tif"
)

# Get metadata
metadata = await geotiff_service.get_geotiff_metadata(
    file_path="path/to/file.tif"
)

await geotiff_service.close()
```

### 8. RegionAnalysisService
Provides advanced region analysis and terrain modeling.

```python
from app.api import RegionAnalysisService

analysis_service = RegionAnalysisService()

# Comprehensive terrain analysis
terrain_analysis = await analysis_service.analyze_region_terrain("test_region")

# Calculate vegetation indices
vegetation_indices = await analysis_service.calculate_vegetation_indices(
    region_name="test_region",
    indices=["NDVI", "NDWI", "EVI"]
)

# Compare regions
comparison = await analysis_service.compare_regions(
    region1="region_a",
    region2="region_b",
    metrics=["elevation", "slope", "vegetation"]
)

await analysis_service.close()
```

## ServiceFactory Usage

The ServiceFactory provides centralized service management:

```python
from app.api import ServiceFactory

# Create factory
factory = ServiceFactory("http://localhost:8000")

# Get services
region_service = factory.get_region_service()
processing_service = factory.get_processing_service()
elevation_service = factory.get_elevation_service()

# Use services...
regions = await region_service.list_regions()

# Close all services at once
await factory.close_all()

# Context manager usage
async with ServiceFactory() as factory:
    regions = await factory.get_region_service().list_regions()
    # Services automatically closed
```

## Convenience Functions

```python
from app.api.factory import (
    create_region_service,
    create_processing_service,
    create_elevation_service
)

# Quick service creation
region_service = create_region_service()
processing_service = create_processing_service()
elevation_service = create_elevation_service()
```

## Global Service Instances

```python
from app.api.factory import regions, processing, elevation, satellite

# Use global service instances
region_service = regions()
processing_service = processing()
elevation_service = elevation()
satellite_service = satellite()
```

## Error Handling

All services use the `ServiceError` exception for API-related errors:

```python
from app.api import ServiceError, RegionService

region_service = RegionService()

try:
    regions = await region_service.list_regions()
except ServiceError as e:
    print(f"API Error: {e.message}")
    print(f"Status Code: {e.status_code}")
    print(f"Details: {e.details}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    await region_service.close()
```

## Synchronous Usage

All services provide synchronous versions of their methods:

```python
from app.api import RegionService

region_service = RegionService()

# Async version
regions = await region_service.list_regions()

# Sync version
regions = region_service.list_regions_sync()

# Close
region_service.close_sync()
```

## Configuration

Services can be configured with different base URLs:

```python
from app.api import RegionService

# Default (localhost:8000)
region_service = RegionService()

# Custom URL
region_service = RegionService("http://production-server:8000")

# With HTTPS
region_service = RegionService("https://api.example.com")
```

## Best Practices

1. **Always close services** when done to free resources
2. **Use context managers** for automatic cleanup
3. **Handle ServiceError exceptions** for API-specific errors
4. **Use the ServiceFactory** for managing multiple services
5. **Consider using sync methods** for simple scripts
6. **Set appropriate base URLs** for different environments

## Integration Examples

See `app/api/examples.py` for comprehensive usage examples of all services.

## Frontend Integration

The service layer is designed to be easily integrated with frontend frameworks:

```javascript
// Frontend can call the service layer through a bridge
async function getRegions() {
    const response = await fetch('/api/service-bridge/regions');
    return response.json();
}

async function generateRasters(regionName) {
    const response = await fetch('/api/service-bridge/process/generate-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ region_name: regionName })
    });
    return response.json();
}
```

This service layer provides a clean, maintainable interface between your frontend and the FastAPI backend, making it easier to develop, test, and maintain your application.
