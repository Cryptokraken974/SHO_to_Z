#!/usr/bin/env python3
"""
Test script for Brazilian Elevation Data Sources Integration
Tests the geographic routing and Brazilian data source functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.data_acquisition.geographic_router import GeographicRouter, download_elevation_data
from app.data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
from app.data_acquisition.utils.coordinates import BoundingBox

class ProgressTracker:
    """Simple progress tracker for testing."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.events = []
    
    async def __call__(self, event):
        self.events.append(event)
        if self.verbose:
            event_type = event.get('type', 'unknown')
            message = event.get('message', '')
            
            if event_type == 'routing_info':
                print(f"🗺️  ROUTING: {message}")
            elif event_type == 'source_selected':
                print(f"🎯 SOURCE: {message}")
            elif event_type == 'download_started':
                print(f"⬇️  DOWNLOAD: {message}")
            elif event_type == 'download_progress':
                progress = event.get('progress', 0)
                print(f"📊 PROGRESS: {message} ({progress}%)")
            elif event_type == 'download_complete':
                print(f"✅ COMPLETE: {message}")
            elif event_type == 'cache_hit':
                print(f"💾 CACHE: {message}")
            elif event_type == 'source_failed':
                print(f"❌ FAILED: {message}")
            elif event_type == 'routing_success':
                print(f"🎉 SUCCESS: {message}")
            else:
                print(f"ℹ️  {event_type.upper()}: {message}")

async def test_geographic_detection():
    """Test geographic region detection."""
    print("\n" + "="*60)
    print("TESTING GEOGRAPHIC REGION DETECTION")
    print("="*60)
    
    router = GeographicRouter()
    
    test_locations = [
        # US locations
        BoundingBox(west=-122.5, east=-122.3, south=37.7, north=37.9, name="San Francisco, CA"),
        BoundingBox(west=-74.1, east=-73.9, south=40.6, north=40.8, name="New York, NY"),
        
        # Brazilian locations
        BoundingBox(west=-47.1, east=-46.9, south=-23.7, north=-23.5, name="São Paulo, Brazil"),
        BoundingBox(west=-43.3, east=-43.1, south=-23.0, north=-22.8, name="Rio de Janeiro, Brazil"),
        
        # Amazon locations
        BoundingBox(west=-60.1, east=-59.9, south=-3.2, north=-3.0, name="Manaus, Amazon"),
        BoundingBox(west=-67.1, east=-66.9, south=-10.6, north=-10.4, name="Amazon Rainforest"),
        
        # Other South America
        BoundingBox(west=-58.5, east=-58.3, south=-34.7, north=-34.5, name="Buenos Aires, Argentina"),
    ]
    
    for bbox in test_locations:
        region_info = router.get_region_info(bbox)
        print(f"\n📍 {bbox.name}:")
        print(f"   Region: {region_info['region']} ({region_info['region_name']})")
        print(f"   Optimal sources: {', '.join(region_info['optimal_sources'])}")
        print(f"   Center: {region_info['center_lat']:.2f}, {region_info['center_lng']:.2f}")

async def test_availability_check():
    """Test data source availability checking."""
    print("\n" + "="*60)
    print("TESTING DATA SOURCE AVAILABILITY")
    print("="*60)
    
    router = GeographicRouter()
    
    test_locations = [
        BoundingBox(west=-47.1, east=-46.9, south=-23.7, north=-23.5, name="São Paulo, Brazil"),
        BoundingBox(west=-60.1, east=-59.9, south=-3.2, north=-3.0, name="Manaus, Amazon"),
        BoundingBox(west=-122.5, east=-122.3, south=37.7, north=37.9, name="San Francisco, CA"),
    ]
    
    for bbox in test_locations:
        print(f"\n📍 Checking availability for {bbox.name}:")
        
        request = DownloadRequest(
            bbox=bbox,
            data_type=DataType.ELEVATION,
            resolution=DataResolution.MEDIUM
        )
        
        availability = await router.check_availability_all(request)
        
        for source, available in availability.items():
            status = "✅ Available" if available else "❌ Not available"
            print(f"   {source}: {status}")

