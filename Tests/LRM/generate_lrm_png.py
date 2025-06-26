#!/usr/bin/env python3
"""
Generate PNG from LRM TIF
=========================

Simple script to convert OR_WizardIsland_LRM_adaptive.tif to PNG using optimal
archaeological LRM visualization settings.

Based on the best practices for coolwarm diverging colormap visualization.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from osgeo import gdal
import warnings
from pathlib import Path

# Add the parent directory to the path to import convert functions
sys.path.append(str(Path(__file__).parent.parent.parent))

warnings.filterwarnings('ignore')

def generate_lrm_png():
    """Generate optimized LRM PNG from the test TIF file."""
    
    lrm_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/LRM/OR_WizardIsland_LRM_adaptive.tif"
    output_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/LRM/OR_WizardIsland_LRM.png"
    
    print(f"📂 Loading LRM data from: {os.path.basename(lrm_path)}")
    
    # Load LRM data
    ds = gdal.Open(lrm_path)
    if ds is None:
        raise Exception(f"Failed to open LRM file: {lrm_path}")
    
    band = ds.GetRasterBand(1)
    lrm_data = band.ReadAsArray().astype(np.float32)
    
    # Get dimensions
    height, width = lrm_data.shape
    print(f"📏 Dimensions: {width} × {height} pixels")
    
    # Handle NoData values (-9999)
    nodata_mask = lrm_data == -9999
    lrm_data[nodata_mask] = np.nan
    
    # Calculate statistics
    valid_data = lrm_data[~np.isnan(lrm_data)]
    stats = {
        'min': np.min(valid_data),
        'max': np.max(valid_data),
        'mean': np.mean(valid_data),
        'std': np.std(valid_data),
        'p2': np.percentile(valid_data, 2),
        'p98': np.percentile(valid_data, 98),
        'count': len(valid_data)
    }
    
    print(f"📊 LRM Statistics:")
    print(f"   🔢 Valid pixels: {stats['count']:,}")
    print(f"   📈 Range: {stats['min']:.3f} to {stats['max']:.3f} meters")
    print(f"   📊 Mean: {stats['mean']:.3f} ± {stats['std']:.3f} meters")
    print(f"   📊 2%-98% percentiles: {stats['p2']:.3f} to {stats['p98']:.3f} meters")
    
    # Apply 2%-98% percentile clipping for enhanced contrast
    p_min, p_max = stats['p2'], stats['p98']
    
    # Symmetric clipping around zero for proper diverging colormap
    max_abs = max(abs(p_min), abs(p_max))
    clip_min, clip_max = -max_abs, max_abs
    lrm_clipped = np.clip(lrm_data, clip_min, clip_max)
    
    # Normalize to [-1, 1] range for coolwarm colormap
    if max_abs > 0:
        lrm_normalized = lrm_clipped / max_abs
    else:
        lrm_normalized = lrm_clipped
    
    print(f"🎨 Applying coolwarm colormap normalization:")
    print(f"   📊 Clip range: ±{max_abs:.3f} meters")
    print(f"   🌡️ Normalized range: -1.0 to +1.0")
    print(f"   🔴 Red: Positive relief (ridges, mounds, elevated features)")
    print(f"   🔵 Blue: Negative relief (valleys, ditches, depressions)")
    print(f"   ⚪ White: Neutral areas (flat terrain)")
    
    # Create high-resolution figure
    dpi = 300
    width_inch = width / dpi
    height_inch = height / dpi
    
    fig, ax = plt.subplots(figsize=(width_inch, height_inch), dpi=dpi)
    
    # Apply coolwarm colormap
    im = ax.imshow(lrm_normalized, cmap='coolwarm', vmin=-1, vmax=1, interpolation='bilinear')
    
    # Add colorbar with archaeological interpretation
    cbar = plt.colorbar(im, ax=ax, shrink=0.6, aspect=20)
    cbar.set_label('Local Relief (normalized)', rotation=270, labelpad=20, fontsize=12)
    
    # Add archaeological interpretation labels
    cbar.ax.text(1.5, 0.85, 'Elevated\n(Mounds, Ridges)', transform=cbar.ax.transAxes, 
                 fontsize=10, ha='left', va='center', color='darkred', weight='bold')
    cbar.ax.text(1.5, 0.15, 'Depressed\n(Ditches, Valleys)', transform=cbar.ax.transAxes, 
                 fontsize=10, ha='left', va='center', color='darkblue', weight='bold')
    
    # Add title with processing parameters
    title = f"Local Relief Model (LRM)\nCoolwarm Archaeological Visualization"
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Remove axes for clean visualization
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add scale information
    geotransform = ds.GetGeoTransform()
    pixel_width = abs(geotransform[1])
    pixel_height = abs(geotransform[5])
    
    scale_text = f"Resolution: {pixel_width:.2f}m/pixel"
    ax.text(0.02, 0.02, scale_text, transform=ax.transAxes, 
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    # Add archaeological analysis note
    analysis_text = "Archaeological Analysis Mode\nBlue: Potential ditches/depressions\nRed: Potential mounds/elevations"
    ax.text(0.02, 0.98, analysis_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.9))
    
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    ds = None
    
    print(f"✅ LRM PNG generated successfully!")
    print(f"📁 Output: {os.path.basename(output_path)}")
    print(f"📏 Resolution: {dpi} DPI")
    print(f"🌡️ Colormap: Coolwarm diverging (archaeological interpretation)")
    print(f"🎯 Ready for archaeological analysis and overlay mapping")

if __name__ == "__main__":
    generate_lrm_png()
