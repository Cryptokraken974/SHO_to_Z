#!/usr/bin/env python3
"""
Analyze TIFF Bounds vs Requested Bounds

This script compares the actual bounds of a returned TIFF file with the 
requested bounds to identify potential misalignment issues in overlay processing.
"""

import rasterio
import json
from pathlib import Path

def analyze_tiff_bounds(tiff_path, metadata_path):
    """
    Compare TIFF actual bounds with requested bounds from metadata
    """
    print(f"🔍 Analyzing TIFF bounds for: {tiff_path}")
    print(f"📄 Metadata file: {metadata_path}")
    print("=" * 80)
    
    # Read metadata.txt to get requested bounds
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
            elif line.startswith('Requested Latitude:'):
                requested_bounds['center_lat'] = float(line.split(':')[1].strip())
            elif line.startswith('Requested Longitude:'):
                requested_bounds['center_lng'] = float(line.split(':')[1].strip())
    
    print("📋 REQUESTED BOUNDS (from metadata.txt):")
    print(f"   North: {requested_bounds['north']}")
    print(f"   South: {requested_bounds['south']}")
    print(f"   East:  {requested_bounds['east']}")
    print(f"   West:  {requested_bounds['west']}")
    print(f"   Center: ({requested_bounds['center_lat']}, {requested_bounds['center_lng']})")
    
    req_width = requested_bounds['east'] - requested_bounds['west']
    req_height = requested_bounds['north'] - requested_bounds['south']
    print(f"   Width:  {req_width:.6f} degrees")
    print(f"   Height: {req_height:.6f} degrees")
    print()
    
    # Read TIFF bounds
    with rasterio.open(tiff_path) as src:
        actual_bounds = src.bounds
        crs = src.crs
        width = src.width
        height = src.height
        transform = src.transform
        
        print("🗺️  ACTUAL TIFF BOUNDS:")
        print(f"   Left (West):  {actual_bounds.left}")
        print(f"   Bottom (South): {actual_bounds.bottom}")
        print(f"   Right (East):   {actual_bounds.right}")
        print(f"   Top (North):    {actual_bounds.top}")
        
        actual_center_lat = (actual_bounds.top + actual_bounds.bottom) / 2
        actual_center_lng = (actual_bounds.left + actual_bounds.right) / 2
        print(f"   Center: ({actual_center_lat}, {actual_center_lng})")
        
        actual_width = actual_bounds.right - actual_bounds.left
        actual_height = actual_bounds.top - actual_bounds.bottom
        print(f"   Width:  {actual_width:.6f} degrees")
        print(f"   Height: {actual_height:.6f} degrees")
        print(f"   CRS: {crs}")
        print(f"   Raster Size: {width} x {height} pixels")
        print(f"   Transform: {transform}")
        print()
        
        # Calculate differences
        print("⚠️  DIFFERENCES (Actual - Requested):")
        north_diff = actual_bounds.top - requested_bounds['north']
        south_diff = actual_bounds.bottom - requested_bounds['south']
        east_diff = actual_bounds.right - requested_bounds['east']
        west_diff = actual_bounds.left - requested_bounds['west']
        
        center_lat_diff = actual_center_lat - requested_bounds['center_lat']
        center_lng_diff = actual_center_lng - requested_bounds['center_lng']
        
        print(f"   North boundary: {north_diff:+.6f} degrees")
        print(f"   South boundary: {south_diff:+.6f} degrees")
        print(f"   East boundary:  {east_diff:+.6f} degrees")
        print(f"   West boundary:  {west_diff:+.6f} degrees")
        print(f"   Center Lat:     {center_lat_diff:+.6f} degrees")
        print(f"   Center Lng:     {center_lng_diff:+.6f} degrees")
        
        width_diff = actual_width - req_width
        height_diff = actual_height - req_height
        print(f"   Width:          {width_diff:+.6f} degrees")
        print(f"   Height:         {height_diff:+.6f} degrees")
        print()
        
        # Check if differences are significant
        threshold = 0.001  # 0.001 degrees ≈ 111 meters at equator
        significant_diffs = []
        
        if abs(north_diff) > threshold:
            significant_diffs.append(f"North boundary off by {north_diff:+.6f}°")
        if abs(south_diff) > threshold:
            significant_diffs.append(f"South boundary off by {south_diff:+.6f}°")
        if abs(east_diff) > threshold:
            significant_diffs.append(f"East boundary off by {east_diff:+.6f}°")
        if abs(west_diff) > threshold:
            significant_diffs.append(f"West boundary off by {west_diff:+.6f}°")
        if abs(center_lat_diff) > threshold:
            significant_diffs.append(f"Center latitude off by {center_lat_diff:+.6f}°")
        if abs(center_lng_diff) > threshold:
            significant_diffs.append(f"Center longitude off by {center_lng_diff:+.6f}°")
        
        if significant_diffs:
            print("🚨 SIGNIFICANT DIFFERENCES DETECTED:")
            for diff in significant_diffs:
                print(f"   • {diff}")
            print(f"   (Threshold: {threshold}° ≈ {threshold * 111:.0f}m at equator)")
        else:
            print("✅ No significant differences detected")
            print(f"   (All differences < {threshold}° ≈ {threshold * 111:.0f}m)")
        
        print()
        
        # Calculate pixel resolution
        pixel_size_x = abs(transform[0])
        pixel_size_y = abs(transform[4])
        print("📐 PIXEL RESOLUTION:")
        print(f"   X direction: {pixel_size_x:.6f} degrees/pixel ≈ {pixel_size_x * 111000:.1f} meters/pixel")
        print(f"   Y direction: {pixel_size_y:.6f} degrees/pixel ≈ {pixel_size_y * 111000:.1f} meters/pixel")
        
        return {
            'requested_bounds': requested_bounds,
            'actual_bounds': {
                'north': actual_bounds.top,
                'south': actual_bounds.bottom,
                'east': actual_bounds.right,
                'west': actual_bounds.left,
                'center_lat': actual_center_lat,
                'center_lng': actual_center_lng,
                'width': actual_width,
                'height': actual_height
            },
            'differences': {
                'north': north_diff,
                'south': south_diff,
                'east': east_diff,
                'west': west_diff,
                'center_lat': center_lat_diff,
                'center_lng': center_lng_diff,
                'width': width_diff,
                'height': height_diff
            },
            'significant_differences': significant_diffs,
            'tiff_info': {
                'crs': str(crs),
                'width': width,
                'height': height,
                'pixel_size_x': pixel_size_x,
                'pixel_size_y': pixel_size_y,
                'transform': list(transform)
            }
        }

if __name__ == "__main__":
    # Analyze the 1.81S_50 region
    region_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/1.81S_50"
    tiff_path = f"{region_path}/lidar/DSM/1.81S_50_copernicus_dsm_30m.tif"
    metadata_path = f"{region_path}/metadata.txt"
    
    if Path(tiff_path).exists() and Path(metadata_path).exists():
        result = analyze_tiff_bounds(tiff_path, metadata_path)
        
        # Save results to JSON for further analysis
        output_file = f"{region_path}/bounds_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"📊 Analysis results saved to: {output_file}")
    else:
        print(f"❌ Files not found:")
        print(f"   TIFF: {tiff_path} ({'✓' if Path(tiff_path).exists() else '✗'})")
        print(f"   Metadata: {metadata_path} ({'✓' if Path(metadata_path).exists() else '✗'})")
