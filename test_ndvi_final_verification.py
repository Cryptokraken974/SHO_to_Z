#!/usr/bin/env python3
"""
Final NDVI Feature Verification Test
Tests both NDVI enabled and disabled workflows to ensure complete functionality.
"""

import requests
import json
import time
from pathlib import Path

def test_ndvi_enabled_upload():
    """Test LAZ upload with NDVI enabled"""
    print("🧪 Testing NDVI Enabled Upload...")
    
    # Create a mock LAZ file for testing
    test_file_content = b"Mock LAZ file content for NDVI enabled test"
    
    # Prepare the upload
    files = {'files': ('test_ndvi_enabled.laz', test_file_content, 'application/octet-stream')}
    data = {'ndvi_enabled': 'true'}  # Enable NDVI
    
    try:
        response = requests.post('http://localhost:8000/api/laz/upload', files=files, data=data)
        print(f"  📤 Upload response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Upload successful: {result['message']}")
            
            # Check if settings file was created with NDVI enabled
            settings_file = Path("input/LAZ/test_ndvi_enabled.settings.json")
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                print(f"  🌿 NDVI setting stored: {settings.get('ndvi_enabled', 'Not found')}")
                return settings.get('ndvi_enabled', False)
            else:
                print("  ⚠️  Settings file not found")
                return False
        else:
            print(f"  ❌ Upload failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Upload error: {str(e)}")
        return False

def test_ndvi_disabled_upload():
    """Test LAZ upload with NDVI disabled"""
    print("\n🧪 Testing NDVI Disabled Upload...")
    
    # Create a mock LAZ file for testing
    test_file_content = b"Mock LAZ file content for NDVI disabled test"
    
    # Prepare the upload
    files = {'files': ('test_ndvi_disabled.laz', test_file_content, 'application/octet-stream')}
    data = {'ndvi_enabled': 'false'}  # Disable NDVI
    
    try:
        response = requests.post('http://localhost:8000/api/laz/upload', files=files, data=data)
        print(f"  📤 Upload response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Upload successful: {result['message']}")
            
            # Check if settings file was created with NDVI disabled
            settings_file = Path("input/LAZ/test_ndvi_disabled.settings.json")
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                print(f"  🚫 NDVI setting stored: {settings.get('ndvi_enabled', 'Not found')}")
                return settings.get('ndvi_enabled', True) == False  # Should be False
            else:
                print("  ⚠️  Settings file not found")
                return False
        else:
            print(f"  ❌ Upload failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Upload error: {str(e)}")
        return False

def test_isregion_ndvi_function():
    """Test the isRegionNDVI function"""
    print("\n🧪 Testing isRegionNDVI Function...")
    
    try:
        # Test with a region that should have NDVI enabled
        response = requests.get('http://localhost:8000/api/regions/test_ndvi_enabled/ndvi-status')
        
        if response.status_code == 200:
            result = response.json()
            print(f"  🌿 test_ndvi_enabled region NDVI status: {result.get('ndvi_enabled', 'Unknown')}")
            enabled_result = result.get('ndvi_enabled', False)
        else:
            print(f"  ⚠️  Could not check enabled region: {response.status_code}")
            enabled_result = None
        
        # Test with a region that should have NDVI disabled
        response = requests.get('http://localhost:8000/api/regions/test_ndvi_disabled/ndvi-status')
        
        if response.status_code == 200:
            result = response.json()
            print(f"  🚫 test_ndvi_disabled region NDVI status: {result.get('ndvi_enabled', 'Unknown')}")
            disabled_result = result.get('ndvi_enabled', True)
        else:
            print(f"  ⚠️  Could not check disabled region: {response.status_code}")
            disabled_result = None
            
        # Test with OR_WizardIsland (should be disabled)
        response = requests.get('http://localhost:8000/api/regions/OR_WizardIsland/ndvi-status')
        
        if response.status_code == 200:
            result = response.json()
            print(f"  🏔️  OR_WizardIsland region NDVI status: {result.get('ndvi_enabled', 'Unknown')}")
            wizard_result = result.get('ndvi_enabled', True)
        else:
            print(f"  ⚠️  Could not check OR_WizardIsland region: {response.status_code}")
            wizard_result = None
        
        return enabled_result, disabled_result, wizard_result
        
    except Exception as e:
        print(f"  ❌ isRegionNDVI test error: {str(e)}")
        return None, None, None

def test_server_health():
    """Test if the server is running and responsive"""
    print("🏥 Testing Server Health...")
    
    try:
        response = requests.get('http://localhost:8000/api/laz/files', timeout=5)
        if response.status_code == 200:
            print("  ✅ Server is running and responsive")
            return True
        else:
            print(f"  ⚠️  Server responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Server health check failed: {str(e)}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    print("\n🧹 Cleaning up test files...")
    
    test_files = [
        "input/LAZ/test_ndvi_enabled.laz",
        "input/LAZ/test_ndvi_enabled.settings.json",
        "input/LAZ/test_ndvi_disabled.laz", 
        "input/LAZ/test_ndvi_disabled.settings.json"
    ]
    
    for file_path in test_files:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                print(f"  🗑️  Removed: {file_path}")
        except Exception as e:
            print(f"  ⚠️  Could not remove {file_path}: {str(e)}")

def main():
    """Run all NDVI feature verification tests"""
    print("🎯 NDVI Feature Final Verification Test")
    print("=" * 50)
    
    # Test server health first
    if not test_server_health():
        print("❌ Server is not running. Please start the server first.")
        return
    
    # Run upload tests
    ndvi_enabled_success = test_ndvi_enabled_upload()
    ndvi_disabled_success = test_ndvi_disabled_upload()
    
    # Wait a moment for files to be processed
    time.sleep(1)
    
    # Test the isRegionNDVI function
    enabled_status, disabled_status, wizard_status = test_isregion_ndvi_function()
    
    # Summarize results
    print("\n📊 Test Results Summary")
    print("=" * 30)
    print(f"✅ NDVI Enabled Upload: {'PASS' if ndvi_enabled_success else 'FAIL'}")
    print(f"✅ NDVI Disabled Upload: {'PASS' if ndvi_disabled_success else 'FAIL'}")
    print(f"✅ isRegionNDVI Enabled Check: {'PASS' if enabled_status else 'FAIL'}")
    print(f"✅ isRegionNDVI Disabled Check: {'PASS' if disabled_status == False else 'FAIL'}")
    print(f"✅ OR_WizardIsland NDVI Check: {'PASS' if wizard_status == False else 'FAIL'}")
    
    # Overall result
    all_tests_passed = all([
        ndvi_enabled_success,
        ndvi_disabled_success, 
        enabled_status,
        disabled_status == False,
        wizard_status == False
    ])
    
    if all_tests_passed:
        print("\n🎉 ALL TESTS PASSED! NDVI Feature is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
    
    # Cleanup
    cleanup_test_files()
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
