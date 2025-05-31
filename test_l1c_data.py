#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_l1c_vs_l2a():
    """Test Paris and Barcelona with L1C data instead of L2A"""
    
    source = CopernicusSentinel2Source()
    
    # Test problematic locations with L1C
    locations = {
        'paris_l1c': {
            'north': 48.8666,
            'south': 48.8466, 
            'east': 2.3622,
            'west': 2.3422,
            'description': 'Paris with L1C data'
        },
        'barcelona_l1c': {
            'north': 41.4001,
            'south': 41.3801, 
            'east': 2.1740,
            'west': 2.1540,
            'description': 'Barcelona with L1C data'
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
                print(f"✅ Downloaded {len(result['files'])} files")
                
                for file_info in result['files']:
                    filepath = file_info['filepath']
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                        print(f"📁 {os.path.basename(filepath)} - {file_size:,} bytes")
                        
                        # Check metadata
                        if 'metadata' in file_info:
                            metadata = file_info['metadata']
                            print(f"  ☁️ Cloud: {metadata.get('cloud_coverage', 'Unknown')}%")
                            print(f"  📅 Date: {metadata.get('acquisition_date', 'Unknown')}")
                            print(f"  🛰️ Level: {metadata.get('processing_level', 'Unknown')}")
                        
                        # Quick statistics check
                        print("  📊 Statistics:")
                        os.system(f'gdalinfo -stats "{filepath}" | grep -E "Min=" | head -4')
                        
                        # Check if we have real data
                        stats_check = os.popen(f'gdalinfo -stats "{filepath}" | grep "Min=" | head -1').read().strip()
                        if "Min=0.000" in stats_check and "Max=0.000" in stats_check:
                            print("  ❌ Still getting all-zero values")
                        elif "Min=1.000" in stats_check and "Max=1.000" in stats_check:
                            print("  ❌ Still getting all-one values")
                        else:
                            print("  ✅ Getting variable data!")
                            
                    else:
                        print(f"❌ File not found: {filepath}")
            else:
                print("❌ No files downloaded")
                
        except Exception as e:
            print(f"💥 Error: {e}")

if __name__ == "__main__":
    test_l1c_vs_l2a()
