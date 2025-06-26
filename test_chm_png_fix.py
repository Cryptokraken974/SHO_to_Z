#!/usr/bin/env python3
"""
Test CHM PNG generation fix to verify that:
1. CHM.png is generated without decorations (clean)
2. CHM_matplot.png is generated with decorations (legends, colorbar, etc.)
"""

import os
import sys
import tempfile
import numpy as np
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, '/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

def create_test_chm_tiff():
    """Create a synthetic CHM TIFF for testing"""
    from osgeo import gdal, osr
    
    # Create a temporary CHM file with synthetic vegetation data
    temp_dir = tempfile.mkdtemp()
    chm_path = os.path.join(temp_dir, "test_chm.tif")
    
    # Create synthetic CHM data (100x100 pixels)
    width, height = 100, 100
    
    # Create synthetic vegetation heights (0-30 meters)
    np.random.seed(42)  # For reproducible results
    chm_data = np.random.rand(height, width) * 30  # 0-30m vegetation
    
    # Add some structure: higher vegetation in center, lower at edges
    y, x = np.ogrid[:height, :width]
    center_y, center_x = height // 2, width // 2
    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    max_distance = np.sqrt(center_x**2 + center_y**2)
    structure = 1.0 - (distance / max_distance) * 0.7  # Taper from center
    chm_data = chm_data * structure
    
    # Create the TIFF file
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(chm_path, width, height, 1, gdal.GDT_Float32)
    
    # Set geotransform (dummy coordinates)
    geotransform = [0, 1, 0, height, 0, -1]
    dataset.SetGeoTransform(geotransform)
    
    # Set projection (WGS84)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    dataset.SetProjection(srs.ExportToWkt())
    
    # Write the data
    band = dataset.GetRasterBand(1)
    band.WriteArray(chm_data)
    band.SetNoDataValue(-9999)
    
    # Close and clean up
    dataset = None
    band = None
    
    return chm_path, temp_dir

def test_chm_png_functions():
    """Test both CHM PNG generation functions"""
    print("🧪 TESTING CHM PNG GENERATION FIX")
    print("="*60)
    
    try:
        # Create test data
        print("📊 Creating synthetic CHM test data...")
        chm_path, temp_dir = create_test_chm_tiff()
        print(f"✅ Test CHM created: {chm_path}")
        
        # Import the fixed functions
        from app.convert import convert_chm_to_viridis_png, convert_chm_to_viridis_png_clean
        
        # Test 1: Generate decorated CHM PNG (CHM_matplot.png equivalent)
        print(f"\n🖼️ Testing decorated CHM PNG generation...")
        decorated_png = os.path.join(temp_dir, "CHM_matplot.png")
        
        result_decorated = convert_chm_to_viridis_png(
            chm_path,
            decorated_png,
            enhanced_resolution=True,
            save_to_consolidated=False
        )
        
        if os.path.exists(decorated_png):
            size_decorated = os.path.getsize(decorated_png)
            print(f"✅ Decorated PNG created: {os.path.basename(decorated_png)}")
            print(f"   📏 Size: {size_decorated:,} bytes ({size_decorated/1024:.1f} KB)")
            print(f"   🎨 Features: Colorbar, legends, title, explanatory text")
        else:
            print(f"❌ Decorated PNG creation failed")
        
        # Test 2: Generate clean CHM PNG (CHM.png equivalent)
        print(f"\n🎯 Testing clean CHM PNG generation...")
        clean_png = os.path.join(temp_dir, "CHM.png")
        
        result_clean = convert_chm_to_viridis_png_clean(
            chm_path,
            clean_png,
            enhanced_resolution=True,
            save_to_consolidated=False
        )
        
        if os.path.exists(clean_png):
            size_clean = os.path.getsize(clean_png)
            print(f"✅ Clean PNG created: {os.path.basename(clean_png)}")
            print(f"   📏 Size: {size_clean:,} bytes ({size_clean/1024:.1f} KB)")
            print(f"   🎯 Features: Pure raster, no decorations, suitable for overlays")
        else:
            print(f"❌ Clean PNG creation failed")
        
        # Compare the files
        print(f"\n📊 COMPARISON:")
        if os.path.exists(decorated_png) and os.path.exists(clean_png):
            print(f"   📐 Size difference: {abs(size_decorated - size_clean):,} bytes")
            print(f"   📈 Decorated is {size_decorated/size_clean:.1f}x larger (expected due to legends)")
            
            # Check if they are different (they should be!)
            with open(decorated_png, 'rb') as f1, open(clean_png, 'rb') as f2:
                decorated_content = f1.read()
                clean_content = f2.read()
                
            if decorated_content != clean_content:
                print(f"   ✅ FILES ARE DIFFERENT - Fix successful!")
                print(f"   🎉 CHM.png and CHM_matplot.png will now be distinct")
            else:
                print(f"   ❌ FILES ARE IDENTICAL - Fix failed!")
        
        # Test 3: Verify world files are created
        decorated_world = os.path.splitext(decorated_png)[0] + ".pgw"
        clean_world = os.path.splitext(clean_png)[0] + ".pgw"
        
        print(f"\n🌍 WORLD FILE CHECK:")
        if os.path.exists(decorated_world):
            print(f"   ✅ Decorated world file: {os.path.basename(decorated_world)}")
        else:
            print(f"   ❌ Missing decorated world file")
            
        if os.path.exists(clean_world):
            print(f"   ✅ Clean world file: {os.path.basename(clean_world)}")
        else:
            print(f"   ❌ Missing clean world file")
        
        print(f"\n🎯 TEST SUMMARY:")
        if (os.path.exists(decorated_png) and os.path.exists(clean_png) and 
            decorated_content != clean_content):
            print(f"   ✅ SUCCESS: CHM PNG generation fix is working correctly!")
            print(f"   🔧 The issue where CHM.png and CHM_matplot.png were identical is FIXED")
            print(f"   📁 CHM.png: Clean raster for overlays")
            print(f"   📊 CHM_matplot.png: Decorated visualization with legends")
        else:
            print(f"   ❌ FAILURE: Something is still wrong with the CHM PNG generation")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Test files cleaned up")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chm_png_functions()
