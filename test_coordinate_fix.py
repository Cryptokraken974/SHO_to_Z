#!/usr/bin/env python3
"""
Test script to verify the coordinate fix for NP_T-0066 DSM overlay
"""
import sys
import os
sys.path.append('app')

from geo_utils import get_image_bounds_from_geotiff
import glob

def test_coordinate_fix():
    print("🧪 Testing coordinate fix for NP_T-0066...")
    
    # Find DSM files for NP_T-0066
    dsm_files = glob.glob('output/NP_T-0066/**/*DSM*.tif', recursive=True)
    
    if not dsm_files:
        print("❌ No DSM files found for NP_T-0066")
        return False
    
    print(f"📁 Found DSM file: {dsm_files[0]}")
    
    # Get bounds using the fixed coordinate logic
    bounds = get_image_bounds_from_geotiff(dsm_files[0])
    
    if not bounds:
        print("❌ Failed to get bounds")
        return False
    
    print(f"\n📊 Extracted Bounds:")
    print(f"  North: {bounds['north']}")
    print(f"  South: {bounds['south']}")
    print(f"  East: {bounds['east']}")
    print(f"  West: {bounds['west']}")
    print(f"  Center Lat: {bounds['center_lat']}")
    print(f"  Center Lng: {bounds['center_lng']}")
    
    # Expected coordinates for Amazon region around Peru-Brazil border
    expected_lat = -8.374269838067747
    expected_lng = -71.57279549806803
    
    print(f"\n🎯 Expected Coordinates (from metadata):")
    print(f"  Center Lat: {expected_lat}")
    print(f"  Center Lng: {expected_lng}")
    
    # Check if coordinates are in the correct region
    lat_diff = abs(bounds['center_lat'] - expected_lat)
    lng_diff = abs(bounds['center_lng'] - expected_lng)
    
    print(f"\n📏 Coordinate Differences:")
    print(f"  Lat difference: {lat_diff}")
    print(f"  Lng difference: {lng_diff}")
    
    # Allow small differences due to coordinate transformation
    if lat_diff < 0.1 and lng_diff < 0.1:
        print("✅ SUCCESS: Coordinates are correct! Overlay should appear in Amazon region.")
        return True
    else:
        print("❌ FAIL: Coordinates are still incorrect.")
        return False

def test_leaflet_bounds_format():
    """Test that the bounds are in the correct format for Leaflet"""
    print("\n🗺️  Testing Leaflet bounds format...")
    
    dsm_files = glob.glob('output/NP_T-0066/**/*DSM*.tif', recursive=True)
    if not dsm_files:
        return False
        
    bounds = get_image_bounds_from_geotiff(dsm_files[0])
    if not bounds:
        return False
    
    # Leaflet expects bounds as [[south, west], [north, east]]
    leaflet_bounds = [[bounds['south'], bounds['west']], [bounds['north'], bounds['east']]]
    
    print(f"🍃 Leaflet bounds format: {leaflet_bounds}")
    
    # Check that south < north and west < east (or west > east for longitude wrap)
    if bounds['south'] < bounds['north']:
        print("✅ South < North (correct)")
    else:
        print("❌ South >= North (incorrect)")
        
    if bounds['west'] < bounds['east']:
        print("✅ West < East (correct)")
    else:
        print("❌ West >= East (incorrect)")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 COORDINATE FIX VERIFICATION")
    print("=" * 60)
    
    success = test_coordinate_fix()
    test_leaflet_bounds_format()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 COORDINATE FIX SUCCESSFUL!")
        print("The DSM overlay for NP_T-0066 should now appear in the Amazon region")
        print("instead of Antarctica.")
    else:
        print("❌ COORDINATE FIX FAILED!")
        print("The overlay is still showing incorrect coordinates.")
    print("=" * 60)
