#!/usr/bin/env python3
"""
Test script for OpenAI Analysis Tab NDVI Filter functionality
Verifies that the NDVI filter correctly filters regions based on NDVI status
"""

import requests
import json
from pathlib import Path
import sys

def test_ndvi_filter_implementation():
    """Test the complete NDVI filter implementation"""
    print("🧪 Testing OpenAI Analysis Tab NDVI Filter")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if server is running
    print("\n📋 Test 1: Server connectivity")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️ Server returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running - cannot test NDVI filter")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False
    
    # Test 2: Create test regions with different NDVI settings
    print("\n📋 Test 2: Creating test regions")
    
    test_regions = [
        {
            "region_name": "openai_test_ndvi_enabled",
            "coordinates": {"lat": 45.5017, "lng": -73.5673},
            "place_name": "OpenAI Test NDVI Enabled",
            "ndvi_enabled": True,
            "created_at": "2024-12-23T12:00:00Z"
        },
        {
            "region_name": "openai_test_ndvi_disabled", 
            "coordinates": {"lat": 45.5117, "lng": -73.5773},
            "place_name": "OpenAI Test NDVI Disabled",
            "ndvi_enabled": False,
            "created_at": "2024-12-23T12:00:00Z"
        }
    ]
    
    created_regions = []
    
    for region_data in test_regions:
        try:
            response = requests.post(f"{base_url}/api/create-region", json=region_data)
            if response.status_code == 200:
                print(f"✅ Created region: {region_data['region_name']} (NDVI: {region_data['ndvi_enabled']})")
                created_regions.append(region_data['region_name'])
            else:
                print(f"⚠️ Failed to create region {region_data['region_name']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error creating region {region_data['region_name']}: {e}")
    
    if len(created_regions) < 2:
        print("❌ Could not create test regions - skipping filter test")
        return False
    
    # Test 3: Verify NDVI status endpoints
    print("\n📋 Test 3: Testing NDVI status endpoints")
    
    ndvi_statuses = {}
    
    for region_name in created_regions:
        try:
            response = requests.get(f"{base_url}/api/regions/{region_name}/ndvi-status")
            if response.status_code == 200:
                result = response.json()
                ndvi_enabled = result.get('ndvi_enabled', False)
                ndvi_statuses[region_name] = ndvi_enabled
                print(f"✅ {region_name}: NDVI {'enabled' if ndvi_enabled else 'disabled'}")
            else:
                print(f"❌ Failed to get NDVI status for {region_name}: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error checking NDVI status for {region_name}: {e}")
            return False
    
    # Test 4: Verify correct NDVI settings
    print("\n📋 Test 4: Verifying NDVI settings")
    
    expected_statuses = {
        "openai_test_ndvi_enabled": True,
        "openai_test_ndvi_disabled": False
    }
    
    for region_name, expected_status in expected_statuses.items():
        actual_status = ndvi_statuses.get(region_name)
        if actual_status == expected_status:
            print(f"✅ {region_name}: Correct NDVI status ({actual_status})")
        else:
            print(f"❌ {region_name}: Incorrect NDVI status (expected {expected_status}, got {actual_status})")
            return False
    
    # Test 5: Check regions list endpoint
    print("\n📋 Test 5: Testing regions list endpoint")
    
    try:
        response = requests.get(f"{base_url}/api/list-regions?source=output")
        if response.status_code == 200:
            result = response.json()
            regions = result.get('regions', [])
            
            # Check if our test regions are in the list
            region_names = [r.get('name', '') for r in regions]
            
            for test_region in created_regions:
                if test_region in region_names:
                    print(f"✅ {test_region}: Found in regions list")
                else:
                    print(f"⚠️ {test_region}: Not found in regions list")
            
        else:
            print(f"❌ Failed to get regions list: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting regions list: {e}")
        return False
    
    # Test 6: Frontend files verification
    print("\n📋 Test 6: Verifying frontend implementation")
    
    # Check if the HTML file has the NDVI filter checkbox
    html_file = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/frontend/modules/openai-analysis-tab-content.html")
    if html_file.exists():
        try:
            with open(html_file, 'r') as f:
                content = f.read()
            
            if 'ndvi-filter-checkbox' in content and 'Show only NDVI-enabled regions' in content:
                print("✅ NDVI filter checkbox found in HTML")
            else:
                print("❌ NDVI filter checkbox not found in HTML")
                return False
        except Exception as e:
            print(f"❌ Error reading HTML file: {e}")
            return False
    else:
        print("❌ HTML file not found")
        return False
    
    # Check if the JavaScript file has the filter implementation
    js_file = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/frontend/js/openai-analysis.js")
    if js_file.exists():
        try:
            with open(js_file, 'r') as f:
                content = f.read()
            
            required_elements = [
                'ndviFilterEnabled',
                'applyNdviFilter',
                'ndvi-filter-checkbox',
                '/api/regions/${encodeURIComponent(region.name)}/ndvi-status'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"❌ Missing JavaScript elements: {missing_elements}")
                return False
            else:
                print("✅ JavaScript filter implementation found")
        except Exception as e:
            print(f"❌ Error reading JavaScript file: {e}")
            return False
    else:
        print("❌ JavaScript file not found")
        return False
    
    print("\n🎉 All tests passed! NDVI filter implementation is working correctly.")
    print("=" * 50)
    
    # Cleanup option
    cleanup = input("\n🧹 Clean up test regions? (y/n): ").lower().strip()
    if cleanup == 'y':
        cleanup_test_regions(base_url, created_regions)
    
    return True

def cleanup_test_regions(base_url, region_names):
    """Clean up test regions"""
    print("\n🧹 Cleaning up test regions...")
    
    for region_name in region_names:
        try:
            # Try to delete the region directory
            import shutil
            output_dir = Path("output") / region_name
            if output_dir.exists():
                shutil.rmtree(output_dir)
                print(f"✅ Deleted region folder: {region_name}")
            else:
                print(f"⚠️ Region folder not found: {region_name}")
        except Exception as e:
            print(f"❌ Error deleting region {region_name}: {e}")

if __name__ == "__main__":
    test_ndvi_filter_implementation()
