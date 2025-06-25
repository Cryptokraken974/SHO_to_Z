#!/usr/bin/env python3
"""
Test proper CHM generation using SRTM DSM and DTM
This directly tests the fixed CHM processing without needing the API server
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

async def test_proper_chm_generation():
    """Test CHM generation with SRTM DSM and DTM"""
    
    print("🌳 TESTING PROPER CHM GENERATION")
    print("="*60)
    
    region_name = "Box_Regions_7"
    
    # Check available files
    region_dir = Path("output") / region_name / "lidar"
    
    # Check for SRTM DSM (downloaded earlier)
    srtm_dsm_dir = region_dir / "DSM"
    srtm_files = list(srtm_dsm_dir.glob("*srtm*dsm*.tif")) if srtm_dsm_dir.exists() else []
    
    # Check for DTM (existing elevation data)
    input_region_dir = Path("input") / region_name
    dtm_files = []
    
    if input_region_dir.exists():
        elevation_dirs = list(input_region_dir.glob("*_elevation"))
        for elev_dir in elevation_dirs:
            original_dir = elev_dir / "Original"
            if original_dir.exists():
                elevation_files = list(original_dir.glob("*.tiff")) + list(original_dir.glob("*.tif"))
                if elevation_files:
                    dtm_files.extend(elevation_files)
                    break
    
    print(f"📁 Region: {region_name}")
    print(f"🌲 SRTM DSM files found: {len(srtm_files)}")
    if srtm_files:
        print(f"   📄 {srtm_files[0]}")
        
    print(f"🏔️ DTM files found: {len(dtm_files)}")
    if dtm_files:
        print(f"   📄 {dtm_files[0]}")
    
    if not srtm_files:
        print("❌ No SRTM DSM files found. Please download SRTM DSM first.")
        return
        
    if not dtm_files:
        print("❌ No DTM files found. Please download elevation data first.")
        return
    
    # Test CHM processing with proper sources
    print(f"\n🔄 Testing CHM processing...")
    print(f"   DSM Source: SRTM GL1 (surface elevation)")
    print(f"   DTM Source: Elevation data (terrain)")
    
    try:
        from app.processing.tiff_processing import process_chm_tiff
        
        # Create CHM output directory
        chm_dir = region_dir / "CHM"
        chm_dir.mkdir(parents=True, exist_ok=True)
        
        # Parameters for CHM processing
        chm_parameters = {
            "dsm_path": str(srtm_files[0]),
            "output_filename": f"{region_name}_proper_CHM.tif"
        }
        
        print(f"🚀 Starting CHM calculation...")
        result = await process_chm_tiff(str(dtm_files[0]), str(chm_dir), chm_parameters)
        
        if result.get("status") == "success":
            print(f"✅ CHM processing completed successfully!")
            print(f"📁 Output file: {result.get('output_file')}")
            print(f"⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
            
            # Display statistics
            stats = result.get("statistics", {})
            if stats:
                print(f"\n📊 CHM STATISTICS:")
                print(f"   Min height: {stats.get('min_height', 'N/A')}m")
                print(f"   Max height: {stats.get('max_height', 'N/A')}m")
                print(f"   Mean height: {stats.get('mean_height', 'N/A')}m")
                print(f"   Std dev: {stats.get('std_height', 'N/A')}m")
            
            # Check for data quality warnings
            warning = result.get("data_quality_warning")
            if warning:
                print(f"\n⚠️ DATA QUALITY WARNING:")
                print(f"   {warning}")
            else:
                print(f"\n✅ NO DATA QUALITY ISSUES DETECTED!")
                print(f"   Proper CHM calculation successful with SRTM DSM")
            
            # Analyze the result
            if stats and stats.get('max_height', 0) > 0.1:
                print(f"\n🎉 SUCCESS: CHM shows vegetation height variation!")
                print(f"   This confirms SRTM DSM includes surface features")
                print(f"   The CHM now properly represents canopy heights")
            else:
                print(f"\n⚠️ CHM still shows minimal variation")
                print(f"   This may indicate spatial misalignment or other issues")
        else:
            print(f"❌ CHM processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during CHM processing: {e}")
        import traceback
        traceback.print_exc()

async def analyze_data_sources():
    """Analyze the spatial properties of SRTM DSM vs DTM"""
    
    print(f"\n\n🔍 ANALYZING DATA SOURCE PROPERTIES")
    print("="*60)
    
    try:
        import rasterio
        import numpy as np
        
        region_name = "Box_Regions_7"
        region_dir = Path("output") / region_name / "lidar"
        
        # SRTM DSM
        srtm_dsm_files = list((region_dir / "DSM").glob("*srtm*dsm*.tif"))
        
        # DTM
        input_region_dir = Path("input") / region_name
        dtm_files = []
        if input_region_dir.exists():
            elevation_dirs = list(input_region_dir.glob("*_elevation"))
            for elev_dir in elevation_dirs:
                original_dir = elev_dir / "Original"
                if original_dir.exists():
                    elevation_files = list(original_dir.glob("*.tiff")) + list(original_dir.glob("*.tif"))
                    if elevation_files:
                        dtm_files.extend(elevation_files)
                        break
        
        if srtm_dsm_files and dtm_files:
            print(f"📊 Comparing SRTM DSM vs DTM data...")
            
            # Read SRTM DSM
            with rasterio.open(srtm_dsm_files[0]) as srtm_src:
                srtm_data = srtm_src.read(1)
                srtm_valid = srtm_data[~np.isnan(srtm_data) & (srtm_data != srtm_src.nodata)]
                
                print(f"\n🌲 SRTM DSM (Surface Elevation):")
                print(f"   Shape: {srtm_data.shape}")
                print(f"   Valid pixels: {len(srtm_valid):,}")
                if len(srtm_valid) > 0:
                    print(f"   Range: {np.min(srtm_valid):.2f} to {np.max(srtm_valid):.2f}m")
                    print(f"   Mean: {np.mean(srtm_valid):.2f}m")
                    print(f"   Std: {np.std(srtm_valid):.2f}m")
                
            # Read DTM
            with rasterio.open(dtm_files[0]) as dtm_src:
                dtm_data = dtm_src.read(1)
                dtm_valid = dtm_data[~np.isnan(dtm_data) & (dtm_data != dtm_src.nodata)]
                
                print(f"\n🏔️ DTM (Terrain Elevation):")
                print(f"   Shape: {dtm_data.shape}")
                print(f"   Valid pixels: {len(dtm_valid):,}")
                if len(dtm_valid) > 0:
                    print(f"   Range: {np.min(dtm_valid):.2f} to {np.max(dtm_valid):.2f}m")
                    print(f"   Mean: {np.mean(dtm_valid):.2f}m")
                    print(f"   Std: {np.std(dtm_valid):.2f}m")
            
            # Compare elevation ranges
            if len(srtm_valid) > 0 and len(dtm_valid) > 0:
                print(f"\n📈 COMPARISON:")
                print(f"   SRTM range: {np.max(srtm_valid) - np.min(srtm_valid):.2f}m")
                print(f"   DTM range: {np.max(dtm_valid) - np.min(dtm_valid):.2f}m")
                print(f"   Mean difference: {np.mean(srtm_valid) - np.mean(dtm_valid):.2f}m")
                
                # Check if they're different (proper for CHM)
                if abs(np.mean(srtm_valid) - np.mean(dtm_valid)) > 0.5:
                    print(f"   ✅ SRTM and DTM show different elevation patterns (good for CHM)")
                else:
                    print(f"   ⚠️ SRTM and DTM have similar elevations (may indicate spatial issues)")
        
    except Exception as e:
        print(f"❌ Error analyzing data sources: {e}")

if __name__ == "__main__":
    asyncio.run(test_proper_chm_generation())
    asyncio.run(analyze_data_sources())
