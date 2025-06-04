# image_utils.py
import rasterio

def get_image_bounds(tif_path: str):
    with rasterio.open(tif_path) as src:
        bounds = src.bounds
        return [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]


# colorize_dem.py
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from PIL import Image
import os

def colorize_dem(tif_path: str, output_path: str, colormap='terrain', enhanced_resolution: bool = True):
    """
    Generate colorized DEM visualization with enhanced quality options
    
    Args:
        tif_path: Path to input elevation TIFF
        output_path: Path for output colorized PNG
        colormap: Matplotlib colormap name
        enhanced_resolution: If True, use enhanced processing for better quality
    """
    with rasterio.open(tif_path) as src:
        dem = src.read(1)
        
        # Handle nodata values
        nodata = src.nodata
        if nodata is not None:
            dem = np.where(dem == nodata, np.nan, dem)
        
        # Enhanced outlier handling for better visualization
        if enhanced_resolution:
            # Use percentile-based clipping for better contrast
            valid_data = dem[~np.isnan(dem)]
            if len(valid_data) > 0:
                p2, p98 = np.percentile(valid_data, [2, 98])
                dem_clipped = np.clip(dem, p2, p98)
                print(f"🎨 Enhanced colorization: Using 2-98% percentile range ({p2:.1f} to {p98:.1f})")
            else:
                dem_clipped = dem
        else:
            # Standard min/max clipping
            dem_clipped = np.clip(dem, np.nanmin(dem), np.nanmax(dem))
            print(f"🎨 Standard colorization: Using full range ({np.nanmin(dem):.1f} to {np.nanmax(dem):.1f})")
        
        # Normalize to 0-1 range
        dem_min, dem_max = np.nanmin(dem_clipped), np.nanmax(dem_clipped)
        if dem_max > dem_min:
            normed = (dem_clipped - dem_min) / (dem_max - dem_min)
        else:
            normed = np.zeros_like(dem_clipped)
        
        # Handle NaN values for visualization
        normed = np.nan_to_num(normed, nan=0.0)
        
        # Apply colormap
        cmap = getattr(plt.cm, colormap)
        colored = cmap(normed)
        
        # Enhanced output quality
        if enhanced_resolution:
            # Convert to high-quality image with better color depth
            img_array = (colored[:, :, :3] * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode='RGB')
            
            # Save with high quality settings
            img.save(output_path, 'PNG', optimize=False, compress_level=1)
            print(f"✅ ENHANCED colorized DEM saved to {output_path}")
        else:
            # Standard output
            img_array = (colored[:, :, :3] * 255).astype(np.uint8) 
            img = Image.fromarray(img_array)
            img.save(output_path)
            print(f"✅ Standard colorized DEM saved to {output_path}")

        return output_path