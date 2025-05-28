from osgeo import gdal
import os
import time
from typing import Optional
import base64

def convert_geotiff_to_png(tif_path: str, png_path: Optional[str] = None) -> str:
    """
    Convert GeoTIFF file to PNG file with worldfile preservation
    
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
        
        # Ensure output directory exists
        output_dir = os.path.dirname(png_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 Created output directory: {output_dir}")
        
        # Open GeoTIFF with GDAL
        ds = gdal.Open(tif_path)
        if ds is None:
            error_msg = f"GDAL failed to open TIF file: {tif_path}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        # Convert to PNG with worldfile using GDAL
        print(f"🎨 Converting with GDAL (worldfile enabled)...")
        gdal.Translate(png_path, ds, format="PNG", options="-co worldfile=yes")
        
        # Close dataset
        ds = None
        
        processing_time = time.time() - start_time
        
        print(f"✅ GeoTIFF to PNG conversion completed in {processing_time:.2f} seconds")
        print(f"📄 PNG saved: {png_path}")
        
        # Check for worldfile
        worldfile_path = os.path.splitext(png_path)[0] + ".pgw"
        if os.path.exists(worldfile_path):
            print(f"✅ Worldfile created: {worldfile_path}")
        
        return png_path
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"GeoTIFF to PNG conversion failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Processing time before error: {processing_time:.2f} seconds")
        raise Exception(error_msg)

def convert_geotiff_to_png_base64(tif_path: str) -> str:
    """
    Convert GeoTIFF file to PNG and return as base64 encoded string
    
    Args:
        tif_path: Path to the input TIF file
        
    Returns:
        Base64 encoded PNG image string
    """
    print(f"\n🖼️ CONVERT: Starting TIF to PNG base64 conversion")
    print(f"📁 Input TIF: {tif_path}")
    
    start_time = time.time()
    
    try:
        # First convert to PNG file
        png_path = convert_geotiff_to_png(tif_path)
        
        # Convert PNG to base64
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
        print(f"✅ TIF to PNG base64 conversion successful!\n")
        
        return base64_data
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"TIF to PNG base64 conversion failed: {str(e)}"
        print(f"❌ Error in TIF to PNG base64 conversion: {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Processing time before error: {processing_time:.2f} seconds")
        raise Exception(error_msg)