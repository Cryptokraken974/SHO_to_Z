# Folder Structure Update - Sentinel-2 Implementation

## Updated Folder Structure Rules

The Sentinel-2 download and processing now follows the standardized folder structure:

### 1. **Input Folder**: `input/<region_name>/`
- **Purpose**: Stores raw downloaded satellite data
- **Contents**: Original TIF files from Copernicus Data Space Ecosystem
- **Example**: `input/test_portland_new/test_portland_new_20250524_sentinel2.tif`

### 2. **Output Folder**: `output/<region_name>/sentinel2/`
- **Purpose**: Stores processed and converted files
- **Contents**: Extracted band TIF files, PNG images, and world files
- **Example Files**:
  - `output/test_portland_new/sentinel2/test_portland_new_20250524_sentinel2_RED_B04.tif`
  - `output/test_portland_new/sentinel2/test_portland_new_20250524_sentinel2_RED_B04.png`
  - `output/test_portland_new/sentinel2/test_portland_new_20250524_sentinel2_NIR_B08.tif`
  - `output/test_portland_new/sentinel2/test_portland_new_20250524_sentinel2_NIR_B08.png`

## Code Changes Made

### 1. **CopernicusSentinel2Source** (`app/data_acquisition/sources/copernicus_sentinel2.py`)
- **BEFORE**: Downloaded to `data_cache/<region_name>/sentinel2/`
- **AFTER**: Downloads to `input/<region_name>/`
- **Change**: Lines 502-522 updated to use standard input folder structure

### 2. **Conversion API** (`app/main.py`)
- **BEFORE**: Read from `data/acquired/<region_name>/sentinel2/`
- **AFTER**: Reads from `input/<region_name>/`
- **Change**: Lines 1269-1277 updated to use input folder as source

### 3. **Conversion Function** (`app/convert.py`)
- **BEFORE**: Expected input from `data/acquired/` structure
- **AFTER**: Processes from `input/<region_name>/` and outputs to `output/<region_name>/sentinel2/`
- **Change**: Documentation updated to reflect new folder structure

## Data Flow

```
1. User clicks "Test: Sentinel2 Images" button
   ↓
2. Frontend calls /api/download-sentinel2
   ↓
3. Backend downloads to: input/<region_name>/
   ↓
4. Frontend automatically calls /api/convert-sentinel2
   ↓
5. Backend processes from: input/<region_name>/
   ↓
6. Backend outputs to: output/<region_name>/sentinel2/
   ↓
7. Gallery displays processed images
```

## Benefits

1. **Consistency**: Follows the same pattern as LiDAR processing
2. **Clear Separation**: Raw data in `input/`, processed data in `output/`
3. **Organized**: Satellite-specific outputs grouped under `sentinel2/` subfolder
4. **Maintainable**: Easier to understand and debug folder structure

## Testing

✅ **Tested with**: Portland, Oregon coordinates (45.5152, -122.6784)
✅ **Result**: Proper folder creation and file processing
✅ **Conversion**: RED and NIR bands successfully extracted and converted to PNG
✅ **Gallery**: Images ready for display and overlay functionality

The implementation now correctly follows your folder structure rules and maintains consistency across the entire application.