async def test_brazilian_download():
    """Test actual download from Brazilian sources."""
    print("\n" + "="*60)
    print("TESTING BRAZILIAN DATA DOWNLOAD")
    print("="*60)
    
    # Small area in São Paulo for testing
    sao_paulo_bbox = BoundingBox(
        west=-46.65, east=-46.63, 
        south=-23.55, north=-23.53, 
        name="São Paulo Downtown (small test area)"
    )
    
    print(f"📍 Testing download for: {sao_paulo_bbox.name}")
    print(f"   Bbox: {sao_paulo_bbox.west}, {sao_paulo_bbox.south} to {sao_paulo_bbox.east}, {sao_paulo_bbox.north}")
    print(f"   Area: {sao_paulo_bbox.area_km2():.2f} km²")
    
    progress_tracker = ProgressTracker(verbose=True)
    
    try:
        result = await download_elevation_data(
            bbox=sao_paulo_bbox,
            resolution=DataResolution.MEDIUM,
            progress_callback=progress_tracker
        )
        
        if result.success:
            print(f"\n🎉 DOWNLOAD SUCCESSFUL!")
            print(f"   File: {result.file_path}")
            print(f"   Size: {result.file_size_mb:.2f} MB")
            print(f"   Resolution: {result.resolution_m}m")
            
            if result.metadata:
                print(f"   Source: {result.metadata.get('source', 'Unknown')}")
                print(f"   Provider: {result.metadata.get('provider', 'Unknown')}")
                print(f"   Routing region: {result.metadata.get('routing_region', 'Unknown')}")
        else:
            print(f"\n❌ DOWNLOAD FAILED: {result.error_message}")
            
    except Exception as e:
        print(f"\n💥 EXCEPTION: {str(e)}")

async def test_amazon_download():
    """Test download from Amazon rainforest area."""
    print("\n" + "="*60)
    print("TESTING AMAZON RAINFOREST DATA DOWNLOAD")
    print("="*60)
    
    # Small area near Manaus
    amazon_bbox = BoundingBox(
        west=-60.05, east=-60.03, 
        south=-3.12, north=-3.10, 
        name="Amazon Rainforest near Manaus (small test area)"
    )
    
    print(f"📍 Testing download for: {amazon_bbox.name}")
    print(f"   Bbox: {amazon_bbox.west}, {amazon_bbox.south} to {amazon_bbox.east}, {amazon_bbox.north}")
    print(f"   Area: {amazon_bbox.area_km2():.2f} km²")
    
    progress_tracker = ProgressTracker(verbose=True)
    
    try:
        result = await download_elevation_data(
            bbox=amazon_bbox,
            resolution=DataResolution.MEDIUM,
            progress_callback=progress_tracker
        )
        
        if result.success:
            print(f"\n🎉 DOWNLOAD SUCCESSFUL!")
            print(f"   File: {result.file_path}")
            print(f"   Size: {result.file_size_mb:.2f} MB")
            print(f"   Resolution: {result.resolution_m}m")
            
            if result.metadata:
                print(f"   Source: {result.metadata.get('source', 'Unknown')}")
                print(f"   Provider: {result.metadata.get('provider', 'Unknown')}")
                print(f"   Routing region: {result.metadata.get('routing_region', 'Unknown')}")
        else:
            print(f"\n❌ DOWNLOAD FAILED: {result.error_message}")
            
    except Exception as e:
        print(f"\n💥 EXCEPTION: {str(e)}")

async def main():
    """Run all tests."""
    print("🌎 BRAZILIAN ELEVATION DATA SOURCES INTEGRATION TEST")
    print("=" * 70)
    
    # Check if required packages are available
    try:
        import aiohttp
        print("✅ aiohttp available")
    except ImportError:
        print("❌ aiohttp not available - install with: pip install aiohttp")
        return
    
    try:
        import geopandas
        print("✅ geopandas available")
    except ImportError:
        print("❌ geopandas not available - install with: pip install geopandas")
        return
    
    # Run tests
    await test_geographic_detection()
    await test_availability_check()
    
    # Only run download tests if user confirms (to avoid unnecessary downloads)
    print("\n" + "="*60)
    response = input("Run actual download tests? This will download small elevation data files. (y/N): ")
    
    if response.lower().startswith('y'):
        await test_brazilian_download()
        await test_amazon_download()
    else:
        print("Skipping download tests.")
    
    print("\n" + "="*60)
    print("🏁 ALL TESTS COMPLETED")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
