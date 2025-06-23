#!/usr/bin/env python3
"""
Simplified test for NDVI conditional logic without requiring valid LAZ files
"""

import requests
import json
import os
from pathlib import Path

def test_ndvi_settings_storage():
    """Test that NDVI settings are properly stored during upload"""
    
    print("🧪 Testing NDVI Settings Storage")
    print("="*50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Upload with NDVI enabled
    print("\n📋 Test 1: Upload with NDVI enabled")
    try:
        test_laz_content = b"Mock LAZ file content for NDVI enabled test"
        
        files = {'files': ('test_ndvi_enabled_simple.laz', test_laz_content, 'application/octet-stream')}
        data = {'ndvi_enabled': 'true'}
        
        response = requests.post(
            f'{base_url}/api/laz/upload',
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload with NDVI enabled successful")
            
            # Check if settings file was created
            settings_file = Path("input/LAZ/test_ndvi_enabled_simple.settings.json")
            if settings_file.exists():
                print("✅ Settings file created successfully")
                
                # Read and verify settings
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                if settings.get('ndvi_enabled') == True:
                    print("✅ NDVI enabled setting stored correctly: True")
                else:
                    print(f"❌ NDVI enabled setting incorrect: {settings.get('ndvi_enabled')}")
                    return False
            else:
                print("❌ Settings file not created")
                return False
                
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"📄 Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        return False
    
    # Test 2: Upload with NDVI disabled
    print("\n📋 Test 2: Upload with NDVI disabled")
    try:
        test_laz_content = b"Mock LAZ file content for NDVI disabled test"
        
        files = {'files': ('test_ndvi_disabled_simple.laz', test_laz_content, 'application/octet-stream')}
        data = {'ndvi_enabled': 'false'}
        
        response = requests.post(
            f'{base_url}/api/laz/upload',
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload with NDVI disabled successful")
            
            # Check if settings file was created
            settings_file = Path("input/LAZ/test_ndvi_disabled_simple.settings.json")
            if settings_file.exists():
                print("✅ Settings file created successfully")
                
                # Read and verify settings
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                if settings.get('ndvi_enabled') == False:
                    print("✅ NDVI disabled setting stored correctly: False")
                else:
                    print(f"❌ NDVI disabled setting incorrect: {settings.get('ndvi_enabled')}")
                    return False
            else:
                print("❌ Settings file not created")
                return False
                
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"📄 Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        return False
    
    return True

def test_isregion_ndvi_function():
    """Test the isRegionNDVI function"""
    
    print("\n📋 Test 3: Testing isRegionNDVI function")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test regions that were created above
        test_cases = [
            ("test_ndvi_enabled_simple", True),
            ("test_ndvi_disabled_simple", False),
        ]
        
        for region_name, expected_ndvi in test_cases:
            print(f"\n🔍 Testing region: {region_name} (expected NDVI: {expected_ndvi})")
            
            response = requests.get(
                f'{base_url}/api/regions/{region_name}/ndvi-status',
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                actual_ndvi = result.get('ndvi_enabled', False)
                
                if actual_ndvi == expected_ndvi:
                    print(f"✅ isRegionNDVI returned correct value: {actual_ndvi}")
                else:
                    print(f"❌ isRegionNDVI returned incorrect value: {actual_ndvi}, expected: {expected_ndvi}")
                    return False
            else:
                print(f"❌ NDVI status check failed: {response.status_code}")
                print(f"📄 Error: {response.text}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files created during testing"""
    test_files = [
        "input/LAZ/test_ndvi_enabled_simple.laz",
        "input/LAZ/test_ndvi_enabled_simple.settings.json",
        "input/LAZ/test_ndvi_disabled_simple.laz",
        "input/LAZ/test_ndvi_disabled_simple.settings.json",
    ]
    
    for file_path in test_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Cleaned up: {file_path}")
        except Exception as e:
            print(f"⚠️ Could not remove {file_path}: {e}")

def main():
    """Run the simplified NDVI conditional tests"""
    
    print("🔧 Testing NDVI Conditional Logic (Simplified)")
    print("This test verifies NDVI settings storage and retrieval")
    print("")
    
    try:
        # Test NDVI settings storage
        storage_ok = test_ndvi_settings_storage()
        
        # Test isRegionNDVI function  
        function_ok = test_isregion_ndvi_function()
        
        print("\n" + "="*50)
        print("📊 Test Results:")
        print(f"   NDVI Settings Storage: {'✅ PASS' if storage_ok else '❌ FAIL'}")
        print(f"   isRegionNDVI Function: {'✅ PASS' if function_ok else '❌ FAIL'}")
        
        if storage_ok and function_ok:
            print("\n🎉 All tests passed!")
            print("✅ NDVI settings are properly stored and retrieved")
            print("✅ The conditional logic foundation is working")
            print("\n💡 Next step: Test with real LAZ files to verify Sentinel-2 conditional download")
        else:
            print("\n❌ Some tests failed.")
            print("🔧 Please check the implementation.")
            
    finally:
        # Always cleanup test files
        print("\n🧹 Cleaning up test files...")
        cleanup_test_files()

if __name__ == "__main__":
    main()
