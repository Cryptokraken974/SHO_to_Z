#!/usr/bin/env python3
"""
Demonstration script showing the difference between old and enhanced processing
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# Add app directory to Python path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
APP_DIR = os.path.join(BASE_DIR, "app")
sys.path.insert(0, APP_DIR)

# Import both old and enhanced functions
from processing.tiff_processing import (
    process_lrm_tiff, process_enhanced_lrm_tiff,
    process_slope_tiff, process_enhanced_slope_tiff
)

# Test with elevation TIFF file
TEST_TIFF = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/TEST_ELEVATION_DEBUG/lidar/2.313S_56.622W_elevation.tiff"
OUTPUT_DIR = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/enhanced_vs_old_comparison"

async def compare_functions():
    """Compare old vs enhanced processing functions"""
    print("🆚 ENHANCED vs OLD PROCESSING COMPARISON")
    print("=" * 70)
    
    if not os.path.exists(TEST_TIFF):
        print(f"❌ Test TIFF not found: {TEST_TIFF}")
        return False
    
    # Create output directories
    old_dir = os.path.join(OUTPUT_DIR, "old")
    enhanced_dir = os.path.join(OUTPUT_DIR, "enhanced")
    os.makedirs(old_dir, exist_ok=True)
    os.makedirs(enhanced_dir, exist_ok=True)
    
    print(f"📄 Input TIFF: {os.path.basename(TEST_TIFF)}")
    print(f"📂 Output directory: {OUTPUT_DIR}")
    print()
    
    # Test 1: LRM Comparison
    print("🌄 LRM PROCESSING COMPARISON")
    print("-" * 50)
    
    # Old LRM
    print("📊 OLD LRM:")
    old_lrm_result = await process_lrm_tiff(TEST_TIFF, old_dir, {"window_size": 11})
    
    print("\n📊 ENHANCED LRM:")
    enhanced_lrm_params = {
        "window_size": None,  # Auto-sizing
        "filter_type": "gaussian",
        "auto_sizing": True,
        "enhanced_normalization": True
    }
    enhanced_lrm_result = await process_enhanced_lrm_tiff(TEST_TIFF, enhanced_dir, enhanced_lrm_params)
    
    print("\n" + "=" * 70)
    
    # Test 2: Slope Comparison
    print("📐 SLOPE PROCESSING COMPARISON")
    print("-" * 50)
    
    # Old Slope
    print("📊 OLD SLOPE:")
    old_slope_result = await process_slope_tiff(TEST_TIFF, old_dir, {})
    
    print("\n📊 ENHANCED SLOPE:")
    enhanced_slope_params = {
        "use_inferno_colormap": True,
        "max_slope_degrees": 60.0,
        "enhanced_contrast": True
    }
    enhanced_slope_result = await process_enhanced_slope_tiff(TEST_TIFF, enhanced_dir, enhanced_slope_params)
    
    print("\n" + "=" * 70)
    
    # Summary
    print("📋 COMPARISON SUMMARY")
    print("-" * 50)
    
    print("🌄 LRM Comparison:")
    if old_lrm_result.get("status") == "success" and enhanced_lrm_result.get("status") == "success":
        old_time = old_lrm_result.get("processing_time", 0)
        enhanced_time = enhanced_lrm_result.get("processing_time", 0)
        print(f"   ⏱️ Old LRM time: {old_time:.2f}s")
        print(f"   ⏱️ Enhanced LRM time: {enhanced_time:.2f}s")
        
        enhanced_features = enhanced_lrm_result.get("enhanced_features", {})
        print(f"   ✨ Enhanced features: {list(enhanced_features.keys())}")
    
    print("\n📐 Slope Comparison:")
    if old_slope_result.get("status") == "success" and enhanced_slope_result.get("status") == "success":
        old_time = old_slope_result.get("processing_time", 0)
        enhanced_time = enhanced_slope_result.get("processing_time", 0)
        print(f"   ⏱️ Old Slope time: {old_time:.2f}s")
        print(f"   ⏱️ Enhanced Slope time: {enhanced_time:.2f}s")
        
        enhanced_features = enhanced_slope_result.get("enhanced_features", {})
        print(f"   ✨ Enhanced features: {list(enhanced_features.keys())}")
    
    print("\n🎯 KEY IMPROVEMENTS:")
    print("   📊 Detailed logging with archaeological context")
    print("   🎨 Enhanced visualization options")
    print("   📐 Adaptive parameters based on data characteristics")
    print("   🏛️ Archaeological feature highlighting")
    print("   🔍 Processing statistics and insights")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(compare_functions())
    if success:
        print("\n🎉 Comparison completed successfully!")
        print("✨ Enhanced functions provide significantly more information!")
    else:
        print("\n💥 Comparison failed!")
    sys.exit(0 if success else 1)
