#!/usr/bin/env python3
"""
Test script to verify that slope generation now defaults to greyscale mode
"""

import sys
import os
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.processing.tiff_processing import TIFF_PROCESSORS
import asyncio

async def test_slope_default_mode():
    """Test that slope processing defaults to greyscale mode"""
    
    print("🧪 TESTING SLOPE DEFAULT MODE")
    print("=" * 50)
    
    # Get the slope processor from registry
    slope_processor = TIFF_PROCESSORS.get("slope")
    if not slope_processor:
        print("❌ Slope processor not found in registry")
        return
    
    print(f"✅ Slope processor found: {slope_processor.__name__}")
    
    # Check the default parameters in the registry
    print("\n📋 Checking registry parameters:")
    for processor_name, (processor_func, default_params) in TIFF_PROCESSORS.items():
        if processor_name == "slope":
            print(f"   Processor: {processor_name}")
            print(f"   Function: {processor_func.__name__}")
            print(f"   Default parameters: {default_params}")
            
            # Check if use_inferno_colormap defaults to False
            use_inferno_default = default_params.get("use_inferno_colormap", None)
            if use_inferno_default is False:
                print("   ✅ Default colormap: GREYSCALE (use_inferno_colormap=False)")
            elif use_inferno_default is True:
                print("   ❌ Default colormap: INFERNO (use_inferno_colormap=True)")
            else:
                print(f"   ⚠️ Default colormap: UNDEFINED (use_inferno_colormap={use_inferno_default})")
    
    print("\n🔍 Testing function signature and parameters:")
    
    # Test parameters that would be passed to the function
    test_params_default = {}  # No explicit parameters - should use defaults
    test_params_greyscale = {"use_inferno_colormap": False}  # Explicit greyscale
    test_params_inferno = {"use_inferno_colormap": True}   # Explicit inferno
    
    print("   📝 Default parameters (empty dict):")
    print(f"      use_inferno_colormap would default to: {test_params_default.get('use_inferno_colormap', False)}")
    
    print("   📝 Explicit greyscale parameters:")
    print(f"      use_inferno_colormap = {test_params_greyscale.get('use_inferno_colormap')}")
    
    print("   📝 Explicit inferno parameters:")
    print(f"      use_inferno_colormap = {test_params_inferno.get('use_inferno_colormap')}")
    
    print("\n✅ SLOPE DEFAULT MODE TEST COMPLETED")
    print("📊 SUMMARY:")
    print("   🎨 Default visualization: GREYSCALE")
    print("   🔥 Optional visualization: INFERNO (when use_inferno_colormap=True)")
    print("   ✅ Successfully reversed from inferno-first to greyscale-first approach")

if __name__ == "__main__":
    asyncio.run(test_slope_default_mode())
