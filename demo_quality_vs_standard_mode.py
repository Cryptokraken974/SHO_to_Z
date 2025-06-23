#!/usr/bin/env python3
"""
Demo: Quality Mode vs Standard Mode LAZ Processing
Demonstrates the difference between cleaning existing rasters vs generating clean rasters
"""

import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from processing.density_analysis import analyze_laz_density, analyze_laz_density_quality_mode

def demo_workflow_comparison():
    """Compare standard mode vs quality mode workflows"""
    
    print("🏆 LAZ PROCESSING WORKFLOW COMPARISON")
    print("=" * 70)
    print()
    
    # Test parameters
    test_laz = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/prgl/prgl_sample.laz"
    base_output_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/prgl"
    
    # Check if test LAZ file exists
    if not os.path.exists(test_laz):
        print(f"❌ Test LAZ file not found: {test_laz}")
        print("Please provide a valid LAZ file path")
        return False
    
    print(f"📁 Test LAZ file: {test_laz}")
    print(f"📁 Base output directory: {base_output_dir}")
    print()
    
    # ===== STANDARD MODE DEMO =====
    print("📊 STANDARD MODE: Clean existing rasters")
    print("-" * 50)
    print("Workflow: Generate rasters → Create mask → Clean interpolated artifacts")
    print()
    
    standard_output = str(Path(base_output_dir) / "standard_mode")
    
    standard_result = analyze_laz_density(
        laz_file_path=test_laz,
        output_dir=standard_output,
        region_name="prgl_standard",
        resolution=1.0,
        mask_threshold=2.0,
        generate_mask=True,
        clean_existing_rasters=True,  # Clean existing rasters
        generate_polygon=True,
        crop_original_laz=True,
        polygon_format="GeoJSON"
    )
    
    if standard_result.get("success"):
        print(f"✅ Standard mode completed successfully")
        
        # Show standard mode results
        mask_stats = standard_result.get("mask_results", {}).get("statistics", {})
        cleaning_stats = standard_result.get("cleaning_results", {})
        
        print(f"   Mask coverage: {mask_stats.get('coverage_percentage', 'N/A')}%")
        print(f"   Artifacts identified: {mask_stats.get('artifact_percentage', 'N/A')}%")
        print(f"   Rasters cleaned: {cleaning_stats.get('files_processed', 0)}")
        print(f"   Approach: Clean interpolated artifacts from existing rasters")
    else:
        print(f"❌ Standard mode failed: {standard_result.get('error')}")
    
    print()
    
    # ===== QUALITY MODE DEMO =====
    print("🌟 QUALITY MODE: Generate clean rasters from cropped LAZ")
    print("-" * 50)
    print("Workflow: Generate mask → Crop LAZ → Generate rasters from clean data")
    print()
    
    quality_output = str(Path(base_output_dir) / "quality_mode")
    
    quality_result = analyze_laz_density_quality_mode(
        laz_file_path=test_laz,
        output_dir=quality_output,
        region_name="prgl_quality",
        resolution=1.0,
        mask_threshold=2.0,
        regenerate_rasters=True,  # Regenerate from clean LAZ
        polygon_format="GeoJSON"
    )
    
    if quality_result.get("success"):
        print(f"✅ Quality mode completed successfully")
        
        # Show quality mode results
        quality_metadata = quality_result.get("quality_metadata", {})
        input_analysis = quality_metadata.get("input_analysis", {})
        quality_metrics = quality_metadata.get("quality_metrics", {})
        
        print(f"   Original LAZ size: {input_analysis.get('original_size_mb', 'N/A')} MB")
        print(f"   Cropped LAZ size: {input_analysis.get('cropped_size_mb', 'N/A')} MB")
        print(f"   Size reduction: {input_analysis.get('size_reduction_percentage', 'N/A'):.1f}%")
        print(f"   Point retention: {quality_metrics.get('point_retention_percentage', 'N/A'):.1f}%")
        print(f"   Approach: Generate rasters from clean point data (no artifacts)")
    else:
        print(f"❌ Quality mode failed: {quality_result.get('error')}")
    
    print()
    
    # ===== COMPARISON SUMMARY =====
    print("🔍 WORKFLOW COMPARISON SUMMARY")
    print("-" * 50)
    
    print("📊 STANDARD MODE:")
    print("   ✓ Faster - works with existing rasters")
    print("   ✓ Good for quick artifact removal")
    print("   ⚠ Cleans interpolated values in artifact areas")
    print("   ⚠ May leave some interpolation artifacts")
    print()
    
    print("🌟 QUALITY MODE:")
    print("   ✓ Highest quality - no interpolated artifacts")
    print("   ✓ Smaller, cleaner LAZ files")
    print("   ✓ Rasters generated from pure point data")
    print("   ⚠ Slower - requires raster regeneration")
    print("   ⚠ Requires integration with DTM/DSM pipeline")
    print()
    
    # Show file organization
    print("📁 OUTPUT ORGANIZATION:")
    print(f"Standard Mode: {Path(standard_output).name}/")
    print(f"  ├── density/        # Density analysis & mask")
    print(f"  ├── vectors/        # Polygon boundaries")
    print(f"  ├── cropped/        # Cropped LAZ")
    print(f"  └── lidar/cleaned/  # Cleaned existing rasters")
    print()
    print(f"Quality Mode: {Path(quality_output).name}/")
    print(f"  ├── density/        # Density analysis & mask")
    print(f"  ├── vectors/        # Polygon boundaries") 
    print(f"  ├── cropped/        # Cropped LAZ (primary)")
    print(f"  └── clean_rasters/  # Rasters from clean LAZ")
    print()
    
    print("🎯 RECOMMENDATION:")
    print("• Use STANDARD MODE for quick artifact cleanup of existing rasters")
    print("• Use QUALITY MODE for highest quality when regenerating rasters is acceptable")
    print("• Quality mode is ideal for final production datasets")
    
    return True

