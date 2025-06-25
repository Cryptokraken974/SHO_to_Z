#!/usr/bin/env python3
"""
Test the fixed CHM processing on Box_Regions_7

This script will test the corrected CHM spatial alignment and data quality detection.
"""

import sys
import os
import asyncio

# Add the app directory to Python path
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/app')

from processing.tiff_processing import process_chm_tiff

async def test_chm_fix():
    """Test the CHM fix"""
    
    print("🧪 TESTING CHM FIX - Box_Regions_7")
    print("=" * 60)
    
    # File paths
    dtm_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/Box_Regions_7/3.787S_63.673W_elevation/Original/3.787S_63.673W_elevation.tiff"
    dsm_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/Box_Regions_7/lidar/DSM/Box_Regions_7_copernicus_dsm_30m.tif"
    output_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/test_chm_output"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 DTM: {os.path.basename(dtm_path)}")
    print(f"📁 DSM: {os.path.basename(dsm_path)}")
    print(f"📂 Output: {output_dir}")
    
    # Set up parameters
    parameters = {
        "dsm_path": dsm_path
    }
    
    try:
        print(f"\n🚀 Starting CHM processing with fixed algorithm...")
        
        result = await process_chm_tiff(
            tiff_path=dtm_path,
            output_dir=output_dir,
            parameters=parameters
        )
        
        print(f"\n📊 RESULTS:")
        print(f"Status: {result.get('status')}")
        print(f"Output file: {result.get('output_file')}")
        print(f"Processing time: {result.get('processing_time', 0):.2f}s")
        
        statistics = result.get('statistics')
        if statistics:
            print(f"Statistics:")
            print(f"  Min height: {statistics.get('min_height', 'N/A')}")
            print(f"  Max height: {statistics.get('max_height', 'N/A')}")
            print(f"  Mean height: {statistics.get('mean_height', 'N/A')}")
            print(f"  Std deviation: {statistics.get('std_height', 'N/A')}")
        
        data_quality_warning = result.get('data_quality_warning')
        if data_quality_warning:
            print(f"\n⚠️ Data Quality Warning:")
            print(f"  {data_quality_warning}")
        
        output_file = result.get('output_file')
        if output_file and os.path.exists(output_file):
            print(f"\n✅ CHM file created successfully: {output_file}")
            
            # Quick verification with rasterio
            import rasterio
            import numpy as np
            
            with rasterio.open(output_file) as src:
                chm_data = src.read(1)
                chm_valid = chm_data[~np.isnan(chm_data)]
                
                print(f"📊 File verification:")
                print(f"  Shape: {chm_data.shape}")
                print(f"  Valid pixels: {len(chm_valid):,}")
                print(f"  CRS: {src.crs}")
                print(f"  Bounds: {src.bounds}")
                
                if len(chm_valid) > 0:
                    print(f"  Data range: {np.min(chm_valid):.2f} to {np.max(chm_valid):.2f}")
                    print(f"  Data mean: {np.mean(chm_valid):.2f}")
        else:
            print(f"❌ CHM file not created or not found")
        
    except Exception as e:
        print(f"❌ CHM processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chm_fix())
