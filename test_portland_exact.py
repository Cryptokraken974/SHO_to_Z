#!/usr/bin/env python3

import os
import sys
import asyncio
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
from app.data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
from app.data_acquisition.utils.coordinates import BoundingBox
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_exact_shell_script_coordinates():
    """Test using the exact same Portland coordinates as the successful shell script"""
    
    source = CopernicusSentinel2Source()
    
    # These are the exact coordinates from the shell script:
    # LAT=45.5152, LNG=-122.6784, 5km buffer
    # Which gives us: WEST=-122.723400, SOUTH=45.470200, EAST=-122.633400, NORTH=45.560200
    
    bbox = BoundingBox(
        west=-122.723400,
        south=45.470200,
        east=-122.633400,
        north=45.560200
    )
    
    print("=== Testing with EXACT shell script coordinates ===")
    print("Portland, Oregon with 5km buffer:")
    print(f"  West: {bbox.west}")
    print(f"  South: {bbox.south}")
    print(f"  East: {bbox.east}")
    print(f"  North: {bbox.north}")
    print()
    
    # Create download request
    download_request = DownloadRequest(
        bbox=bbox,
        data_type=DataType.IMAGERY,
        resolution=DataResolution.HIGH,
        max_file_size_mb=100.0,
        output_format="GeoTIFF"
    )
    
    try:
        result = await source.download(download_request)
        
        if result.success:
            print(f"✅ Download successful!")
            print(f"📁 File: {result.file_path}")
            
            if os.path.exists(result.file_path):
                file_size = os.path.getsize(result.file_path)
                print(f"📊 File size: {file_size:,} bytes")
                
                # Compare with our reference file
                ref_size = os.path.getsize("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/test_shell_script_dn.tif")
                print(f"📋 Reference file size: {ref_size:,} bytes")
                
                if abs(file_size - ref_size) < 100000:  # Within 100KB
                    print("✅ File size matches reference!")
                else:
                    print("⚠️ File size differs from reference")
                
                # Check metadata
                if result.metadata:
                    print(f"  ☁️ Cloud: {result.metadata.get('cloud_cover', 'Unknown')}%")
                    print(f"  📅 Date: {result.metadata.get('acquisition_date', 'Unknown')}")
                
                # Detailed statistics comparison
                print("\n📊 GDAL Statistics:")
                os.system(f'gdalinfo -stats "{result.file_path}"')
                
                # Compare with reference
                print("\n📋 Reference File Statistics:")
                os.system(f'gdalinfo -stats "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/test_shell_script_dn.tif"')
                
            else:
                print(f"❌ File not found: {result.file_path}")
        else:
            print("❌ Download failed")
            print(f"Error: {result.error_message}")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await source.close()

if __name__ == "__main__":
    asyncio.run(test_exact_shell_script_coordinates())
