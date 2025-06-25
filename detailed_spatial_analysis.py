#!/usr/bin/env python3
"""
Detailed Spatial Analysis Script
Analyzes the spatial properties, extents, and compatibility of DTM and DSM files
"""

import os
import rasterio
from rasterio.warp import transform_bounds
import pyproj
from pathlib import Path
import numpy as np

def analyze_raster_file(file_path, file_type):
    """Analyze a raster file and return comprehensive spatial information"""
    print(f"\n{'='*60}")
    print(f"ANALYZING {file_type}: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    try:
        with rasterio.open(file_path) as src:
            # Basic properties
            print(f"📁 File: {file_path}")
            print(f"🗺️  CRS: {src.crs}")
            print(f"📏 Resolution: {src.res[0]:.6f} x {src.res[1]:.6f} units")
            print(f"📐 Dimensions: {src.width} x {src.height} pixels")
            print(f"🎯 Transform: {src.transform}")
            
            # Get bounds in native CRS
            native_bounds = src.bounds
            print(f"\n🔲 BOUNDS IN NATIVE CRS ({src.crs}):")
            print(f"   West: {native_bounds.left:.6f}")
            print(f"   South: {native_bounds.bottom:.6f}")
            print(f"   East: {native_bounds.right:.6f}")
            print(f"   North: {native_bounds.top:.6f}")
            
            # Convert bounds to WGS84 for comparison
            try:
                wgs84_bounds = transform_bounds(src.crs, 'EPSG:4326', *native_bounds)
                print(f"\n🌍 BOUNDS IN WGS84 (EPSG:4326):")
                print(f"   West: {wgs84_bounds[0]:.6f}°")
                print(f"   South: {wgs84_bounds[1]:.6f}°")
                print(f"   East: {wgs84_bounds[2]:.6f}°")
                print(f"   North: {wgs84_bounds[3]:.6f}°")
                
                # Calculate center point
                center_lat = (wgs84_bounds[1] + wgs84_bounds[3]) / 2
                center_lng = (wgs84_bounds[0] + wgs84_bounds[2]) / 2
                print(f"   Center: {center_lat:.6f}°, {center_lng:.6f}°")
                
                # Determine geographic region
                if center_lat >= 0:
                    lat_hemisphere = "Northern Hemisphere"
                else:
                    lat_hemisphere = "Southern Hemisphere"
                    
                if center_lng >= 0:
                    lng_hemisphere = "Eastern Hemisphere"
                else:
                    lng_hemisphere = "Western Hemisphere"
                    
                print(f"   Location: {lat_hemisphere}, {lng_hemisphere}")
                
                # Rough geographic identification
                if -180 <= center_lng <= -30 and 25 <= center_lat <= 75:
                    region = "North America"
                elif -15 <= center_lng <= 60 and 35 <= center_lat <= 75:
                    region = "Europe"
                elif -90 <= center_lng <= -30 and -60 <= center_lat <= 15:
                    region = "South America"
                elif 90 <= center_lng <= 180 and -50 <= center_lat <= 50:
                    region = "Asia/Oceania"
                elif -20 <= center_lng <= 60 and -40 <= center_lat <= 40:
                    region = "Africa"
                else:
                    region = "Unknown/Ocean"
                    
                print(f"   Approximate Region: {region}")
                
            except Exception as e:
                print(f"❌ Error converting bounds to WGS84: {e}")
                wgs84_bounds = None
            
            # Data statistics
            try:
                # Read a sample of the data to get statistics
                sample_data = src.read(1, window=rasterio.windows.Window(0, 0, min(1000, src.width), min(1000, src.height)))
                valid_data = sample_data[sample_data != src.nodata] if src.nodata is not None else sample_data
                
                if len(valid_data) > 0:
                    print(f"\n📊 DATA STATISTICS (sample):")
                    print(f"   No-data value: {src.nodata}")
                    print(f"   Min elevation: {np.min(valid_data):.2f}")
                    print(f"   Max elevation: {np.max(valid_data):.2f}")
                    print(f"   Mean elevation: {np.mean(valid_data):.2f}")
                    print(f"   Std deviation: {np.std(valid_data):.2f}")
                else:
                    print(f"\n📊 DATA STATISTICS: No valid data found")
            except Exception as e:
                print(f"❌ Error reading data statistics: {e}")
            
            return {
                'file_path': file_path,
                'file_type': file_type,
                'crs': str(src.crs),
                'resolution': src.res,
                'dimensions': (src.width, src.height),
                'native_bounds': native_bounds,
                'wgs84_bounds': wgs84_bounds,
                'transform': src.transform,
                'nodata': src.nodata
            }
            
    except Exception as e:
        print(f"❌ Error analyzing {file_path}: {e}")
        return None

def check_spatial_compatibility(dtm_info, dsm_info):
    """Check if DTM and DSM are spatially compatible"""
    print(f"\n{'='*60}")
    print("SPATIAL COMPATIBILITY ANALYSIS")
    print(f"{'='*60}")
    
    if not dtm_info or not dsm_info:
        print("❌ Cannot perform compatibility analysis - missing file information")
        return False
    
    # Check CRS compatibility
    print(f"🗺️  CRS COMPARISON:")
    print(f"   DTM CRS: {dtm_info['crs']}")
    print(f"   DSM CRS: {dsm_info['crs']}")
    
    crs_compatible = dtm_info['crs'] == dsm_info['crs']
    if crs_compatible:
        print("   ✅ CRS match - files use the same coordinate system")
    else:
        print("   ⚠️  CRS differ - files use different coordinate systems")
    
    # Check resolution compatibility
    print(f"\n📏 RESOLUTION COMPARISON:")
    dtm_res = dtm_info['resolution']
    dsm_res = dsm_info['resolution']
    print(f"   DTM resolution: {dtm_res[0]:.6f} x {dtm_res[1]:.6f}")
    print(f"   DSM resolution: {dsm_res[0]:.6f} x {dsm_res[1]:.6f}")
    
    # Allow for small floating point differences
    res_compatible = (abs(dtm_res[0] - dsm_res[0]) < 0.001 and 
                     abs(dtm_res[1] - dsm_res[1]) < 0.001)
    
    if res_compatible:
        print("   ✅ Resolutions match")
    else:
        print("   ⚠️  Resolutions differ significantly")
    
    # Check spatial extent overlap using WGS84 bounds
    print(f"\n🌍 SPATIAL EXTENT OVERLAP (WGS84):")
    
    if dtm_info['wgs84_bounds'] and dsm_info['wgs84_bounds']:
        dtm_bounds = dtm_info['wgs84_bounds']
        dsm_bounds = dsm_info['wgs84_bounds']
        
        print(f"   DTM extent: {dtm_bounds[0]:.3f}°W to {dtm_bounds[2]:.3f}°E, {dtm_bounds[1]:.3f}°S to {dtm_bounds[3]:.3f}°N")
        print(f"   DSM extent: {dsm_bounds[0]:.3f}°W to {dsm_bounds[2]:.3f}°E, {dsm_bounds[1]:.3f}°S to {dsm_bounds[3]:.3f}°N")
        
        # Check for overlap
        overlap_west = max(dtm_bounds[0], dsm_bounds[0])
        overlap_east = min(dtm_bounds[2], dsm_bounds[2])
        overlap_south = max(dtm_bounds[1], dsm_bounds[1])
        overlap_north = min(dtm_bounds[3], dsm_bounds[3])
        
        has_overlap = (overlap_west < overlap_east) and (overlap_south < overlap_north)
        
        if has_overlap:
            overlap_width = overlap_east - overlap_west
            overlap_height = overlap_north - overlap_south
            print(f"   ✅ Spatial overlap detected!")
            print(f"   📏 Overlap area: {overlap_width:.3f}° x {overlap_height:.3f}°")
            print(f"   🔲 Overlap bounds: {overlap_west:.3f}°W to {overlap_east:.3f}°E, {overlap_south:.3f}°S to {overlap_north:.3f}°N")
        else:
            print(f"   ❌ NO SPATIAL OVERLAP - Files cover completely different areas!")
            
            # Calculate distances between centers
            dtm_center_lat = (dtm_bounds[1] + dtm_bounds[3]) / 2
            dtm_center_lng = (dtm_bounds[0] + dtm_bounds[2]) / 2
            dsm_center_lat = (dsm_bounds[1] + dsm_bounds[3]) / 2
            dsm_center_lng = (dsm_bounds[0] + dsm_bounds[2]) / 2
            
            # Rough distance calculation
            lat_diff = abs(dtm_center_lat - dsm_center_lat)
            lng_diff = abs(dtm_center_lng - dsm_center_lng)
            
            print(f"   📍 Distance between centers:")
            print(f"      Latitude difference: {lat_diff:.3f}° (~{lat_diff * 111:.0f} km)")
            print(f"      Longitude difference: {lng_diff:.3f}° (~{lng_diff * 111:.0f} km)")
        
        spatial_compatible = has_overlap
    else:
        print("   ❌ Cannot compare spatial extents - coordinate transformation failed")
        spatial_compatible = False
    
    # Overall compatibility assessment
    print(f"\n🎯 OVERALL COMPATIBILITY ASSESSMENT:")
    if crs_compatible and res_compatible and spatial_compatible:
        print("   ✅ FILES ARE COMPATIBLE - CHM generation should work")
        return True
    else:
        print("   ❌ FILES ARE NOT COMPATIBLE - CHM generation will fail")
        print("\n🔧 ISSUES TO RESOLVE:")
        if not crs_compatible:
            print("   - Reproject one file to match the other's CRS")
        if not res_compatible:
            print("   - Resample one file to match the other's resolution")
        if not spatial_compatible:
            print("   - Ensure both files cover the same geographic area")
        return False

def main():
    """Main analysis function"""
    print("🔍 DETAILED SPATIAL ANALYSIS")
    print("=" * 60)
    
    # Look for DTM and DSM files
    output_dir = Path("output")
    
    # Find DTM files (OR_WizardIsland)
    dtm_files = []
    for pattern in ["**/*DTM*.tif", "**/*dtm*.tif", "**/*elevation*.tif"]:
        dtm_files.extend(list(output_dir.glob(pattern)))
    
    # Find DSM files (Box_Regions)
    dsm_files = []
    for pattern in ["**/*DSM*.tif", "**/*dsm*.tif", "**/*copernicus*.tif"]:
        dsm_files.extend(list(output_dir.glob(pattern)))
    
    print(f"📁 Found {len(dtm_files)} DTM files")
    print(f"📁 Found {len(dsm_files)} DSM files")
    
    if not dtm_files:
        print("❌ No DTM files found!")
        return
    
    if not dsm_files:
        print("❌ No DSM files found!")
        return
    
    # Analyze the first DTM and DSM files
    dtm_file = dtm_files[0]
    dsm_file = dsm_files[0]
    
    print(f"\n🎯 ANALYZING REPRESENTATIVE FILES:")
    print(f"   DTM: {dtm_file}")
    print(f"   DSM: {dsm_file}")
    
    # Perform detailed analysis
    dtm_info = analyze_raster_file(dtm_file, "DTM")
    dsm_info = analyze_raster_file(dsm_file, "DSM")
    
    # Check compatibility
    check_spatial_compatibility(dtm_info, dsm_info)
    
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
