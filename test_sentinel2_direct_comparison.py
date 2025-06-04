#!/usr/bin/env python3
"""
🛰️ SENTINEL-2 DIRECT COMPARISON TEST
====================================

Test Sentinel-2 data with the EXACT same region and 25km configuration 
as our successful elevation data test for direct quality comparison.

Based on the elevation test success:
- Location: Amazon Basin, Brazil (-9.38, 62.67)  
- Buffer: 12.5km radius (25x25km area)
- Objective: Get highest resolution Sentinel-2 GeoTIFF
"""

import asyncio
import sys
import os
import time
import math
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
from data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
from data_acquisition.utils.coordinates import BoundingBox

async def progress_callback(update):
    """Handle progress updates"""
    message = update.get("message", "")
    progress = update.get("progress", 0)
    if progress > 0:
        print(f"   📊 {message} ({progress:.1f}%)")
    else:
        print(f"   ℹ️ {message}")

async def test_sentinel2_25km():
    """Test Sentinel-2 with optimal 25km configuration"""
    
    print("🛰️ SENTINEL-2 25KM OPTIMAL CONFIGURATION TEST")
    print("=" * 60)
    print("📍 Using EXACT same parameters as successful elevation test")
    print()
    
    # EXACT same coordinates as elevation test
    lat, lng = -9.38, 62.67  # Amazon Basin, Brazil
    buffer_km = 12.5  # 25km x 25km area
    
    print(f"📍 Target location: Amazon Basin, Brazil")
    print(f"🗺️ Coordinates: {lat}, {lng}")
    print(f"📏 Buffer radius: {buffer_km}km (25x25km area)")
    print()
    
    # Calculate bounding box (same method as elevation test)
    lat_delta = buffer_km / 111.0
    lng_delta = buffer_km / (111.0 * abs(math.cos(math.radians(lat))))
    
    bbox = BoundingBox(
        west=lng - lng_delta,
        south=lat - lat_delta,
        east=lng + lng_delta,
        north=lat + lat_delta
    )
    
    area_km2 = bbox.area_km2()
    print(f"🔲 Bounding Box:")
    print(f"   West: {bbox.west:.6f}°")
    print(f"   South: {bbox.south:.6f}°") 
    print(f"   East: {bbox.east:.6f}°")
    print(f"   North: {bbox.north:.6f}°")
    print(f"📐 Calculated area: {area_km2:.2f} km²")
    print(f"📏 Dimensions: {(bbox.east-bbox.west)*111:.2f}km x {(bbox.north-bbox.south)*111:.2f}km")
    print()
    
    # Initialize Sentinel-2 source
    print("🔧 Setting up Copernicus Sentinel-2 data source...")
    
    client_id = os.getenv("CDSE_CLIENT_ID")
    client_secret = os.getenv("CDSE_CLIENT_SECRET") 
    token = os.getenv("CDSE_TOKEN")
    
    if not (client_id and client_secret) and not token:
        print("⚠️ WARNING: No Copernicus credentials found!")
        print("   Set CDSE_CLIENT_ID/CDSE_CLIENT_SECRET or CDSE_TOKEN environment variables")
        print("   Continuing with limited functionality...")
    
    source = CopernicusSentinel2Source(
        client_id=client_id,
        client_secret=client_secret,
        token=token,
        progress_callback=progress_callback
    )
    
    print("✅ Copernicus Sentinel-2 source initialized")
    print()
    
    # Create download request for MAXIMUM quality
    request = DownloadRequest(
        bbox=bbox,
        data_type=DataType.IMAGERY,
        resolution=DataResolution.HIGH,  # Highest resolution
        max_file_size_mb=500.0,  # Allow large files for best quality
        output_format="GeoTIFF",
        region_name="amazon_brazil_25km_optimal"
    )
    
    try:
        # Test availability
        print("🔍 Checking Sentinel-2 data availability...")
        start_time = time.time()
        
        available = await source.check_availability(request)
        check_time = time.time() - start_time
        
        if not available:
            print(f"❌ No Sentinel-2 data available for this area")
            return
        
        print(f"✅ Sentinel-2 data available! (checked in {check_time:.2f}s)")
        print()
        
        # Estimate download size
        estimated_size = await source.estimate_size(request)
        print(f"📊 Estimated download size: {estimated_size:.2f} MB")
        print()
        
        # Download the data
        print("📥 Starting Sentinel-2 download with 25km optimal configuration...")
        download_start = time.time()
        
        result = await source.download(request)
        download_time = time.time() - download_start
        
        if result.success:
            print()
            print("🎉 SUCCESS! Sentinel-2 download completed!")
            print("=" * 60)
            print(f"📁 File path: {result.file_path}")
            print(f"📊 File size: {result.file_size_mb:.2f} MB")
            print(f"📏 Resolution: {result.resolution_m}m per pixel")
            print(f"⏱️ Download time: {download_time:.2f} seconds")
            print()
            
            # Analyze the downloaded file
            print("🔍 Analyzing downloaded Sentinel-2 data...")
            await analyze_sentinel2_file(result.file_path)
            
            # Display metadata if available
            if result.metadata:
                print("\n📋 Scene Metadata:")
                for key, value in result.metadata.items():
                    print(f"   {key}: {value}")
            
            print()
            print("💡 QUALITY COMPARISON WITH ELEVATION DATA:")
            print("=" * 60)
            print("📊 Elevation (25km): 12-15MB TIFF, 1800x1800+ pixels")
            print(f"🛰️ Sentinel-2 (25km): {result.file_size_mb:.2f}MB GeoTIFF, {result.resolution_m}m resolution")
            print()
            print("✅ Both datasets now use optimal 25km configuration!")
            
        else:
            print(f"❌ Download failed: {result.error_message}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(traceback.format_exc())
        
    finally:
        # Cleanup
        if source:
            await source.close()

async def analyze_sentinel2_file(file_path: str):
    """Analyze the downloaded Sentinel-2 file"""
    try:
        if not os.path.exists(file_path):
            print("⚠️ File not found for analysis")
            return
        
        if os.path.isdir(file_path):
            # Directory with multiple band files
            band_files = [f for f in os.listdir(file_path) if f.endswith('.tif')]
            total_size = sum(os.path.getsize(os.path.join(file_path, f)) for f in band_files)
            total_size_mb = total_size / (1024 * 1024)
            
            print(f"📁 Multi-band directory:")
            print(f"   📊 Total size: {total_size_mb:.2f} MB")
            print(f"   🎞️ Band count: {len(band_files)}")
            print(f"   📂 Band files:")
            for band_file in band_files:
                band_path = os.path.join(file_path, band_file)
                band_size_mb = os.path.getsize(band_path) / (1024 * 1024)
                print(f"      • {band_file}: {band_size_mb:.2f} MB")
                
        else:
            # Single GeoTIFF file
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"📄 Single GeoTIFF file: {file_size_mb:.2f} MB")
        
        # Try to get detailed info using GDAL if available
        try:
            from osgeo import gdal
            
            if os.path.isdir(file_path):
                # Analyze first band file
                band_files = [f for f in os.listdir(file_path) if f.endswith('.tif')]
                if band_files:
                    sample_file = os.path.join(file_path, band_files[0])
                else:
                    print("⚠️ No GeoTIFF files found in directory")
                    return
            else:
                sample_file = file_path
            
            dataset = gdal.Open(sample_file)
            if dataset:
                width = dataset.RasterXSize
                height = dataset.RasterYSize
                bands = dataset.RasterCount
                projection = dataset.GetProjection()
                geotransform = dataset.GetGeoTransform()
                
                # Calculate pixel size
                pixel_width = abs(geotransform[1])
                pixel_height = abs(geotransform[5])
                
                print(f"\n📏 Image Analysis (GDAL):")
                print(f"   📐 Dimensions: {width} x {height} pixels")
                print(f"   🔢 Total pixels: {width * height:,}")
                print(f"   🎞️ Bands: {bands}")
                print(f"   📊 Pixel size: {pixel_width:.6f}° x {pixel_height:.6f}°")
                print(f"   🗺️ Has projection: {'Yes' if projection else 'No'}")
                
                # Calculate approximate resolution in meters
                if pixel_width > 0:
                    approx_res_m = pixel_width * 111000  # Convert degrees to meters (approximate)
                    print(f"   📏 Approximate resolution: {approx_res_m:.1f}m per pixel")
                
                dataset = None  # Close file
                
        except ImportError:
            print("⚠️ GDAL not available for detailed analysis")
        except Exception as e:
            print(f"⚠️ Analysis error: {e}")
            
    except Exception as e:
        print(f"⚠️ File analysis failed: {e}")

async def main():
    """Main test execution"""
    print("Starting Sentinel-2 25km optimal configuration test...")
    print()
    
    await test_sentinel2_25km()
    
    print()
    print("🎉 Sentinel-2 test completed!")
    print()
    print("💡 Next steps:")
    print("   1. Compare Sentinel-2 file size and resolution with elevation data")
    print("   2. Verify both use optimal 25km configuration")  
    print("   3. Check image quality and geographic accuracy")

if __name__ == "__main__":
    asyncio.run(main())
