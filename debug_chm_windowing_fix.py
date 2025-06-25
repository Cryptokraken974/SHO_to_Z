#!/usr/bin/env python3
"""
Advanced CHM windowing debug and fix for Box_Regions_7

This script will test the exact windowing operation that's causing issues
and implement a corrected version of the spatial alignment.
"""

import rasterio
import numpy as np
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from rasterio.warp import reproject
import tempfile
import os

def debug_and_fix_chm_windowing():
    """Debug and fix the CHM windowing operation"""
    
    print("🔧 CHM WINDOWING DEBUG AND FIX - Box_Regions_7")
    print("=" * 70)
    
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
        dtm_crs = dtm_src.crs
        dsm_crs = dsm_src.crs
        
        print(f"\n📊 DETAILED SPATIAL ANALYSIS:")
        print(f"DTM: {dtm_src.width}×{dtm_src.height}, res={dtm_res}, CRS={dtm_crs}")
        print(f"DSM: {dsm_src.width}×{dsm_src.height}, res={dsm_res}, CRS={dsm_crs}")
        
        print(f"\n📍 COORDINATE SYSTEM CHECK:")
        print(f"CRS Match: {dtm_crs == dsm_crs}")
        if dtm_crs != dsm_crs:
            print(f"⚠️ CRS MISMATCH! DTM: {dtm_crs}, DSM: {dsm_crs}")
        
        print(f"\n📍 BOUNDS ANALYSIS:")
        print(f"DTM bounds: {dtm_bounds}")
        print(f"DSM bounds: {dsm_bounds}")
        
        # Check if DTM is fully within DSM
        dtm_within_dsm = (dtm_bounds.left >= dsm_bounds.left and
                         dtm_bounds.right <= dsm_bounds.right and
                         dtm_bounds.bottom >= dsm_bounds.bottom and
                         dtm_bounds.top <= dsm_bounds.top)
        
        print(f"DTM within DSM: {dtm_within_dsm}")
        
        # Calculate the problematic window
        print(f"\n🔧 TESTING CURRENT WINDOWING APPROACH:")
        window = from_bounds(*dtm_bounds, dsm_src.transform)
        print(f"Window: {window}")
        print(f"Window pixel offset: ({window.col_off:.1f}, {window.row_off:.1f})")
        print(f"Window size: {window.width:.1f} × {window.height:.1f}")
        
        # Read data using current approach
        print(f"\n📖 CURRENT APPROACH RESULT:")
        current_data = dsm_src.read(1, window=window)
        current_valid = current_data[~np.isnan(current_data)]
        if len(current_valid) > 0:
            print(f"   Range: {np.min(current_valid):.2f} to {np.max(current_valid):.2f}")
            print(f"   Mean: {np.mean(current_valid):.2f}")
        
        # Read DTM for comparison
        dtm_data = dtm_src.read(1)
        dtm_valid = dtm_data[~np.isnan(dtm_data)]
        print(f"\n📖 DTM REFERENCE:")
        if len(dtm_valid) > 0:
            print(f"   Range: {np.min(dtm_valid):.2f} to {np.max(dtm_valid):.2f}")
            print(f"   Mean: {np.mean(dtm_valid):.2f}")
        
        # Check if current data matches DTM (indicating the bug)
        ranges_match = (abs(np.min(current_valid) - np.min(dtm_valid)) < 0.01 and
                       abs(np.max(current_valid) - np.max(dtm_valid)) < 0.01)
        print(f"\n🔍 DIAGNOSIS:")
        print(f"Current cropped DSM matches DTM: {ranges_match}")
        
        if ranges_match:
            print("❌ BUG CONFIRMED: Windowing is returning DTM-like values!")
            
            # FIXED APPROACH: Use reprojection instead of windowing
            print(f"\n🔧 IMPLEMENTING FIX: Using reprojection approach")
            
            # Create temporary resampled DSM that exactly matches DTM
            with tempfile.NamedTemporaryFile(suffix='_dsm_aligned.tif', delete=False) as tmp_file:
                aligned_dsm_path = tmp_file.name
            
            try:
                # Get DTM properties to use as target
                target_crs = dtm_src.crs
                target_transform = dtm_src.transform
                target_width = dtm_src.width
                target_height = dtm_src.height
                
                # Create output profile for aligned DSM
                dsm_profile = dsm_src.profile.copy()
                dsm_profile.update({
                    'crs': target_crs,
                    'transform': target_transform,
                    'width': target_width,
                    'height': target_height
                })
                
                print(f"🔄 Reprojecting DSM to exactly match DTM grid...")
                
                # Reproject DSM to match DTM exactly
                with rasterio.open(aligned_dsm_path, 'w', **dsm_profile) as dst:
                    reproject(
                        source=rasterio.band(dsm_src, 1),
                        destination=rasterio.band(dst, 1),
                        src_transform=dsm_src.transform,
                        src_crs=dsm_src.crs,
                        dst_transform=target_transform,
                        dst_crs=target_crs,
                        resampling=Resampling.bilinear
                    )
                
                # Read the reprojected DSM
                print(f"\n📖 FIXED APPROACH RESULT:")
                with rasterio.open(aligned_dsm_path) as aligned_src:
                    aligned_data = aligned_src.read(1)
                    aligned_valid = aligned_data[~np.isnan(aligned_data)]
                    if len(aligned_valid) > 0:
                        print(f"   Range: {np.min(aligned_valid):.2f} to {np.max(aligned_valid):.2f}")
                        print(f"   Mean: {np.mean(aligned_valid):.2f}")
                        print(f"   Shape: {aligned_data.shape}")
                    
                    # Test CHM calculation
                    if aligned_data.shape == dtm_data.shape:
                        print(f"\n🧮 TESTING CHM CALCULATION:")
                        chm_data = aligned_data.astype(np.float32) - dtm_data.astype(np.float32)
                        chm_valid = chm_data[~np.isnan(chm_data)]
                        
                        if len(chm_valid) > 0:
                            chm_min, chm_max = np.min(chm_valid), np.max(chm_valid)
                            chm_mean = np.mean(chm_valid)
                            print(f"   CHM Range: {chm_min:.2f} to {chm_max:.2f}")
                            print(f"   CHM Mean: {chm_mean:.2f}")
                            
                            # Check for reasonable CHM values
                            non_zero_count = np.sum(np.abs(chm_valid) > 0.1)
                            zero_count = np.sum(np.abs(chm_valid) <= 0.1)
                            print(f"   Non-zero CHM pixels: {non_zero_count:,}")
                            print(f"   Near-zero CHM pixels: {zero_count:,}")
                            
                            if chm_max > chm_min + 1.0:
                                print("✅ CHM calculation SUCCESS: Valid height variation detected!")
                            else:
                                print("❌ CHM calculation FAILED: Still getting flat results")
                        else:
                            print("❌ No valid CHM data")
                    else:
                        print(f"❌ Shape mismatch: DTM {dtm_data.shape} vs aligned DSM {aligned_data.shape}")
                
                # Clean up
                os.unlink(aligned_dsm_path)
                
            except Exception as e:
                # Clean up on error
                if os.path.exists(aligned_dsm_path):
                    os.unlink(aligned_dsm_path)
                print(f"❌ Reprojection failed: {e}")
        else:
            print("✅ No bug detected: Windowing appears to work correctly")
    
    print(f"\n🎯 ANALYSIS COMPLETE")

if __name__ == "__main__":
    debug_and_fix_chm_windowing()
