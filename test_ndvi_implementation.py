#!/usr/bin/env python3
"""
Test NDVI Implementation
Tests the complete NDVI feature implementation including:
1. NDVI checkbox capture in frontend
2. NDVI parameter passing to backend
3. NDVI storage in metadata.txt
4. isRegionNDVI function
"""

import requests
import json
from pathlib import Path
import tempfile
import os

def test_ndvi_region_creation():
    """Test NDVI region creation via API"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing NDVI region creation...")
    
    # Test data for region creation
    region_data = {
        "region_name": "test_ndvi_region",
        "coordinates": {
            "lat": 40.7128,
            "lng": -74.0060
        },
        "place_name": "Test NDVI Region",
        "ndvi_enabled": True,
        "created_at": "2024-01-01T12:00:00Z"
    }
    
    try:
        response = requests.post(f"{base_url}/api/create-region", json=region_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ NDVI region creation successful")
            print(f"   📁 Region folder: {result.get('region_folder')}")
            return True
        else:
            print(f"❌ Region creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing region creation: {e}")
        return False

def test_ndvi_status_api():
    """Test NDVI status API endpoint"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing NDVI status API...")
    
    try:
        # Test the NDVI status endpoint
        response = requests.get(f"{base_url}/api/regions/test_ndvi_region/ndvi-status")
        
        if response.status_code == 200:
            result = response.json()
            ndvi_enabled = result.get('ndvi_enabled', False)
            print(f"✅ NDVI status API working: NDVI enabled = {ndvi_enabled}")
            return ndvi_enabled
        elif response.status_code == 404:
            print("⚠️ Region not found (expected if region creation failed)")
            return False
        else:
            print(f"❌ NDVI status API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing NDVI status API: {e}")
        return False

def test_metadata_file_ndvi():
    """Test that metadata.txt contains NDVI information"""
    base_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z")
    metadata_path = base_path / "output" / "test_ndvi_region" / "metadata.txt"
    
    print("🧪 Testing metadata.txt NDVI content...")
    
    if not metadata_path.exists():
        print("⚠️ Metadata file not found (expected if region was just created)")
        return False
    
    try:
        with open(metadata_path, 'r') as f:
            content = f.read()
        
        if "NDVI Enabled: true" in content:
            print("✅ Metadata contains NDVI enabled: true")
            return True
        elif "NDVI Enabled: false" in content:
            print("❌ Metadata contains NDVI enabled: false (should be true)")
            return False
        else:
            print("❌ Metadata does not contain NDVI information")
            print("   Content preview:")
            print("   " + "\n   ".join(content.split('\n')[:10]))
            return False
            
    except Exception as e:
        print(f"❌ Error reading metadata file: {e}")
        return False

def test_laz_upload_with_ndvi():
    """Test LAZ upload with NDVI parameter"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing LAZ upload with NDVI parameter...")
    
    # Create a minimal test file to simulate a LAZ file
    test_content = b"Test LAZ file content for NDVI testing"
    
    try:
        # Test the upload endpoint with NDVI parameter
        files = {
            'files': ('test_ndvi.laz', test_content, 'application/octet-stream')
        }
        data = {
            'ndvi_enabled': 'true'  # Form data, so string
        }
        
        response = requests.post(f"{base_url}/api/laz/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ LAZ upload with NDVI parameter successful")
            print(f"   📁 Uploaded files: {len(result.get('files', []))}")
            return True
        else:
            print(f"❌ LAZ upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing LAZ upload: {e}")
        return False

def check_laz_settings_file():
    """Check if LAZ settings file was created"""
    laz_input_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ")
    settings_file = laz_input_path / "test_ndvi.settings.json"
    
    print("🧪 Checking LAZ settings file...")
    
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            
            ndvi_enabled = settings.get('ndvi_enabled', False)
            print(f"✅ Settings file found with NDVI enabled: {ndvi_enabled}")
            return ndvi_enabled
        except Exception as e:
            print(f"❌ Error reading settings file: {e}")
            return False
    else:
        print("❌ Settings file not found")
        return False

def cleanup_test_files():
    """Clean up test files"""
    print("🧹 Cleaning up test files...")
    
    # Remove test region
    test_region_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/test_ndvi_region")
    if test_region_path.exists():
        import shutil
        shutil.rmtree(test_region_path)
        print("   ✅ Removed test region folder")
    
    # Remove test LAZ file and settings
    laz_input_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ")
    test_laz = laz_input_path / "test_ndvi.laz"
    test_settings = laz_input_path / "test_ndvi.settings.json"
    
    if test_laz.exists():
        test_laz.unlink()
        print("   ✅ Removed test LAZ file")
    
    if test_settings.exists():
        test_settings.unlink()
        print("   ✅ Removed test settings file")

def main():
    """Run all NDVI tests"""
    print("🎯 NDVI Implementation Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test 1: Region creation with NDVI
    results.append(("Region Creation with NDVI", test_ndvi_region_creation()))
    
    # Test 2: NDVI status API
    results.append(("NDVI Status API", test_ndvi_status_api()))
    
    # Test 3: Metadata file content
    results.append(("Metadata NDVI Content", test_metadata_file_ndvi()))
    
    # Test 4: LAZ upload with NDVI
    results.append(("LAZ Upload with NDVI", test_laz_upload_with_ndvi()))
    
    # Test 5: LAZ settings file
    results.append(("LAZ Settings File", check_laz_settings_file()))
    
    # Print results summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All NDVI tests passed! Implementation is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the implementation.")
    
    # Ask about cleanup
    cleanup = input("\n🧹 Clean up test files? (y/n): ").lower().strip()
    if cleanup == 'y':
        cleanup_test_files()
    else:
        print("   Test files preserved for inspection")

if __name__ == "__main__":
    main()
