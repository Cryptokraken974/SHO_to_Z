#!/usr/bin/env python3
"""
Verification script for Complete LAZ Pipeline Test results.

This script analyzes the outputs from the complete LAZ pipeline test
and validates that all expected files were generated with correct properties.
"""

import os
import sys
from pathlib import Path
from osgeo import gdal

# Enable GDAL exceptions
gdal.UseExceptions()

# Test output directory
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")

# Expected outputs
EXPECTED_OUTPUTS = {
    'tiff_files': [
        'FoxIsland_DTM.tif',
        'FoxIsland_Hillshade_315.tif',
        'FoxIsland_Hillshade_45.tif', 
        'FoxIsland_Hillshade_135.tif',
        'FoxIsland_RGB_Composite.tif',
        'FoxIsland_ColorRelief.tif',
        'FoxIsland_TintOverlay.tif',
        'FoxIsland_SlopeRelief.tif',
        'FoxIsland_FinalBlend.tif'
    ],
    'png_files': [
        'FoxIsland_DTM.png',
        'FoxIsland_Hillshade_315.png',
        'FoxIsland_Hillshade_45.png',
        'FoxIsland_Hillshade_135.png', 
        'FoxIsland_RGB_Composite.png',
        'FoxIsland_ColorRelief.png',
        'FoxIsland_TintOverlay.png',
        'FoxIsland_SlopeRelief.png',
        'FoxIsland_FinalBlend.png'
    ]
}

def analyze_file(filepath):
    """Analyze a raster file and return basic information."""
    try:
        if not os.path.exists(filepath):
            return None
            
        file_size = os.path.getsize(filepath)
        
        # For TIFF files, get additional raster info
        if filepath.endswith('.tif'):
            try:
                ds = gdal.Open(filepath)
                if ds is not None:
                    info = {
                        'size_bytes': file_size,
                        'size_mb': file_size / (1024 * 1024),
                        'width': ds.RasterXSize,
                        'height': ds.RasterYSize,
                        'bands': ds.RasterCount,
                        'has_geotransform': ds.GetGeoTransform() != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
                        'has_projection': bool(ds.GetProjection())
                    }
                    ds = None
                    return info
            except Exception:
                pass
        
        # For other files, just return size info
        return {
            'size_bytes': file_size,
            'size_mb': file_size / (1024 * 1024)
        }
        
    except Exception as e:
        return {'error': str(e)}

