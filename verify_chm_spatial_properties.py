#!/usr/bin/env python3
"""
Quick verification of DTM and DSM spatial properties for CHM calculation
"""

import rasterio
from pathlib import Path

def analyze_spatial_properties():
    """Analyze DTM and DSM spatial properties for Box_Regions_6"""
    
    print("📊 Box_Regions_6 DTM vs DSM Spatial Analysis")
    print("=" * 50)
    
    base_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z")
    
    # File paths
    dtm_path = base_path / "input/Box_Regions_6/3.787S_63.734W_elevation/Original/3.787S_63.734W_elevation.tiff"
    dsm_path = base_path / "output/Box_Regions_6/lidar/DSM/Box_Regions_6_copernicus_dsm_30m.tif"
    
    files = [
        ("DTM", dtm_path),
        ("DSM", dsm_path)
    ]
    
    for name, file_path in files:
        print(f"\n🔍 {name}: {file_path.name}")
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue
            
        try:
            with rasterio.open(str(file_path)) as src:
                print(f"   📐 Dimensions: {src.width}x{src.height}")
                print(f"   🗺️ CRS: {src.crs}")
                print(f"   📏 Resolution: {src.res[0]:.6f} x {src.res[1]:.6f}")
                print(f"   📍 Bounds:")
                print(f"      West: {src.bounds.left:.6f}")
                print(f"      East: {src.bounds.right:.6f}")
                print(f"      South: {src.bounds.bottom:.6f}")
                print(f"      North: {src.bounds.top:.6f}")
                print(f"   📦 Extent: {src.bounds.right - src.bounds.left:.6f} x {src.bounds.top - src.bounds.bottom:.6f}")
                
        except Exception as e:
            print(f"❌ Error reading {name}: {e}")
    
    print(f"\n🎯 CHM CALCULATION ANALYSIS:")
    
    # Check if files exist and can be compared
    if dtm_path.exists() and dsm_path.exists():
        try:
            with rasterio.open(str(dtm_path)) as dtm_src, rasterio.open(str(dsm_path)) as dsm_src:
                
                # Check spatial compatibility
                print(f"   📐 Dimension match: {dtm_src.width == dsm_src.width and dtm_src.height == dsm_src.height}")
                print(f"   🗺️ CRS match: {dtm_src.crs == dsm_src.crs}")
                print(f"   📏 Resolution match: {abs(dtm_src.res[0] - dsm_src.res[0]) < 1e-6}")
                
                # Check spatial overlap
                dtm_bounds = dtm_src.bounds
                dsm_bounds = dsm_src.bounds
                
                dtm_within_dsm = (dtm_bounds.left >= dsm_bounds.left and 
                                 dtm_bounds.right <= dsm_bounds.right and
                                 dtm_bounds.bottom >= dsm_bounds.bottom and
                                 dtm_bounds.top <= dsm_bounds.top)
                
                print(f"   📍 DTM within DSM bounds: {dtm_within_dsm}")
                
                if dtm_within_dsm:
                    print(f"   ✅ OPTIMAL: Can crop DSM to DTM extent")
                    print(f"   🎯 Strategy: Crop DSM ({dsm_src.width}x{dsm_src.height}) → DTM extent ({dtm_src.width}x{dtm_src.height})")
                else:
                    print(f"   ⚠️ COMPLEX: Spatial overlap issues detected")
                    print(f"   🔧 Strategy: Resampling required")
                
        except Exception as e:
            print(f"❌ Error comparing files: {e}")
    
    print(f"\n💡 CONCLUSION:")
    print(f"The CHM spatial alignment fix should:")
    print(f"1. Detect DTM is subset of DSM with same resolution")
    print(f"2. Crop DSM to DTM extent (preserves DTM quality)")
    print(f"3. Calculate CHM = DSM_cropped - DTM")
    print(f"4. Result: CHM with DTM dimensions (no black squares)")

if __name__ == "__main__":
    analyze_spatial_properties()
