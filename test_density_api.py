#!/usr/bin/env python3
"""
Test the density analysis API endpoint with PRGL LAZ file
"""

import requests
import json
import time

def test_density_api():
    """Test the density analysis API endpoint"""
    
    print("🧪 Testing Density Analysis API with PRGL LAZ")
    print("=" * 50)
    
    # API endpoint
    url = "http://localhost:8000/api/density/analyze"
    
    # Request payload for PRGL LAZ file
    payload = {
        "laz_file_path": "input/LAZ/PRGL1260C9597_2014.laz",
        "region_name": "PRGL1260C9597_2014",
        "resolution": 1.0
    }
    
    print(f"🚀 Making API request...")
    print(f"   URL: {url}")
    print(f"   LAZ file: {payload['laz_file_path']}")
    print(f"   Region: {payload['region_name']}")
    print(f"   Resolution: {payload['resolution']}m")
    
    try:
        start_time = time.time()
        
        response = requests.post(url, json=payload, timeout=60)
        
        end_time = time.time()
        api_time = end_time - start_time
        
        print(f"⏱️ API response time: {api_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ API call successful!")
            print(f"\n📋 Response:")
            print(json.dumps(result, indent=2))
            
            if result.get("success"):
                print(f"\n🎯 Analysis Results:")
                if "metadata" in result and "statistics" in result["metadata"]: 
                    stats = result["metadata"]["statistics"]
                    print(f"   Min density: {stats.get('min', 'N/A')} points/cell")
                    print(f"   Max density: {stats.get('max', 'N/A')} points/cell")
                    print(f"   Mean density: {stats.get('mean', 'N/A'):.2f} points/cell")
                
                print(f"\n📁 Generated Files:")
                if "tiff_path" in result:
                    print(f"   TIFF: {result['tiff_path']}")
                if "png_path" in result:
                    print(f"   PNG: {result['png_path']}")
                if "metadata_path" in result:
                    print(f"   Metadata: {result['metadata_path']}")
                
                return True
            else:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Server not running on localhost:8000")
        print(f"   Start the server with: python main.py")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Request timeout: Analysis took longer than 60 seconds")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_density_api()
    
    if success:
        print(f"\n🎉 API test PASSED!")
    else:
        print(f"\n💥 API test FAILED!")
        print(f"Make sure the server is running: python main.py")
