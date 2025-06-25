#!/usr/bin/env python3
"""
Debug CHM spatial alignment for Box_Regions_7

This script will diagnose exactly why the CHM is coming out as all zeros.
"""

import rasterio
import numpy as np
from rasterio.windows import from_bounds
import tempfile
import os

def debug_chm_alignment():
    """Debug the CHM spatial alignment process"""
    
    print("🔍 CHM SPATIAL ALIGNMENT DEBUG - Box_Regions_7")
    print("=" * 60)
    
    # File paths
    dtm_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/Box_Regions_7/3.787S_63.673W_elevation/Original/3.787S_63.673W_elevation.tiff"
    dsm_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/Box_Regions_7/lidar/DSM/Box_Regions_7_copernicus_dsm_30m.tif"
    
    print(f"📁 DTM: {os.path.basename(dtm_path)}")
    print(f"📁 DSM: {os.path.basename(dsm_path)}")
    
    # Open both files
    with rasterio.open(dtm_path) as dtm_src, rasterio.open(dsm_path) as dsm_src:
        
        # Get spatial properties
        dtm_bounds = dtm_src.bounds
        dsm_bounds = dsm_src.bounds
        dtm_res = dtm_src.res
        dsm_res = dsm_src.res
        
        print(f"\n📊 SPATIAL PROPERTIES:")
        print(f"DTM: {dtm_src.width}×{dtm_src.height}, res={dtm_res}")
        print(f"DSM: {dsm_src.width}×{dsm_src.height}, res={dsm_res}")
        
        print(f"\n📍 BOUNDS COMPARISON:")
        print(f"DTM bounds: {dtm_bounds}")
        print(f"DSM bounds: {dsm_bounds}")
        
        # Check overlap
        overlap_left = max(dtm_bounds.left, dsm_bounds.left)
        overlap_right = min(dtm_bounds.right, dsm_bounds.right)
        overlap_bottom = max(dtm_bounds.bottom, dsm_bounds.bottom)
        overlap_top = min(dtm_bounds.top, dsm_bounds.top)
        
        has_overlap = (overlap_left < overlap_right and overlap_bottom < overlap_top)
        
        print(f"\n🔗 OVERLAP ANALYSIS:")
        print(f"Overlap bounds: ({overlap_left:.6f}, {overlap_bottom:.6f}) to ({overlap_right:.6f}, {overlap_top:.6f})")
        print(f"Has overlap: {has_overlap}")
        
        if has_overlap:
            overlap_width = overlap_right - overlap_left
            overlap_height = overlap_top - overlap_bottom
            print(f"Overlap size: {overlap_width:.6f}° × {overlap_height:.6f}°")
        
        # Test the windowing operation that's failing
        print(f"\n🔧 TESTING WINDOWING OPERATION:")
        
        try:
            # This is the problematic line from the CHM code
            window = from_bounds(*dtm_bounds, dsm_src.transform)
            print(f"✅ Window calculation succeeded: {window}")
            print(f"   Window size: {window.width} × {window.height}")
            print(f"   Window valid: {window.width > 0 and window.height > 0}")
            
            # Check if window is within DSM bounds
            window_in_bounds = (window.col_off >= 0 and window.row_off >= 0 and 
                              window.col_off + window.width <= dsm_src.width and
                              window.row_off + window.height <= dsm_src.height)
            print(f"   Window within DSM: {window_in_bounds}")
            
            if not window_in_bounds:
                print(f"   ⚠️  PROBLEM: Window extends outside DSM boundaries!")
                print(f"   DSM size: {dsm_src.width} × {dsm_src.height}")
                print(f"   Window needs: {window.col_off + window.width} × {window.row_off + window.height}")
            
            # Try to read the data
            print(f"\n📖 TESTING DATA READ:")
            cropped_data = dsm_src.read(1, window=window)
            print(f"✅ Data read succeeded: shape {cropped_data.shape}")
            
            # Check data content
            valid_data = cropped_data[~np.isnan(cropped_data)]
            if len(valid_data) > 0:
                print(f"   📊 Valid data: {len(valid_data):,} pixels")
                print(f"   📈 Range: {np.min(valid_data):.2f} to {np.max(valid_data):.2f}")
                print(f"   📊 Mean: {np.mean(valid_data):.2f}")
            else:
                print(f"   ❌ NO VALID DATA - all pixels are NaN/NoData!")
                
            # Check for specific values
            zero_count = np.sum(cropped_data == 0)
            nan_count = np.sum(np.isnan(cropped_data))
            print(f"   🔢 Zero pixels: {zero_count:,}")
            print(f"   🔢 NaN pixels: {nan_count:,}")
            
        except Exception as e:
            print(f"❌ Window operation failed: {e}")
        
        # Test reading DTM data for comparison
        print(f"\n📖 DTM DATA CHECK:")
        dtm_data = dtm_src.read(1)
        dtm_valid = dtm_data[~np.isnan(dtm_data)]
        if len(dtm_valid) > 0:
            print(f"   📊 DTM valid data: {len(dtm_valid):,} pixels") 
            print(f"   📈 DTM range: {np.min(dtm_valid):.2f} to {np.max(dtm_valid):.2f}")
            print(f"   📊 DTM mean: {np.mean(dtm_valid):.2f}")
        
        # Test reading DSM data for comparison
        print(f"\n📖 DSM DATA CHECK:")
        dsm_data = dsm_src.read(1)
        dsm_valid = dsm_data[~np.isnan(dsm_data)]
        if len(dsm_valid) > 0:
            print(f"   📊 DSM valid data: {len(dsm_valid):,} pixels")
            print(f"   📈 DSM range: {np.min(dsm_valid):.2f} to {np.max(dsm_valid):.2f}")
            print(f"   📊 DSM mean: {np.mean(dsm_valid):.2f}")

    print(f"\n🎯 DIAGNOSIS COMPLETE")

if __name__ == "__main__":
    debug_chm_alignment()
