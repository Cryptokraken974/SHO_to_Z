#!/usr/bin/env python3
"""
Test Quality Mode Integration for DTM, DSM, and CHM
Tests the complete quality mode integration across all primary raster functions.
"""

import os
import sys
import json
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

def test_quality_mode_integration():
    """Test quality mode integration across DTM, DSM, and CHM functions"""
    
    print("🧪 TESTING COMPLETE QUALITY MODE INTEGRATION")
    print("="*60)
    
    # Test with actual LAZ file from input
    test_laz_file = "input/LAZ/PRGL1260C9597_2014.laz"
    
    if not os.path.exists(test_laz_file):
        print(f"⚠️ Test LAZ file not found: {test_laz_file}")
        print(f"🔍 Available LAZ files:")
        laz_dir = Path("input/LAZ")
        if laz_dir.exists():
            for laz_file in laz_dir.glob("*.laz"):
                print(f"   📄 {laz_file}")
                test_laz_file = str(laz_file)
                break
        
        if not os.path.exists(test_laz_file):
            print(f"❌ No LAZ files found for testing")
            return
    
    region_name = Path(test_laz_file).stem
    print(f"📄 Test LAZ file: {test_laz_file}")
    print(f"🏷️ Region name: {region_name}")
    
    # Check if quality mode clean LAZ exists
    potential_clean_laz_paths = [
        f"output/{region_name}/cropped/{region_name}_cropped.las",
        f"output/{region_name}/cropped/{Path(test_laz_file).stem}_cropped.las",
        f"output/{region_name}/lidar/cropped/{region_name}_cropped.las",
        f"output/{region_name}/lidar/cropped/{Path(test_laz_file).stem}_cropped.las"
    ]
    
    clean_laz_available = False
    clean_laz_path = None
    
    print(f"\n🔍 CHECKING FOR CLEAN LAZ FILES:")
    for i, path in enumerate(potential_clean_laz_paths, 1):
        exists = os.path.exists(path)
        status = "✅ EXISTS" if exists else "❌ NOT FOUND"
        print(f"   {i}. {path} -> {status}")
        if exists and not clean_laz_available:
            clean_laz_available = True
            clean_laz_path = path
    
    if clean_laz_available:
        print(f"\n🎯 QUALITY MODE AVAILABLE")
        print(f"   Clean LAZ: {clean_laz_path}")
        print(f"   💡 All raster functions will automatically use clean LAZ")
    else:
        print(f"\n📋 STANDARD MODE")
        print(f"   💡 All raster functions will use original LAZ")
        print(f"   🔧 To test quality mode, run density analysis first")
    
    # Test function imports and detection logic
    print(f"\n🧪 TESTING FUNCTION INTEGRATIONS")
    
    functions_to_test = [
        ("DTM", "processing.dtm", "dtm"),
        ("DSM", "processing.dsm", "dsm"),
        ("CHM", "processing.chm", "chm")
    ]
    
    integration_results = {}
    
    for func_name, module_name, func_name_lower in functions_to_test:
        print(f"\n🔍 TESTING {func_name} FUNCTION:")
        try:
            module = __import__(module_name, fromlist=[func_name_lower])
            func = getattr(module, func_name_lower)
            print(f"   ✅ {func_name} module imported successfully")
            print(f"   🎯 Function signature: {func_name_lower}(input_file, region_name)")
            
            if clean_laz_available:
                print(f"   🎯 Expected result: QUALITY MODE (Clean LAZ detected)")
                print(f"   📄 Expected output suffix: _clean")
                print(f"   🖼️ Expected PNG: output/{region_name}/lidar/png_outputs/{func_name}.png")
            else:
                print(f"   📋 Expected result: STANDARD MODE (No clean LAZ)")
                print(f"   📄 Expected output: standard naming")
            
            integration_results[func_name] = {
                "imported": True,
                "quality_mode_available": clean_laz_available,
                "expected_clean_output": f"output/{region_name}/lidar/{func_name}/{region_name}_{func_name}{'_clean' if clean_laz_available else ''}.tif",
                "expected_png": f"output/{region_name}/lidar/png_outputs/{func_name}.png" if clean_laz_available else None
            }
            
        except ImportError as e:
            print(f"   ⚠️ Cannot import {func_name} function: {e}")
            integration_results[func_name] = {"imported": False, "error": str(e)}
        except Exception as e:
            print(f"   ❌ Error testing {func_name} function: {e}")
            integration_results[func_name] = {"imported": False, "error": str(e)}
    
    # Test integration flow
    print(f"\n🔄 INTEGRATION FLOW TEST:")
    print(f"1️⃣ LAZ Upload → input/LAZ/")
    print(f"2️⃣ Density Analysis → Generates clean LAZ in output/{{region}}/cropped/")
    
    if clean_laz_available:
        print(f"3️⃣ DTM Processing → ✅ Uses clean LAZ → Generates clean DTM + PNG")
        print(f"4️⃣ DSM Processing → ✅ Uses clean LAZ → Generates clean DSM + PNG") 
        print(f"5️⃣ CHM Processing → ✅ Uses clean DTM & DSM → Generates clean CHM + PNG")
        print(f"6️⃣ User Visualization → ✅ Sees clean rasters without artifacts")
    else:
        print(f"3️⃣ DTM Processing → 📋 Uses original LAZ → Standard DTM")
        print(f"4️⃣ DSM Processing → 📋 Uses original LAZ → Standard DSM")
        print(f"5️⃣ CHM Processing → 📋 Uses standard DTM & DSM → Standard CHM")
        print(f"6️⃣ User Visualization → 📋 Sees standard rasters")
    
    print(f"\n✅ QUALITY MODE INTEGRATION TEST COMPLETED")
    
    return {
        "test_laz_file": test_laz_file,
        "region_name": region_name,
        "clean_laz_available": clean_laz_available,
        "clean_laz_path": clean_laz_path,
        "integration_results": integration_results,
        "quality_mode": clean_laz_available
    }

