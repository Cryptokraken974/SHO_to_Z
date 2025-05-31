#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_paris_different_dates():
    """Test Paris with different acquisition date ranges to identify if it's date-specific"""
    
    source = CopernicusSentinel2Source()
    
    # Paris coordinates (48.8566° N, 2.3522° E)
    paris_bounds = {
        'north': 48.8666,
        'south': 48.8466, 
        'east': 2.3622,
        'west': 2.3422
    }
    
    # Test different date ranges
    date_ranges = [
        ("2024-06-01", "2024-08-31", "summer_2024"),
        ("2024-03-01", "2024-05-31", "spring_2024"), 
        ("2023-06-01", "2023-08-31", "summer_2023"),
        ("2023-09-01", "2023-11-30", "autumn_2023"),
        ("2024-09-01", "2024-11-30", "autumn_2024"),
        ("2022-06-01", "2022-08-31", "summer_2022")
    ]
    
    for start_date, end_date, period_name in date_ranges:
        print(f"\n=== Testing Paris for {period_name} ({start_date} to {end_date}) ===")
        
        try:
            # Download with specific date range
            result = source.download_data(
                bounds=paris_bounds,
                output_dir=f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/data/acquired/paris_{period_name}",
                start_date=start_date,
                end_date=end_date
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
                        print(f"Running gdalinfo -stats on {filepath}...")
                        os.system(f'gdalinfo -stats "{filepath}" | grep -E "(Min|Max|Mean|Band)"')
                    else:
                        print(f"File not found: {filepath}")
            else:
                print(f"No files downloaded for {period_name}")
                
        except Exception as e:
            print(f"Error downloading {period_name}: {e}")

if __name__ == "__main__":
    test_paris_different_dates()
