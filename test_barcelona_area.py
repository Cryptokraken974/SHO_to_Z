#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_barcelona_and_nearby():
    """Test Barcelona and nearby locations to see if it's area-specific"""
    
    source = CopernicusSentinel2Source()
    
    # Test locations around Barcelona area
    locations = {
        'barcelona_city': {
            'north': 41.4001,
            'south': 41.3801, 
            'east': 2.1740,
            'west': 2.1540,
            'description': 'Barcelona city center'
        },
        'barcelona_coast': {
            'north': 41.3900,
            'south': 41.3700, 
            'east': 2.2000,
            'west': 2.1800,
            'description': 'Barcelona coastal area'
        },
        'girona': {
            'north': 41.9901,
            'south': 41.9701, 
            'east': 2.8340,
            'west': 2.8140,
            'description': 'Girona (north of Barcelona)'
        },
        'tarragona': {
            'north': 41.1290,
            'south': 41.1090, 
            'east': 1.2640,
            'west': 1.2440,
            'description': 'Tarragona (south of Barcelona)'
        },
        'valencia': {
            'north': 39.4801,
            'south': 39.4601, 
            'east': -0.3540,
            'west': -0.3740,
            'description': 'Valencia (south along coast)'
        }
    }
    
    for location_name, bounds in locations.items():
        print(f"\n=== Testing {bounds['description']} ===")
        
        try:
            # Download with summer 2024 date range (known good period)
            result = source.download_data(
                bounds=bounds,
                output_dir=f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/data/acquired/{location_name}_test",
                start_date="2024-06-01",
                end_date="2024-08-31"
            )
            
            if result and 'files' in result:
                for file_info in result['files']:
                    filepath = file_info['filepath']
                    if os.path.exists(filepath):
                        # Check file size
                        file_size = os.path.getsize(filepath)
                        print(f"Downloaded: {filepath}")
                        print(f"File size: {file_size:,} bytes")
                        
                        # Run gdalinfo to check statistics
                        print(f"Running gdalinfo -stats...")
                        os.system(f'gdalinfo -stats "{filepath}" | grep -E "(Min|Max|Mean|Band)"')
                    else:
                        print(f"File not found: {filepath}")
            else:
                print(f"No files downloaded for {location_name}")
                
        except Exception as e:
            print(f"Error downloading {location_name}: {e}")

if __name__ == "__main__":
    test_barcelona_and_nearby()
