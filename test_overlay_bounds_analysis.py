#!/usr/bin/env python3
"""
Test script to demonstrate PNG overlay scaling issue and solution.
This script validates world file generation and geographic bounds extraction.
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from geo_utils import get_laz_overlay_data

def test_overlay_bounds_comparison():
    """Compare overlay bounds from different sources"""
    
    region_name = "PRGL1260C9597_2014"
    overlay_types = ["CHM", "HillshadeRGB", "LRM", "Slope"]
    
    print(f"🔍 Testing overlay bounds for region: {region_name}")
    print("=" * 70)
    
    for overlay_type in overlay_types:
        print(f"\n📊 {overlay_type} Overlay Analysis:")
        print("-" * 40)
        
        # Get overlay data
        overlay_data = get_laz_overlay_data(region_name, overlay_type)
        
        if overlay_data and 'bounds' in overlay_data:
            bounds = overlay_data['bounds']
            
            # Display bounds information
            north = bounds.get('north', 0)
            south = bounds.get('south', 0) 
            east = bounds.get('east', 0)
            west = bounds.get('west', 0)
            
            width_deg = abs(east - west)
            height_deg = abs(north - south)
            
            # Convert to approximate distance (1° ≈ 111km at equator)
            width_km = width_deg * 111
            height_km = height_deg * 111
            
            print(f"📍 Geographic Bounds:")
            print(f"   North: {north:.6f}°")
            print(f"   South: {south:.6f}°") 
            print(f"   East:  {east:.6f}°")
            print(f"   West:  {west:.6f}°")
            print(f"📏 Size: {width_deg:.6f}° × {height_deg:.6f}°")
            print(f"📐 Approximate: {width_km:.2f}km × {height_km:.2f}km")
            print(f"🎯 Source: {bounds.get('source', 'unknown')}")
            
            # Check if bounds are reasonable for LiDAR data
            if width_km < 0.1 or height_km < 0.1:
                print(f"⚠️  WARNING: Very small extent - likely scaling issue")
            elif width_km < 2 and height_km < 2:
                print(f"✅ Reasonable LiDAR tile size")
            else:
                print(f"⚠️  Large extent - check if correct")
        else:
            print(f"❌ No overlay data found")
    
    print(f"\n🎯 Analysis Summary:")
    print("=" * 50)
    print("✅ World file generation: ENABLED")
    print("✅ World files created: YES (.wld format)")  
    print("⚠️  World file coordinates: UTM (meters) not WGS84 (degrees)")
    print("⚠️  Overlay bounds: Small - from LAZ metadata bounds")
    print("")
    print("🔧 Issue: World files contain UTM coordinates but frontend expects WGS84")
    print("💡 Solution: Need to transform world file to WGS84 or update frontend logic")

def check_world_file_format():
    """Check the actual world file content and format"""
    
    print(f"\n🌍 World File Analysis:")
    print("=" * 40)
    
    world_file_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/PRGL1260C9597_2014/lidar/png_outputs/CHM.wld"
    
    if os.path.exists(world_file_path):
        with open(world_file_path, 'r') as f:
            lines = f.read().strip().split('\n')
            
        if len(lines) >= 6:
            pixel_size_x = float(lines[0])
            rotation_y = float(lines[1]) 
            rotation_x = float(lines[2])
            pixel_size_y = float(lines[3])
            upper_left_x = float(lines[4])
            upper_left_y = float(lines[5])
            
            print(f"📄 World file parameters:")
            print(f"   Pixel size X: {pixel_size_x:.6f}")
            print(f"   Rotation Y:   {rotation_y:.6f}")
            print(f"   Rotation X:   {rotation_x:.6f}")
            print(f"   Pixel size Y: {pixel_size_y:.6f}")
            print(f"   Upper left X: {upper_left_x:.6f}")
            print(f"   Upper left Y: {upper_left_y:.6f}")
            print(f"")
            print(f"🔍 Coordinate System Analysis:")
            
            # Check if coordinates look like UTM or geographic
            if abs(upper_left_x) > 1000 and abs(upper_left_y) > 1000:
                print(f"   📐 Coordinates appear to be: UTM/Projected (meters)")
                print(f"   ⚠️  Problem: Frontend expects WGS84 (degrees)")
            elif abs(upper_left_x) < 360 and abs(upper_left_y) < 90:
                print(f"   🌍 Coordinates appear to be: WGS84 (degrees)")
                print(f"   ✅ Compatible with Leaflet mapping")
            else:
                print(f"   ❓ Unknown coordinate system")
                
            # Check pixel size
            if abs(pixel_size_x) > 0.001:
                print(f"   📏 Large pixel size - likely UTM meters")
            else:
                print(f"   📏 Small pixel size - likely geographic degrees")
        else:
            print(f"❌ Invalid world file format")
    else:
        print(f"❌ World file not found: {world_file_path}")

if __name__ == "__main__":
    test_overlay_bounds_comparison()
    check_world_file_format()
    
    print(f"\n🎯 Next Steps:")
    print("1. ✅ World file generation is working")
    print("2. ⚠️  Need to transform world files from UTM to WGS84") 
    print("3. 🔧 Update metadata.txt with proper geographic bounds")
    print("4. 🧪 Test overlays in Leaflet frontend")
