#!/usr/bin/env python3
"""
Test script to manually trigger raster processing on the existing elevation TIFF
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, 'app')

from processing.tiff_processing import process_all_raster_products
from data_acquisition.utils.coordinates import BoundingBox

class MockRequest:
    """Mock request object with coordinates for the existing elevation TIFF"""
    def __init__(self):
        # Coordinates for the 3.10S_57.70W region
        self.bbox = BoundingBox(west=-57.75, south=-3.15, east=-57.65, north=-3.05)
        self.region_name = None

async def test_raster_processing():
    """Test the raster processing on the existing elevation TIFF"""
    print("🚀 Testing automatic raster processing...")
    
    # Path to the existing elevation TIFF
    tiff_path = "input/3.10S_57.70W/lidar/3.097S_57.700W_elevation.tiff"
    
    # Check if file exists
    if not os.path.exists(tiff_path):
        print(f"❌ ERROR: TIFF file not found: {tiff_path}")
        return False
    
    print(f"📁 Processing TIFF: {tiff_path}")
    
    # Create mock request with proper coordinates
    request = MockRequest()
    
    # Process all raster products
    try:
        result = await process_all_raster_products(tiff_path, None, request)
        
        print("\n📊 PROCESSING RESULTS:")
        print(f"✅ Total tasks: {result.get('total_tasks', 0)}")
        print(f"✅ Successful: {result.get('successful', 0)}")
        print(f"❌ Failed: {result.get('failed', 0)}")
        print(f"⏱️ Total time: {result.get('total_time', 0):.2f} seconds")
        print(f"📂 Output directory: {result.get('output_directory', 'N/A')}")
        
        return result.get('successful', 0) > 0
        
    except Exception as e:
        print(f"❌ ERROR during processing: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_raster_processing())
    if success:
        print("\n🎉 SUCCESS: Raster processing completed!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: Raster processing failed!")
        sys.exit(1)
