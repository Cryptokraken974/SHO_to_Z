"""
TIFF-native processing functions for elevation rasters
These functions work directly with elevation TIFF files without requiring LAZ conversion
"""

import os
import time
import logging
import numpy as np
from osgeo import gdal, gdalconst
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

# Enable GDAL exceptions
gdal.UseExceptions()

def read_elevation_tiff(tiff_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Read elevation TIFF file and return data array with metadata
    
    Args:
        tiff_path: Path to the elevation TIFF file
        
    Returns:
        Tuple of (elevation_array, metadata_dict)
    """
    print(f"📖 Reading elevation TIFF: {os.path.basename(tiff_path)}")
    
    dataset = gdal.Open(tiff_path, gdalconst.GA_ReadOnly)
    if dataset is None:
        raise ValueError(f"Could not open TIFF file: {tiff_path}")
    
    # Get raster band (assuming single band elevation data)
    band = dataset.GetRasterBand(1)
    elevation_array = band.ReadAsArray()
    
    # Get geospatial metadata
    geotransform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()
    nodata_value = band.GetNoDataValue()
    
    metadata = {
        'geotransform': geotransform,
        'projection': projection,
        'nodata_value': nodata_value,
        'width': dataset.RasterXSize,
        'height': dataset.RasterYSize,
        'pixel_width': geotransform[1],
        'pixel_height': abs(geotransform[5])
    }
    
    print(f"✅ Elevation data loaded: {metadata['width']}x{metadata['height']} pixels")
    print(f"📏 Pixel size: {metadata['pixel_width']:.6f} x {metadata['pixel_height']:.6f}")
    
    return elevation_array, metadata

def save_raster(array: np.ndarray, output_path: str, metadata: Dict[str, Any], dtype=gdal.GDT_Float32, enhanced_quality: bool = True):
    """
    Save numpy array as GeoTIFF with spatial reference and enhanced quality options
    
    Args:
        array: Numpy array to save
        output_path: Output file path
        metadata: Spatial metadata from original raster
        dtype: GDAL data type for output
        enhanced_quality: If True, use enhanced compression and quality settings
    """
    print(f"💾 Saving {'ENHANCED QUALITY' if enhanced_quality else 'standard'} raster: {os.path.basename(output_path)}")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create the output raster with enhanced options
    driver = gdal.GetDriverByName('GTiff')
    height, width = array.shape
    
    # Enhanced creation options for better quality
    if enhanced_quality:
        creation_options = [
            'COMPRESS=LZW',           # Lossless compression
            'PREDICTOR=2',            # Horizontal differencing predictor
            'TILED=YES',              # Tiled format for better performance
            'BLOCKXSIZE=512',         # Optimal tile size
            'BLOCKYSIZE=512',
            'BIGTIFF=IF_SAFER',       # Handle large files
            'NUM_THREADS=ALL_CPUS'    # Use all available CPUs
        ]
        dataset = driver.Create(output_path, width, height, 1, dtype, options=creation_options)
        print(f"🔧 Using enhanced TIFF options: LZW compression, tiled format, multi-threading")
    else:
        dataset = driver.Create(output_path, width, height, 1, dtype)
    
    # Set geospatial information
    dataset.SetGeoTransform(metadata['geotransform'])
    dataset.SetProjection(metadata['projection'])
    
    # Write the array
    band = dataset.GetRasterBand(1)
    band.WriteArray(array)
    
    # Set nodata value if available
    if metadata.get('nodata_value') is not None:
        band.SetNoDataValue(metadata['nodata_value'])
    
    # Enhanced: Calculate and set statistics for better visualization
    if enhanced_quality:
        band.ComputeStatistics(False)
        min_val, max_val, mean_val, std_val = band.GetStatistics(True, True)
        print(f"📊 Statistics computed: Min={min_val:.2f}, Max={max_val:.2f}, Mean={mean_val:.2f}, StdDev={std_val:.2f}")
    
    # Ensure data is written to disk
    dataset.FlushCache()
    dataset = None
    
    if enhanced_quality:
        print(f"✅ Enhanced quality raster saved successfully")
    else:
        print(f"✅ Raster saved successfully")

async def process_hillshade_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate hillshade from elevation TIFF
    
    Args:
        tiff_path: Path to elevation TIFF file
        output_dir: Output directory
        parameters: Processing parameters (azimuth, altitude)
        
    Returns:
        Processing results dictionary
    """
    start_time = time.time()
    
    print(f"\n🌄 HILLSHADE PROCESSING (TIFF)")
    print(f"📁 Input: {os.path.basename(tiff_path)}")
    print(f"📂 Output: {output_dir}")
    
    try:
        # Get parameters
        azimuth = parameters.get("azimuth", 315)
        altitude = parameters.get("altitude", 45)
        z_factor = parameters.get("z_factor", 1.0)
        
        print(f"⚙️ Parameters: azimuth={azimuth}°, altitude={altitude}°, z_factor={z_factor}")
        
        # Create output filename
        base_name = os.path.splitext(os.path.basename(tiff_path))[0]
        output_filename = f"{base_name}_hillshade.tif"
        output_path = os.path.join(output_dir, output_filename)
        
        # Read elevation data
        elevation_array, metadata = read_elevation_tiff(tiff_path)
        
        # Calculate hillshade
        print(f"🔄 Calculating hillshade...")
        hillshade_array = calculate_hillshade(elevation_array, azimuth, altitude, z_factor, metadata)
        
        # Save result with enhanced quality
        save_raster(hillshade_array, output_path, metadata, gdal.GDT_Byte, enhanced_quality=True)
        
        processing_time = time.time() - start_time
        
        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time,
            "parameters": parameters
        }
        
        print(f"✅ Hillshade completed in {processing_time:.2f} seconds")
        return result
        
    except Exception as e:
        error_msg = f"Hillshade processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "processing_time": time.time() - start_time
        }

