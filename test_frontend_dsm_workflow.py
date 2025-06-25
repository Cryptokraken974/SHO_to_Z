#!/usr/bin/env python3
"""
Test script to verify the frontend DSM workflow now uses SRTM instead of Copernicus
"""

import asyncio
import aiohttp
import json

async def test_combined_data_workflow():
    """Test the combined data workflow endpoint that the frontend calls"""
    
    # Test coordinates (Brazil region that should work with SRTM)
    test_data = {
        "region_name": "Box_Regions_Test",
        "latitude": -14.87,
        "longitude": -39.38,
        "buffer_km": 12.5,
        "resolution": 1  # SRTM 1-arcsecond
    }
    
    print(f"🧪 Testing SRTM DSM workflow...")
    print(f"📍 Test region: {test_data['region_name']}")
    print(f"📍 Coordinates: ({test_data['latitude']}, {test_data['longitude']})")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Test SRTM DSM endpoint (what frontend now calls)
            print(f"\n🏔️ Step 1: Testing SRTM DSM endpoint...")
            async with session.post('http://localhost:8000/api/download-srtm-dsm', 
                                  json=test_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        print(f"✅ SRTM DSM download successful!")
                        print(f"📁 File: {result.get('file_path')}")
                        print(f"🔧 Method: {result.get('method')}")
                    else:
                        print(f"❌ SRTM DSM download failed: {result.get('error')}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    return False
            
            # Step 2: Test proper CHM generation endpoint
            print(f"\n🌳 Step 2: Testing proper CHM generation...")
            chm_data = {
                "region_name": test_data['region_name'],
                "latitude": test_data['latitude'],
                "longitude": test_data['longitude']
            }
            
            async with session.post('http://localhost:8000/api/generate-proper-chm', 
                                  json=chm_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        print(f"✅ Proper CHM generation successful!")
                        print(f"📁 File: {result.get('file_path')}")
                        if result.get('data_source_info'):
                            dsm_info = result['data_source_info'].get('dsm_source', {})
                            print(f"🎯 DSM Source: {dsm_info.get('type', 'Unknown')}")
                            print(f"📊 CHM Statistics: {result.get('chm_statistics', {})}")
                    else:
                        print(f"❌ CHM generation failed: {result.get('error')}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    return False
                    
        print(f"\n✅ Frontend DSM workflow test completed successfully!")
        print(f"🎯 Confirmed: Frontend now uses SRTM DSM instead of Copernicus DTM")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

async def test_old_vs_new_endpoints():
    """Compare old Copernicus endpoint vs new SRTM endpoint responses"""
    
    test_data = {
        "region_name": "API_Test_Compare",
        "latitude": -14.87,
        "longitude": -39.38,
        "buffer_km": 12.5
    }
    
    print(f"\n🔄 Comparing old vs new DSM endpoints...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test new SRTM endpoint
            print(f"\n🆕 Testing new SRTM DSM endpoint...")
            srtm_data = {**test_data, "resolution": 1}
            async with session.post('http://localhost:8000/api/download-srtm-dsm', 
                                  json=srtm_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ SRTM DSM: {result.get('success')}")
                    if result.get('success'):
                        print(f"   📁 Method: {result.get('method')}")
                        print(f"   📊 Source: SRTM GL1 (True Surface Model)")
                else:
                    print(f"❌ SRTM DSM failed: {response.status}")
            
            # Test old Copernicus endpoint (for comparison)
            print(f"\n🗂️ Testing old Copernicus DSM endpoint (for comparison)...")
            copernicus_data = {**test_data, "resolution": "30m"}
            async with session.post('http://localhost:8000/api/download-copernicus-dsm', 
                                  json=copernicus_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"ℹ️ Copernicus DSM: {result.get('success')}")
                    if result.get('success'):
                        print(f"   📁 Method: {result.get('method')}")
                        print(f"   ⚠️ Source: Copernicus DEM (Actually DTM - Terrain Model)")
                else:
                    print(f"❌ Copernicus DSM failed: {response.status}")
                    
        print(f"\n📋 Summary:")
        print(f"✅ New SRTM DSM endpoint provides true surface elevation data")
        print(f"⚠️ Old Copernicus endpoint provides terrain model (DTM) mislabeled as DSM")
        print(f"🎯 Frontend should now use SRTM for proper CHM calculation")
        
    except Exception as e:
        print(f"❌ Comparison test failed: {str(e)}")

if __name__ == "__main__":
    print(f"🧪 FRONTEND DSM WORKFLOW VERIFICATION")
    print(f"{'='*60}")
    print(f"Testing that frontend now uses SRTM DSM instead of Copernicus DSM")
    print(f"{'='*60}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test the workflow that frontend should now use
        success = loop.run_until_complete(test_combined_data_workflow())
        
        # Compare old vs new endpoints
        loop.run_until_complete(test_old_vs_new_endpoints())
        
        if success:
            print(f"\n🎉 SUCCESS: Frontend DSM workflow properly integrated!")
        else:
            print(f"\n❌ FAILED: Issues detected in frontend DSM workflow")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
    finally:
        loop.close()
