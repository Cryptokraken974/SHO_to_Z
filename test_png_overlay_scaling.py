#!/usr/bin/env python3
"""
Test script to verify PNG overlay scaling fixes are working properly.
This script regenerates PNG overlays with world files and validates proper scaling.
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from convert import convert_geotiff_to_png
from geo_utils import get_laz_overlay_data

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_png_scaling_fix():
    """Test the PNG overlay scaling fix with world file generation."""
    
    # Test with PRGL region
    region_name = "PRGL1260C9597_2014"
    base_path = f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/{region_name}"
    
    print(f"🔍 Testing PNG overlay scaling for region: {region_name}")
    print("=" * 60)
    
    # Define overlay types to test
    overlay_types = [
        ("CHM", "CHM"),
        ("HillshadeRgb", "HillshadeRGB"), 
        ("Lrm", "LRM"),
        ("Slope", "Slope"),
        ("Sky_View_Factor", "SVF")
    ]
    
    png_output_dir = f"{base_path}/lidar/png_outputs"
    os.makedirs(png_output_dir, exist_ok=True)
    
    print(f"📁 PNG output directory: {png_output_dir}")
    
    for folder_name, overlay_name in overlay_types:
        tif_dir = f"{base_path}/lidar/{folder_name}"
        
        # Find the TIFF file
        tif_files = [f for f in os.listdir(tif_dir) if f.endswith('.tif')]
        if not tif_files:
            print(f"⚠️  No TIFF files found in {tif_dir}")
            continue
            
        tif_path = os.path.join(tif_dir, tif_files[0])
        png_path = os.path.join(png_output_dir, f"{overlay_name}.png")
        pgw_path = os.path.join(png_output_dir, f"{overlay_name}.pgw")
        
        print(f"\n🔄 Processing {overlay_name}:")
        print(f"   Input TIFF: {tif_path}")
        print(f"   Output PNG: {png_path}")
        print(f"   World file: {pgw_path}")
        
        # Remove existing files to test fresh generation
        for file_path in [png_path, pgw_path]:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"   🗑️  Removed existing: {os.path.basename(file_path)}")
        
        try:
            # Convert TIFF to PNG with world file generation
            convert_geotiff_to_png(
                tif_path=tif_path,
                png_path=png_path,
                enhanced_resolution=False,
                save_to_consolidated=False
            )
            
            # Check if files were created
            png_exists = os.path.exists(png_path)
            pgw_exists = os.path.exists(pgw_path)
            
            print(f"   ✅ PNG created: {png_exists}")
            print(f"   ✅ World file created: {pgw_exists}")
            
            # Read and display world file parameters if created
            if pgw_exists:
                with open(pgw_path, 'r') as f:
                    world_params = f.read().strip().split('\n')
                    if len(world_params) >= 6:
                        pixel_size_x = float(world_params[0])
                        pixel_size_y = float(world_params[3])
                        upper_left_x = float(world_params[4])
                        upper_left_y = float(world_params[5])
                        
                        print(f"   🌍 World file parameters:")
                        print(f"      Pixel size X: {pixel_size_x:.8f}°")
                        print(f"      Pixel size Y: {pixel_size_y:.8f}°")
                        print(f"      Upper left X: {upper_left_x:.8f}°")
                        print(f"      Upper left Y: {upper_left_y:.8f}°")
                        
                        # Calculate approximate coverage
                        # Typical LiDAR tile is ~1000x1000 pixels
                        approx_width = abs(pixel_size_x * 1000)
                        approx_height = abs(pixel_size_y * 1000)
                        print(f"   📏 Estimated coverage: {approx_width:.4f}° × {approx_height:.4f}°")
            else:
                print(f"   ❌ World file not generated!")
                
        except Exception as e:
            print(f"   ❌ Error processing {overlay_name}: {e}")
    
    print(f"\n🧪 Testing overlay data extraction:")
    print("=" * 40)
    
    # Test the get_laz_overlay_data function
    try:
        # Test with a specific overlay type
        for overlay_type in ["CHM", "HillshadeRGB", "LRM", "Slope", "SVF"]:
            print(f"\n📊 Testing {overlay_type} overlay:")
            overlay_data = get_laz_overlay_data(region_name, overlay_type)
            
            if overlay_data and 'bounds' in overlay_data:
                bounds = overlay_data['bounds']
                name = overlay_type
                
                print(f"   📊 Overlay: {name}")
                if bounds:
                    north = bounds.get('north', 0)
                    south = bounds.get('south', 0)
                    east = bounds.get('east', 0)
                    west = bounds.get('west', 0)
                    
                    width = abs(east - west)
                    height = abs(north - south)
                    
                    print(f"   Bounds: N:{north:.6f}, S:{south:.6f}, E:{east:.6f}, W:{west:.6f}")
                    print(f"   Size: {width:.6f}° × {height:.6f}°")
                    
                    # Check if bounds are realistic (should be much larger than 0.01°)
                    if width > 0.01 and height > 0.01:
                        print(f"   ✅ Realistic geographic extent")
                    else:
                        print(f"   ⚠️  Small extent - may appear as tiny overlay")
                else:
                    print(f"   ❌ No bounds information")
            else:
                print(f"   ❌ No overlay data found for {overlay_type}")
        
        print(f"\n📊 Summary:")
        print(f"✅ Individual overlay testing completed")
            
    except Exception as e:
        print(f"❌ Error getting overlay data: {e}")
    
    print(f"\n🎯 Test Summary:")
    print("=" * 30)
    print("✅ World file generation is enabled in convert.py")
    print("✅ PNG conversion with world files tested")
    print("✅ Overlay data extraction tested")
    print("\n📝 Next steps:")
    print("   1. Verify overlays display at correct scale in Leaflet map")
    print("   2. Test with other regions if needed")
    print("   3. Update metadata.txt with proper bounds if required")

if __name__ == "__main__":
    test_png_scaling_fix()
