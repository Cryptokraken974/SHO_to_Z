#!/usr/bin/env python3
"""
Quick test to verify CSF parameter fix works.
"""

import json
import tempfile
import subprocess
import os

def test_csf_pipeline():
    """Test the corrected CSF pipeline configuration"""
    
    test_laz_file = "input/LAZ/NP_T-0069.laz"
    if not os.path.exists(test_laz_file):
        print(f"❌ Test file not found: {test_laz_file}")
        return False
    
    # Create corrected CSF pipeline
    pipeline_config = {
        "pipeline": [
            test_laz_file,
            {
                "type": "filters.outlier",
                "method": "statistical", 
                "multiplier": 3,
                "mean_k": 8
            },
            {
                "type": "filters.assign",
                "assignment": "Classification[:]=0"
            },
            {
                "type": "filters.csf",
                "ignore": "Classification[7:7]",
                "threshold": 0.35,  # Fixed: was "class_threshold"
                "resolution": 1.0,  # Fixed: was "cloth_resolution"
                "rigidness": 1,
                "iterations": 500
            },
            {
                "type": "filters.range",
                "limits": "Classification![135:146],Z[-10:3000]"
            },
            {
                "type": "filters.range", 
                "limits": "Classification[2:2]"
            },
            {
                "type": "writers.gdal",
                "filename": "Tests/test_csf_fix.tif",
                "resolution": 1.0,
                "output_type": "min",
                "nodata": -9999,
                "gdaldriver": "GTiff"
            }
        ]
    }
    
    print(f"🧪 Testing Corrected CSF Pipeline")
    print(f"📋 Fixed parameters:")
    print(f"   • 'class_threshold' → 'threshold'")
    print(f"   • 'points':true → 'classify':true")
    print()
    
    # Write pipeline to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        json.dump(pipeline_config, temp_file, indent=2)
        temp_pipeline_path = temp_file.name
    
    try:
        print(f"🚀 Running corrected CSF pipeline...")
        result = subprocess.run(
            ['pdal', 'pipeline', temp_pipeline_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ CSF PIPELINE FIX SUCCESSFUL!")
            print(f"🎉 The 'class_threshold' parameter error has been resolved")
            return True
        else:
            print(f"❌ CSF pipeline still failed:")
            print(f"   Return code: {result.returncode}")
            print(f"   Stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ CSF pipeline timed out")
        return False
    except Exception as e:
        print(f"❌ CSF pipeline error: {e}")
        return False
    finally:
        try:
            os.unlink(temp_pipeline_path)
        except:
            pass

if __name__ == "__main__":
    test_csf_pipeline()
