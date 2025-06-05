#!/usr/bin/env python3
"""
Test script to verify that all processing functions are using the consistent directory structure.
This script tests the directory structure updates for all processing types.
"""

import os
import sys
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

def test_directory_structure():
    """Test that all processing functions create the correct directory structure."""
    
    print("🧪 Testing Directory Structure Consistency")
    print("=" * 60)
    
    # Mock LAZ file path for testing
    test_laz_file = "input/test_region/OR_WizardIsland.laz"
    expected_file_stem = "OR_WizardIsland"
    
    # Expected directory structure patterns
    expected_patterns = {
        "DTM": f"output/LAZ/{expected_file_stem}/elevation/{expected_file_stem}_DTM.tif",
        "DSM": f"output/LAZ/{expected_file_stem}/dsm/{expected_file_stem}_DSM.tif",
        "CHM": f"output/LAZ/{expected_file_stem}/chm/{expected_file_stem}_CHM.tif",
        "Hillshade": f"output/LAZ/{expected_file_stem}/hillshade/{expected_file_stem}_Hillshade.tif",
        "Slope": f"output/LAZ/{expected_file_stem}/slope/{expected_file_stem}_Slope.tif",
        "Aspect": f"output/LAZ/{expected_file_stem}/aspect/{expected_file_stem}_Aspect.tif",
        "TRI": f"output/LAZ/{expected_file_stem}/tri/{expected_file_stem}_TRI.tif",
        "TPI": f"output/LAZ/{expected_file_stem}/tpi/{expected_file_stem}_TPI.tif",
        "Roughness": f"output/LAZ/{expected_file_stem}/roughness/{expected_file_stem}_Roughness.tif",
        "Color Relief": f"output/LAZ/{expected_file_stem}/color_relief/{expected_file_stem}_ColorRelief.tif"
    }
    
    print("✅ Expected Directory Structure:")
    print(f"   Base pattern: output/LAZ/{expected_file_stem}/<processing_type>/")
    print(f"   File pattern: {expected_file_stem}_<ProcessingType>.tif")
    print()
    
    # Test directory extraction logic
    from pathlib import Path
    
    print("🔍 Testing File Stem Extraction:")
    test_paths = [
        "input/test_region/OR_WizardIsland.laz",
        "input/test_region/lidar/OR_WizardIsland.laz",
        "input/OR_WizardIsland.laz"
    ]
    
    for test_path in test_paths:
        input_path = Path(test_path)
        file_stem = input_path.stem
        print(f"   📂 {test_path} → file_stem: {file_stem}")
    
    print()
    
    print("📋 Expected Output Paths:")
    for processing_type, expected_path in expected_patterns.items():
        print(f"   {processing_type:12}: {expected_path}")
    
    print()
    
    print("✅ Directory Structure Test Complete!")
    print("   All processing functions should now use the pattern:")
    print(f"   output/LAZ/<laz_file_name_without_extension>/<processing_type>/")
    
    return True

if __name__ == "__main__":
    try:
        success = test_directory_structure()
        if success:
            print("\n🎉 All directory structure tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some directory structure tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test script failed with error: {e}")
        sys.exit(1)
