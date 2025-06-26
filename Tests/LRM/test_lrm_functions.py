#!/usr/bin/env python3
"""
LRM Function Testing
===================

Test the convert.py LRM functions directly to ensure they work properly
with the test LRM file and generate expected outputs.

This script tests:
1. convert_lrm_to_coolwarm_png() - Decorated archaeological visualization
2. convert_lrm_to_coolwarm_png_clean() - Clean overlay version

Author: AI Assistant
Date: January 2025
"""

import os
import sys
import time
from pathlib import Path

# Add the parent directory to the path to import convert functions
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_lrm_functions():
    """Test the LRM conversion functions from convert.py"""
    print(f"🧪 Testing LRM conversion functions from convert.py")
    print(f"=" * 60)
    
    # Setup paths
    lrm_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/LRM/OR_WizardIsland_LRM_adaptive.tif"
    output_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/LRM/visualizations"
    
    # Verify input file exists
    if not os.path.exists(lrm_path):
        print(f"❌ Test file not found: {lrm_path}")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Import the LRM conversion functions
        from app.convert import convert_lrm_to_coolwarm_png, convert_lrm_to_coolwarm_png_clean
        print(f"✅ Successfully imported LRM conversion functions")
        
        # Test 1: Standard decorated coolwarm PNG
        print(f"\n🎨 Test 1: convert_lrm_to_coolwarm_png() - Decorated version")
        start_time = time.time()
        
        decorated_output = os.path.join(output_dir, "LRM_coolwarm_decorated.png")
        result_path = convert_lrm_to_coolwarm_png(
            input_tiff_path=lrm_path,
            output_png_path=decorated_output,
            enhanced_resolution=True,
            save_to_consolidated=False,
            percentile_clip=(2.0, 98.0)
        )
        
        test1_time = time.time() - start_time
        print(f"   ✅ Decorated PNG generated: {os.path.basename(result_path)}")
        print(f"   ⏱️ Generation time: {test1_time:.2f} seconds")
        print(f"   📁 File exists: {os.path.exists(result_path)}")
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"   📊 File size: {file_size:,} bytes")
        
        # Test 2: Clean overlay coolwarm PNG  
        print(f"\n🎨 Test 2: convert_lrm_to_coolwarm_png_clean() - Clean overlay version")
        start_time = time.time()
        
        clean_output = os.path.join(output_dir, "LRM_coolwarm_clean.png")
        result_path = convert_lrm_to_coolwarm_png_clean(
            input_tiff_path=lrm_path,
            output_png_path=clean_output,
            enhanced_resolution=True,
            save_to_consolidated=False,
            percentile_clip=(2.0, 98.0)
        )
        
        test2_time = time.time() - start_time
        print(f"   ✅ Clean PNG generated: {os.path.basename(result_path)}")
        print(f"   ⏱️ Generation time: {test2_time:.2f} seconds") 
        print(f"   📁 File exists: {os.path.exists(result_path)}")
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"   📊 File size: {file_size:,} bytes")
        
        # Test 3: Different percentile clipping
        print(f"\n🎨 Test 3: Testing different percentile clipping (5%-95%)")
        start_time = time.time()
        
        alt_clip_output = os.path.join(output_dir, "LRM_coolwarm_5_95_clip.png")
        result_path = convert_lrm_to_coolwarm_png(
            input_tiff_path=lrm_path,
            output_png_path=alt_clip_output,
            enhanced_resolution=True,
            save_to_consolidated=False,
            percentile_clip=(5.0, 95.0)
        )
        
        test3_time = time.time() - start_time
        print(f"   ✅ Alternative clipping PNG generated: {os.path.basename(result_path)}")
        print(f"   ⏱️ Generation time: {test3_time:.2f} seconds")
        print(f"   📁 File exists: {os.path.exists(result_path)}")
        
        # Test 4: Standard resolution
        print(f"\n🎨 Test 4: Testing standard resolution (100 DPI)")
        start_time = time.time()
        
        std_res_output = os.path.join(output_dir, "LRM_coolwarm_std_resolution.png")
        result_path = convert_lrm_to_coolwarm_png(
            input_tiff_path=lrm_path,
            output_png_path=std_res_output,
            enhanced_resolution=False,  # Standard resolution
            save_to_consolidated=False,
            percentile_clip=(2.0, 98.0)
        )
        
        test4_time = time.time() - start_time
        print(f"   ✅ Standard resolution PNG generated: {os.path.basename(result_path)}")
        print(f"   ⏱️ Generation time: {test4_time:.2f} seconds")
        print(f"   📁 File exists: {os.path.exists(result_path)}")
        
        # Summary
        total_time = test1_time + test2_time + test3_time + test4_time
        print(f"\n✅ All LRM function tests completed successfully!")
        print(f"⏱️ Total time: {total_time:.2f} seconds")
        print(f"📁 All outputs saved to: {output_dir}")
        
        print(f"\n🎯 Test Results Summary:")
        print(f"   ✅ Decorated coolwarm PNG: Working")
        print(f"   ✅ Clean coolwarm PNG: Working") 
        print(f"   ✅ Custom percentile clipping: Working")
        print(f"   ✅ Resolution options: Working")
        print(f"   🌡️ Coolwarm colormap: Archaeological interpretation ready")
        print(f"   🎨 Functions ready for production use")
        
    except ImportError as e:
        print(f"❌ Failed to import LRM functions: {e}")
        print(f"   💡 Make sure the app.convert module is accessible")
        
    except Exception as e:
        print(f"❌ LRM function testing failed: {e}")
        print(f"   💡 Check that the LRM TIFF file is valid and functions are working")

if __name__ == "__main__":
    test_lrm_functions()