def calculate_hillshade(elevation: np.ndarray, azimuth: float, altitude: float, 
                       z_factor: float, metadata: Dict[str, Any]) -> np.ndarray:
    """
    Calculate hillshade from elevation array
    
    Args:
        elevation: Elevation array
        azimuth: Light source azimuth (degrees)
        altitude: Light source altitude (degrees)  
        z_factor: Vertical exaggeration factor
        metadata: Raster metadata for pixel size
        
    Returns:
        Hillshade array (0-255)
    """
    print(f"🔄 Computing slopes and aspects...")
    
    # Get pixel size
    pixel_size = metadata['pixel_width']
    
    # Calculate gradients
    dy, dx = np.gradient(elevation * z_factor, pixel_size)
    
    # Calculate slope and aspect
    slope = np.arctan(np.sqrt(dx*dx + dy*dy))
    aspect = np.arctan2(-dx, dy)
    
    print(f"🔄 Applying lighting model...")
    
    # Convert angles to radians
    azimuth_rad = np.radians(azimuth)
    altitude_rad = np.radians(altitude)
    
    # Calculate hillshade
    hillshade = (np.cos(altitude_rad) * np.cos(slope) + 
                np.sin(altitude_rad) * np.sin(slope) * 
                np.cos(azimuth_rad - aspect))
    
    # Convert to 0-255 range
    hillshade = np.clip(hillshade * 255, 0, 255).astype(np.uint8)
    
    return hillshade

