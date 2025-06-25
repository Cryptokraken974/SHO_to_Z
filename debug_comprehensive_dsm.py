#!/usr/bin/env python3
"""
Comprehensive DSM data analysis to understand why CHM is zero

This script will analyze different parts of the DSM to see if it contains
proper surface elevation data or if it's somehow terrain-like everywhere.
"""

import rasterio
import numpy as np
from rasterio.windows import Window
import matplotlib.pyplot as plt
import os

def comprehensive_dsm_analysis():
    """Analyze DSM data comprehensively"""
    
    print("🔍 COMPREHENSIVE DSM ANALYSIS - Box_Regions_7")
    print("=" * 70)
    
    # File paths
    dtm_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/Box_Regions_7/3.787S_63.673W_elevation/Original/3.787S_63.673W_elevation.tiff"
    dsm_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/Box_Regions_7/lidar/DSM/Box_Regions_7_copernicus_dsm_30m.tif"
    
    print(f"📁 DTM: {os.path.basename(dtm_path)}")
    print(f"📁 DSM: {os.path.basename(dsm_path)}")
    
    with rasterio.open(dtm_path) as dtm_src, rasterio.open(dsm_path) as dsm_src:
        
        # Read full DTM for reference
        dtm_data = dtm_src.read(1)
        dtm_valid = dtm_data[~np.isnan(dtm_data)]
        
        print(f"\n📖 DTM REFERENCE DATA:")
        print(f"   Shape: {dtm_data.shape}")
        print(f"   Range: {np.min(dtm_valid):.2f} to {np.max(dtm_valid):.2f}")
        print(f"   Mean: {np.mean(dtm_valid):.2f}")
        print(f"   Std: {np.std(dtm_valid):.2f}")
        
        # Read full DSM
        print(f"\n📖 FULL DSM DATA:")
        dsm_data = dsm_src.read(1)
        dsm_valid = dsm_data[~np.isnan(dsm_data)]
        
        print(f"   Shape: {dsm_data.shape}")
        print(f"   Range: {np.min(dsm_valid):.2f} to {np.max(dsm_valid):.2f}")
        print(f"   Mean: {np.mean(dsm_valid):.2f}")
        print(f"   Std: {np.std(dsm_valid):.2f}")
        
        # Sample different parts of the DSM
        height, width = dsm_data.shape
        
        # Define sample windows
        sample_regions = [
            ("Top-Left", Window(0, 0, 500, 500)),
            ("Top-Right", Window(width-500, 0, 500, 500)),
            ("Center", Window(width//2-250, height//2-250, 500, 500)),
            ("Bottom-Left", Window(0, height-500, 500, 500)),
            ("Bottom-Right", Window(width-500, height-500, 500, 500)),
            ("DTM Overlap Area", Window(int(770), int(2429), 810, 810))  # The problematic area
        ]
        
        print(f"\n📍 REGIONAL DSM ANALYSIS:")
        for region_name, window in sample_regions:
            try:
                sample_data = dsm_src.read(1, window=window)
                sample_valid = sample_data[~np.isnan(sample_data)]
                
                if len(sample_valid) > 0:
                    sample_min = np.min(sample_valid)
                    sample_max = np.max(sample_valid)
                    sample_mean = np.mean(sample_valid)
                    sample_std = np.std(sample_valid)
                    
                    print(f"   {region_name}:")
                    print(f"      Range: {sample_min:.2f} to {sample_max:.2f}")
                    print(f"      Mean: {sample_mean:.2f}, Std: {sample_std:.2f}")
                    
                    # Check if this region has the same values as DTM
                    dtm_like = (abs(sample_min - np.min(dtm_valid)) < 0.1 and 
                               abs(sample_max - np.max(dtm_valid)) < 0.1)
                    print(f"      DTM-like values: {dtm_like}")
                    
                else:
                    print(f"   {region_name}: No valid data")
                    
            except Exception as e:
                print(f"   {region_name}: Error - {e}")
        
        # Check DSM metadata
        print(f"\n📊 DSM METADATA:")
        print(f"   CRS: {dsm_src.crs}")
        print(f"   NoData: {dsm_src.nodata}")
        print(f"   Data Type: {dsm_src.dtypes[0]}")
        print(f"   Bounds: {dsm_src.bounds}")
        print(f"   Transform: {dsm_src.transform}")
        
        # Statistical analysis of the overlap region specifically
        print(f"\n🎯 DETAILED OVERLAP ANALYSIS:")
        
        # Get the exact DTM bounds
        dtm_bounds = dtm_src.bounds
        
        # Calculate window more carefully
        from rasterio.windows import from_bounds
        overlap_window = from_bounds(*dtm_bounds, dsm_src.transform)
        
        # Round to ensure integer window
        overlap_window = Window(
            int(round(overlap_window.col_off)),
            int(round(overlap_window.row_off)),
            int(round(overlap_window.width)),
            int(round(overlap_window.height))
        )
        
        print(f"   Refined window: {overlap_window}")
        
        # Read overlap data
        overlap_data = dsm_src.read(1, window=overlap_window)
        overlap_valid = overlap_data[~np.isnan(overlap_data)]
        
        if len(overlap_valid) > 0:
            print(f"   Overlap shape: {overlap_data.shape}")
            print(f"   Overlap range: {np.min(overlap_valid):.2f} to {np.max(overlap_valid):.2f}")
            print(f"   Overlap mean: {np.mean(overlap_valid):.2f}")
            
            # Create histograms to understand data distribution
            print(f"\n📊 VALUE DISTRIBUTION ANALYSIS:")
            
            # Count unique values in overlap region
            unique_overlap = np.unique(overlap_valid.round(2))
            unique_dtm = np.unique(dtm_valid.round(2))
            
            print(f"   Unique values in overlap DSM: {len(unique_overlap)}")
            print(f"   Unique values in DTM: {len(unique_dtm)}")
            
            # Check if overlap DSM has exactly the same unique values as DTM
            overlap_set = set(unique_overlap)
            dtm_set = set(unique_dtm)
            
            intersection = len(overlap_set & dtm_set)
            overlap_only = len(overlap_set - dtm_set)
            dtm_only = len(dtm_set - overlap_set)
            
            print(f"   Common values: {intersection}")
            print(f"   Overlap-only values: {overlap_only}")
            print(f"   DTM-only values: {dtm_only}")
            
            if overlap_only == 0 and dtm_only == 0:
                print("❌ PROBLEM IDENTIFIED: Overlap DSM has IDENTICAL values to DTM!")
                print("   This suggests DSM is providing terrain rather than surface elevation")
            elif abs(len(overlap_set) - len(dtm_set)) < 10:
                print("⚠️ POTENTIAL ISSUE: Very similar value sets")
            else:
                print("✅ Value sets are different - this is expected")
        
        # Final check: Let's look at some specific coordinates
        print(f"\n🔬 PIXEL-LEVEL COMPARISON:")
        
        # Sample a few specific coordinates
        test_coords = [
            (100, 100),  # Top area of overlap
            (400, 400),  # Center of overlap
            (700, 700)   # Bottom area of overlap
        ]
        
        for i, (x, y) in enumerate(test_coords):
            if x < overlap_data.shape[1] and y < overlap_data.shape[0]:
                dsm_val = overlap_data[y, x]
                dtm_val = dtm_data[y, x] if y < dtm_data.shape[0] and x < dtm_data.shape[1] else np.nan
                
                print(f"   Coord ({x},{y}): DSM={dsm_val:.2f}, DTM={dtm_val:.2f}, Diff={dsm_val-dtm_val:.2f}")

    print(f"\n🎯 ANALYSIS COMPLETE")

if __name__ == "__main__":
    comprehensive_dsm_analysis()
