#!/usr/bin/env python3
"""
Test Complete Quality Mode Workflow for LAZ Pipeline

This script simulates the complete data flow and function calls from loading a LAZ file 
through the quality mode pipeline to confirm that:
1. LAZ is cleaned using the new quality mode process
2. Rasters are generated using the clean LAS file  
3. PNGs generated from the cleaned rasters are placed in the png_outputs folder

Based on the conversation summary, we need to trigger the quality mode with:
- crop_laz_first=True
- regenerate_rasters=True
"""

import os
import sys
import time
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.append('app')

from processing.density_analysis import analyze_laz_density_quality_mode

def main():
    print("🔬 COMPLETE QUALITY MODE WORKFLOW TEST")
    print("=" * 60)
    print("Testing LAZ → Quality Mode Analysis → Clean LAZ → Rasters → PNGs")
    print()
    
    # Configuration
    test_laz = "input/LAZ/PRGL1260C9597_2014.laz"
    region_name = "PRGL1260C9597_2014"
    output_base = f"output/{region_name}"
    
    # Verify LAZ file exists
    if not os.path.exists(test_laz):
        print(f"❌ LAZ file not found: {test_laz}")
        return False
    
    print(f"📄 Input LAZ: {test_laz}")
    print(f"🎯 Region: {region_name}")
    print(f"📁 Output base: {output_base}")
    print()
    
    # Get LAZ file size
    laz_size = os.path.getsize(test_laz)
    laz_size_mb = laz_size / (1024 * 1024)
    print(f"📊 LAZ file size: {laz_size_mb:.1f} MB")
    print()
    
    # Start timing
    start_time = time.time()
    
    # ===== QUALITY MODE WORKFLOW =====
    print("🌟 EXECUTING QUALITY MODE WORKFLOW")
    print("-" * 50)
    print("Step 1: Generate density raster and mask from original LAZ")
    print("Step 2: Create polygon from binary mask") 
    print("Step 3: Crop original LAZ using polygon")
    print("Step 4: Regenerate all rasters from clean LAZ data")
    print("Step 5: Generate PNGs and place in png_outputs folder")
    print()
    
    try:
        # Execute quality mode analysis with raster regeneration
        result = analyze_laz_density_quality_mode(
            laz_file_path=test_laz,
            output_dir=f"{output_base}/lidar",
            region_name=region_name,
            resolution=1.0,
            mask_threshold=2.0,
            regenerate_rasters=True,  # 🎯 KEY: This triggers raster generation from clean LAZ
            polygon_format="GeoJSON"
        )
        
        processing_time = time.time() - start_time
        
        if result.get("success"):
            print("✅ QUALITY MODE WORKFLOW COMPLETED SUCCESSFULLY")
            print(f"⏱️ Total processing time: {processing_time:.1f} seconds")
            print()
            
            # Analyze results
            analyze_workflow_results(result, output_base, region_name)
            
            return True
            
        else:
            print("❌ QUALITY MODE WORKFLOW FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ WORKFLOW EXECUTION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def analyze_workflow_results(result, output_base, region_name):
    """Analyze the quality mode workflow results"""
    print("📊 WORKFLOW RESULTS ANALYSIS")
    print("-" * 40)
    
    # 1. Check density analysis results
    print("1️⃣ DENSITY ANALYSIS:")
    if result.get("tiff_path"):
        print(f"   ✅ Density raster: {Path(result['tiff_path']).name}")
    if result.get("png_path"):
        print(f"   ✅ Density PNG: {Path(result['png_path']).name}")
    
    mask_results = result.get("mask_results", {})
    if mask_results.get("success"):
        print(f"   ✅ Binary mask: {Path(mask_results['mask_path']).name}")
        stats = mask_results.get("statistics", {})
        if stats:
            print(f"   📊 Coverage: {stats.get('coverage_percentage', 0):.1f}%")
            print(f"   📊 Artifacts: {stats.get('artifact_percentage', 0):.1f}%")
    print()
    
    # 2. Check LAZ cropping results
    print("2️⃣ LAZ CROPPING:")
    cropping_results = result.get("cropping_results", {})
    if cropping_results.get("success"):
        cropped_path = cropping_results.get("cropped_laz_path")
        if cropped_path and os.path.exists(cropped_path):
            print(f"   ✅ Clean LAZ: {Path(cropped_path).name}")
            cropped_size = os.path.getsize(cropped_path) / (1024 * 1024)
            print(f"   📊 Clean LAZ size: {cropped_size:.1f} MB")
            
            stats = cropping_results.get("statistics", {})
            if stats.get("retention_percentage"):
                print(f"   📊 Point retention: {stats['retention_percentage']:.1f}%")
        else:
            print("   ❌ Clean LAZ file not found")
    else:
        print("   ❌ LAZ cropping failed")
    print()
    
    # 3. Check raster regeneration results
    print("3️⃣ RASTER REGENERATION:")
    regeneration_results = result.get("regeneration_results", {})
    if regeneration_results.get("success"):
        rasters_generated = regeneration_results.get("rasters_generated", 0)
        print(f"   ✅ Regenerated rasters: {rasters_generated}")
        
        # List generated raster files
        raster_dir = Path(output_base) / "lidar"
        if raster_dir.exists():
            raster_files = list(raster_dir.glob("**/*.tif"))
            print(f"   📄 Total raster files found: {len(raster_files)}")
            for raster_file in sorted(raster_files)[:10]:  # Show first 10
                print(f"      - {raster_file.name}")
            if len(raster_files) > 10:
                print(f"      ... and {len(raster_files) - 10} more")
    else:
        print("   ❌ Raster regeneration failed or not executed")
    print()
    
    # 4. Check PNG outputs
    print("4️⃣ PNG OUTPUTS:")
    png_dir = Path(output_base) / "lidar" / "png_outputs"
    if png_dir.exists():
        png_files = list(png_dir.glob("*.png"))
        print(f"   ✅ PNG outputs folder: {len(png_files)} files")
        for png_file in sorted(png_files):
            print(f"      - {png_file.name}")
    else:
        print("   ❌ PNG outputs folder not found")
    print()
    
    # 5. Check quality metadata
    print("5️⃣ QUALITY METADATA:")
    quality_metadata = result.get("quality_metadata")
    if quality_metadata:
        metadata_path = result.get("quality_metadata_path")
        if metadata_path and os.path.exists(metadata_path):
            print(f"   ✅ Quality metadata: {Path(metadata_path).name}")
            
            # Show key quality metrics
            input_analysis = quality_metadata.get("input_analysis", {})
            quality_metrics = quality_metadata.get("quality_metrics", {})
            
            if input_analysis:
                print(f"   📊 Original size: {input_analysis.get('original_size_mb', 'N/A')} MB")
                print(f"   📊 Cropped size: {input_analysis.get('cropped_size_mb', 'N/A')} MB")
                
            if quality_metrics:
                print(f"   📊 Improvement score: {quality_metrics.get('improvement_score', 'N/A')}")
        else:
            print("   ❌ Quality metadata file not found")
    else:
        print("   ❌ Quality metadata not generated")
    print()

def verify_complete_pipeline():
    """Verify that the complete pipeline executed correctly"""
    print("🔍 PIPELINE VERIFICATION")
    print("-" * 30)
    
    region_name = "PRGL1260C9597_2014"
    output_base = f"output/{region_name}"
    
    # Check key files exist
    checks = [
        ("Density raster", f"{output_base}/lidar/density/{region_name}_density.tif"),
        ("Density PNG", f"{output_base}/lidar/density/{region_name}_density.png"),
        ("Binary mask", f"{output_base}/lidar/density/masks/{region_name}_valid_mask.tif"),
        ("Clean LAZ", f"{output_base}/lidar/cropped/{region_name}_cropped.las"),
        ("PNG outputs folder", f"{output_base}/lidar/png_outputs"),
        ("Quality metadata", f"{output_base}/lidar/density/{region_name}_quality_mode_metadata.json")
    ]
    
    all_passed = True
    for check_name, file_path in checks:
        if os.path.exists(file_path):
            print(f"   ✅ {check_name}")
        else:
            print(f"   ❌ {check_name} - NOT FOUND: {file_path}")
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 COMPLETE PIPELINE VERIFICATION: ALL CHECKS PASSED")
        print("   Quality mode workflow successfully executed!")
        print("   LAZ was cleaned and rasters generated from clean data")
        print("   PNGs are ready in the png_outputs folder")
    else:
        print("⚠️ PIPELINE VERIFICATION: SOME CHECKS FAILED")
        print("   Review the missing files above")
    
    return all_passed

if __name__ == "__main__":
    print("Starting quality mode workflow test...")
    print()
    
    success = main()
    print()
    
    if success:
        verify_complete_pipeline()
    
    print()
    print("🏁 Test completed")
    sys.exit(0 if success else 1)
