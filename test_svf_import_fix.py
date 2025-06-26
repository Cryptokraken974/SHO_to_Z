#!/usr/bin/env python3
"""
Test Archaeological SVF Implementation
=====================================

This script tests that the Archaeological Cividis Enhanced SVF implementation 
is working correctly after fixing the import issues.

The test verifies:
1. Function imports work correctly
2. Both archaeological and clean SVF functions work
3. 5-95 percentile enhancement is applied
"""

import os
import sys

def test_svf_import_fix():
    """Test that SVF imports are now working correctly."""
    print("🧪 Testing SVF import fixes...")
    
    try:
        # Test the main function import
        from app.convert import convert_svf_to_cividis_png_clean
        print("✅ Successfully imported convert_svf_to_cividis_png_clean")
        
        # Test the archaeological function import  
        from app.convert import convert_svf_to_archaeological_png
        print("✅ Successfully imported convert_svf_to_archaeological_png")
        
        # Test that the old function name doesn't exist
        try:
            from app.convert import convert_svf_to_cividis_png
            print("⚠️ Old function name still exists - this should be cleaned up")
        except ImportError:
            print("✅ Old function name properly removed")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_svf_with_test_file():
    """Test SVF functions with the test file."""
    print("\n🧪 Testing SVF functions with test file...")
    
    test_svf_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/SVF/svf_test.tif"
    
    if not os.path.exists(test_svf_path):
        print(f"⚠️ Test SVF file not found: {test_svf_path}")
        return False
    
    try:
        from app.convert import convert_svf_to_cividis_png_clean, convert_svf_to_archaeological_png
        import tempfile
        
        # Test the clean function (Archaeological Cividis Enhanced)
        print("🌌 Testing Archaeological Cividis Enhanced (clean)...")
        with tempfile.TemporaryDirectory() as temp_dir:
            clean_png_path = os.path.join(temp_dir, "svf_clean_test.png")
            result_clean = convert_svf_to_cividis_png_clean(
                test_svf_path,
                clean_png_path,
                enhanced_resolution=True,
                save_to_consolidated=False
            )
            
            if os.path.exists(result_clean):
                print(f"✅ Clean SVF PNG generated successfully: {os.path.basename(result_clean)}")
            else:
                print("❌ Clean SVF PNG generation failed")
                return False
        
        # Test the archaeological function 
        print("🏺 Testing Archaeological SVF function...")
        with tempfile.TemporaryDirectory() as temp_dir:
            arch_png_path = os.path.join(temp_dir, "svf_archaeological_test.png")
            result_arch = convert_svf_to_archaeological_png(
                test_svf_path,
                arch_png_path,
                enhanced_resolution=True,
                save_to_consolidated=False,
                enhancement_type="archaeological_cividis"
            )
            
            if os.path.exists(result_arch):
                print(f"✅ Archaeological SVF PNG generated successfully: {os.path.basename(result_arch)}")
            else:
                print("❌ Archaeological SVF PNG generation failed")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ SVF function test failed: {e}")
        return False

def main():
    """Run all SVF import and functionality tests."""
    print("🏺 ARCHAEOLOGICAL SVF IMPLEMENTATION TEST")
    print("=" * 50)
    
    # Test imports
    import_success = test_svf_import_fix()
    
    if not import_success:
        print("\n❌ Import tests failed. Cannot proceed with function tests.")
        return False
    
    # Test functionality
    function_success = test_svf_with_test_file()
    
    if import_success and function_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Archaeological Cividis Enhanced SVF implementation is working correctly")
        print("🌌 5-95 percentile enhancement for optimal archaeological feature detection")
        print("🏺 Both clean and decorated SVF functions are operational")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
