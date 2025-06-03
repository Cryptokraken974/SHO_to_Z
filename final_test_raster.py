
import asyncio
import sys
import os
sys.path.insert(0, 'app')

from processing.tiff_processing import process_all_raster_products

async def simple_test():
    tiff_path = 'input/3.93S_38.65W/lidar/3.926S_38.653W_elevation.tiff'
    print(f'📁 Processing: {tiff_path}')
    print(f'📋 File exists: {os.path.exists(tiff_path)}')
    
    # Call without request object first
    result = await process_all_raster_products(tiff_path, None, None)
    print('📊 Result:', result)
    
asyncio.run(simple_test())