async def process_slope_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate slope raster from elevation TIFF
    """
    start_time = time.time()
    
    print(f"\n📐 SLOPE PROCESSING (TIFF)")
    print(f"📁 Input: {os.path.basename(tiff_path)}")
    
    try:
        # Read elevation data
        elevation_array, metadata = read_elevation_tiff(tiff_path)
        
        # Calculate slope
        print(f"🔄 Calculating slope...")
        slope_array = calculate_slope(elevation_array, metadata)
        
        # Create output filename
        base_name = os.path.splitext(os.path.basename(tiff_path))[0]
        output_filename = f"{base_name}_slope.tif"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save result with enhanced quality
        save_raster(slope_array, output_path, metadata, enhanced_quality=True)
        
        processing_time = time.time() - start_time
        
        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time
        }
        
        print(f"✅ Slope completed in {processing_time:.2f} seconds")
        return result
        
    except Exception as e:
        error_msg = f"Slope processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "processing_time": time.time() - start_time
        }

def calculate_slope(elevation: np.ndarray, metadata: Dict[str, Any]) -> np.ndarray:
    """
    Calculate slope in degrees from elevation array
    """
    pixel_size = metadata['pixel_width']
    
    # Calculate gradients
    dy, dx = np.gradient(elevation, pixel_size)
    
    # Calculate slope in radians, then convert to degrees
    slope_rad = np.arctan(np.sqrt(dx*dx + dy*dy))
    slope_deg = np.degrees(slope_rad)
    
    return slope_deg

async def process_aspect_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate aspect raster from elevation TIFF
    """
    start_time = time.time()
    
    print(f"\n🧭 ASPECT PROCESSING (TIFF)")
    print(f"📁 Input: {os.path.basename(tiff_path)}")
    
    try:
        # Read elevation data
        elevation_array, metadata = read_elevation_tiff(tiff_path)
        
        # Calculate aspect
        print(f"🔄 Calculating aspect...")
        aspect_array = calculate_aspect(elevation_array, metadata)
        
        # Create output filename
        base_name = os.path.splitext(os.path.basename(tiff_path))[0]
        output_filename = f"{base_name}_aspect.tif"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save result with enhanced quality
        save_raster(aspect_array, output_path, metadata, enhanced_quality=True)
        
        processing_time = time.time() - start_time
        
        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time
        }
        
        print(f"✅ Aspect completed in {processing_time:.2f} seconds")
        return result
        
    except Exception as e:
        error_msg = f"Aspect processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "processing_time": time.time() - start_time
        }

def calculate_aspect(elevation: np.ndarray, metadata: Dict[str, Any]) -> np.ndarray:
    """
    Calculate aspect in degrees from elevation array
    """
    pixel_size = metadata['pixel_width']
    
    # Calculate gradients
    dy, dx = np.gradient(elevation, pixel_size)
    
    # Calculate aspect in radians
    aspect_rad = np.arctan2(-dx, dy)
    
    # Convert to degrees (0-360)
    aspect_deg = np.degrees(aspect_rad)
    aspect_deg = (aspect_deg + 360) % 360
    
    return aspect_deg

async def process_tri_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Terrain Ruggedness Index (TRI) from elevation TIFF
    """
    start_time = time.time()
    
    print(f"\n🏔️ TRI PROCESSING (TIFF)")
    print(f"📁 Input: {os.path.basename(tiff_path)}")
    
    try:
        # Read elevation data
        elevation_array, metadata = read_elevation_tiff(tiff_path)
        
        # Calculate TRI
        print(f"🔄 Calculating Terrain Ruggedness Index...")
        tri_array = calculate_tri(elevation_array)
        
        # Create output filename
        base_name = os.path.splitext(os.path.basename(tiff_path))[0]
        output_filename = f"{base_name}_TRI.tif"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save result with enhanced quality
        save_raster(tri_array, output_path, metadata, enhanced_quality=True)
        
        processing_time = time.time() - start_time
        
        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time
        }
        
        print(f"✅ TRI completed in {processing_time:.2f} seconds")
        return result
        
    except Exception as e:
        error_msg = f"TRI processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "processing_time": time.time() - start_time
        }

def calculate_tri(elevation: np.ndarray) -> np.ndarray:
    """
    Calculate Terrain Ruggedness Index
    TRI is the mean of the absolute differences between a cell and its 8 neighbors
    """
    from scipy import ndimage
    
    # Define 3x3 kernel for neighbors
    kernel = np.array([[1, 1, 1],
                      [1, 0, 1], 
                      [1, 1, 1]])
    
    # Calculate mean of neighbors
    neighbor_mean = ndimage.convolve(elevation, kernel/8, mode='constant', cval=0)
    
    # TRI is absolute difference from neighbor mean
    tri = np.abs(elevation - neighbor_mean)
    
    return tri

async def process_tpi_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Topographic Position Index (TPI) from elevation TIFF
    """
    start_time = time.time()
    
    print(f"\n🗻 TPI PROCESSING (TIFF)")
    print(f"📁 Input: {os.path.basename(tiff_path)}")
    
    try:
        # Get neighborhood radius parameter
        radius = parameters.get("radius", 3)
        
        # Read elevation data
        elevation_array, metadata = read_elevation_tiff(tiff_path)
        
        # Calculate TPI
        print(f"🔄 Calculating Topographic Position Index (radius={radius})...")
        tpi_array = calculate_tpi(elevation_array, radius)
        
        # Create output filename
        base_name = os.path.splitext(os.path.basename(tiff_path))[0]
        output_filename = f"{base_name}_TPI.tif"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save result with enhanced quality
        save_raster(tpi_array, output_path, metadata, enhanced_quality=True)
        
        processing_time = time.time() - start_time
        
        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time,
            "parameters": {"radius": radius}
        }
        
        print(f"✅ TPI completed in {processing_time:.2f} seconds")
        return result
        
    except Exception as e:
        error_msg = f"TPI processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "processing_time": time.time() - start_time
        }

