#!/usr/bin/env python3
"""
Script to clean up duplicate PNG files in the output directories.
Removes long-named duplicates while keeping short-named consolidated versions.
"""

import os
import glob
from pathlib import Path

def cleanup_duplicate_pngs():
    """Remove duplicate PNG files, keeping the short-named versions"""
    
    # Find all png_outputs directories
    output_dirs = glob.glob("output/*/lidar/png_outputs")
    
    total_removed = 0
    total_size_saved = 0
    
    for png_outputs_dir in output_dirs:
        print(f"\n🔍 Checking directory: {png_outputs_dir}")
        
        # Define the mapping of short names to long name patterns
        duplicate_patterns = {
            "LRM.png": "*_LRM.png",
            "SVF.png": "*_Sky_View_Factor.png", 
            "Slope.png": "*_slope.png",
            "HillshadeRGB.png": "*_HillshadeRGB.png",
            "TintOverlay.png": "*_TintOverlay.png"
        }
        
        # Also check for case variations and other duplicates
        case_duplicates = {
            "HillshadeRGB.png": "hillshade_rgb.png",
            "TintOverlay.png": "tint_overlay.png"
        }
        
        for short_name, long_pattern in duplicate_patterns.items():
            short_path = os.path.join(png_outputs_dir, short_name)
            long_files = glob.glob(os.path.join(png_outputs_dir, long_pattern))
            
            # Remove files that match the long pattern but are not the short name
            long_files = [f for f in long_files if not f.endswith(short_name)]
            
            if os.path.exists(short_path) and long_files:
                print(f"  ✅ Found short version: {short_name}")
                for long_file in long_files:
                    try:
                        file_size = os.path.getsize(long_file)
                        os.remove(long_file)
                        print(f"  🗑️  Removed duplicate: {os.path.basename(long_file)} ({file_size:,} bytes)")
                        total_removed += 1
                        total_size_saved += file_size
                        
                        # Also remove associated worldfile if it exists
                        worldfile = os.path.splitext(long_file)[0] + ".pgw"
                        if os.path.exists(worldfile):
                            os.remove(worldfile)
                            print(f"  🗑️  Removed worldfile: {os.path.basename(worldfile)}")
                            
                    except Exception as e:
                        print(f"  ❌ Error removing {long_file}: {e}")
            elif long_files and not os.path.exists(short_path):
                print(f"  ⚠️  Long version exists but no short version: {long_pattern}")
        
        # Handle case duplicates (e.g., HillshadeRGB.png vs hillshade_rgb.png)
        for preferred_name, duplicate_name in case_duplicates.items():
            preferred_path = os.path.join(png_outputs_dir, preferred_name)
            duplicate_path = os.path.join(png_outputs_dir, duplicate_name)
            
            if os.path.exists(preferred_path) and os.path.exists(duplicate_path):
                try:
                    file_size = os.path.getsize(duplicate_path)
                    os.remove(duplicate_path)
                    print(f"  🗑️  Removed case duplicate: {duplicate_name} ({file_size:,} bytes)")
                    total_removed += 1
                    total_size_saved += file_size
                    
                    # Also remove associated worldfile if it exists
                    worldfile = os.path.splitext(duplicate_path)[0] + ".pgw"
                    if os.path.exists(worldfile):
                        os.remove(worldfile)
                        print(f"  🗑️  Removed worldfile: {os.path.basename(worldfile)}")
                        
                except Exception as e:
                    print(f"  ❌ Error removing {duplicate_path}: {e}")
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   Files removed: {total_removed}")
    print(f"   Space saved: {total_size_saved:,} bytes ({total_size_saved/(1024*1024):.2f} MB)")

if __name__ == "__main__":
    print("🧹 Starting PNG duplicate cleanup...")
    cleanup_duplicate_pngs()
    print("✅ Cleanup complete!")
