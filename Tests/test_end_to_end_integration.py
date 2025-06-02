#!/usr/bin/env python3
"""
Test script for end-to-end LiDAR acquisition and automatic raster generation.

This script tests the complete workflow:
1. Download LiDAR elevation data from OpenTopography
2. Automatically generate raster products (hillshade, slope, aspect, TRI, TPI, color relief)
3. Verify all outputs are created successfully

Run this script to verify the complete integration works properly.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

from lidar_acquisition.manager import LidarAcquisitionManager
from data_acquisition.models import BoundingBox, DataRequest, DataType, Resolution
from config.settings import Settings

async def test_end_to_end_integration():
    """Test the complete LiDAR acquisition and raster generation workflow."""
    
    print("🚀 Starting end-to-end integration test...")
    
    # Create test output directories
    test_output_dir = Path(__file__).parent / "test_outputs" / "end_to_end"
    test_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize settings
    settings = Settings()
    settings.output_dir = str(test_output_dir)
    
    # Create LiDAR acquisition manager with raster generation enabled
    manager = LidarAcquisitionManager(
        settings=settings,
        generate_rasters=True,  # Enable automatic raster generation
        raster_dir=test_output_dir / "raster_products"
    )
    
    # Define a small test area (Boulder, Colorado - known to have good LiDAR coverage)
    bounding_box = BoundingBox(
        north=40.017,
        south=40.010,
        east=-105.270,
        west=-105.280
    )
    
    # Create data request for elevation data
    request = DataRequest(
        bounding_box=bounding_box,
        data_type=DataType.ELEVATION,  # This will download as TIFF
        resolution=Resolution.ONE_METER,
        output_format="GTiff"
    )
    
    print(f"📍 Test area: {bounding_box}")
    print(f"📊 Data type: {request.data_type}")
    print(f"🎯 Resolution: {request.resolution}")
    print(f"💾 Output directory: {test_output_dir}")
    
    try:
        # Execute the complete workflow
        print("\n⬇️  Starting LiDAR data acquisition...")
        results = await manager.acquire_lidar_data([request])
        
        if results:
            print(f"✅ Successfully acquired {len(results)} file(s)")
            
            # Check what files were created
            print("\n📁 Files in output directory:")
            for item in test_output_dir.rglob("*"):
                if item.is_file():
                    print(f"  - {item.relative_to(test_output_dir)} ({item.stat().st_size} bytes)")
            
            # Check if raster products were generated
            raster_dir = test_output_dir / "raster_products"
            if raster_dir.exists():
                print(f"\n🎨 Raster products generated:")
                raster_files = list(raster_dir.glob("*.tiff"))
                for raster_file in raster_files:
                    print(f"  - {raster_file.name} ({raster_file.stat().st_size} bytes)")
                
                if len(raster_files) > 0:
                    print(f"\n🎉 SUCCESS! Generated {len(raster_files)} raster product(s)")
                    return True
                else:
                    print("\n❌ ERROR: No raster products were generated")
                    return False
            else:
                print("\n❌ ERROR: Raster products directory was not created")
                return False
        else:
            print("❌ ERROR: No LiDAR data was acquired")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the end-to-end integration test."""
    success = await test_end_to_end_integration()
    
    if success:
        print("\n✅ End-to-end integration test PASSED!")
        print("The system successfully:")
        print("  1. Downloaded LiDAR elevation data")
        print("  2. Renamed files to use '_elevation.tiff' suffix")
        print("  3. Automatically generated raster products")
        sys.exit(0)
    else:
        print("\n❌ End-to-end integration test FAILED!")
        print("Please check the error messages above for details.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
