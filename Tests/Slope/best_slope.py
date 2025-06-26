#!/usr/bin/env python3
"""
Best Slope Visualization Test
=============================

This script tests different slope visualization techniques to find the optimal
approach for archaeological terrain analysis. It processes the test slope file
with various colormaps, normalization methods, and enhancement techniques.

Test File: OR_WizardIsland_slope.tif
Goal: Generate the best possible slope visualization for archaeological analysis

Author: AI Assistant
Date: June 26, 2025
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from osgeo import gdal
import time
from pathlib import Path

# Add the parent directory to the path to import convert functions
sys.path.append(str(Path(__file__).parent.parent.parent))

def load_test_slope(slope_path: str):
    """Load the test slope TIFF file and return data with statistics."""
    print(f"📂 Loading test slope: {os.path.basename(slope_path)}")
    
    ds = gdal.Open(slope_path)
    if ds is None:
        raise Exception(f"Failed to open slope file: {slope_path}")
    
    band = ds.GetRasterBand(1)
    slope_data = band.ReadAsArray()
    
    # Get geospatial info
    geotransform = ds.GetGeoTransform()
    width = ds.RasterXSize
    height = ds.RasterYSize
    
    ds = None
    band = None
    
    # Handle NoData values
    nodata_mask = slope_data == -9999
    slope_data[nodata_mask] = np.nan
    
    # Calculate statistics
    valid_data = slope_data[~np.isnan(slope_data)]
    if len(valid_data) > 0:
        stats = {
            'min': np.min(valid_data),
            'max': np.max(valid_data),
            'mean': np.mean(valid_data),
            'std': np.std(valid_data),
            'median': np.median(valid_data),
            'p5': np.percentile(valid_data, 5),
            'p95': np.percentile(valid_data, 95),
            'p2': np.percentile(valid_data, 2),
            'p98': np.percentile(valid_data, 98),
            'valid_pixels': len(valid_data),
            'total_pixels': slope_data.size
        }
    else:
        stats = {}
    
    print(f"📊 Slope Statistics:")
    print(f"   Dimensions: {width} × {height} pixels")
    print(f"   Valid pixels: {stats.get('valid_pixels', 0):,} / {stats.get('total_pixels', 0):,}")
    if stats:
        print(f"   Range: {stats['min']:.2f}° to {stats['max']:.2f}°")
        print(f"   Mean: {stats['mean']:.2f}° ± {stats['std']:.2f}°")
        print(f"   Median: {stats['median']:.2f}°")
        print(f"   P2-P98: {stats['p2']:.2f}° to {stats['p98']:.2f}°")
        print(f"   P5-P95: {stats['p5']:.2f}° to {stats['p95']:.2f}°")
    
    return slope_data, stats, geotransform, width, height

def generate_slope_visualization(slope_data, stats, width, height, method_name, 
                               colormap, normalization, enhancement=None, output_path=None):
    """Generate a slope visualization with the specified parameters."""
    print(f"\n🎨 Generating: {method_name}")
    print(f"   Colormap: {colormap}")
    print(f"   Normalization: {normalization}")
    if enhancement:
        print(f"   Enhancement: {enhancement}")
    
    start_time = time.time()
    
    # Apply normalization
    valid_data = slope_data[~np.isnan(slope_data)]
    if len(valid_data) == 0:
        print("   ⚠️ No valid data")
        return None
    
    if normalization == "minmax":
        vmin, vmax = stats['min'], stats['max']
    elif normalization == "stddev_2":
        vmin = max(stats['mean'] - 2*stats['std'], stats['min'])
        vmax = min(stats['mean'] + 2*stats['std'], stats['max'])
    elif normalization == "stddev_1.5":
        vmin = max(stats['mean'] - 1.5*stats['std'], stats['min'])
        vmax = min(stats['mean'] + 1.5*stats['std'], stats['max'])
    elif normalization == "percentile_2_98":
        vmin, vmax = stats['p2'], stats['p98']
    elif normalization == "percentile_5_95":
        vmin, vmax = stats['p5'], stats['p95']
    elif normalization == "archaeological_2_20":
        # Archaeological standard: focus on 2-20 degree range
        vmin, vmax = 2.0, 20.0
    else:
        vmin, vmax = stats['min'], stats['max']
    
    print(f"   Data range: {vmin:.2f}° to {vmax:.2f}°")
    
    # Normalize data
    normalized_data = np.clip((slope_data - vmin) / (vmax - vmin), 0, 1)
    
    # Apply enhancement if specified
    if enhancement == "gamma_0.5":
        normalized_data = np.power(normalized_data, 0.5)
    elif enhancement == "gamma_1.5":
        normalized_data = np.power(normalized_data, 1.5)
    elif enhancement == "log":
        normalized_data = np.log1p(normalized_data * 9) / np.log(10)  # log10(1+9x)
    elif enhancement == "sqrt":
        normalized_data = np.sqrt(normalized_data)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10), dpi=150)
    
    # Get colormap
    if colormap == "custom_archaeological":
        # Create custom colormap for archaeological analysis
        colors = ['#1a1a1a', '#2d5016', '#4a7c59', '#8fb996', '#d4e7ca', '#f0f7e8']
        cmap = mcolors.LinearSegmentedColormap.from_list('archaeological', colors)
    else:
        cmap = plt.cm.get_cmap(colormap)
    
    # Create masked array
    masked_data = np.ma.masked_where(np.isnan(normalized_data), normalized_data)
    
    # Display image
    im = ax.imshow(masked_data, cmap=cmap, vmin=0, vmax=1, 
                  aspect='equal', interpolation='nearest')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('Slope (degrees)', rotation=270, labelpad=20, fontsize=12)
    
    # Set colorbar ticks to show actual slope values
    tick_positions = np.linspace(0, 1, 6)
    tick_labels = [f"{vmin + pos * (vmax - vmin):.1f}" for pos in tick_positions]
    cbar.set_ticks(tick_positions)
    cbar.set_ticklabels(tick_labels)
    
    # Add title
    title = f"{method_name}\n{colormap} | {normalization}"
    if enhancement:
        title += f" | {enhancement}"
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Remove axes
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add statistics text
    textstr = f'Range: {vmin:.1f}°-{vmax:.1f}°\nMean: {stats["mean"]:.1f}°\nStd: {stats["std"]:.1f}°'
    props = dict(boxstyle='round', facecolor='white', alpha=0.8)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', bbox=props)
    
    # Save if output path provided
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', format='PNG')
        print(f"   💾 Saved: {os.path.basename(output_path)}")
    
    processing_time = time.time() - start_time
    print(f"   ⏱️ Generated in {processing_time:.2f}s")
    
    plt.close()
    return output_path

def test_slope_visualizations():
    """Test various slope visualization methods."""
    print("🧪 SLOPE VISUALIZATION TESTING")
    print("=" * 50)
    
    # Get the test file path
    test_dir = Path(__file__).parent
    slope_file = test_dir / "OR_WizardIsland_slope.tif"
    
    if not slope_file.exists():
        print(f"❌ Test file not found: {slope_file}")
        return
    
    # Load test data
    slope_data, stats, geotransform, width, height = load_test_slope(str(slope_file))
    
    # Create output directory
    output_dir = test_dir / "visualizations"
    output_dir.mkdir(exist_ok=True)
    
    # Define test cases
    test_cases = [
        # Standard colormaps with different normalizations
        ("Standard_Gray_MinMax", "gray", "minmax", None),
        ("Standard_Gray_StdDev2", "gray", "stddev_2", None),
        ("Standard_Gray_Percentile", "gray", "percentile_2_98", None),
        
        # Terrain analysis colormaps
        ("Terrain_Viridis_StdDev", "viridis", "stddev_2", None),
        ("Terrain_Plasma_StdDev", "plasma", "stddev_2", None),
        ("Terrain_Inferno_StdDev", "inferno", "stddev_2", None),
        
        # Archaeological focused
        ("Archaeological_Custom_2to20", "custom_archaeological", "archaeological_2_20", None),
        ("Archaeological_Viridis_2to20", "viridis", "archaeological_2_20", None),
        ("Archaeological_YlOrRd_2to20", "YlOrRd", "archaeological_2_20", None),
        
        # Enhanced contrast versions
        ("Enhanced_Gray_Gamma05", "gray", "stddev_2", "gamma_0.5"),
        ("Enhanced_Gray_Gamma15", "gray", "stddev_2", "gamma_1.5"),
        ("Enhanced_Viridis_Sqrt", "viridis", "archaeological_2_20", "sqrt"),
        
        # Specialized terrain colormaps
        ("Specialized_Terrain", "terrain", "percentile_5_95", None),
        ("Specialized_Gist_Earth", "gist_earth", "percentile_5_95", None),
        ("Specialized_Copper", "copper", "archaeological_2_20", "gamma_0.5"),
    ]
    
    print(f"\n🔬 Running {len(test_cases)} visualization tests...")
    
    results = []
    for i, (name, colormap, normalization, enhancement) in enumerate(test_cases, 1):
        output_path = output_dir / f"{i:02d}_{name}.png"
        
        try:
            result = generate_slope_visualization(
                slope_data, stats, width, height, name,
                colormap, normalization, enhancement, str(output_path)
            )
            if result:
                results.append((name, str(output_path)))
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n✅ Successfully generated {len(results)} visualizations")
    print(f"📁 Results saved in: {output_dir}")
    
    # Generate comparison HTML
    generate_comparison_html(results, stats, output_dir)
    
    return results

def generate_comparison_html(results, stats, output_dir):
    """Generate an HTML file for easy comparison of all visualizations."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Slope Visualization Comparison - OR Wizard Island</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #333; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }}
        .item {{ background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .item img {{ width: 100%; border-radius: 4px; }}
        .item h3 {{ margin-top: 10px; color: #333; }}
        .best {{ border: 3px solid #4CAF50; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Slope Visualization Testing Results</h1>
        <p>Test File: OR_WizardIsland_slope.tif</p>
        <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="stats">
        <h2>📊 Data Statistics</h2>
        <p><strong>Range:</strong> {stats['min']:.2f}° to {stats['max']:.2f}°</p>
        <p><strong>Mean:</strong> {stats['mean']:.2f}° ± {stats['std']:.2f}°</p>
        <p><strong>Median:</strong> {stats['median']:.2f}°</p>
        <p><strong>P2-P98:</strong> {stats['p2']:.2f}° to {stats['p98']:.2f}°</p>
        <p><strong>Valid Pixels:</strong> {stats['valid_pixels']:,} / {stats['total_pixels']:,}</p>
    </div>
    
    <div class="grid">
"""
    
    for i, (name, path) in enumerate(results):
        img_name = os.path.basename(path)
        # Mark recommended visualizations
        css_class = "item best" if "Archaeological" in name or "Enhanced" in name else "item"
        
        html_content += f"""
        <div class="{css_class}">
            <img src="{img_name}" alt="{name}">
            <h3>{name.replace('_', ' ')}</h3>
        </div>
"""
    
    html_content += """
    </div>
    
    <div style="margin-top: 40px; padding: 20px; background: white; border-radius: 8px;">
        <h2>🎯 Recommendations</h2>
        <p><strong>For Archaeological Analysis:</strong> Look for visualizations that enhance subtle terrain features in the 2-20° range.</p>
        <p><strong>For General Terrain:</strong> Standard gray or viridis colormaps with statistical normalization work well.</p>
        <p><strong>Enhanced Contrast:</strong> Gamma corrections can help emphasize different slope ranges.</p>
        <p><em>Items with green borders are recommended for archaeological applications.</em></p>
    </div>
</body>
</html>
"""
    
    html_path = output_dir / "comparison.html"
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    print(f"📄 Comparison HTML generated: {html_path}")

if __name__ == "__main__":
    test_slope_visualizations()
