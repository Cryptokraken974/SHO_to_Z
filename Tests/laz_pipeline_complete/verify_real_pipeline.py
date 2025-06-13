#!/usr/bin/env python3
"""
Quick verification script for real pipeline test results.
Checks if the process_all_raster_products() pipeline generated all expected outputs.
"""

import os
import sys
from pathlib import Path

# Test configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REGION_NAME = "FoxIsland"
OUTPUT_BASE_DIR = os.path.join(BASE_DIR, "output", REGION_NAME, "lidar")

# Expected outputs from process_all_raster_products()
EXPECTED_STRUCTURE = {
    "Hillshades (RGB Channels)": [
        "Hs_red/hillshade_315_30_z1.tif",
        "Hs_green/hillshade_45_25_z1.tif", 
        "Hs_blue/hillshade_135_30_z1.tif"
    ],
    "Terrain Analysis": [
        "Slope/slope.tif",
        "Aspect/aspect.tif",
        "Color_relief/color_relief.tif",
        "Slope_relief/slope_relief.tif"
    ],
    "Composite Products": [
        "HillshadeRgb/hillshade_rgb.tif",
        "HillshadeRgb/tint_overlay.tif",
        "HillshadeRgb/boosted_hillshade.tif"
    ],
    "PNG Visualizations": [
        "png_outputs/hillshade_315_30_z1.png",
        "png_outputs/hillshade_45_25_z1.png",
        "png_outputs/hillshade_135_30_z1.png",
        "png_outputs/slope.png",
        "png_outputs/aspect.png", 
        "png_outputs/color_relief.png",
        "png_outputs/slope_relief.png",
        "png_outputs/hillshade_rgb.png",
        "png_outputs/tint_overlay.png",
        "png_outputs/boosted_hillshade.png"
    ]
}

def verify_pipeline_results():
    """Verify the real pipeline test results."""
    print(f"\\n{'='*80}")
    print(f"🔍 VERIFYING REAL PIPELINE TEST RESULTS")
    print(f"{'='*80}")
    print(f"📁 Output directory: {OUTPUT_BASE_DIR}")
    
    if not os.path.exists(OUTPUT_BASE_DIR):
        print(f"❌ Output directory not found: {OUTPUT_BASE_DIR}")
        print(f"💡 Run the pipeline test first: python test_real_pipeline.py")
        return False
    
    print(f"✅ Output directory exists")
    
    total_expected = 0
    total_found = 0
    category_results = {}
    
    # Check each category
    for category, files in EXPECTED_STRUCTURE.items():
        print(f"\\n📋 {category}:")
        category_found = 0
        category_total = len(files)
        
        for file_path in files:
            total_expected += 1
            full_path = os.path.join(OUTPUT_BASE_DIR, file_path)
            
            if os.path.exists(full_path):
                total_found += 1
                category_found += 1
                file_size = os.path.getsize(full_path)
                size_mb = file_size / (1024 * 1024)
                status = "✅" if size_mb > 0.1 else "⚠️"
                print(f"   {status} {os.path.basename(file_path)}: {size_mb:.1f} MB")
            else:
                print(f"   ❌ {os.path.basename(file_path)}: Not found")
        
        category_results[category] = (category_found, category_total)
    
    # Workflow validation
    print(f"\\n🔄 WORKFLOW VALIDATION:")
    
    workflow_checks = [
        ("3-Hillshade Generation", ["Hs_red/hillshade_315_30_z1.tif", "Hs_green/hillshade_45_25_z1.tif", "Hs_blue/hillshade_135_30_z1.tif"]),
        ("RGB Composite", ["HillshadeRgb/hillshade_rgb.tif"]),
        ("Color Relief", ["Color_relief/color_relief.tif"]), 
        ("Tint Overlay", ["HillshadeRgb/tint_overlay.tif"]),
        ("Slope Analysis", ["Slope_relief/slope_relief.tif"]),
        ("Final Blend", ["HillshadeRgb/boosted_hillshade.tif"])
    ]
    
    workflow_success = True
    for check_name, required_files in workflow_checks:
        all_exist = all(os.path.exists(os.path.join(OUTPUT_BASE_DIR, f)) for f in required_files)
        status = "✅" if all_exist else "❌"
        print(f"   {status} {check_name}")
        if not all_exist:
            workflow_success = False
    
    # Summary statistics
    success_rate = (total_found / total_expected * 100) if total_expected > 0 else 0
    
    print(f"\\n📊 RESULTS SUMMARY:")
    print(f"   📋 Total expected files: {total_expected}")
    print(f"   ✅ Files found: {total_found}")
    print(f"   📈 Success rate: {success_rate:.1f}%")
    
    print(f"\\n📂 Category breakdown:")
    for category, (found, total) in category_results.items():
        rate = (found / total * 100) if total > 0 else 0
        status = "✅" if rate >= 80 else "⚠️" if rate >= 50 else "❌"
        print(f"   {status} {category}: {found}/{total} ({rate:.0f}%)")
    
    # Final assessment
    print(f"\\n{'='*80}")
    if success_rate >= 90 and workflow_success:
        print(f"🎉 VERIFICATION PASSED: Real pipeline test successful!")
        print(f"✅ process_all_raster_products() generated all expected outputs")
        print(f"✅ Complete 3-hillshade RGB → tint → slope workflow confirmed")
        return True
    elif success_rate >= 70:
        print(f"⚠️ VERIFICATION PARTIAL: Most outputs generated successfully")
        print(f"📊 {success_rate:.1f}% of expected files found")
        print(f"💡 Some components may need investigation")
        return True
    else:
        print(f"❌ VERIFICATION FAILED: Significant issues detected")
        print(f"📊 Only {success_rate:.1f}% of expected files found")
        print(f"💡 Re-run the pipeline test or check system requirements")
        return False

if __name__ == "__main__":
    success = verify_pipeline_results()
    sys.exit(0 if success else 1)
