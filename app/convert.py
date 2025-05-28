import rasterio
from matplotlib import pyplot as plt
import os
import base64
import time
from typing import Optional

def tif_to_png_base64(tif_path: str) -> str:
    """
    Convert GeoTIFF file to PNG and return as base64 encoded string
    
    Args:
        tif_path: Path to the input TIF file
        
    Returns:
        Base64 encoded PNG image string
    """
    print(f"\n🖼️ CONVERT: Starting TIF to PNG conversion")
    print(f"📁 Input TIF: {tif_path}")
    
    start_time = time.time()
    
    try:
        # Generate output PNG filename following our standard: <basename>_<step>.png
        tif_basename = os.path.splitext(tif_path)[0]  # Remove .tif extension
        png_path = f"{tif_basename}.png"
        
        print(f"📁 Output PNG: {png_path}")
        
        # Validate input file
        print(f"🔍 Validating input TIF file...")
        if not os.path.exists(tif_path):
            error_msg = f"TIF file not found: {tif_path}"
            print(f"❌ {error_msg}")
            raise FileNotFoundError(error_msg)
        
        tif_size = os.path.getsize(tif_path)
        print(f"✅ Input TIF validated")
        print(f"📊 TIF file size: {tif_size:,} bytes ({tif_size / (1024**2):.2f} MB)")
        
        # Read GeoTIFF using rasterio
        print(f"📖 Reading GeoTIFF with rasterio...")
        with rasterio.open(tif_path) as src:
            print(f"   📊 Raster info:")
            print(f"      🗺️ CRS: {src.crs}")
            print(f"      📐 Shape: {src.width} x {src.height}")
            print(f"      📊 Bands: {src.count}")
            print(f"      🎯 Data type: {src.dtypes[0]}")
            print(f"      🌍 Bounds: {src.bounds}")
            
            # Read the first band
            print(f"   📊 Reading band 1...")
            image = src.read(1)
            
            print(f"   📊 Image array info:")
            print(f"      📐 Shape: {image.shape}")
            print(f"      📊 Data type: {image.dtype}")
            print(f"      📈 Min value: {image.min()}")
            print(f"      📈 Max value: {image.max()}")
            print(f"      📈 Mean value: {image.mean():.2f}")
        
        # Convert to PNG using matplotlib
        print(f"🎨 Converting to PNG with matplotlib...")
        conversion_start = time.time()
        
        plt.imsave(png_path, image, cmap="gray")
        
        conversion_time = time.time() - conversion_start
        print(f"✅ PNG conversion completed in {conversion_time:.2f} seconds")
        
        # Validate output file
        print(f"🔍 Validating output PNG file...")
        if not os.path.exists(png_path):
            error_msg = f"PNG file was not created: {png_path}"
            print(f"❌ {error_msg}")
            raise FileNotFoundError(error_msg)
        
        png_size = os.path.getsize(png_path)
        print(f"✅ Output PNG validated")
        print(f"📊 PNG file size: {png_size:,} bytes ({png_size / (1024**2):.2f} MB)")
        print(f"📄 PNG file path: {os.path.abspath(png_path)}")
        
        # Convert to base64
        print(f"🔄 Converting PNG to base64...")
        base64_start = time.time()
        
        with open(png_path, 'rb') as png_file:
            png_data = png_file.read()
            base64_data = base64.b64encode(png_data).decode('utf-8')
        
        base64_time = time.time() - base64_start
        total_time = time.time() - start_time
        
        print(f"✅ Base64 conversion completed in {base64_time:.2f} seconds")
        print(f"📊 Base64 string length: {len(base64_data):,} characters")
        print(f"⏱️ Total conversion time: {total_time:.2f} seconds")
        print(f"✅ TIF to PNG conversion successful!\n")
        
        return base64_data
        
    except rasterio.errors.RasterioIOError as e:
        error_msg = f"Rasterio failed to read TIF file: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Error type: RasterioIOError")
        raise Exception(error_msg)
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"TIF to PNG conversion failed: {str(e)}"
        print(f"❌ Error in TIF to PNG conversion: {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Processing time before error: {processing_time:.2f} seconds")
        raise Exception(error_msg)

def convert_geotiff_to_png(tif_path: str, png_path: Optional[str] = None) -> str:
    """
    Convert GeoTIFF file to PNG file
    
    Args:
        tif_path: Path to the input TIF file
        png_path: Optional path for output PNG file. If None, will be generated from tif_path
        
    Returns:
        Path to the generated PNG file
    """
    print(f"\n🎨 GEOTIFF TO PNG: Starting conversion")
    print(f"📁 Input TIF: {tif_path}")
    
    start_time = time.time()
    
    try:
        # Generate output PNG filename if not provided
        if png_path is None:
            tif_basename = os.path.splitext(tif_path)[0]  # Remove .tif extension
            png_path = f"{tif_basename}.png"
        
        print(f"📁 Output PNG: {png_path}")
        
        # Read GeoTIFF and convert to PNG
        with rasterio.open(tif_path) as src:
            image = src.read(1)
            plt.imsave(png_path, image, cmap="gray")
        
        processing_time = time.time() - start_time
        
        print(f"✅ GeoTIFF to PNG conversion completed in {processing_time:.2f} seconds")
        print(f"📄 PNG saved: {png_path}")
        
        return png_path
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"GeoTIFF to PNG conversion failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Processing time before error: {processing_time:.2f} seconds")
        raise Exception(error_msg)