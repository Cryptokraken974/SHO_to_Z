#!/usr/bin/env python3

import os
import sys
import json
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_problematic_locations_debug():
    """Test Paris and Barcelona with detailed debugging"""
    
    source = CopernicusSentinel2Source()
    
    # Test locations that have shown issues
    locations = {
        'paris_debug': {
            'north': 48.8666,
            'south': 48.8466, 
            'east': 2.3622,
            'west': 2.3422,
            'description': 'Paris (problematic - all zeros)'
        },
        'barcelona_debug': {
            'north': 41.4001,
            'south': 41.3801, 
            'east': 2.1740,
            'west': 2.1540,
            'description': 'Barcelona (problematic - all ones)'
        },
        'munich_debug': {
            'north': 48.1501,
            'south': 48.1301, 
            'east': 11.5920,
            'west': 11.5720,
            'description': 'Munich (working control)'
        }
    }
    
    for location_name, bounds in locations.items():
        print(f"\n{'='*60}")
        print(f"TESTING: {bounds['description']}")
        print(f"Bounds: {json.dumps(bounds, indent=2)}")
        print(f"{'='*60}")
        
        try:
            # Download with debugging
            result = source.download_data(
                bounds=bounds,
                output_dir=f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/data/acquired/{location_name}",
                start_date="2024-06-01",
                end_date="2024-08-31"
            )
            
            if result and 'files' in result:
                print(f"✅ Download result: {len(result['files'])} files")
                
                for i, file_info in enumerate(result['files']):
                    filepath = file_info['filepath']
                    print(f"\n--- File {i+1}: {os.path.basename(filepath)} ---")
                    
                    if os.path.exists(filepath):
                        # Check file size
                        file_size = os.path.getsize(filepath)
                        print(f"📁 File size: {file_size:,} bytes")
                        
                        # Show metadata if available
                        if 'metadata' in file_info:
                            metadata = file_info['metadata']
                            print(f"📅 Acquisition date: {metadata.get('acquisition_date', 'Unknown')}")
                            print(f"☁️ Cloud coverage: {metadata.get('cloud_coverage', 'Unknown')}%")
                            print(f"🛰️ Processing level: {metadata.get('processing_level', 'Unknown')}")
                        
                        # Detailed GDAL analysis
                        print(f"\n🔍 GDAL Analysis:")
                        os.system(f'gdalinfo -stats "{filepath}"')
                        
                        # Also try a pixel sample
                        print(f"\n🎯 Pixel sampling (top-left 5x5):")
                        os.system(f'gdal_translate -of XYZ -srcwin 0 0 5 5 "{filepath}" /dev/stdout | head -25')
                        
                    else:
                        print(f"❌ File not found: {filepath}")
            else:
                print(f"❌ No files downloaded for {location_name}")
                print(f"Result: {result}")
                
        except Exception as e:
            print(f"💥 Error downloading {location_name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_problematic_locations_debug()
