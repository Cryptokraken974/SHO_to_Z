#!/usr/bin/env python3
"""
Generate PNG from Hillshade RGB TIF
===================================

Simple script to convert hillshade_rgb.tif to PNG using various visualization approaches.
Unlike single-band rasters, this RGB composite can be visualized in different ways.

Author: AI Assistant  
Date: January 2025
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal
import warnings
from pathlib import Path

# Add the parent directory to the path to import convert functions
sys.path.append(str(Path(__file__).parent.parent.parent))

warnings.filterwarnings('ignore')

def generate_hillshade_rgb_png():
    """Generate optimized PNG from the hillshade RGB TIF file."""
    
    rgb_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb.tif"
    output_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb.png"
    
    print(f"📂 Loading Hillshade RGB data from: {os.path.basename(rgb_path)}")
    
    # Load RGB data
    ds = gdal.Open(rgb_path)
    if ds is None:
        raise Exception(f"Failed to open Hillshade RGB file: {rgb_path}")
    
    # Get dimensions and band count
    width = ds.RasterXSize
    height = ds.RasterYSize
    num_bands = ds.RasterCount
    
    print(f"📏 Dimensions: {width} × {height} pixels")
    print(f"🎨 Bands: {num_bands} (RGB composite)")
    
    # Read RGB bands
    red_band = ds.GetRasterBand(1).ReadAsArray()
    green_band = ds.GetRasterBand(2).ReadAsArray()
    blue_band = ds.GetRasterBand(3).ReadAsArray()
    
    # Get geospatial info
    geotransform = ds.GetGeoTransform()
    pixel_size = abs(geotransform[1])
    
    ds = None
    
    # Calculate statistics for each band
    for i, (band_data, band_name, color) in enumerate([(red_band, "Red", "🔴"), 
                                                      (green_band, "Green", "🟢"), 
                                                      (blue_band, "Blue", "🔵")]):
        band_stats = {
            'min': np.min(band_data),
            'max': np.max(band_data), 
            'mean': np.mean(band_data),
            'std': np.std(band_data)
        }
        print(f"📊 {color} {band_name} band: range {band_stats['min']}-{band_stats['max']}, "
              f"mean {band_stats['mean']:.1f} ± {band_stats['std']:.1f}")
    
    # Combine into RGB array
    rgb_array = np.stack([red_band, green_band, blue_band], axis=-1)
    
    print(f"🎨 Creating RGB visualization:")
    print(f"   📐 Resolution: {pixel_size:.2f}m/pixel")
    print(f"   🌈 RGB composite ready for display")
    
    # Create high-resolution figure
    dpi = 300
    width_inch = width / dpi
    height_inch = height / dpi
    
    fig, ax = plt.subplots(figsize=(width_inch, height_inch), dpi=dpi)
    
    # Display RGB image (values already in 0-255 range)
    rgb_normalized = rgb_array.astype(np.uint8)
    ax.imshow(rgb_normalized, aspect='equal', interpolation='nearest')
    
    # Add title and information
    title = f"Hillshade RGB Composite\n{os.path.basename(rgb_path)}"
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Remove axes for clean visualization
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add scale information
    scale_text = f"Resolution: {pixel_size:.2f}m/pixel"
    ax.text(0.02, 0.02, scale_text, transform=ax.transAxes, 
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    # Add RGB composite explanation
    explanation_text = "RGB Hillshade Composite\nMulti-directional relief visualization\nCombines different illumination angles"
    ax.text(0.02, 0.98, explanation_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.9))
    
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"✅ Hillshade RGB PNG generated successfully!")
    print(f"📁 Output: {os.path.basename(output_path)}")
    print(f"📏 Resolution: {dpi} DPI")
    print(f"🌈 RGB composite visualization complete")

if __name__ == "__main__":
    generate_hillshade_rgb_png()
