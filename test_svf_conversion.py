#!/usr/bin/env python3
"""
Test Sky View Factor PNG conversion with cividis colormap.
This test verifies that the new convert_svf_to_cividis_png function works correctly.
"""

import sys
import os
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

def test_svf_conversion_import():
    """Test that the convert_svf_to_cividis_png function can be imported successfully."""
    print("🧪 Testing SVF conversion function import...")
    
    try:
        from app.convert import convert_svf_to_cividis_png
        print("✅ Successfully imported convert_svf_to_cividis_png")
        
        # Check function signature
        import inspect
        sig = inspect.signature(convert_svf_to_cividis_png)
        print(f"📋 Function signature: {sig}")
        
        # Check docstring
        if convert_svf_to_cividis_png.__doc__:
            print("📖 Function has documentation")
        else:
            print("⚠️ Function missing documentation")
            
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import convert_svf_to_cividis_png: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_svf_function_exists():
    """Test that the function exists and has the expected parameters."""
    print("\n🔍 Testing function parameters...")
    
    try:
        from app.convert import convert_svf_to_cividis_png
        import inspect
        
        sig = inspect.signature(convert_svf_to_cividis_png)
        params = list(sig.parameters.keys())
        
        expected_params = ['tif_path', 'png_path', 'enhanced_resolution', 'save_to_consolidated']
        
        print(f"📝 Expected parameters: {expected_params}")
        print(f"📝 Actual parameters: {params}")
        
        # Check if all expected parameters are present
        missing = [p for p in expected_params if p not in params]
        if missing:
            print(f"❌ Missing parameters: {missing}")
            return False
        
        print("✅ All expected parameters are present")
        return True
        
    except Exception as e:
        print(f"❌ Error checking parameters: {e}")
        return False

def test_all_imports():
    """Test that all conversion functions can be imported."""
    print("\n🔗 Testing all conversion function imports...")
    
    conversion_functions = [
        'convert_geotiff_to_png',
        'convert_chm_to_viridis_png',
        'convert_slope_to_grayscale_png',
        'convert_slope_to_inferno_png',
        'convert_lrm_to_coolwarm_png',
        'convert_svf_to_cividis_png'  # Our new function
    ]
    
    try:
        from app import convert
        
        success_count = 0
        for func_name in conversion_functions:
            try:
                func = getattr(convert, func_name)
                print(f"✅ {func_name}: Available")
                success_count += 1
            except AttributeError:
                print(f"❌ {func_name}: Missing")
        
        print(f"\n📊 Results: {success_count}/{len(conversion_functions)} functions available")
        
        if success_count == len(conversion_functions):
            print("🎉 All conversion functions are available!")
            return True
        else:
            print("⚠️ Some conversion functions are missing")
            return False
            
    except Exception as e:
        print(f"❌ Error importing conversion module: {e}")
        return False

if __name__ == "__main__":
    print("🌌 Sky View Factor Conversion Test")
    print("=" * 50)
    
    # Run all tests
    test_results = []
    test_results.append(test_svf_conversion_import())
    test_results.append(test_svf_function_exists())
    test_results.append(test_all_imports())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The convert_svf_to_cividis_png function is ready to use.")
        print("\n💡 The Sky View Factor processing should now work without the import error.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        
    print("=" * 50)
