#!/usr/bin/env python3
"""
Minimal CSF test to identify correct parameters.
"""

import json
import tempfile
import subprocess
import os

def test_minimal_csf():
    """Test CSF with minimal parameters"""
    
    test_laz_file = "input/LAZ/NP_T-0069.laz"
    if not os.path.exists(test_laz_file):
        print(f"❌ Test file not found: {test_laz_file}")
        return False
    
    # Start with absolute minimal CSF configuration
    pipeline_config = {
        "pipeline": [
            test_laz_file,
            {
                "type": "filters.csf"
            },
            {
                "type": "writers.las",
                "filename": "test_csf_minimal.las"
            }
        ]
    }
    
    # Write pipeline to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        json.dump(pipeline_config, temp_file, indent=2)
        temp_pipeline_path = temp_file.name
    
    print(f"🧪 Testing minimal CSF configuration...")
    print(f"📋 Pipeline: {json.dumps(pipeline_config, indent=2)}")
    
    try:
        result = subprocess.run(
            ['pdal', 'pipeline', temp_pipeline_path], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ Minimal CSF pipeline SUCCEEDED")
            print(f"📝 Stdout: {result.stdout}")
        else:
            print(f"❌ Minimal CSF pipeline FAILED")
            print(f"🔥 Return code: {result.returncode}")
            print(f"📝 Stderr: {result.stderr}")
            print(f"📝 Stdout: {result.stdout}")
            
    except subprocess.TimeoutExpired:
        print(f"⏰ CSF pipeline TIMED OUT")
    except Exception as e:
        print(f"❌ CSF pipeline ERROR: {e}")
    finally:
        try:
            os.unlink(temp_pipeline_path)
            if os.path.exists("test_csf_minimal.las"):
                os.unlink("test_csf_minimal.las")
        except:
            pass

if __name__ == "__main__":
    test_minimal_csf()
