#!/usr/bin/env python3
"""
Test script for integrated density analysis with raster cleaning
Demonstrates the complete workflow: density → mas    print("📊 WORKFLOW SUMMARY")
    print("-" * 40) cleaning
"""

import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from processing.density_analysis import analyze_laz_density, analyze_laz_density_quality_mode
from processing.raster_cleaning import RasterCleaner

def test_integrated_workflow():
    """Test the complete integrated workflow"""
    
    print("🧪 TESTING INTEGRATED DENSITY ANALYSIS + RASTER CLEANING")
    print("=" * 60)
    
    # Test parameters
    test_laz = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ/PRGL1260C9597_2014.laz"
    test_output_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/prgl/test_integrated"
    
    # Check if test LAZ file exists
    if not os.path.exists(test_laz):
        print(f"❌ Test LAZ file not found: {test_laz}")
        print("Please provide a valid LAZ file path")
        return False
    
    print(f"📁 Test LAZ file: {test_laz}")
    print(f"📁 Output directory: {test_output_dir}")
    print()
    
    # Step 1: Run density analysis with complete workflow
    print("🚀 STEP 1: Complete Density Analysis Workflow")
    print("-" * 40)
    
    result = analyze_laz_density(
        laz_file_path=test_laz,
        output_dir=test_output_dir,
        region_name="prgl_test",
        resolution=1.0,
        mask_threshold=2.0,
        generate_mask=True,
        clean_existing_rasters=True,  # Enable integrated cleaning
        generate_polygon=True,        # Enable polygon generation
        crop_original_laz=True,       # Enable LAZ cropping
        polygon_format="GeoJSON"      # Output format for polygon
    )
    
    if not result.get("success"):
        print(f"❌ Density analysis failed: {result.get('error')}")
        return False
    
    print(f"✅ Density analysis completed successfully!")
    print(f"   Region: {result.get('region_name')}")
    print(f"   Density TIFF: {Path(result.get('tiff_path', '')).name}")
    print(f"   Density PNG: {Path(result.get('png_path', '')).name}")
    print()
    
    # Step 2: Check mask results
    mask_results = result.get("mask_results", {})
    if mask_results and not mask_results.get("error"):
        print("🎭 STEP 2: Binary Mask Results")
        print("-" * 40)
        
        mask_stats = mask_results.get("statistics", {})
        print(f"   Mask TIFF: {Path(mask_results.get('tiff_path', '')).name}")
        print(f"   Mask PNG: {Path(mask_results.get('png_path', '')).name}")
        print(f"   Threshold: {mask_stats.get('threshold', 'N/A')} points/cell")
        print(f"   Coverage: {mask_stats.get('coverage_percentage', 'N/A')}% valid")
        print(f"   Artifacts: {mask_stats.get('artifact_percentage', 'N/A')}% removed")
        print()
    
    # Step 3: Check cleaning results
    cleaning_results = result.get("cleaning_results", {})
    if cleaning_results and not cleaning_results.get("error"):
        print("🧹 STEP 3: Raster Cleaning Results")
        print("-" * 40)
        
        if cleaning_results.get("success"):
            print(f"   Files processed: {cleaning_results.get('files_processed', 0)}")
            print(f"   Successful cleanings: {cleaning_results.get('successful_cleanings', 0)}")
            print(f"   Target directory: {cleaning_results.get('target_directory', 'N/A')}")
            print(f"   Mask used: {Path(cleaning_results.get('mask_used', '')).name}")
            
            # Show cleaned files
            cleaned_files = [r.get('output_path') for r in cleaning_results.get('results', []) if r.get('success')]
            if cleaned_files:
                print(f"   Cleaned files:")
                for file_path in cleaned_files[:5]:  # Show first 5
                    print(f"     - {Path(file_path).name}")
                if len(cleaned_files) > 5:
                    print(f"     ... and {len(cleaned_files) - 5} more")
        else:
            print(f"   Cleaning message: {cleaning_results.get('message', 'No details available')}")
        print()
    
    # Step 4: Check polygon results
    polygon_results = result.get("polygon_results", {})
    if polygon_results and not polygon_results.get("error"):
        print("🔗 STEP 4: Polygon Generation Results")
        print("-" * 40)
        
        polygon_stats = polygon_results.get("statistics", {})
        print(f"   Vector file: {Path(polygon_results.get('vector_path', '')).name}")
        print(f"   Output format: {polygon_results.get('output_format', 'N/A')}")
        print(f"   Method used: {polygon_results.get('method_used', 'N/A')}")
        print(f"   Polygons: {polygon_stats.get('polygon_count', 'N/A')}")
        print(f"   Total area: {polygon_stats.get('total_area_sqm', 'N/A'):.1f} m²" if polygon_stats.get('total_area_sqm') else "")
        print()
    
    # Step 5: Check LAZ cropping results
    cropping_results = result.get("cropping_results", {})
    if cropping_results and not cropping_results.get("error"):
        print("✂️ STEP 5: LAZ Cropping Results")
        print("-" * 40)
        
        cropping_stats = cropping_results.get("statistics", {})
        print(f"   Cropped LAZ: {Path(cropping_results.get('cropped_laz_path', '')).name}")
        print(f"   Output format: {cropping_results.get('output_format', 'N/A')}")
        print(f"   Crop method: {cropping_results.get('crop_method', 'N/A')}")
        
        if cropping_stats.get('original') and cropping_stats.get('cropped'):
            orig_pts = cropping_stats['original'].get('point_count', 0)
            crop_pts = cropping_stats['cropped'].get('point_count', 0)
            retention = cropping_stats.get('retention_percentage', 0)
            
            print(f"   Original points: {orig_pts:,}")
            print(f"   Cropped points: {crop_pts:,}")
            print(f"   Point retention: {retention:.1f}%")
            
            orig_size = cropping_stats['original'].get('file_size_mb', 0)
            crop_size = cropping_stats['cropped'].get('file_size_mb', 0)
            print(f"   Original size: {orig_size:.1f} MB")
            print(f"   Cropped size: {crop_size:.1f} MB")
        print()
    
    # Step 6: Display summary
    print("📊 WORKFLOW SUMMARY")
    print("-" * 40)
    
    metadata = result.get("metadata", {})
    input_info = metadata.get("input", {})
    output_info = metadata.get("output", {})
    
    print(f"   Input file: {input_info.get('file_name', 'N/A')} ({input_info.get('file_size_mb', 0):.1f} MB)")
    print(f"   Density raster: {output_info.get('tiff_size_mb', 0):.1f} MB")
    print(f"   Analysis timestamp: {metadata.get('timestamp', 'N/A')}")
    
    # Check if all steps completed
    steps_completed = []
    if result.get("success"):
        steps_completed.append("✅ Density Analysis")
    if mask_results and not mask_results.get("error"):
        steps_completed.append("✅ Binary Mask")
    if cleaning_results and cleaning_results.get("success"):
        steps_completed.append("✅ Raster Cleaning")
    if polygon_results and polygon_results.get("success"):
        steps_completed.append("✅ Polygon Generation")  
    if cropping_results and cropping_results.get("success"):
        steps_completed.append("✅ LAZ Cropping")
    
    print(f"   Steps completed: {', '.join(steps_completed)}")
    print()
    
    print("🎉 INTEGRATED WORKFLOW TEST COMPLETED SUCCESSFULLY!")
    return True

