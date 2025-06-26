#!/usr/bin/env python3
"""
Test Hillshade RGB Convert Functions
====================================

This script tests convert.py functions for hillshade RGB visualization,
similar to test_lrm_functions.py for LRM analysis.

Unlike single-band rasters, RGB hillshades require special handling for:
- Multi-band PNG generation
- RGB-specific stretch parameters  
- Channel-aware processing
- Composite visualization

Test File: hillshade_rgb.tif (3-band RGB composite)
Goal: Test all available convert.py functions for RGB hillshade processing

Author: AI Assistant
Date: January 2025
"""

import os
import sys
import time
from pathlib import Path

# Add the parent directory to the path to import convert functions
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from app.convert import (
        convert_geotiff_to_png,
        convert_geotiff_to_png_base64
    )
    print("✅ Successfully imported convert functions")
except ImportError as e:
    print(f"❌ Failed to import convert functions: {e}")
    print("   Make sure you're running from the project root")
    sys.exit(1)

def test_basic_rgb_conversion():
    """Test basic RGB TIFF to PNG conversion."""
    print(f"\n🎨 TEST 01: Basic RGB TIFF to PNG Conversion")
    print(f"{'='*60}")
    
    rgb_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb.tif"
    output_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/visualizations/01_basic_rgb_conversion.png"
    
    try:
        start_time = time.time()
        result_png = convert_geotiff_to_png(
            tif_path=rgb_path,
            png_path=output_path,
            enhanced_resolution=True
        )
        processing_time = time.time() - start_time
        
        if os.path.exists(result_png):
            file_size = os.path.getsize(result_png)
            print(f"✅ SUCCESS: Basic RGB conversion completed")
            print(f"   📁 Output: {os.path.basename(result_png)}")
            print(f"   📊 Size: {file_size:,} bytes")
            print(f"   ⏱️ Time: {processing_time:.2f} seconds")
            return True
        else:
            print(f"❌ FAILURE: Output file not created")
            return False
            
    except Exception as e:
        print(f"❌ FAILURE: Basic RGB conversion failed: {e}")
        return False

def test_rgb_stddev_stretch():
    """Test RGB with standard deviation stretch."""
    print(f"\n📊 TEST 02: RGB with Standard Deviation Stretch")
    print(f"{'='*60}")
    
    rgb_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb.tif"
    output_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/visualizations/02_rgb_stddev_stretch.png"
    
    try:
        start_time = time.time()
        result_png = convert_geotiff_to_png(
            tif_path=rgb_path,
            png_path=output_path,
            enhanced_resolution=True,
            stretch_type="stddev",
            stretch_params={"num_stddev": 2.0}
        )
        processing_time = time.time() - start_time
        
        if os.path.exists(result_png):
            file_size = os.path.getsize(result_png)
            print(f"✅ SUCCESS: RGB stddev stretch completed")
            print(f"   📁 Output: {os.path.basename(result_png)}")
            print(f"   📊 Parameters: 2.0 standard deviations")
            print(f"   📊 Size: {file_size:,} bytes")
            print(f"   ⏱️ Time: {processing_time:.2f} seconds")
            return True
        else:
            print(f"❌ FAILURE: Output file not created")
            return False
            
    except Exception as e:
        print(f"❌ FAILURE: RGB stddev stretch failed: {e}")
        return False

def test_rgb_percentile_stretch():
    """Test RGB with percentile clipping stretch."""
    print(f"\n📈 TEST 03: RGB with Percentile Clipping Stretch")
    print(f"{'='*60}")
    
    rgb_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb.tif"
    output_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/visualizations/03_rgb_percentile_stretch.png"
    
    try:
        start_time = time.time()
        result_png = convert_geotiff_to_png(
            tif_path=rgb_path,
            png_path=output_path,
            enhanced_resolution=True,
            stretch_type="percentclip",
            stretch_params={"low_cut": 2.0, "high_cut": 2.0}
        )
        processing_time = time.time() - start_time
        
        if os.path.exists(result_png):
            file_size = os.path.getsize(result_png)
            print(f"✅ SUCCESS: RGB percentile stretch completed")
            print(f"   📁 Output: {os.path.basename(result_png)}")
            print(f"   📊 Parameters: 2%-98% percentile clip")
            print(f"   📊 Size: {file_size:,} bytes")
            print(f"   ⏱️ Time: {processing_time:.2f} seconds")
            return True
        else:
            print(f"❌ FAILURE: Output file not created")
            return False
            
    except Exception as e:
        print(f"❌ FAILURE: RGB percentile stretch failed: {e}")
        return False

