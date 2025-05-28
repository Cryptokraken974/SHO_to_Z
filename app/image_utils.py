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

def colorize_dem(tif_path: str, output_path: str, colormap='terrain'):
    with rasterio.open(tif_path) as src:
        dem = src.read(1)

        dem = np.clip(dem, dem.min(), dem.max())
        normed = (dem - dem.min()) / (dem.max() - dem.min())

        cmap = getattr(plt.cm, colormap)
        colored = cmap(normed)

        img = Image.fromarray((colored[:, :, :3] * 255).astype(np.uint8))
        img.save(output_path)

        print(f"Saved colorized DEM to {output_path}")
        return output_path