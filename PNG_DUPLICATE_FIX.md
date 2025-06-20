# PNG Duplicate Generation Fix

## Problem
The system was generating duplicate PNG files with different naming conventions:
- **Short names** (preferred): `LRM.png`, `SVF.png`, `Slope.png`, etc.
- **Long names** (duplicates): `REGION_DTM_1.0m_csf1.0m_filled_LRM.png`, etc.

Example duplicates found:
```
/output/PRGL1260C9597_2014/lidar/png_outputs/
├── LRM.png                                              # ✅ Keep (preferred)
├── PRGL1260C9597_2014_DTM_1.0m_csf1.0m_filled_LRM.png  # ❌ Remove (duplicate)
├── HillshadeRGB.png                                     # ✅ Keep (preferred)  
├── hillshade_rgb.png                                    # ❌ Remove (duplicate)
└── ...
```

## Root Cause
The `convert_geotiff_to_png()` function in `app/convert.py` had a `save_to_consolidated` feature that would:

1. Create the requested PNG file (e.g., `LRM.png` in `png_outputs/`)
2. **Also** copy it to the consolidated directory with the full TIFF filename

This caused duplication when the PNG was already being created directly in the `png_outputs` directory by the processing pipeline.

## Solution

### 1. Fixed convert_geotiff_to_png()
Modified `app/convert.py` to detect when the target PNG path is already within the `png_outputs` directory and skip the duplicate consolidated copy:

```python
# Check if the PNG is already being created directly in png_outputs directory
png_normalized = os.path.normpath(png_path)
consolidated_normalized = os.path.normpath(consolidated_dir)

if consolidated_normalized in png_normalized:
    print(f"ℹ️ PNG already in png_outputs directory, skipping duplicate consolidated copy: {png_path}")
else:
    # Only create consolidated copy if not already in png_outputs
    # ... copy logic ...
```

### 2. Cleaned Up Existing Duplicates
Created and ran `cleanup_duplicate_pngs.py` to remove existing duplicate files:

- **Pattern duplicates**: Files matching `*_LRM.png`, `*_Sky_View_Factor.png`, etc. when short versions exist
- **Case duplicates**: Files like `hillshade_rgb.png` when `HillshadeRGB.png` exists
- **Space saved**: ~10MB across all regions

### 3. Verified Fix
Created `test_png_duplicate_fix.py` to verify the fix works correctly:
- ✅ No duplicate files created when PNG target is in `png_outputs/`
- ✅ Consolidated copy logic still works for other directories
- ✅ Proper detection and logging of skip behavior

## Results

**Before Fix:**
```
png_outputs/
├── LRM.png                                     (20KB)
├── REGION_DTM_filled_LRM.png                   (20KB) ← Duplicate!
├── HillshadeRGB.png                           (282KB)
├── hillshade_rgb.png                          (282KB) ← Duplicate!
└── ...
```

**After Fix:**
```
png_outputs/
├── LRM.png                                     (20KB) ✅
├── HillshadeRGB.png                           (282KB) ✅  
├── SVF.png                                     (98KB) ✅
├── Slope.png                                  (100KB) ✅
└── TintOverlay.png                            (132KB) ✅
```

## Files Modified
- `app/convert.py` - Added duplicate detection logic
- `cleanup_duplicate_pngs.py` - Script to clean existing duplicates  
- `test_png_duplicate_fix.py` - Test to verify fix works

## Benefits
1. **Storage savings**: ~10MB saved by removing duplicates
2. **Cleaner file organization**: Only preferred short names remain
3. **Future-proof**: Prevents new duplicates from being created
4. **Backwards compatible**: Existing functionality preserved for other use cases
