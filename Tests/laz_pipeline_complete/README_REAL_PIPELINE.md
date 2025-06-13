# Real LAZ Pipeline Test

This test runs the actual `process_all_raster_products()` function from the application to verify that all raster outputs are generated correctly for the FoxIsland.laz file.

## Test Overview

This test validates the real application pipeline by:

1. **Using the actual DTM function** - Calls `dtm()` from `app/processing/dtm.py`
2. **Running the real pipeline** - Calls `process_all_raster_products()` from `app/processing/tiff_processing.py`
3. **Validating complete workflow** - Checks 3-hillshade RGB → tint → slope blend pipeline
4. **Verifying all outputs** - Ensures all expected TIFF and PNG files are generated

## Key Difference from Standalone Test

- **Real Application Code**: Uses actual functions from the app, not reimplemented logic
- **Production Pipeline**: Runs the exact same code that processes LAZ files in the application
- **Authentic Workflow**: Tests the real `process_all_raster_products()` orchestration

## Files

- `test_real_pipeline.py` - Main test that calls real application functions
- `run_real_pipeline_test.sh` - Executable script to run the test
- `verify_real_pipeline.py` - Verification script for results
- `README_REAL_PIPELINE.md` - This documentation

## Running the Test

### Quick Start (Recommended)
```bash
./run_real_pipeline_test.sh
```

### Manual Execution
```bash
python test_real_pipeline.py
```

### Verification Only
```bash
python verify_real_pipeline.py
```

## Expected Runtime

- **FoxIsland.laz (18MB)**: 3-8 minutes
- Includes DTM generation + complete raster pipeline

## Expected Outputs

The test validates that `process_all_raster_products()` creates:

### 📁 Directory Structure: `output/FoxIsland/lidar/`

#### Hillshades (RGB Channels)
- `Hs_red/hillshade_315_30_z1.tif` - Red channel (315° azimuth)
- `Hs_green/hillshade_45_25_z1.tif` - Green channel (45° azimuth)  
- `Hs_blue/hillshade_135_30_z1.tif` - Blue channel (135° azimuth)

#### Terrain Analysis
- `Slope/slope.tif` - Slope analysis
- `Aspect/aspect.tif` - Aspect analysis
- `Color_relief/color_relief.tif` - Elevation color visualization
- `Slope_relief/slope_relief.tif` - Slope relief for blending

#### Composite Products  
- `HillshadeRgb/hillshade_rgb.tif` - RGB composite from 3 hillshades
- `HillshadeRgb/tint_overlay.tif` - Color relief tinted by RGB composite
- `HillshadeRgb/boosted_hillshade.tif` - Final blend (tint + slope)

#### PNG Visualizations
- `png_outputs/` directory with PNG versions of all TIFF files

## Workflow Validation

The test specifically validates the complete pipeline you requested:

1. ✅ **3 Hillshades**: Different azimuths (315°, 45°, 135°) for RGB channels
2. ✅ **RGB Composite**: Combines 3 hillshades into RGB bands
3. ✅ **Color Relief Tint**: Applies elevation colors as tint overlay  
4. ✅ **Slope Blending**: Final blend with slope for enhanced visualization
5. ✅ **PNG Generation**: All outputs converted to PNG for viewing

## Test Validation Criteria

The test passes when:

- ✅ DTM generation succeeds
- ✅ `process_all_raster_products()` completes without errors
- ✅ All expected output directories are created
- ✅ At least 90% of expected files are generated
- ✅ Key workflow files exist (3 hillshades, RGB composite, tint, final blend)
- ✅ Files have reasonable sizes (> 100KB)

## Integration Benefits

This test provides several advantages:

### 🎯 **Real Code Validation**
- Tests actual application functions, not test reimplementations
- Catches integration issues between DTM generation and raster processing
- Validates real configuration files (`hillshade.json`, `dtm.json`)

### 🔄 **Complete Workflow Testing**
- Ensures `process_all_raster_products()` orchestration works correctly
- Validates async processing and progress tracking
- Tests error handling and recovery

### 📊 **Production Accuracy**
- Same code path as web application LAZ processing
- Real hillshade configuration (315°, 45°, 135° azimuths)
- Authentic color relief and slope blending parameters

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the correct directory
2. **Missing Dependencies**: Install GDAL, PDAL, and required Python packages
3. **LAZ File Missing**: Verify `input/LAZ/FoxIsland.laz` exists
4. **Permission Issues**: Check write permissions for `output/` directory

### Debug Steps

1. **Check Prerequisites**:
   ```bash
   python -c "from processing.dtm import dtm; print('DTM import OK')"
   python -c "from processing.tiff_processing import process_all_raster_products; print('Pipeline import OK')"
   ```

2. **Verify LAZ File**:
   ```bash
   ls -la ../../input/LAZ/FoxIsland.laz
   ```

3. **Check Output Permissions**:
   ```bash
   mkdir -p ../../output/test && rmdir ../../output/test
   ```

### Memory Requirements

- **Minimum**: 4GB RAM
- **Recommended**: 8GB+ RAM for smooth processing
- **Storage**: ~500MB for all outputs

## Expected Output Summary

If successful, you should see:

- **~13 TIFF files**: Various terrain analysis products
- **~10 PNG files**: Visualization versions  
- **Complete directory structure**: Organized by processing type
- **Total size**: ~200-500MB depending on LAZ complexity

The key validation is that the 3-hillshade RGB workflow produces:
1. Three individual hillshades (315°, 45°, 135°)
2. RGB composite combining all three
3. Color relief tint overlay
4. Final slope-enhanced blend

This confirms the complete blending/mixing pipeline is working correctly for LAZ files.
