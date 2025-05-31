#!/usr/bin/env python3
"""Direct test of Sentinel-2 download without the full application stack."""

print("SCRIPT_MESSAGE: test_sentinel2_direct.py starting execution.")

import asyncio
import sys
import os
from pathlib import Path
import math # Moved to top

print(f"SCRIPT_MESSAGE: Python version: {sys.version}")
print(f"SCRIPT_MESSAGE: Current working directory: {os.getcwd()}")
print(f"SCRIPT_MESSAGE: Script path (__file__): {Path(__file__).resolve()}")
print(f"SCRIPT_MESSAGE: Initial sys.path: {sys.path}")

# Add the app directory to the path
# Assuming test_sentinel2_direct.py is in the project root, and 'app' is a subdirectory
APP_DIR_PATH = Path(__file__).resolve().parent / "app"
sys.path.insert(0, str(APP_DIR_PATH.parent)) # Add project root so "from app..." works
# sys.path.append(str(Path(__file__).parent / "app")) # Original line from generation
print(f"SCRIPT_MESSAGE: Path to app directory: {APP_DIR_PATH}")
print(f"SCRIPT_MESSAGE: Modified sys.path: {sys.path}")

try:
    print("SCRIPT_MESSAGE: Attempting to import app modules...")
    from app.data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
    from app.data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
    from app.data_acquisition.utils.coordinates import BoundingBox
    from app.config import get_settings
    print("SCRIPT_MESSAGE: App-specific imports successful.")
except ImportError as e:
    print(f"SCRIPT_ERROR: ImportError occurred: {e}")
    print("SCRIPT_ERROR: Please check PYTHONPATH or script location relative to the 'app' directory.")
    sys.exit(1)
except Exception as e:
    print(f"SCRIPT_ERROR: An unexpected error occurred during imports: {e}")
    sys.exit(1)

print("SCRIPT_MESSAGE: Imports completed. Defining test_sentinel2_download function.")


