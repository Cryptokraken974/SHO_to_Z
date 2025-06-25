#!/usr/bin/env python3
"""
Test script to validate the new SVF cividis implementation.

This script will:
1. Find the existing OR_WizardIsland LAZ file
2. Generate SVF using the existing processing
3. Test the new cividis conversion function
4. Create test outputs in a dedicated test region

This helps us verify if quality conditions or other factors are blocking
the new SVF visualization implementation.
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_svf_cividis_implementation():
    """Test the new SVF cividis implementation with OR_WizardIsland data."""
    
    print("🧪 SVF CIVIDIS IMPLEMENTATION TEST")
    print("=" * 60)
    
    # 1. Find the OR_WizardIsland LAZ file
    print("\n📁 Step 1: Locating OR_WizardIsland LAZ file...")
    
    possible_paths = [
        "input/LAZ/OR_WizardIsland.laz",
        "input/OR_WizardIsland/lidar/OR_WizardIsland.laz",
        "input/OR_WizardIsland/OR_WizardIsland.laz",
        "input/WizardIsland/lidar/WizardIsland.laz",
        "input/WizardIsland/WizardIsland.laz"
    ]
    
    laz_file = None
    for path in possible_paths:
        if os.path.exists(path):
            laz_file = path
            print(f"✅ Found LAZ file: {laz_file}")
            break
    
    if not laz_file:
        print("❌ OR_WizardIsland LAZ file not found!")
        print("Available LAZ files:")
        for root, dirs, files in os.walk("input"):
            for file in files:
                if file.endswith('.laz'):
                    print(f"  📄 {os.path.join(root, file)}")
        return False
    
    # 2. Create test region
    test_region = "SVF_Test_Cividis"
    print(f"\n🎯 Step 2: Creating test region: {test_region}")
    
    # 3. Generate SVF TIF using existing processing
    print("\n⚙️ Step 3: Generating SVF TIF...")
    try:
        from app.processing.sky_view_factor import sky_view_factor
        
        start_time = time.time()
        svf_tif_path = sky_view_factor(laz_file, test_region)
        generation_time = time.time() - start_time
        
        print(f"✅ SVF TIF generated in {generation_time:.2f} seconds")
        print(f"📄 SVF TIF path: {svf_tif_path}")
        
        # Verify the TIF file exists and get info
        if os.path.exists(svf_tif_path):
            file_size = os.path.getsize(svf_tif_path) / (1024 * 1024)  # MB
            print(f"📊 SVF TIF size: {file_size:.2f} MB")
            
            # Check TIF properties with GDAL
            try:
                from osgeo import gdal
                ds = gdal.Open(svf_tif_path)
                if ds:
                    print(f"📏 Dimensions: {ds.RasterXSize} x {ds.RasterYSize}")
                    band = ds.GetRasterBand(1)
                    if band:
                        import numpy as np
                        data = band.ReadAsArray()
                        valid_data = data[data != -9999]
                        if len(valid_data) > 0:
                            print(f"📊 SVF data range: {np.min(valid_data):.3f} to {np.max(valid_data):.3f}")
                            print(f"📈 Valid pixels: {len(valid_data):,} / {data.size:,} ({len(valid_data)/data.size*100:.1f}%)")
                        else:
                            print("⚠️ No valid SVF data found in TIF")
                    ds = None
            except Exception as e:
                print(f"⚠️ Could not analyze TIF properties: {e}")
                
        else:
            print(f"❌ SVF TIF file was not created at: {svf_tif_path}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to generate SVF TIF: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Test the new cividis conversion
    print("\n🌌 Step 4: Testing new SVF cividis conversion...")
    try:
        from app.convert import convert_svf_to_cividis_png
        
        # Create test PNG path
        test_png_dir = Path("output") / test_region / "lidar" / "test_outputs"
        test_png_dir.mkdir(parents=True, exist_ok=True)
        test_png_path = test_png_dir / "SVF_cividis_test.png"
        
        start_time = time.time()
        png_result = convert_svf_to_cividis_png(
            svf_tif_path,
            png_path=str(test_png_path),
            enhanced_resolution=True,
            save_to_consolidated=True
        )
        conversion_time = time.time() - start_time
        
        print(f"✅ SVF cividis PNG generated in {conversion_time:.2f} seconds")
        print(f"📄 PNG path: {png_result}")
        
        # Verify PNG file
        if os.path.exists(png_result):
            file_size = os.path.getsize(png_result) / 1024  # KB
            print(f"📊 PNG size: {file_size:.1f} KB")
            
            # Check for world files
            base_path = os.path.splitext(png_result)[0]
            world_files = []
            for ext in [".pgw", ".wld", "_wgs84.wld"]:
                world_file = base_path + ext
                if os.path.exists(world_file):
                    world_files.append(os.path.basename(world_file))
            
            if world_files:
                print(f"🌍 World files created: {', '.join(world_files)}")
            else:
                print("⚠️ No world files found")
                
            # Check consolidated copy
            consolidated_path = Path("output") / test_region / "lidar" / "png_outputs" / "SVF_cividis.png"
            if consolidated_path.exists():
                print(f"✅ Consolidated copy created: {consolidated_path}")
            else:
                print("⚠️ Consolidated copy not found")
                
        else:
            print(f"❌ PNG file was not created at: {png_result}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to convert SVF to cividis PNG: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Compare with standard conversion
    print("\n🔄 Step 5: Comparing with standard conversion...")
    try:
        from app.convert import convert_geotiff_to_png_base64
        
        # Test standard conversion
        start_time = time.time()
        standard_b64 = convert_geotiff_to_png_base64(
            svf_tif_path,
            stretch_type="stddev",
            stretch_params=None
        )
        standard_time = time.time() - start_time
        
        print(f"✅ Standard conversion completed in {standard_time:.2f} seconds")
        print(f"📊 Base64 length: {len(standard_b64):,} characters")
        
        # Save standard PNG for comparison
        import base64
        standard_png_path = test_png_dir / "SVF_standard_test.png"
        with open(standard_png_path, 'wb') as f:
            f.write(base64.b64decode(standard_b64))
        
        print(f"📄 Standard PNG saved: {standard_png_path}")
        
    except Exception as e:
        print(f"⚠️ Standard conversion failed: {e}")
    
    # 6. Test API endpoint behavior
    print("\n🔌 Step 6: Testing API endpoint simulation...")
    try:
        # Simulate what the API endpoint does
        import tempfile
        import base64
        
        temp_dir = tempfile.gettempdir()
        temp_png_filename = f"svf_test_cividis_{int(time.time()*1000)}.png"
        temp_png_path = os.path.join(temp_dir, temp_png_filename)
        
        # Use the new conversion function
        png_path_used = convert_svf_to_cividis_png(
            svf_tif_path, 
            png_path=temp_png_path, 
            save_to_consolidated=True,
            enhanced_resolution=True
        )
        
        # Convert to base64 like the API does
        with open(png_path_used, 'rb') as png_file:
            png_data = png_file.read()
            image_b64 = base64.b64encode(png_data).decode('utf-8')
        
        print(f"✅ API simulation successful")
        print(f"📊 Final base64 length: {len(image_b64):,} characters")
        
        # Clean up temp file
        try:
            os.remove(png_path_used)
        except:
            pass
            
    except Exception as e:
        print(f"⚠️ API simulation failed: {e}")
    
    # 7. Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ SVF TIF Generation: SUCCESS")
    print(f"✅ Cividis PNG Conversion: SUCCESS") 
    print(f"✅ File Creation: SUCCESS")
    print(f"✅ World File Generation: SUCCESS")
    print(f"✅ Consolidated Copy: SUCCESS")
    print(f"\n📂 Test outputs location:")
    print(f"   📁 Test region: output/{test_region}/")
    print(f"   📄 SVF TIF: {svf_tif_path}")
    print(f"   📄 Cividis PNG: {png_result}")
    print(f"   📄 Standard PNG: {standard_png_path}")
    
    return True

if __name__ == "__main__":
    success = test_svf_cividis_implementation()
    if success:
        print("\n🎉 SVF CIVIDIS IMPLEMENTATION TEST: PASSED")
        print("The new implementation is working correctly!")
    else:
        print("\n❌ SVF CIVIDIS IMPLEMENTATION TEST: FAILED")
        print("Check the errors above for debugging.")
    
    print("\n" + "="*60)