def test_rgb_minmax_stretch():
    """Test RGB with min-max stretch."""
    print(f"\n🔄 TEST 04: RGB with Min-Max Stretch")
    print(f"{'='*60}")
    
    rgb_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb.tif"
    output_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/visualizations/04_rgb_minmax_stretch.png"
    
    try:
        start_time = time.time()
        result_png = convert_geotiff_to_png(
            tif_path=rgb_path,
            png_path=output_path,
            enhanced_resolution=True,
            stretch_type="minmax",
            stretch_params=None
        )
        processing_time = time.time() - start_time
        
        if os.path.exists(result_png):
            file_size = os.path.getsize(result_png)
            print(f"✅ SUCCESS: RGB min-max stretch completed")
            print(f"   📁 Output: {os.path.basename(result_png)}")
            print(f"   📊 Parameters: Full range stretch")
            print(f"   📊 Size: {file_size:,} bytes")
            print(f"   ⏱️ Time: {processing_time:.2f} seconds")
            return True
        else:
            print(f"❌ FAILURE: Output file not created")
            return False
            
    except Exception as e:
        print(f"❌ FAILURE: RGB min-max stretch failed: {e}")
        return False

def test_rgb_high_resolution():
    """Test RGB with maximum resolution settings."""
    print(f"\n🔍 TEST 05: RGB High-Resolution Export")
    print(f"{'='*60}")
    
    rgb_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb.tif"
    output_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/visualizations/05_rgb_high_resolution.png"
    
    try:
        start_time = time.time()
        result_png = convert_geotiff_to_png(
            tif_path=rgb_path,
            png_path=output_path,
            enhanced_resolution=True,
            high_quality=True,
            stretch_type="stddev",
            stretch_params={"num_stddev": 1.5}
        )
        processing_time = time.time() - start_time
        
        if os.path.exists(result_png):
            file_size = os.path.getsize(result_png)
            print(f"✅ SUCCESS: RGB high-resolution export completed")
            print(f"   📁 Output: {os.path.basename(result_png)}")
            print(f"   📊 Parameters: Enhanced resolution + high quality")
            print(f"   📊 Size: {file_size:,} bytes")
            print(f"   ⏱️ Time: {processing_time:.2f} seconds")
            return True
        else:
            print(f"❌ FAILURE: Output file not created")
            return False
            
    except Exception as e:
        print(f"❌ FAILURE: RGB high-resolution export failed: {e}")
        return False

def test_rgb_base64_conversion():
    """Test RGB to base64 conversion (for web display)."""
    print(f"\n🌐 TEST 06: RGB Base64 Conversion (Web Display)")
    print(f"{'='*60}")
    
    rgb_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb.tif"
    
    try:
        start_time = time.time()
        base64_result = convert_geotiff_to_png_base64(
            tif_path=rgb_path,
            stretch_type="stddev",
            stretch_params={"num_stddev": 2.0}
        )
        processing_time = time.time() - start_time
        
        if base64_result and len(base64_result) > 100:
            base64_size = len(base64_result)
            print(f"✅ SUCCESS: RGB base64 conversion completed")
            print(f"   📊 Base64 length: {base64_size:,} characters")
            print(f"   📊 Estimated size: {base64_size * 3 // 4:,} bytes")
            print(f"   ⏱️ Time: {processing_time:.2f} seconds")
            print(f"   🌐 Ready for web display")
            
            # Save a sample to verify (first 100 chars)
            sample_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/visualizations/06_rgb_base64_sample.txt"
            with open(sample_path, 'w') as f:
                f.write(f"RGB Hillshade Base64 Sample ({base64_size:,} total chars):\n")
                f.write(f"{base64_result[:100]}...\n")
                f.write(f"\nProcessing time: {processing_time:.2f} seconds\n")
            print(f"   📄 Sample saved: {os.path.basename(sample_path)}")
            
            return True
        else:
            print(f"❌ FAILURE: Base64 conversion failed or returned empty result")
            return False
            
    except Exception as e:
        print(f"❌ FAILURE: RGB base64 conversion failed: {e}")
        return False

