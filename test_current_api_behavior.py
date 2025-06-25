#!/usr/bin/env python3
"""
Test script to verify what the current API is actually doing
"""

import asyncio
import aiohttp
import json

async def test_current_api():
    """Test what the current API endpoints are actually returning"""
    print("🧪 Testing Current API Behavior")
    print("="*50)
    
    # Test data for Box_Regions_8 coordinates
    test_data = {
        "region_name": "Box_Regions_8",
        "latitude": -14.87,
        "longitude": -39.38,
        "buffer_km": 12.5,
        "resolution": 1  # SRTM resolution
    }
    
    async with aiohttp.ClientSession() as session:
        print(f"\n📍 Testing with coordinates: ({test_data['latitude']}, {test_data['longitude']})")
        
        # Test 1: Check if old Copernicus DSM endpoint still works
        print(f"\n1️⃣ Testing OLD Copernicus DSM endpoint...")
        try:
            old_copernicus_data = {
                "region_name": test_data["region_name"],
                "latitude": test_data["latitude"],
                "longitude": test_data["longitude"],
                "buffer_km": test_data["buffer_km"],
                "resolution": "30m"
            }
            
            async with session.post(
                'http://localhost:8000/api/download-copernicus-dsm',
                json=old_copernicus_data
            ) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"   Success: {result.get('success')}")
                    print(f"   Message: {result.get('message', '')}")
                else:
                    print(f"   Failed: {response.status}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: Check new SRTM DSM endpoint
        print(f"\n2️⃣ Testing NEW SRTM DSM endpoint...")
        try:
            async with session.post(
                'http://localhost:8000/api/download-srtm-dsm',
                json=test_data
            ) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"   Success: {result.get('success')}")
                    print(f"   Message: {result.get('message', '')}")
                else:
                    print(f"   Failed: {response.status}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 3: Check CHM generation endpoint
        print(f"\n3️⃣ Testing CHM generation endpoint...")
        try:
            chm_data = {
                "region_name": test_data["region_name"],
                "latitude": test_data["latitude"],
                "longitude": test_data["longitude"]
            }
            
            async with session.post(
                'http://localhost:8000/api/generate-proper-chm',
                json=chm_data
            ) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"   Success: {result.get('success')}")
                    print(f"   Message: {result.get('message', '')}")
                else:
                    print(f"   Failed: {response.status}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print(f"\n✅ API behavior test completed")

if __name__ == "__main__":
    asyncio.run(test_current_api())
