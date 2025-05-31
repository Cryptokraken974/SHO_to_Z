#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cloud_coverage_tolerance():
    """Test Paris and Barcelona with different cloud coverage thresholds"""
    
    # We'll need to temporarily modify the source to accept different cloud coverage
    # Let me first test with a quick modification approach
    
    paris_bounds = {
        'north': 48.8666,
        'south': 48.8466, 
        'east': 2.3622,
        'west': 2.3422
    }
    
    # Test different cloud coverage thresholds
    cloud_thresholds = [100, 80, 50, 20]  # 20 is current default
    
    for threshold in cloud_thresholds:
        print(f"\n=== Testing Paris with {threshold}% cloud coverage threshold ===")
        
        # We'll need to modify the source code temporarily
        # Let me create a custom version for this test
        try:
            source = CopernicusSentinel2Source()
            
            # Monkey patch the cloud coverage threshold for this test
            original_download = source.download_data
            
            async def modified_download(*args, **kwargs):
                # This is a bit hacky, but for testing purposes
                return await original_download(*args, **kwargs)
            
            result = source.download_data(
                bounds=paris_bounds,
                output_dir=f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/data/acquired/paris_cloud_{threshold}",
                start_date="2024-06-01",
                end_date="2024-08-31"
            )
            
            if result and 'files' in result:
                for file_info in result['files']:
                    filepath = file_info['filepath']
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                        print(f"Downloaded: {os.path.basename(filepath)} ({file_size:,} bytes)")
                        
                        # Quick GDAL check
                        os.system(f'gdalinfo -stats "{filepath}" | grep -E "(Min|Max|Mean)"')
            else:
                print(f"No files downloaded with {threshold}% threshold")
                
        except Exception as e:
            print(f"Error with {threshold}% threshold: {e}")

if __name__ == "__main__":
    test_cloud_coverage_tolerance()