def calculate_tpi(elevation: np.ndarray, radius: int = 3) -> np.ndarray:
    """
    Calculate Topographic Position Index
    TPI is the difference between a cell and the mean of its neighborhood
    """
    from scipy import ndimage
    
    # Create circular kernel for neighborhood
    y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
    kernel = (x*x + y*y) <= radius*radius
    kernel = kernel.astype(float)
    kernel[radius, radius] = 0  # Exclude center cell
    
    # Normalize kernel (excluding center)
    kernel = kernel / kernel.sum()
    
    # Calculate neighborhood mean
    neighbor_mean = ndimage.convolve(elevation, kernel, mode='constant', cval=0)
    
    # TPI is difference from neighborhood mean
    tpi = elevation - neighbor_mean
    
    return tpi

async def process_color_relief_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate color relief map from elevation TIFF
    """
    start_time = time.time()
    
    print(f"\n🎨 COLOR RELIEF PROCESSING (TIFF)")
    print(f"📁 Input: {os.path.basename(tiff_path)}")
    
    try:
        # Read elevation data
        elevation_array, metadata = read_elevation_tiff(tiff_path)
        
        # Apply color relief
        print(f"🔄 Generating color relief map...")
        color_array = apply_color_relief(elevation_array)
        
        # Create output filename
        base_name = os.path.splitext(os.path.basename(tiff_path))[0]
        output_filename = f"{base_name}_color_relief.tif"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save result (3-band RGB) with enhanced quality
        save_color_raster(color_array, output_path, metadata, enhanced_quality=True)
        
        processing_time = time.time() - start_time
        
        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time
        }
        
        print(f"✅ Color relief completed in {processing_time:.2f} seconds")
        return result
        
    except Exception as e:
        error_msg = f"Color relief processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "processing_time": time.time() - start_time
        }

def apply_color_relief(elevation: np.ndarray) -> np.ndarray:
    """
    Apply color relief mapping to elevation data
    Returns RGB array
    """
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    
    # Normalize elevation to 0-1 range
    elev_min, elev_max = np.nanmin(elevation), np.nanmax(elevation)
    elev_norm = (elevation - elev_min) / (elev_max - elev_min)
    
    # Create terrain colormap (blue to green to brown to white)
    colors = ['#2E4053', '#1ABC9C', '#58D68D', '#F4D03F', '#E67E22', '#FFFFFF']
    n_bins = 256
    cmap = LinearSegmentedColormap.from_list('terrain', colors, N=n_bins)
    
    # Apply colormap
    rgb_array = cmap(elev_norm)[:, :, :3]  # Remove alpha channel
    
    # Convert to 0-255 range
    rgb_array = (rgb_array * 255).astype(np.uint8)
    
    return rgb_array

def save_color_raster(rgb_array: np.ndarray, output_path: str, metadata: Dict[str, Any], enhanced_quality: bool = True):
    """
    Save RGB array as 3-band GeoTIFF with enhanced quality options
    """
    print(f"💾 Saving {'ENHANCED QUALITY' if enhanced_quality else 'standard'} color raster: {os.path.basename(output_path)}")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create the output raster (3 bands for RGB)
    driver = gdal.GetDriverByName('GTiff')
    height, width, bands = rgb_array.shape
    
    # Enhanced creation options for better quality
    if enhanced_quality:
        creation_options = [
            'COMPRESS=LZW',           # Lossless compression
            'PREDICTOR=2',            # Horizontal differencing predictor
            'TILED=YES',              # Tiled format for better performance
            'BLOCKXSIZE=512',         # Optimal tile size
            'BLOCKYSIZE=512',
            'BIGTIFF=IF_SAFER',       # Handle large files
            'NUM_THREADS=ALL_CPUS',   # Use all available CPUs
            'PHOTOMETRIC=RGB'         # Specify RGB photometric interpretation
        ]
        dataset = driver.Create(output_path, width, height, bands, gdal.GDT_Byte, options=creation_options)
        print(f"🔧 Using enhanced color TIFF options: LZW compression, RGB photometric, tiled format")
    else:
        dataset = driver.Create(output_path, width, height, bands, gdal.GDT_Byte)
    
    # Set geospatial information
    dataset.SetGeoTransform(metadata['geotransform'])
    dataset.SetProjection(metadata['projection'])
    
    # Write each band with enhanced statistics
    for i in range(bands):
        band = dataset.GetRasterBand(i + 1)
        band.WriteArray(rgb_array[:, :, i])
        
        # Enhanced: Set color interpretation for RGB bands
        if enhanced_quality:
            if i == 0:
                band.SetColorInterpretation(gdal.GCI_RedBand)
            elif i == 1:
                band.SetColorInterpretation(gdal.GCI_GreenBand)
            elif i == 2:
                band.SetColorInterpretation(gdal.GCI_BlueBand)
    
    # Ensure data is written to disk
    dataset.FlushCache()
    dataset = None
    
    if enhanced_quality:
        print(f"✅ Enhanced quality color raster saved successfully")
    else:
        print(f"✅ Color raster saved successfully")

async def process_all_raster_products(tiff_path: str, progress_callback=None, request=None) -> Dict[str, Any]:
    """
    Automatically process all raster products from a downloaded elevation TIFF
    
    Args:
        tiff_path: Path to the elevation TIFF file
        progress_callback: Optional callback for progress updates
        request: Optional DownloadRequest to get coordinate information for proper output structure
        
    Returns:
        Dictionary with processing results for all products
    """
    from pathlib import Path
    
    start_time = time.time()
    
    print(f"\n🚀 AUTOMATIC RASTER PROCESSING")
    print(f"📁 Input TIFF: {os.path.basename(tiff_path)}")
    print(f"{'='*60}")
    
    # Create output directory structure matching the input folder structure
    # First, try to extract region name from the input file path
    # Expected path format: input/<region>/lidar/<filename>.tiff
    tiff_path_parts = Path(tiff_path).parts
    region_folder = None
    
    if len(tiff_path_parts) >= 3 and tiff_path_parts[0] == 'input':
        # Extract region name from path: input/<region>/lidar/file.tiff
        region_folder = tiff_path_parts[1]
        print(f"📍 Extracted region from path: {region_folder}")
    elif request and hasattr(request, 'region_name') and request.region_name:
        # Use region name if provided in request
        region_folder = request.region_name
        print(f"📍 Using region from request: {region_folder}")
    elif request and hasattr(request, 'bbox'):
        # Create coordinate-based folder name from bounding box
        center_lat = (request.bbox.north + request.bbox.south) / 2
        center_lng = (request.bbox.east + request.bbox.west) / 2
        lat_dir = 'S' if center_lat < 0 else 'N'
        lng_dir = 'W' if center_lng < 0 else 'E'
        region_folder = f"{abs(center_lat):.2f}{lat_dir}_{abs(center_lng):.2f}{lng_dir}"
        print(f"📍 Generated region from coordinates: {region_folder}")
    else:
        # Fallback to filename-based folder (should be avoided)
        base_name = os.path.splitext(os.path.basename(tiff_path))[0]
        region_folder = base_name
        print(f"⚠️ Fallback to filename-based region: {region_folder}")
    
    # Create output structure: output/<region coordinates>/lidar
    base_output_dir = os.path.join("output", region_folder, "lidar")
    
    print(f"📂 Output directory: {base_output_dir}")
    
    # Define all processing tasks
    processing_tasks = [
        ("hillshade_315", process_hillshade_tiff, {"azimuth": 315, "altitude": 45}),
        ("hillshade_225", process_hillshade_tiff, {"azimuth": 225, "altitude": 45}), 
        ("slope", process_slope_tiff, {}),
        ("aspect", process_aspect_tiff, {}),
        ("color_relief", process_color_relief_tiff, {})
    ]
    
    results = {}
    total_tasks = len(processing_tasks)
    
    for i, (task_name, process_func, parameters) in enumerate(processing_tasks):
        try:
            if progress_callback:
                await progress_callback({
                    "type": "processing_progress",
                    "message": f"Processing {task_name.replace('_', ' ').title()}...",
                    "progress": int((i / total_tasks) * 100)
                })
            
            print(f"\n📊 Processing {task_name} ({i+1}/{total_tasks})")
            
            # Create task-specific output directory
            task_output_dir = os.path.join(base_output_dir, task_name.title())
            os.makedirs(task_output_dir, exist_ok=True)
            
            # Process the raster product
            result = await process_func(tiff_path, task_output_dir, parameters)
            results[task_name] = result
            
            if result["status"] == "success":
                print(f"✅ {task_name} completed successfully")
                
                # Convert to PNG for visualization
                try:
                    # Import the conversion function with proper path handling
                    import sys
                    from pathlib import Path
                    
                    # Add the app directory to sys.path if not already there
                    app_dir = Path(__file__).parent.parent
                    if str(app_dir) not in sys.path:
                        sys.path.insert(0, str(app_dir))
                    
                    from convert import convert_geotiff_to_png
                    
                    # Create PNG output directory under the main lidar output folder
                    png_output_dir = os.path.join(base_output_dir, "png_outputs")
                    os.makedirs(png_output_dir, exist_ok=True)
                    
                    # Generate PNG filename and path
                    tiff_basename = os.path.splitext(os.path.basename(result["output_file"]))[0]
                    png_filename = f"{tiff_basename}.png"
                    png_path = os.path.join(png_output_dir, png_filename)
                    
                    # Convert TIFF to PNG
                    converted_png = convert_geotiff_to_png(result["output_file"], png_path)
                    
                    if converted_png and os.path.exists(converted_png):
                        result["png_file"] = converted_png
                        png_size = os.path.getsize(converted_png) / (1024 * 1024)  # MB
                        print(f"🖼️ PNG created: {os.path.basename(converted_png)} ({png_size:.1f} MB)")
                    else:
                        print(f"⚠️ PNG conversion failed for {task_name}: No output file created")
                        
                except Exception as e:
                    print(f"⚠️ PNG conversion failed for {task_name}: {e}")
            else:
                print(f"❌ {task_name} failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            error_msg = f"Processing failed for {task_name}: {str(e)}"
            print(f"❌ {error_msg}")
            results[task_name] = {
                "status": "error",
                "error": error_msg
            }
    
    # Final progress update
    if progress_callback:
        await progress_callback({
            "type": "processing_completed",
            "message": "All raster products processed",
            "progress": 100
        })
    
    total_time = time.time() - start_time
    
    # Summary
    successful = sum(1 for r in results.values() if r.get("status") == "success")
    failed = total_tasks - successful
    
    print(f"\n{'='*60}")
    print(f"🎯 PROCESSING SUMMARY")
    print(f"✅ Successful: {successful}/{total_tasks}")
    print(f"❌ Failed: {failed}/{total_tasks}")
    print(f"⏱️ Total time: {total_time:.2f} seconds")
    print(f"📂 Output directory: {base_output_dir}")
    print(f"{'='*60}")
    
    return {
        "total_tasks": total_tasks,
        "successful": successful,
        "failed": failed,
        "total_time": total_time,
        "output_directory": base_output_dir,
        "results": results
    }