def test_quality_mode():
    """Test the quality mode workflow"""
    
    print("\n🌟 TESTING QUALITY MODE WORKFLOW")
    print("=" * 60)
    
    # Test parameters for quality mode
    test_laz = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ/PRGL1260C9597_2014.laz"
    test_output_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/prgl/test_quality_mode"
    
    # Check if test LAZ file exists
    if not os.path.exists(test_laz):
        print(f"❌ Test LAZ file not found: {test_laz}")
        return False
    
    print(f"📁 Test LAZ file: {test_laz}")
    print(f"📁 Output directory: {test_output_dir}")
    print()
    
    # Run quality mode analysis
    print("🚀 Running quality mode analysis...")
    result = analyze_laz_density_quality_mode(
        laz_file_path=test_laz,
        output_dir=test_output_dir,
        region_name="prgl_quality",
        resolution=1.0,
        mask_threshold=2.0,
        regenerate_rasters=True,  # Enable raster regeneration framework
        polygon_format="GeoJSON"
    )
    
    if not result.get("success"):
        print(f"❌ Quality mode failed: {result.get('error')}")
        return False
    
    print(f"✅ Quality mode completed successfully!")
    print()
    
    # Show quality mode results
    print("📊 QUALITY MODE RESULTS:")
    print("-" * 40)
    
    quality_metadata = result.get("quality_metadata", {})
    input_analysis = quality_metadata.get("input_analysis", {})
    quality_metrics = quality_metadata.get("quality_metrics", {})
    processing_steps = quality_metadata.get("processing_steps", {})
    
    print(f"   Workflow mode: {result.get('workflow_mode', 'N/A')}")
    print(f"   Original LAZ: {Path(input_analysis.get('original_laz_path', '')).name}")
    cropped_path = input_analysis.get('cropped_laz_path')
    if cropped_path:
        print(f"   Cropped LAZ: {Path(cropped_path).name}")
    else:
        print(f"   Cropped LAZ: Not generated")
    print()
    
    print("📈 SIZE ANALYSIS:")
    print(f"   Original size: {input_analysis.get('original_size_mb', 'N/A')} MB")
    print(f"   Cropped size: {input_analysis.get('cropped_size_mb', 'N/A')} MB")
    print(f"   Size reduction: {input_analysis.get('size_reduction_percentage', 'N/A'):.1f}%")
    print()
    
    print("🎯 QUALITY METRICS:")
    print(f"   Mask coverage: {quality_metrics.get('mask_coverage_percentage', 'N/A'):.1f}%")
    print(f"   Artifact removal: {quality_metrics.get('artifact_removal_percentage', 'N/A'):.1f}%")
    print(f"   Point retention: {quality_metrics.get('point_retention_percentage', 'N/A'):.1f}%")
    print()
    
    print("✅ PROCESSING STEPS:")
    for step, status in processing_steps.items():
        status_icon = "✅" if status else "❌"
        step_name = step.replace('_', ' ').title()
        print(f"   {status_icon} {step_name}")
    print()
    
    # Show file outputs
    print("📁 QUALITY MODE OUTPUTS:")
    cropped_laz = result.get("cropped_laz_path")
    if cropped_laz and os.path.exists(cropped_laz):
        print(f"   ✅ Cropped LAZ: {Path(cropped_laz).name}")
    
    regeneration_results = result.get("regeneration_results", {})
    if regeneration_results.get("success"):
        raster_count = regeneration_results.get("rasters_generated", 0)
        print(f"   ✅ Raster framework: {raster_count} raster types prepared")
        print(f"   📁 Clean rasters dir: {Path(regeneration_results.get('output_directory', '')).name}")
    
    print()
    print("🌟 Quality mode provides the highest quality results by:")
    print("   • Generating rasters from clean point data")
    print("   • Eliminating interpolated artifacts at source")
    print("   • Creating smaller, more accurate datasets")
    
    return True

