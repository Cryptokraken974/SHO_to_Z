#!/usr/bin/env python3
"""Test Sentinel-2 download for Portland Oregon (same as working shell script)."""

import asyncio
import sys
import os
from pathlib import Path
import math

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
from app.data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
from app.data_acquisition.utils.coordinates import BoundingBox
from app.config import get_settings

async def test_portland_download():
    """Test downloading Sentinel-2 data for Portland Oregon (same as shell script)."""
    print("Testing Portland Oregon download...")

    # Load settings
    settings = get_settings()
    print(f"CDSE Token present: {bool(settings.cdse_token)}, Client ID present: {bool(settings.cdse_client_id)}")

    # Create source
    source = CopernicusSentinel2Source(
        token=settings.cdse_token,
        client_id=settings.cdse_client_id,
        client_secret=settings.cdse_client_secret
    )

    # Portland Oregon coordinates (same as shell script)
    lat = 45.5152
    lng = -122.6784
    buffer_km = 5.0

    # Calculate bounding box (same as shell script)
    lat_delta = buffer_km / 111.0
    lng_delta = buffer_km / 111.0

    bbox = BoundingBox(
        west=lng - lng_delta,
        south=lat - lat_delta,
        east=lng + lng_delta,
        north=lat + lat_delta
    )

    print(f"Portland coordinates: {lat}, {lng}")
    print(f"BBox: {bbox.west:.6f}, {bbox.south:.6f}, {bbox.east:.6f}, {bbox.north:.6f}")

    # Create download request
    request = DownloadRequest(
        bbox=bbox,
        data_type=DataType.IMAGERY,
        resolution=DataResolution.HIGH,
        max_file_size_mb=100.0,
        output_format="GeoTIFF"
    )

    try:
        # Check availability
        print("Checking availability...")
        available = await source.check_availability(request)
        print(f"Available: {available}")

        if available:
            print("Starting download...")
            result = await source.download(request)
            print(f"Download result: success={result.success}")

            if result.success:
                print(f"File: {result.file_path}")
                print(f"Size: {result.file_size_mb:.2f} MB")
                print(f"Metadata: {result.metadata}")

                # Check if file was actually created
                if result.file_path and os.path.exists(result.file_path):
                    file_size_bytes = os.path.getsize(result.file_path)
                    file_size_mb = file_size_bytes / (1024 * 1024)
                    print(f"File exists: {result.file_path}, Size: {file_size_mb:.2f} MB")
                    
                    # Check statistics with gdalinfo
                    try:
                        import subprocess
                        result_stats = subprocess.run(['gdalinfo', '-stats', result.file_path],
                                                    capture_output=True, text=True, timeout=30, check=False)
                        if result_stats.returncode == 0:
                            print("GDALINFO Statistics:")
                            lines = result_stats.stdout.split('\n')
                            for line in lines:
                                if 'Minimum=' in line or 'Maximum=' in line or 'Mean=' in line or 'StdDev=' in line:
                                    print(f"  {line.strip()}")
                        else:
                            print(f"gdalinfo failed: {result_stats.stderr}")
                    except Exception as e:
                        print(f"Could not run gdalinfo: {e}")
                else:
                    print(f"File not found: {result.file_path}")
            else:
                print(f"Download failed: {result.error_message}")
        else:
            print("No data available for Portland")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await source.close()

if __name__ == "__main__":
    asyncio.run(test_portland_download())
