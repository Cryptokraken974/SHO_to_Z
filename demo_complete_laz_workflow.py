#!/usr/bin/env python3
"""
Complete LAZ Processing Demo
Demonstrates the full 5-step workflow:
1. Density Analysis
2. Binary Mask Generation  
3. Raster Cleaning
4. Polygon Generation
5. LAZ Cropping
"""

import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from processing.density_analysis import analyze_laz_density

def demo_complete_workflow():
    """Demonstrate the complete 5-step LAZ processing workflow"""
    
    print("🚀 COMPLETE LAZ PROCESSING WORKFLOW DEMO")
    print("=" * 60)
    print("Steps: Density → Mask → Cleaning → Polygon → Cropping")
    print()
    
    # Configuration
    test_laz = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/prgl/prgl_sample.laz"
    output_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/prgl/complete_demo"
    
    # Check if test file exists
    if not os.path.exists(test_laz):
        print(f"❌ Test LAZ file not found: {test_laz}")
        print("Please provide a valid LAZ file path")
        return False
    
    print(f"📁 Input LAZ: {test_laz}")
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Execute complete workflow
    print("🎯 EXECUTING COMPLETE WORKFLOW")
    print("=" * 50)
    
    result = analyze_laz_density(
        laz_file_path=test_laz,
        output_dir=output_dir,
        region_name="prgl_complete",
        resolution=1.0,
        mask_threshold=2.0,
        generate_mask=True,           # Step 2: Generate binary mask
        clean_existing_rasters=True,  # Step 3: Clean existing rasters  
        generate_polygon=True,        # Step 4: Generate polygon from mask
        crop_original_laz=True,       # Step 5: Crop LAZ with polygon
        polygon_format="GeoJSON"
    )
    
    if not result.get("success"):
        print(f"❌ Workflow failed: {result.get('error')}")
        return False
    
    print()
    print("📊 WORKFLOW RESULTS SUMMARY")
    print("=" * 50)
    
    # Step 1: Density Analysis
    print("1️⃣ DENSITY ANALYSIS")
    print(f"   ✅ Density raster: {Path(result.get('tiff_path', '')).name}")
    print(f"   ✅ Visualization: {Path(result.get('png_path', '')).name}")
    
    # Step 2: Binary Mask
    mask_results = result.get("mask_results", {})
    if mask_results and not mask_results.get("error"):
        print("2️⃣ BINARY MASK GENERATION")
        mask_stats = mask_results.get("statistics", {})
        print(f"   ✅ Binary mask: {Path(mask_results.get('tiff_path', '')).name}")
        print(f"   📊 Coverage: {mask_stats.get('coverage_percentage', 0):.1f}% valid data")
        print(f"   📊 Artifacts: {mask_stats.get('artifact_percentage', 0):.1f}% removed")
    
    # Step 3: Raster Cleaning
    cleaning_results = result.get("cleaning_results", {})
    if cleaning_results and cleaning_results.get("success"):
        print("3️⃣ RASTER CLEANING")
        print(f"   ✅ Files processed: {cleaning_results.get('files_processed', 0)}")
        print(f"   ✅ Successful cleanings: {cleaning_results.get('successful_cleanings', 0)}")
        print(f"   📁 Output: {Path(cleaning_results.get('target_directory', '')).name}/cleaned/")
    
    # Step 4: Polygon Generation
    polygon_results = result.get("polygon_results", {})
    if polygon_results and polygon_results.get("success"):
        print("4️⃣ POLYGON GENERATION")
        polygon_stats = polygon_results.get("statistics", {})
        print(f"   ✅ Vector file: {Path(polygon_results.get('vector_path', '')).name}")
        print(f"   📊 Format: {polygon_results.get('output_format', 'N/A')}")
        print(f"   📊 Polygons: {polygon_stats.get('polygon_count', 'N/A')}")
        if polygon_stats.get('total_area_sqm'):
            area_hectares = polygon_stats['total_area_sqm'] / 10000
            print(f"   📊 Total area: {area_hectares:.2f} hectares")
    
    # Step 5: LAZ Cropping
    cropping_results = result.get("cropping_results", {})
    if cropping_results and cropping_results.get("success"):
        print("5️⃣ LAZ CROPPING")
        cropping_stats = cropping_results.get("statistics", {})
        print(f"   ✅ Cropped LAZ: {Path(cropping_results.get('cropped_laz_path', '')).name}")
        
        if cropping_stats.get('retention_percentage'):
            print(f"   📊 Point retention: {cropping_stats['retention_percentage']:.1f}%")
        
        orig_stats = cropping_stats.get('original', {})
        crop_stats = cropping_stats.get('cropped', {})
        
        if orig_stats.get('point_count') and crop_stats.get('point_count'):
            print(f"   📊 Original points: {orig_stats['point_count']:,}")
            print(f"   📊 Cropped points: {crop_stats['point_count']:,}")
        
        if orig_stats.get('file_size_mb') and crop_stats.get('file_size_mb'):
            print(f"   📊 Size reduction: {orig_stats['file_size_mb']:.1f}MB → {crop_stats['file_size_mb']:.1f}MB")
    
    print()
    print("🎉 COMPLETE WORKFLOW FINISHED SUCCESSFULLY!")
    print()
    
    # Show file structure
    print("📁 OUTPUT FILE STRUCTURE")
    print("=" * 30)
    output_path = Path(output_dir)
    if output_path.exists():
        for root, dirs, files in os.walk(output_path):
            level = root.replace(str(output_path), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                if file.endswith(('.tif', '.png', '.json', '.geojson', '.laz')):
                    print(f"{subindent}{file}")
    
    return True

def demonstrate_individual_steps():
    """Demonstrate individual steps that can be run separately"""
    
    print("\n🔧 INDIVIDUAL STEP DEMONSTRATIONS")
    print("=" * 50)
    
    # Show individual function calls
    print("You can also run individual steps:")
    print()
    
    print("1️⃣ Just density analysis:")
    print("   analyze_laz_density(laz_file, output_dir, generate_mask=False)")
    print()
    
    print("2️⃣ Density + mask only:")
    print("   analyze_laz_density(laz_file, output_dir, generate_mask=True)")
    print()
    
    print("3️⃣ Density + mask + cleaning:")
    print("   analyze_laz_density(laz_file, output_dir, generate_mask=True, clean_existing_rasters=True)")
    print()
    
    print("4️⃣ Add polygon generation:")
    print("   analyze_laz_density(laz_file, output_dir, generate_mask=True, generate_polygon=True)")
    print()
    
    print("5️⃣ Complete workflow:")
    print("   analyze_laz_density(laz_file, output_dir, generate_mask=True,")
    print("                       clean_existing_rasters=True, generate_polygon=True,")
    print("                       crop_original_laz=True)")
    print()
    
    # Show modular usage
    print("🔧 MODULAR USAGE")
    print("-" * 30)
    print("Each step can also be used independently:")
    print()
    
    print("Vector operations:")
    print("   from app.processing.vector_operations import convert_mask_to_polygon")
    print("   result = convert_mask_to_polygon(mask_path, output_dir)")
    print()
    
    print("LAZ cropping:")
    print("   from app.processing.laz_cropping import crop_laz_with_polygon")
    print("   result = crop_laz_with_polygon(laz_path, polygon_path, output_dir)")
    print()
    
    print("Raster cleaning:")
    print("   from app.processing.raster_cleaning import RasterCleaner")
    print("   cleaner = RasterCleaner()")
    print("   result = cleaner.batch_clean_rasters(raster_dir, mask_path, output_dir)")

if __name__ == "__main__":
    print("🌟 COMPLETE LAZ PROCESSING WORKFLOW")
    print("=" * 60)
    print("This demo shows the full 5-step workflow:")
    print("1. Density Analysis")
    print("2. Binary Mask Generation")
    print("3. Raster Cleaning")
    print("4. Polygon Generation")
    print("5. LAZ Cropping")
    print()
    
    try:
        success = demo_complete_workflow()
        
        if success:
            demonstrate_individual_steps()
            print("\n🎊 DEMO COMPLETED SUCCESSFULLY!")
            print("The modular workflow is ready for production use!")
        else:
            print("\n⚠️  Demo encountered issues. Check the output above for details.")
            
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
