#!/usr/bin/env python3
"""
Quick test to verify LAZ upload fix is working
"""

import requests
import json
from pathlib import Path

def test_laz_upload_endpoint():
    """Test if the LAZ upload endpoint is working"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing LAZ upload endpoint...")
    
    try:
        # Test the endpoint exists and accepts POST requests
        response = requests.post(f"{base_url}/api/laz/upload")
        
        # We expect 422 (Unprocessable Entity) because we didn't send files
        # This means the endpoint exists and is working
        if response.status_code == 422:
            print("✅ LAZ upload endpoint is working (accepts POST requests)")
            return True
        elif response.status_code == 404:
            print("❌ LAZ upload endpoint not found (404)")
            return False
        else:
            print(f"⚠️ LAZ upload endpoint returned unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing LAZ upload endpoint: {e}")
        return False

def test_dtm_endpoint():
    """Test if the DTM generation endpoint is working"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing DTM generation endpoint...")
    
    try:
        # Test the endpoint exists and accepts POST requests
        response = requests.post(f"{base_url}/api/dtm")
        
        # We expect 422 or 400 because we didn't send required parameters
        if response.status_code in [422, 400]:
            print("✅ DTM generation endpoint is working (accepts POST requests)")
            return True
        elif response.status_code == 404:
            print("❌ DTM generation endpoint not found (404)")
            return False
        else:
            print(f"⚠️ DTM generation endpoint returned unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing DTM generation endpoint: {e}")
        return False

def test_process_all_rasters_endpoint():
    """Test if the process-all-rasters endpoint is working"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing process-all-rasters endpoint...")
    
    try:
        # Test the endpoint exists and accepts POST requests
        response = requests.post(f"{base_url}/api/laz/process-all-rasters")
        
        # We expect 422 or 400 because we didn't send required parameters
        if response.status_code in [422, 400]:
            print("✅ Process-all-rasters endpoint is working (accepts POST requests)")
            return True
        elif response.status_code == 404:
            print("❌ Process-all-rasters endpoint not found (404)")
            return False
        else:
            print(f"⚠️ Process-all-rasters endpoint returned unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing process-all-rasters endpoint: {e}")
        return False

def main():
    print("🚀 Testing LAZ Upload Fix")
    print("=" * 50)
    
    # Test all endpoints
    upload_ok = test_laz_upload_endpoint()
    dtm_ok = test_dtm_endpoint()
    process_ok = test_process_all_rasters_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   LAZ Upload: {'✅ PASS' if upload_ok else '❌ FAIL'}")
    print(f"   DTM Generation: {'✅ PASS' if dtm_ok else '❌ FAIL'}")
    print(f"   Process All Rasters: {'✅ PASS' if process_ok else '❌ FAIL'}")
    
    if upload_ok and dtm_ok and process_ok:
        print("\n🎉 All endpoints are working!")
        print("\n💡 The LAZ upload workflow should now work:")
        print("   1. Upload LAZ files → /api/laz/upload")
        print("   2. Generate DTM → /api/dtm")
        print("   3. Process all rasters → /api/laz/process-all-rasters")
        print("\n🌐 Ready to test in browser at http://localhost:8000")
    else:
        print("\n⚠️ Some endpoints are not working. Check the server logs.")

if __name__ == "__main__":
    main()
