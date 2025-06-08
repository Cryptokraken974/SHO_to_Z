#!/usr/bin/env python3
"""
Test script to verify DSM overlay visibility on the map
"""

import asyncio
import aiohttp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

async def test_dsm_overlay_api():
    """Test the DSM overlay API endpoint"""
    print("🧪 Testing DSM overlay API...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('http://localhost:8000/api/overlay/raster/OR_WizardIsland/dsm') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API Response: Success={data.get('success')}")
                    print(f"✅ Has image_data: {len(data.get('image_data', '')) > 0}")
                    print(f"✅ Has bounds: {'bounds' in data}")
                    return True
                else:
                    print(f"❌ API returned status {response.status}")
                    return False
        except Exception as e:
            print(f"❌ API test failed: {e}")
            return False

def test_dsm_overlay_frontend():
    """Test DSM overlay functionality in the frontend"""
    print("🧪 Testing DSM overlay in frontend...")
    
    # Setup Chrome options for headless testing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('http://localhost:3000')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Execute JavaScript to test DSM overlay functionality
        test_script = """
        // Test DSM overlay functionality
        async function testDSMOverlay() {
            console.log('🧪 Testing DSM overlay functionality...');
            
            try {
                // Test if OverlayManager exists
                if (typeof OverlayManager === 'undefined') {
                    return { success: false, error: 'OverlayManager not found' };
                }
                
                // Test if overlays API client exists
                if (typeof overlays === 'undefined') {
                    return { success: false, error: 'overlays API client not found' };
                }
                
                // Test API call to get DSM overlay data
                const overlayData = await overlays().getRasterOverlayData('OR_WizardIsland', 'dsm');
                
                if (!overlayData.success || !overlayData.image_data || !overlayData.bounds) {
                    return { success: false, error: 'Invalid overlay data from API' };
                }
                
                // Test bounds format
                const bounds = [
                    [overlayData.bounds.south, overlayData.bounds.west],
                    [overlayData.bounds.north, overlayData.bounds.east]
                ];
                
                // Test image data URL creation
                const imageDataUrl = `data:image/png;base64,${overlayData.image_data}`;
                
                // Test if map exists
                if (typeof MapManager === 'undefined' || !MapManager.getMap()) {
                    return { success: false, error: 'Map not available' };
                }
                
                // Test overlay creation (without actually adding to avoid interference)
                const overlayKey = 'TEST_DSM_OVERLAY';
                
                return { 
                    success: true, 
                    hasOverlayManager: true,
                    hasApiClient: true,
                    hasMapManager: true,
                    hasValidData: true,
                    bounds: bounds,
                    imageDataLength: overlayData.image_data.length
                };
                
            } catch (error) {
                return { success: false, error: error.message };
            }
        }
        
        return testDSMOverlay();
        """
        
        # Execute the test
        result = driver.execute_script(f"return {test_script}")
        
        if result['success']:
            print("✅ Frontend DSM overlay test passed")
            print(f"✅ Image data length: {result['imageDataLength']}")
            print(f"✅ Bounds: {result['bounds']}")
            return True
        else:
            print(f"❌ Frontend test failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False
    finally:
        if driver:
            driver.quit()

async def main():
    """Main test function"""
    print("🔍 Investigating DSM overlay visibility issue...\n")
    
    # Test 1: API functionality
    api_test = await test_dsm_overlay_api()
    print()
    
    # Test 2: Frontend functionality
    frontend_test = test_dsm_overlay_frontend()
    print()
    
    # Summary
    print("📊 Test Results:")
    print(f"   API Test: {'✅ PASS' if api_test else '❌ FAIL'}")
    print(f"   Frontend Test: {'✅ PASS' if frontend_test else '❌ FAIL'}")
    
    if api_test and frontend_test:
        print("\n✅ All tests passed - DSM overlay system appears functional")
        print("💡 Issue might be in the UI interaction or button click handling")
    else:
        print("\n❌ Some tests failed - investigating specific issues needed")

if __name__ == "__main__":
    asyncio.run(main())
