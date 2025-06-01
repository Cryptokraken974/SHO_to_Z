# LIDAR Data Acquisition Module

This module provides functionality to acquire LIDAR data from various external providers and integrate it into the LAZ Terrain Processor workflow.

## Features

- **Multi-provider support**: OpenTopography, USGS 3DEP, and extensible for additional providers
- **Automatic provider selection**: Chooses the best provider based on location and data availability
- **Progress tracking**: Real-time updates via WebSocket connection
- **Caching**: Avoids duplicate downloads for the same regions
- **Format standardization**: Converts various LIDAR formats to LAZ for consistent processing

## How It Works

### Frontend Integration

1. **"Get LIDAR Data" Button**: Located in the sidebar below the Sentinel-2 test button
2. **Coordinate Input**: Uses the same lat/lng input fields as other features
3. **Default Location**: Falls back to Portland, Oregon if no coordinates are specified
4. **Progress Display**: Shows real-time acquisition progress with WebSocket updates

### Backend Architecture

```
app/lidar_acquisition/
├── __init__.py          # Module exports
├── manager.py           # Main acquisition coordinator
└── providers.py         # Provider implementations
```

### API Endpoints

- `POST /api/acquire-lidar`: Start LIDAR data acquisition
- `POST /api/process-lidar`: Process acquired data into LAZ format
- `GET /api/lidar/providers`: List available providers and their coverage

## Usage

1. **Set Coordinates**: Enter latitude and longitude in the input fields
2. **Click "Get LIDAR Data"**: Initiates the acquisition process
3. **Monitor Progress**: Watch real-time updates in the progress display
4. **Automatic Processing**: Downloaded data is automatically processed into LAZ format
5. **File Integration**: Processed LAZ files appear in the file list for terrain analysis

## Supported Providers

### OpenTopography
- **Coverage**: United States (USGS 3DEP datasets)
- **Resolution**: 1-10m (configurable)
- **Point Density**: 2-8 points/m²
- **Data Access**: PDAL pipelines with AWS S3 EPT buckets
- **API**: No traditional REST API - uses PDAL with `https://s3-us-west-2.amazonaws.com/usgs-lidar-public/{dataset}/ept.json`
- **Boundaries**: Dataset boundaries from GitHub: `https://raw.githubusercontent.com/hobuinc/usgs-lidar/master/boundaries/resources.geojson`
- **Authentication**: Not required (public access)

### USGS 3DEP
- **Coverage**: United States only
- **Resolution**: 1-2m  
- **Point Density**: 2-8 points/m²
- **API**: https://tnmaccess.nationalmap.gov/api/v1/

## Configuration

Provider configurations can be set in the application settings:

```python
# In config.py
LIDAR_PROVIDERS = {
    "opentopography": {
        # OpenTopography uses PDAL with direct AWS S3 access
        # No API key required for public 3DEP datasets
        "boundaries_url": "https://raw.githubusercontent.com/hobuinc/usgs-lidar/master/boundaries/resources.geojson",
        "ept_base_url": "https://s3-us-west-2.amazonaws.com/usgs-lidar-public"
    },
    "usgs_3dep": {
        "base_url": "https://tnmaccess.nationalmap.gov/api/v1/"
    }
}

# PDAL requirements
PDAL_REQUIRED = True  # OpenTopography implementation requires PDAL
```

## Development Status

### Completed ✅
- [x] Frontend UI integration
- [x] Backend API structure
- [x] Provider abstraction layer
- [x] Progress tracking system
- [x] Basic error handling
- [x] Module architecture
- [x] OpenTopography PDAL integration
- [x] 3DEP dataset boundary detection
- [x] Point cloud and DTM/DEM generation via PDAL
- [x] Test script verification

### PDAL Implementation Details

The OpenTopography provider now uses PDAL (Point Data Abstraction Library) instead of traditional REST APIs:

1. **Dataset Discovery**: Fetches 3DEP dataset boundaries from GitHub repository
2. **Intersection Detection**: Finds datasets that overlap with requested coordinates  
3. **PDAL Pipeline Creation**: Builds pipelines for point cloud or DEM extraction
4. **AWS S3 EPT Access**: Direct access to EPT (Entwine Point Tiles) buckets
5. **Format Output**: LAZ for point clouds, GeoTIFF for elevation models

**Example Pipeline Structure**:
```json
{
  "pipeline": [
    {
      "type": "readers.ept",
      "filename": "https://s3-us-west-2.amazonaws.com/usgs-lidar-public/{dataset}/ept.json",
      "polygon": "POLYGON(...)",
      "resolution": 5.0
    },
    {
      "type": "filters.outlier",
      "method": "statistical"
    },
    {
      "type": "writers.las",
      "compression": "laszip",
      "filename": "output.laz"
    }
  ]
}
```

### In Progress 🚧
- [ ] Integration with existing workflow UI
- [ ] Enhanced error handling for PDAL operations
- [ ] Provider selection logic optimization
- [ ] Performance optimization for large areas

### Future Enhancements 🔮
- [ ] Additional providers (international sources)
- [ ] Advanced filtering options
- [ ] Metadata extraction and display
- [ ] Quality assessment tools
- [ ] Automatic coordinate system conversion

## Adding New Providers

To add a new LIDAR provider:

1. **Create Provider Class**:
```python
class MyLidarProvider(LidarProvider):
    def __init__(self):
        super().__init__("MyProvider")
        self.base_url = "https://api.myprovider.com"
    
    async def download_lidar(self, lat, lng, buffer_km, output_dir, progress_callback=None):
        # Implement actual API calls
        pass
    
    def check_availability(self, lat, lng):
        # Check if data is available for location
        pass
    
    def get_coverage_info(self, lat, lng):
        # Return coverage information
        pass
```

2. **Register Provider**:
```python
from .providers import register_provider
register_provider("myprovider", MyLidarProvider)
```

## Error Handling

The system includes comprehensive error handling:

- **Network errors**: Retry logic and fallback providers
- **Authentication errors**: Clear error messages for API key issues
- **Data availability**: Graceful handling when no data exists for a location
- **Format errors**: Automatic format detection and conversion
- **Progress updates**: Error status communicated via WebSocket

## Testing

Use the test coordinates (Portland, OR: 45.5152, -122.6784) which should have good LIDAR coverage from multiple providers.

## Integration with Existing Workflow

Once LIDAR data is acquired and processed:

1. LAZ files appear in the file selection dropdown
2. All existing terrain analysis tools work with the new data
3. Results can be overlaid on the map like other processed data
4. Standard caching and file management applies
