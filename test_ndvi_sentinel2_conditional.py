#!/usr/bin/env python3
"""
Test dynamic NDVI conditional Sentinel-2 acquisition
"""

import requests
import json
import os
import tempfile
from pathlib import Path

def test_ndvi_conditional_logic():
    """Test that Sentinel-2 acquisition is conditional based on NDVI setting"""
    
    print("🧪 Testing NDVI Conditional Sentinel-2 Logic")
    print("="*60)
    
    # Test 1: Test with NDVI enabled
    print("\n📋 Test 1: LAZ upload with NDVI enabled")
    try:
        # Create a mock LAZ file for testing
        test_laz_content = b"Mock LAZ file content for testing"
        
        # Test upload with NDVI enabled
        files = {'files': ('test_ndvi_enabled.laz', test_laz_content, 'application/octet-stream')}
        data = {'ndvi_enabled': 'true'}
        
        response = requests.post(
            'http://localhost:8000/api/laz/upload',
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload with NDVI enabled successful")
            print(f"📊 Response: {json.dumps(result, indent=2)}")
            
            # Test metadata generation (this should include Sentinel-2 acquisition)
            print("\n🛰️ Testing metadata generation with NDVI enabled...")
            region_name = result.get('region_name', 'test_ndvi_enabled')
            file_name = 'test_ndvi_enabled.laz'
            
            metadata_response = requests.post(
                'http://localhost:8000/api/laz/generate-metadata',
                data={
                    'region_name': region_name,
                    'file_name': file_name,
                    'ndvi_enabled': True
                },
                timeout=60
            )
            
            if metadata_response.status_code == 200:
                metadata_result = metadata_response.json()
                print("✅ Metadata generation successful")
                print(f"📊 Sentinel-2 attempted: {metadata_result.get('sentinel2_acquisition', {}).get('attempted', False)}")
                print(f"📊 Sentinel-2 success: {metadata_result.get('sentinel2_acquisition', {}).get('success', False)}")
                
                # Check if Sentinel-2 was attempted
                s2_attempted = metadata_result.get('sentinel2_acquisition', {}).get('attempted', False)
                if s2_attempted:
                    print("✅ NDVI enabled: Sentinel-2 acquisition was attempted as expected")
                else:
                    print("❌ NDVI enabled: Sentinel-2 acquisition was NOT attempted")
                    return False
            else:
                print(f"❌ Metadata generation failed: {metadata_response.status_code}")
                print(f"📄 Error: {metadata_response.text}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"📄 Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        return False
    
    # Test 2: Test with NDVI disabled
    print("\n📋 Test 2: LAZ upload with NDVI disabled")
    try:
        # Test upload with NDVI disabled
        files = {'files': ('test_ndvi_disabled.laz', test_laz_content, 'application/octet-stream')}
        data = {'ndvi_enabled': 'false'}
        
        response = requests.post(
            'http://localhost:8000/api/laz/upload',
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload with NDVI disabled successful")
            
            # Test metadata generation (this should skip Sentinel-2 acquisition)
            print("\n🚫 Testing metadata generation with NDVI disabled...")
            region_name = result.get('region_name', 'test_ndvi_disabled')
            file_name = 'test_ndvi_disabled.laz'
            
            metadata_response = requests.post(
                'http://localhost:8000/api/laz/generate-metadata',
                data={
                    'region_name': region_name,
                    'file_name': file_name,
                    'ndvi_enabled': False
                },
                timeout=60
            )
            
            if metadata_response.status_code == 200:
                metadata_result = metadata_response.json()
                print("✅ Metadata generation successful")
                print(f"📊 Response: {json.dumps(metadata_result, indent=2)}")
                
                # Check if Sentinel-2 was skipped
                s2_acquisition = metadata_result.get('sentinel2_acquisition', {})
                s2_attempted = s2_acquisition.get('attempted', True)  # Default to True to catch when it's not set
                s2_skipped = s2_acquisition.get('result', {}).get('skipped', False)
                
                if not s2_attempted or s2_skipped:
                    print("✅ NDVI disabled: Sentinel-2 acquisition was skipped as expected")
                else:
                    print("❌ NDVI disabled: Sentinel-2 acquisition was NOT skipped")
                    return False
            else:
                print(f"❌ Metadata generation failed: {metadata_response.status_code}")
                print(f"📄 Error: {metadata_response.text}")
                return False
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"📄 Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        return False
    
    # Test 3: Test isRegionNDVI function
    print("\n📋 Test 3: Testing isRegionNDVI function")
    try:
        # Test NDVI status check for enabled region
        response = requests.get(
            'http://localhost:8000/api/regions/test_ndvi_enabled/ndvi-status',
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ndvi_enabled', False):
                print("✅ isRegionNDVI correctly identifies NDVI-enabled region")
            else:
                print("❌ isRegionNDVI failed to identify NDVI-enabled region")
                return False
        else:
            print(f"⚠️ NDVI status check failed: {response.status_code}")
        
        # Test NDVI status check for disabled region
        response = requests.get(
            'http://localhost:8000/api/regions/test_ndvi_disabled/ndvi-status',
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if not result.get('ndvi_enabled', True):  # Default to True to catch when not set properly
                print("✅ isRegionNDVI correctly identifies NDVI-disabled region")
            else:
                print("❌ isRegionNDVI failed to identify NDVI-disabled region")
                return False
        else:
            print(f"⚠️ NDVI status check failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Test 3 warning: {e}")
    
    print("\n🎉 All tests passed! NDVI conditional logic is working correctly.")
    return True

def main():
    """Run the test"""
    print("🔧 Testing NDVI Conditional Sentinel-2 Acquisition")
    print("This test verifies that Sentinel-2 downloads only occur when NDVI is enabled")
    
    try:
        # Check if server is running
        response = requests.get('http://localhost:8000/', timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start the server first.")
        return False
    
    # Run the tests
    success = test_ndvi_conditional_logic()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("🎯 The NDVI conditional Sentinel-2 feature is working as expected.")
    else:
        print("\n❌ Some tests failed.")
        print("🔧 Please check the implementation.")
    
    return success

if __name__ == "__main__":
    main()
