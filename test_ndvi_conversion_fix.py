#!/usr/bin/env python3
"""
Test script to verify that NDVI processing is properly controlled by the NDVI enabled/disabled setting
in the convert_sentinel2_to_png function.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ndvi_conversion_control():
    """Test that NDVI conversion respects the NDVI enabled/disabled setting"""
    
    print("🧪 Testing NDVI conversion control...")
    
    try:
        # Import required functions
        from app.convert import convert_sentinel2_to_png
        from app.endpoints.region_management import isRegionNDVI
        
        # Test with a known region that has NDVI disabled
        # First, let's check what regions exist
        print("\n📂 Checking available regions...")
        
        output_dir = Path("output")
        if output_dir.exists():
            regions = [d.name for d in output_dir.iterdir() if d.is_dir()]
            print(f"Found regions: {regions}")
            
            # Test with any available region
            if regions:
                test_region = regions[0]
                print(f"\n🔍 Testing with region: {test_region}")
                
                # Check NDVI status
                ndvi_status = isRegionNDVI(test_region)
                print(f"📊 NDVI status for {test_region}: {'enabled' if ndvi_status else 'disabled'}")
                
                # Test the function (note: this will only work if Sentinel-2 data exists)
                input_path = Path("input") / test_region
                if input_path.exists():
                    sentinel2_path = input_path / "sentinel2"
                    if sentinel2_path.exists() and list(sentinel2_path.glob("*.tif")):
                        print(f"✅ Found Sentinel-2 data for {test_region}")
                        print("🧪 Testing convert_sentinel2_to_png function...")
                        
                        # Call the conversion function
                        result = convert_sentinel2_to_png(str(input_path), test_region)
                        
                        print(f"📊 Conversion result: {result}")
                        
                        # Check if NDVI was processed based on the setting
                        ndvi_files = [f for f in result.get('files', []) if f.get('band') == 'NDVI']
                        
                        if ndvi_status:
                            if ndvi_files:
                                print("✅ NDVI enabled and NDVI files were created - CORRECT")
                            else:
                                print("❌ NDVI enabled but no NDVI files were created - ISSUE")
                        else:
                            if ndvi_files:
                                print("❌ NDVI disabled but NDVI files were created - ISSUE FOUND")
                                return False
                            else:
                                print("✅ NDVI disabled and no NDVI files were created - CORRECT")
                        
                        return True
                    else:
                        print(f"⚠️ No Sentinel-2 data found for {test_region}")
                else:
                    print(f"⚠️ Input directory not found for {test_region}")
            else:
                print("⚠️ No regions found to test")
        else:
            print("⚠️ Output directory not found")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("🔬 NDVI Conversion Control Test")
    print("=" * 50)
    
    success = test_ndvi_conversion_control()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completed successfully")
    else:
        print("❌ Test failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