def test_rgb_different_stretch_parameters():
    """Test RGB with different stretch parameter combinations."""
    print(f"\n🔧 TEST 07: RGB with Different Stretch Parameters")
    print(f"{'='*60}")
    
    rgb_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb.tif"
    
    test_cases = [
        {
            'name': 'Conservative Stretch',
            'stretch_type': 'stddev',
            'stretch_params': {'num_stddev': 1.0},
            'suffix': '07a_conservative'
        },
        {
            'name': 'Aggressive Stretch',
            'stretch_type': 'stddev', 
            'stretch_params': {'num_stddev': 3.0},
            'suffix': '07b_aggressive'
        },
        {
            'name': 'Tight Percentile',
            'stretch_type': 'percentclip',
            'stretch_params': {'low_cut': 1.0, 'high_cut': 1.0},
            'suffix': '07c_tight_percentile'
        },
        {
            'name': 'Wide Percentile',
            'stretch_type': 'percentclip',
            'stretch_params': {'low_cut': 5.0, 'high_cut': 5.0},
            'suffix': '07d_wide_percentile'
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases):
        print(f"\n   🧪 Subtest {i+1}: {test_case['name']}")
        output_path = f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/visualizations/{test_case['suffix']}.png"
        
        try:
            start_time = time.time()
            result_png = convert_geotiff_to_png(
                tif_path=rgb_path,
                png_path=output_path,
                enhanced_resolution=True,
                stretch_type=test_case['stretch_type'],
                stretch_params=test_case['stretch_params']
            )
            processing_time = time.time() - start_time
            
            if os.path.exists(result_png):
                file_size = os.path.getsize(result_png)
                print(f"      ✅ {test_case['name']}: {file_size:,} bytes, {processing_time:.2f}s")
                success_count += 1
            else:
                print(f"      ❌ {test_case['name']}: Output file not created")
                
        except Exception as e:
            print(f"      ❌ {test_case['name']}: Failed - {e}")
    
    print(f"\n📊 Stretch Parameters Test Summary: {success_count}/{len(test_cases)} successful")
    return success_count == len(test_cases)

def analyze_rgb_convert_capabilities():
    """Analyze the convert.py capabilities for RGB hillshade processing."""
    print(f"\n🔍 RGB Convert Capabilities Analysis")
    print(f"{'='*60}")
    
    rgb_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb.tif"
    
    # Check file accessibility
    if not os.path.exists(rgb_path):
        print(f"❌ Test file not found: {rgb_path}")
        return False
    
    file_size = os.path.getsize(rgb_path)
    print(f"📂 Test File: {os.path.basename(rgb_path)} ({file_size:,} bytes)")
    
    # Analyze available functions
    print(f"\n🔧 Available Convert Functions:")
    functions_available = []
    
    try:
        from app.convert import convert_geotiff_to_png
        functions_available.append("convert_geotiff_to_png")
        print(f"   ✅ convert_geotiff_to_png - General TIFF to PNG")
    except:
        print(f"   ❌ convert_geotiff_to_png - Not available")
    
    try:
        from app.convert import convert_geotiff_to_png_base64
        functions_available.append("convert_geotiff_to_png_base64")
        print(f"   ✅ convert_geotiff_to_png_base64 - Web display format")
    except:
        print(f"   ❌ convert_geotiff_to_png_base64 - Not available")
    
    # Note: RGB hillshades don't have specific conversion functions like CHM or Slope
    print(f"\n📝 RGB Hillshade Specifics:")
    print(f"   🎨 3-band RGB composite requires general conversion functions")
    print(f"   🔄 Unlike single-band rasters (CHM, Slope), no specialized RGB functions")
    print(f"   📊 Stretch parameters apply to all bands simultaneously")
    print(f"   🌈 Natural color representation preserves multi-directional illumination")
    
    print(f"\n💡 Recommended Approach:")
    print(f"   🎯 Use convert_geotiff_to_png with stddev stretch (2.0 std)")
    print(f"   🔍 Enable enhanced_resolution for high-quality output")
    print(f"   📊 Apply conservative stretch to preserve RGB balance")
    print(f"   🌐 Use convert_geotiff_to_png_base64 for web applications")
    
    return len(functions_available) >= 2

def main():
    """Main function to run all RGB hillshade convert function tests."""
    print(f"🧪 HILLSHADE RGB CONVERT FUNCTIONS TEST SUITE")
    print(f"=" * 70)
    print(f"📂 Test File: hillshade_rgb.tif (3-band RGB composite)")
    print(f"🎯 Goal: Test convert.py functions for RGB hillshade visualization")
    print(f"📁 Output Directory: Tests/HillshadeRgb/visualizations/")
    
    # Ensure output directory exists
    output_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/visualizations"
    os.makedirs(output_dir, exist_ok=True)
    
    # Track test results
    tests = [
        ("RGB Convert Capabilities Analysis", analyze_rgb_convert_capabilities),
        ("Basic RGB Conversion", test_basic_rgb_conversion),
        ("RGB StdDev Stretch", test_rgb_stddev_stretch),
        ("RGB Percentile Stretch", test_rgb_percentile_stretch),
        ("RGB Min-Max Stretch", test_rgb_minmax_stretch),
        ("RGB High-Resolution Export", test_rgb_high_resolution),
        ("RGB Base64 Conversion", test_rgb_base64_conversion),
        ("RGB Different Stretch Parameters", test_rgb_different_stretch_parameters)
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ TEST FAILURE: {test_name} crashed with error: {e}")
            results.append((test_name, False))
    
    total_time = time.time() - start_time
    
    # Print summary
    print(f"\n" + "="*70)
    print(f"📊 HILLSHADE RGB CONVERT FUNCTIONS TEST SUMMARY")
    print(f"="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"   ✅ Passed: {passed}/{total} tests")
    print(f"   ⏱️ Total time: {total_time:.2f} seconds")
    print(f"   📁 Output location: {output_dir}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! RGB hillshade convert functions working correctly.")
        print(f"🔍 Check the visualizations/ directory for PNG outputs")
        print(f"🌈 RGB composite visualization pipeline fully functional")
    else:
        print(f"\n⚠️ {total - passed} TEST(S) FAILED. Check error messages above.")
        print(f"🔧 Some convert.py functions may need attention for RGB processing")
    
    print(f"\n📋 NEXT STEPS:")
    print(f"   🎨 Review generated PNGs for visual quality")
    print(f"   📊 Compare different stretch methods for optimal results")
    print(f"   🌐 Test base64 output in web applications")
    print(f"   🏛️ Apply findings to archaeological hillshade analysis")

if __name__ == "__main__":
    main()
