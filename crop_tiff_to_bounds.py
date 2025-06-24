#!/usr/bin/env python3
"""
TIFF Bounds Cropping Tool

This script crops TIFF files to match the exact requested bounds from metadata.txt
to fix overlay alignment issues caused by elevation services returning larger areas
than requested.
"""

import rasterio
from rasterio.mask import mask
from rasterio.windows import from_bounds
import json
from pathlib import Path
from shapely.geometry import box
import shutil

def crop_tiff_to_requested_bounds(tiff_path, metadata_path, output_path=None):
    """
    Crop TIFF file to match the requested bounds from metadata.txt
    """
    print(f"🔧 Cropping TIFF to requested bounds: {tiff_path}")
    print(f"📄 Using metadata from: {metadata_path}")
    print("=" * 80)
    
    # Read requested bounds from metadata.txt
    requested_bounds = {}
    with open(metadata_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith('North Bound:'):
                requested_bounds['north'] = float(line.split(':')[1].strip())
            elif line.startswith('South Bound:'):
                requested_bounds['south'] = float(line.split(':')[1].strip())
            elif line.startswith('East Bound:'):
                requested_bounds['east'] = float(line.split(':')[1].strip())
            elif line.startswith('West Bound:'):
                requested_bounds['west'] = float(line.split(':')[1].strip())
    
    print("📋 REQUESTED BOUNDS (from metadata.txt):")
    print(f"   North: {requested_bounds['north']}")
    print(f"   South: {requested_bounds['south']}")
    print(f"   East:  {requested_bounds['east']}")
    print(f"   West:  {requested_bounds['west']}")
    
    # Create output path if not provided
    if output_path is None:
        tiff_path_obj = Path(tiff_path)
        output_path = tiff_path_obj.parent / f"{tiff_path_obj.stem}_cropped{tiff_path_obj.suffix}"
    
    # Open the original TIFF
    with rasterio.open(tiff_path) as src:
        print(f"\n🗺️  ORIGINAL TIFF BOUNDS:")
        print(f"   Left:   {src.bounds.left}")
        print(f"   Bottom: {src.bounds.bottom}")
        print(f"   Right:  {src.bounds.right}")
        print(f"   Top:    {src.bounds.top}")
        print(f"   CRS:    {src.crs}")
        print(f"   Size:   {src.width} x {src.height} pixels")
        
        # Create bounding box for cropping
        crop_bounds = (
            requested_bounds['west'],
            requested_bounds['south'], 
            requested_bounds['east'],
            requested_bounds['north']
        )
        
        # Check if requested bounds are within the TIFF bounds
        if (crop_bounds[0] < src.bounds.left or crop_bounds[1] < src.bounds.bottom or
            crop_bounds[2] > src.bounds.right or crop_bounds[3] > src.bounds.top):
            print("\n⚠️  WARNING: Requested bounds extend outside TIFF bounds!")
            print("   Cropping to intersection of requested and available bounds...")
            
            # Clip to intersection
            crop_bounds = (
                max(crop_bounds[0], src.bounds.left),
                max(crop_bounds[1], src.bounds.bottom),
                min(crop_bounds[2], src.bounds.right),
                min(crop_bounds[3], src.bounds.top)
            )
        
        print(f"\n✂️  CROPPING TO BOUNDS:")
        print(f"   West:  {crop_bounds[0]}")
        print(f"   South: {crop_bounds[1]}")
        print(f"   East:  {crop_bounds[2]}")
        print(f"   North: {crop_bounds[3]}")
        
        # Calculate window for cropping
        window = from_bounds(*crop_bounds, src.transform)
        
        # Read the data within the window
        cropped_data = src.read(window=window)
        
        # Calculate new transform for the cropped area
        new_transform = src.window_transform(window)
        
        # Write the cropped TIFF
        profile = src.profile.copy()
        profile.update({
            'height': cropped_data.shape[1],
            'width': cropped_data.shape[2], 
            'transform': new_transform
        })
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(cropped_data)
        
        print(f"\n✅ CROPPED TIFF SAVED:")
        print(f"   File: {output_path}")
        
        # Verify the cropped file
        with rasterio.open(output_path) as cropped_src:
            print(f"   New size: {cropped_src.width} x {cropped_src.height} pixels")
            print(f"   New bounds:")
            print(f"     Left:   {cropped_src.bounds.left:.6f}")
            print(f"     Bottom: {cropped_src.bounds.bottom:.6f}")
            print(f"     Right:  {cropped_src.bounds.right:.6f}")
            print(f"     Top:    {cropped_src.bounds.top:.6f}")
            
            # Calculate accuracy
            bounds_diff = {
                'west': abs(cropped_src.bounds.left - requested_bounds['west']),
                'south': abs(cropped_src.bounds.bottom - requested_bounds['south']),
                'east': abs(cropped_src.bounds.right - requested_bounds['east']),
                'north': abs(cropped_src.bounds.top - requested_bounds['north'])
            }
            
            max_diff = max(bounds_diff.values())
            print(f"   Maximum bounds difference: {max_diff:.6f}° ({max_diff * 111000:.1f}m)")
            
            if max_diff < 0.001:  # Within ~111 meters
                print("   ✅ Cropping accuracy: EXCELLENT")
            elif max_diff < 0.01:  # Within ~1.1 km
                print("   ✅ Cropping accuracy: GOOD") 
            else:
                print("   ⚠️  Cropping accuracy: FAIR (check pixel alignment)")
    
    return str(output_path)

def backup_and_replace_original(original_path, cropped_path):
    """
    Backup the original file and replace it with the cropped version
    """
    original_path_obj = Path(original_path)
    backup_path = original_path_obj.parent / f"{original_path_obj.stem}_original_backup{original_path_obj.suffix}"
    
    # Create backup
    shutil.copy2(original_path, backup_path)
    print(f"📦 Original backed up to: {backup_path}")
    
    # Replace original with cropped version
    shutil.move(cropped_path, original_path)
    print(f"🔄 Original file replaced with cropped version")
    
    return str(backup_path)

if __name__ == "__main__":
    # Crop the problematic region 1.81S_50
    region_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/1.81S_50"
    tiff_path = f"{region_path}/lidar/DSM/1.81S_50_copernicus_dsm_30m.tif"
    metadata_path = f"{region_path}/metadata.txt"
    
    if Path(tiff_path).exists() and Path(metadata_path).exists():
        print("🎯 CROPPING TIFF TO FIX OVERLAY ALIGNMENT")
        print("=" * 80)
        
        # Crop the TIFF to match requested bounds
        cropped_path = crop_tiff_to_requested_bounds(tiff_path, metadata_path)
        
        # Backup original and replace with cropped version
        backup_path = backup_and_replace_original(tiff_path, cropped_path)
        
        print(f"\n🎉 OVERLAY ALIGNMENT FIX COMPLETE!")
        print(f"   ✅ TIFF cropped to match requested bounds")
        print(f"   ✅ Original backed up: {Path(backup_path).name}")
        print(f"   ✅ Cropped version now in place")
        print(f"\n💡 The elevation data should now align perfectly with LAZ overlays!")
        
    else:
        print(f"❌ Files not found:")
        print(f"   TIFF: {tiff_path} ({'✓' if Path(tiff_path).exists() else '✗'})")
        print(f"   Metadata: {metadata_path} ({'✓' if Path(metadata_path).exists() else '✗'})")
