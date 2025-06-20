#!/usr/bin/env python3
"""
Test script to verify that the duplicate PNG generation fix works correctly.
"""

import os
import tempfile
import shutil
from pathlib import Path

# Add the app directory to the path so we can import the convert function
import sys
sys.path.insert(0, 'app')

from convert import convert_geotiff_to_png

def test_no_duplicate_png_generation():
    """Test that PNG files are not duplicated when already in png_outputs directory"""
    
    print("🧪 Testing PNG duplicate prevention...")
    
    # Create a temporary test structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test region structure
        region_name = "test_region"
        png_outputs_dir = os.path.join(temp_dir, "output", region_name, "lidar", "png_outputs")
        os.makedirs(png_outputs_dir, exist_ok=True)
        
        # Create a simple test TIFF (copy one from existing data)
        test_tiff_source = "output/PRGL1260C9597_2014/lidar/LRM/PRGL1260C9597_2014_DTM_1.0m_csf1.0m_filled_LRM.tif"
        
        if os.path.exists(test_tiff_source):
            test_tiff_path = os.path.join(png_outputs_dir, "test_LRM.tif")
            shutil.copy2(test_tiff_source, test_tiff_path)
            
            # Test 1: PNG generated directly in png_outputs should not be duplicated
            direct_png_path = os.path.join(png_outputs_dir, "LRM.png")
            
            print(f"📁 Test TIF: {test_tiff_path}")
            print(f"📁 Target PNG: {direct_png_path}")
            
            # Count files before conversion
            files_before = len(os.listdir(png_outputs_dir))
            
            # Convert with save_to_consolidated=True (default)
            try:
                result_png = convert_geotiff_to_png(test_tiff_path, direct_png_path, save_to_consolidated=True)
                
                # Count files after conversion
                files_after = len(os.listdir(png_outputs_dir))
                
                print(f"📊 Files before: {files_before}")
                print(f"📊 Files after: {files_after}")
                print(f"📊 Result PNG: {result_png}")
                
                # Check that no additional files were created (should be +1 for the PNG only)
                expected_files = files_before + 1  # +1 for the PNG
                if files_after == expected_files:
                    print("✅ SUCCESS: No duplicate PNG files created!")
                    
                    # List final files for verification
                    final_files = os.listdir(png_outputs_dir)
                    print(f"📋 Final files: {final_files}")
                    
                    # Check for any files with the original TIFF name
                    duplicate_pattern = "test_LRM.png"
                    if duplicate_pattern in final_files:
                        print(f"❌ FAILURE: Found duplicate file: {duplicate_pattern}")
                        return False
                    else:
                        print(f"✅ No duplicate found with pattern: {duplicate_pattern}")
                        return True
                else:
                    print(f"❌ FAILURE: Expected {expected_files} files, got {files_after}")
                    print(f"📋 Files: {os.listdir(png_outputs_dir)}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error during conversion: {e}")
                return False
        else:
            print(f"⚠️ Test source file not found: {test_tiff_source}")
            print("🔍 Available LRM files:")
            lrm_files = []
            for root, dirs, files in os.walk("output"):
                for file in files:
                    if "LRM" in file and file.endswith(".tif"):
                        lrm_files.append(os.path.join(root, file))
            
            for lrm_file in lrm_files[:5]:  # Show first 5
                print(f"   {lrm_file}")
            
            if lrm_files:
                # Use the first available LRM file
                test_tiff_source = lrm_files[0]
                print(f"🔄 Using alternative source: {test_tiff_source}")
                # Recursively call the test with the found file
                return test_with_file(temp_dir, region_name, png_outputs_dir, test_tiff_source)
            else:
                print("❌ No LRM TIFF files found for testing")
                return False

def test_with_file(temp_dir, region_name, png_outputs_dir, test_tiff_source):
    """Helper function to test with a specific file"""
    test_tiff_path = os.path.join(png_outputs_dir, "test_LRM.tif")
    shutil.copy2(test_tiff_source, test_tiff_path)
    
    direct_png_path = os.path.join(png_outputs_dir, "LRM.png")
    
    files_before = len(os.listdir(png_outputs_dir))
    
    try:
        result_png = convert_geotiff_to_png(test_tiff_path, direct_png_path, save_to_consolidated=True)
        files_after = len(os.listdir(png_outputs_dir))
        
        print(f"📊 Files before: {files_before}")
        print(f"📊 Files after: {files_after}")
        
        expected_files = files_before + 1
        if files_after == expected_files:
            print("✅ SUCCESS: No duplicate PNG files created!")
            return True
        else:
            print(f"❌ FAILURE: Expected {expected_files} files, got {files_after}")
            return False
            
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        return False

if __name__ == "__main__":
    success = test_no_duplicate_png_generation()
    if success:
        print("\n🎉 All tests passed! Duplicate PNG generation has been fixed.")
    else:
        print("\n❌ Tests failed. There may still be issues with duplicate generation.")
