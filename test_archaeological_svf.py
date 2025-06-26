#!/usr/bin/env python3
"""
Test the Archaeological SVF Implementation
==========================================

Tests both the new convert_svf_to_archaeological_png() function and the updated
convert_svf_to_cividis_png_clean() function with Archaeological Cividis Enhanced
5-95 percentile contrast enhancement.

Author: AI Assistant
Date: June 2025
"""

import sys
import os
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.convert import convert_svf_to_archaeological_png, convert_svf_to_cividis_png_clean

def test_archaeological_svf():
    """Test both SVF archaeological visualization functions."""
    
    # Test file path
    svf_test_file = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/SVF/svf_test.tif"
    
    if not os.path.exists(svf_test_file):
        print(f"❌ Test file not found: {svf_test_file}")
        return False
    
    print("🧪 TESTING ARCHAEOLOGICAL SVF IMPLEMENTATIONS")
    print("=" * 60)
    
    try:
        # Test 1: Archaeological SVF with full annotations
        print("\n📋 TEST 1: Archaeological SVF with Full Annotations")
        print("-" * 50)
        
        archaeological_png = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/SVF/test_archaeological_full.png"
        result1 = convert_svf_to_archaeological_png(
            tif_path=svf_test_file,
            png_path=archaeological_png,
            enhanced_resolution=True,
            save_to_consolidated=False,
            enhancement_type="archaeological_cividis"
        )
        print(f"✅ Archaeological SVF (full): {os.path.basename(result1)}")
        
        # Test 2: Archaeological SVF with high contrast
        print("\n📋 TEST 2: Archaeological SVF with High Contrast")
        print("-" * 50)
        
        high_contrast_png = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/SVF/test_archaeological_high_contrast.png"
        result2 = convert_svf_to_archaeological_png(
            tif_path=svf_test_file,
            png_path=high_contrast_png,
            enhanced_resolution=True,
            save_to_consolidated=False,
            enhancement_type="high_contrast"
        )
        print(f"✅ Archaeological SVF (high contrast): {os.path.basename(result2)}")
        
        # Test 3: Archaeological SVF with standard enhancement
        print("\n📋 TEST 3: Archaeological SVF with Standard Enhancement")
        print("-" * 50)
        
        standard_png = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/SVF/test_archaeological_standard.png"
        result3 = convert_svf_to_archaeological_png(
            tif_path=svf_test_file,
            png_path=standard_png,
            enhanced_resolution=True,
            save_to_consolidated=False,
            enhancement_type="standard"
        )
        print(f"✅ Archaeological SVF (standard): {os.path.basename(result3)}")
        
        # Test 4: Clean SVF with Archaeological Cividis Enhanced
        print("\n📋 TEST 4: Clean SVF with Archaeological Cividis Enhanced")
        print("-" * 50)
        
        clean_png = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/SVF/test_svf_clean_enhanced.png"
        result4 = convert_svf_to_cividis_png_clean(
            tif_path=svf_test_file,
            png_path=clean_png,
            enhanced_resolution=True,
            save_to_consolidated=False
        )
        print(f"✅ Clean SVF (Archaeological Cividis Enhanced): {os.path.basename(result4)}")
        
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Results in: /Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/Tests/SVF/")
        print("📁 test_archaeological_full.png - Full archaeological visualization")
        print("📁 test_archaeological_high_contrast.png - High contrast version")
        print("📁 test_archaeological_standard.png - Standard version")
        print("📁 test_svf_clean_enhanced.png - Clean overlay-ready version")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_archaeological_svf()
    sys.exit(0 if success else 1)