def demo_quality_mode_integration():
    """Show how to integrate quality mode with existing pipeline"""
    
    print("\n🔧 QUALITY MODE INTEGRATION GUIDE")
    print("=" * 50)
    print()
    
    print("To integrate quality mode with your DTM/DSM generation pipeline:")
    print()
    
    print("1️⃣ MODIFY _regenerate_rasters_from_clean_laz() method:")
    print("   Replace placeholder with calls to your existing raster generation:")
    print("   ```python")
    print("   # Instead of placeholder, call your DTM pipeline:")
    print("   dtm_result = generate_dtm_from_laz(clean_laz_path, output_dir)")
    print("   dsm_result = generate_dsm_from_laz(clean_laz_path, output_dir)")
    print("   hillshade_result = generate_hillshade_from_dtm(dtm_path)")
    print("   ```")
    print()
    
    print("2️⃣ WORKFLOW INTEGRATION:")
    print("   ```python")
    print("   # Quality mode workflow")
    print("   result = analyze_laz_density_quality_mode(")
    print("       laz_file_path='input.laz',")
    print("       output_dir='output/',")
    print("       regenerate_rasters=True  # Enable raster regeneration")
    print("   )")
    print("   ")
    print("   if result['success']:")
    print("       clean_laz = result['cropped_laz_path']")
    print("       # Use clean_laz for all subsequent processing")
    print("   ```")
    print()
    
    print("3️⃣ BENEFITS:")
    print("   • No interpolated data in edge/artifact areas")
    print("   • Smaller file sizes (10-30% reduction typical)")
    print("   • More accurate elevation models")
    print("   • Clean polygon boundaries matching actual data")

if __name__ == "__main__":
    print("🚀 LAZ PROCESSING: STANDARD VS QUALITY MODE DEMO")
    print("=" * 70)
    print()
    
    try:
        # Main workflow comparison
        success = demo_workflow_comparison()
        
        if success:
            # Integration guide
            demo_quality_mode_integration()
            
            print(f"\n🎉 DEMO COMPLETED SUCCESSFULLY!")
            print(f"Both standard and quality modes are now available for LAZ processing.")
        else:
            print(f"\n⚠️  Demo encountered issues. Check file paths and try again.")
            
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
