#!/usr/bin/env python3
"""
Migration script to move PNG files from scattered processing directories 
to consolidated png_outputs structure.

This script consolidates PNG files from:
  output/{region}/lidar/{processing_type}/{region}_{type}.png
To:
  output/{region}/lidar/png_outputs/{region}_{type}.png

Maintains backward compatibility by keeping original files as well.
"""

import os
import shutil
import glob
from pathlib import Path

def migrate_region_pngs(region_name):
    """Migrate PNG files for a specific region to consolidated png_outputs structure"""
    
    region_path = Path(f"output/{region_name}")
    if not region_path.exists():
        print(f"❌ Region directory not found: {region_path}")
        return False
    
    lidar_path = region_path / "lidar"
    if not lidar_path.exists():
        print(f"❌ Lidar directory not found: {lidar_path}")
        return False
    
    # Create png_outputs directory
    png_outputs_dir = lidar_path / "png_outputs"
    png_outputs_dir.mkdir(exist_ok=True)
    print(f"📁 Created PNG outputs directory: {png_outputs_dir}")
    
    # Processing types to look for
    processing_types = ["Hillshade", "Slope", "Aspect", "TRI", "TPI", "Roughness", "DTM", "DEM", "DSM", "CHM"]
    
    moved_count = 0
    copied_count = 0
    
    for proc_type in processing_types:
        proc_dir = lidar_path / proc_type
        if proc_dir.exists():
            print(f"\n🔍 Processing {proc_type} directory...")
            
            # Find PNG files in this directory
            png_files = list(proc_dir.glob("*.png"))
            
            for png_file in png_files:
                # Skip auxiliary files
                if png_file.name.endswith('.aux.xml'):
                    continue
                    
                print(f"  📸 Found PNG: {png_file.name}")
                
                # Determine target filename
                target_name = png_file.name
                
                # Convert naming convention for consistency
                # OR_WizardIsland_Hillshade.png -> OR_WizardIsland_elevation_hillshade.png
                if not "_elevation_" in target_name:
                    base_name = target_name.replace(f"_{proc_type}", f"_elevation_{proc_type.lower()}")
                    target_name = base_name
                
                target_path = png_outputs_dir / target_name
                
                # Copy the file (don't move to preserve original structure)
                try:
                    shutil.copy2(png_file, target_path)
                    print(f"  ✅ Copied to: {target_path.name}")
                    copied_count += 1
                    
                    # Also copy associated files (.wld, .tif, .aux.xml)
                    base_name = png_file.stem
                    for ext in ['.wld', '.tif', '.aux.xml']:
                        source_associated = png_file.parent / f"{base_name}{ext}"
                        if source_associated.exists():
                            target_associated = png_outputs_dir / f"{Path(target_name).stem}{ext}"
                            shutil.copy2(source_associated, target_associated)
                            print(f"    📎 Associated file: {target_associated.name}")
                            
                except Exception as e:
                    print(f"  ❌ Error copying {png_file.name}: {e}")
    
    print(f"\n✅ Migration complete for {region_name}:")
    print(f"   📸 PNG files copied: {copied_count}")
    print(f"   📁 Target directory: {png_outputs_dir}")
    
    return copied_count > 0

def main():
    """Main migration function"""
    print("🔄 PNG Consolidation Migration")
    print("=" * 50)
    
    # Find all regions with lidar data
    output_dir = Path("output")
    if not output_dir.exists():
        print("❌ Output directory not found")
        return
    
    regions_migrated = []
    
    for region_dir in output_dir.iterdir():
        if region_dir.is_dir() and region_dir.name != "LAZ":
            lidar_dir = region_dir / "lidar"
            if lidar_dir.exists():
                # Check if this region has scattered PNG files
                has_scattered_pngs = False
                processing_dirs = ["Hillshade", "Slope", "Aspect", "TRI", "TPI", "Roughness", "DTM"]
                
                for proc_dir in processing_dirs:
                    proc_path = lidar_dir / proc_dir
                    if proc_path.exists() and list(proc_path.glob("*.png")):
                        has_scattered_pngs = True
                        break
                
                if has_scattered_pngs:
                    print(f"\n🔍 Found region with scattered PNGs: {region_dir.name}")
                    if migrate_region_pngs(region_dir.name):
                        regions_migrated.append(region_dir.name)
    
    print(f"\n🎉 Migration Summary:")
    print(f"   Regions processed: {len(regions_migrated)}")
    for region in regions_migrated:
        print(f"   ✅ {region}")
    
    if not regions_migrated:
        print("   ℹ️  No regions found with scattered PNG files to migrate")

if __name__ == "__main__":
    main()
