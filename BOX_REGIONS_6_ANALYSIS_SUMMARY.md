# Box_Regions_6 Spatial Coherence Analysis Results

## 🔍 Key Findings

### ✅ Positive Findings:
1. **All 8 files are valid and readable**
2. **Consistent CRS**: All files use EPSG:4326 (WGS84 Geographic)
3. **Consistent resolution**: All files have 0.000278° pixel resolution (~30m)
4. **All files located in South America** (-3° to -4°S, -63° to -64°W)
5. **SVF file has 100% valid pixels** - indicating good data quality

### ❌ Major Issues Detected:

#### 1. **Dimension Mismatch** (Critical)
- **DTM group**: 810x810 pixels
  - `3.787S_63.734W_elevation.tiff` (original DTM)
  - `3.787S_63.734W_elevation_color_relief.tif`
  - `3.787S_63.734W_elevation_slope_relief.tif`
  - `3.787S_63.734W_elevation_LRM_adaptive.tif`
  - `3.787S_63.734W_elevation_Sky_View_Factor.tif`

- **DSM/CHM group**: 3600x3600 pixels  
  - `Box_Regions_6_copernicus_dsm_30m.tif`
  - `3.787S_63.734W_elevation_CHM.tif`

#### 2. **Spatial Extent Mismatch** (Critical)
- **DTM group extent**: 
  - West: -63.846°, East: -63.621°
  - South: -3.900°, North: -3.675°
  - **Size**: ~0.225° × 0.225° (~25km × 25km)

- **DSM/CHM group extent**:
  - West: -64.000°, East: -63.000° 
  - South: -4.000°, North: -3.000°
  - **Size**: 1.000° × 1.000° (~111km × 111km)

#### 3. **Data Quality Issues**
- **Most files show 0.0% valid pixels**, indicating heavy masking or NoData values
- Only **SVF file has usable data** (100% valid pixels)
- **CHM calculation impossible** due to DTM/DSM spatial mismatch

## 🚨 Critical Problems

### **The CHM Problem**
The CHM (Canopy Height Model) requires DTM and DSM to have:
- ✅ Same CRS (EPSG:4326) - **ACHIEVED**
- ✅ Same resolution (0.000278°) - **ACHIEVED** 
- ❌ Same spatial extent - **FAILED**
- ❌ Same dimensions - **FAILED**

**Result**: CHM = DSM - DTM is spatially invalid because:
1. DTM covers ~25km × 25km area
2. DSM covers ~111km × 111km area (16x larger)
3. DTM is subset within DSM bounds but misaligned

### **Data Processing Pipeline Issues**
1. **DTM source**: Original elevation data at ~25km extent
2. **DSM source**: Copernicus 30m DSM at ~111km extent  
3. **No spatial alignment** between data sources
4. **CHM processing** should have failed but generated invalid result

## 📋 Recommended Actions

### **Immediate Fixes**
1. **Crop DSM to DTM extent** OR **Expand DTM to DSM extent**
2. **Resample to consistent dimensions** (810x810 or 3600x3600)
3. **Re-calculate CHM** after spatial alignment
4. **Validate all derivative products** after realignment

### **Pipeline Improvements**
1. **Add spatial validation** before CHM calculation
2. **Implement automatic resampling/cropping** for mismatched inputs
3. **Add data quality checks** to detect masked/invalid data
4. **Enhance error reporting** for spatial mismatches

### **Quality Control**
1. **Visual inspection** of all raster products
2. **Cross-validation** of CHM values (should be 0-50m typically)
3. **Boundary checking** for all derivative products
4. **Data statistics validation** to ensure realistic ranges

## 🎯 Technical Specifications

### **Current State**:
- Resolution: 0.000278° (~30m at equator)
- CRS: EPSG:4326 (Geographic WGS84)
- DTM: 810×810 pixels, 25km×25km extent
- DSM: 3600×3600 pixels, 111km×111km extent
- CHM: Invalid (calculated from mismatched inputs)

### **Target State**:
- Resolution: Maintain 0.000278° 
- CRS: Keep EPSG:4326
- All rasters: **Consistent dimensions and extent**
- CHM: **Valid calculation from aligned DTM/DSM**
- Data quality: **>90% valid pixels for terrain data**

---

**Priority**: 🔥 **CRITICAL** - CHM and all derived products are spatially invalid
**Impact**: 🚨 **HIGH** - Affects all downstream archaeological analysis
**Effort**: 💻 **MEDIUM** - Requires reprocessing with spatial alignment
