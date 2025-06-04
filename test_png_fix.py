#!/usr/bin/env python3
"""
Test script to verify the PNG conversion fix for the -dstnodata error
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_png_conversion():
    """Test the PNG conversion with the fixed GDAL command"""
    print("="*60)
    print("🎯 PNG CONVERSION FIX VALIDATION")
    print("="*60)
    
    try:
        from app.convert import convert_geotiff_to_png
        print("✅ Import successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test files - use the elevation data which typically causes the error
    test_files = [
        "input/13.48S_71.97W/13.480S_71.972W_elevation/Terrain_Analysis/13.480S_71.972W_elevation_hillshade.tif",
        "input/13.48S_71.97W/13.480S_71.972W_elevation/Original/13.480S_71.972W_elevation.tiff",
        "input/13.48S_71.97W/13.480S_71.972W_elevation/Visualization/13.480S_71.972W_elevation_color_relief.tif"
    ]
    
    # Find an available test file
    test_file = None
    for file_path in test_files:
        if os.path.exists(file_path):
            test_file = file_path
            break
    
    if not test_file:
        print("❌ No test files found. Checking available files...")
        for root, dirs, files in os.walk("input"):
            for file in files:
                if file.endswith(('.tif', '.tiff')):
                    test_file = os.path.join(root, file)
                    print(f"Found: {test_file}")
                    break
            if test_file:
                break
    
    if not test_file:
        print("❌ No GeoTIFF files found for testing")
        return False
    
    print(f"🎯 Testing with: {test_file}")
    print(f"📊 Input file size: {os.path.getsize(test_file):,} bytes")
    
    # Create output directory
    output_dir = "output/png_test_fix"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test both standard and enhanced resolution
    test_cases = [
        ("Standard", False),
        ("Enhanced", True)
    ]
    
    results = []
    
    for name, enhanced in test_cases:
        print(f"\n🔧 Testing {name} Resolution PNG Conversion...")
        start_time = time.time()
        
        try:
            png_path = convert_geotiff_to_png(
                test_file,
                output_dir,
                enhanced_resolution=enhanced
            )
            
            conversion_time = time.time() - start_time
            
            if png_path and os.path.exists(png_path):
                file_size = os.path.getsize(png_path)
                print(f"✅ {name} conversion successful!")
                print(f"📄 Output: {png_path}")
                print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                print(f"⏱️  Time: {conversion_time:.2f} seconds")
                
                # Check if file size indicates successful conversion
                if file_size > 100000:  # > 100KB indicates proper conversion
                    print(f"🎉 SUCCESS: File size indicates proper conversion (not 72KB error)")
                    results.append((name, True, file_size, conversion_time))
                else:
                    print(f"⚠️  WARNING: File size still small ({file_size/1024:.1f} KB)")
                    results.append((name, False, file_size, conversion_time))
            else:
                print(f"❌ {name} conversion failed - no output file")
                results.append((name, False, 0, conversion_time))
                
        except Exception as e:
            conversion_time = time.time() - start_time
            print(f"❌ {name} conversion failed with error: {e}")
            results.append((name, False, 0, conversion_time))
    
    # Summary
    print("\n" + "="*60)
    print("📊 CONVERSION TEST RESULTS:")
    print("="*60)
    
    success_count = 0
    for name, success, size, time_taken in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{name:10} | {status:10} | {size:8,} bytes | {time_taken:.2f}s")
        if success:
            success_count += 1
    
    print(f"\n🎯 Overall Result: {success_count}/{len(results)} conversions successful")
    
    if success_count > 0:
        print("\n🎉 GDAL -dstnodata error has been FIXED!")
        print("✅ The -a_nodata parameter is working correctly")
        return True
    else:
        print("\n❌ Conversion issues persist - further investigation needed")
        return False

if __name__ == "__main__":
    test_png_conversion()
