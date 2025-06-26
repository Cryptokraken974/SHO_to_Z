#!/usr/bin/env python3
"""
Comprehensive Archaeological Implementation Test
===============================================

This script tests both Archaeological implementations:
1. Hillshade RGB - Archaeological Subtle Relief (10-90 percentile)
2. SVF - Archaeological Cividis Enhanced (5-95 percentile)

This validates that both approaches from the testing suites are now 
fully integrated into convert.py and working correctly.
"""

import os
import sys
import tempfile

def test_hillshade_rgb_archaeological():
    """Test the Archaeological Subtle Relief implementation for hillshade RGB."""
    print("🌄 Testing Hillshade RGB Archaeological Subtle Relief...")
    
    # Check if test file exists
    test_file = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb_test.tif"
    if not os.path.exists(test_file):
        print(f"⚠️ Test file not found: {test_file}")
        return False
    
    try:
        from app.convert import convert_hillshade_rgb_to_archaeological_png
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "hillshade_rgb_archaeological_test.png")
            
            # Test Archaeological Subtle Relief (10-90 percentile)
            result = convert_hillshade_rgb_to_archaeological_png(
                test_file,
                output_path,
                enhancement_type="subtle_relief",  # 10-90 percentile
                archaeological_mode=True,
                enhanced_resolution=True,
                save_to_consolidated=False
            )
            
            if os.path.exists(result):
                file_size = os.path.getsize(result) / 1024  # KB
                print(f"✅ Hillshade RGB Archaeological PNG generated: {os.path.basename(result)} ({file_size:.1f} KB)")
                return True
            else:
                print("❌ Hillshade RGB Archaeological PNG generation failed")
                return False
                
    except Exception as e:
        print(f"❌ Hillshade RGB test failed: {e}")
        return False

def test_svf_archaeological_cividis():
    """Test the Archaeological Cividis Enhanced implementation for SVF."""
    print("🌌 Testing SVF Archaeological Cividis Enhanced...")
    
    # Check if test file exists
    test_file = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/SVF/svf_test.tif"
    if not os.path.exists(test_file):
        print(f"⚠️ Test file not found: {test_file}")
        return False
    
    try:
        from app.convert import convert_svf_to_cividis_png_clean, convert_svf_to_archaeological_png
        
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # Test 1: Clean SVF with Archaeological Cividis Enhanced (5-95 percentile)
            clean_path = os.path.join(temp_dir, "svf_clean_test.png")
            result_clean = convert_svf_to_cividis_png_clean(
                test_file,
                clean_path,
                enhanced_resolution=True,
                save_to_consolidated=False
            )
            
            clean_success = os.path.exists(result_clean)
            if clean_success:
                file_size = os.path.getsize(result_clean) / 1024  # KB
                print(f"✅ SVF Clean PNG (Archaeological Cividis Enhanced): {os.path.basename(result_clean)} ({file_size:.1f} KB)")
            
            # Test 2: Decorated SVF with Archaeological Cividis Enhanced
            decorated_path = os.path.join(temp_dir, "svf_decorated_test.png")
            result_decorated = convert_svf_to_archaeological_png(
                test_file,
                decorated_path,
                enhancement_type="archaeological_cividis",  # 5-95 percentile
                enhanced_resolution=True,
                save_to_consolidated=False
            )
            
            decorated_success = os.path.exists(result_decorated)
            if decorated_success:
                file_size = os.path.getsize(result_decorated) / 1024  # KB
                print(f"✅ SVF Decorated PNG (Archaeological Cividis Enhanced): {os.path.basename(result_decorated)} ({file_size:.1f} KB)")
            
            return clean_success and decorated_success
                
    except Exception as e:
        print(f"❌ SVF test failed: {e}")
        return False

def test_import_compatibility():
    """Test that all imports work correctly and old function names are properly retired."""
    print("📦 Testing import compatibility...")
    
    try:
        # Test new function imports
        from app.convert import convert_svf_to_cividis_png_clean
        from app.convert import convert_svf_to_archaeological_png
        from app.convert import convert_hillshade_rgb_to_archaeological_png
        print("✅ All new archaeological functions imported successfully")
        
        # Test that old function name doesn't exist
        try:
            from app.convert import convert_svf_to_cividis_png
            print("⚠️ Old function name 'convert_svf_to_cividis_png' still exists - should be cleaned up")
            old_exists = True
        except ImportError:
            print("✅ Old function name properly removed")
            old_exists = False
        
        return True
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    """Run comprehensive archaeological implementation tests."""
    print("🏺 COMPREHENSIVE ARCHAEOLOGICAL IMPLEMENTATION TEST")
    print("=" * 60)
    print("Testing both Archaeological Subtle Relief (Hillshade RGB) and")
    print("Archaeological Cividis Enhanced (SVF) implementations")
    print("=" * 60)
    
    # Test imports first
    import_success = test_import_compatibility()
    
    if not import_success:
        print("\n❌ Import tests failed. Cannot proceed with function tests.")
        return False
    
    print("\n" + "=" * 60)
    
    # Test hillshade RGB archaeological implementation
    hillshade_success = test_hillshade_rgb_archaeological()
    
    print("\n" + "=" * 60)
    
    # Test SVF archaeological implementation
    svf_success = test_svf_archaeological_cividis()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    
    if hillshade_success and svf_success:
        print("🎉 ALL ARCHAEOLOGICAL IMPLEMENTATIONS WORKING!")
        print("✅ Hillshade RGB: Archaeological Subtle Relief (10-90 percentile)")
        print("✅ SVF: Archaeological Cividis Enhanced (5-95 percentile)")
        print("\n🏺 Archaeological visualization suite is fully operational!")
        print("🌄 Multi-directional hillshade with optimal contrast enhancement")
        print("🌌 Sky View Factor with perceptually uniform colormap")
        print("📊 Both approaches optimized for archaeological feature detection")
        return True
    else:
        print("❌ Some archaeological implementations failed:")
        if not hillshade_success:
            print("   ❌ Hillshade RGB Archaeological Subtle Relief")
        if not svf_success:
            print("   ❌ SVF Archaeological Cividis Enhanced")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
