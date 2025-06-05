#!/usr/bin/env python3

import requests
import json

def test_frontend_dtm_case():
    """Test the exact DTM case from frontend that's failing"""
    base_url = "http://localhost:8000/api/dtm"
    
    # The parameters that the frontend is sending based on conversation summary
    test_data = {
        "region_name": "LAZ",
        "processing_type": "dtm",
        "resolution": "1",
        "output_type": "min"
    }
    
    print(f"🎯 Testing frontend DTM case:")
    print(f"📦 Data: {test_data}")
    
    try:
        response = requests.post(base_url, data=test_data, timeout=30)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request successful!")
            response_data = response.json()
            if "image" in response_data:
                print(f"🖼️ Image data length: {len(response_data['image'])} characters")
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
    test_frontend_dtm_case()
