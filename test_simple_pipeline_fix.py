#!/usr/bin/env python3
"""
Quick test of the Simple Ground-Only pipeline to verify fixes work.
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

from processing.dtm import create_dtm_simple_pipeline

def test_simple_pipeline_fix():
    """Test the Simple Ground-Only pipeline quickly"""
    
    test_laz_file = "input/LAZ/NP_T-0069.laz"
    
    if not os.path.exists(test_laz_file):
        print(f"❌ Test file not found: {test_laz_file}")
        return False
    
    print(f"🧪 TESTING SIMPLE GROUND-ONLY PIPELINE FIX")
    print(f"{'='*60}")
    print(f"📁 Test file: {test_laz_file}")
    print(f"⏰ Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    output_file = "test_simple_pipeline_output.tif"
    
    try:
        # Create simple pipeline 
        pipeline_config = create_dtm_simple_pipeline(test_laz_file, output_file, 1.0)
        
        print(f"📋 Pipeline config:")
        print(json.dumps(pipeline_config, indent=2))
        print()
        
        # Write pipeline to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(pipeline_config, temp_file, indent=2)
            temp_pipeline_path = temp_file.name
        
        try:
            print(f"🚀 Executing Simple Ground-Only pipeline...")
            start_time = time.time()
            result = subprocess.run(
                ['pdal', 'pipeline', temp_pipeline_path], 
                capture_output=True, 
                text=True, 
                timeout=120  # 2 minute timeout
            )
            exec_time = time.time() - start_time
            
            if result.returncode == 0 and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ SIMPLE PIPELINE FIX SUCCESSFUL!")
                print(f"📄 Output file: {output_file}")
                print(f"📊 File size: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")
                print(f"⏱️ Processing time: {exec_time:.2f} seconds")
                
                # Clean up
                os.unlink(output_file)
                return True
                
            elif result.returncode != 0:
                print(f"❌ Simple pipeline FAILED")
                print(f"🔥 Return code: {result.returncode}")
                print(f"📝 Stderr: {result.stderr}")
                print(f"📝 Stdout: {result.stdout}")
                return False
            else:
                print(f"⚠️ Pipeline completed but no output file created")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Simple pipeline TIMED OUT (>120s)")
            return False
        except Exception as e:
            print(f"❌ Simple pipeline ERROR: {e}")
            return False
        finally:
            try:
                os.unlink(temp_pipeline_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ SIMPLE PIPELINE TEST FAILED")
        print(f"🔥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_pipeline_fix()
    
    print(f"\n{'='*60}")
    if success:
        print(f"✅ SIMPLE PIPELINE FIX SUCCESSFUL")
        print(f"🎉 The simple ground-only pipeline works correctly!")
    else:
        print(f"❌ SIMPLE PIPELINE FIX FAILED")
        print(f"💡 Check the error messages above for details")
    print(f"{'='*60}")
