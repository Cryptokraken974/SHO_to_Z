#!/usr/bin/env python3

import requests
import json

def test_dtm_api():
    """Test the DTM API endpoint"""
    url = "http://localhost:8000/api/dtm"
    
    # Test data - using the LAZ file we know exists
    data = {
        "input_file": "input/LAZ/OR_WizardIsland.laz"
    }
    
    print(f"🧪 Testing DTM API endpoint...")
    print(f"📍 URL: {url}")
    print(f"📦 Data: {data}")
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"✅ API call successful!")
            try:
                json_response = response.json()
                print(f"📋 JSON Response keys: {list(json_response.keys())}")
                if 'image' in json_response:
                    print(f"📸 Image data length: {len(json_response['image'])} characters")
                    print(f"📸 Image data preview: {json_response['image'][:100]}...")
            except Exception as e:
                print(f"⚠️ Failed to parse JSON response: {e}")
                print(f"📄 Raw response: {response.text[:500]}...")
        else:
            print(f"❌ API call failed!")
            print(f"📄 Response text: {response.text}")
            
            # Try to parse as JSON error
            try:
                error_data = response.json()
                print(f"📋 Error JSON: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📄 Raw error text: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed - is the server running?")
        print(f"💡 Start the server with: uvicorn app.main:app --reload --port 8000")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_dtm_api()
