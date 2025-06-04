#!/usr/bin/env python3
"""
Debug API Test - Simple test to verify API connectivity
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_api_simple():
    """Simple API test"""
    api_key = os.getenv('OPENTOPOGRAPHY_API_KEY')
    
    print("🔍 Debug API Test")
    print(f"🔑 API Key available: {bool(api_key)}")
    
    # Test parameters for small area
    params = {
        'demtype': 'COP30',
        'west': -62.72,
        'south': -9.43, 
        'east': -62.62,
        'north': -9.33,
        'outputFormat': 'GTiff'
    }
    
    if api_key:
        params['API_Key'] = api_key
    
    print(f"🌍 Testing region: {params}")
    
    try:
        print("📡 Making API request...")
        url = 'https://portal.opentopography.org/API/globaldem'
        response = requests.get(url, params=params, timeout=60)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📏 Content length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            file_size = len(response.content)
            
            if file_size > 1000:
                # Save test file
                output_dir = Path("Tests/debug_output")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                filepath = output_dir / "debug_test.tif"
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Success! Saved {file_size} bytes to {filepath}")
                return filepath
            else:
                print(f"❌ Response too small: {file_size} bytes")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    test_api_simple()
