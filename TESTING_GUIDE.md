# Testing Guide - Region Selection API Call Optimization

## Issue Fixed
- **Problem**: API calls for PNG images (elevation and satellite) were being triggered when users simply clicked on region names in the "Select Region" modal, causing unnecessary API calls for images that may not exist.
- **Solution**: Separated region browsing (clicking on items) from region selection (confirming choice) so API calls only happen when users actually select a region.

## Changes Made

### 1. Modified `fileManager.js`
- **File**: `/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/frontend/js/fileManager.js`
- **Change**: Updated region item click handlers to only highlight regions instead of immediately selecting them
- **Before**: Clicking region items immediately called `this.selectRegion()` which triggered API calls
- **After**: Clicking region items only highlights them and stores coordinate data for later use

### 2. Modified `ui.js`
- **File**: `/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/frontend/js/ui.js`
- **Change**: Updated the "Select Region" button handler to perform actual selection and API calls
- **Before**: Region items were selected on click, "Select Region" button just closed modal
- **After**: "Select Region" button now performs the actual selection which triggers API calls

## How to Test

### Test 1: Browse Regions Without API Calls
1. Open the application in a browser
2. Click "Select Region" button in the header
3. **Click on different region names in the modal**
4. **Expected Result**: 
   - Regions should highlight (visual selection) when clicked
   - **No API calls should be made** (check browser Network tab)
   - No satellite or elevation images should load in galleries
   - Delete button should appear when a region is highlighted

### Test 2: Confirm Selection Triggers API Calls
1. In the same modal, after clicking on a region name to highlight it
2. **Click the "Select Region" button** (blue button at bottom of modal)
3. **Expected Result**:
   - Modal should close
   - API calls should now be made to check for overlay data:
     - `/api/overlay/sentinel2/region_*` calls for satellite images
     - `/api/overlay/raster/region_*/hillshade`, `/api/overlay/raster/region_*/slope`, etc. for elevation data
   - Map should center on the selected region
   - Satellite gallery should populate with available images
   - Processing gallery should show available raster overlays

### Test 3: Cancel Without Selection
1. Open "Select Region" modal
2. Click on various region names to browse/highlight them
3. Click "Cancel" button
4. **Expected Result**:
   - Modal should close
   - No region should be selected
   - No API calls should have been made
   - No galleries should be updated

## API Call Monitoring

To verify the fix is working:

1. **Open browser Developer Tools** (F12)
2. **Go to Network tab**
3. **Filter by "api"** to see only API calls
4. **Clear the network log**
5. **Test the region browsing behavior**

### Expected Network Activity:

#### During Browsing (clicking region names):
- **No overlay API calls** should appear
- Only the initial `/api/list-regions` call when modal opens

#### During Selection (clicking "Select Region" button):
- **Multiple overlay API calls** should appear:
  - `/api/overlay/sentinel2/region_B02` (Blue band)
  - `/api/overlay/sentinel2/region_B03` (Green band)  
  - `/api/overlay/sentinel2/region_B04` (Red band)
  - `/api/overlay/sentinel2/region_B08` (NIR band)
  - `/api/overlay/raster/region/hillshade`
  - `/api/overlay/raster/region/slope`
  - `/api/overlay/raster/region/aspect`

## Benefits of This Fix

1. **Reduced Server Load**: No unnecessary API calls when users are just browsing region names
2. **Better User Experience**: Faster modal interaction when browsing regions
3. **Clearer Intent**: API calls only happen when user explicitly confirms selection
4. **Resource Efficiency**: Prevents checking for non-existent overlay files until actually needed

## Code Flow After Fix

1. **Modal Opens**: User clicks "Select Region" → `/api/list-regions` called to populate modal
2. **Browsing**: User clicks region names → Only visual highlighting, no API calls
3. **Selection**: User clicks "Select Region" button → Calls `selectRegion()` → Triggers overlay API calls
4. **Gallery Updates**: Available overlays populate satellite and processing galleries

This ensures overlay API calls only happen when users have made a deliberate choice to select a region.
