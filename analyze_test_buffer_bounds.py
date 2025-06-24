#!/usr/bin/env python3
"""
Analyze TIFF bounds for test_fresh_buffer region to verify buffer size optimization
"""

import os
from pathlib import Path
import subprocess
import re

def analyze_region_bounds(region_name):
    """Analyze bounds for a specific region"""
    print(f"\n🔍 Analyzing bounds for region: {region_name}")
    
    # Check for metadata file
    metadata_file = Path(f"output/{region_name}/metadata.txt")
    if not metadata_file.exists():
        print(f"❌ Metadata file not found: {metadata_file}")
        return
        
    # Read requested bounds from metadata
    with open(metadata_file, 'r') as f:
        metadata_content = f.read()
    
    print("📄 Metadata content:")
    print(metadata_content)
    
    # Extract requested bounds
    requested_bounds = {}
    for line in metadata_content.split('\n'):
        if line.startswith('North Bound:'):
            requested_bounds['north'] = float(line.split(':')[1].strip())
        elif line.startswith('South Bound:'):
            requested_bounds['south'] = float(line.split(':')[1].strip())
        elif line.startswith('East Bound:'):
            requested_bounds['east'] = float(line.split(':')[1].strip())
        elif line.startswith('West Bound:'):
            requested_bounds['west'] = float(line.split(':')[1].strip())
        elif line.startswith('Buffer Distance (km):'):
            buffer_km = float(line.split(':')[1].strip())
    
    # Calculate requested area
    req_width_deg = requested_bounds['east'] - requested_bounds['west']
    req_height_deg = requested_bounds['north'] - requested_bounds['south']
    req_width_km = req_width_deg * 111.0
    req_height_km = req_height_deg * 111.0
    req_area_km2 = req_width_km * req_height_km
    
    print(f"\n📐 REQUESTED BOUNDS:")
    print(f"   Buffer: {buffer_km}km")
    print(f"   Bounds: {requested_bounds}")
    print(f"   Size: {req_width_km:.1f}km × {req_height_km:.1f}km = {req_area_km2:.0f} km²")
    
    # Find TIFF files
    tiff_files = []
    for tiff_path in Path(f"output/{region_name}").rglob("*.tif"):
        tiff_files.append(tiff_path)
    
    if not tiff_files:
        print(f"❌ No TIFF files found in output/{region_name}")
        return
    
    print(f"\n🗂️ Found {len(tiff_files)} TIFF file(s):")
    
    for tiff_path in tiff_files:
        print(f"\n📊 Analyzing: {tiff_path}")
        
        # Get TIFF info using gdalinfo
        try:
            result = subprocess.run(['gdalinfo', str(tiff_path)], 
                                  capture_output=True, text=True, check=True)
            gdalinfo_output = result.stdout
            
            # Extract actual bounds from gdalinfo
            actual_bounds = {}
            
            # Look for coordinate bounds
            for line in gdalinfo_output.split('\n'):
                if 'Upper Left' in line:
                    # Extract coordinates from "Upper Left  (  -50.1126127,   -1.6973874)"
                    coords = re.search(r'\(\s*([-\d.]+),\s*([-\d.]+)\)', line)
                    if coords:
                        actual_bounds['west'] = float(coords.group(1))
                        actual_bounds['north'] = float(coords.group(2))
                        
                elif 'Lower Right' in line:
                    # Extract coordinates from "Lower Right (  -49.8873873,   -1.9226126)"
                    coords = re.search(r'\(\s*([-\d.]+),\s*([-\d.]+)\)', line)
                    if coords:
                        actual_bounds['east'] = float(coords.group(1))
                        actual_bounds['south'] = float(coords.group(2))
            
            if len(actual_bounds) == 4:
                # Calculate actual area
                act_width_deg = actual_bounds['east'] - actual_bounds['west']
                act_height_deg = actual_bounds['north'] - actual_bounds['south']
                act_width_km = act_width_deg * 111.0
                act_height_km = act_height_deg * 111.0
                act_area_km2 = act_width_km * act_height_km
                
                print(f"   📏 ACTUAL BOUNDS:")
                print(f"      Bounds: {actual_bounds}")
                print(f"      Size: {act_width_km:.1f}km × {act_height_km:.1f}km = {act_area_km2:.0f} km²")
                
                # Compare bounds
                print(f"   🔍 COMPARISON:")
                width_diff = abs(act_width_km - req_width_km)
                height_diff = abs(act_height_km - req_height_km)
                area_diff = abs(act_area_km2 - req_area_km2)
                
                print(f"      Width difference: {width_diff:.1f}km")
                print(f"      Height difference: {height_diff:.1f}km") 
                print(f"      Area difference: {area_diff:.0f} km²")
                
                # Determine if bounds match well
                if width_diff < 5 and height_diff < 5 and area_diff < 100:
                    print(f"   ✅ BOUNDS MATCH WELL - Optimal buffer size working!")
                else:
                    print(f"   ⚠️  BOUNDS MISMATCH - May need investigation")
                    print(f"      Requested: {req_width_km:.1f}km × {req_height_km:.1f}km")
                    print(f"      Received:  {act_width_km:.1f}km × {act_height_km:.1f}km")
                    
            else:
                print(f"   ❌ Could not extract bounds from gdalinfo")
                
        except subprocess.CalledProcessError as e:
            print(f"   ❌ gdalinfo failed: {e}")
        except Exception as e:
            print(f"   ❌ Error analyzing TIFF: {e}")

if __name__ == "__main__":
    analyze_region_bounds("2.01S_54.99W")
