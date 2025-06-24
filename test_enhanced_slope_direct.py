#!/usr/bin/env python3
"""
Direct test of enhanced slope processing to verify enhanced logging works
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

# Import the enhanced slope function directly
from processing.tiff_processing import process_enhanced_slope_tiff

# Test with the same elevation TIFF file used for LRM
TEST_TIFF = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/TEST_ELEVATION_DEBUG/lidar/2.313S_56.622W_elevation.tiff"
OUTPUT_DIR = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/test_enhanced_slope_output"

async def test_enhanced_slope():
    """Test the enhanced slope function directly"""
    print("🧪 DIRECT ENHANCED SLOPE TEST")
    print("=" * 60)
    
    if not os.path.exists(TEST_TIFF):
        print(f"❌ Test TIFF not found: {TEST_TIFF}")
        return False
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Test parameters with enhanced features enabled
    test_parameters = {
        "use_inferno_colormap": True,  # Use inferno colormap
        "max_slope_degrees": 60.0,    # Archaeological analysis range
        "enhanced_contrast": True     # Enable enhanced contrast
    }
    
    print(f"📄 Input TIFF: {os.path.basename(TEST_TIFF)}")
    print(f"📂 Output directory: {OUTPUT_DIR}")
    print(f"⚙️ Test parameters:")
    for key, value in test_parameters.items():
        print(f"   {key}: {value}")
    print()
    
    start_time = time.time()
    
    try:
        # Call the enhanced slope function directly
        result = await process_enhanced_slope_tiff(TEST_TIFF, OUTPUT_DIR, test_parameters)
        
        processing_time = time.time() - start_time
        
        if result.get("status") == "success":
            print(f"\n✅ ENHANCED SLOPE TEST SUCCESSFUL!")
            print(f"⏱️ Processing time: {processing_time:.2f} seconds")
            print(f"📄 Output file: {result.get('output_file')}")
            
            # Check if output file exists
            output_file = result.get('output_file')
            if output_file and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"📊 Output size: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")
                
                # Display enhanced features used
                enhanced_features = result.get('enhanced_features', {})
                print(f"\n🎯 Enhanced features used:")
                print(f"   🔥 Inferno colormap: {enhanced_features.get('inferno_colormap')}")
                print(f"   📐 Max slope range: {enhanced_features.get('max_slope_degrees')}°")
                print(f"   🎨 Enhanced contrast: {enhanced_features.get('enhanced_contrast')}")
                
                # Display slope distribution
                slope_dist = enhanced_features.get('slope_distribution', {})
                if slope_dist:
                    print(f"\n📊 Slope distribution analysis:")
                    print(f"   🟫 Flat areas (0°-5°): {slope_dist.get('flat_areas_percent', 0):.1f}%")
                    print(f"   🟡 Moderate slopes (5°-20°): {slope_dist.get('moderate_slopes_percent', 0):.1f}%")
                    print(f"   🔴 Steep terrain (20°+): {slope_dist.get('steep_terrain_percent', 0):.1f}%")
                
                return True
            else:
                print(f"❌ Output file not created: {output_file}")
                return False
                
        else:
            print(f"❌ Enhanced Slope failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_slope())
    if success:
        print("\n🎉 Enhanced Slope logging is working correctly!")
    else:
        print("\n💥 Enhanced Slope test failed!")
    sys.exit(0 if success else 1)
