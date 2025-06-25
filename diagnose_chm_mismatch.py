#!/usr/bin/env python3
"""
Diagnostic script to analyze spatial mismatches between DTM and DSM for CHM generation.
This will help identify why your CHM calculation might be failing.
"""

import os
import sys
import rasterio
import numpy as np
from pathlib import Path

def analyze_raster_properties(file_path, raster_type):
    """Analyze and display key properties of a raster file."""
    print(f"\n{'='*50}")
    print(f"🔍 ANALYZING {raster_type.upper()}: {os.path.basename(file_path)}")
    print(f"{'='*50}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    try:
        with rasterio.open(file_path) as src:
            # Basic properties
            print(f"📊 Basic Properties:")
            print(f"   Width: {src.width} pixels")
            print(f"   Height: {src.height} pixels")
            print(f"   Bands: {src.count}")
            print(f"   Data type: {src.dtypes[0]}")
            print(f"   No data value: {src.nodata}")
            
            # Coordinate system
            print(f"\n🌍 Spatial Reference:")
            print(f"   CRS: {src.crs}")
            print(f"   EPSG: {src.crs.to_epsg() if src.crs else 'Unknown'}")
            
            # Geotransform and resolution
            transform = src.transform
            print(f"\n📐 Geospatial Properties:")
            print(f"   Pixel width: {abs(transform[0]):.6f} units")
            print(f"   Pixel height: {abs(transform[4]):.6f} units")
            print(f"   Origin X: {transform[2]:.6f}")
            print(f"   Origin Y: {transform[5]:.6f}")
            
            # Bounds
            bounds = src.bounds
            print(f"\n📦 Bounds:")
            print(f"   Left: {bounds.left:.6f}")
            print(f"   Bottom: {bounds.bottom:.6f}")
            print(f"   Right: {bounds.right:.6f}")
            print(f"   Top: {bounds.top:.6f}")
            print(f"   Width: {bounds.right - bounds.left:.6f} units")
            print(f"   Height: {bounds.top - bounds.bottom:.6f} units")
            
            # Data statistics
            try:
                data = src.read(1)
                valid_data = data[data != src.nodata] if src.nodata is not None else data
                valid_data = valid_data[~np.isnan(valid_data)]
                
                if len(valid_data) > 0:
                    print(f"\n📈 Data Statistics:")
                    print(f"   Min: {np.min(valid_data):.3f}")
                    print(f"   Max: {np.max(valid_data):.3f}")
                    print(f"   Mean: {np.mean(valid_data):.3f}")
                    print(f"   Valid pixels: {len(valid_data):,}")
                    print(f"   Total pixels: {data.size:,}")
                    print(f"   Coverage: {len(valid_data)/data.size*100:.1f}%")
                else:
                    print(f"\n⚠️ No valid data found in raster")
            except Exception as e:
                print(f"\n⚠️ Could not read data statistics: {e}")
            
            return {
                'width': src.width,
                'height': src.height,
                'crs': src.crs,
                'transform': src.transform,
                'bounds': src.bounds,
                'data_type': src.dtypes[0],
                'nodata': src.nodata
            }
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def compare_rasters(dtm_info, dsm_info):
    """Compare two raster datasets and identify mismatches."""
    print(f"\n{'='*50}")
    print(f"🔍 COMPARISON ANALYSIS")
    print(f"{'='*50}")
    
    if not dtm_info or not dsm_info:
        print("❌ Cannot compare - missing raster information")
        return
    
    # Dimension comparison
    print(f"📊 Dimension Comparison:")
    print(f"   DTM: {dtm_info['width']} x {dtm_info['height']} pixels")
    print(f"   DSM: {dsm_info['width']} x {dsm_info['height']} pixels")
    if dtm_info['width'] != dsm_info['width'] or dtm_info['height'] != dsm_info['height']:
        print(f"   ⚠️ DIMENSION MISMATCH DETECTED")
    else:
        print(f"   ✅ Dimensions match")
    
    # CRS comparison
    print(f"\n🌍 Coordinate System Comparison:")
    print(f"   DTM CRS: {dtm_info['crs']}")
    print(f"   DSM CRS: {dsm_info['crs']}")
    if dtm_info['crs'] != dsm_info['crs']:
        print(f"   ⚠️ CRS MISMATCH DETECTED")
    else:
        print(f"   ✅ CRS match")
    
    # Resolution comparison
    dtm_res_x = abs(dtm_info['transform'][0])
    dtm_res_y = abs(dtm_info['transform'][4])
    dsm_res_x = abs(dsm_info['transform'][0])
    dsm_res_y = abs(dsm_info['transform'][4])
    
    print(f"\n📐 Resolution Comparison:")
    print(f"   DTM: {dtm_res_x:.6f} x {dtm_res_y:.6f} units/pixel")
    print(f"   DSM: {dsm_res_x:.6f} x {dsm_res_y:.6f} units/pixel")
    
    res_diff_x = abs(dtm_res_x - dsm_res_x)
    res_diff_y = abs(dtm_res_y - dsm_res_y)
    
    if res_diff_x > 0.001 or res_diff_y > 0.001:
        print(f"   ⚠️ RESOLUTION MISMATCH DETECTED")
        print(f"   Difference X: {res_diff_x:.6f}")
        print(f"   Difference Y: {res_diff_y:.6f}")
    else:
        print(f"   ✅ Resolutions match")
    
    # Spatial extent comparison
    dtm_bounds = dtm_info['bounds']
    dsm_bounds = dsm_info['bounds']
    
    print(f"\n📦 Spatial Extent Comparison:")
    print(f"   DTM bounds: {dtm_bounds.left:.3f}, {dtm_bounds.bottom:.3f}, {dtm_bounds.right:.3f}, {dtm_bounds.top:.3f}")
    print(f"   DSM bounds: {dsm_bounds.left:.3f}, {dsm_bounds.bottom:.3f}, {dsm_bounds.right:.3f}, {dsm_bounds.top:.3f}")
    
    # Calculate overlap
    overlap_left = max(dtm_bounds.left, dsm_bounds.left)
    overlap_bottom = max(dtm_bounds.bottom, dsm_bounds.bottom)
    overlap_right = min(dtm_bounds.right, dsm_bounds.right)
    overlap_top = min(dtm_bounds.top, dsm_bounds.top)
    
    if overlap_left < overlap_right and overlap_bottom < overlap_top:
        overlap_width = overlap_right - overlap_left
        overlap_height = overlap_top - overlap_bottom
        overlap_area = overlap_width * overlap_height
        
        dtm_area = (dtm_bounds.right - dtm_bounds.left) * (dtm_bounds.top - dtm_bounds.bottom)
        dsm_area = (dsm_bounds.right - dsm_bounds.left) * (dsm_bounds.top - dsm_bounds.bottom)
        
        overlap_percent_dtm = (overlap_area / dtm_area) * 100
        overlap_percent_dsm = (overlap_area / dsm_area) * 100
        
        print(f"\n✅ SPATIAL OVERLAP DETECTED:")
        print(f"   Overlap bounds: {overlap_left:.3f}, {overlap_bottom:.3f}, {overlap_right:.3f}, {overlap_top:.3f}")
        print(f"   Overlap area: {overlap_area:.6f} square units")
        print(f"   DTM coverage: {overlap_percent_dtm:.1f}%")
        print(f"   DSM coverage: {overlap_percent_dsm:.1f}%")
        
        if overlap_percent_dtm < 50 or overlap_percent_dsm < 50:
            print(f"   ⚠️ LOW OVERLAP - CHM quality may be poor")
        else:
            print(f"   ✅ Good overlap for CHM generation")
    else:
        print(f"\n❌ NO SPATIAL OVERLAP - CHM generation will fail")

def find_files_in_directory(directory, file_pattern):
    """Find files matching a pattern in a directory."""
    if not os.path.exists(directory):
        return []
    
    matching_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file_pattern.lower() in file.lower() and file.endswith('.tif'):
                matching_files.append(os.path.join(root, file))
    return matching_files

def main():
    """Main diagnostic function."""
    print("🔍 CHM SPATIAL MISMATCH DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Check if we're in the correct workspace
    current_dir = os.getcwd()
    if "SHO_to_Z" not in current_dir:
        print("⚠️ Make sure you're running this from the SHO_to_Z workspace")
    
    # Look for DTM and DSM files in common locations
    search_directories = [
        "output",
        "input",
        "input/LAZ",
        "output/*/lidar",
        "output/*/lidar/DTM",
        "output/*/lidar/DSM"
    ]
    
    dtm_files = []
    dsm_files = []
    
    print("\n🔍 Searching for DTM and DSM files...")
    
    for search_dir in search_directories:
        # Handle glob patterns
        if "*" in search_dir:
            from glob import glob
            expanded_dirs = glob(search_dir)
            for exp_dir in expanded_dirs:
                dtm_files.extend(find_files_in_directory(exp_dir, "dtm"))
                dsm_files.extend(find_files_in_directory(exp_dir, "dsm"))
        else:
            dtm_files.extend(find_files_in_directory(search_dir, "dtm"))
            dsm_files.extend(find_files_in_directory(search_dir, "dsm"))
    
    # Remove duplicates
    dtm_files = list(set(dtm_files))
    dsm_files = list(set(dsm_files))
    
    print(f"\n📁 Found Files:")
    print(f"   DTM files: {len(dtm_files)}")
    for i, dtm in enumerate(dtm_files):
        print(f"      {i+1}. {dtm}")
    
    print(f"   DSM files: {len(dsm_files)}")
    for i, dsm in enumerate(dsm_files):
        print(f"      {i+1}. {dsm}")
    
    if not dtm_files:
        print("\n❌ No DTM files found. Make sure you have processed DTM data.")
        return
    
    if not dsm_files:
        print("\n❌ No DSM files found. Make sure you have Copernicus DSM data.")
        print("💡 Tip: Download DSM data using the Copernicus acquisition feature")
        return
    
    # If we have multiple files, use the first ones for analysis
    dtm_file = dtm_files[0]
    dsm_file = dsm_files[0]
    
    if len(dtm_files) > 1 or len(dsm_files) > 1:
        print(f"\n💡 Multiple files found. Analyzing:")
        print(f"   DTM: {dtm_file}")
        print(f"   DSM: {dsm_file}")
        print(f"\n   To analyze different files, modify the script or specify files manually.")
    
    # Analyze both files
    dtm_info = analyze_raster_properties(dtm_file, "DTM")
    dsm_info = analyze_raster_properties(dsm_file, "DSM")
    
    # Compare them
    compare_rasters(dtm_info, dsm_info)
    
    # Provide recommendations
    print(f"\n{'='*50}")
    print(f"💡 RECOMMENDATIONS")
    print(f"{'='*50}")
    
    if not dtm_info or not dsm_info:
        print("❌ Cannot provide recommendations due to file reading errors")
        return
    
    # Check for common issues
    has_dimension_mismatch = (dtm_info['width'] != dsm_info['width'] or 
                             dtm_info['height'] != dsm_info['height'])
    has_crs_mismatch = dtm_info['crs'] != dsm_info['crs']
    
    dtm_res_x = abs(dtm_info['transform'][0])
    dsm_res_x = abs(dsm_info['transform'][0])
    has_resolution_mismatch = abs(dtm_res_x - dsm_res_x) > 0.001
    
    if has_dimension_mismatch:
        print("🔧 DIMENSION MISMATCH:")
        print("   - Your CHM processing should handle this automatically")
        print("   - The DTM will be resampled to match the DSM")
        print("   - Check the console output during CHM processing for resampling messages")
    
    if has_crs_mismatch:
        print("🔧 CRS MISMATCH:")
        print("   - This requires coordinate system transformation")
        print("   - The CHM processing should handle this with rasterio.warp.reproject")
        print("   - Verify both files use compatible coordinate systems")
    
    if has_resolution_mismatch:
        print("🔧 RESOLUTION MISMATCH:")
        print(f"   - DTM resolution: {dtm_res_x:.6f} units/pixel")
        print(f"   - DSM resolution: {dsm_res_x:.6f} units/pixel")
        print("   - CHM will be generated at the DSM resolution")
        print("   - Consider if this resolution is appropriate for your analysis")
    
    # Calculate overlap
    dtm_bounds = dtm_info['bounds']
    dsm_bounds = dsm_info['bounds']
    overlap_left = max(dtm_bounds.left, dsm_bounds.left)
    overlap_bottom = max(dtm_bounds.bottom, dsm_bounds.bottom)
    overlap_right = min(dtm_bounds.right, dsm_bounds.right)
    overlap_top = min(dtm_bounds.top, dsm_bounds.top)
    
    if overlap_left >= overlap_right or overlap_bottom >= overlap_top:
        print("❌ NO SPATIAL OVERLAP:")
        print("   - DTM and DSM do not cover the same area")
        print("   - CHM generation will fail")
        print("   - Verify you downloaded the correct DSM area")
        print("   - Check coordinate systems are compatible")
    else:
        overlap_area = (overlap_right - overlap_left) * (overlap_top - overlap_bottom)
        dtm_area = (dtm_bounds.right - dtm_bounds.left) * (dtm_bounds.top - dtm_bounds.bottom)
        overlap_percent = (overlap_area / dtm_area) * 100
        
        if overlap_percent < 25:
            print("⚠️ LOW SPATIAL OVERLAP:")
            print(f"   - Only {overlap_percent:.1f}% of DTM area is covered by DSM")
            print("   - CHM will only be valid in the overlap area")
            print("   - Consider downloading a larger DSM area")
        elif overlap_percent < 75:
            print("✅ PARTIAL SPATIAL OVERLAP:")
            print(f"   - {overlap_percent:.1f}% of DTM area is covered by DSM")
            print("   - CHM generation should work for the overlap area")
        else:
            print("✅ GOOD SPATIAL OVERLAP:")
            print(f"   - {overlap_percent:.1f}% of DTM area is covered by DSM")
            print("   - CHM generation should work well")
    
    print(f"\n🚀 NEXT STEPS:")
    print("   1. If spatial overlap is good, try running CHM processing again")
    print("   2. Check the console output for detailed resampling information")
    print("   3. If issues persist, the problem may be in the resampling logic")
    print("   4. Consider cropping the DSM to better match your DTM extent")

if __name__ == "__main__":
    main()
