# Complete LAZ Processing Workflow

## Overview

The complete LAZ processing workflow provides a comprehensive solution for LAZ file processing that includes:

1. **Density Analysis**: Generate point density rasters from LAZ files using PDAL
2. **Binary Mask Generation**: Create validity masks to identify artifacts and edge effects
3. **Raster Cleaning**: Apply masks to clean existing raster outputs
4. **Polygon Generation**: Convert binary masks to vector polygons using GDAL
5. **LAZ Cropping**: Crop original LAZ files to real data footprint using PDAL

## Architecture

### Core Components

1. **DensityAnalyzer** (`app/processing/density_analysis.py`)
   - Main workflow orchestrator
   - PDAL pipeline execution
   - Metadata generation

2. **RasterCleaner** (`app/processing/raster_cleaning.py`)
   - Modular raster cleaning service
   - Support for both GDAL and Python approaches
   - Batch processing capabilities

3. **VectorProcessor** (`app/processing/vector_operations.py`)
   - Mask-to-polygon conversion service
   - Multiple output formats (GeoJSON, Shapefile, GPKG)
   - Polygon simplification and filtering

4. **LAZCropper** (`app/processing/laz_cropping.py`)
   - LAZ point cloud cropping service
   - Polygon and bounding box cropping
   - PDAL-based processing

### Integration Points

The `DensityAnalyzer` integrates with all processing modules through:
- Automatic mask generation
- Optional raster cleaning step
- Optional polygon generation step
- Optional LAZ cropping step
- Unified result reporting

## Workflow Steps

### Step 1: Density Analysis
```python
# Generate point density raster using PDAL
pipeline = {
    "pipeline": [
        {"type": "readers.las", "filename": input_laz},
        {
            "type": "writers.gdal",
            "filename": output_tiff,
            "resolution": 1.0,
            "output_type": "count",
            "nodata": 0
        }
    ]
}
```

**Outputs:**
- `{region}_density.tif` - Point density raster
- `{region}_density.png` - Visualization
- `{region}_density_metadata.json` - Processing metadata

### Step 2: Binary Mask Generation
```python
# Create binary mask from density raster
mask = (density_data > threshold).astype(np.uint8)
# Where: 1 = valid data, 0 = artifact/edge effect
```

**Outputs:**
- `masks/{region}_valid_mask.tif` - Binary validity mask
- `masks/{region}_valid_mask.png` - Mask visualization

### Step 3: Raster Cleaning (Optional)
```python
# Apply mask to existing rasters
cleaned_raster = original_raster * mask
# Result: artifacts removed, edges cleaned
```

**Outputs:**
- `cleaned/{raster}_cleaned.tif` - Cleaned raster files
- Comprehensive cleaning statistics

### Step 4: Polygon Generation (Optional)
```bash
# Convert binary mask to polygon using GDAL
gdal_polygonize.py valid_mask.tif -f "GeoJSON" valid_mask.geojson
```

**Outputs:**
- `vectors/{region}_valid_footprint.geojson` - Polygon vector file
- Polygon statistics and metadata

### Step 5: LAZ Cropping (Optional)
```python
# Crop LAZ using polygon geometry with PDAL
pipeline = {
    "pipeline": [
        {"type": "readers.las", "filename": input_laz},
        {"type": "filters.crop", "polygon": polygon_path},
        {"type": "writers.laz", "filename": output_laz}
    ]
}
```

**Outputs:**
- `cropped/{region}_cropped.laz` - Cropped LAZ file
- Point retention statistics

## Usage Examples

### Basic Usage
```python
from app.processing.density_analysis import analyze_laz_density

# Simple density analysis
result = analyze_laz_density(
    laz_file_path="input/region/data.laz",
    output_dir="output/region",
    resolution=1.0,
    mask_threshold=2.0
)
```

### Complete Workflow
```python
# Complete 5-step workflow
result = analyze_laz_density(
    laz_file_path="input/region/data.laz",
    output_dir="output/region",
    resolution=1.0,
    mask_threshold=2.0,
    generate_mask=True,
    clean_existing_rasters=True,  # Step 3: Enable cleaning
    generate_polygon=True,        # Step 4: Enable polygon generation
    crop_original_laz=True,       # Step 5: Enable LAZ cropping
    polygon_format="GeoJSON"      # Output format for polygon
)

# Access results from all steps
density_path = result["tiff_path"]
mask_results = result["mask_results"]
cleaning_results = result["cleaning_results"]
polygon_results = result["polygon_results"]
cropping_results = result["cropping_results"]
```

### Standalone Operations
```python
# Individual step operations
from app.processing.raster_cleaning import RasterCleaner
from app.processing.vector_operations import convert_mask_to_polygon
from app.processing.laz_cropping import crop_laz_with_polygon

# Standalone raster cleaning
cleaner = RasterCleaner(method="auto", cleaned_suffix="_cleaned")
result = cleaner.batch_clean_rasters(
    raster_directory="output/region/lidar",
    mask_path="output/region/density/masks/region_valid_mask.tif",
    output_directory="output/region/lidar/cleaned",
    raster_patterns=["*DTM*.tif", "*DSM*.tif", "*hillshade*.tif"]
)

# Standalone polygon generation
polygon_result = convert_mask_to_polygon(
    mask_raster_path="masks/region_valid_mask.tif",
    output_dir="output/region",
    region_name="region",
    output_format="GeoJSON",
    simplify_tolerance=0.5
)

# Standalone LAZ cropping
crop_result = crop_laz_with_polygon(
    input_laz_path="input/region/data.laz",
    polygon_path="vectors/region_valid_footprint.geojson",
    output_dir="output/region",
    region_name="region"
)
```

