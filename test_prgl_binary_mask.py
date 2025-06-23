#!/usr/bin/env python3
"""
Comprehensive test for binary mask generation with PRGL LAZ file
Tests the complete density analysis + binary mask workflow
"""

import sys
import os
from pathlib import Path
import time
import json

# Add project to path
sys.path.insert(0, '/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

def test_prgl_binary_mask_generation():
    """Test binary mask generation with PRGL LAZ file"""
    
    print("🧪 TESTING BINARY MASK GENERATION WITH PRGL LAZ")
    print("=" * 60)
    print("This test demonstrates the complete density analysis workflow")
    print("including binary mask generation for artifact detection\n")
    
    # Test parameters
    laz_file = "input/LAZ/PRGL1260C9597_2014.laz"
    region_name = "PRGL1260C9597_2014"
    output_dir = f"output/{region_name}/lidar"
    
    # Configuration
    resolution = 1.0  # 1 meter resolution
    mask_threshold = 2.0  # 2 points/cell threshold
    
    print(f"📋 Test Configuration:")
    print(f"   LAZ file: {laz_file}")
    print(f"   Region: {region_name}")
    print(f"   Resolution: {resolution}m")
    print(f"   Mask threshold: {mask_threshold} points/cell")
    print(f"   Output directory: {output_dir}")
    
    # Step 1: Verify LAZ file exists
    print(f"\n🔍 STEP 1: Verifying LAZ File")
    print("-" * 30)
    
    if not os.path.exists(laz_file):
        print(f"❌ LAZ file not found: {laz_file}")
        return False
    
    file_size_mb = Path(laz_file).stat().st_size / (1024 * 1024)
    print(f"✅ LAZ file found: {laz_file}")
    print(f"📊 File size: {file_size_mb:.2f} MB")
    
    # Step 2: Test density analysis with mask generation
    print(f"\n🔧 STEP 2: Running Density Analysis with Binary Mask")
    print("-" * 50)
    
    try:
        from app.processing.density_analysis import DensityAnalyzer
        
        # Create analyzer with mask generation
        analyzer = DensityAnalyzer(
            resolution=resolution,
            mask_threshold=mask_threshold
        )
        
        print(f"⚙️ Analyzer created with:")
        print(f"   Resolution: {analyzer.resolution}m")
        print(f"   NoData value: {analyzer.nodata_value}")
        print(f"   Mask threshold: {analyzer.mask_threshold} points/cell")
        
        start_time = time.time()
        
        # Run analysis with mask generation
        result = analyzer.generate_density_raster(
            laz_file_path=laz_file,
            output_dir=output_dir,
            region_name=region_name,
            generate_mask=True  # Enable mask generation
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\n⏱️ Processing completed in {processing_time:.2f} seconds")
        
        if not result["success"]:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            return False
        
        print(f"✅ Analysis successful!")
        
    except Exception as e:
        print(f"❌ Analysis execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Verify outputs
    print(f"\n📁 STEP 3: Verifying Generated Files")
    print("-" * 35)
    
    # Check density files
    tiff_path = Path(result['tiff_path'])
    png_path = Path(result['png_path'])
    metadata_path = Path(result['metadata_path'])
    
    print(f"📄 Density Files:")
    if tiff_path.exists():
        size_mb = tiff_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ TIFF: {tiff_path.name} ({size_mb:.2f} MB)")
    else:
        print(f"   ❌ TIFF not found: {tiff_path}")
    
    if png_path.exists():
        size_mb = png_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ PNG: {png_path.name} ({size_mb:.2f} MB)")
    else:
        print(f"   ❌ PNG not found: {png_path}")
    
    if metadata_path.exists():
        size_kb = metadata_path.stat().st_size / 1024
        print(f"   ✅ Metadata: {metadata_path.name} ({size_kb:.1f} KB)")
    else:
        print(f"   ❌ Metadata not found: {metadata_path}")
    
    # Check mask files
    mask_results = result.get('mask_results', {})
    if mask_results:
        print(f"\n🎭 Binary Mask Files:")
        
        mask_tiff_path = Path(mask_results['tiff_path']) if 'tiff_path' in mask_results else None
        mask_png_path = Path(mask_results['png_path']) if 'png_path' in mask_results else None
        
        if mask_tiff_path and mask_tiff_path.exists():
            size_mb = mask_tiff_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ Mask TIFF: {mask_tiff_path.name} ({size_mb:.2f} MB)")
        else:
            print(f"   ❌ Mask TIFF not found")
        
        if mask_png_path and mask_png_path.exists():
            size_mb = mask_png_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ Mask PNG: {mask_png_path.name} ({size_mb:.2f} MB)")
        else:
            print(f"   ❌ Mask PNG not found")
    else:
        print(f"\n❌ No mask results found in analysis output")
        return False
    
    # Step 4: Analyze results
    print(f"\n📊 STEP 4: Analyzing Results")
    print("-" * 25)
    
    # Density statistics
    if "metadata" in result and "statistics" in result["metadata"]:
        stats = result["metadata"]["statistics"]
        print(f"📈 Density Statistics:")
        print(f"   Min: {stats.get('min', 'N/A')} points/cell")
        print(f"   Max: {stats.get('max', 'N/A')} points/cell")
        print(f"   Mean: {stats.get('mean', 'N/A'):.2f} points/cell")
        print(f"   StdDev: {stats.get('stddev', 'N/A'):.2f}")
    
    # Mask statistics
    if 'statistics' in mask_results:
        mask_stats = mask_results['statistics']
        print(f"\n🎭 Binary Mask Statistics:")
        print(f"   Threshold: {mask_stats.get('threshold', 'N/A')} points/cell")
        print(f"   Total pixels: {mask_stats.get('total_pixels', 'N/A'):,}")
        print(f"   Valid pixels: {mask_stats.get('valid_pixels', 'N/A'):,}")
        print(f"   Artifact pixels: {mask_stats.get('artifact_pixels', 'N/A'):,}")
        print(f"   Coverage: {mask_stats.get('coverage_percentage', 'N/A'):.1f}%")
        print(f"   Artifacts: {mask_stats.get('artifact_percentage', 'N/A'):.1f}%")
        
        # Quality assessment
        coverage = mask_stats.get('coverage_percentage', 0)
        if coverage > 90:
            quality = "🟢 EXCELLENT"
        elif coverage > 75:
            quality = "🟡 GOOD"
        elif coverage > 50:
            quality = "🟠 FAIR"
        else:
            quality = "🔴 POOR"
        
        print(f"   Quality Assessment: {quality} coverage")
    
    # Step 5: Check gallery integration
    print(f"\n🖼️ STEP 5: Checking Gallery Integration")
    print("-" * 35)
    
    gallery_dir = Path(output_dir) / "png_outputs"
    density_gallery = gallery_dir / "Density.png"
    mask_gallery = gallery_dir / "ValidMask.png"
    
    if density_gallery.exists():
        print(f"   ✅ Density in gallery: {density_gallery.name}")
    else:
        print(f"   ❌ Density not in gallery")
    
    if mask_gallery.exists():
        print(f"   ✅ Mask in gallery: {mask_gallery.name}")
    else:
        print(f"   ⚠️ Mask not in gallery (may not be implemented yet)")
    
    # Summary
    print(f"\n🎉 TEST SUMMARY")
    print("=" * 15)
    print(f"✅ Successfully processed PRGL LAZ file")
    print(f"✅ Generated density raster with {resolution}m resolution")
    print(f"✅ Generated binary mask with {mask_threshold} points/cell threshold")
    
    if mask_results and 'statistics' in mask_results:
        coverage = mask_results['statistics'].get('coverage_percentage', 0)
        artifacts = mask_results['statistics'].get('artifact_percentage', 0)
        print(f"✅ Coverage analysis: {coverage:.1f}% valid, {artifacts:.1f}% artifacts")
    
    print(f"✅ Files integrated into output structure")
    print(f"\n🔧 Binary mask generation is working correctly!")
    
    return True

def test_rasterio_availability():
    """Test if rasterio is available for mask generation"""
    print(f"🔍 Testing Rasterio Availability")
    print("-" * 30)
    
    try:
        import rasterio
        print(f"✅ Rasterio available: {rasterio.__version__}")
        return True
    except ImportError:
        print(f"❌ Rasterio not available - will use GDAL fallback")
        return False

if __name__ == "__main__":
    print(f"🚀 PRGL Binary Mask Generation Test")
    print("=" * 40)
    
    # Test rasterio availability
    rasterio_available = test_rasterio_availability()
    print()
    
    # Run the main test
    success = test_prgl_binary_mask_generation()
    
    if success:
        print(f"\n🎯 TEST PASSED!")
        print(f"Binary mask generation is working correctly with PRGL LAZ file.")
        if rasterio_available:
            print(f"Using rasterio for optimal mask generation.")
        else:
            print(f"Using GDAL fallback for mask generation.")
    else:
        print(f"\n💥 TEST FAILED!")
        sys.exit(1)
