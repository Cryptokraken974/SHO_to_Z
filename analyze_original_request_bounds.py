#!/usr/bin/env python3
"""
Analyze the original LAZ request bounds vs what we see in world files.
This should reveal the true discrepancy between what was requested and what we get.
"""

import os
import sys
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from geo_utils import get_laz_overlay_data

def analyze_original_vs_world_bounds():
    """Compare original LAZ request bounds with world file bounds"""
    
    regions_to_test = [
        "PRGL1260C9597_2014", 
        "OR_WizardIsland_1"
    ]
    
    print(f"🔍 ANALYZING ORIGINAL REQUEST BOUNDS vs WORLD FILE BOUNDS")
    print("=" * 80)
    
    for region_name in regions_to_test:
        print(f"\n📊 Region: {region_name}")
        print("-" * 50)
        
        # 1. Check for original download metadata/logs
        region_dir = f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/{region_name}"
        
        # Look for original request information
        request_info_sources = [
            f"{region_dir}/download_metadata.json",
            f"{region_dir}/opentopography_request.json", 
            f"{region_dir}/acquisition_log.txt",
            f"{region_dir}/request_bounds.txt",
            f"{region_dir}/metadata.txt"
        ]
        
        original_bounds = None
        original_area_km2 = None
        
        # Search for original request bounds
        for source_file in request_info_sources:
            if os.path.exists(source_file):
                print(f"📄 Found: {os.path.basename(source_file)}")
                
                with open(source_file, 'r') as f:
                    content = f.read()
                
                # Look for bounds information
                if 'bbox' in content.lower() or 'bound' in content.lower():
                    print(f"   📍 Contains bounds information")
                    
                    # Extract bounds from metadata.txt
                    if source_file.endswith('metadata.txt'):
                        lines = content.split('\n')
                        bounds_data = {}
                        for line in lines:
                            if 'North Bound:' in line:
                                bounds_data['north'] = float(line.split(':')[1].strip())
                            elif 'South Bound:' in line:
                                bounds_data['south'] = float(line.split(':')[1].strip())
                            elif 'East Bound:' in line:
                                bounds_data['east'] = float(line.split(':')[1].strip())
                            elif 'West Bound:' in line:
                                bounds_data['west'] = float(line.split(':')[1].strip())
                        
                        if len(bounds_data) == 4:
                            original_bounds = bounds_data
                            width_deg = abs(bounds_data['east'] - bounds_data['west'])
                            height_deg = abs(bounds_data['north'] - bounds_data['south'])
                            original_area_km2 = (width_deg * 111) * (height_deg * 111)
                            
                            print(f"   ✅ Extracted original bounds:")
                            print(f"      N: {bounds_data['north']:.6f}°")
                            print(f"      S: {bounds_data['south']:.6f}°") 
                            print(f"      E: {bounds_data['east']:.6f}°")
                            print(f"      W: {bounds_data['west']:.6f}°")
                            print(f"      📏 Area: {width_deg:.6f}° × {height_deg:.6f}° ({original_area_km2:.2f} km²)")
                
                # Look for comments with bounds info
                if '# Bounds:' in content:
                    bounds_line = [line for line in content.split('\n') if '# Bounds:' in line]
                    if bounds_line:
                        print(f"   📍 Request bounds comment: {bounds_line[0]}")
        
        # 2. Check world file bounds
        world_file_path = f"{region_dir}/lidar/png_outputs/CHM.wld"
        if os.path.exists(world_file_path):
            print(f"\n🌍 World file analysis:")
            
            with open(world_file_path, 'r') as f:
                world_lines = f.read().strip().split('\n')
            
            if len(world_lines) >= 6:
                pixel_x = float(world_lines[0])
                pixel_y = float(world_lines[3])
                upper_left_x = float(world_lines[4])
                upper_left_y = float(world_lines[5])
                
                print(f"   📐 Pixel size: {pixel_x} × {pixel_y}")
                print(f"   📍 Upper left: ({upper_left_x}, {upper_left_y})")
                
                # Estimate image size (we need to check PNG dimensions)
                png_path = f"{region_dir}/lidar/png_outputs/CHM.png"
                if os.path.exists(png_path):
                    from PIL import Image
                    with Image.open(png_path) as img:
                        width_px, height_px = img.size
                    
                    # Calculate world file coverage
                    world_width = abs(pixel_x * width_px)
                    world_height = abs(pixel_y * height_px)
                    
                    print(f"   📏 PNG dimensions: {width_px} × {height_px} pixels")
                    print(f"   📐 World file coverage: {world_width} × {world_height} (in projection units)")
                    
                    # Check if coordinates look like projected system
                    if abs(upper_left_x) > 100000 or abs(upper_left_y) > 100000:
                        print(f"   🗺️  Coordinates appear to be in projected system")
                        # Try to convert to approximate area
                        if abs(pixel_x) < 10:  # If pixel size is small, likely meters or feet
                            if abs(pixel_x) > 0.1:  # Probably feet
                                world_width_m = world_width * 0.3048  # feet to meters
                                world_height_m = world_height * 0.3048
                                world_area_km2 = (world_width_m / 1000) * (world_height_m / 1000)
                                print(f"   📏 Estimated area (feet→m): {world_area_km2:.4f} km²")
                            else:  # Probably meters
                                world_area_km2 = (world_width / 1000) * (world_height / 1000)
                                print(f"   📏 Estimated area (meters): {world_area_km2:.4f} km²")
                    else:
                        print(f"   🌍 Coordinates appear to be in geographic system (degrees)")
                        world_area_km2 = (world_width * 111) * (world_height * 111)
                        print(f"   📏 Estimated area (degrees): {world_area_km2:.2f} km²")
        
        # 3. Compare original vs world file areas
        if original_bounds and 'world_area_km2' in locals():
            print(f"\n🔍 COMPARISON:")
            print(f"   📍 Original request area: {original_area_km2:.2f} km²")
            print(f"   🌍 World file area: {world_area_km2:.4f} km²")
            
            ratio = world_area_km2 / original_area_km2 if original_area_km2 > 0 else 0
            print(f"   📊 Ratio (world/original): {ratio:.6f}")
            
            if ratio < 0.001:
                print(f"   🚨 HUGE DISCREPANCY! World file area is {1/ratio:.0f}x smaller!")
                print(f"   💡 This suggests major coordinate/scaling issues")
            elif ratio < 0.1:
                print(f"   ⚠️  Significant discrepancy - world file area is {1/ratio:.1f}x smaller")
            elif 0.8 <= ratio <= 1.2:
                print(f"   ✅ Areas match reasonably well")
            else:
                print(f"   ⚠️  Moderate discrepancy")
        
        # 4. Check for LAZ file bounds
        laz_files = list(Path(region_dir).glob("*.laz"))
        if laz_files:
            print(f"\n📦 LAZ file analysis:")
            laz_file = laz_files[0]
            print(f"   📄 LAZ file: {laz_file.name}")
            
            # Try to get LAZ bounds using pdal info
            import subprocess
            try:
                result = subprocess.run(['pdal', 'info', str(laz_file), '--summary'], 
                                     capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    info_output = result.stdout
                    if 'bbox' in info_output or 'bounds' in info_output:
                        print(f"   📍 LAZ contains bounds information")
                        # Extract and compare
                        for line in info_output.split('\n'):
                            if 'bbox' in line.lower() or 'bounds' in line.lower():
                                print(f"      {line.strip()}")
                else:
                    print(f"   ❌ Could not read LAZ bounds: {result.stderr}")
            except Exception as e:
                print(f"   ❌ PDAL not available or error: {e}")
        
        print()

def check_acquisition_logs():
    """Look for acquisition logs that might contain original request info"""
    
    print(f"\n🔍 SEARCHING FOR ACQUISITION LOGS:")
    print("=" * 50)
    
    # Search for any files that might contain original request information
    search_patterns = [
        "**/download*.log",
        "**/acquisition*.log", 
        "**/opentopography*.json",
        "**/request*.txt",
        "**/bounds*.txt"
    ]
    
    output_dir = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output")
    
    found_files = []
    for pattern in search_patterns:
        found_files.extend(output_dir.glob(pattern))
    
    for file_path in found_files:
        print(f"📄 Found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Look for bounds information
            if any(keyword in content.lower() for keyword in ['bbox', 'bound', 'north', 'south', 'east', 'west']):
                print(f"   📍 Contains bounds information")
                
                # Show relevant lines
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if any(keyword in line.lower() for keyword in ['bbox', 'bound', 'north', 'south', 'east', 'west']):
                        print(f"      Line {i+1}: {line.strip()}")
        except Exception as e:
            print(f"   ❌ Could not read file: {e}")

if __name__ == "__main__":
    analyze_original_vs_world_bounds()
    check_acquisition_logs()
    
    print(f"\n🎯 KEY INSIGHTS:")
    print("=" * 40)
    print("🔍 This analysis should reveal:")
    print("   1. What area was originally requested from Copernicus/OpenTopography")
    print("   2. What area the world files think they represent")
    print("   3. The magnitude of discrepancy between request and world file")
    print("   4. Whether the issue is in coordinate systems or actual data extent")
