#!/usr/bin/env python3
"""
Test script to verify DTM pipeline fixes.
Tests the corrected CSF, PMF, and SMRF pipelines with the NP_T-0069.laz file.
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

from processing.dtm import dtm, convert_las_to_dtm

def test_dtm_pipeline_fix():
    """Test the fixed DTM pipeline with NP_T-0069.laz"""
    
    # Test file that was failing
    test_laz_file = "input/LAZ/NP_T-0069.laz"
    
    if not os.path.exists(test_laz_file):
        print(f"❌ Test file not found: {test_laz_file}")
        print("Available LAZ files:")
        laz_dir = "input/LAZ"
        if os.path.exists(laz_dir):
            for file in os.listdir(laz_dir):
                if file.lower().endswith('.laz'):
                    print(f"  📄 {file}")
        return False
    
    print(f"🧪 TESTING DTM PIPELINE FIXES")
    print(f"{'='*60}")
    print(f"📁 Test file: {test_laz_file}")
    print(f"🎯 Testing corrected CSF, PMF, and SMRF pipelines")
    print(f"⏰ Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test the DTM generation with fixes
        start_time = time.time()
        result_path = dtm(
            input_file=test_laz_file,
            region_name="NP_T-0069",
            resolution=1.0,
            csf_cloth_resolution=1.0
        )
        
        processing_time = time.time() - start_time
        
        if result_path and os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"✅ DTM PIPELINE FIX SUCCESSFUL!")
            print(f"📄 Output file: {result_path}")
            print(f"📊 File size: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")
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

def test_individual_pipelines():
    """Test each pipeline individually to see which ones work"""
    
    test_laz_file = "input/LAZ/NP_T-0069.laz"
    if not os.path.exists(test_laz_file):
        print(f"❌ Test file not found: {test_laz_file}")
        return
    
    print(f"\n🔬 TESTING INDIVIDUAL PIPELINES")
    print(f"{'='*60}")
    
    # Test output directory
    test_output_dir = "Tests/dtm_pipeline_test"
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Import pipeline creation functions
    from processing.dtm import (
        create_dtm_fallback_pipeline, 
        create_dtm_adaptive_pipeline,
        create_dtm_simple_pipeline
    )
    
    pipelines_to_test = [
        ("Simple Ground-Only", create_dtm_simple_pipeline),
        ("PMF Fallback", create_dtm_fallback_pipeline),
        ("SMRF Adaptive", create_dtm_adaptive_pipeline),
    ]
    
    for pipeline_name, pipeline_func in pipelines_to_test:
        print(f"\n🧪 Testing {pipeline_name} Pipeline...")
        
        output_file = os.path.join(test_output_dir, f"test_dtm_{pipeline_name.lower().replace(' ', '_').replace('-', '_')}.tif")
        
        try:
            # Create pipeline
            pipeline_config = pipeline_func(test_laz_file, output_file, 1.0)
            
            # Write pipeline to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(pipeline_config, temp_file, indent=2)
                temp_pipeline_path = temp_file.name
            
            print(f"📋 Pipeline config: {json.dumps(pipeline_config, indent=2)}")
            
            try:
                # Execute pipeline with shorter timeout
                start_time = time.time()
                result = subprocess.run(
                    ['pdal', 'pipeline', temp_pipeline_path], 
                    capture_output=True, 
                    text=True, 
                    timeout=60  # 1 minute timeout for testing
                )
                exec_time = time.time() - start_time
                
                if result.returncode == 0 and os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    print(f"✅ {pipeline_name} pipeline SUCCEEDED")
                    print(f"   ⏱️ Time: {exec_time:.2f}s")
                    print(f"   📊 Size: {file_size:,} bytes")
                elif result.returncode != 0:
                    print(f"❌ {pipeline_name} pipeline FAILED")
                    print(f"   🔥 Return code: {result.returncode}")
                    print(f"   📝 Stderr: {result.stderr}")
                else:
                    print(f"⚠️ {pipeline_name} pipeline completed but no output file")
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ {pipeline_name} pipeline TIMED OUT (>60s)")
            except Exception as e:
                print(f"❌ {pipeline_name} pipeline ERROR: {e}")
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_pipeline_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Failed to create {pipeline_name} pipeline: {e}")

if __name__ == "__main__":
    print(f"🧪 DTM PIPELINE FIX VALIDATION")
    print(f"{'='*60}")
    
    # Test the full DTM function
    success = test_dtm_pipeline_fix()
    
    # Test individual pipelines for debugging
    test_individual_pipelines()
    
    print(f"\n{'='*60}")
    if success:
        print(f"✅ DTM PIPELINE FIXES SUCCESSFUL")
        print(f"🎉 The CSF parameter and SMRF filter issues have been resolved!")
    else:
        print(f"❌ DTM PIPELINE FIXES STILL NEED WORK")
        print(f"💡 Check the individual pipeline test results above for details")
    print(f"{'='*60}")
