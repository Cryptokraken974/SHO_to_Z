# LRM (Local Relief Model) Implementation - COMPLETE

## 🎉 Implementation Status: ✅ COMPLETE

The LRM (Local Relief Model) implementation for archaeological analysis is now fully complete and integrated into the SHO to Z application.

## 📋 Implementation Summary

### ✅ Backend Implementation (Complete)

1. **LRM Processing Function** (`app/processing/lrm.py`)
   - Async `process_lrm()` function for LAZ file processing
   - Main `lrm()` function that generates LRM from DTM using uniform filter smoothing
   - Quality mode integration (automatically uses clean LAZ files when available)
   - Proper caching and output directory structure
   - Window size parameter (default: 11 pixels)
   - Formula: `LRM = elevation_array - smooth_elevation_array`

2. **Specialized Archaeological Visualization** (`app/convert.py`)
   - `convert_lrm_to_coolwarm_png()` function for specialized visualization
   - Percentile-based contrast stretching (2nd to 98th percentile by default)
   - Coolwarm diverging colormap application:
     - **Blue** = Depressions/valleys (negative relief)
     - **White** = Neutral/flat areas (zero relief)
     - **Red** = Elevated terrain/ridges (positive relief)
   - High-resolution PNG generation with georeferencing
   - World file creation for proper overlay scaling

3. **API Endpoint** (`app/endpoints/laz_processing.py`)
   - `/api/lrm` endpoint with comprehensive parameters:
     - `window_size`: Filter window size (default: 11)
     - `use_coolwarm_colormap`: Enable specialized visualization (default: True)
     - `percentile_clip_min/max`: Contrast stretching percentiles (default: 2%, 98%)
     - `stretch_type` and `stretch_params_json`: Alternative visualization options
   - Base64 image return for frontend display
   - Specialized archaeological visualization by default

4. **Module Integration**
   - LRM imports added to processing module `__init__.py`
   - LRM and coolwarm conversion imports added to laz_processing endpoints
   - Base64 import for PNG conversion

### ✅ Frontend Integration (Complete)

1. **API Client** (`frontend/js/api-client.js`)
   - `generateLRM()` method in ProcessingAPIClient
   - Support for both camelCase and snake_case parameters
   - LRM-specific parameters (windowSize, useCoolwarmColormap, percentileClip)
   - Added to processRegion method mapping

2. **Processing Manager** (`frontend/js/processing.js`)
   - `processLRM()` method with default archaeological parameters
   - Integrated into `sendProcess()` routing (case 'lrm')
   - Added to processAllRasters queue
   - LRM display name configuration

3. **UI Integration**
   - LRM already included in LAZ modal queue (`laz-queue-lrm`)
   - Processing queue visual indicators
   - Display name: "Local Relief Model"
   - Icon: 📏

### ✅ Quality Mode Integration

The LRM implementation includes full quality mode support:
- Automatically detects and uses clean LAZ files when available
- Searches for clean LAZ files in multiple locations:
  - `output/{region}/cropped/{region}_cropped.las`
  - `output/{region}/lidar/cropped/{region}_cropped.las`
- Adds "_clean" suffix to output filenames when quality mode is used
- Logging indicates whether standard or quality mode is active

## 🎯 Archaeological Benefits

### Enhanced Feature Detection
- **Percentile-based contrast stretching** enhances subtle relief variations
- **Coolwarm diverging colormap** makes anthropogenic features stand out
- **Local relief calculation** removes regional trends, highlighting local modifications

### Optimal Parameters for Archaeology
- **Window size: 11 pixels** - Good balance for detecting human-scale features
- **2%-98% percentile clipping** - Removes extreme outliers while preserving detail
- **Coolwarm colormap** - Intuitive visualization for archaeological interpretation

### Feature Interpretation
- **Blue areas** = Potential archaeological depressions (ditches, pits, foundations)
- **Red areas** = Potential archaeological elevations (mounds, walls, earthworks)
- **White areas** = Neutral terrain with minimal local relief variation

## 🚀 Usage Instructions

### For Individual LAZ Files:
1. Load a LAZ file using "Load LAZ" button
2. Click "Generate Rasters" to process all terrain analysis products
3. LRM will be automatically included in the processing queue
4. View results in the raster gallery with coolwarm visualization

### For Batch Processing:
1. Use the complete LAZ workflow with quality mode
2. LRM will automatically use clean LAZ files when available
3. Results saved to: `output/{region}/lidar/png_outputs/LRM_coolwarm.png`

### API Usage:
```javascript
// Process LRM with custom parameters
await ProcessingManager.processLRM({
  windowSize: 15,
  useCoolwarmColormap: true,
  percentileClipMin: 1.0,
  percentileClipMax: 99.0
});

// Or use API client directly
await APIClient.processing.generateLRM({
  regionName: 'my-region',
  processingType: 'lrm',
  windowSize: 11,
  useCoolwarmColormap: true
});
```

## 📁 Output Files

### Generated Files:
- **LRM TIF**: `output/{region}/lidar/LRM/{region}_LRM.tif` (or `_clean.tif`)
- **Coolwarm PNG**: `output/{region}/lidar/png_outputs/LRM_coolwarm.png`
- **World Files**: `.pgw` and `_wgs84.wld` for georeferencing

### File Properties:
- **Format**: 32-bit float GeoTIFF (preserves sign and precision)
- **Compression**: LZW compression with tiling
- **NoData**: -9999 for invalid areas
- **Visualization**: High-resolution PNG (300 DPI) with archaeological colormap

## 🧪 Testing

Run the integration test:
```javascript
// Load in browser console
loadScript('/frontend/js/tests/lrm-integration-test.js');
```

## 📚 Technical Implementation Details

### Algorithm:
1. **DTM Generation**: Create or load Digital Terrain Model from LAZ
2. **Smoothing**: Apply uniform filter with specified window size
3. **Relief Calculation**: `LRM = DTM - smooth(DTM)`
4. **Contrast Stretching**: Clip to percentile range for optimal contrast
5. **Colormap Application**: Apply coolwarm diverging colormap
6. **Export**: Save as GeoTIFF and high-resolution PNG

### Performance:
- **Caching**: Automatic caching prevents redundant processing
- **Quality Mode**: Automatically uses cleaned data when available  
- **Memory Efficient**: Processes in chunks for large datasets
- **Fast Processing**: Optimized scipy uniform_filter implementation

## 🎉 Ready for Production

The LRM implementation is complete and ready for archaeological analysis:

✅ **Backend Processing**: Complete with quality mode integration  
✅ **Specialized Visualization**: Coolwarm archaeological colormap  
✅ **Frontend Integration**: Full API and UI integration  
✅ **Documentation**: Comprehensive user and technical documentation  
✅ **Testing**: Integration tests and validation  

**The LRM feature enhances the SHO to Z application's archaeological capabilities by providing specialized local relief analysis with optimal visualization for detecting subtle anthropogenic landscape modifications.**
