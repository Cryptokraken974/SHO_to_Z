#!/usr/bin/env python3
"""
Create a visual demonstration of the new archaeological gentle color scheme
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import os

def create_archaeological_gentle_demo():
    """Create a visual demonstration of the new color scheme"""
    
    print("🎨 Creating archaeological gentle color scheme demonstration...")
    
    # Define the new archaeological gentle color ramp
    colors = [
        '#FFFADC',  # Pale cream/yellow (lowest elevation)
        '#FFE4B5',  # Soft peach/orange  
        '#FFC098',  # Gentle salmon
        '#FFA07A',  # Soft coral/light red
        '#FF8C69'   # Warm light red (highest elevation)
    ]
    
    color_names = [
        'Pale cream/yellow (lowest)',
        'Soft peach/orange',
        'Gentle salmon',
        'Soft coral/light red', 
        'Warm light red (highest)'
    ]
    
    # Create elevation gradient for demonstration
    width, height = 800, 200
    elevation_gradient = np.linspace(0, 1, width)
    elevation_array = np.tile(elevation_gradient, (height, 1))
    
    # Create colormap
    n_bins = 256
    cmap = LinearSegmentedColormap.from_list('archaeological_gentle', colors, N=n_bins)
    
    # Apply colormap
    colored_gradient = cmap(elevation_array)
    
    # Create figure with color band demonstration
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Top plot: Color gradient
    ax1.imshow(colored_gradient, aspect='auto', extent=[0, 100, 0, 1])
    ax1.set_title('Archaeological Gentle Color Scheme - Elevation Gradient', fontsize=16, fontweight='bold')
    ax1.set_xlabel('Elevation Percentage (%)', fontsize=12)
    ax1.set_ylabel('Color Band', fontsize=12)
    
    # Add elevation markers
    elevation_percentages = [0, 25, 50, 75, 100]
    for i, pct in enumerate(elevation_percentages):
        ax1.axvline(x=pct, color='white', linestyle='--', alpha=0.7, linewidth=1)
        if i < len(color_names):
            ax1.text(pct, 0.5, f'{pct}%', ha='center', va='center', 
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                    fontsize=10, fontweight='bold')
    
    # Bottom plot: Color swatches with descriptions
    ax2.set_xlim(0, 5)
    ax2.set_ylim(0, 1)
    
    for i, (color, name) in enumerate(zip(colors, color_names)):
        # Color swatch
        rect = plt.Rectangle((i, 0.3), 0.8, 0.4, facecolor=color, edgecolor='black', linewidth=1)
        ax2.add_patch(rect)
        
        # Color code
        ax2.text(i + 0.4, 0.15, color, ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Description
        ax2.text(i + 0.4, 0.85, name, ha='center', va='center', fontsize=9, 
                rotation=0, wrap=True)
    
    ax2.set_title('Color Band Details', fontsize=14, fontweight='bold')
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_xlim(-0.1, 5.1)
    
    # Remove spines
    for spine in ax2.spines.values():
        spine.set_visible(False)
    
    plt.tight_layout()
    
    # Save the demonstration
    output_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/archaeological_gentle_color_scheme_demo.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Color scheme demonstration saved: {output_path}")
    
    # Create a comparison with the old scheme
    create_color_scheme_comparison()
    
    return output_path

def create_color_scheme_comparison():
    """Create a side-by-side comparison of old vs new color schemes"""
    
    print("🔄 Creating color scheme comparison...")
    
    # Old color scheme (arch_subtle) - darker colors
    old_colors = [
        '#C8B4A0',  # Light brownish
        '#DCC8B4',  # Soft tan
        '#B4A08C',  # Medium brown
        '#E6D2BE',  # Light beige
        '#F0DCB4',  # Cream
        '#FFF5EB'   # Very light cream
    ]
    
    # New archaeological gentle color scheme
    new_colors = [
        '#FFFADC',  # Pale cream/yellow (lowest elevation)
        '#FFE4B5',  # Soft peach/orange  
        '#FFC098',  # Gentle salmon
        '#FFA07A',  # Soft coral/light red
        '#FF8C69'   # Warm light red (highest elevation)
    ]
    
    # Create elevation gradient
    width, height = 400, 100
    elevation_gradient = np.linspace(0, 1, width)
    elevation_array = np.tile(elevation_gradient, (height, 1))
    
    # Create colormaps
    old_cmap = LinearSegmentedColormap.from_list('arch_subtle', old_colors, N=256)
    new_cmap = LinearSegmentedColormap.from_list('archaeological_gentle', new_colors, N=256)
    
    # Apply colormaps
    old_gradient = old_cmap(elevation_array)
    new_gradient = new_cmap(elevation_array)
    
    # Create comparison figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6))
    
    # Old color scheme
    ax1.imshow(old_gradient, aspect='auto', extent=[0, 100, 0, 1])
    ax1.set_title('OLD: "arch_subtle" Color Scheme (Dark/Brown Tones)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Old Colors', fontsize=12)
    ax1.set_xticks([])
    
    # New color scheme  
    ax2.imshow(new_gradient, aspect='auto', extent=[0, 100, 0, 1])
    ax2.set_title('NEW: "archaeological_gentle" Color Scheme (Warm/Bright Tones)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Elevation Percentage (%)', fontsize=12)
    ax2.set_ylabel('New Colors', fontsize=12)
    
    # Add comparison notes
    fig.suptitle('Color Scheme Comparison for Archaeological Visualization', 
                fontsize=16, fontweight='bold', y=0.95)
    
    plt.tight_layout()
    
    # Save comparison
    comparison_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/color_scheme_comparison.png"
    plt.savefig(comparison_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Color scheme comparison saved: {comparison_path}")
    return comparison_path

def main():
    """Main function"""
    print("🎨 ARCHAEOLOGICAL GENTLE COLOR SCHEME DEMONSTRATION")
    print("=" * 60)
    
    demo_path = create_archaeological_gentle_demo()
    
    print("\n✅ DEMONSTRATION COMPLETE!")
    print(f"📁 Color scheme demo: {demo_path}")
    print(f"📁 Comparison chart: /Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/color_scheme_comparison.png")
    print("\n🔍 Key improvements in the new archaeological_gentle scheme:")
    print("   • Brighter, more vibrant colors for better feature visibility")
    print("   • Warm color palette (cream → peach → salmon → coral → red)")
    print("   • Smooth transitions between elevation zones")
    print("   • Enhanced contrast for archaeological feature detection")
    print("   • Optimized for hillshade blending")

if __name__ == "__main__":
    main()