## Configuration Options

### Density Analysis Parameters
- `resolution`: Grid resolution in meters (default: 1.0)
- `nodata_value`: Value for empty cells (default: 0)
- `mask_threshold`: Minimum points/cell for validity (default: 2.0)

### Cleaning Parameters
- `method`: Cleaning approach ("gdal", "python", "auto")
- `cleaned_suffix`: Suffix for cleaned files (default: "_cleaned")
- `preserve_nodata`: Whether to maintain NoData values (default: True)

### Vector Generation Parameters
- `polygon_format`: Output format ("GeoJSON", "Shapefile", "GPKG")
- `simplify_tolerance`: Polygon simplification tolerance in meters (default: 0.5)
- `min_area`: Minimum polygon area in square meters (default: 100.0)

### LAZ Cropping Parameters
- `output_format`: Output format ("laz", "las", "ply")
- `crop_method`: Cropping method ("inside", "outside")
- `compression`: Enable compression for output (default: True)

## Output Structure

```
output/
└── {region}/
    ├── density/
    │   ├── {region}_density.tif
    │   ├── {region}_density.png
    │   ├── {region}_density_metadata.json
    │   └── masks/
    │       ├── {region}_valid_mask.tif
    │       └── {region}_valid_mask.png
    ├── vectors/
    │   └── {region}_valid_footprint.geojson
    ├── cropped/
    │   └── {region}_cropped.laz
    ├── lidar/
    │   ├── original_rasters.tif
    │   └── cleaned/
    │       └── original_rasters_cleaned.tif
    └── ...other processing outputs
```

## Quality Assessment

### Mask Statistics
The binary mask provides quality metrics:
- **Coverage Percentage**: Valid data coverage
- **Artifact Percentage**: Data identified as artifacts
- **Threshold Applied**: Points/cell threshold used

### Cleaning Results
Each cleaning operation reports:
- **Files Processed**: Number of rasters processed
- **Successful Cleanings**: Number of successful operations
- **Error Details**: Any processing issues encountered

## Integration with Existing Workflows

### LAZ Processing Pipeline
The integrated workflow fits seamlessly into existing LAZ processing:

```python
# 1. LAZ Upload & Validation
upload_result = process_laz_upload(...)

# 2. Standard Processing (DTM, DSM, etc.)
processing_result = process_laz_data(...)

# 3. Density Analysis + Cleaning
density_result = analyze_laz_density(
    laz_file_path=upload_result["laz_path"],
    output_dir=processing_result["output_dir"],
    clean_existing_rasters=True  # Clean the DTM, DSM, etc.
)
```

### Gallery Integration
Cleaned rasters can be automatically added to the gallery:

```python
# Add cleaned rasters to gallery
if density_result["cleaning_results"]["success"]:
    cleaned_files = [r["output_path"] for r in density_result["cleaning_results"]["results"]]
    for cleaned_file in cleaned_files:
        add_to_gallery(cleaned_file, category="cleaned_lidar")
```

## Error Handling

The workflow includes comprehensive error handling:

### Graceful Degradation
- If rasterio unavailable → Falls back to GDAL
- If cleaning fails → Continues without cleaning
- If mask generation fails → Skips cleaning step

### Error Reporting
```python
result = analyze_laz_density(...)

if not result["success"]:
    print(f"Error: {result['error']}")

# Check individual step results
if result["mask_results"].get("error"):
    print(f"Mask generation failed: {result['mask_results']['error']}")

if result["cleaning_results"].get("error"):
    print(f"Cleaning failed: {result['cleaning_results']['error']}")
```

## Performance Considerations

### Memory Usage
- Large rasters are processed in chunks
- Temporary files are cleaned up automatically
- Memory-efficient numpy operations

### Processing Time
- PDAL operations: ~30-60 seconds for typical LAZ files
- Mask generation: ~5-10 seconds
- Raster cleaning: ~2-5 seconds per raster

### Scalability
- Batch processing support
- Configurable timeouts
- Background processing compatible

## Dependencies

### Required
- **PDAL**: LAZ file processing and density generation
- **GDAL**: Raster operations and format conversion
- **numpy**: Numerical operations for mask generation

### Optional
- **rasterio**: Enhanced Python raster operations
- **matplotlib**: Advanced visualization options

## Testing

Run the comprehensive test suite:

```bash
python test_integrated_density_cleaning.py
```

This tests:
- Complete integrated workflow
- Standalone cleaning functionality
- Error handling and edge cases
- Output validation

## Future Enhancements

### Planned Features
1. **Advanced Mask Algorithms**: Morphological operations, edge detection
2. **Quality Metrics**: Automated quality scoring for cleaned rasters
3. **Batch Region Processing**: Process multiple regions simultaneously
4. **Custom Cleaning Rules**: User-defined cleaning algorithms

### API Integration
The workflow can be exposed via REST API:

```python
@app.route('/api/density-analysis', methods=['POST'])
def api_density_analysis():
    result = analyze_laz_density(
        laz_file_path=request.json['laz_path'],
        output_dir=request.json['output_dir'],
        clean_existing_rasters=request.json.get('clean_rasters', False)
    )
    return jsonify(result)
```

## Conclusion

The integrated density analysis + raster cleaning workflow provides a robust, modular solution for LAZ file processing. It combines the power of PDAL for density analysis with intelligent artifact removal, resulting in cleaner, more accurate raster outputs for downstream analysis and visualization.
