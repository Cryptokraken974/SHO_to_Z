#!/usr/bin/env python3
"""
Generate world files for areweok PNG overlays based on TIFF georeferencing
"""

import os
from PIL import Image

def generate_world_files():
    """Generate world files for PNG overlays in areweok region"""
    
    # Geographic bounds from TIFF files (WGS84)
    upper_left_x = -63.0001389  # West
    upper_left_y = -7.9998611   # North  
    pixel_size_x = 0.000277777777778   # Degrees per pixel (positive = east)
    pixel_size_y = -0.000277777777778  # Degrees per pixel (negative = south)
    
    # PNG files directory
    png_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/areweok/lidar/png_outputs"
    
    # List of PNG files to process
    png_files = [
        "CHM.png",
        "HillshadeRGB.png", 
        "LRM.png",
        "Slope.png",
        "SVF.png",
        "TintOverlay.png"
    ]
    
    print("🌍 Generating world files for areweok PNG overlays...")
    print(f"📍 Geographic extent:")
    print(f"   Upper Left: ({upper_left_x}, {upper_left_y})")
    print(f"   Pixel Size: ({pixel_size_x}, {pixel_size_y})")
    print()
    
    for png_file in png_files:
        png_path = os.path.join(png_dir, png_file)
        
        if not os.path.exists(png_path):
            print(f"❌ PNG file not found: {png_file}")
            continue
            
        try:
            # Get PNG dimensions
            with Image.open(png_path) as img:
                width, height = img.size
                
            print(f"📏 {png_file}: {width}x{height} pixels")
            
            # Generate world file content
            # World file format (6 lines):
            # 1. Pixel size in X direction (map units per pixel)
            # 2. Rotation about Y axis (usually 0)
            # 3. Rotation about X axis (usually 0)  
            # 4. Pixel size in Y direction (negative for north-up images)
            # 5. X coordinate of center of upper left pixel
            # 6. Y coordinate of center of upper left pixel
            
            world_content = f"""{pixel_size_x}
0.0
0.0
{pixel_size_y}
{upper_left_x}
{upper_left_y}
"""
            
            # Create world file (.pgw for PNG)
            base_name = os.path.splitext(png_file)[0]
            world_file = os.path.join(png_dir, f"{base_name}.pgw")
            
            with open(world_file, 'w') as f:
                f.write(world_content)
                
            print(f"✅ Created world file: {base_name}.pgw")
            
            # Calculate and display bounds for verification
            lower_right_x = upper_left_x + (width * pixel_size_x)
            lower_right_y = upper_left_y + (height * pixel_size_y)
            
            print(f"   Bounds: W={upper_left_x:.6f}, E={lower_right_x:.6f}")
            print(f"          N={upper_left_y:.6f}, S={lower_right_y:.6f}")
            print()
            
        except Exception as e:
            print(f"❌ Error processing {png_file}: {e}")
            continue
    
    print("🎯 World file generation complete!")
    print("\nNext steps:")
    print("1. The PNG overlays should now display properly on the map")
    print("2. The metadata.txt has been updated with correct bounds")
    print("3. Test the overlay display in the web interface")

if __name__ == "__main__":
    generate_world_files()