async def test_sentinel2_download():
    """Test downloading Sentinel-2 data for different locations."""
    print("SCRIPT_MESSAGE: test_sentinel2_download async function called.")

    # Load settings
    print("SCRIPT_MESSAGE: Attempting to load settings via get_settings().")
    settings = get_settings()
    print(f"SCRIPT_MESSAGE: Settings loaded. CDSE Token present: {bool(settings.cdse_token)}, Client ID present: {bool(settings.cdse_client_id)}")

    # Create source
    print("SCRIPT_MESSAGE: Creating CopernicusSentinel2Source instance.")
    try:
        source = CopernicusSentinel2Source(
            token=settings.cdse_token,
            client_id=settings.cdse_client_id,
            client_secret=settings.cdse_client_secret
        )
        print("SCRIPT_MESSAGE: CopernicusSentinel2Source instance created successfully.")
    except Exception as e:
        print(f"SCRIPT_ERROR: Failed to create CopernicusSentinel2Source instance: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test locations with known Sentinel-2 coverage
    test_locations = [
        {
            "name": "Paris, France",
            "lat": 48.8566,
            "lng": 2.3522,
            "buffer_km": 2.0
        },
        {
            "name": "Barcelona, Spain",
            "lat": 41.3851,
            "lng": 2.1734,
            "buffer_km": 2.0
        },
        {
            "name": "California Central Valley",
            "lat": 36.7783,
            "lng": -119.4179,
            "buffer_km": 2.0
        }
    ]
    print(f"SCRIPT_MESSAGE: Starting to loop through {len(test_locations)} test locations.")

    for i, location in enumerate(test_locations):
        print(f"\nSCRIPT_MESSAGE: Testing location {i+1}/{len(test_locations)}: {location['name']}")
        print(f"SCRIPT_MESSAGE: Coordinates: {location['lat']}, {location['lng']}")

        # Calculate bounding box
        lat_delta = location['buffer_km'] / 111.0
        lng_delta = location['buffer_km'] / (111.0 * abs(math.cos(math.radians(location['lat']))))

        bbox = BoundingBox(
            west=location['lng'] - lng_delta,
            south=location['lat'] - lat_delta,
            east=location['lng'] + lng_delta,
            north=location['lat'] + lat_delta
        )

        # Create download request
        request = DownloadRequest(
            bbox=bbox,
            data_type=DataType.IMAGERY,
            resolution=DataResolution.HIGH,
            max_file_size_mb=100.0,
            output_format="GeoTIFF"
        )

        print(f"SCRIPT_MESSAGE: BBox: {bbox.west:.4f}, {bbox.south:.4f}, {bbox.east:.4f}, {bbox.north:.4f}")

        # Check availability
        try:
            print("SCRIPT_MESSAGE: Checking availability...")
            available = await source.check_availability(request)
            print(f"SCRIPT_MESSAGE: Available: {available}")

            if available:
                print("SCRIPT_MESSAGE: Starting download...")
                result = await source.download(request)
                print(f"SCRIPT_MESSAGE: Download result: success={result.success}")

                if result.success:
                    print(f"SCRIPT_MESSAGE: File: {result.file_path}")
                    print(f"SCRIPT_MESSAGE: Size: {result.file_size_mb:.2f} MB")
                    print(f"SCRIPT_MESSAGE: Resolution: {result.resolution_m} m")
                    print(f"SCRIPT_MESSAGE: Metadata: {result.metadata}")

                    # Check if file was actually created
                    if result.file_path and os.path.exists(result.file_path):
                        file_size_bytes = os.path.getsize(result.file_path)
                        file_size_mb = file_size_bytes / (1024 * 1024)
                        print(f"SCRIPT_MESSAGE: File exists on disk: {result.file_path}, Size: {file_size_mb:.2f} MB ({file_size_bytes} bytes)")
                        
                        if file_size_bytes == 0:
                            print("SCRIPT_WARNING: Downloaded file is 0 bytes.")

                        # Quick check with gdalinfo if available
                        try:
                            import subprocess
                            print(f"SCRIPT_MESSAGE: Running gdalinfo on {result.file_path}")
                            gdal_process = subprocess.run(['gdalinfo', result.file_path],
                                                          capture_output=True, text=True, timeout=20, check=False)
                            if gdal_process.returncode == 0:
                                print("SCRIPT_MESSAGE: gdalinfo successful.")
                                lines = gdal_process.stdout.split('\n')
                                for line_idx, line_content in enumerate(lines):
                                    if line_idx < 15 or 'Band' in line_content or 'Size is' in line_content: # Print more info
                                        print(f"SCRIPT_GDALINFO: {line_content.strip()}")
                            else:
                                print(f"SCRIPT_ERROR: gdalinfo failed with return code {gdal_process.returncode}.")
                                print(f"SCRIPT_GDALINFO_STDOUT: {gdal_process.stdout}")
                                print(f"SCRIPT_GDALINFO_STDERR: {gdal_process.stderr}")
                        except FileNotFoundError:
                            print("SCRIPT_WARNING: gdalinfo command not found. Cannot verify TIFF structure.")
                        except subprocess.TimeoutExpired:
                            print("SCRIPT_ERROR: gdalinfo command timed out.")
                        except Exception as e_gdal:
                            print(f"SCRIPT_WARNING: Could not run gdalinfo: {e_gdal}")
                    elif result.file_path:
                        print(f"SCRIPT_ERROR: File not found at expected path: {result.file_path}")
                    else:
                        print("SCRIPT_ERROR: Download reported success but no file path was returned.")
                else:
                    print(f"SCRIPT_ERROR: Download failed: {result.error_message}")
            else:
                print("SCRIPT_MESSAGE: No data available for this location according to check_availability.")

        except Exception as e:
            print(f"SCRIPT_ERROR: An error occurred during processing for location {location['name']}: {e}")
            import traceback
            traceback.print_exc()

    # Clean up
    print("SCRIPT_MESSAGE: All locations processed. Closing source session.")
    await source.close()
    print("SCRIPT_MESSAGE: Source session closed.")

if __name__ == "__main__":
    print("SCRIPT_MESSAGE: __main__ block reached.")
    # import math # Already moved to top
    try:
        asyncio.run(test_sentinel2_download())
        print("SCRIPT_MESSAGE: asyncio.run(test_sentinel2_download) completed.")
    except Exception as e:
        print(f"SCRIPT_ERROR: An error occurred in asyncio.run or test_sentinel2_download: {e}")
        import traceback
        traceback.print_exc()
    print("SCRIPT_MESSAGE: test_sentinel2_direct.py finished.")