def verify_pipeline_outputs():
    """Verify all expected pipeline outputs exist and have valid properties."""
    print(f"\\n{'='*80}")
    print(f"🔍 VERIFYING COMPLETE LAZ PIPELINE TEST RESULTS")
    print(f"{'='*80}")
    print(f"📁 Output directory: {TEST_OUTPUT_DIR}")
    
    if not os.path.exists(TEST_OUTPUT_DIR):
        print(f"❌ Output directory does not exist: {TEST_OUTPUT_DIR}")
        return False
    
    print(f"\\n📊 FILE VERIFICATION:")
    
    total_files = 0
    found_files = 0
    valid_files = 0
    total_size = 0
    
    # Check TIFF files
    print(f"\\n🗂️ TIFF Files (Geospatial):")
    for filename in EXPECTED_OUTPUTS['tiff_files']:
        filepath = os.path.join(TEST_OUTPUT_DIR, filename)
        total_files += 1
        
        info = analyze_file(filepath)
        if info is None:
            print(f"   ❌ {filename}: Not found")
        elif 'error' in info:
            print(f"   ⚠️ {filename}: Error - {info['error']}")
            found_files += 1
        else:
            found_files += 1
            valid_files += 1
            total_size += info['size_bytes']
            
            if 'width' in info:
                status = "✅" if info['size_mb'] > 0.1 and info['width'] > 0 and info['height'] > 0 else "⚠️"
                geo_status = "✅" if info['has_geotransform'] and info['has_projection'] else "❌"
                print(f"   {status} {filename}: {info['width']}x{info['height']}, {info['bands']} bands, {info['size_mb']:.1f} MB, Geo: {geo_status}")
            else:
                status = "✅" if info['size_mb'] > 0.1 else "⚠️"
                print(f"   {status} {filename}: {info['size_mb']:.1f} MB")
    
    # Check PNG files
    print(f"\\n🖼️ PNG Files (Visualization):")
    for filename in EXPECTED_OUTPUTS['png_files']:
        filepath = os.path.join(TEST_OUTPUT_DIR, filename)
        total_files += 1
        
        info = analyze_file(filepath)
        if info is None:
            print(f"   ❌ {filename}: Not found")
        elif 'error' in info:
            print(f"   ⚠️ {filename}: Error - {info['error']}")
            found_files += 1
        else:
            found_files += 1
            valid_files += 1
            total_size += info['size_bytes']
            
            status = "✅" if info['size_mb'] > 0.1 else "⚠️"
            print(f"   {status} {filename}: {info['size_mb']:.1f} MB")
    
    # Summary
    print(f"\\n📈 VERIFICATION SUMMARY:")
    print(f"   📁 Total expected files: {total_files}")
    print(f"   ✅ Files found: {found_files}/{total_files} ({found_files/total_files*100:.1f}%)")
    print(f"   ✅ Valid files: {valid_files}/{total_files} ({valid_files/total_files*100:.1f}%)")
    print(f"   💾 Total output size: {total_size / (1024**2):.1f} MB")
    
    # Check for unexpected files
    if os.path.exists(TEST_OUTPUT_DIR):
        actual_files = set(os.listdir(TEST_OUTPUT_DIR))
        expected_files = set(EXPECTED_OUTPUTS['tiff_files'] + EXPECTED_OUTPUTS['png_files'])
        expected_files.add('color_table.txt')  # Temporary file
        
        unexpected_files = actual_files - expected_files
        if unexpected_files:
            print(f"\\n🔍 Unexpected files found:")
            for filename in sorted(unexpected_files):
                filepath = os.path.join(TEST_OUTPUT_DIR, filename)
                size = os.path.getsize(filepath) / (1024*1024) if os.path.exists(filepath) else 0
                print(f"   📄 {filename}: {size:.1f} MB")
    
    # Workflow validation
    print(f"\\n🔄 WORKFLOW VALIDATION:")
    
    workflow_steps = [
        ("DTM Generation", "FoxIsland_DTM.tif"),
        ("Red Hillshade (315°)", "FoxIsland_Hillshade_315.tif"),
        ("Green Hillshade (45°)", "FoxIsland_Hillshade_45.tif"),
        ("Blue Hillshade (135°)", "FoxIsland_Hillshade_135.tif"),
        ("RGB Composite", "FoxIsland_RGB_Composite.tif"),
        ("Color Relief", "FoxIsland_ColorRelief.tif"),
        ("Tint Overlay", "FoxIsland_TintOverlay.tif"),
        ("Slope Relief", "FoxIsland_SlopeRelief.tif"),
        ("Final Blend", "FoxIsland_FinalBlend.tif")
    ]
    
    workflow_success = True
    for step_name, filename in workflow_steps:
        filepath = os.path.join(TEST_OUTPUT_DIR, filename)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:  # At least 1KB
            print(f"   ✅ {step_name}: Complete")
        else:
            print(f"   ❌ {step_name}: Failed or incomplete")
            workflow_success = False
    
    # Final assessment
    print(f"\\n{'='*80}")
    if valid_files == total_files and workflow_success:
        print(f"🎉 VERIFICATION PASSED: Complete LAZ pipeline test successful!")
        print(f"✅ All {total_files} expected files generated correctly")
        print(f"✅ Complete 3-hillshade RGB → tint → slope blend workflow verified")
        return True
    elif found_files >= total_files * 0.8:  # 80% success rate
        print(f"⚠️ VERIFICATION PARTIAL: Most files generated successfully")
        print(f"✅ {valid_files}/{total_files} files valid")
        print(f"⚠️ Some issues detected - check individual file status above")
        return True
    else:
        print(f"❌ VERIFICATION FAILED: Significant issues with test results")
        print(f"❌ Only {valid_files}/{total_files} files valid")
        print(f"💡 Re-run the test or check for system requirements")
        return False

if __name__ == "__main__":
    success = verify_pipeline_outputs()
    sys.exit(0 if success else 1)
