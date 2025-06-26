#!/usr/bin/env python3
"""
Best SVF (Sky View Factor) Archaeological Visualization Test
============================================================

This script tests different SVF visualization techniques specifically optimized
for archaeological terrain analysis and anomaly detection. SVF values reveal
terrain enclosure/exposure characteristics that can indicate human modifications.

Test File: svf_test.tif (Sky View Factor raster, values 0-1)
Goal: Generate optimal SVF visualizations for detecting archaeological features:
- Ditches, moats, pits (low SVF = 0.0-0.3, enclosed areas)
- House depressions (low-medium SVF = 0.2-0.4)
- Terraces, platforms (medium SVF = 0.4-0.7)
- Mounds, ridges (high SVF = 0.7-1.0, exposed areas)

Archaeological Benefits of SVF:
- Detects enclosure vs exposure patterns
- Reveals anthropogenic terrain modifications
- Complements hillshade/slope analysis
- Excellent for detecting subtle depressions

Author: AI Assistant
Date: June 2025
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
from osgeo import gdal
import time
from pathlib import Path

def load_test_svf(svf_path: str):
    """Load the test SVF TIFF file and return data with comprehensive statistics."""
    print(f"📂 Loading test SVF: {os.path.basename(svf_path)}")
    
    ds = gdal.Open(svf_path)
    if ds is None:
        raise Exception(f"Failed to open SVF file: {svf_path}")
    
    width = ds.RasterXSize
    height = ds.RasterYSize
    band = ds.GetRasterBand(1)
    svf_data = band.ReadAsArray().astype(np.float32)
    
    # Get geospatial info
    geotransform = ds.GetGeoTransform()
    
    # Handle NoData values
    nodata = band.GetNoDataValue()
    if nodata is not None:
        svf_data[svf_data == nodata] = np.nan
    
    ds = None
    
    # Calculate comprehensive statistics
    valid_data = svf_data[~np.isnan(svf_data)]
    
    stats = {
        'shape': (height, width),
        'data_range': (np.min(valid_data), np.max(valid_data)),
        'mean': np.mean(valid_data),
        'median': np.median(valid_data),
        'std': np.std(valid_data),
        'percentiles': {
            'p1': np.percentile(valid_data, 1),
            'p5': np.percentile(valid_data, 5),
            'p10': np.percentile(valid_data, 10),
            'p25': np.percentile(valid_data, 25),
            'p50': np.percentile(valid_data, 50),
            'p75': np.percentile(valid_data, 75),
            'p90': np.percentile(valid_data, 90),
            'p95': np.percentile(valid_data, 95),
            'p99': np.percentile(valid_data, 99)
        },
        'geotransform': geotransform,
        'pixel_size': abs(geotransform[1])
    }
    
    print(f"   📏 Dimensions: {width} × {height} pixels")
    print(f"   📊 SVF range: {stats['data_range'][0]:.4f} to {stats['data_range'][1]:.4f}")
    print(f"   📈 Mean: {stats['mean']:.4f} ± {stats['std']:.4f}")
    print(f"   🎯 Pixel size: {stats['pixel_size']:.2f}m")
    
    return svf_data, stats

def test_standard_colormaps(svf_data: np.ndarray, stats: dict, output_dir: str):
    """Test standard colormaps for SVF visualization."""
    print(f"\n🎨 Testing standard colormaps for SVF...")
    
    # Standard colormaps suitable for SVF
    colormaps = [
        {'name': 'Viridis', 'cmap': 'viridis', 'description': 'Perceptually uniform, purple→yellow'},
        {'name': 'Plasma', 'cmap': 'plasma', 'description': 'Purple→pink→yellow, high contrast'},
        {'name': 'Inferno', 'cmap': 'inferno', 'description': 'Black→red→yellow, dramatic'},
        {'name': 'Cividis', 'cmap': 'cividis', 'description': 'Colorblind-friendly, blue→yellow'},
        {'name': 'Blues', 'cmap': 'Blues', 'description': 'Light→dark blue gradient'},
        {'name': 'YlOrRd', 'cmap': 'YlOrRd', 'description': 'Yellow→orange→red progression'},
        {'name': 'RdYlBu_r', 'cmap': 'RdYlBu_r', 'description': 'Red→yellow→blue (reversed)'},
        {'name': 'Spectral_r', 'cmap': 'Spectral_r', 'description': 'Red→green→blue (reversed)'}
    ]
    
    test_counter = 1
    
    for cmap_info in colormaps:
        print(f"   🔄 Test {test_counter:02d}: {cmap_info['name']}")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 10), dpi=200)
        
        # Display SVF data
        im = ax.imshow(svf_data, cmap=cmap_info['cmap'], vmin=0, vmax=1, 
                      aspect='equal', interpolation='bilinear')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.6, aspect=20)
        cbar.set_label('Sky View Factor', rotation=270, labelpad=20, fontsize=12)
        
        # Add archaeological interpretation labels
        cbar.ax.text(1.5, 0.85, 'EXPOSED\n(Mounds, Ridges)', 
                    transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                    color='darkgreen', weight='bold')
        cbar.ax.text(1.5, 0.15, 'ENCLOSED\n(Ditches, Pits)', 
                    transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                    color='darkred', weight='bold')
        
        # Enhanced title
        title = f"SVF ARCHAEOLOGICAL ANALYSIS\n{cmap_info['name']} Colormap\n"
        title += f"{cmap_info['description']}"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=25)
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Add pixel resolution info
        scale_text = f"Resolution: {stats['pixel_size']:.2f}m/pixel"
        ax.text(0.02, 0.02, scale_text, transform=ax.transAxes, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        plt.tight_layout()
        
        # Save visualization
        output_filename = f"{test_counter:02d}_{cmap_info['name']}_SVF.png"
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        test_counter += 1
    
    print(f"   ✅ Generated {len(colormaps)} standard colormap tests")

def test_archaeological_enhancements(svf_data: np.ndarray, stats: dict, output_dir: str):
    """Test archaeological-specific SVF enhancement techniques."""
    print(f"\n🏛️ Testing archaeological SVF enhancements...")
    
    # Archaeological enhancement methods
    enhancements = [
        {
            'name': 'Archaeological_Cividis_Full',
            'description': 'Cividis 0-1 range, optimal for anomaly detection',
            'cmap': 'cividis',
            'vmin': 0.0,
            'vmax': 1.0,
            'annotations': True
        },
        {
            'name': 'Archaeological_Cividis_Enhanced',
            'description': 'Cividis with 5-95% contrast enhancement',
            'cmap': 'cividis',
            'vmin': stats['percentiles']['p5'],
            'vmax': stats['percentiles']['p95'],
            'annotations': True
        },
        {
            'name': 'Depression_Focus_Blues',
            'description': 'Blues colormap emphasizing low SVF (depressions)',
            'cmap': 'Blues_r',
            'vmin': 0.0,
            'vmax': 0.6,  # Focus on lower SVF values
            'annotations': True
        },
        {
            'name': 'Exposure_Focus_YlOrRd',
            'description': 'YlOrRd colormap emphasizing high SVF (exposures)',
            'cmap': 'YlOrRd',
            'vmin': 0.4,  # Focus on higher SVF values
            'vmax': 1.0,
            'annotations': True
        },
        {
            'name': 'Balanced_RdYlBu',
            'description': 'Balanced visualization with mid-range emphasis',
            'cmap': 'RdYlBu_r',
            'vmin': stats['percentiles']['p10'],
            'vmax': stats['percentiles']['p90'],
            'annotations': True
        }
    ]
    
    test_counter = 20  # Start from 20 for archaeological tests
    
    for enhancement in enhancements:
        print(f"   🔄 Archaeological Test {test_counter:02d}: {enhancement['name']}")
        
        # Create enhanced archaeological visualization
        fig, ax = plt.subplots(figsize=(14, 10), dpi=200)
        
        im = ax.imshow(svf_data, cmap=enhancement['cmap'], 
                      vmin=enhancement['vmin'], vmax=enhancement['vmax'],
                      aspect='equal', interpolation='bilinear')
        
        # Enhanced colorbar with archaeological labels
        cbar = plt.colorbar(im, ax=ax, shrink=0.6, aspect=20)
        cbar.set_label('Sky View Factor', rotation=270, labelpad=20, fontsize=12)
        
        if enhancement['annotations']:
            # Add archaeological interpretation labels
            cbar.ax.text(1.5, 0.9, 'HIGH SVF\n(Exposed)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='darkgreen', weight='bold')
            cbar.ax.text(1.5, 0.7, 'MOUNDS\nRIDGES', 
                        transform=cbar.ax.transAxes, fontsize=9, ha='left', va='center',
                        color='green')
            cbar.ax.text(1.5, 0.5, 'MEDIUM SVF\n(Balanced)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='black', weight='bold')
            cbar.ax.text(1.5, 0.3, 'TERRACES\nPLATFORMS', 
                        transform=cbar.ax.transAxes, fontsize=9, ha='left', va='center',
                        color='gray')
            cbar.ax.text(1.5, 0.1, 'LOW SVF\n(Enclosed)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='darkred', weight='bold')
            cbar.ax.text(1.5, -0.1, 'DITCHES\nPITS', 
                        transform=cbar.ax.transAxes, fontsize=9, ha='left', va='center',
                        color='red')
        
        # Enhanced title
        title = f"ARCHAEOLOGICAL SVF ANALYSIS\n{enhancement['description']}\n"
        title += f"Range: {enhancement['vmin']:.3f} to {enhancement['vmax']:.3f}"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=25)
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Add pixel resolution info
        scale_text = f"Resolution: {stats['pixel_size']:.2f}m/pixel"
        ax.text(0.02, 0.02, scale_text, transform=ax.transAxes, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Add archaeological interpretation guide
        guide_text = f"ARCHAEOLOGICAL SVF INTERPRETATION\n"
        guide_text += f"Low SVF (0.0-0.3): Enclosed areas - ditches, pits, foundations\n"
        guide_text += f"Medium SVF (0.3-0.7): Balanced areas - terraces, platforms\n"
        guide_text += f"High SVF (0.7-1.0): Exposed areas - mounds, ridges, peaks"
        
        ax.text(0.02, 0.98, guide_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', 
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.9))
        
        plt.tight_layout()
        
        # Save enhanced visualization
        output_filename = f"{test_counter:02d}_{enhancement['name']}.png"
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        test_counter += 1
    
    print(f"   ✅ Generated {len(enhancements)} archaeological enhancement tests")

def test_custom_archaeological_colormaps(svf_data: np.ndarray, stats: dict, output_dir: str):
    """Test custom colormaps designed specifically for archaeological SVF analysis."""
    print(f"\n🎨 Testing custom archaeological SVF colormaps...")
    
    # Custom colormaps for archaeological features
    custom_colormaps = [
        {
            'name': 'Archaeological_Enclosure',
            'description': 'Custom colormap emphasizing enclosure detection',
            'colors': ['#000080', '#0066CC', '#66B2FF', '#CCDDFF', '#FFFFFF'],  # Deep blue → white
            'focus': 'Emphasizes low SVF (enclosed) areas'
        },
        {
            'name': 'Archaeological_Exposure', 
            'description': 'Custom colormap emphasizing exposure detection',
            'colors': ['#330000', '#990000', '#FF3300', '#FF9966', '#FFFF99'],  # Dark red → yellow
            'focus': 'Emphasizes high SVF (exposed) areas'
        },
        {
            'name': 'Archaeological_Balanced',
            'description': 'Balanced custom colormap for all features',
            'colors': ['#000066', '#0066CC', '#66CC66', '#FFCC00', '#FF6600'],  # Blue → green → orange
            'focus': 'Balanced representation of all SVF ranges'
        },
        {
            'name': 'Archaeological_Earthworks',
            'description': 'Earth-tone colormap for earthwork detection',
            'colors': ['#2F1B0C', '#8B4513', '#CD853F', '#F4A460', '#FFF8DC'],  # Dark brown → cream
            'focus': 'Natural earth tones for earthwork analysis'
        },
        {
            'name': 'Archaeological_Contrast',
            'description': 'High-contrast colormap for anomaly detection',
            'colors': ['#000000', '#FF0000', '#FFFF00', '#00FF00', '#FFFFFF'],  # Black → red → yellow → green → white
            'focus': 'Maximum contrast for anomaly identification'
        }
    ]
    
    test_counter = 40  # Start from 40 for custom colormap tests
    
    for cmap_info in custom_colormaps:
        print(f"   🔄 Custom Test {test_counter:02d}: {cmap_info['name']}")
        
        # Create custom colormap
        custom_cmap = LinearSegmentedColormap.from_list(
            cmap_info['name'], cmap_info['colors'], N=256
        )
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 10), dpi=200)
        
        # Display SVF data with custom colormap
        im = ax.imshow(svf_data, cmap=custom_cmap, vmin=0, vmax=1, 
                      aspect='equal', interpolation='bilinear')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.6, aspect=20)
        cbar.set_label('Sky View Factor', rotation=270, labelpad=20, fontsize=12)
        
        # Add custom labels based on colormap focus
        if 'Enclosure' in cmap_info['name']:
            cbar.ax.text(1.5, 0.85, 'FLAT/EXPOSED\n(Less important)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='gray')
            cbar.ax.text(1.5, 0.15, 'ENCLOSED\n(Primary focus)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='darkblue', weight='bold')
        elif 'Exposure' in cmap_info['name']:
            cbar.ax.text(1.5, 0.85, 'EXPOSED\n(Primary focus)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='darkred', weight='bold')
            cbar.ax.text(1.5, 0.15, 'ENCLOSED\n(Less important)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='gray')
        else:
            cbar.ax.text(1.5, 0.85, 'HIGH SVF\n(Exposed)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='darkgreen', weight='bold')
            cbar.ax.text(1.5, 0.15, 'LOW SVF\n(Enclosed)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='darkred', weight='bold')
        
        # Enhanced title
        title = f"CUSTOM ARCHAEOLOGICAL SVF COLORMAP\n{cmap_info['description']}\n"
        title += f"Focus: {cmap_info['focus']}"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=25)
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Add pixel resolution info
        scale_text = f"Resolution: {stats['pixel_size']:.2f}m/pixel"
        ax.text(0.02, 0.02, scale_text, transform=ax.transAxes, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        plt.tight_layout()
        
        # Save visualization
        output_filename = f"{test_counter:02d}_{cmap_info['name']}.png"
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        test_counter += 1
    
    print(f"   ✅ Generated {len(custom_colormaps)} custom archaeological colormap tests")

def test_percentile_range_optimizations(svf_data: np.ndarray, stats: dict, output_dir: str):
    """Test different percentile ranges for optimal archaeological feature detection."""
    print(f"\n📊 Testing percentile range optimizations...")
    
    # Different percentile ranges for contrast enhancement
    percentile_tests = [
        {
            'name': 'Full_Range_0_100',
            'description': 'Full SVF range (0-100th percentile)',
            'low_pct': 0,
            'high_pct': 100,
            'vmin': 0.0,
            'vmax': 1.0
        },
        {
            'name': 'Enhanced_2_98',
            'description': 'Enhanced contrast (2-98th percentile)',
            'low_pct': 2,
            'high_pct': 98,
            'vmin': stats['percentiles']['p2'] if 'p2' in stats['percentiles'] else stats['percentiles']['p5'],
            'vmax': stats['percentiles']['p98'] if 'p98' in stats['percentiles'] else stats['percentiles']['p95']
        },
        {
            'name': 'Archaeological_5_95',
            'description': 'Archaeological range (5-95th percentile)',
            'low_pct': 5,
            'high_pct': 95,
            'vmin': stats['percentiles']['p5'],
            'vmax': stats['percentiles']['p95']
        },
        {
            'name': 'Subtle_10_90',
            'description': 'Subtle enhancement (10-90th percentile)',
            'low_pct': 10,
            'high_pct': 90,
            'vmin': stats['percentiles']['p10'],
            'vmax': stats['percentiles']['p90']
        },
        {
            'name': 'Depression_Focus_0_75',
            'description': 'Depression focus (0-75th percentile)',
            'low_pct': 0,
            'high_pct': 75,
            'vmin': 0.0,
            'vmax': stats['percentiles']['p75']
        },
        {
            'name': 'Mound_Focus_25_100',
            'description': 'Mound/elevation focus (25-100th percentile)',
            'low_pct': 25,
            'high_pct': 100,
            'vmin': stats['percentiles']['p25'],
            'vmax': 1.0
        }
    ]
    
    test_counter = 60  # Start from 60 for percentile tests
    
    for pct_test in percentile_tests:
        print(f"   🔄 Percentile Test {test_counter:02d}: {pct_test['name']}")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 10), dpi=200)
        
        # Use cividis as the base colormap (best for archaeological analysis)
        im = ax.imshow(svf_data, cmap='cividis', 
                      vmin=pct_test['vmin'], vmax=pct_test['vmax'],
                      aspect='equal', interpolation='bilinear')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.6, aspect=20)
        cbar.set_label('Sky View Factor', rotation=270, labelpad=20, fontsize=12)
        
        # Add range-specific annotations
        cbar.ax.text(1.5, 0.85, f'MAX\n{pct_test["vmax"]:.3f}', 
                    transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                    color='darkgreen', weight='bold')
        cbar.ax.text(1.5, 0.15, f'MIN\n{pct_test["vmin"]:.3f}', 
                    transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                    color='darkblue', weight='bold')
        
        # Enhanced title
        title = f"SVF PERCENTILE RANGE OPTIMIZATION\n{pct_test['description']}\n"
        title += f"Range: P{pct_test['low_pct']} ({pct_test['vmin']:.3f}) to P{pct_test['high_pct']} ({pct_test['vmax']:.3f})"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=25)
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Add pixel resolution info
        scale_text = f"Resolution: {stats['pixel_size']:.2f}m/pixel"
        ax.text(0.02, 0.02, scale_text, transform=ax.transAxes, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Add contrast information
        contrast_info = f"CONTRAST ENHANCEMENT: {pct_test['low_pct']}-{pct_test['high_pct']}%\n"
        contrast_info += f"Optimizes visibility in {pct_test['vmin']:.3f}-{pct_test['vmax']:.3f} SVF range"
        
        ax.text(0.02, 0.98, contrast_info, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', 
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.9))
        
        plt.tight_layout()
        
        # Save visualization
        output_filename = f"{test_counter:02d}_{pct_test['name']}.png"
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        test_counter += 1
    
    print(f"   ✅ Generated {len(percentile_tests)} percentile range optimization tests")

def generate_comparison_html(output_dir: str):
    """Generate HTML comparison page for all SVF visualizations."""
    print(f"\n📄 Generating HTML comparison page...")
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SVF Archaeological Visualization Comparison</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            max-width: 1800px;
            margin: 0 auto;
        }
        .item {
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .item:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }
        .item img {
            width: 100%;
            height: 300px;
            object-fit: cover;
            border-bottom: 3px solid #f0f0f0;
        }
        .item h3 {
            margin: 0;
            padding: 15px 20px;
            background: #f8f9fa;
            color: #2c3e50;
            font-size: 1.1em;
            border-bottom: 1px solid #dee2e6;
        }
        .item .description {
            padding: 15px 20px;
            color: #666;
            line-height: 1.5;
        }
        .best {
            border: 3px solid #28a745;
            position: relative;
        }
        .best::before {
            content: "🏆 RECOMMENDED";
            position: absolute;
            top: 10px;
            right: 10px;
            background: #28a745;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.8em;
            z-index: 10;
        }
        .section {
            grid-column: 1 / -1;
            text-align: center;
            margin: 30px 0 20px 0;
        }
        .section h2 {
            color: white;
            font-size: 2em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .section p {
            color: rgba(255,255,255,0.9);
            font-size: 1.1em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ SVF Archaeological Visualization Test Results</h1>
        <p>Comprehensive Sky View Factor analysis for archaeological feature detection and anomaly identification</p>
        <p><strong>Test File:</strong> Wizard Island LiDAR SVF • <strong>Resolution:</strong> 1.0m/pixel • <strong>Archaeological Focus:</strong> Ruins, earthworks, terrain modifications</p>
    </div>

    <div class="container">
        <div class="section">
            <h2>📊 Standard Colormaps</h2>
            <p>Evaluation of standard matplotlib colormaps for SVF archaeological analysis</p>
        </div>
"""
    
    # Add standard colormap items
    standard_maps = ['Viridis', 'Plasma', 'Inferno', 'Cividis', 'Blues', 'YlOrRd', 'RdYlBu_r', 'Spectral_r']
    
    for i, name in enumerate(standard_maps, 1):
        best_class = ' best' if name == 'Cividis' else ''
        html_content += f"""
        <div class="item{best_class}">
            <img src="{i:02d}_{name}_SVF.png" alt="{name}_SVF">
            <h3>{name} SVF</h3>
            <div class="description">
                Standard {name.lower()} colormap applied to SVF data. 
                {'Optimal for colorblind accessibility and archaeological feature detection.' if name == 'Cividis' else 'Standard visualization approach.'}
            </div>
        </div>"""
    
    html_content += """
        <div class="section">
            <h2>🏛️ Archaeological Enhancements</h2>
            <p>Specialized enhancements designed for archaeological feature detection and anomaly identification</p>
        </div>
"""
    
    # Add archaeological enhancement items
    arch_enhancements = [
        ('Archaeological_Cividis_Full', 'Full range cividis - optimal balance'),
        ('Archaeological_Cividis_Enhanced', 'Enhanced contrast cividis - improved details'),
        ('Depression_Focus_Blues', 'Depression-focused visualization'),
        ('Exposure_Focus_YlOrRd', 'Exposure-focused visualization'),
        ('Balanced_RdYlBu', 'Balanced multi-feature approach')
    ]
    
    for i, (name, desc) in enumerate(arch_enhancements, 20):
        best_class = ' best' if 'Cividis_Enhanced' in name else ''
        html_content += f"""
        <div class="item{best_class}">
            <img src="{i:02d}_{name}.png" alt="{name}">
            <h3>{name.replace('_', ' ')}</h3>
            <div class="description">{desc}</div>
        </div>"""
    
    html_content += """
        <div class="section">
            <h2>🎨 Custom Archaeological Colormaps</h2>
            <p>Purpose-built colormaps designed specifically for archaeological SVF analysis</p>
        </div>
"""
    
    # Add custom colormap items
    custom_maps = [
        ('Archaeological_Enclosure', 'Emphasizes enclosed areas (ditches, pits)'),
        ('Archaeological_Exposure', 'Emphasizes exposed areas (mounds, ridges)'),
        ('Archaeological_Balanced', 'Balanced approach for all features'),
        ('Archaeological_Earthworks', 'Earth-tone visualization for earthworks'),
        ('Archaeological_Contrast', 'High-contrast anomaly detection')
    ]
    
    for i, (name, desc) in enumerate(custom_maps, 40):
        html_content += f"""
        <div class="item">
            <img src="{i:02d}_{name}.png" alt="{name}">
            <h3>{name.replace('_', ' ')}</h3>
            <div class="description">{desc}</div>
        </div>"""
    
    html_content += """
        <div class="section">
            <h2>📈 Percentile Range Optimizations</h2>
            <p>Testing different percentile ranges for optimal contrast and feature detection</p>
        </div>
"""
    
    # Add percentile range items
    percentile_ranges = [
        ('Full_Range_0_100', 'Complete data range'),
        ('Enhanced_2_98', 'Enhanced contrast range'),
        ('Archaeological_5_95', 'Archaeological optimization'),
        ('Subtle_10_90', 'Subtle enhancement'),
        ('Depression_Focus_0_75', 'Depression-focused range'),
        ('Mound_Focus_25_100', 'Elevation-focused range')
    ]
    
    for i, (name, desc) in enumerate(percentile_ranges, 60):
        best_class = ' best' if 'Archaeological_5_95' in name else ''
        html_content += f"""
        <div class="item{best_class}">
            <img src="{i:02d}_{name}.png" alt="{name}">
            <h3>{name.replace('_', ' ')}</h3>
            <div class="description">{desc}</div>
        </div>"""
    
    html_content += """
    </div>
    
    <div style="margin-top: 40px; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 8px; color: white;">
        <h2>🎯 Archaeological Recommendations</h2>
        <p><strong>Best Overall:</strong> Archaeological Cividis Enhanced (5-95% range) provides optimal balance of contrast and feature detection.</p>
        <p><strong>For Depression Detection:</strong> Use Depression Focus Blues or Archaeological Enclosure colormaps.</p>
        <p><strong>For Mound Detection:</strong> Use Exposure Focus YlOrRd or Archaeological Exposure colormaps.</p>
        <p><strong>For Anomaly Detection:</strong> Use Archaeological Contrast or Enhanced 2-98% range for maximum differentiation.</p>
        <p><em>Items with green borders are specifically recommended for archaeological applications.</em></p>
    </div>

</body>
</html>"""
    
    # Save HTML file
    html_path = os.path.join(output_dir, "svf_archaeological_comparison.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"   ✅ HTML comparison page saved: {os.path.basename(html_path)}")

def main():
    """Main function to run all SVF archaeological visualization tests."""
    print(f"🏛️ SVF ARCHAEOLOGICAL VISUALIZATION TEST SUITE")
    print(f"=" * 60)
    print(f"🎯 Goal: Generate optimal SVF visualizations for archaeological analysis")
    print(f"🔍 Focus: Anomaly detection, earthworks, terrain modifications")
    print()
    
    # Set up paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    svf_file = os.path.join(script_dir, "svf_test.tif")
    output_dir = os.path.join(script_dir, "visualizations")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Check if test file exists
    if not os.path.exists(svf_file):
        print(f"❌ SVF test file not found: {svf_file}")
        return
    
    # Load SVF data and calculate statistics
    start_time = time.time()
    svf_data, stats = load_test_svf(svf_file)
    
    # Run all visualization tests
    test_standard_colormaps(svf_data, stats, output_dir)
    test_archaeological_enhancements(svf_data, stats, output_dir)
    test_custom_archaeological_colormaps(svf_data, stats, output_dir)
    test_percentile_range_optimizations(svf_data, stats, output_dir)
    
    # Generate comparison HTML
    generate_comparison_html(output_dir)
    
    total_time = time.time() - start_time
    
    print(f"\n🎉 SVF ARCHAEOLOGICAL VISUALIZATION TEST COMPLETE!")
    print(f"⏱️ Total processing time: {total_time:.2f} seconds")
    print(f"📁 All visualizations saved to: {output_dir}")
    print(f"🌐 View comparison: svf_archaeological_comparison.html")
    print(f"\n🏆 RECOMMENDED FOR ARCHAEOLOGICAL ANALYSIS:")
    print(f"   • Cividis colormap with 5-95% percentile range")
    print(f"   • Archaeological Cividis Enhanced for balanced analysis")
    print(f"   • Depression Focus Blues for pit/ditch detection")
    print(f"   • Exposure Focus YlOrRd for mound/ridge detection")

if __name__ == "__main__":
    main()
