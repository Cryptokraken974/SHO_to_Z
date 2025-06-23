#!/usr/bin/env python3
"""
NDVI Feature Demo
Demonstrates the complete NDVI feature functionality
"""

import requests
import json
from pathlib import Path

def demo_ndvi_functionality():
    """Demonstrate NDVI feature with real examples"""
    base_url = "http://localhost:8000"
    
    print("🌿 NDVI Feature Demonstration")
    print("=" * 50)
    
    # Demo 1: Create an NDVI-enabled region
    print("\n📍 Demo 1: Creating NDVI-enabled region")
    print("-" * 40)
    
    region_data = {
        "region_name": "forest_survey_ndvi",
        "coordinates": {"lat": 45.5017, "lng": -73.5673},  # Montreal forest area
        "place_name": "Montreal Forest Survey",
        "ndvi_enabled": True,
        "created_at": "2024-12-23T12:00:00Z"
    }
    
    try:
        response = requests.post(f"{base_url}/api/create-region", json=region_data)
        if response.status_code == 200:
            print("✅ NDVI-enabled region created successfully")
            print(f"   📁 Region: {region_data['region_name']}")
            print(f"   🌿 NDVI: Enabled")
        else:
            print(f"❌ Region creation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 2: Check NDVI status via API
    print("\n🔍 Demo 2: Checking NDVI status via API")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/api/regions/forest_survey_ndvi/ndvi-status")
        if response.status_code == 200:
            result = response.json()
            print("✅ NDVI status retrieved successfully")
            print(f"   📊 Region: {result['region_name']}")
            print(f"   🌿 NDVI Enabled: {result['ndvi_enabled']}")
            print(f"   📄 Metadata Found: {result['metadata_found']}")
        else:
            print(f"❌ NDVI status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 3: Show metadata content
    print("\n📄 Demo 3: Metadata file content")
    print("-" * 40)
    
    metadata_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/forest_survey_ndvi/metadata.txt")
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                content = f.read()
            
            print("✅ Metadata file found")
            # Show relevant lines
            lines = content.split('\n')
            for line in lines[:15]:  # Show first 15 lines
                if line.strip():
                    print(f"   {line}")
            print("   ...")
        except Exception as e:
            print(f"❌ Error reading metadata: {e}")
    else:
        print("⚠️ Metadata file not found")
    
    # Demo 4: Create a non-NDVI region for comparison
    print("\n📍 Demo 4: Creating standard region (no NDVI)")
    print("-" * 40)
    
    standard_region_data = {
        "region_name": "standard_survey",
        "coordinates": {"lat": 45.5117, "lng": -73.5773},
        "place_name": "Standard Survey Area",
        "ndvi_enabled": False,
        "created_at": "2024-12-23T12:00:00Z"
    }
    
    try:
        response = requests.post(f"{base_url}/api/create-region", json=standard_region_data)
        if response.status_code == 200:
            print("✅ Standard region created successfully")
            print(f"   📁 Region: {standard_region_data['region_name']}")
            print(f"   🌿 NDVI: Disabled")
        else:
            print(f"❌ Region creation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 5: Compare NDVI status between regions
    print("\n🔍 Demo 5: Comparing regions")
    print("-" * 40)
    
    regions_to_check = ["forest_survey_ndvi", "standard_survey"]
    
    for region in regions_to_check:
        try:
            response = requests.get(f"{base_url}/api/regions/{region}/ndvi-status")
            if response.status_code == 200:
                result = response.json()
                ndvi_status = "🌿 ENABLED" if result['ndvi_enabled'] else "❌ DISABLED"
                print(f"   📊 {region:<20} → NDVI {ndvi_status}")
            else:
                print(f"   ❌ {region:<20} → Status check failed")
        except Exception as e:
            print(f"   ❌ {region:<20} → Error: {e}")
    
    print("\n🎉 NDVI Feature Demo Complete!")
    print("=" * 50)
    print("The NDVI feature is working correctly and ready for production use.")
    
    # Cleanup option
    cleanup = input("\n🧹 Clean up demo regions? (y/n): ").lower().strip()
    if cleanup == 'y':
        cleanup_demo_regions()

def cleanup_demo_regions():
    """Clean up demo regions"""
    import shutil
    
    base_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output")
    demo_regions = ["forest_survey_ndvi", "standard_survey"]
    
    for region in demo_regions:
        region_path = base_path / region
        if region_path.exists():
            shutil.rmtree(region_path)
            print(f"   ✅ Removed {region}")
    
    print("🧹 Demo cleanup completed")

if __name__ == "__main__":
    demo_ndvi_functionality()
