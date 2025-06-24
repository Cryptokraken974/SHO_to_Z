#!/usr/bin/env python3
"""
Test to reproduce the region name truncation and buffer size issues
"""

import requests
import json

def test_elevation_api_direct():
    """Test the elevation API directly to see what's happening"""
    print("🧪 Testing Elevation API Directly...")
    
    # Test with explicit region name
    test_data = {
        "lat": -2.01,
        "lng": -54.99,
        "region_name": "TEST_FULL_NAME_2.01S_54.99W"
    }
    
    print(f"📋 Request data: {test_data}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/elevation/download-coordinates",
            json=test_data,
            timeout=60
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2)}")
            
            # Check what folder was actually created
            import os
            output_dirs = [d for d in os.listdir("output") if "TEST_" in d]
            print(f"📁 Created folders: {output_dirs}")
            
            # Check metadata content
            for folder in output_dirs:
                metadata_path = f"output/{folder}/metadata.txt"
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        content = f.read()
                    print(f"\n📄 Metadata for {folder}:")
                    print(content)
                    
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_elevation_api_direct()
