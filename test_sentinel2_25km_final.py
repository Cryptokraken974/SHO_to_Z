#!/usr/bin/env python3
"""
🛰️ SENTINEL-2 25KM OPTIMAL CONFIGURATION TEST (NO AUTH REQUIRED)
================================================================

Test Sentinel-2 data with the EXACT same region and 25km configuration 
as our successful elevation data test using Microsoft Planetary Computer STAC API.

Based on the elevation test success:
- Location: Amazon Basin, Brazil (-9.38, 62.67)  
- Buffer: 12.5km radius (25x25km area)
- Objective: Get highest resolution Sentinel-2 GeoTIFF
- Source: Microsoft Planetary Computer (no authentication required)
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

try:
    from data_acquisition.sources.sentinel2 import Sentinel2Source
    from data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
    from data_acquisition.utils.coordinates import BoundingBox
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the app directory structure is correct and dependencies are installed")
    sys.exit(1)

async def progress_callback(update):
    """Handle progress updates"""
    message = update.get("message", "")
    progress = update.get("progress", 0)
    if progress > 0:
        print(f"   📊 {message} ({progress:.1f}%)")
    else:
        print(f"   ℹ️ {message}")

def analyze_file_detailed(file_path):
    """Analyze downloaded file with detailed information"""
    if not file_path.exists():
        return {"exists": False}
    
    # Basic file info
    file_size = file_path.stat().st_size
    size_mb = file_size / (1024 * 1024)
    
    info = {
        "exists": True,
        "path": str(file_path),
        "size_bytes": file_size,
        "size_mb": round(size_mb, 2),
        "size_kb": round(file_size / 1024, 1),
        "extension": file_path.suffix.lower()
    }
    
    # Try to get image dimensions if it's a GeoTIFF
    if file_path.suffix.lower() in ['.tif', '.tiff']:
        try:
            from osgeo import gdal
            dataset = gdal.Open(str(file_path))
            if dataset:
                info.update({
                    "width": dataset.RasterXSize,
                    "height": dataset.RasterYSize,
                    "bands": dataset.RasterCount,
                    "resolution": f"{dataset.RasterXSize}x{dataset.RasterYSize}",
                    "driver": dataset.GetDriver().ShortName
                })
                
                # Get geotransform info
                geotransform = dataset.GetGeoTransform()
                if geotransform:
                    pixel_width = abs(geotransform[1])
                    pixel_height = abs(geotransform[5])
                    info.update({
                        "pixel_size_x": pixel_width,
                        "pixel_size_y": pixel_height,
                        "pixel_size_degrees": round(pixel_width, 6)
                    })
                
                dataset = None
        except Exception as e:
            info["gdal_error"] = str(e)
    
    return info

async def test_sentinel2_25km():
    """Test Sentinel-2 with optimal 25km configuration"""
    
    print("🛰️ SENTINEL-2 25KM OPTIMAL CONFIGURATION TEST")
    print("=" * 60)
    print("📍 Using EXACT same parameters as successful elevation test")
    print("🔓 Using Microsoft Planetary Computer (no authentication required)")
    print()
    
    # EXACT same coordinates as elevation test
    lat, lng = -9.38, 62.67  # Amazon Basin, Brazil
    buffer_km = 12.5  # 25km x 25km area
    
    print(f"📍 Target location: Amazon Basin, Brazil")
    print(f"📐 Coordinates: {lat}°, {lng}°")
    print(f"📏 Buffer radius: {buffer_km}km (Total area: 25x25km)")
    print()
    
    # Calculate buffer in degrees (111.32 km per degree)
    buffer_deg = buffer_km / 111.32
    
    # Create bounding box with exact same calculation as elevation test
    bbox = BoundingBox(
        west=lng - buffer_deg,
        east=lng + buffer_deg,
        south=lat - buffer_deg,
        north=lat + buffer_deg
    )
    
    print(f"📦 Bounding box:")
    print(f"   West: {bbox.west:.6f}°")
    print(f"   East: {bbox.east:.6f}°") 
    print(f"   South: {bbox.south:.6f}°")
    print(f"   North: {bbox.north:.6f}°")
    print(f"   Area: {bbox.area_km2():.1f} km²")
    print()
    
    # Initialize Sentinel-2 source
    print("🛰️ Initializing Sentinel-2 source...")
    source = Sentinel2Source(progress_callback=progress_callback)
    
    # Create download request
    request = DownloadRequest(
        bbox=bbox,
        data_type=DataType.IMAGERY,
        resolution=DataResolution.HIGH,
        output_format="GEOTIFF"
    )
    
    print(f"📋 Download request:")
    print(f"   Data type: {request.data_type}")
    print(f"   Resolution: {request.resolution}")
    print(f"   Format: {request.output_format}")
    print()
    
    # Check availability
    print("🔍 Checking data availability...")
    start_time = time.time()
    
    try:
        available = await source.check_availability(request)
        check_time = time.time() - start_time
        
        if not available:
            print(f"❌ No Sentinel-2 data available for this region")
            return
        
        print(f"✅ Data available (checked in {check_time:.1f}s)")
        
        # Estimate size
        estimated_size = await source.estimate_size(request)
        print(f"📊 Estimated download size: {estimated_size:.1f} MB")
        print()
        
        # Perform download
        print("⬬ Starting Sentinel-2 download...")
        print("   This may take several minutes for high-resolution imagery...")
        
        download_start = time.time()
        result = await source.download(request)
        download_time = time.time() - download_start
        
        print(f"✅ Download completed in {download_time:.1f}s")
        print()
        
        # Analyze results
        print("📋 DOWNLOAD RESULTS:")
        print("=" * 40)
        
        if result.success:
            print(f"✅ Status: SUCCESS")
            print(f"📁 Output file: {result.file_path}")
            print(f"📊 Reported size: {result.size_mb:.2f} MB")
            print()
            
            # Detailed file analysis
            if result.file_path:
                file_path = Path(result.file_path)
                analysis = analyze_file_detailed(file_path)
                
                print("🔍 DETAILED FILE ANALYSIS:")
                print("-" * 30)
                
                if analysis["exists"]:
                    print(f"📁 File: {analysis['path']}")
                    print(f"📊 Size: {analysis['size_mb']} MB ({analysis['size_kb']} KB)")
                    print(f"📏 Bytes: {analysis['size_bytes']:,}")
                    
                    if "resolution" in analysis:
                        print(f"🖼️ Resolution: {analysis['resolution']}")
                        print(f"🎨 Bands: {analysis['bands']}")
                        print(f"🔧 Format: {analysis['driver']}")
                        
                        if "pixel_size_degrees" in analysis:
                            print(f"📐 Pixel size: {analysis['pixel_size_degrees']:.6f}°")
                            
                            # Calculate equivalent resolution at this latitude
                            lat_correction = math.cos(math.radians(abs(lat)))
                            meters_per_degree_x = 111320 * lat_correction
                            meters_per_degree_y = 111320
                            
                            pixel_size_m_x = analysis['pixel_size_degrees'] * meters_per_degree_x
                            pixel_size_m_y = analysis['pixel_size_degrees'] * meters_per_degree_y
                            
                            print(f"📏 Pixel size: ~{pixel_size_m_x:.1f}m x {pixel_size_m_y:.1f}m")
                else:
                    print("❌ File not found or inaccessible")
                
        else:
            print(f"❌ Status: FAILED")
            if result.error:
                print(f"💥 Error: {result.error}")
        
        print()
        
        # Compare with elevation test results
        print("📊 COMPARISON WITH ELEVATION TEST:")
        print("-" * 40)
        print("Elevation test (25km area):")
        print("  • File size: ~13,500 KB (13.5 MB)")
        print("  • Resolution: 1800x1800+ pixels")
        print("  • Success rate: 100%")
        print()
        
        if result.success and result.file_path:
            file_path = Path(result.file_path)
            if file_path.exists():
                size_comparison = file_path.stat().st_size / (13.5 * 1024 * 1024)
                print(f"Sentinel-2 test (25km area):")
                print(f"  • File size: {analysis['size_kb']} KB ({analysis['size_mb']} MB)")
                if "resolution" in analysis:
                    print(f"  • Resolution: {analysis['resolution']}")
                print(f"  • Size ratio vs elevation: {size_comparison:.2f}x")
                
                # Quality assessment
                if analysis['size_mb'] > 10:
                    print("  ✅ HIGH QUALITY: Large file size indicates good detail")
                elif analysis['size_mb'] > 5:
                    print("  ⚠️ MEDIUM QUALITY: Moderate file size")
                else:
                    print("  ❌ LOW QUALITY: Small file size may indicate compression")
        
        print()
        print("🎯 CONCLUSION:")
        print("--------------")
        
        total_time = time.time() - start_time
        print(f"⏱️ Total test time: {total_time:.1f}s")
        
        if result.success:
            print("✅ Sentinel-2 25km configuration test SUCCESSFUL")
            print("🏆 Same region as elevation test produces high-quality satellite imagery")
        else:
            print("❌ Sentinel-2 25km configuration test FAILED")
            print("🔄 May need to retry or check different time periods")
            
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    print("🚀 Starting Sentinel-2 25km optimal configuration test...")
    print()
    
    try:
        asyncio.run(test_sentinel2_25km())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
