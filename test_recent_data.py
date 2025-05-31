#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_recent_data():
    """Test Paris and Barcelona with very recent data"""
    
    source = CopernicusSentinel2Source()
    
    # Get dates for the last 3 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    print(f"Testing with date range: {start_str} to {end_str}")
    
    locations = {
        'paris_recent': {
            'north': 48.8666,
            'south': 48.8466, 
            'east': 2.3622,
            'west': 2.3422,
            'description': 'Paris - recent 3 months'
        },
        'barcelona_recent': {
            'north': 41.4001,
            'south': 41.3801, 
            'east': 2.1740,
            'west': 2.1540,
            'description': 'Barcelona - recent 3 months'
        },
        'london_recent': {
            'north': 51.5151,
            'south': 51.4951, 
            'east': -0.1040,
            'west': -0.1240,
            'description': 'London - recent 3 months (control)'
        }
    }
    
    for location_name, bounds in locations.items():
        print(f"\n=== Testing {bounds['description']} ===")
        
        try:
            result = source.download_data(
                bounds=bounds,
                output_dir=f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/data/acquired/{location_name}",
                start_date=start_str,
                end_date=end_str
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
                        
                        # Quick statistics check
                        print("  📊 Statistics:")
                        os.system(f'gdalinfo -stats "{filepath}" | grep -E "Min=" | head -4')
                    else:
                        print(f"❌ File not found: {filepath}")
            else:
                print(f"❌ No files downloaded for {location_name}")
                
        except Exception as e:
            print(f"💥 Error downloading {location_name}: {e}")

if __name__ == "__main__":
    test_recent_data()