def test_standalone_cleaning():
    """Test standalone raster cleaning functionality"""
    
    print("\n🧪 TESTING STANDALONE RASTER CLEANING")
    print("=" * 60)
    
    # Test parameters for standalone cleaning
    test_mask = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/prgl/test_integrated/density/masks/prgl_test_valid_mask.tif"
    test_raster_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/prgl"
    
    # Check if mask exists
    if not os.path.exists(test_mask):
        print(f"❌ Test mask not found: {test_mask}")
        print("Run the integrated workflow test first to generate a mask")
        return False
    
    print(f"📁 Test mask: {test_mask}")
    print(f"📁 Raster directory: {test_raster_dir}")
    print()
    
    # Initialize standalone cleaner
    cleaner = RasterCleaner(method="auto", nodata_value=0)
    
    # Run region cleaning
    print("🚀 Running standalone region cleaning...")
    result = cleaner.clean_region_rasters(
        region_dir=test_raster_dir,
        mask_path=test_mask,
        raster_types=None  # Clean all raster types
    )
    
    if result.get("success"):
        print(f"✅ Standalone cleaning completed!")
        print(f"   Files processed: {result.get('files_processed', 0)}")
        print(f"   Successful cleanings: {result.get('successful_cleanings', 0)}")
        print(f"   Output directory: {result.get('output_directory', 'N/A')}")
    else:
        print(f"❌ Standalone cleaning failed: {result.get('error')}")
        return False
    
    return True

if __name__ == "__main__":
    print("🌟 INTEGRATED DENSITY ANALYSIS + RASTER CLEANING TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        # Test integrated workflow
        success1 = test_integrated_workflow()
        
        # Test quality mode
        success2 = test_quality_mode()
        
        # Test standalone cleaning
        success3 = test_standalone_cleaning()
        
        if success1 and success2 and success3:
            print("\n🎊 ALL TESTS COMPLETED SUCCESSFULLY!")
            print("Both standard and quality mode LAZ processing workflows are ready!")
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
