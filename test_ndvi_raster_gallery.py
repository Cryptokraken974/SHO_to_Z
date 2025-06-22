#!/usr/bin/env python3
"""
Test script to verify NDVI appears in raster gallery.
"""

import requests
import json

def test_region_png_files():
    """Test that region PNG files API includes NDVI"""
    
    # Test region that should have NDVI data
    test_region = "PRE_A05-01"
    
    print(f"🧪 Testing region PNG files for region: {test_region}")
    
    try:
        # Test the region PNG files endpoint
        print("📡 Testing /api/regions/{region}/png-files endpoint...")
        response = requests.get(
            f'http://localhost:8000/api/regions/{test_region}/png-files',
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful")
            print(f"📊 Found {len(result.get('png_files', []))} PNG files")
            
            # Look for NDVI files
            ndvi_files = [f for f in result.get('png_files', []) if 'ndvi' in f.get('processing_type', '').lower()]
            
            if ndvi_files:
                print("✅ NDVI files found in raster gallery:")
                for ndvi_file in ndvi_files:
                    print(f"   📄 {ndvi_file['file_name']} - {ndvi_file['display_name']}")
                    print(f"      Processing type: {ndvi_file['processing_type']}")
                    print(f"      Size: {ndvi_file['file_size_mb']} MB")
                return True
            else:
                print("❌ No NDVI files found in raster gallery")
                print("📄 Available processing types:")
                processing_types = set(f.get('processing_type', 'unknown') for f in result.get('png_files', []))
                for pt in sorted(processing_types):
                    print(f"   - {pt}")
                    
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    return False

def test_raster_overlay_api():
    """Test that raster overlay API works for NDVI"""
    
    # Test NDVI overlay for a region
    test_region = "PRE_A05-01"
    
    print(f"🧪 Testing raster overlay API for NDVI: {test_region}")
    
    try:
        response = requests.get(
            f'http://localhost:8000/api/overlay/raster/{test_region}/ndvi',
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Raster overlay API successful")
            print(f"📊 Response keys: {list(result.keys())}")
            
            if 'image_data' in result and result['image_data']:
                print("✅ NDVI image data found in raster overlay")
                return True
            else:
                print("❌ No image data in raster overlay response")
                
        elif response.status_code == 404:
            print("⚠️ NDVI raster overlay not found (may need processing first)")
            print(f"📄 Response: {response.text}")
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    return False

def main():
    """Run all tests"""
    print("🚀 Starting NDVI raster gallery tests")
    print("="*60)
    
    # Test 1: Region PNG files includes NDVI
    print("\n🧪 Test 1: Region PNG files includes NDVI")
    test1_passed = test_region_png_files()
    
    # Test 2: Raster overlay API works for NDVI
    print("\n🧪 Test 2: Raster overlay API for NDVI")
    test2_passed = test_raster_overlay_api()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Results Summary:")
    print(f"   Test 1 (PNG files include NDVI): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Test 2 (Raster overlay API): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! NDVI should appear in raster gallery.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
