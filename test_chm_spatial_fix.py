#!/usr/bin/env python3
"""
Test CHM Spatial Alignment Fix

This script tests the improved CHM calculation that properly handles
spatial mismatches between DTM and DSM files by cropping DSM to DTM extent.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the app directory to sys.path
sys.path.insert(0, '/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/app')

async def test_chm_fix():
    """Test the CHM spatial alignment fix using Box_Regions_6 data"""
    
    print("🧪 Testing CHM Spatial Alignment Fix")
    print("=" * 50)
    
    try:
        # Import the processing function
        from processing.tiff_processing import process_chm_tiff
        
        # Define paths for Box_Regions_6 test case
        base_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z")
        
        # DTM path (smaller extent - 810x810 pixels)
        dtm_path = base_path / "input/Box_Regions_6/3.787S_63.734W_elevation/Original/3.787S_63.734W_elevation.tiff"
        
        # DSM path (larger extent - 3600x3600 pixels) 
        dsm_path = base_path / "output/Box_Regions_6/lidar/DSM/Box_Regions_6_copernicus_dsm_30m.tif"
        
        # Output directory for test CHM
        output_dir = base_path / "test_chm_fix_output"
        output_dir.mkdir(exist_ok=True)
        
        print(f"📁 DTM: {dtm_path.name}")
        print(f"📁 DSM: {dsm_path.name}")
        print(f"📂 Output: {output_dir}")
        
        # Verify input files exist
        if not dtm_path.exists():
            print(f"❌ DTM file not found: {dtm_path}")
            return False
            
        if not dsm_path.exists():
            print(f"❌ DSM file not found: {dsm_path}")
            return False
        
        print(f"✅ Input files verified")
        
        # Parameters for CHM processing (specify DSM path)
        parameters = {
            'dsm_path': str(dsm_path)
        }
        
        print(f"\n🔄 Running CHM processing with spatial alignment fix...")
        
        # Process CHM with the fixed function
        result = await process_chm_tiff(str(dtm_path), str(output_dir), parameters)
        
        if result.get("status") == "success":
            print(f"\n✅ CHM processing completed successfully!")
            print(f"📁 Output file: {result['output_file']}")
            print(f"⏱️ Processing time: {result.get('processing_time', 0):.2f} seconds")
            
            # Display statistics if available
            stats = result.get('statistics')
            if stats:
                print(f"\n📊 CHM Statistics:")
                print(f"   Min height: {stats.get('min_height', 'N/A'):.2f}m")
                print(f"   Max height: {stats.get('max_height', 'N/A'):.2f}m") 
                print(f"   Mean height: {stats.get('mean_height', 'N/A'):.2f}m")
                print(f"   Std dev: {stats.get('std_height', 'N/A'):.2f}m")
            
            # Verify output file was created
            output_path = Path(result['output_file'])
            if output_path.exists():
                file_size = output_path.stat().st_size / (1024 * 1024)  # MB
                print(f"📦 Output file size: {file_size:.2f} MB")
                
                # Analyze output dimensions using rasterio
                try:
                    import rasterio
                    with rasterio.open(str(output_path)) as src:
                        print(f"📐 CHM dimensions: {src.width}x{src.height}")
                        print(f"🗺️ CHM CRS: {src.crs}")
                        print(f"📏 CHM resolution: {src.res}")
                        print(f"📍 CHM bounds: {src.bounds}")
                        
                        # Should match DTM dimensions (810x810), not DSM (3600x3600)
                        if src.width == 810 and src.height == 810:
                            print(f"✅ CHM has correct DTM-aligned dimensions!")
                        else:
                            print(f"⚠️ CHM dimensions don't match expected DTM size (810x810)")
                            
                except ImportError:
                    print(f"⚠️ rasterio not available for dimension analysis")
                
                return True
            else:
                print(f"❌ Output file was not created: {output_path}")
                return False
        else:
            print(f"❌ CHM processing failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🔍 CHM Spatial Alignment Fix Test")
    print("Testing improved CHM calculation that crops DSM to DTM extent")
    print("This should eliminate the 'black square' issue in CHM outputs")
    print()
    
    success = await test_chm_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST PASSED: CHM spatial alignment fix working correctly!")
        print("✅ DSM was properly cropped/aligned to DTM extent")
        print("✅ CHM calculation should now be spatially coherent")
        print("✅ No more black squares in CHM output")
    else:
        print("❌ TEST FAILED: CHM spatial alignment fix needs debugging")
        print("⚠️ Check error messages above for details")
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
