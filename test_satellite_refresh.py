#!/usr/bin/env python3
"""
Test script to verify satellite gallery refresh functionality after NDVI processing.
"""

import requests
import json
import time

def test_ndvi_processing_triggers_refresh():
    """Test that NDVI processing includes satellite refresh flags"""
    
    # Test region that should have Sentinel-2 data
    test_region = "PRE_A05-01"
    
    print(f"🧪 Testing NDVI processing for region: {test_region}")
    
    try:
        # Test the conversion endpoint
        print("📡 Testing /api/convert-sentinel2 endpoint...")
        response = requests.post(
            'http://localhost:8000/api/convert-sentinel2',
            data={'region_name': test_region},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful")
            print(f"📊 Response structure: {json.dumps(result, indent=2)}")
            
            # Check for NDVI completion flags
            if result.get('ndvi_completed'):
                print("✅ NDVI completion flag found in response")
                if result.get('trigger_satellite_refresh'):
                    print("✅ Satellite refresh trigger found in response")
                    print(f"🔄 Refresh region: {result.get('trigger_satellite_refresh')}")
                    return True
                else:
                    print("❌ No satellite refresh trigger in response")
            else:
                print("❌ No NDVI completion flag in response")
                
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    return False

def test_satellite_overlay_api():
    """Test that satellite overlay API works for NDVI"""
    
    # Test NDVI overlay for a region
    test_region_band = "PRE_A05-01_NDVI"
    
    print(f"🧪 Testing satellite overlay API for: {test_region_band}")
    
    try:
        response = requests.get(
            f'http://localhost:8000/api/overlay/sentinel2/{test_region_band}',
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Satellite overlay API successful")
            print(f"📊 Response keys: {list(result.keys())}")
            
            if 'image_data' in result and result['image_data']:
                print("✅ NDVI image data found in response")
                return True
            else:
                print("❌ No image data in response")
                
        elif response.status_code == 404:
            print("⚠️ NDVI overlay not found (may need processing first)")
            print(f"📄 Response: {response.text}")
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    return False

def main():
    """Run all tests"""
    print("🚀 Starting satellite gallery refresh tests")
    print("="*60)
    
    # Test 1: NDVI processing includes refresh flags
    print("\n🧪 Test 1: NDVI processing refresh flags")
    test1_passed = test_ndvi_processing_triggers_refresh()
    
    # Test 2: Satellite overlay API works
    print("\n🧪 Test 2: Satellite overlay API")
    test2_passed = test_satellite_overlay_api()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Results Summary:")
    print(f"   Test 1 (NDVI refresh flags): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Test 2 (Satellite overlay API): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Satellite gallery refresh should work correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
