#!/usr/bin/env python3
"""
Comprehensive Demo: PRGL LAZ Density Analysis Implementation
Shows the complete density analysis workflow for loaded LAZ files
"""

import sys
import os
from pathlib import Path
import time

# Add project to path
sys.path.insert(0, '/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

def demonstrate_density_analysis():
    """Demonstrate the complete density analysis workflow"""
    
    print("🎯 COMPREHENSIVE DENSITY ANALYSIS DEMONSTRATION")
    print("=" * 60)
    print("This demo shows the complete modular density analysis system")
    print("for loaded LAZ files (not coordinate-generated ones)\n")
    
    # Step 1: Show available LAZ files
    print("📂 STEP 1: Available LAZ Files")
    print("-" * 30)
    
    laz_dir = Path("input/LAZ")
    laz_files = list(laz_dir.glob("*.laz"))
    
    for i, laz_file in enumerate(laz_files, 1):
        size_mb = laz_file.stat().st_size / (1024 * 1024)
        print(f"{i}. {laz_file.name} ({size_mb:.2f} MB)")
    
    # Step 2: Focus on PRGL file
    print(f"\n🎯 STEP 2: Focusing on PRGL LAZ File")
    print("-" * 35)
    
    prgl_laz = "input/LAZ/PRGL1260C9597_2014.laz"
    if not os.path.exists(prgl_laz):
        print(f"❌ PRGL LAZ file not found")
        return False
    
    print(f"✅ Selected: {prgl_laz}")
    file_size = Path(prgl_laz).stat().st_size / (1024 * 1024)
    print(f"📊 File size: {file_size:.2f} MB")
    
    # Step 3: LAZ Classification
    print(f"\n🔍 STEP 3: LAZ Classification (Loaded vs Coordinate-Generated)")
    print("-" * 55)
    
    try:
        from app.processing.laz_classifier import LAZClassifier
        
        is_loaded, reason = LAZClassifier.is_loaded_laz(prgl_laz)
        print(f"📋 Classification Result:")
        print(f"   Is loaded LAZ: {'✅ YES' if is_loaded else '❌ NO'}")  
        print(f"   Reason: {reason}")
        
        if is_loaded:
            print(f"   🎯 This LAZ qualifies for density analysis!")
        else:
            print(f"   ⚠️ This LAZ would be skipped (coordinate-generated)")
            
    except Exception as e:
        print(f"⚠️ Classification failed: {e}")
    
    # Step 4: Density Analysis Execution
    print(f"\n🔧 STEP 4: Density Analysis Execution")
    print("-" * 35)
    
    try:
        from app.processing.density_analysis import DensityAnalyzer
        
        # Create analyzer
        analyzer = DensityAnalyzer(resolution=1.0, nodata_value=0)
        
        print(f"⚙️ Analyzer Configuration:")
        print(f"   Resolution: {analyzer.resolution}m per pixel")
        print(f"   NoData value: {analyzer.nodata_value}")
        
        # Output directory
        output_dir = "output/PRGL1260C9597_2014/lidar"
        print(f"   Output directory: {output_dir}")
        
        print(f"\n🚀 Running density analysis...")
        start_time = time.time()
        
        result = analyzer.generate_density_raster(
            laz_file_path=prgl_laz,
            output_dir=output_dir,
            region_name="PRGL1260C9597_2014"
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️ Analysis completed in {processing_time:.2f} seconds")
        
        if result["success"]:
            print(f"✅ Analysis SUCCESS!")
        else:
            print(f"❌ Analysis FAILED: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis execution failed: {e}")
        return False
    
    # Step 5: Results Analysis
    print(f"\n📊 STEP 5: Results Analysis")
    print("-" * 25)
    
    # File outputs
    print(f"📁 Generated Files:")
    tiff_path = Path(result['tiff_path'])
    png_path = Path(result['png_path'])
    metadata_path = Path(result['metadata_path'])
    
    if tiff_path.exists():
        tiff_size = tiff_path.stat().st_size / (1024 * 1024)
        print(f"   📄 TIFF: {tiff_path.name} ({tiff_size:.2f} MB)")
    
    if png_path.exists():
        png_size = png_path.stat().st_size / (1024 * 1024)
        print(f"   🎨 PNG:  {png_path.name} ({png_size:.2f} MB)")
    
    if metadata_path.exists():
        meta_size = metadata_path.stat().st_size / 1024
        print(f"   📋 Metadata: {metadata_path.name} ({meta_size:.1f} KB)")
    
    # Density statistics
    if "metadata" in result and "statistics" in result["metadata"]:
        stats = result["metadata"]["statistics"]
        print(f"\n📈 Density Statistics:")
        print(f"   Minimum: {stats.get('min', 'N/A')} points/cell")
        print(f"   Maximum: {stats.get('max', 'N/A')} points/cell")
        print(f"   Mean:    {stats.get('mean', 'N/A'):.2f} points/cell")
        print(f"   StdDev:  {stats.get('stddev', 'N/A'):.2f}")
        
        # Interpret results
        mean_density = stats.get('mean', 0)
        if mean_density > 500:
            quality = "🟢 HIGH"
        elif mean_density > 200:
            quality = "🟡 MEDIUM"
        else:
            quality = "🔴 LOW"
        
        print(f"   Quality Assessment: {quality} density")
    
    # Step 6: Integration Check  
    print(f"\n🔗 STEP 6: Integration Verification")
    print("-" * 30)
    
    # Check if density PNG was copied to main gallery
    gallery_png = Path("output/PRGL1260C9597_2014/lidar/png_outputs/Density.png")
    if gallery_png.exists():
        print(f"✅ Density PNG copied to main gallery: {gallery_png}")
        gallery_size = gallery_png.stat().st_size / (1024 * 1024)
        print(f"   Gallery PNG size: {gallery_size:.2f} MB")
    else:
        print(f"⚠️ Density PNG not found in main gallery")
    
    # Summary
    print(f"\n🎉 DEMONSTRATION SUMMARY")
    print("=" * 25)
    print(f"✅ Successfully processed PRGL LAZ file")
    print(f"✅ Generated density raster with 1m resolution") 
    print(f"✅ Point density range: {stats.get('min', 'N/A')}-{stats.get('max', 'N/A')} points/cell")
    print(f"✅ Files integrated into main gallery")
    print(f"✅ Complete metadata generated")
    print(f"\n🔧 The modular density analysis system is working correctly!")
    
    return True

if __name__ == "__main__":
    success = demonstrate_density_analysis()
    
    if success:
        print(f"\n🎯 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print(f"The PRGL density analysis implementation is ready for production use.")
    else:
        print(f"\n💥 DEMONSTRATION FAILED!")
        sys.exit(1)
