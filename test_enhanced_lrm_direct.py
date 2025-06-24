#!/usr/bin/env python3
"""
Direct test of enhanced LRM processing to verify enhanced logging works
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# Add app directory to Python path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
APP_DIR = os.path.join(BASE_DIR, "app")
sys.path.insert(0, APP_DIR)

# Import the enhanced LRM function directly
from processing.tiff_processing import process_enhanced_lrm_tiff

# Test with a real elevation TIFF file
TEST_TIFF = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/TEST_ELEVATION_DEBUG/lidar/2.313S_56.622W_elevation.tiff"
OUTPUT_DIR = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/test_enhanced_lrm_output"

async def test_enhanced_lrm():
    """Test the enhanced LRM function directly"""
    print("🧪 DIRECT ENHANCED LRM TEST")
    print("=" * 60)
    
    if not os.path.exists(TEST_TIFF):
        print(f"❌ Test TIFF not found: {TEST_TIFF}")
        return False
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Test parameters with enhanced features enabled
    test_parameters = {
        "window_size": None,  # Force auto-sizing
        "filter_type": "gaussian",  # Use Gaussian filter
        "auto_sizing": True,  # Enable adaptive sizing
        "enhanced_normalization": True  # Enable enhanced normalization
    }
    
    print(f"📄 Input TIFF: {os.path.basename(TEST_TIFF)}")
    print(f"📂 Output directory: {OUTPUT_DIR}")
    print(f"⚙️ Test parameters:")
    for key, value in test_parameters.items():
        print(f"   {key}: {value}")
    print()
    
    start_time = time.time()
    
    try:
        # Call the enhanced LRM function directly
        result = await process_enhanced_lrm_tiff(TEST_TIFF, OUTPUT_DIR, test_parameters)
        
        processing_time = time.time() - start_time
        
        if result.get("status") == "success":
            print(f"\n✅ ENHANCED LRM TEST SUCCESSFUL!")
            print(f"⏱️ Processing time: {processing_time:.2f} seconds")
            print(f"📄 Output file: {result.get('output_file')}")
            
            # Check if output file exists
            output_file = result.get('output_file')
            if output_file and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"📊 Output size: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")
                return True
            else:
                print(f"❌ Output file not created: {output_file}")
                return False
                
        else:
            print(f"❌ Enhanced LRM failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_lrm())
    if success:
        print("\n🎉 Enhanced LRM logging is working correctly!")
    else:
        print("\n💥 Enhanced LRM test failed!")
    sys.exit(0 if success else 1)
