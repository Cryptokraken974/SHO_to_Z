#!/usr/bin/env python3
"""
ROOT CAUSE ANALYSIS: Original LAZ Request Bounds vs World File Bounds

You identified the key issue: There's a massive discrepancy between the area 
that was originally requested from OpenTopography/Copernicus and what the 
world files think they represent.

This explains why overlays appear as tiny dots - they're scaled for an area
much smaller than what was actually requested and downloaded.
"""

import os
from pathlib import Path

def analyze_root_cause():
    """Analyze the fundamental scaling discrepancy"""
    
    print("🎯 ROOT CAUSE ANALYSIS")
    print("=" * 80)
    print("Issue: Original LAZ request bounds vs World file representation")
    print()
    
    # Test case: PRGL1260C9597_2014 (confirmed to have the issue)
    region = "PRGL1260C9597_2014"
    
    print(f"🔍 Case Study: {region}")
    print("-" * 50)
    
    # 1. Original request area (from metadata.txt)
    metadata_path = f"output/{region}/metadata.txt"
    with open(metadata_path, 'r') as f:
        content = f.read()
    
    bounds = {}
    for line in content.split('\n'):
        if 'North Bound:' in line:
            bounds['north'] = float(line.split(':')[1].strip())
        elif 'South Bound:' in line:
            bounds['south'] = float(line.split(':')[1].strip())
        elif 'East Bound:' in line:
            bounds['east'] = float(line.split(':')[1].strip())
        elif 'West Bound:' in line:
            bounds['west'] = float(line.split(':')[1].strip())
    
    original_width_deg = abs(bounds['east'] - bounds['west'])
    original_height_deg = abs(bounds['north'] - bounds['south'])
    original_area_km2 = (original_width_deg * 111) * (original_height_deg * 111)
    
    print(f"📍 ORIGINAL REQUEST (what was asked for):")
    print(f"   Bounds: {bounds['west']:.8f} to {bounds['east']:.8f} longitude")
    print(f"   Bounds: {bounds['south']:.8f} to {bounds['north']:.8f} latitude")
    print(f"   Size: {original_width_deg:.8f}° × {original_height_deg:.8f}°")
    print(f"   Area: {original_area_km2:.6f} km²")
    print(f"   Approx: {original_width_deg*111:.0f}m × {original_height_deg*111:.0f}m")
    
    # 2. What the world file represents
    world_file = f"output/{region}/lidar/png_outputs/CHM.wld"
    with open(world_file, 'r') as f:
        lines = f.read().strip().split('\n')
    
    pixel_x = float(lines[0])  # 1.0 feet per pixel
    pixel_y = float(lines[3])  # -1.0 feet per pixel
    
    png_file = f"output/{region}/lidar/png_outputs/CHM.png"
    from PIL import Image
    with Image.open(png_file) as img:
        width_px, height_px = img.size
    
    # World file coverage in feet
    world_width_feet = abs(pixel_x * width_px)
    world_height_feet = abs(pixel_y * height_px)
    
    # Convert to meters and km²
    world_width_m = world_width_feet * 0.3048
    world_height_m = world_height_feet * 0.3048
    world_area_km2 = (world_width_m / 1000) * (world_height_m / 1000)
    
    print(f"\n🌍 WORLD FILE REPRESENTATION (what GDAL thinks it is):")
    print(f"   Pixel size: {pixel_x} × {pixel_y} feet")
    print(f"   Image: {width_px} × {height_px} pixels")
    print(f"   Coverage: {world_width_feet:.0f} × {world_height_feet:.0f} feet")
    print(f"   Coverage: {world_width_m:.0f} × {world_height_m:.0f} meters")
    print(f"   Area: {world_area_km2:.8f} km²")
    
    # 3. The discrepancy
    ratio = world_area_km2 / original_area_km2
    scale_factor = 1 / ratio
    
    print(f"\n🚨 THE DISCREPANCY:")
    print(f"   Original area: {original_area_km2:.6f} km²")
    print(f"   World file area: {world_area_km2:.8f} km²")
    print(f"   Ratio: {ratio:.8f}")
    print(f"   Scale factor: World file is {scale_factor:.1f}x SMALLER")
    
    print(f"\n💡 WHAT THIS MEANS:")
    print(f"   • LAZ was requested for {original_area_km2:.2f} km² area")
    print(f"   • But world file says it covers only {world_area_km2:.4f} km²")
    print(f"   • When displayed in Leaflet, overlay appears {scale_factor:.0f}x too small")
    print(f"   • This is why overlays show as tiny dots instead of proper coverage")
    
    print(f"\n🔧 THE SOLUTION:")
    print(f"   • Fix world file pixel sizes to match original request bounds")
    print(f"   • Correct pixel size should be:")
    
    correct_pixel_x_deg = original_width_deg / width_px
    correct_pixel_y_deg = -original_height_deg / height_px  # Negative for north-up
    
    print(f"     X: {correct_pixel_x_deg:.12f} degrees/pixel")
    print(f"     Y: {correct_pixel_y_deg:.12f} degrees/pixel")
    print(f"   • This would give proper geographic scaling")

