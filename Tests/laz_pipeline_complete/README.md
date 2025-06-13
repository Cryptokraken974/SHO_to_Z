# Complete LAZ Processing Pipeline Test

This test directory contains a comprehensive test for the entire LAZ processing workflow using the FoxIsland.laz file.

## Test Overview

The test validates the complete 3-hillshade RGB blending pipeline with color-relief tinting and slope blending:

1. **DTM Generation** - Converts LAZ to Digital Terrain Model using PDAL
2. **Multiple Hillshades** - Generates 3 hillshades with different azimuths:
   - Red Channel: 315° azimuth, 30° altitude  
   - Green Channel: 45° azimuth, 25° altitude
   - Blue Channel: 135° azimuth, 30° altitude
3. **RGB Composite** - Combines the 3 hillshades into RGB bands
4. **Color Relief** - Generates elevation-based color visualization
5. **Tint Overlay** - Blends color relief with RGB composite intensity
6. **Slope Relief** - Generates slope analysis from DTM
7. **Final Blend** - Combines tint overlay with slope for final enhanced visualization
8. **PNG Conversion** - Creates PNG files for all outputs for easy viewing

## Files

- `test_complete_laz_pipeline.py` - Main test script
- `outputs/` - Directory containing all generated outputs
- `README.md` - This documentation

## Requirements

- Python 3.7+
- GDAL with Python bindings
- PDAL command-line tool
- NumPy
- FoxIsland.laz in `input/LAZ/` directory

## Running the Test

From the project root directory:

```bash
cd Tests/laz_pipeline_complete
python test_complete_laz_pipeline.py
```

Or run directly:

```bash
python Tests/laz_pipeline_complete/test_complete_laz_pipeline.py
```

## Expected Outputs

The test generates the following files in the `outputs/` directory:

### TIFF Files (Geospatial)
- `FoxIsland_DTM.tif` - Digital Terrain Model
- `FoxIsland_Hillshade_315.tif` - Red channel hillshade
- `FoxIsland_Hillshade_45.tif` - Green channel hillshade  
- `FoxIsland_Hillshade_135.tif` - Blue channel hillshade
- `FoxIsland_RGB_Composite.tif` - 3-band RGB composite
- `FoxIsland_ColorRelief.tif` - Elevation-based color visualization
- `FoxIsland_TintOverlay.tif` - Color relief tinted by hillshade
- `FoxIsland_SlopeRelief.tif` - Slope analysis
- `FoxIsland_FinalBlend.tif` - Final blended visualization

### PNG Files (Visualization)
- `FoxIsland_DTM.png`
- `FoxIsland_Hillshade_315.png`
- `FoxIsland_Hillshade_45.png`
- `FoxIsland_Hillshade_135.png`
- `FoxIsland_RGB_Composite.png`
- `FoxIsland_ColorRelief.png`
- `FoxIsland_TintOverlay.png`
- `FoxIsland_SlopeRelief.png`
- `FoxIsland_FinalBlend.png`

### Temporary Files
- `color_table.txt` - Color ramp definition for terrain visualization

## Test Validation

The test validates:

1. **File Generation** - All expected output files are created
2. **Size Verification** - Files have reasonable sizes (not empty)
3. **Raster Properties** - Correct dimensions, bands, and geospatial properties
4. **Processing Chain** - Each step depends on the previous step's output
5. **Error Handling** - Proper error messages and cleanup on failure

## Configuration

The test uses the same configuration as the production system:

- **DTM Pipeline**: `app/processing/pipelines_json/dtm.json`
- **Hillshade Config**: `app/processing/pipelines_json/hillshade.json`
- **Color Ramp**: 8-stop terrain color ramp (blue → cyan → green → yellow → orange → red → white)
- **Blend Factor**: 0.5 for final slope overlay

## Integration

This test replicates the `process_all_raster_products()` function from the main application to ensure the complete workflow functions correctly for LAZ files. It validates that:

- The 3-hillshade RGB workflow is active and functional
- Color relief tinting works correctly
- Slope blending produces the expected enhanced visualization
- All file formats and geospatial properties are preserved

## Troubleshooting

**Common Issues:**

1. **PDAL not found**: Install PDAL (`conda install -c conda-forge pdal` or system package)
2. **GDAL import error**: Install GDAL Python bindings (`conda install -c conda-forge gdal`)
3. **LAZ file missing**: Ensure `FoxIsland.laz` exists in `input/LAZ/`
4. **Permission errors**: Check write permissions in `Tests/laz_pipeline_complete/outputs/`
5. **Memory errors**: Large LAZ files may require more RAM

**Debug Mode:**

Add verbose output by modifying the print statements in the test script.

## Expected Runtime

- Small LAZ files (< 50MB): 2-5 minutes
- Medium LAZ files (50-200MB): 5-15 minutes  
- Large LAZ files (> 200MB): 15+ minutes

The test displays progress and timing for each step.
