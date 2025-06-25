#!/usr/bin/env python3
"""
Regenerate TintOverlay with new archaeological gentle color scheme for Box_Regions_4
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from processing.tiff_processing import create_tint_overlay
from processing.color_relief import create_color_table
import numpy as np
from osgeo import gdal
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


def generate_color_relief_with_new_ramp(dtm_path: str, output_path: str):
    """Generate color relief using the new archaeological_gentle ramp"""
    print(f"🎨 Generating color relief with archaeological_gentle ramp...")
    print(f"   📥 Input DTM: {dtm_path}")
    print(f"   📤 Output: {output_path}")
    
    try:
        # Read DTM to get elevation data
        ds = gdal.Open(dtm_path)
        if ds is None:
            raise FileNotFoundError(f"Cannot open DTM: {dtm_path}")
        
        band = ds.GetRasterBand(1)
        elevation = band.ReadAsArray().astype(np.float32)
        geo = ds.GetGeoTransform()
        proj = ds.GetProjection()
        
        # Get elevation statistics
        nodata = band.GetNoDataValue()
        if nodata is not None:
            valid_mask = elevation != nodata
            elevation[~valid_mask] = np.nan
        
        elev_min, elev_max = np.nanmin(elevation), np.nanmax(elevation)
        print(f"   📊 Elevation range: {elev_min:.2f} to {elev_max:.2f}")
        
        # Normalize elevation to 0-1 range
        elev_norm = (elevation - elev_min) / (elev_max - elev_min)
        
        # 🟣 New archaeological gentle color ramp with 5 soft color bands
        colors = [
            '#FFFADC',  # Pale cream/yellow (lowest elevation)
            '#FFE4B5',  # Soft peach/orange  
            '#FFC098',  # Gentle salmon
            '#FFA07A',  # Soft coral/light red
            '#FF8C69'   # Warm light red (highest elevation)
        ]
        
        # Create colormap
        n_bins = 256
        cmap = LinearSegmentedColormap.from_list('archaeological_gentle', colors, N=n_bins)
        
        # Apply colormap
        rgb_array = cmap(elev_norm)[:, :, :3]  # Remove alpha channel
        rgb_array = (rgb_array * 255).astype(np.uint8)
        
        # Handle NaN values (set to black)
        nan_mask = np.isnan(elev_norm)
        if np.any(nan_mask):
            rgb_array[nan_mask] = [0, 0, 0]
        
        # Save as 3-band GeoTIFF
        driver = gdal.GetDriverByName('GTiff')
        h, w = elevation.shape
        out_ds = driver.Create(output_path, w, h, 3, gdal.GDT_Byte)
        out_ds.SetGeoTransform(geo)
        out_ds.SetProjection(proj)
        
        for i in range(3):
            out_band = out_ds.GetRasterBand(i + 1)
            out_band.WriteArray(rgb_array[:, :, i])
            out_band.FlushCache()
        
        out_ds = None
        ds = None
        
        print(f"✅ Color relief generated with archaeological_gentle ramp")
        return True
        
    except Exception as e:
        print(f"❌ Color relief generation failed: {e}")
        return False


async def regenerate_box_regions_4_tint_overlay():
    """Regenerate TintOverlay for Box_Regions_4 with new archaeological gentle color scheme"""
    
    region_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/Box_Regions_4"
    lidar_path = os.path.join(region_path, "lidar")
    
    print("🟣 REGENERATING BOX_REGIONS_4 TINT OVERLAY")
    print("=" * 60)
    print(f"📁 Region path: {region_path}")
    
    # Check if region exists
    if not os.path.exists(region_path):
        print(f"❌ Region not found: {region_path}")
        return False
    
    # Look for existing DTM file
    dtm_paths = []
    for root, dirs, files in os.walk(lidar_path):
        for file in files:
            if file.endswith('.tif') and any(keyword in file.lower() for keyword in ['dtm', 'elevation']):
                dtm_paths.append(os.path.join(root, file))
    
    if not dtm_paths:
        print("❌ No DTM file found - cannot regenerate without elevation data")
        print("   Looking for files containing 'dtm' or 'elevation' in:")
        for root, dirs, files in os.walk(lidar_path):
            for file in files:
                if file.endswith('.tif'):
                    print(f"   Found: {os.path.join(root, file)}")
        return False
    
    # Use the first DTM found
    dtm_path = dtm_paths[0]
    print(f"📊 Using DTM: {os.path.basename(dtm_path)}")
    
    # Look for existing hillshade
    hillshade_paths = []
    for root, dirs, files in os.walk(lidar_path):
        for file in files:
            if file.endswith('.tif') and 'hillshade' in file.lower():
                hillshade_paths.append(os.path.join(root, file))
    
    if not hillshade_paths:
        print("❌ No hillshade file found - cannot create tint overlay without hillshade")
        return False
    
    hillshade_path = hillshade_paths[0]
    print(f"🌄 Using hillshade: {os.path.basename(hillshade_path)}")
    
    # Generate new color relief with archaeological_gentle ramp
    color_relief_dir = os.path.join(lidar_path, "Color_Relief")
    os.makedirs(color_relief_dir, exist_ok=True)
    color_relief_path = os.path.join(color_relief_dir, "archaeological_gentle_color_relief.tif")
    
    if not generate_color_relief_with_new_ramp(dtm_path, color_relief_path):
        return False
    
    # Generate new TintOverlay
    png_outputs_dir = os.path.join(lidar_path, "png_outputs")
    os.makedirs(png_outputs_dir, exist_ok=True)
    tint_overlay_path = os.path.join(png_outputs_dir, "TintOverlay.png")
    
    print(f"🎭 Creating new TintOverlay...")
    print(f"   🎨 Color relief: {os.path.basename(color_relief_path)}")
    print(f"   🌄 Hillshade: {os.path.basename(hillshade_path)}")
    print(f"   📤 Output: {tint_overlay_path}")
    
    # Create tint overlay as TIFF first
    tint_overlay_tiff = os.path.join(png_outputs_dir, "TintOverlay.tif")
    
    try:
        result = await create_tint_overlay(color_relief_path, hillshade_path, tint_overlay_tiff)
        
        if result.get('status') == 'success':
            # Convert TIFF to PNG for web display
            from processing.convert import save_enhanced_png
            
            # Read the tint overlay TIFF
            ds = gdal.Open(tint_overlay_tiff)
            if ds is not None:
                rgb_data = ds.ReadAsArray()
                if rgb_data.ndim == 3:
                    # Convert from (bands, height, width) to (height, width, bands)
                    rgb_data = np.transpose(rgb_data, (1, 2, 0))
                
                # Save as PNG
                plt.figure(figsize=(10, 10), dpi=150)
                plt.imshow(rgb_data)
                plt.axis('off')
                plt.savefig(tint_overlay_path, bbox_inches='tight', pad_inches=0, dpi=150)
                plt.close()
                
                ds = None
                
                print(f"✅ New TintOverlay created successfully!")
                print(f"📁 Location: {tint_overlay_path}")
                
                # Backup old TintOverlay if it exists
                if os.path.exists(tint_overlay_path + ".backup"):
                    os.remove(tint_overlay_path + ".backup")
                
                return True
            else:
                print(f"❌ Failed to read generated tint overlay TIFF")
                return False
        else:
            print(f"❌ Tint overlay creation failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating tint overlay: {e}")
        return False


async def main():
    """Main function"""
    print("🔄 TINT OVERLAY REGENERATION WITH ARCHAEOLOGICAL GENTLE COLOR SCHEME")
    print("=" * 80)
    
    success = await regenerate_box_regions_4_tint_overlay()
    
    if success:
        print("\n🎉 REGENERATION COMPLETE!")
        print("✅ Box_Regions_4 now uses the new archaeological gentle color scheme")
        print("🎨 The TintOverlay should now show:")
        print("   • Pale cream/yellow for lowest elevations")
        print("   • Soft peach/orange for low-medium elevations") 
        print("   • Gentle salmon for medium elevations")
        print("   • Soft coral/light red for medium-high elevations")
        print("   • Warm light red for highest elevations")
        print("\n🔍 You can verify the new colors by running:")
        print("   python analyze_tint_overlay_colors.py")
    else:
        print("\n❌ REGENERATION FAILED")
        print("Please check the error messages above")


if __name__ == "__main__":
    asyncio.run(main())
