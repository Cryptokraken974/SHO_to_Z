#!/usr/bin/env python3
"""
Best Hillshade RGB Visualization Test
=====================================

This script tests different RGB hillshade visualization techniques to find the optimal
approaches for archaeological terrain analysis. Unlike single-band rasters, RGB composites
offer unique visualization opportunities through channel manipulation.

Test File: hillshade_rgb.tif (3-band RGB composite)
Goal: Generate the best possible RGB hillshade visualizations for archaeological analysis

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

def load_test_hillshade_rgb(rgb_path: str):
    """Load the test Hillshade RGB TIFF file and return data with statistics."""
    print(f"📂 Loading test Hillshade RGB: {os.path.basename(rgb_path)}")
    
    ds = gdal.Open(rgb_path)
    if ds is None:
        raise Exception(f"Failed to open Hillshade RGB file: {rgb_path}")
    
    width = ds.RasterXSize
    height = ds.RasterYSize
    num_bands = ds.RasterCount
    
    # Get geospatial info
    geotransform = ds.GetGeoTransform()
    
    # Read RGB bands
    red_band = ds.GetRasterBand(1).ReadAsArray()
    green_band = ds.GetRasterBand(2).ReadAsArray()
    blue_band = ds.GetRasterBand(3).ReadAsArray()
    
    ds = None
    
    # Calculate comprehensive statistics for each band
    bands_data = {
        'red': red_band,
        'green': green_band,
        'blue': blue_band
    }
    
    stats = {
        'shape': (height, width),
        'num_bands': num_bands,
        'bands': {},
        'geotransform': geotransform
    }
    
    for band_name, band_data in bands_data.items():
        band_stats = {
            'min': np.min(band_data),
            'max': np.max(band_data),
            'mean': np.mean(band_data),
            'median': np.median(band_data),
            'std': np.std(band_data),
            'percentiles': {
                'p1': np.percentile(band_data, 1),
                'p5': np.percentile(band_data, 5),
                'p25': np.percentile(band_data, 25),
                'p75': np.percentile(band_data, 75),
                'p95': np.percentile(band_data, 95),
                'p99': np.percentile(band_data, 99)
            }
        }
        stats['bands'][band_name] = band_stats
    
    print(f"   📏 Dimensions: {width} × {height} pixels")
    print(f"   🎨 Bands: {num_bands} (RGB composite)")
    
    for band_name, band_stats in stats['bands'].items():
        color_emoji = "🔴" if band_name == "red" else "🟢" if band_name == "green" else "🔵"
        print(f"   {color_emoji} {band_name.capitalize()}: {band_stats['min']}-{band_stats['max']}, "
              f"mean {band_stats['mean']:.1f} ± {band_stats['std']:.1f}")
    
    return bands_data, stats

def test_rgb_enhancement_methods(bands_data: dict, stats: dict, output_dir: str):
    """Test different RGB enhancement and manipulation methods."""
    print(f"\n🎨 Testing RGB enhancement methods...")
    
    red_band = bands_data['red']
    green_band = bands_data['green']
    blue_band = bands_data['blue']
    
    # Define enhancement methods
    enhancements = {
        'original': {
            'name': 'Original_RGB',
            'description': 'Original RGB composite (no enhancement)',
            'method': 'original'
        },
        'contrast_stretch': {
            'name': 'Contrast_Stretched',
            'description': 'Per-band contrast stretching (2%-98%)',
            'method': 'contrast_stretch'
        },
        'histogram_eq': {
            'name': 'Histogram_Equalized',
            'description': 'Per-band histogram equalization',
            'method': 'histogram_eq'
        },
        'gamma_correction': {
            'name': 'Gamma_Corrected',
            'description': 'Gamma correction (γ=0.8) for shadow enhancement',
            'method': 'gamma_correction'
        },
        'adaptive_histogram': {
            'name': 'Adaptive_Enhanced',
            'description': 'Adaptive histogram enhancement',
            'method': 'adaptive_histogram'
        },
        'archaeological_enhance': {
            'name': 'Archaeological_Enhanced',
            'description': 'Archaeological-optimized enhancement',
            'method': 'archaeological_enhance'
        }
    }
    
    test_counter = 1
    
    for enhancement_key, enhancement in enhancements.items():
        print(f"   🔄 Test {test_counter:02d}: {enhancement['name']}")
        
        # Apply enhancement method
        if enhancement['method'] == 'original':
            # Original RGB data
            enhanced_red = red_band.copy()
            enhanced_green = green_band.copy()
            enhanced_blue = blue_band.copy()
            
        elif enhancement['method'] == 'contrast_stretch':
            # Per-band 2%-98% stretch
            enhanced_red = stretch_band(red_band, 2, 98)
            enhanced_green = stretch_band(green_band, 2, 98)
            enhanced_blue = stretch_band(blue_band, 2, 98)
            
        elif enhancement['method'] == 'histogram_eq':
            # Histogram equalization
            enhanced_red = histogram_equalize(red_band)
            enhanced_green = histogram_equalize(green_band)
            enhanced_blue = histogram_equalize(blue_band)
            
        elif enhancement['method'] == 'gamma_correction':
            # Gamma correction for shadow enhancement
            gamma = 0.8
            enhanced_red = gamma_correct(red_band, gamma)
            enhanced_green = gamma_correct(green_band, gamma)
            enhanced_blue = gamma_correct(blue_band, gamma)
            
        elif enhancement['method'] == 'adaptive_histogram':
            # Adaptive enhancement
            enhanced_red = adaptive_enhance(red_band)
            enhanced_green = adaptive_enhance(green_band)
            enhanced_blue = adaptive_enhance(blue_band)
            
        elif enhancement['method'] == 'archaeological_enhance':
            # Archaeological-specific enhancement
            enhanced_red = archaeological_enhance(red_band)
            enhanced_green = archaeological_enhance(green_band)
            enhanced_blue = archaeological_enhance(blue_band)
        
        # Combine enhanced bands
        rgb_enhanced = np.stack([enhanced_red, enhanced_green, enhanced_blue], axis=-1)
        rgb_enhanced = np.clip(rgb_enhanced, 0, 255).astype(np.uint8)
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
        
        ax.imshow(rgb_enhanced, aspect='equal', interpolation='nearest')
        
        # Add title with enhancement info
        title = f"{enhancement['name'].upper()}\n"
        title += f"{enhancement['description']}"
        ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Add test info
        pixel_size = abs(stats['geotransform'][1])
        info_text = f"Test {test_counter:02d}: Hillshade RGB Enhancement\nResolution: {pixel_size:.2f}m/pixel"
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Save figure
        output_filename = f"{test_counter:02d}_{enhancement['name']}.png"
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        test_counter += 1
    
    print(f"   ✅ Generated {len(enhancements)} RGB enhancement tests")

def test_channel_manipulations(bands_data: dict, stats: dict, output_dir: str):
    """Test different channel manipulation techniques."""
    print(f"\n🔄 Testing channel manipulation techniques...")
    
    red_band = bands_data['red']
    green_band = bands_data['green']
    blue_band = bands_data['blue']
    
    # Define channel manipulation tests
    manipulations = [
        {
            'name': 'RGB_Swapped_RBG',
            'description': 'Channel swap: Red-Blue-Green',
            'channels': [red_band, blue_band, green_band]
        },
        {
            'name': 'RGB_Swapped_GRB', 
            'description': 'Channel swap: Green-Red-Blue',
            'channels': [green_band, red_band, blue_band]
        },
        {
            'name': 'RGB_Swapped_GBR',
            'description': 'Channel swap: Green-Blue-Red',
            'channels': [green_band, blue_band, red_band]
        },
        {
            'name': 'RGB_Swapped_BRG',
            'description': 'Channel swap: Blue-Red-Green',
            'channels': [blue_band, red_band, green_band]
        },
        {
            'name': 'RGB_Swapped_BGR',
            'description': 'Channel swap: Blue-Green-Red',
            'channels': [blue_band, green_band, red_band]
        },
        {
            'name': 'Red_Only_Grayscale',
            'description': 'Red channel only (grayscale)',
            'channels': [red_band, red_band, red_band]
        },
        {
            'name': 'Green_Only_Grayscale',
            'description': 'Green channel only (grayscale)', 
            'channels': [green_band, green_band, green_band]
        },
        {
            'name': 'Blue_Only_Grayscale',
            'description': 'Blue channel only (grayscale)',
            'channels': [blue_band, blue_band, blue_band]
        },
        {
            'name': 'Enhanced_Contrast_Mix',
            'description': 'Enhanced contrast with channel weighting',
            'channels': 'enhanced_contrast'
        },
        {
            'name': 'Archaeological_Mix',
            'description': 'Archaeological-optimized channel mix',
            'channels': 'archaeological_mix'
        }
    ]
    
    test_counter = 20  # Start from 20 to differentiate from enhancement tests
    
    for manipulation in manipulations:
        print(f"   🔄 Channel Test {test_counter:02d}: {manipulation['name']}")
        
        if manipulation['channels'] == 'enhanced_contrast':
            # Enhanced contrast mixing
            enhanced_red = stretch_band(red_band, 1, 99)
            enhanced_green = stretch_band(green_band, 1, 99) 
            enhanced_blue = stretch_band(blue_band, 1, 99)
            channels = [enhanced_red, enhanced_green, enhanced_blue]
            
        elif manipulation['channels'] == 'archaeological_mix':
            # Archaeological-optimized mixing
            # Emphasize red channel (often captures more relief detail)
            emphasized_red = np.clip(red_band * 1.2, 0, 255)
            balanced_green = stretch_band(green_band, 5, 95)
            subdued_blue = np.clip(blue_band * 0.8, 0, 255)
            channels = [emphasized_red, balanced_green, subdued_blue]
            
        else:
            channels = manipulation['channels']
        
        # Combine channels
        rgb_manipulated = np.stack(channels, axis=-1)
        rgb_manipulated = np.clip(rgb_manipulated, 0, 255).astype(np.uint8)
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
        
        ax.imshow(rgb_manipulated, aspect='equal', interpolation='nearest')
        
        # Add title
        title = f"{manipulation['name'].upper()}\n"
        title += f"{manipulation['description']}"
        ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Add test info
        pixel_size = abs(stats['geotransform'][1])
        info_text = f"Channel Test {test_counter:02d}: RGB Manipulation\nResolution: {pixel_size:.2f}m/pixel"
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Save figure
        output_filename = f"{test_counter:02d}_{manipulation['name']}.png"
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        test_counter += 1
    
    print(f"   ✅ Generated {len(manipulations)} channel manipulation tests")

def test_archaeological_enhancements(bands_data: dict, stats: dict, output_dir: str):
    """Test archaeological-specific enhancement techniques for RGB hillshade."""
    print(f"\n🏛️ Testing archaeological enhancement techniques...")
    
    red_band = bands_data['red']
    green_band = bands_data['green']
    blue_band = bands_data['blue']
    
    # Archaeological enhancement techniques
    archaeological_tests = [
        {
            'name': 'Archaeological_High_Contrast',
            'description': 'High contrast for feature detection',
            'method': 'high_contrast'
        },
        {
            'name': 'Archaeological_Shadow_Enhanced',
            'description': 'Shadow enhancement for linear features',
            'method': 'shadow_enhanced'
        },
        {
            'name': 'Archaeological_Subtle_Relief',
            'description': 'Subtle relief enhancement for earthworks',
            'method': 'subtle_relief'
        },
        {
            'name': 'Archaeological_Multi_Scale',
            'description': 'Multi-scale enhancement for various features',
            'method': 'multi_scale'
        }
    ]
    
    test_counter = 50  # Start from 50 for archaeological tests
    
    for test in archaeological_tests:
        print(f"   🔄 Archaeological Test {test_counter:02d}: {test['name']}")
        
        if test['method'] == 'high_contrast':
            # High contrast for archaeological features
            enhanced_red = stretch_band(red_band, 0.5, 99.5)
            enhanced_green = stretch_band(green_band, 0.5, 99.5)
            enhanced_blue = stretch_band(blue_band, 0.5, 99.5)
            
        elif test['method'] == 'shadow_enhanced':
            # Shadow enhancement for linear features
            gamma = 0.7  # Brighten shadows
            enhanced_red = gamma_correct(red_band, gamma)
            enhanced_green = gamma_correct(green_band, gamma)
            enhanced_blue = gamma_correct(blue_band, gamma)
            
        elif test['method'] == 'subtle_relief':
            # Subtle relief enhancement
            enhanced_red = stretch_band(red_band, 10, 90)
            enhanced_green = stretch_band(green_band, 10, 90)
            enhanced_blue = stretch_band(blue_band, 10, 90)
            
        elif test['method'] == 'multi_scale':
            # Multi-scale enhancement
            enhanced_red = multi_scale_enhance(red_band)
            enhanced_green = multi_scale_enhance(green_band)
            enhanced_blue = multi_scale_enhance(blue_band)
        
        # Combine enhanced bands
        rgb_archaeological = np.stack([enhanced_red, enhanced_green, enhanced_blue], axis=-1)
        rgb_archaeological = np.clip(rgb_archaeological, 0, 255).astype(np.uint8)
        
        # Create enhanced archaeological visualization
        fig, ax = plt.subplots(figsize=(14, 10), dpi=200)
        
        ax.imshow(rgb_archaeological, aspect='equal', interpolation='nearest')
        
        # Enhanced title
        title = f"ARCHAEOLOGICAL HILLSHADE RGB ANALYSIS\n{test['description']}"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=25)
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Add pixel resolution info
        pixel_size = abs(stats['geotransform'][1])
        scale_text = f"Resolution: {pixel_size:.2f}m/pixel"
        ax.text(0.02, 0.02, scale_text, transform=ax.transAxes, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Add archaeological interpretation guide
        guide_text = f"ARCHAEOLOGICAL RGB HILLSHADE ANALYSIS\n"
        guide_text += f"Multi-directional relief visualization\n"
        guide_text += f"Enhancement: {test['description']}\n"
        guide_text += f"Optimized for archaeological feature detection"
        
        ax.text(0.02, 0.98, guide_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', 
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.9))
        
        plt.tight_layout()
        
        # Save enhanced visualization
        output_filename = f"{test_counter:02d}_{test['name']}.png"
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        test_counter += 1
    
    print(f"   ✅ Generated {len(archaeological_tests)} archaeological enhancement tests")

# Helper functions for enhancement methods
def stretch_band(band, low_percentile, high_percentile):
    """Apply percentile-based contrast stretching to a band."""
    p_low = np.percentile(band, low_percentile)
    p_high = np.percentile(band, high_percentile)
    
    if p_high > p_low:
        stretched = (band - p_low) / (p_high - p_low) * 255
        return np.clip(stretched, 0, 255)
    else:
        return band.copy()

def histogram_equalize(band):
    """Apply histogram equalization to a band."""
    # Simple histogram equalization
    hist, bins = np.histogram(band.flatten(), 256, [0, 256])
    cdf = hist.cumsum()
    cdf_normalized = cdf * 255 / cdf[-1]
    
    equalized = np.interp(band.flatten(), bins[:-1], cdf_normalized)
    return equalized.reshape(band.shape)

def gamma_correct(band, gamma):
    """Apply gamma correction to a band."""
    normalized = band / 255.0
    corrected = np.power(normalized, gamma) * 255
    return np.clip(corrected, 0, 255)

def adaptive_enhance(band):
    """Apply adaptive enhancement to a band."""
    # Simple adaptive enhancement using local statistics
    mean_val = np.mean(band)
    std_val = np.std(band)
    
    enhanced = (band - mean_val) / std_val * 50 + 127
    return np.clip(enhanced, 0, 255)

def archaeological_enhance(band):
    """Apply archaeological-specific enhancement."""
    # Conservative stretch with shadow enhancement
    p5 = np.percentile(band, 5)
    p95 = np.percentile(band, 95)
    
    stretched = (band - p5) / (p95 - p5) * 255
    stretched = np.clip(stretched, 0, 255)
    
    # Slight gamma correction for shadow detail
    gamma_corrected = gamma_correct(stretched, 0.9)
    return gamma_corrected

def multi_scale_enhance(band):
    """Apply multi-scale enhancement."""
    # Combine different contrast stretches
    stretch1 = stretch_band(band, 2, 98)  # Standard
    stretch2 = stretch_band(band, 10, 90)  # Conservative
    
    # Weighted combination
    enhanced = 0.7 * stretch1 + 0.3 * stretch2
    return np.clip(enhanced, 0, 255)

def analyze_rgb_best_practices(stats: dict):
    """Analyze the RGB data and recommend best practices."""
    print(f"\n📊 RGB Hillshade Analysis & Best Practices:")
    print(f"{'='*60}")
    
    # Data characteristics analysis
    print(f"📈 RGB DATA CHARACTERISTICS:")
    pixel_size = abs(stats['geotransform'][1])
    print(f"   📐 Resolution: {pixel_size:.2f}m/pixel")
    print(f"   🎨 Format: 3-band RGB composite (Byte: 0-255)")
    
    for band_name, band_stats in stats['bands'].items():
        color_emoji = "🔴" if band_name == "red" else "🟢" if band_name == "green" else "🔵"
        print(f"   {color_emoji} {band_name.capitalize()} band range: {band_stats['min']}-{band_stats['max']} "
              f"(mean: {band_stats['mean']:.1f} ± {band_stats['std']:.1f})")
    
    # Band balance analysis
    red_stats = stats['bands']['red']
    green_stats = stats['bands']['green']
    blue_stats = stats['bands']['blue']
    
    print(f"\n📊 BAND BALANCE ANALYSIS:")
    print(f"   📈 Red dominance: {red_stats['mean']:.1f} (higher = more relief detail)")
    print(f"   📈 Green balance: {green_stats['mean']:.1f} (intermediate illumination)")
    print(f"   📈 Blue contribution: {blue_stats['mean']:.1f} (shadow details)")
    
    # Determine optimal enhancement approach
    mean_values = [red_stats['mean'], green_stats['mean'], blue_stats['mean']]
    std_values = [red_stats['std'], green_stats['std'], blue_stats['std']]
    
    dominant_channel = ['Red', 'Green', 'Blue'][np.argmax(mean_values)]
    highest_contrast = ['Red', 'Green', 'Blue'][np.argmax(std_values)]
    
    print(f"\n🎯 ENHANCEMENT RECOMMENDATIONS:")
    print(f"   🏆 Dominant channel: {dominant_channel} (likely captures most relief)")
    print(f"   🎨 Highest contrast: {highest_contrast} (best for feature detection)")
    
    # Enhancement strategy recommendations
    overall_contrast = np.mean(std_values)
    if overall_contrast > 30:
        print(f"   ✅ RECOMMENDED: Standard contrast stretching (good natural contrast)")
    elif overall_contrast > 20:
        print(f"   ✅ RECOMMENDED: Moderate enhancement with gamma correction")
    else:
        print(f"   ⚠️ RECOMMENDED: Aggressive enhancement needed (low contrast data)")
    
    # Archaeological interpretation recommendations
    print(f"\n🏛️ ARCHAEOLOGICAL VISUALIZATION:")
    print(f"   🎨 RGB Composite Advantages:")
    print(f"      • Multi-directional illumination reveals all feature orientations")
    print(f"      • Color differences highlight subtle topographic variations")
    print(f"      • Combined illumination reduces shadowing artifacts")
    print(f"   🎯 Feature Detection: Linear features, earthworks, field boundaries")
    print(f"   📏 Scale: {pixel_size:.2f}m resolution ideal for archaeological features")
    
    # Final recommendations
    print(f"\n🌟 FINAL RECOMMENDATIONS:")
    print(f"   🎨 Primary Approach: RGB composite with moderate contrast enhancement")
    print(f"   📊 Enhancement: 2%-98% percentile stretch + gamma correction (γ=0.8-0.9)")
    print(f"   🔄 Alternative: Channel manipulation for specific feature types")
    print(f"   📏 Resolution: {pixel_size:.2f}m/pixel excellent for archaeological analysis")
    print(f"   💾 Output: High-resolution PNG (200-300 DPI) for detailed interpretation")

def main():
    """Main function to run all RGB hillshade visualization tests."""
    print(f"🌄 RGB Hillshade Visualization Testing Suite")
    print(f"=" * 60)
    
    # Setup paths
    rgb_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/hillshade_rgb.tif"
    output_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/HillshadeRgb/visualizations"
    
    # Verify input file exists
    if not os.path.exists(rgb_path):
        print(f"❌ Test file not found: {rgb_path}")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    start_time = time.time()
    
    try:
        # Load and analyze test data
        bands_data, stats = load_test_hillshade_rgb(rgb_path)
        
        # Run RGB enhancement tests
        test_rgb_enhancement_methods(bands_data, stats, output_dir)
        
        # Run channel manipulation tests
        test_channel_manipulations(bands_data, stats, output_dir)
        
        # Run archaeological enhancement tests
        test_archaeological_enhancements(bands_data, stats, output_dir)
        
        # Analyze and recommend best practices
        analyze_rgb_best_practices(stats)
        
        # Summary
        total_time = time.time() - start_time
        print(f"\n✅ RGB Hillshade visualization testing completed!")
        print(f"⏱️ Total time: {total_time:.2f} seconds")
        print(f"📁 Results saved to: {output_dir}")
        print(f"🎯 Review archaeological tests (50+) for optimal archaeological visualization")
        
    except Exception as e:
        print(f"❌ Testing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
