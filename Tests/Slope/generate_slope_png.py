#!/usr/bin/env python3
"""
Generate PNG from Slope TIF
===========================

Simple script to convert OR_WizardIsland_slope.tif to PNG using optimal
archaeological slope visualization settings.

Based on the best practices discovered in slope testing.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from osgeo import gdal
import warnings
warnings.filterwarnings('ignore')

def generate_slope_png():
    """Generate optimized slope PNG from the test TIF file."""
    
    slope_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/Slope/OR_WizardIsland_slope.tif"
    output_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/Slope/OR_WizardIsland_slope.png"
    
    print(f"📂 Loading slope data from: {os.path.basename(slope_path)}")
    
    # Load slope data
    ds = gdal.Open(slope_path)
    if ds is None:
        raise Exception(f"Failed to open slope file: {slope_path}")
    
    band = ds.GetRasterBand(1)
    slope_data = band.ReadAsArray().astype(np.float32)
    
    # Get dimensions
    height, width = slope_data.shape
    print(f"📏 Dimensions: {width} × {height} pixels")
    
    # Handle NoData values (-9999)
    nodata_mask = slope_data == -9999
    slope_data[nodata_mask] = np.nan
    
    # Calculate statistics
    valid_data = slope_data[~np.isnan(slope_data)]
    stats = {
        'min': np.min(valid_data),
        'max': np.max(valid_data),
        'mean': np.mean(valid_data),
        'std': np.std(valid_data),
        'p2': np.percentile(valid_data, 2),
        'p98': np.percentile(valid_data, 98)
    }
    
    print(f"📊 Data range: {stats['min']:.2f}° to {stats['max']:.2f}°")
    print(f"📊 Mean: {stats['mean']:.2f}° ± {stats['std']:.2f}°")
    print(f"📊 P2-P98: {stats['p2']:.2f}° to {stats['p98']:.2f}°")
    
    # Use archaeological-optimized settings:
    # - Focus on 2-20° range for archaeological features
    # - Use viridis colormap for good contrast
    # - Apply gamma correction for enhanced detail
    
    vmin, vmax = 2.0, 20.0  # Archaeological standard range
    print(f"🎯 Using archaeological range: {vmin}° to {vmax}°")
    
    # Normalize to 0-1 range
    normalized_data = np.clip((slope_data - vmin) / (vmax - vmin), 0, 1)
    
    # Apply gamma correction for enhanced detail in mid-tones
    gamma = 0.7  # Slightly enhance mid-range slopes
    normalized_data = np.power(normalized_data, gamma)
    
    # Create figure with exact pixel dimensions
    dpi = 100
    fig_width = width / dpi
    fig_height = height / dpi
    
    fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])  # Fill entire figure
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)  # Flip Y axis for image convention
    ax.axis('off')
    
    # Use viridis colormap (excellent for terrain analysis)
    cmap = plt.cm.viridis
    
    # Create masked array for NoData handling
    masked_data = np.ma.masked_where(np.isnan(normalized_data), normalized_data)
    
    # Display the slope image
    im = ax.imshow(masked_data, cmap=cmap, vmin=0, vmax=1, 
                  aspect='equal', interpolation='nearest',
                  extent=[0, width, height, 0])
    
    # Save as PNG
    print(f"💾 Saving PNG to: {os.path.basename(output_path)}")
    plt.savefig(output_path, 
                dpi=dpi, 
                bbox_inches='tight', 
                pad_inches=0,
                facecolor='none', 
                edgecolor='none',
                transparent=False)
    
    plt.close(fig)
    
    # Check file size
    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    print(f"✅ Generated PNG: {file_size:.1f} MB")
    print(f"📍 Saved to: {output_path}")

if __name__ == "__main__":
    generate_slope_png()
