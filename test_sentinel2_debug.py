#!/usr/bin/env python3
"""
🛰️ SENTINEL-2 25KM DEBUG TEST - Enhanced Debugging
==================================================

Debug version of Sentinel-2 test with broader time range and detailed logging
to understand why data is not found for the Amazon Basin location.
"""

import asyncio
import sys
import os
import time
import math
from pathlib import Path
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

try:
    from data_acquisition.sources.sentinel2 import Sentinel2Source
    from data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
    from data_acquisition.utils.coordinates import BoundingBox
    
    # Import STAC components for direct debugging  
    from pystac_client import Client
    import planetary_computer as pc
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure dependencies are installed: pip install pystac-client planetary-computer")
    sys.exit(1)

async def debug_availability(bbox, verbose=True):
    """Debug Sentinel-2 availability with detailed logging"""
    
    if verbose:
        print("🔍 DEBUGGING SENTINEL-2 AVAILABILITY")
        print("-" * 40)
    
    try:
        # Initialize STAC client
        client = Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=pc.sign_inplace
        )
        
        if verbose:
            print(f"✅ STAC client initialized")
            print(f"📦 Bounding box: [{bbox.west:.6f}, {bbox.south:.6f}, {bbox.east:.6f}, {bbox.north:.6f}]")
        
        # Try different time ranges
        time_ranges = [
            ("2024-01-01T00:00:00Z/2025-06-04T23:59:59Z", "Last 1.5 years"),
            ("2023-01-01T00:00:00Z/2025-06-04T23:59:59Z", "Last 2.5 years"),  
            ("2022-01-01T00:00:00Z/2025-06-04T23:59:59Z", "Last 3.5 years"),
            ("2020-01-01T00:00:00Z/2025-06-04T23:59:59Z", "Last 5 years"),
        ]
        
        for time_range, description in time_ranges:
            if verbose:
                print(f"\n🔍 Searching {description} ({time_range.split('/')[0][:4]} - {time_range.split('/')[1][:4]})")
            
            try:
                search = client.search(
                    collections=["sentinel-2-l2a"],
                    bbox=[bbox.west, bbox.south, bbox.east, bbox.north],
                    datetime=time_range,
                    limit=10  # Get more items for analysis
                )
                
                items = list(search.items())
                
                if verbose:
                    print(f"   📊 Found {len(items)} items")
                
                if items:
                    # Analyze the items found
                    if verbose:
                        print("   📋 Item details:")
                        for i, item in enumerate(items[:3]):  # Show first 3
                            print(f"      {i+1}. ID: {item.id}")
                            print(f"         Date: {item.datetime}")
                            if hasattr(item, 'properties'):
                                cloud_cover = item.properties.get('eo:cloud_cover', 'unknown')
                                print(f"         Cloud cover: {cloud_cover}%")
                    
                    return True, items
                    
            except Exception as e:
                if verbose:
                    print(f"   ❌ Error searching {description}: {e}")
                continue
        
        return False, []
        
    except Exception as e:
        if verbose:
            print(f"💥 Client initialization error: {e}")
        return False, []