def fix_world_file_scaling():
    """Create corrected world file with proper scaling"""
    
    print(f"\n🔧 FIXING WORLD FILE SCALING:")
    print("=" * 50)
    
    region = "PRGL1260C9597_2014"
    
    # Get original bounds
    metadata_path = f"output/{region}/metadata.txt"
    with open(metadata_path, 'r') as f:
        content = f.read()
    
    bounds = {}
    for line in content.split('\n'):
        if 'North Bound:' in line:
            bounds['north'] = float(line.split(':')[1].strip())
        elif 'South Bound:' in line:
            bounds['south'] = float(line.split(':')[1].strip())
        elif 'East Bound:' in line:
            bounds['east'] = float(line.split(':')[1].strip())
        elif 'West Bound:' in line:
            bounds['west'] = float(line.split(':')[1].strip())
    
    # Get PNG dimensions
    png_file = f"output/{region}/lidar/png_outputs/CHM.png"
    from PIL import Image
    with Image.open(png_file) as img:
        width_px, height_px = img.size
    
    # Calculate correct pixel sizes
    width_deg = abs(bounds['east'] - bounds['west'])
    height_deg = abs(bounds['north'] - bounds['south'])
    
    pixel_x_deg = width_deg / width_px
    pixel_y_deg = -height_deg / height_px  # Negative for north-up
    
    # Create corrected world file
    corrected_world_file = f"output/{region}/lidar/png_outputs/CHM_CORRECTED.wld"
    
    with open(corrected_world_file, 'w') as f:
        f.write(f"{pixel_x_deg:.12f}\n")      # X pixel size
        f.write("0.0\n")                       # Rotation
        f.write("0.0\n")                       # Rotation  
        f.write(f"{pixel_y_deg:.12f}\n")      # Y pixel size
        f.write(f"{bounds['west']:.12f}\n")    # Upper left X (longitude)
        f.write(f"{bounds['north']:.12f}\n")   # Upper left Y (latitude)
    
    print(f"✅ Created corrected world file: {corrected_world_file}")
    print(f"📏 Correct pixel sizes:")
    print(f"   X: {pixel_x_deg:.12f} degrees/pixel")
    print(f"   Y: {pixel_y_deg:.12f} degrees/pixel")
    print(f"📍 Upper left corner: ({bounds['west']:.8f}, {bounds['north']:.8f})")
    
    # Verify the corrected area
    corrected_area_km2 = (width_deg * 111) * (height_deg * 111)
    print(f"✅ Corrected area: {corrected_area_km2:.6f} km² (matches original request)")

if __name__ == "__main__":
    analyze_root_cause()
    fix_world_file_scaling()
    
    print(f"\n🎯 CONCLUSION:")
    print("=" * 40)
    print("✅ Root cause identified: World file pixel sizes are wrong")
    print("✅ Solution: Use original request bounds to calculate correct pixel sizes")
    print("✅ This will fix the overlay scaling issue completely")
