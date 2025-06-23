#!/usr/bin/env python3
"""
Comprehensive test to verify the NDVI bug fix.
This test simulates the complete workflow that was causing the issue.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_coordinate_region_ndvi_bug_fix():
    """Test the complete workflow that was causing NDVI to be created when disabled"""
    
    print("🧪 Testing coordinate-based region creation with NDVI disabled...")
    
    try:
        # Simulate creating a coordinate-based region with NDVI disabled
        test_region = "5_99N_36_15W_test"
        
        # 1. Create region metadata with NDVI disabled (simulating coordinate-based region creation)
        output_dir = Path("output") / test_region
        output_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = output_dir / "metadata.txt"
        metadata_content = f"""# Region Metadata
# Generated: 2025-06-23 14:30:00
# Source: coordinate-based

Region Name: {test_region}
Source: coordinate-based
NDVI Enabled: false
Center Latitude: 5.99
Center Longitude: -36.15
"""
        
        with open(metadata_file, 'w') as f:
            f.write(metadata_content)
        
        print(f"✅ Created region with NDVI disabled: {test_region}")
        
        # 2. Check NDVI status
        from app.endpoints.region_management import isRegionNDVI
        ndvi_status = isRegionNDVI(test_region)
        print(f"📊 NDVI status: {'enabled' if ndvi_status else 'disabled'}")
        
        if ndvi_status:
            print("❌ ERROR: NDVI should be disabled for this test")
            return False
        
        # 3. Simulate Sentinel-2 data being available (this could happen through various pathways)
        input_dir = Path("input") / test_region
        sentinel2_dir = input_dir / "sentinel2"
        sentinel2_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy test Sentinel-2 data
        source_tif = Path("input/test_ndvi/sentinel2/test_ndvi_20250529_sentinel2.tif")
        if source_tif.exists():
            target_tif = sentinel2_dir / f"{test_region}_20250529_sentinel2.tif"
            shutil.copy(source_tif, target_tif)
            print(f"✅ Simulated Sentinel-2 data: {target_tif}")
        else:
            print("⚠️ No source Sentinel-2 data found for simulation")
            return False
        
        # 4. Test the conversion process (this is where the bug was)
        from app.convert import convert_sentinel2_to_png
        
        print("🔍 Testing convert_sentinel2_to_png with NDVI disabled...")
        result = convert_sentinel2_to_png(str(input_dir), test_region)
        
        # 5. Check results
        print(f"📊 Conversion result: success={result.get('success', False)}")
        print(f"📊 Files created: {len(result.get('files', []))}")
        print(f"📊 Errors: {len(result.get('errors', []))}")
        
        # 6. The critical test - check if NDVI files were created
        ndvi_files = [f for f in result.get('files', []) if f.get('band') == 'NDVI']
        
        if ndvi_files:
            print("❌ BUG STILL EXISTS: NDVI files were created despite NDVI being disabled!")
            print(f"❌ NDVI files: {ndvi_files}")
            return False
        else:
            print("✅ BUG FIXED: No NDVI files created when NDVI is disabled")
        
        # 7. Also check the file system to make sure no NDVI files exist
        ndvi_tiff_files = list(output_dir.rglob("*NDVI*.tif"))
        ndvi_png_files = list(output_dir.rglob("*NDVI*.png"))
        
        if ndvi_tiff_files or ndvi_png_files:
            print(f"❌ FILESYSTEM CHECK FAILED: Found NDVI files in filesystem!")
            print(f"❌ NDVI TIFFs: {ndvi_tiff_files}")
            print(f"❌ NDVI PNGs: {ndvi_png_files}")
            return False
        else:
            print("✅ FILESYSTEM CHECK PASSED: No NDVI files found in filesystem")
        
        # 8. Cleanup
        if output_dir.exists():
            shutil.rmtree(output_dir)
        if input_dir.exists():
            shutil.rmtree(input_dir)
        
        print("✅ All tests passed - NDVI bug has been fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ndvi_still_works_when_enabled():
    """Test that NDVI still works correctly when enabled"""
    
    print("\n🧪 Testing that NDVI still works when enabled...")
    
    try:
        test_region = "5_99N_36_15W_enabled_test"
        
        # 1. Create region metadata with NDVI enabled
        output_dir = Path("output") / test_region
        output_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = output_dir / "metadata.txt"
        metadata_content = f"""# Region Metadata
# Generated: 2025-06-23 14:30:00
# Source: coordinate-based

Region Name: {test_region}
Source: coordinate-based
NDVI Enabled: true
Center Latitude: 5.99
Center Longitude: -36.15
"""
        
        with open(metadata_file, 'w') as f:
            f.write(metadata_content)
        
        print(f"✅ Created region with NDVI enabled: {test_region}")
        
        # 2. Check NDVI status
        from app.endpoints.region_management import isRegionNDVI
        ndvi_status = isRegionNDVI(test_region)
        print(f"📊 NDVI status: {'enabled' if ndvi_status else 'disabled'}")
        
        if not ndvi_status:
            print("❌ ERROR: NDVI should be enabled for this test")
            return False
        
        # 3. Simulate Sentinel-2 data
        input_dir = Path("input") / test_region
        sentinel2_dir = input_dir / "sentinel2"
        sentinel2_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy test Sentinel-2 data
        source_tif = Path("input/test_ndvi/sentinel2/test_ndvi_20250529_sentinel2.tif")
        if source_tif.exists():
            target_tif = sentinel2_dir / f"{test_region}_20250529_sentinel2.tif"
            shutil.copy(source_tif, target_tif)
            print(f"✅ Simulated Sentinel-2 data: {target_tif}")
        else:
            print("⚠️ No source Sentinel-2 data found for simulation")
            return False
        
        # 4. Test the conversion process
        from app.convert import convert_sentinel2_to_png
        
        print("🔍 Testing convert_sentinel2_to_png with NDVI enabled...")
        result = convert_sentinel2_to_png(str(input_dir), test_region)
        
        # 5. Check results
        print(f"📊 Conversion result: success={result.get('success', False)}")
        print(f"📊 Files created: {len(result.get('files', []))}")
        
        # 6. Check if NDVI files were created (should be created)
        ndvi_files = [f for f in result.get('files', []) if f.get('band') == 'NDVI']
        
        if ndvi_files:
            print("✅ NDVI functionality still works: NDVI files created when enabled")
        else:
            print("❌ NDVI functionality broken: No NDVI files created despite being enabled")
            print(f"❌ Errors: {result.get('errors', [])}")
            return False
        
        # 7. Cleanup
        if output_dir.exists():
            shutil.rmtree(output_dir)
        if input_dir.exists():
            shutil.rmtree(input_dir)
        
        print("✅ NDVI enabled test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🔬 COMPREHENSIVE NDVI BUG FIX TEST")
    print("=" * 60)
    
    # Test 1: Verify fix works (NDVI disabled)
    test1_passed = test_coordinate_region_ndvi_bug_fix()
    
    # Test 2: Verify NDVI still works when enabled
    test2_passed = test_ndvi_still_works_when_enabled()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"✅ NDVI Disabled Test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ NDVI Enabled Test: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! The NDVI bug has been successfully fixed!")
        print("🔧 NDVI processing is now properly controlled by the NDVI enabled/disabled setting.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED! The bug fix needs more work.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
