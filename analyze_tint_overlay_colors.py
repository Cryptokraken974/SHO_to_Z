#!/usr/bin/env python3
"""
Analyze TintOverlay PNG colors to verify if it's using the new archaeological gentle color scheme
"""

import numpy as np
from PIL import Image
import sys
import os
from collections import Counter

def analyze_tint_overlay_colors(png_path):
    """Analyze the color palette of a TintOverlay PNG"""
    
    print(f"🔍 Analyzing TintOverlay colors: {png_path}")
    print("=" * 60)
    
    if not os.path.exists(png_path):
        print(f"❌ File not found: {png_path}")
        return False
    
    # Load the image
    try:
        image = Image.open(png_path)
        print(f"📊 Image info: {image.size[0]}x{image.size[1]} pixels, mode: {image.mode}")
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get pixel data
        pixels = np.array(image)
        print(f"📈 Pixel array shape: {pixels.shape}")
        
        # Flatten to list of RGB tuples
        pixel_colors = pixels.reshape(-1, 3)
        
        # Get unique colors and their frequencies
        unique_colors = []
        for pixel in pixel_colors:
            unique_colors.append(tuple(pixel))
        
        color_counts = Counter(unique_colors)
        most_common = color_counts.most_common(20)  # Top 20 colors
        
        print(f"\n🎨 Color Analysis:")
        print(f"Total unique colors: {len(color_counts)}")
        print(f"Total pixels: {len(pixel_colors)}")
        
        print(f"\n🔝 Top 20 most common colors:")
        print("Rank | RGB Values      | Hex Code | Count    | %")
        print("-" * 55)
        
        # Expected archaeological gentle colors (from our implementation)
        expected_colors = [
            (255, 250, 220),  # Pale cream/yellow (lowest elevation)
            (255, 228, 181),  # Soft peach/orange
            (255, 192, 152),  # Gentle salmon
            (255, 160, 122),  # Soft coral/light red
            (255, 140, 105)   # Warm light red (highest elevation)
        ]
        
        found_archaeological_colors = []
        
        for i, (color, count) in enumerate(most_common, 1):
            r, g, b = color
            hex_code = f"#{r:02x}{g:02x}{b:02x}"
            percentage = (count / len(pixel_colors)) * 100
            
            print(f"{i:4d} | ({r:3d},{g:3d},{b:3d}) | {hex_code} | {count:8d} | {percentage:5.2f}%")
            
            # Check if this color is close to any expected archaeological color
            for exp_color in expected_colors:
                if color_distance(color, exp_color) < 30:  # Allow some tolerance
                    found_archaeological_colors.append((color, exp_color, count))
        
        print(f"\n🎯 Archaeological Color Analysis:")
        print(f"Expected gentle colors found: {len(found_archaeological_colors)}/5")
        
        if found_archaeological_colors:
            print(f"\n✅ Found archaeological gentle colors:")
            for actual, expected, count in found_archaeological_colors:
                print(f"   Actual: {actual} → Expected: {expected} (distance: {color_distance(actual, expected):.1f})")
        
        # Check for old color schemes (terrain/arch_subtle)
        old_terrain_colors = [
            (0, 0, 139),      # Dark blue (terrain low)
            (0, 100, 255),    # Blue
            (0, 255, 255),    # Cyan
            (0, 255, 0),      # Green
            (255, 255, 0),    # Yellow
            (255, 165, 0),    # Orange
            (255, 69, 0),     # Red-orange
            (255, 255, 255)   # White (terrain high)
        ]
        
        found_old_colors = []
        for color, count in most_common:
            for old_color in old_terrain_colors:
                if color_distance(color, old_color) < 30:
                    found_old_colors.append((color, old_color))
        
        if found_old_colors:
            print(f"\n⚠️  Old terrain colors detected:")
            for actual, old in found_old_colors:
                print(f"   {actual} matches old terrain color {old}")
        
        # Determine which color scheme is being used
        arch_score = len(found_archaeological_colors)
        old_score = len(found_old_colors)
        
        print(f"\n🏆 Color Scheme Analysis:")
        print(f"Archaeological gentle score: {arch_score}/5")
        print(f"Old terrain color score: {old_score}")
        
        if arch_score >= 3:
            print(f"✅ CONFIRMED: Using new archaeological gentle color scheme!")
            return True
        elif old_score >= 3:
            print(f"❌ DETECTED: Using old terrain color scheme")
            return False
        else:
            print(f"❓ UNCLEAR: Mixed or unknown color scheme")
            return None
            
    except Exception as e:
        print(f"❌ Error analyzing image: {e}")
        return False

def color_distance(color1, color2):
    """Calculate Euclidean distance between two RGB colors"""
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(color1, color2)))

def main():
    # Test Box_Regions_4 TintOverlay
    tint_overlay_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/Box_Regions_4/lidar/png_outputs/TintOverlay.png"
    
    result = analyze_tint_overlay_colors(tint_overlay_path)
    
    print(f"\n🎬 Final Result:")
    if result is True:
        print("✅ Box_Regions_4 TintOverlay is using the NEW archaeological gentle color scheme!")
    elif result is False:
        print("❌ Box_Regions_4 TintOverlay is using an OLD color scheme")
    else:
        print("❓ Unable to determine color scheme definitively")

if __name__ == "__main__":
    main()