async def test_sentinel2_debug():
    """Debug test for Sentinel-2 availability"""
    
    print("🛰️ SENTINEL-2 DEBUG TEST")
    print("=" * 50)
    print("🔍 Enhanced debugging for Amazon Basin location")
    print()
    
    # Same coordinates as elevation test
    lat, lng = -9.38, 62.67  # Amazon Basin, Brazil
    buffer_km = 12.5  # 25km x 25km area
    
    print(f"📍 Target location: Amazon Basin, Brazil")
    print(f"📐 Coordinates: {lat}°, {lng}°")
    print(f"📏 Buffer radius: {buffer_km}km")
    print()
    
    # Calculate bounding box
    buffer_deg = buffer_km / 111.32
    bbox = BoundingBox(
        west=lng - buffer_deg,
        east=lng + buffer_deg,
        south=lat - buffer_deg,
        north=lat + buffer_deg
    )
    
    print(f"📦 Calculated bounding box:")
    print(f"   West: {bbox.west:.6f}°")
    print(f"   East: {bbox.east:.6f}°")
    print(f"   South: {bbox.south:.6f}°")
    print(f"   North: {bbox.north:.6f}°")
    print(f"   Area: {bbox.area_km2():.1f} km²")
    print()
    
    # Debug availability
    available, items = await debug_availability(bbox, verbose=True)
    
    if available:
        print(f"\n✅ SUCCESS: Found {len(items)} Sentinel-2 items!")
        print("\n📊 ITEM ANALYSIS:")
        print("-" * 30)
        
        # Analyze cloud coverage and dates
        dates = []
        cloud_covers = []
        
        for item in items[:5]:  # Analyze first 5 items
            print(f"🛰️ Item: {item.id}")
            print(f"   📅 Date: {item.datetime}")
            dates.append(item.datetime)
            
            if hasattr(item, 'properties'):
                cloud_cover = item.properties.get('eo:cloud_cover', None)
                if cloud_cover is not None:
                    cloud_covers.append(cloud_cover)
                    print(f"   ☁️ Cloud cover: {cloud_cover:.1f}%")
                else:
                    print(f"   ☁️ Cloud cover: Unknown")
                    
                # Check for other relevant properties
                for key, value in item.properties.items():
                    if key in ['platform', 'instruments', 'gsd']:
                        print(f"   📋 {key}: {value}")
            print()
        
        # Summary
        if cloud_covers:
            avg_cloud = sum(cloud_covers) / len(cloud_covers)
            min_cloud = min(cloud_covers)
            print(f"📊 Cloud cover analysis:")
            print(f"   Average: {avg_cloud:.1f}%")
            print(f"   Minimum: {min_cloud:.1f}%")
            print(f"   Items with <20% clouds: {len([c for c in cloud_covers if c < 20])}")
        
        if dates:
            latest_date = max(dates)
            earliest_date = min(dates)
            print(f"📅 Date range:")
            print(f"   Latest: {latest_date}")
            print(f"   Earliest: {earliest_date}")
        
        print(f"\n🎯 RECOMMENDATION:")
        print("✅ Data is available! You can proceed with download.")
        
        if cloud_covers and min(cloud_covers) < 30:
            print("🌤️ Found scenes with acceptable cloud cover (<30%)")
        elif cloud_covers:
            print("⚠️ High cloud cover - may affect image quality")
        
        # Test actual download with the Sentinel2Source
        print(f"\n🔄 Testing actual Sentinel2Source...")
        source = Sentinel2Source()
        
        request = DownloadRequest(
            bbox=bbox,
            data_type=DataType.IMAGERY,
            resolution=DataResolution.HIGH,
            output_format="GEOTIFF"
        )
        
        print("   🔍 Checking availability via Sentinel2Source...")
        source_available = await source.check_availability(request)
        print(f"   📊 Sentinel2Source result: {'✅ Available' if source_available else '❌ Not available'}")
        
        if source_available:
            estimated_size = await source.estimate_size(request)
            print(f"   📊 Estimated size: {estimated_size:.1f} MB")
            
            print(f"\n⬬ Attempting download...")
            try:
                result = await source.download(request)
                
                if result.success:
                    print(f"✅ Download successful!")
                    print(f"📁 File: {result.file_path}")
                    print(f"📊 Size: {result.file_size_mb:.1f} MB")
                else:
                    print(f"❌ Download failed: {result.error_message}")
            except Exception as e:
                print(f"💥 Download error: {e}")
        
    else:
        print("\n❌ NO DATA FOUND")
        print("This could be due to:")
        print("• Location is over ocean/water")
        print("• No Sentinel-2 coverage for this specific area")
        print("• All scenes have very high cloud cover")
        print("• API or connection issues")
        
        # Try a known good location for comparison
        print(f"\n🔄 Testing known good location (São Paulo, Brazil)...")
        test_lat, test_lng = -23.55, -46.63  # São Paulo
        test_buffer_deg = 5 / 111.32  # 5km buffer
        
        test_bbox = BoundingBox(
            west=test_lng - test_buffer_deg,
            east=test_lng + test_buffer_deg,
            south=test_lat - test_buffer_deg,
            north=test_lat + test_buffer_deg
        )
        
        test_available, test_items = await debug_availability(test_bbox, verbose=False)
        
        if test_available:
            print(f"✅ São Paulo test: Found {len(test_items)} items")
            print("🔍 API is working - issue is likely with the Amazon location")
        else:
            print("❌ São Paulo test also failed - API issue")

if __name__ == "__main__":
    print("🚀 Starting Sentinel-2 debug test...")
    print()
    
    try:
        asyncio.run(test_sentinel2_debug())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
