#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_high_cloud_tolerance():
    """Test Paris and Barcelona with 100% cloud coverage tolerance"""
    
    source = CopernicusSentinel2Source()
    
    locations = {
        'paris_100cloud': {
            'north': 48.8666,
            'south': 48.8466, 
            'east': 2.3622,
            'west': 2.3422,
            'description': 'Paris with 100% cloud tolerance'
        },
        'barcelona_100cloud': {
            'north': 41.4001,
            'south': 41.3801, 
            'east': 2.1740,
            'west': 2.1540,
            'description': 'Barcelona with 100% cloud tolerance'
        }
    }
    
    for location_name, bounds in locations.items():
        print(f"\n=== Testing {bounds['description']} ===")
        
        try:
            result = source.download_data(
                bounds=bounds,
                output_dir=f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/data/acquired/{location_name}",
                start_date="2024-06-01",
                end_date="2024-08-31"
            )
            
            if result and 'files' in result:
                for file_info in result['files']:
                    filepath = file_info['filepath']
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                        print(f"Downloaded: {os.path.basename(filepath)}")
                        print(f"File size: {file_size:,} bytes")
                        
                        # Check metadata
                        if 'metadata' in file_info:
                            metadata = file_info['metadata']
                            print(f"Cloud coverage: {metadata.get('cloud_coverage', 'Unknown')}%")
                            print(f"Acquisition date: {metadata.get('acquisition_date', 'Unknown')}")
                        
                        # Quick GDAL statistics
                        print("GDAL Statistics:")
                        os.system(f'gdalinfo -stats "{filepath}" | grep -E "(Min|Max|Mean|Band [1-4])"')
                    else:
                        print(f"File not found: {filepath}")
            else:
                print(f"No files downloaded for {location_name}")
                
        except Exception as e:
            print(f"Error downloading {location_name}: {e}")

if __name__ == "__main__":
    test_high_cloud_tolerance()
