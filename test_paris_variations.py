#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_paris_coordinate_variations():
    """Test different coordinates around Paris area to find working spots"""
    
    source = CopernicusSentinel2Source()
    
    # Test multiple locations around Paris
    paris_variations = {
        'paris_center': {
            'north': 48.8666, 'south': 48.8466, 
            'east': 2.3622, 'west': 2.3422,
            'description': 'Paris Center (original problematic)'
        },
        'paris_north': {
            'north': 48.9000, 'south': 48.8800, 
            'east': 2.3622, 'west': 2.3422,
            'description': 'Paris North'
        },
        'paris_south': {
            'north': 48.8200, 'south': 48.8000, 
            'east': 2.3622, 'west': 2.3422,
            'description': 'Paris South'
        },
        'paris_east': {
            'north': 48.8666, 'south': 48.8466, 
            'east': 2.4000, 'west': 2.3800,
            'description': 'Paris East'
        },
        'paris_west': {
            'north': 48.8666, 'south': 48.8466, 
            'east': 2.3200, 'west': 2.3000,
            'description': 'Paris West'
        },
        'versailles': {
            'north': 48.8145, 'south': 48.7945, 
            'east': 2.1344, 'west': 2.1144,
            'description': 'Versailles (southwest of Paris)'
        },
        'bois_de_vincennes': {
            'north': 48.8300, 'south': 48.8100, 
            'east': 2.4500, 'west': 2.4300,
            'description': 'Bois de Vincennes (east of Paris)'
        }
    }
    
    for location_name, bounds in paris_variations.items():
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
                        print(f"📁 {os.path.basename(filepath)} - {file_size:,} bytes")
                        
                        # Quick stats check
                        stats_output = os.popen(f'gdalinfo -stats "{filepath}" | grep "Min=" | head -1').read().strip()
                        print(f"  📊 {stats_output}")
                        
                        if "Min=0.000" in stats_output and "Max=0.000" in stats_output:
                            print("  ❌ All-zero values")
                        elif "Min=1.000" in stats_output and "Max=1.000" in stats_output:
                            print("  ❌ All-one values")
                        else:
                            print("  ✅ Variable data found!")
                            # Get full stats for successful location
                            os.system(f'gdalinfo -stats "{filepath}" | grep -E "Min="')
                    else:
                        print(f"❌ File not found")
            else:
                print("❌ No files downloaded")
                
        except Exception as e:
            print(f"💥 Error: {e}")

if __name__ == "__main__":
    test_paris_coordinate_variations()
