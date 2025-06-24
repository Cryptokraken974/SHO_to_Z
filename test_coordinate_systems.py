#!/usr/bin/env python3
"""
Test script to compare coordinate systems between different regions
and understand why OR_WizardIsland overlays work correctly.
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from geo_utils import get_laz_overlay_data

def compare_regions():
    """Compare overlay bounds between different regions"""
    
    regions_to_test = [
        "PRGL1260C9597_2014", 
        "OR_WizardIsland_1"
    ]
    
    print(f"🔍 Comparing PNG Overlay Coordinate Systems")
    print("=" * 60)
    
    for region_name in regions_to_test:
        print(f"\n📊 Region: {region_name}")
        print("-" * 40)
        
        # Read metadata
        metadata_path = f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/{region_name}/metadata.txt"
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                content = f.read()
                
            # Extract key information
            lines = content.split('\n')
            for line in lines:
                if 'Center Latitude:' in line:
                    center_lat = float(line.split(':')[1].strip())
                elif 'Center Longitude:' in line:
                    center_lng = float(line.split(':')[1].strip())
                elif 'Source CRS:' in line:
                    source_crs = line.split(':', 1)[1].strip()
                elif 'Native Bounds:' in line:
                    native_bounds = line.split(':', 1)[1].strip()
            
            print(f"📍 Center: ({center_lat:.6f}, {center_lng:.6f})")
            
            # Identify coordinate system
            if "UTM" in source_crs:
                crs_type = "UTM (meters)"
            elif "Lambert" in source_crs:
                crs_type = "Lambert (feet)"
            else:
                crs_type = "Unknown"
            print(f"🗺️  Coordinate System: {crs_type}")
            
            # Check world file
            world_file_path = f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/{region_name}/lidar/png_outputs/CHM.wld"
            if os.path.exists(world_file_path):
                with open(world_file_path, 'r') as f:
                    world_lines = f.read().strip().split('\n')
                if len(world_lines) >= 6:
                    upper_left_x = float(world_lines[4])
                    upper_left_y = float(world_lines[5])
                    print(f"🌍 World file coords: ({upper_left_x:.1f}, {upper_left_y:.1f})")
                    
                    # Check magnitude to identify coordinate system
                    if abs(upper_left_x) > 100000:
                        print(f"   📐 Large coordinates - projected system")
                    else:
                        print(f"   📐 Small coordinates - geographic system")
            
            # Test overlay data extraction
            print(f"🧪 Testing CHM overlay extraction...")
            overlay_data = get_laz_overlay_data(region_name, "CHM")
            
            if overlay_data and 'bounds' in overlay_data:
                bounds = overlay_data['bounds']
                width_deg = abs(bounds['east'] - bounds['west'])
                height_deg = abs(bounds['north'] - bounds['south'])
                width_km = width_deg * 111
                height_km = height_deg * 111
                
                print(f"✅ Overlay bounds extracted:")
                print(f"   📏 Size: {width_deg:.6f}° × {height_deg:.6f}°")
                print(f"   📐 Approx: {width_km:.2f}km × {height_km:.2f}km")
                print(f"   🎯 Source: {bounds.get('source', 'unknown')}")
                
                # Check if bounds are reasonable
                if width_km > 0.5 and height_km > 0.5:
                    print(f"   ✅ Realistic size for LiDAR tile")
                else:
                    print(f"   ⚠️  Small size - check coordinate handling")
            else:
                print(f"❌ No overlay data extracted")
        else:
            print(f"❌ No metadata found")

def check_world_file_usage():
    """Check how world files are used in overlay bounds calculation"""
    
    print(f"\n🌍 World File Usage Analysis:")
    print("=" * 50)
    
    # Check if the system actually uses world files for bounds calculation
    # by temporarily removing metadata.txt and seeing what happens
    
    region_name = "OR_WizardIsland_1"
    metadata_path = f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/{region_name}/metadata.txt"
    backup_path = f"{metadata_path}.backup"
    
    print(f"📄 Testing world file fallback for {region_name}")
    
    # Backup metadata
    if os.path.exists(metadata_path):
        os.rename(metadata_path, backup_path)
        print(f"✅ Backed up metadata.txt")
        
        # Test overlay extraction without metadata
        print(f"🧪 Testing overlay extraction without metadata.txt...")
        overlay_data = get_laz_overlay_data(region_name, "CHM")
        
        if overlay_data and 'bounds' in overlay_data:
            bounds = overlay_data['bounds']
            print(f"✅ Bounds extracted from alternative source:")
            print(f"   📏 Bounds: {bounds}")
            print(f"   🎯 Source: {bounds.get('source', 'unknown')}")
        else:
            print(f"❌ No bounds extracted without metadata")
        
        # Restore metadata
        os.rename(backup_path, metadata_path)
        print(f"✅ Restored metadata.txt")
    else:
        print(f"❌ No metadata.txt found for {region_name}")

if __name__ == "__main__":
    compare_regions()
    check_world_file_usage()
    
    print(f"\n🎯 Analysis Summary:")
    print("=" * 40)
    print("📍 Different regions use different coordinate systems:")
    print("   - PRGL: UTM Zone 18S (meters)")  
    print("   - OR_WizardIsland: NAD83 Oregon Lambert (feet)")
    print("🌍 World files contain native projection coordinates")
    print("📄 System prioritizes metadata.txt bounds (WGS84)")
    print("💡 This explains why overlays work despite world file coordinates")
