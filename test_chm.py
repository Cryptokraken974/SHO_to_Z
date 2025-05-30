#!/usr/bin/env python3
"""
Test script to verify CHM (Canopy Height Model) functionality
"""

import os
import sys
import traceback

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_chm_processing():
    """Test CHM processing with available LAZ files"""
    
    # Test with available LAZ files
    test_files = [
        "input/foxisland/FoxIsland.laz",
        "input/wizardisland/OR_WizardIsland.laz"
    ]
    
    for laz_file in test_files:
        if os.path.exists(laz_file):
            print(f"\n{'='*60}")
            print(f"🧪 Testing CHM processing with: {laz_file}")
            print(f"{'='*60}")
            
            try:
                # Import the CHM function
                from processing.chm import chm
                
                # Test CHM generation
                print(f"🌳 Starting CHM test...")
                chm_path = chm(laz_file)
                
                if chm_path and os.path.exists(chm_path):
                    print(f"✅ CHM test PASSED!")
                    print(f"📄 CHM file created: {chm_path}")
                    print(f"📊 CHM file size: {os.path.getsize(chm_path):,} bytes")
                else:
                    print(f"❌ CHM test FAILED: No output file created")
                    
            except Exception as e:
                print(f"❌ CHM test FAILED with error:")
                print(f"   Error: {str(e)}")
                print(f"   Type: {type(e).__name__}")
                traceback.print_exc()
                
        else:
            print(f"⚠️ Test file not found: {laz_file}")

def test_chm_dependencies():
    """Test that CHM dependencies (DSM and DTM) work correctly"""
    
    print(f"\n{'='*60}")
    print(f"🔍 Testing CHM Dependencies")
    print(f"{'='*60}")
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from processing.dsm import dsm
        from processing.dtm import dtm
        from processing.chm import chm
        print("✅ All imports successful")
        
        # Test GDAL availability
        print("📦 Testing GDAL...")
        from osgeo import gdal
        from osgeo_utils import gdal_calc
        print("✅ GDAL and gdal_calc available")
        
        # Test with a file if available
        test_file = "input/foxisland/FoxIsland.laz"
        if os.path.exists(test_file):
            print(f"🧪 Testing dependency chain with {test_file}...")
            
            print("🏗️ Testing DSM generation...")
            dsm_path = dsm(test_file)
            print(f"✅ DSM: {dsm_path}")
            
            print("🏔️ Testing DTM generation...")
            dtm_path = dtm(test_file)
            print(f"✅ DTM: {dtm_path}")
            
            if os.path.exists(dsm_path) and os.path.exists(dtm_path):
                print("✅ Both DSM and DTM files exist - ready for CHM calculation")
            else:
                print("❌ Missing DSM or DTM files")
                print(f"   DSM exists: {os.path.exists(dsm_path)}")
                print(f"   DTM exists: {os.path.exists(dtm_path)}")
        
    except Exception as e:
        print(f"❌ Dependency test FAILED:")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        traceback.print_exc()

if __name__ == "__main__":
    print("🌳 CHM (Canopy Height Model) Test Suite")
    print("=" * 60)
    
    # Test dependencies first
    test_chm_dependencies()
    
    # Test CHM processing
    test_chm_processing()
    
    print(f"\n{'='*60}")
    print("🏁 CHM test suite completed")
    print(f"{'='*60}")
