#!/usr/bin/env python3
"""
Best LRM Visualization Test
===========================

This script tests different LRM visualization techniques to find the optimal
approach for archaeological terrain analysis. It processes the test LRM file
with various colormaps, normalization methods, and enhancement techniques.

Test File: OR_WizardIsland_LRM_adaptive.tif
Goal: Generate the best possible LRM visualization for archaeological analysis

Author: AI Assistant
Date: January 2025
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

def load_test_lrm(lrm_path: str):
    """Load the test LRM TIFF file and return data with statistics."""
    print(f"📂 Loading test LRM: {os.path.basename(lrm_path)}")
    
    ds = gdal.Open(lrm_path)
    if ds is None:
        raise Exception(f"Failed to open LRM file: {lrm_path}")
    
    band = ds.GetRasterBand(1)
    lrm_data = band.ReadAsArray()
    
    # Get geospatial info
    geotransform = ds.GetGeoTransform()
    width = ds.RasterXSize
    height = ds.RasterYSize
    
    ds = None
    band = None
    
    # Handle NoData values
    nodata_mask = lrm_data == -9999
    lrm_data[nodata_mask] = np.nan
    
    # Calculate comprehensive statistics
    valid_data = lrm_data[~np.isnan(lrm_data)]
    
    stats = {
        'shape': (height, width),
        'valid_pixels': len(valid_data),
        'total_pixels': height * width,
        'nodata_pixels': np.sum(nodata_mask),
        'min': np.min(valid_data),
        'max': np.max(valid_data),
        'mean': np.mean(valid_data),
        'median': np.median(valid_data),
        'std': np.std(valid_data),
        'percentiles': {
            'p1': np.percentile(valid_data, 1),
            'p2': np.percentile(valid_data, 2),
            'p5': np.percentile(valid_data, 5),
            'p10': np.percentile(valid_data, 10),
            'p25': np.percentile(valid_data, 25),
            'p75': np.percentile(valid_data, 75),
            'p90': np.percentile(valid_data, 90),
            'p95': np.percentile(valid_data, 95),
            'p98': np.percentile(valid_data, 98),
            'p99': np.percentile(valid_data, 99)
        },
        'geotransform': geotransform
    }
    
    print(f"   📏 Dimensions: {width} × {height} pixels")
    print(f"   🔢 Valid pixels: {stats['valid_pixels']:,} ({100*stats['valid_pixels']/stats['total_pixels']:.1f}%)")
    print(f"   📊 Range: {stats['min']:.3f} to {stats['max']:.3f} meters")
    print(f"   📈 Mean: {stats['mean']:.3f} ± {stats['std']:.3f} meters")
    print(f"   📊 Median: {stats['median']:.3f} meters")
    
    return lrm_data, stats

def test_colormap_variations(lrm_data: np.ndarray, stats: dict, output_dir: str):
    """Test different colormap approaches for LRM visualization."""
    print(f"\n🎨 Testing colormap variations...")
    
    # Define test colormaps
    colormaps = {
        'coolwarm': {
            'cmap': 'coolwarm',
            'type': 'diverging',
            'description': 'Blue-White-Red diverging (archaeological standard)',
            'normalize': 'symmetric'
        },
        'RdBu_r': {
            'cmap': 'RdBu_r', 
            'type': 'diverging',
            'description': 'Red-Blue diverging (reversed)',
            'normalize': 'symmetric'
        },
        'seismic': {
            'cmap': 'seismic',
            'type': 'diverging', 
            'description': 'Red-White-Blue seismic',
            'normalize': 'symmetric'
        },
        'viridis': {
            'cmap': 'viridis',
            'type': 'sequential',
            'description': 'Viridis sequential (perceptually uniform)',
            'normalize': 'minmax'
        },
        'terrain': {
            'cmap': 'terrain',
            'type': 'sequential',
            'description': 'Terrain-like colors',
            'normalize': 'minmax'
        },
        'RdYlBu_r': {
            'cmap': 'RdYlBu_r',
            'type': 'diverging',
            'description': 'Red-Yellow-Blue diverging (reversed)',
            'normalize': 'symmetric'
        }
    }
    
    # Test different normalization approaches
    normalizations = {
        'p2_p98': (stats['percentiles']['p2'], stats['percentiles']['p98']),
        'p5_p95': (stats['percentiles']['p5'], stats['percentiles']['p95']),
        'p10_p90': (stats['percentiles']['p10'], stats['percentiles']['p90']),
        'minmax': (stats['min'], stats['max']),
        'std2': (stats['mean'] - 2*stats['std'], stats['mean'] + 2*stats['std']),
        'std3': (stats['mean'] - 3*stats['std'], stats['mean'] + 3*stats['std'])
    }
    
    test_counter = 1
    
    for norm_name, (vmin, vmax) in normalizations.items():
        for cmap_name, cmap_info in colormaps.items():
            print(f"   🔄 Test {test_counter:02d}: {cmap_name} + {norm_name}")
            
            # Prepare data based on normalization type
            if cmap_info['normalize'] == 'symmetric':
                # For diverging colormaps, ensure symmetric range around zero
                max_abs = max(abs(vmin), abs(vmax))
                clip_min, clip_max = -max_abs, max_abs
                lrm_clipped = np.clip(lrm_data, clip_min, clip_max)
                if max_abs > 0:
                    lrm_normalized = lrm_clipped / max_abs
                    vmin_plot, vmax_plot = -1, 1
                else:
                    lrm_normalized = lrm_clipped
                    vmin_plot, vmax_plot = vmin, vmax
            else:
                # For sequential colormaps, use direct clipping
                lrm_normalized = np.clip(lrm_data, vmin, vmax)
                vmin_plot, vmax_plot = vmin, vmax
            
            # Create visualization
            fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
            
            im = ax.imshow(lrm_normalized, cmap=cmap_info['cmap'], 
                          vmin=vmin_plot, vmax=vmax_plot, interpolation='bilinear')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax, shrink=0.6)
            cbar.set_label('Local Relief (m)', rotation=270, labelpad=15)
            
            # Add title with parameters
            title = f"{cmap_name.upper()} + {norm_name.upper()}\n"
            title += f"{cmap_info['description']}\n"
            title += f"Range: {vmin:.3f} to {vmax:.3f}m"
            ax.set_title(title, fontsize=11, pad=15)
            
            # Remove axes
            ax.set_xticks([])
            ax.set_yticks([])
            
            # Add test info
            info_text = f"Test {test_counter:02d}: Archaeological LRM Analysis"
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
                   fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
            
            # Save figure
            output_filename = f"{test_counter:02d}_{cmap_name}_{norm_name}.png"
            output_path = os.path.join(output_dir, output_filename)
            plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            test_counter += 1
    
    print(f"   ✅ Generated {test_counter-1} test visualizations")

def test_archaeological_enhancements(lrm_data: np.ndarray, stats: dict, output_dir: str):
    """Test archaeological-specific enhancement techniques."""
    print(f"\n🏛️ Testing archaeological enhancement techniques...")
    
    # Test coolwarm with different archaeological interpretations
    enhancements = [
        {
            'name': 'Archaeological_Standard',
            'description': 'Standard coolwarm with 2%-98% clipping',
            'percentiles': (2, 98),
            'cmap': 'coolwarm',
            'annotations': True
        },
        {
            'name': 'Archaeological_Conservative', 
            'description': 'Conservative coolwarm with 5%-95% clipping',
            'percentiles': (5, 95),
            'cmap': 'coolwarm',
            'annotations': True
        },
        {
            'name': 'Archaeological_Aggressive',
            'description': 'Aggressive coolwarm with 1%-99% clipping',
            'percentiles': (1, 99),
            'cmap': 'coolwarm',
            'annotations': True
        },
        {
            'name': 'Archaeological_Subtle',
            'description': 'Subtle coolwarm with 10%-90% clipping',
            'percentiles': (10, 90),
            'cmap': 'coolwarm', 
            'annotations': True
        }
    ]
    
    test_counter = 50  # Start from 50 to differentiate from colormap tests
    
    for enhancement in enhancements:
        print(f"   🔄 Archaeological Test {test_counter:02d}: {enhancement['name']}")
        
        # Apply percentile clipping
        p_min = np.percentile(lrm_data[~np.isnan(lrm_data)], enhancement['percentiles'][0])
        p_max = np.percentile(lrm_data[~np.isnan(lrm_data)], enhancement['percentiles'][1])
        
        # Symmetric clipping for diverging colormap
        max_abs = max(abs(p_min), abs(p_max))
        lrm_clipped = np.clip(lrm_data, -max_abs, max_abs)
        
        # Normalize to [-1, 1]
        if max_abs > 0:
            lrm_normalized = lrm_clipped / max_abs
        else:
            lrm_normalized = lrm_clipped
        
        # Create enhanced archaeological visualization
        fig, ax = plt.subplots(figsize=(14, 10), dpi=200)
        
        im = ax.imshow(lrm_normalized, cmap=enhancement['cmap'], vmin=-1, vmax=1, 
                      interpolation='bilinear')
        
        # Enhanced colorbar with archaeological labels
        cbar = plt.colorbar(im, ax=ax, shrink=0.6, aspect=20)
        cbar.set_label('Local Relief (normalized)', rotation=270, labelpad=20, fontsize=12)
        
        if enhancement['annotations']:
            # Add archaeological interpretation labels
            cbar.ax.text(1.5, 0.85, 'ELEVATED\n(Mounds, Ridges,\nEarthworks)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='darkred', weight='bold')
            cbar.ax.text(1.5, 0.15, 'DEPRESSED\n(Ditches, Pits,\nFoundations)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='darkblue', weight='bold')
            cbar.ax.text(1.5, 0.5, 'NEUTRAL\n(Natural Terrain)', 
                        transform=cbar.ax.transAxes, fontsize=10, ha='left', va='center',
                        color='black', weight='bold')
        
        # Enhanced title
        title = f"ARCHAEOLOGICAL LRM ANALYSIS\n{enhancement['description']}\n"
        title += f"Percentile Range: {enhancement['percentiles'][0]}%-{enhancement['percentiles'][1]}%"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=25)
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Add pixel resolution info
        geotransform = stats['geotransform']
        pixel_width = abs(geotransform[1])
        scale_text = f"Resolution: {pixel_width:.2f}m/pixel"
        ax.text(0.02, 0.02, scale_text, transform=ax.transAxes, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Add archaeological interpretation guide
        guide_text = "ARCHAEOLOGICAL INTERPRETATION GUIDE\n"
        guide_text += "🔴 Red Areas: Potential elevated features\n"
        guide_text += "🔵 Blue Areas: Potential buried/cut features\n"
        guide_text += "⚪ White Areas: Natural undisturbed terrain"
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

def analyze_best_practices(stats: dict):
    """Analyze the LRM data and recommend best practices."""
    print(f"\n📊 LRM Analysis & Best Practices Recommendations:")
    print(f"{'='*60}")
    
    # Data characteristics analysis
    print(f"📈 DATA CHARACTERISTICS:")
    print(f"   🔢 Value range: {stats['min']:.3f} to {stats['max']:.3f} meters")
    print(f"   📊 Standard deviation: {stats['std']:.3f} meters")
    print(f"   📊 Mean: {stats['mean']:.3f} meters")
    
    # Determine if data is well-centered around zero
    mean_offset = abs(stats['mean'])
    if mean_offset < 0.1 * stats['std']:
        print(f"   ✅ Data well-centered around zero (offset: {mean_offset:.3f}m)")
        print(f"   🎯 RECOMMENDATION: Use diverging colormaps (coolwarm, RdBu)")
    else:
        print(f"   ⚠️ Data offset from zero (offset: {mean_offset:.3f}m)")
        print(f"   🎯 RECOMMENDATION: Consider data centering or sequential colormaps")
    
    # Percentile analysis for clipping recommendations
    print(f"\n📊 PERCENTILE ANALYSIS:")
    for p in [1, 2, 5, 10]:
        pval = stats['percentiles'][f'p{p}']
        print(f"   {p:2d}%: {pval:8.3f}m")
    print(f"   Mean: {stats['mean']:8.3f}m")
    for p in [90, 95, 98, 99]:
        pval = stats['percentiles'][f'p{p}']
        print(f"   {p:2d}%: {pval:8.3f}m")
    
    # Clipping recommendations
    p2_range = stats['percentiles']['p98'] - stats['percentiles']['p2']
    p5_range = stats['percentiles']['p95'] - stats['percentiles']['p5']
    full_range = stats['max'] - stats['min']
    
    print(f"\n🎯 CLIPPING RECOMMENDATIONS:")
    print(f"   📊 2%-98% range: {p2_range:.3f}m ({100*p2_range/full_range:.1f}% of full range)")
    print(f"   📊 5%-95% range: {p5_range:.3f}m ({100*p5_range/full_range:.1f}% of full range)")
    
    if p2_range / full_range > 0.8:
        print(f"   ✅ RECOMMENDED: 2%-98% percentile clipping (good data distribution)")
    elif p5_range / full_range > 0.7:
        print(f"   ✅ RECOMMENDED: 5%-95% percentile clipping (some outliers present)")
    else:
        print(f"   ⚠️ RECOMMENDED: 10%-90% percentile clipping (many outliers present)")
    
    # Archaeological interpretation recommendations
    print(f"\n🏛️ ARCHAEOLOGICAL INTERPRETATION:")
    print(f"   🔴 Positive values (Red): Elevated terrain, potential mounds, ridges, earthworks")
    print(f"   🔵 Negative values (Blue): Depressions, potential ditches, pits, foundations")
    print(f"   ⚪ Near-zero values (White): Natural undisturbed terrain")
    print(f"   🎯 Feature scale: {abs(stats['geotransform'][1]):.2f}m pixel resolution")
    
    # Final recommendations
    print(f"\n🌟 FINAL RECOMMENDATIONS:")
    print(f"   🎨 Colormap: Coolwarm diverging (blue-white-red)")
    print(f"   📊 Normalization: 2%-98% percentile clipping with symmetric scaling")
    print(f"   🔧 Range: Normalize to [-1, 1] for optimal contrast")
    print(f"   📏 Resolution: {abs(stats['geotransform'][1]):.2f}m/pixel suitable for archaeological features")
    print(f"   💾 Output: High-resolution PNG (200-300 DPI) for detailed analysis")

def main():
    """Main function to run all LRM visualization tests."""
    print(f"🌄 LRM Visualization Testing Suite")
    print(f"=" * 50)
    
    # Setup paths
    lrm_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/LRM/OR_WizardIsland_LRM_adaptive.tif"
    output_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/LRM/visualizations"
    
    # Verify input file exists
    if not os.path.exists(lrm_path):
        print(f"❌ Test file not found: {lrm_path}")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    start_time = time.time()
    
    try:
        # Load and analyze test data
        lrm_data, stats = load_test_lrm(lrm_path)
        
        # Run colormap variation tests
        test_colormap_variations(lrm_data, stats, output_dir)
        
        # Run archaeological enhancement tests  
        test_archaeological_enhancements(lrm_data, stats, output_dir)
        
        # Analyze and recommend best practices
        analyze_best_practices(stats)
        
        # Summary
        total_time = time.time() - start_time
        print(f"\n✅ LRM visualization testing completed!")
        print(f"⏱️ Total time: {total_time:.2f} seconds")
        print(f"📁 Results saved to: {output_dir}")
        print(f"🎯 Review the archaeological enhancement tests (50+) for optimal results")
        
    except Exception as e:
        print(f"❌ Testing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
