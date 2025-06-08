#!/usr/bin/env python3
"""
Test DTM processing request to debug the parameter issue
"""

import requests
import json

def test_dtm_region_based():
    """Test DTM processing with region-based parameters"""
    print("🧪 Testing DTM processing with region-based parameters...")
    
    url = "http://localhost:8000/api/dtm"
    
    # Test data that should work (region-based)
    data = {
        'region_name': 'CUI_A01_10-04',
        'processing_type': 'dtm',
        'display_region_name': 'CUI_A01_10-04'
    }
    
    print(f"📤 Sending request to: {url}")
    print(f"📦 Data: {data}")
    
    try:
        response = requests.post(url, data=data)
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📄 Response keys: {list(result.keys())}")
        else:
            print("❌ Error!")
            print(f"📄 Response text: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

def test_dtm_file_based():
    """Test DTM processing with file-based parameters"""
    print("\n🧪 Testing DTM processing with file-based parameters...")
    
    url = "http://localhost:8000/api/dtm"
    
    # Test data that should work (file-based)
    data = {
        'input_file': 'input/LAZ/CUI_A01_10-04.laz'
    }
    
    print(f"📤 Sending request to: {url}")
    print(f"📦 Data: {data}")
    
    try:
        response = requests.post(url, data=data)
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📄 Response keys: {list(result.keys())}")
        else:
            print("❌ Error!")
            print(f"📄 Response text: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

def test_dtm_empty_request():
    """Test DTM processing with no parameters (should fail with 400)"""
    print("\n🧪 Testing DTM processing with no parameters (should fail)...")
    
    url = "http://localhost:8000/api/dtm"
    
    # Empty data - should trigger the error we're seeing
    data = {}
    
    print(f"📤 Sending request to: {url}")
    print(f"📦 Data: {data}")
    
    try:
        response = requests.post(url, data=data)
        print(f"📥 Response status: {response.status_code}")
        print(f"📄 Response text: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    print("🔬 DTM Processing Request Test")
    print("=" * 50)
    
    test_dtm_region_based()
    test_dtm_file_based() 
    test_dtm_empty_request()