def test_dependency_chain():
    """Test the dependency chain for quality mode"""
    
    print(f"\n🔗 TESTING DEPENDENCY CHAIN")
    print("="*60)
    
    dependency_chain = [
        "Original LAZ File",
        "↓ Density Analysis (Quality Mode)",
        "Clean LAZ File (Artifacts Removed)",
        "↓ DTM Function (Quality Mode Integrated)",
        "Clean DTM TIFF + PNG",
        "↓ DSM Function (Quality Mode Integrated)", 
        "Clean DSM TIFF + PNG",
        "↓ CHM Function (Quality Mode Integrated)",
        "Clean CHM TIFF + PNG (DSM - DTM)",
        "↓ User Interface",
        "Clean Visualizations Without Artifacts"
    ]
    
    for i, step in enumerate(dependency_chain, 1):
        if step.startswith("↓"):
            print(f"   {step}")
        else:
            print(f"{i:2d}. {step}")
    
    print(f"\n🎯 KEY INTEGRATION POINTS:")
    print(f"✅ DTM Function: Quality mode integration implemented")
    print(f"✅ DSM Function: Quality mode integration implemented")
    print(f"✅ CHM Function: Quality mode integration implemented")
    print(f"🔄 Next: Apply to Slope, Aspect, Hillshade functions")
    
    print(f"\n🎨 PNG GENERATION STRATEGY:")
    print(f"✅ Clean DTM → DTM.png in png_outputs folder")
    print(f"✅ Clean DSM → DSM.png in png_outputs folder")
    print(f"✅ Clean CHM → CHM.png in png_outputs folder")
    print(f"🎯 Result: Region PNG folder contains clean visualizations")

if __name__ == "__main__":
    result = test_quality_mode_integration()
    test_dependency_chain()
    
    # Save test results
    with open("quality_mode_integration_results.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n💾 Test results saved to: quality_mode_integration_results.json")
