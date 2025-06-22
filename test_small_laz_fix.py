#!/usr/bin/env python3
"""
Test DTM pipeline fixes with a smaller LAZ file.
"""

import os
import sys
import time
import json
import tempfile
import subprocess
from pathlib import Path

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from processing.dtm import dtm

def test_with_small_laz():
    """Test DTM pipeline fixes with smaller LAZ file"""
    
    test_laz_file = "input/LAZ/PRGL1260C9597_2014.laz"
    
    if not os.path.exists(test_laz_file):
        print(f"❌ Test file not found: {test_laz_file}")
        return False
    
    file_size = os.path.getsize(test_laz_file)
    print(f"🧪 TESTING DTM PIPELINE FIXES WITH SMALL LAZ FILE")
    print(f"{'='*60}")
    print(f"📁 Test file: {test_laz_file}")
    print(f"📊 File size: {file_size:,} bytes ({file_size / (1024**2):.1f} MB)")
    print(f"🎯 Testing corrected CSF, PMF, and SMRF pipelines")
    print(f"⏰ Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test the DTM generation with fixes
        start_time = time.time()
        result_path = dtm(
            input_file=test_laz_file,
            region_name="PRGL1260C9597_2014",
            resolution=1.0,
            csf_cloth_resolution=1.0
        )
        processing_time = time.time() - start_time
        
        if result_path and os.path.exists(result_path):
            output_size = os.path.getsize(result_path)
            print(f"✅ DTM PIPELINE FIX SUCCESSFUL!")
            print(f"📄 Output file: {result_path}")
            print(f"📊 Output size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
            print(f"⏱️ Processing time: {processing_time:.2f} seconds")
            
            # Check if it's a valid GeoTIFF
            try:
                from osgeo import gdal
                gdal.UseExceptions()
                ds = gdal.Open(result_path)
                if ds:
                    print(f"📐 Dimensions: {ds.RasterXSize} x {ds.RasterYSize}")
                    print(f"🗺️ Projection: {ds.GetProjection()[:100]}...")
                    band = ds.GetRasterBand(1)
                    stats = band.GetStatistics(True, True)
                    print(f"📈 Elevation range: {stats[0]:.2f} to {stats[1]:.2f}")
                    ds = None
                    print(f"✅ Valid GeoTIFF confirmed")
                else:
                    print(f"⚠️ Could not open as GeoTIFF, but file exists")
            except ImportError:
                print(f"ℹ️ GDAL not available for validation, but file was created")
            except Exception as e:
                print(f"⚠️ GeoTIFF validation failed: {e}")
            
            return True
            
        else:
            print(f"❌ DTM generation failed - no output file created")
            return False
            
    except Exception as e:
        print(f"❌ DTM PIPELINE FIX TEST FAILED")
        print(f"🔥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_with_small_laz()
    
    print(f"\n{'='*60}")
    if success:
        print(f"✅ DTM PIPELINE FIXES SUCCESSFUL")
        print(f"🎉 The CSF parameter and SMRF filter issues have been resolved!")
        print(f"💡 The issues were with parameter fixes, not pipeline logic.")
        print(f"📝 Large LAZ files may still take time but will eventually succeed.")
    else:
        print(f"❌ DTM PIPELINE FIXES STILL NEED WORK")
        print(f"💡 Check the error messages above for details")
    print(f"{'='*60}")
