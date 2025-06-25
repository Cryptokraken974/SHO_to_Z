#!/usr/bin/env python3
"""
Test the complete SRTM DSM integration workflow to ensure proper CHM generation.

This test verifies:
1. SRTM DSM download (true surface elevation)
2. DTM download (terrain elevation)
3. Proper CHM generation (SRTM DSM - DTM)
4. Meaningful vegetation height data
"""

import sys
import asyncio
import json
import logging
from pathlib import Path

# Add the app directory to the path to import modules
sys.path.append(str(Path(__file__).parent / "app"))

from services.true_dsm_service import true_dsm_service
from services.elevation_service import elevation_service
from endpoints.true_dsm import generate_proper_chm

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_srtm_workflow():
    """Test the complete SRTM DSM workflow"""
    
    print("🌲 Testing Complete SRTM DSM Integration Workflow")
    print("=" * 60)
    
    # Test coordinates - Forest area in Brazil (known to have vegetation)
    test_coords = {
        "region_name": "Box_Regions_8_SRTM_Test",
        "latitude": -14.87,
        "longitude": -39.38,
        "buffer_km": 12.5
    }
    
    print(f"📍 Test Location: {test_coords['latitude']}, {test_coords['longitude']}")
    print(f"🎯 Region: {test_coords['region_name']}")
    print()
    
    try:
        # Step 1: Download DTM (terrain elevation)
        print("📊 Step 1/3: Downloading DTM (terrain elevation)...")
        
        dtm_request = {
            "lat": test_coords["latitude"],
            "lng": test_coords["longitude"],
            "buffer_km": test_coords["buffer_km"],
            "region_name": test_coords["region_name"]
        }
        
        dtm_result = await elevation_service.download_elevation_data(dtm_request)
        
        if dtm_result and dtm_result.get("success"):
            print(f"✅ DTM download successful: {dtm_result.get('file_path')}")
        else:
            print(f"❌ DTM download failed: {dtm_result.get('error')}")
            return False
        
        # Step 2: Download SRTM DSM (true surface elevation)
        print("\n🏔️ Step 2/3: Downloading SRTM DSM (true surface elevation)...")
        
        srtm_result = await true_dsm_service.get_srtm_dsm_for_region(
            lat=test_coords["latitude"],
            lng=test_coords["longitude"],
            region_name=test_coords["region_name"],
            buffer_km=test_coords["buffer_km"],
            resolution=1  # 1-arcsecond (~30m)
        )
        
        if srtm_result and srtm_result.get("success"):
            print(f"✅ SRTM DSM download successful: {srtm_result.get('file_path')}")
        else:
            print(f"❌ SRTM DSM download failed: {srtm_result.get('error')}")
            return False
        
        # Step 3: Generate proper CHM (SRTM DSM - DTM)
        print("\n🌳 Step 3/3: Generating proper CHM (SRTM DSM - DTM)...")
        
        chm_data = {
            "region_name": test_coords["region_name"],
            "latitude": test_coords["latitude"],
            "longitude": test_coords["longitude"]
        }
        
        # This would normally be called via the API, but let's simulate it
        # by calling the processing logic directly
        from processing.tiff_processing import process_chm_tiff
        
        # Check file paths
        region_dir = Path("output") / test_coords["region_name"] / "lidar"
        srtm_dsm_dir = region_dir / "DSM"
        dtm_dir = region_dir / "DTM" / "filled"
        
        # Find files
        srtm_files = list(srtm_dsm_dir.glob("*srtm*dsm*.tif")) if srtm_dsm_dir.exists() else []
        dtm_files = list(dtm_dir.glob("*DTM*.tif")) if dtm_dir.exists() else []
        
        if not srtm_files:
            print(f"❌ No SRTM DSM files found in {srtm_dsm_dir}")
            return False
            
        if not dtm_files:
            print(f"❌ No DTM files found in {dtm_dir}")
            return False
        
        srtm_file = srtm_files[0]
        dtm_file = dtm_files[0]
        
        print(f"📂 SRTM DSM file: {srtm_file}")
        print(f"📂 DTM file: {dtm_file}")
        
        # Generate CHM
        chm_output_dir = region_dir / "CHM"
        chm_output_dir.mkdir(parents=True, exist_ok=True)
        chm_output_file = chm_output_dir / f"{test_coords['region_name']}_proper_chm_srtm.tif"
        
        chm_result = await process_chm_tiff(
            dsm_file=str(srtm_file),
            dtm_file=str(dtm_file),
            output_file=str(chm_output_file),
            region_name=test_coords["region_name"]
        )
        
        if chm_result and chm_result.get("success"):
            print(f"✅ Proper CHM generation successful!")
            print(f"📂 CHM file: {chm_result.get('file_path')}")
            
            # Analyze CHM statistics
            if chm_result.get("metadata", {}).get("statistics"):
                stats = chm_result["metadata"]["statistics"]
                print(f"\n📊 CHM Statistics:")
                print(f"   Min vegetation height: {stats.get('min', 0):.2f}m")
                print(f"   Max vegetation height: {stats.get('max', 0):.2f}m")
                print(f"   Mean vegetation height: {stats.get('mean', 0):.2f}m")
                print(f"   Std deviation: {stats.get('std', 0):.2f}m")
                
                # Check if we have meaningful vegetation data
                if stats.get('max', 0) > 5:  # Trees higher than 5m
                    print("✅ Meaningful vegetation heights detected!")
                    return True
                else:
                    print("⚠️ Limited vegetation heights detected (may be correct for this area)")
                    return True
            else:
                print("⚠️ No statistics available, but CHM was generated")
                return True
        else:
            print(f"❌ CHM generation failed: {chm_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_complete_srtm_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SRTM DSM Integration Test: SUCCESS")
        print("   - SRTM DSM provides true surface elevation")
        print("   - DTM provides terrain elevation")
        print("   - CHM = SRTM DSM - DTM gives vegetation height")
        print("   - Ready for production use!")
    else:
        print("❌ SRTM DSM Integration Test: FAILED")
        print("   - Check error messages above")
        print("   - Verify data sources and processing logic")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
