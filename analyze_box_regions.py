#!/usr/bin/env python3
"""
Analyze Box_Regions_6 DSM file to understand the spatial mismatch
"""

import os
import rasterio
from rasterio.warp import transform_bounds
import pyproj
from pathlib import Path
import numpy as np

def analyze_box_regions_dsm():
    """Analyze the Box_Regions_6 DSM file"""
    print("🔍 ANALYZING BOX_REGIONS_6 DSM FILE")
    print("=" * 60)
    
    dsm_file = "output/Box_Regions_6/lidar/DSM/Box_Regions_6_copernicus_dsm_30m.tif"
    
    if not os.path.exists(dsm_file):
        print(f"❌ File not found: {dsm_file}")
        return
    
    try:
        with rasterio.open(dsm_file) as src:
            print(f"📁 File: {dsm_file}")
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
                
    except Exception as e:
        print(f"❌ Error analyzing {dsm_file}: {e}")

def compare_oregon_vs_box():
    """Compare Oregon and Box_Regions coordinates"""
    print(f"\n🌍 GEOGRAPHIC COMPARISON")
    print("=" * 60)
    
    print("📍 OR_WizardIsland:")
    print("   Location: Oregon, USA")
    print("   Coordinates: ~42.94°N, 122.14°W")
    print("   Region: North America (Pacific Northwest)")
    
    print("\n📍 Box_Regions_6:")
    print("   Expected: South America (based on naming pattern)")
    print("   Coordinates: To be determined from DSM analysis")
    
    print(f"\n❌ PROBLEM IDENTIFIED:")
    print("   You're trying to generate CHM using:")
    print("   - DTM from Oregon, USA")
    print("   - DSM from Box_Regions (likely South America)")
    print("   These are thousands of kilometers apart!")
    
    print(f"\n✅ SOLUTION:")
    print("   For OR_WizardIsland CHM, use:")
    print("   - DTM: output/OR_WizardIsland/lidar/DTM/[DTM_file]")
    print("   - DSM: output/OR_WizardIsland/lidar/DSM/OR_WizardIsland_DSM.tif")

if __name__ == "__main__":
    analyze_box_regions_dsm()
    compare_oregon_vs_box()
