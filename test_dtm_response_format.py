#!/usr/bin/env python3

import requests
import json

def test_dtm_response_format():
    """Test the actual DTM API response format"""
    base_url = "http://localhost:8000/api/dtm"
    
    test_data = {
        "region_name": "LAZ",
        "processing_type": "dtm"
    }
    
    print(f"🎯 Testing DTM API response format:")
    print(f"📦 Data: {test_data}")
    
    try:
        response = requests.post(base_url, data=test_data, timeout=30)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request successful!")
            response_data = response.json()
            print(f"📄 Response keys: {list(response_data.keys())}")
            print(f"📄 Response structure: {json.dumps({k: str(type(v)) for k, v in response_data.items()}, indent=2)}")
            if "image" in response_data:
                print(f"🖼️ Image data length: {len(response_data['image'])} characters")
            
            # Check what the frontend is expecting
            print(f"\n🔍 Frontend expectations:")
            print(f"- Checking for 'success' field: {'success' in response_data}")
            print(f"- Has 'image' field: {'image' in response_data}")
            print(f"- Has 'error' field: {'error' in response_data}")
        else:
            print(f"❌ Request failed")
            try:
                error_data = response.json()
                print(f"📄 Error response: {error_data}")
            except:
                print(f"📄 Raw response: {response.text}")
                
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - is the server running?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_dtm_response_format()
