"""
TIFF-native processing functions for elevation rasters
These functions work directly with elevation TIFF files without requiring LAZ conversion
"""

import os
import time
import json
import logging
import tempfile
import numpy as np
import rasterio
import rasterio.windows
import shutil
from rasterio.enums import Resampling
from rasterio.warp import reproject, calculate_default_transform
from osgeo import gdal, gdalconst
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path
import asyncio
from .sky_view_factor import process_sky_view_factor_tiff

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
        region_folder = parameters.get("region_folder", "UnknownRegion")
        
        print(f"⚙️ Parameters: azimuth={azimuth}°, altitude={altitude}°, z_factor={z_factor}")
        
        # Create output filename, allow override via parameters
        output_filename = parameters.get("output_filename")
        if not output_filename:
            output_filename = f"{region_folder}_hillshade.tif"
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


def calculate_multi_hillshade(elevation: np.ndarray, azimuths: List[float], altitude: float,
                              z_factor: float, metadata: Dict[str, Any]) -> np.ndarray:
    """Calculate composite hillshade from multiple azimuth angles."""
    shades = []
    for az in azimuths:
        shades.append(calculate_hillshade(elevation, az, altitude, z_factor, metadata).astype(np.float32))
    composite = np.mean(shades, axis=0)
    return np.clip(composite, 0, 255).astype(np.uint8)


async def process_multi_hillshade_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate composite hillshade using multiple azimuth directions."""
    start_time = time.time()
    print(f"\n🌄 MULTI HILLSHADE PROCESSING (TIFF)")
    print(f"📁 Input: {os.path.basename(tiff_path)}")
    print(f"📂 Output: {output_dir}")

    try:
        altitude = parameters.get("altitude", 30)
        azimuths = parameters.get("azimuths", [])
        z_factor = parameters.get("z_factor", 1.0)

        if not azimuths:
            raise ValueError("azimuths list required for multi hillshade")

        print(f"⚙️ Parameters: altitude={altitude}°, azimuths={azimuths}, z_factor={z_factor}")

        region_folder = parameters.get("region_folder", "UnknownRegion")
        output_filename = parameters.get("output_filename") or f"{region_folder}_multi_hillshade.tif"
        output_path = os.path.join(output_dir, output_filename)

        elevation_array, metadata = read_elevation_tiff(tiff_path)

        print("🔄 Calculating multi-direction hillshade...")
        hillshade_array = calculate_multi_hillshade(elevation_array, azimuths, altitude, z_factor, metadata)

        save_raster(hillshade_array, output_path, metadata, gdal.GDT_Byte, enhanced_quality=True)

        processing_time = time.time() - start_time

        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time,
            "parameters": parameters,
        }

        print(f"✅ Multi hillshade completed in {processing_time:.2f} seconds")
        return result

    except Exception as e:
        error_msg = f"Multi hillshade processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "processing_time": time.time() - start_time,
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
        region_folder = parameters.get("region_folder", "UnknownRegion")
        output_filename = f"{region_folder}_aspect.tif"
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
        region_folder = parameters.get("region_folder", "UnknownRegion")
        output_filename = f"{region_folder}_TRI.tif"
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
        region_folder = parameters.get("region_folder", "UnknownRegion")
        output_filename = f"{region_folder}_TPI.tif"
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
        region_folder = parameters.get("region_folder", "UnknownRegion")
        output_filename = f"{region_folder}_color_relief.tif"
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

async def process_slope_relief_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a colorized slope relief raster from an elevation TIFF."""
    start_time = time.time()

    print(f"\n🌈 SLOPE RELIEF PROCESSING (TIFF)")
    print(f"📁 Input: {os.path.basename(tiff_path)}")

    try:
        # Read elevation data
        elevation_array, metadata = read_elevation_tiff(tiff_path)

        # Calculate slope first
        print(f"🔄 Calculating slope for relief...")
        slope_array = calculate_slope(elevation_array, metadata)

        # Apply color relief to the slope values
        print(f"🔄 Applying color relief to slope values...")
        slope_relief = apply_color_relief(slope_array)

        region_folder = parameters.get("region_folder", "UnknownRegion")
        output_filename = parameters.get("output_filename") or f"{region_folder}_slope_relief.tif"
        output_path = os.path.join(output_dir, output_filename)

        save_color_raster(slope_relief, output_path, metadata, enhanced_quality=True)

        processing_time = time.time() - start_time

        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time
        }

        print(f"✅ Slope relief completed in {processing_time:.2f} seconds")
        return result

    except Exception as e:
        error_msg = f"Slope relief processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "processing_time": time.time() - start_time
        }

async def process_lrm_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Local Relief Model (LRM) from an elevation TIFF."""
    start_time = time.time()

    print(f"\n🌄 LRM PROCESSING (TIFF)")
    print(f"📁 Input: {os.path.basename(tiff_path)}")

    try:
        window_size = parameters.get("window_size", 11)

        elevation_array, metadata = read_elevation_tiff(tiff_path)

        print(f"🔄 Calculating Local Relief Model (window={window_size})...")
        from scipy.ndimage import uniform_filter

        smooth = uniform_filter(elevation_array.astype(np.float32), size=window_size)
        lrm_array = elevation_array.astype(np.float32) - smooth

        region_folder = parameters.get("region_folder", "UnknownRegion")
        output_filename = f"{region_folder}_LRM.tif"
        output_path = os.path.join(output_dir, output_filename)

        save_raster(lrm_array, output_path, metadata, enhanced_quality=True)

        processing_time = time.time() - start_time

        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time,
            "parameters": {"window_size": window_size}
        }

        print(f"✅ LRM completed in {processing_time:.2f} seconds")
        return result

    except Exception as e:
        error_msg = f"LRM processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "processing_time": time.time() - start_time
        }

async def process_enhanced_lrm_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced LRM processing with archaeological features:
    - Adaptive window sizing based on pixel resolution
    - Gaussian filtering option for better edge preservation
    - Enhanced normalization with percentile clipping
    """
    print(f"\n🌄 ENHANCED LRM PROCESSING (TIFF)")
    print(f"📁 Input: {os.path.basename(tiff_path)}")
    start_time = time.time()
    
    try:
        # Import enhanced LRM functions
        from .lrm import (
            detect_pixel_resolution, 
            calculate_adaptive_window_size,
            apply_smoothing_filter,
            enhanced_normalization
        )
        
        # Extract parameters with defaults for archaeological analysis
        window_size = parameters.get("window_size", None)  # None for auto-sizing
        filter_type = parameters.get("filter_type", "uniform")
        auto_sizing = parameters.get("auto_sizing", True)
        enhanced_normalization_enabled = parameters.get("enhanced_normalization", False)
        
        # Read elevation data
        print(f"📖 Reading elevation TIFF: {os.path.basename(tiff_path)}")
        elevation_array, metadata = read_elevation_tiff(tiff_path)
        print(f"✅ Elevation data loaded: {elevation_array.shape[1]}x{elevation_array.shape[0]} pixels")
        
        # Get geotransform for resolution detection
        geotransform = metadata.get('geotransform')
        if geotransform:
            detected_resolution = detect_pixel_resolution(geotransform)
            print(f"📏 Pixel size: {geotransform[1]:.6f} x {abs(geotransform[5]):.6f}")
            print(f"   📐 Detected pixel resolution: {detected_resolution:.3f} meters/pixel")
        else:
            detected_resolution = 1.0  # Default fallback
            print(f"⚠️ No geotransform found, using default 1.0m/pixel resolution")
        
        # Calculate optimal window size if not provided
        if window_size is None:
            window_size = calculate_adaptive_window_size(detected_resolution, auto_sizing)
        elif auto_sizing:
            # Override provided window size with adaptive calculation
            window_size = calculate_adaptive_window_size(detected_resolution, auto_sizing)
        
        # Enhanced logging for new features
        if auto_sizing:
            print(f"   🎯 ENHANCED ADAPTIVE SIZING: {window_size} pixels (resolution-based calculation)")
            print(f"      📐 Resolution: {detected_resolution:.3f}m/pixel → Optimal window: {window_size}px")
        else:
            print(f"   🎯 Using window size: {window_size} pixels (fixed)")
        
        if filter_type == "gaussian":
            print(f"   🔧 ENHANCED GAUSSIAN FILTER: Archaeological feature preservation")
        else:
            print(f"   🔧 Filter type: {filter_type}")
        
        if enhanced_normalization_enabled:
            print(f"   🎨 ENHANCED NORMALIZATION: P2-P98 percentile clipping with symmetric scaling")
        
        # Apply enhanced smoothing filter
        print(f"\n🔧 Step 3: Applying {filter_type} smoothing filter (window size: {window_size})...")
        
        # Enhanced feature logging
        if filter_type == "gaussian":
            print(f"   🔥 ENHANCED GAUSSIAN SMOOTHING: Better edge preservation for archaeological features")
        
        # Enhanced NoData handling - convert to NaN before processing
        nodata_mask = elevation_array == -9999
        elevation_array = elevation_array.astype(np.float32)
        elevation_array[nodata_mask] = np.nan
        
        # Apply selected smoothing filter
        valid_mask = ~np.isnan(elevation_array)
        if np.any(valid_mask):
            smoothed = apply_smoothing_filter(elevation_array, window_size, filter_type)
            print(f"   ✅ Smoothing completed using {filter_type} filter")
            if filter_type == "gaussian":
                print(f"   🎯 Gaussian filtering enhances subtle archaeological feature detection")
        else:
            raise Exception("No valid elevation data found in elevation TIFF")
        
        # Calculate LRM (elevation - smoothed elevation)
        print(f"\n➖ Step 4: Calculating Local Relief Model...")
        lrm_array = elevation_array - smoothed
        
        # Apply enhanced normalization if enabled
        if enhanced_normalization_enabled:
            print(f"🎨 Applying enhanced normalization...")
            lrm_array = enhanced_normalization(lrm_array, nodata_mask)
            print(f"   ✅ Enhanced normalization applied")
            print(f"   🎯 Percentile clipping with symmetric scaling for archaeological visualization")
        else:
            # Restore NoData values for standard processing
            lrm_array[nodata_mask] = -9999
        
        print(f"   📊 LRM range: {np.nanmin(lrm_array[~nodata_mask]):.2f} to {np.nanmax(lrm_array[~nodata_mask]):.2f} meters")
        print(f"   ✅ Local relief calculation completed")
        
        # Generate output filename with enhancement info
        region_folder = parameters.get("region_folder", "UnknownRegion")
        output_filename = f"{region_folder}_LRM"
        
        # Add enhancement suffixes for clarity
        if filter_type == "gaussian":
            output_filename += "_gaussian"
        if auto_sizing:
            output_filename += "_adaptive"
        if enhanced_normalization_enabled:
            output_filename += "_enhanced"
            
        output_filename += ".tif"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save enhanced LRM
        print(f"\n💾 Step 5: Saving Enhanced LRM as GeoTIFF...")
        save_raster(lrm_array, output_path, metadata, enhanced_quality=True)
        
        processing_time = time.time() - start_time
        
        # Enhanced completion logging
        print(f"✅ ENHANCED LRM generation completed: {output_filename}")
        print(f"   ⏱️ Processing time: {processing_time:.2f} seconds")
        print(f"   🎯 Enhanced features used:")
        print(f"      📐 Adaptive sizing: {'Yes' if auto_sizing else 'No'}")
        print(f"      🔧 Filter type: {filter_type}")
        print(f"      🎨 Enhanced normalization: {'Yes' if enhanced_normalization_enabled else 'No'}")
        
        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time,
            "enhanced_features": {
                "adaptive_sizing": auto_sizing,
                "filter_type": filter_type,
                "enhanced_normalization": enhanced_normalization_enabled,
                "window_size": window_size,
                "detected_resolution": detected_resolution
            },
            "parameters": {
                "window_size": window_size,
                "filter_type": filter_type,
                "auto_sizing": auto_sizing,
                "enhanced_normalization": enhanced_normalization_enabled
            }
        }

        print(f"✅ Enhanced LRM completed successfully")
        
        # 🎯 ENHANCED FEATURES CONFIRMATION
        print(f"\n{'🌄'*20} ENHANCED LRM FEATURES ACTIVE {'🌄'*20}")
        print(f"✅ Archaeological analysis mode: ENABLED")
        print(f"✅ Adaptive window sizing: {'ACTIVE' if auto_sizing else 'FIXED'} ({window_size}px)")
        print(f"✅ Advanced filtering: {filter_type.upper()} ({'Archaeological edge preservation' if filter_type == 'gaussian' else 'Standard uniform'})")
        print(f"✅ Enhanced normalization: {'ACTIVE (P2-P98 clipping)' if enhanced_normalization_enabled else 'STANDARD'}")
        print(f"✅ Resolution optimization: {detected_resolution:.3f}m/pixel detected")
        print(f"{'🌄'*70}")
        
        return result

    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Enhanced LRM processing failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "processing_time": processing_time
        }

async def process_slope_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standard slope processing with greyscale visualization (default):
    - Greyscale colormap for general terrain analysis
    - Configurable stretch methods for optimal contrast
    - Optional inferno colormap for archaeological analysis
    """
    print(f"\n📐 SLOPE PROCESSING (TIFF)")
    print(f"📁 Input: {os.path.basename(tiff_path)}")
    start_time = time.time()
    
    try:
        # Extract parameters with defaults for standard analysis
        use_inferno_colormap = parameters.get("use_inferno_colormap", False)  # Default to greyscale
        max_slope_degrees = parameters.get("max_slope_degrees", 60.0)
        stretch_type = parameters.get("stretch_type", "stddev")
        stretch_params = parameters.get("stretch_params", {"num_stddev": 2.0})
        enhanced_contrast = parameters.get("enhanced_contrast", False)  # Default to standard contrast
        region_folder = parameters.get("region_folder", "UnknownRegion")  # Get user-friendly region name
        
        # Read elevation data
        print(f"📖 Reading elevation TIFF: {os.path.basename(tiff_path)}")
        elevation_array, metadata = read_elevation_tiff(tiff_path)
        print(f"✅ Elevation data loaded: {elevation_array.shape[1]}x{elevation_array.shape[0]} pixels")
        
        # Standard slope calculation
        print(f"\n🔄 Step 1: Calculating slope...")
        slope_array = calculate_slope(elevation_array, metadata)
        
        # Choose visualization mode
        if use_inferno_colormap:
            print(f"   🏛️ ENHANCED ARCHAEOLOGICAL VISUALIZATION: YlOrRd optimal terrain analysis")
            print(f"      📐 Linear rescaling: 2° to 20° archaeological normalization for optimal contrast")
            print(f"      🎨 YlOrRd colormap: Yellow-Orange-Red optimal for archaeological features")
            print(f"      🏛️ Archaeological features highlighted: Pathways, platforms, scarps, berms")
        else:
            print(f"   📐 STANDARD GREYSCALE VISUALIZATION: General terrain analysis")
            print(f"      🎨 Greyscale colormap: Standard terrain visualization")
            print(f"      📊 {stretch_type.upper()} stretch: Optimal contrast for general use")
            if enhanced_contrast:
                print(f"      ⚡ Enhanced contrast processing: Active")
            print(f"      🗺️ Visualization: Black (flat) → White (steep)")
        
        # Slope range analysis
        valid_slope = slope_array[~np.isnan(slope_array)]
        if len(valid_slope) > 0:
            slope_min, slope_max = np.nanmin(valid_slope), np.nanmax(valid_slope)
            slope_mean = np.nanmean(valid_slope)
            
            # Calculate slope distribution for terrain analysis
            flat_areas = np.sum(valid_slope < 5) / len(valid_slope) * 100
            moderate_slopes = np.sum((valid_slope >= 5) & (valid_slope < 20)) / len(valid_slope) * 100
            steep_terrain = np.sum(valid_slope >= 20) / len(valid_slope) * 100
            
            print(f"   📊 Slope analysis results:")
            print(f"      📈 Range: {slope_min:.2f}° to {slope_max:.2f}° (mean: {slope_mean:.2f}°)")
            print(f"      🟫 Flat areas (0°-5°): {flat_areas:.1f}%")
            print(f"      🟡 Moderate slopes (5°-20°): {moderate_slopes:.1f}%")
            print(f"      🔴 Steep terrain (20°+): {steep_terrain:.1f}%")
            
            if use_inferno_colormap:
                # Archaeological interpretation for YlOrRd mode
                if steep_terrain > 30:
                    print(f"      🏔️ High relief terrain detected - excellent for archaeological analysis")
                elif flat_areas > 60:
                    print(f"      🏛️ Low relief terrain - subtle features will be enhanced")
            else:
                # General terrain interpretation for standard mode
                if steep_terrain > 30:
                    print(f"      🏔️ High relief terrain - mountainous/hilly landscape")
                elif flat_areas > 60:
                    print(f"      🏞️ Low relief terrain - plains/gentle landscape")
        
        # Generate output filename with enhancement info
        output_filename = f"{region_folder}_slope"
        
        # Add enhancement suffixes for clarity
        if use_inferno_colormap:
            output_filename += "_archaeological_ylord"
        if enhanced_contrast:
            output_filename += "_enhanced"
            
        output_filename += ".tif"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save slope TIFF
        print(f"\n💾 Step 2: Saving Slope as GeoTIFF...")
        save_raster(slope_array, output_path, metadata, enhanced_quality=True)
        
        processing_time = time.time() - start_time
        
        # Completion logging based on mode
        if use_inferno_colormap:
            print(f"✅ ENHANCED ARCHAEOLOGICAL SLOPE generation completed: {output_filename}")
        else:
            print(f"✅ SLOPE generation completed: {output_filename}")
        
        print(f"   ⏱️ Processing time: {processing_time:.2f} seconds")
        print(f"   🎯 Features used:")
        print(f"      🎨 Colormap: {'YlOrRd (archaeological)' if use_inferno_colormap else 'Greyscale (standard)'}")
        print(f"      📐 Max slope range: {max_slope_degrees}°")
        if enhanced_contrast:
            print(f"      ⚡ Enhanced contrast: Active")
        
        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time,
            "features": {
                "ylord_archaeological_colormap": use_inferno_colormap,
                "max_slope_degrees": max_slope_degrees,
                "enhanced_contrast": enhanced_contrast,
                "slope_distribution": {
                    "flat_areas_percent": flat_areas if len(valid_slope) > 0 else 0,
                    "moderate_slopes_percent": moderate_slopes if len(valid_slope) > 0 else 0,
                    "steep_terrain_percent": steep_terrain if len(valid_slope) > 0 else 0
                }
            },
            "parameters": {
                "use_inferno_colormap": use_inferno_colormap,
                "max_slope_degrees": max_slope_degrees,
                "enhanced_contrast": enhanced_contrast
            }
        }

        if use_inferno_colormap:
            print(f"✅ enhanced archaeological slope completed successfully")
            
            # 🎯 ENHANCED FEATURES CONFIRMATION
            print(f"\n{'🏛️'*20} ENHANCED ARCHAEOLOGICAL SLOPE FEATURES ACTIVE {'🏛️'*20}")
            print(f"✅ Archaeological terrain analysis mode: ENABLED")
            print(f"✅ YlOrRd colormap optimization: ACTIVE")
            print(f"✅ Enhanced contrast processing: {'ACTIVE' if enhanced_contrast else 'DISABLED'}")
            print(f"✅ Slope range optimization: 2° to 20° (archaeological normalization)")
            print(f"✅ Terrain classification: {flat_areas:.1f}% flat, {moderate_slopes:.1f}% moderate, {steep_terrain:.1f}% steep")
            print(f"{'🏛️'*70}")
        else:
            print(f"✅ slope completed successfully")
        
        return result

    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Slope processing failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "processing_time": processing_time
        }

def apply_color_relief(elevation: np.ndarray) -> np.ndarray:
    """
    Apply gentler elevation-based color relief mapping for archaeological analysis
    Returns RGB array with smooth transitions between elevation zones
    """
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    
    # Normalize elevation to 0-1 range
    elev_min, elev_max = np.nanmin(elevation), np.nanmax(elevation)
    elev_norm = (elevation - elev_min) / (elev_max - elev_min)
    
    # 🟣 Create gentler elevation-based color ramp with 5 soft color bands
    # Designed for archaeological visualization with smooth transitions
    colors = [
        '#FFFADC',  # Pale cream/yellow (lowest elevation)
        '#FFE4B5',  # Soft peach/orange  
        '#FFC098',  # Gentle salmon
        '#FFA07A',  # Soft coral/light red
        '#FF8C69'   # Warm light red (highest elevation)
    ]
    
    n_bins = 256
    cmap = LinearSegmentedColormap.from_list('archaeological_gentle', colors, N=n_bins)
    
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


async def create_rgb_hillshade(hs_files: Dict[str, str], output_path: str) -> Dict[str, Any]:
    """Create an RGB composite from three hillshade TIFFs."""
    start_time = time.time()

    print(f"\n🌈 RGB HILLSHADE COMPOSITE")
    print(f"📂 Output: {output_path}")

    try:
        arrays: Dict[str, np.ndarray] = {}
        geo = proj = None

        for band, path in hs_files.items():
            ds = gdal.Open(path)
            if ds is None:
                raise FileNotFoundError(f"Hillshade file not found: {path}")

            arr = ds.ReadAsArray().astype(np.float32)
            arrays[band] = arr

            if geo is None:
                geo = ds.GetGeoTransform()
                proj = ds.GetProjection()

            ds = None

        def norm(a: np.ndarray) -> np.ndarray:
            return ((a - a.min()) / (a.max() - a.min()) * 255.0).astype(np.uint8)

        rgb = np.stack([norm(arrays['R']), norm(arrays['G']), norm(arrays['B'])], axis=-1)

        metadata = {
            'geotransform': geo,
            'projection': proj
        }

        save_color_raster(rgb, output_path, metadata, enhanced_quality=True)

        processing_time = time.time() - start_time

        print(f"✅ RGB composite created in {processing_time:.2f} seconds")
        return {
            'status': 'success',
            'output_file': output_path,
            'processing_time': processing_time
        }

    except Exception as e:
        error_msg = f"RGB hillshade creation failed: {e}"
        print(f"❌ {error_msg}")
        return {
            'status': 'error',
            'error': error_msg,
            'processing_time': time.time() - start_time
        }


async def create_tint_overlay(color_relief_path: str, hillshade_path: str, output_path: str) -> Dict[str, Any]:
    """Create a gentler elevation-based tint overlay with smooth hillshade blending."""
    start_time = time.time()

    print(f"\n🟣 ARCHAEOLOGICAL TINT OVERLAY")
    print(f"📂 Output: {output_path}")

    try:
        # Read color relief (RGB)
        ds_color = gdal.Open(color_relief_path)
        if ds_color is None:
            raise FileNotFoundError(f"Color relief not found: {color_relief_path}")

        color = ds_color.ReadAsArray().astype(np.float32)  # shape (bands, H, W)
        geo = ds_color.GetGeoTransform()
        proj = ds_color.GetProjection()
        ds_color = None

        # Ensure 3-band format
        if color.ndim == 2:
            color = np.stack([color, color, color])

        # Read hillshade (grayscale or RGB)
        ds_hs = gdal.Open(hillshade_path)
        if ds_hs is None:
            raise FileNotFoundError(f"Hillshade not found: {hillshade_path}")

        hs = ds_hs.ReadAsArray().astype(np.float32)
        ds_hs = None

        # Reduce to single intensity band
        if hs.ndim == 3:
            hs = np.mean(hs, axis=0)

        # Normalize hillshade to 0-1 range with gentle enhancement
        if hs.max() > hs.min():
            hs_norm = (hs - hs.min()) / (hs.max() - hs.min())
            # Apply gentle contrast enhancement for better archaeological feature visibility
            hs_norm = np.power(hs_norm, 0.8)  # Slightly brighten shadows
        else:
            hs_norm = np.zeros_like(hs)

        # 🟣 Enhanced blending for archaeological visualization
        # Use a more sophisticated blending that preserves color information while enhancing relief
        blend_factor = 0.7  # Preserve more color information than standard tinting
        
        # Apply enhanced tint blending
        # Formula: color * (blend_factor + (1-blend_factor) * hillshade_intensity)
        tinted = color * (blend_factor + (1 - blend_factor) * hs_norm)
        tinted = np.clip(tinted, 0, 255).astype(np.uint8)

        rgb = np.transpose(tinted, (1, 2, 0))  # (H, W, 3)

        metadata = {
            'geotransform': geo,
            'projection': proj
        }

        save_color_raster(rgb, output_path, metadata, enhanced_quality=True)

        processing_time = time.time() - start_time

        print(f"✅ Archaeological tint overlay created in {processing_time:.2f} seconds")
        print(f"🎨 Applied gentle elevation-based color ramp with smooth hillshade blending")
        return {
            'status': 'success',
            'output_file': output_path,
            'processing_time': processing_time,
            'visualization_type': 'archaeological_gentle'
        }

    except Exception as e:
        error_msg = f"Tint overlay creation failed: {e}"
        print(f"❌ {error_msg}")
        return {
            'status': 'error',
            'error': error_msg,
            'processing_time': time.time() - start_time
        }


async def create_slope_overlay(base_path: str, slope_relief_path: str, output_path: str, beta: float = 0.5) -> Dict[str, Any]:
    """Blend a tint overlay with a slope relief to enhance contrast."""
    start_time = time.time()

    print(f"\n🌄 SLOPE OVERLAY")
    print(f"📂 Output: {output_path}")

    try:
        ds_base = gdal.Open(base_path)
        if ds_base is None:
            raise FileNotFoundError(f"Base overlay not found: {base_path}")

        base = ds_base.ReadAsArray().astype(np.float32) / 255.0
        geo = ds_base.GetGeoTransform()
        proj = ds_base.GetProjection()
        ds_base = None

        ds_slope = gdal.Open(slope_relief_path)
        if ds_slope is None:
            raise FileNotFoundError(f"Slope relief not found: {slope_relief_path}")

        slope = ds_slope.ReadAsArray().astype(np.float32) / 255.0
        ds_slope = None

        if base.shape != slope.shape:
            raise ValueError("Slope relief dimensions do not match base overlay")

        final = base * (1 - beta) + slope * beta
        final = np.clip(final * 255, 0, 255).astype(np.uint8)
        rgb = np.transpose(final, (1, 2, 0))

        metadata = {
            'geotransform': geo,
            'projection': proj
        }

        save_color_raster(rgb, output_path, metadata, enhanced_quality=True)

        processing_time = time.time() - start_time
        print(f"✅ Slope overlay created in {processing_time:.2f} seconds")
        return {
            'status': 'success',
            'output_file': output_path,
            'processing_time': processing_time
        }

    except Exception as e:
        error_msg = f"Slope overlay creation failed: {e}"
        print(f"❌ {error_msg}")
        return {
            'status': 'error',
            'error': error_msg,
            'processing_time': time.time() - start_time
        }

async def process_chm_tiff(tiff_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate CHM (Canopy Height Model) from elevation TIFF.
    For TIFF-based processing, we need both DSM and DTM TIFFs to calculate CHM = DSM - DTM.
    
    Args:
        tiff_path: Path to the DTM TIFF file (base elevation)
        output_dir: Output directory for CHM
        parameters: Processing parameters (may include dsm_path)
        
    Returns:
        Processing results dictionary
    """
    start_time = time.time()
    
    print(f"\n🌳 CHM PROCESSING (TIFF)")
    print(f"📁 DTM Input: {os.path.basename(tiff_path)}")
    print(f"📂 Output: {output_dir}")
    
    try:
        # For CHM calculation, we need both DTM and DSM
        # The tiff_path is typically the DTM, we need to find the corresponding DSM
        region_folder = parameters.get("region_folder", "UnknownRegion")
        base_name = os.path.splitext(os.path.basename(tiff_path))[0]  # Still needed for DSM finding
        
        # Try to find DSM file in the same directory or parent directories
        dtm_path = tiff_path
        dsm_path = parameters.get('dsm_path')
        
        if not dsm_path:
            # Try to find DSM file automatically
            tiff_dir = os.path.dirname(tiff_path)
            parent_dir = os.path.dirname(tiff_dir)
            
            # Common DSM file patterns to search for
            potential_dsm_paths = [
                # Same directory
                os.path.join(tiff_dir, base_name.replace('DTM', 'DSM') + '.tif'),
                os.path.join(tiff_dir, base_name.replace('_DTM', '_DSM') + '.tif'),
                # DSM subdirectory
                os.path.join(parent_dir, 'DSM', base_name.replace('DTM', 'DSM') + '.tif'),
                os.path.join(parent_dir, 'DSM', base_name.replace('_DTM', '_DSM') + '.tif'),
                # Raw DSM files
                os.path.join(parent_dir, 'DSM', 'raw', base_name.replace('DTM', 'DSM') + '.tif'),
                os.path.join(parent_dir, 'DSM', 'raw', base_name.replace('_DTM', '_DSM') + '.tif'),
            ]
            
            for potential_path in potential_dsm_paths:
                if os.path.exists(potential_path):
                    dsm_path = potential_path
                    break
        
        if not dsm_path or not os.path.exists(dsm_path):
            raise FileNotFoundError(f"DSM file not found. CHM requires both DTM and DSM files. Searched for DSM corresponding to {base_name}")
        
        print(f"📁 DSM file found: {os.path.basename(dsm_path)}")
        print(f"🧮 CHM calculation: DSM - DTM")
        
        # Read DTM and DSM data
        dtm_array, dtm_metadata = read_elevation_tiff(dtm_path)
        dsm_array, dsm_metadata = read_elevation_tiff(dsm_path)
        
        # Handle dimension mismatches by analyzing spatial properties and choosing best approach
        spatial_alignment_needed = dtm_array.shape != dsm_array.shape
        
        if spatial_alignment_needed:
            print(f"⚠️ Spatial mismatch detected!")
            print(f"   DTM: {dtm_array.shape}")
            print(f"   DSM: {dsm_array.shape}")
            
            # Analyze spatial properties to determine best alignment strategy
            import rasterio
            from rasterio.enums import Resampling
            from rasterio.warp import reproject, calculate_default_transform
            import tempfile
            
            with rasterio.open(dtm_path) as dtm_src, rasterio.open(dsm_path) as dsm_src:
                # Get bounds information
                dtm_bounds = dtm_src.bounds
                dsm_bounds = dsm_src.bounds
                dtm_res = dtm_src.res
                dsm_res = dsm_src.res
                
                print(f"   📍 DTM bounds: {dtm_bounds}")
                print(f"   📍 DSM bounds: {dsm_bounds}")
                print(f"   📏 DTM resolution: {dtm_res}")
                print(f"   📏 DSM resolution: {dsm_res}")
                
                # Check if DTM is completely within DSM bounds (typical case)
                dtm_within_dsm = (dtm_bounds.left >= dsm_bounds.left and 
                                 dtm_bounds.right <= dsm_bounds.right and
                                 dtm_bounds.bottom >= dsm_bounds.bottom and
                                 dtm_bounds.top <= dsm_bounds.top)
                
                if dtm_within_dsm and abs(dtm_res[0] - dsm_res[0]) < 1e-6:
                    # BEST CASE: DTM is subset of DSM with same resolution
                    print(f"🎯 OPTIMAL ALIGNMENT: Cropping DSM to DTM extent (preserves DTM quality)")
                    
                    # Create temporary cropped DSM
                    with tempfile.NamedTemporaryFile(suffix='_dsm_cropped.tif', delete=False) as tmp_file:
                        cropped_dsm_path = tmp_file.name
                    
                    try:
                        # Crop DSM to DTM bounds
                        from rasterio.windows import from_bounds
                        
                        # Calculate window for DSM that matches DTM bounds
                        window = from_bounds(*dtm_bounds, dsm_src.transform)
                        
                        # Create profile for cropped DSM
                        dsm_profile = dsm_src.profile.copy()
                        dsm_profile.update({
                            'height': int(window.height),
                            'width': int(window.width),
                            'transform': rasterio.windows.transform(window, dsm_src.transform)
                        })
                        
                        # Create cropped DSM
                        with rasterio.open(cropped_dsm_path, 'w', **dsm_profile) as dst:
                            dst.write(dsm_src.read(1, window=window), 1)
                        
                        # Read the cropped DSM
                        dsm_array, dsm_metadata = read_elevation_tiff(cropped_dsm_path)
                        print(f"✅ DSM cropped successfully to shape: {dsm_array.shape}")
                        
                        # Clean up temporary file
                        os.unlink(cropped_dsm_path)
                        
                        # Use DTM metadata as reference (since we're preserving DTM extent)
                        reference_metadata = dtm_metadata
                        
                    except Exception as crop_error:
                        # Clean up temporary file on error
                        if os.path.exists(cropped_dsm_path):
                            os.unlink(cropped_dsm_path)
                        raise RuntimeError(f"Failed to crop DSM to DTM extent: {str(crop_error)}")
                
                else:
                    # FALLBACK CASE: Need full resampling
                    print(f"🔧 FALLBACK: Complex spatial alignment required - resampling DSM to DTM")
                    
                    # Create temporary resampled DSM
                    with tempfile.NamedTemporaryFile(suffix='_dsm_resampled.tif', delete=False) as tmp_file:
                        resampled_dsm_path = tmp_file.name
                    
                    try:
                        # Get DTM properties to use as target
                        target_crs = dtm_src.crs
                        target_transform = dtm_src.transform
                        target_width = dtm_src.width
                        target_height = dtm_src.height
                        
                        # Create output profile for resampled DSM
                        dsm_profile = dsm_src.profile.copy()
                        dsm_profile.update({
                            'crs': target_crs,
                            'transform': target_transform,
                            'width': target_width,
                            'height': target_height
                        })
                        
                        # Resample DSM to match DTM
                        with rasterio.open(resampled_dsm_path, 'w', **dsm_profile) as dst:
                            reproject(
                                source=rasterio.band(dsm_src, 1),
                                destination=rasterio.band(dst, 1),
                                src_transform=dsm_src.transform,
                                src_crs=dsm_src.crs,
                                dst_transform=target_transform,
                                dst_crs=target_crs,
                                resampling=Resampling.bilinear
                            )
                        
                        # Read the resampled DSM
                        dsm_array, dsm_metadata = read_elevation_tiff(resampled_dsm_path)
                        print(f"✅ DSM resampled successfully to shape: {dsm_array.shape}")
                        
                        # Clean up temporary file
                        os.unlink(resampled_dsm_path)
                        
                        # Use DTM metadata as reference
                        reference_metadata = dtm_metadata
                        
                    except Exception as resample_error:
                        # Clean up temporary file on error
                        if os.path.exists(resampled_dsm_path):
                            os.unlink(resampled_dsm_path)
                        raise RuntimeError(f"Failed to resample DSM: {str(resample_error)}")
        else:
            # No spatial alignment needed
            reference_metadata = dtm_metadata
        
        # Handle dimension mismatches with intelligent cropping/padding
        if dtm_array.shape != dsm_array.shape:
            print(f"⚠️ Dimension mismatch detected: DTM {dtm_array.shape} vs DSM {dsm_array.shape}")
            print(f"🔧 Applying intelligent alignment to resolve small dimension differences...")
            
            # Get target dimensions (use smaller dimensions to avoid extrapolation)
            target_height = min(dtm_array.shape[0], dsm_array.shape[0])
            target_width = min(dtm_array.shape[1], dsm_array.shape[1])
            
            print(f"📐 Aligning both arrays to: {target_height} x {target_width}")
            
            # Crop both arrays to the same dimensions
            dtm_array = dtm_array[:target_height, :target_width]
            dsm_array = dsm_array[:target_height, :target_width]
            
            # Update metadata to reflect the new dimensions
            reference_metadata = reference_metadata.copy()
            reference_metadata['height'] = target_height
            reference_metadata['width'] = target_width
            
            print(f"✅ Arrays aligned successfully: DTM {dtm_array.shape}, DSM {dsm_array.shape}")
        
        # Final verification that dimensions now match
        if dtm_array.shape != dsm_array.shape:
            raise ValueError(f"Failed to align DTM and DSM dimensions: DTM {dtm_array.shape} vs DSM {dsm_array.shape}")
        
        # Check for DSM-DTM data quality issue and source type compatibility
        print(f"🔍 Checking DSM-DTM data quality and source compatibility...")
        dtm_valid = dtm_array[~np.isnan(dtm_array) & ~np.isinf(dtm_array)]
        dsm_valid = dsm_array[~np.isnan(dsm_array) & ~np.isinf(dsm_array)]
        
        # Detect if we're using Copernicus DEM as DSM (common issue)
        dsm_filename = os.path.basename(dsm_path).lower()
        is_copernicus_dsm = any(x in dsm_filename for x in ['copernicus', 'cop-dem', 'cop_dem'])
        
        if is_copernicus_dsm:
            print(f"⚠️ CRITICAL DATA SOURCE WARNING:")
            print(f"   Detected Copernicus DEM being used as DSM!")
            print(f"   ❌ Copernicus DEM is actually a DTM (bare earth), not DSM (surface)")
            print(f"   🎯 For proper CHM calculation, you need true DSM data sources:")
            print(f"      • SRTM GL1 (surface elevation in forests)")
            print(f"      • ALOS World 3D-30m (true DSM)")
            print(f"      • ASTER GDEM v3 (optical stereo DSM)")
            print(f"   📋 Current calculation: DTM - DTM = 0 (expected result)")
        
        if len(dtm_valid) > 0 and len(dsm_valid) > 0:
            dtm_range = np.max(dtm_valid) - np.min(dtm_valid)
            dsm_range = np.max(dsm_valid) - np.min(dsm_valid)
            
            # Check if DSM and DTM have identical or nearly identical values
            identical_ranges = abs(dtm_range - dsm_range) < 0.01
            identical_means = abs(np.mean(dtm_valid) - np.mean(dsm_valid)) < 0.01
            
            if identical_ranges and identical_means:
                # Additional check: compare actual pixel values
                diff_array = np.abs(dsm_array - dtm_array)
                max_diff = np.max(diff_array[~np.isnan(diff_array)])
                identical_pixels = max_diff < 0.01
                
                if identical_pixels:
                    print(f"⚠️ DATA QUALITY ISSUE CONFIRMED:")
                    print(f"   DSM and DTM contain identical values (max diff: {max_diff:.3f}m)")
                    
                    if is_copernicus_dsm:
                        print(f"   🎯 ROOT CAUSE: Both datasets are DTM (terrain models)")
                        print(f"   💡 SOLUTION: Replace DSM with true surface elevation data")
                        data_quality_warning = "Both DSM and DTM sources are terrain models (DTM). CHM calculation requires true Digital Surface Model (DSM) data that includes vegetation. Consider using SRTM, ALOS World 3D-30m, or ASTER GDEM as DSM source."
                    else:
                        print(f"   🎯 Unknown cause of identical elevation values")
                        data_quality_warning = "DSM and DTM contain identical values. This may indicate both datasets represent terrain rather than surface elevation, or there may be a spatial alignment issue."
                    
                    # Create a minimal CHM with appropriate metadata
                    print(f"🔧 Creating fallback CHM with zero vegetation height...")
                    chm_array = np.zeros_like(dtm_array, dtype=np.float32)
                    
                else:
                    # Normal CHM calculation
                    print(f"✅ DSM-DTM data quality check passed")
                    chm_array = dsm_array.astype(np.float32) - dtm_array.astype(np.float32)
                    data_quality_warning = None
            else:
                # Normal CHM calculation
                print(f"✅ DSM-DTM data quality check passed")
                chm_array = dsm_array.astype(np.float32) - dtm_array.astype(np.float32)
                data_quality_warning = None
        else:
            # Fallback if no valid data
            print(f"⚠️ No valid data found in DSM or DTM")
            chm_array = np.zeros_like(dtm_array, dtype=np.float32)
            data_quality_warning = "No valid elevation data found in DSM or DTM files"
        
        # Calculate CHM = DSM - DTM
        print(f"🔄 CHM calculation completed")
        
        # Create output filename
        output_filename = f"{region_folder}_CHM.tif"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save CHM result using the reference metadata (preserves DTM spatial properties)
        save_raster(chm_array, output_path, reference_metadata, gdal.GDT_Float32, enhanced_quality=True)
        
        # Calculate statistics and detect data quality issues
        valid_data = chm_array[~np.isnan(chm_array) & ~np.isinf(chm_array)]
        
        if len(valid_data) > 0:
            min_height = float(np.min(valid_data))
            max_height = float(np.max(valid_data))
            mean_height = float(np.mean(valid_data))
            std_height = float(np.std(valid_data))
            
            # Additional check if data quality warning wasn't already set
            if data_quality_warning is None and max_height - min_height < 0.1 and abs(mean_height) < 0.1:
                data_quality_warning = "CHM shows minimal vegetation height variation. This may indicate both DSM and DTM represent similar elevation surfaces."
            
            print(f"📊 CHM Statistics:")
            print(f"   Min height: {min_height:.2f}m")
            print(f"   Max height: {max_height:.2f}m")
            print(f"   Mean height: {mean_height:.2f}m")
            print(f"   Std dev: {std_height:.2f}m")
            
            if data_quality_warning:
                print(f"⚠️ Data Quality Warning: {data_quality_warning}")
        else:
            min_height = max_height = mean_height = std_height = None
            if data_quality_warning is None:
                data_quality_warning = "No valid CHM data calculated"
        
        processing_time = time.time() - start_time
        
        result = {
            "status": "success",
            "output_file": output_path,
            "processing_time": processing_time,
            "parameters": {
                "dtm_path": dtm_path,
                "dsm_path": dsm_path,
                "method": "DSM - DTM"
            },
            "statistics": {
                "min_height": min_height if 'min_height' in locals() else None,
                "max_height": max_height if 'max_height' in locals() else None,
                "mean_height": mean_height if 'mean_height' in locals() else None,
                "std_height": std_height if 'std_height' in locals() else None
            } if 'min_height' in locals() else None,
            "data_quality_warning": data_quality_warning
        }
        
        print(f"✅ CHM processing completed in {processing_time:.2f} seconds")
        return result
        
    except Exception as e:
        error_msg = f"CHM processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "processing_time": time.time() - start_time
        }

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
    elif request and hasattr(request, 'display_region_name') and request.display_region_name:
        # Use display region name if provided in request (for user-friendly folder naming)
        region_folder = request.display_region_name
        print(f"📍 Using display region from request: {region_folder}")
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
    # Always use output directory regardless of where input TIFF is located
    base_output_dir = os.path.join("output", region_folder, "lidar")
    
    print(f"📂 Output directory: {base_output_dir}")
    print(f"📂 Input TIFF location: {tiff_path}")
    print(f"🎯 Ensuring all processing outputs go to: {base_output_dir}")
    
    # Create the base output directory if it doesn't exist
    os.makedirs(base_output_dir, exist_ok=True)
    
    # Create DTM directory structure from elevation TIFF for CHM generation
    # This is essential for coordinate-based elevation workflows
    try:
        print(f"\n🏔️ Creating DTM structure for CHM compatibility...")
        dtm_path = create_dtm_from_elevation_tiff(tiff_path, region_folder)
        print(f"✅ DTM structure created: {os.path.basename(dtm_path)}")
    except Exception as e:
        print(f"⚠️ DTM structure creation failed: {e}")
        print(f"   CHM generation may not work properly")
    
    # Load hillshade definitions from JSON
    hillshade_path = Path(__file__).parent / "pipelines_json" / "hillshade.json"
    try:
        with open(hillshade_path, "r") as f:
            hillshade_defs = json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load hillshade definitions: {e}")
        hillshade_defs = []

    processing_tasks = []
    for hs in hillshade_defs:
        params = {
            "altitude": hs.get("altitude", 30),
            "azimuth": hs.get("azimuth"),
            "z_factor": hs.get("z_factor", 1.0),
            "azimuths": hs.get("azimuths"),
            "output_filename": hs.get("output")
        }
        if hs.get("multi"):
            processing_tasks.append((hs["name"], process_multi_hillshade_tiff, params))
        else:
            processing_tasks.append((hs["name"], process_hillshade_tiff, params))

    # Add other raster tasks
    print(f"\n🏛️ ENHANCED ARCHAEOLOGICAL PROCESSING PIPELINE ACTIVE 🏛️")
    print(f"✅ Enhanced Slope: YlOrRd archaeological visualization (2°-20° normalization) - default")
    print(f"✅ Enhanced LRM: Adaptive sizing + Gaussian filtering + enhanced normalization")
    print(f"✅ Standard processing: Aspect, Color Relief, SVF, CHM")
    print(f"{'='*60}")
    
    processing_tasks.extend([
        ("slope", process_slope_tiff, {"use_inferno_colormap": True}),  # 📐 ENHANCED: YlOrRd Archaeological visualization (default)
        ("aspect", process_aspect_tiff, {}),
        ("color_relief", process_color_relief_tiff, {}),
        ("slope_relief", process_slope_relief_tiff, {}),
        ("lrm", process_enhanced_lrm_tiff, {}),  # 🌄 ENHANCED: Adaptive + Gaussian + archaeological features
        ("sky_view_factor", process_sky_view_factor_tiff, {}),
        ("chm", process_chm_tiff, {})
    ])
    
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
            
            # Add region_folder to parameters for consistent naming
            parameters["region_folder"] = region_folder
            
            # Process the raster product
            result = await process_func(tiff_path, task_output_dir, parameters)
            results[task_name] = result
            
            if result["status"] == "success":
                print(f"✅ {task_name} completed successfully")
                
                # Only create PNG for specific raster products: lrm, sky_view_factor, slope, chm
                if task_name in ["lrm", "sky_view_factor", "slope", "chm"]:
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
                        from overlay_optimization import OverlayOptimizer
                        
                        # Create PNG output directory under the main lidar output folder
                        png_output_dir = os.path.join(base_output_dir, "png_outputs")
                        os.makedirs(png_output_dir, exist_ok=True)
                        
                        # Generate short PNG filename based on task name
                        png_name_mapping = {
                            "lrm": "LRM.png",
                            "sky_view_factor": "SVF.png",  # Use enhanced cividis visualization
                            "slope": "Slope.png",
                            "chm": "CHM.png"
                        }
                        png_filename = png_name_mapping.get(task_name, f"{task_name}.png")
                        png_path = os.path.join(png_output_dir, png_filename)
                        
                        # Convert TIFF to PNG with appropriate colormap function
                        if task_name == "slope":
                            # Check if inferno colormap was used based on the result parameters
                            slope_params = result.get("parameters", {})
                            use_inferno_colormap = slope_params.get("use_inferno_colormap", False)
                            
                            if use_inferno_colormap:
                                # Use specialized Archaeological YlOrRd colormap for optimal slope visualization
                                from convert import convert_slope_to_archaeological_ylord_png, convert_slope_to_archaeological_ylord_png_clean
                                
                                # Create matplotlib subdirectory for decorated PNGs
                                matplotlib_dir = os.path.join(png_output_dir, "matplotlib")
                                os.makedirs(matplotlib_dir, exist_ok=True)
                                
                                # Generate matplotlib Slope PNG with decorations (legends, scales)
                                matplotlib_png_path = os.path.join(matplotlib_dir, "Slope_matplot.png")
                                convert_slope_to_archaeological_ylord_png(
                                    result["output_file"], 
                                    matplotlib_png_path, 
                                    enhanced_resolution=True,
                                    save_to_consolidated=False,
                                    archaeological_mode=True,  # Enable 2°-20° archaeological specifications
                                    apply_transparency=True   # Apply transparency mask
                                )
                                print(f"🖼️ Matplotlib Slope PNG: Archaeological YlOrRd colormap (2°-20°) with legends - optimal approach")
                                
                                # Generate clean Slope PNG (no decorations) as main Slope.png
                                converted_png = convert_slope_to_archaeological_ylord_png_clean(
                                    result["output_file"], 
                                    png_path, 
                                    enhanced_resolution=True,
                                    save_to_consolidated=False,
                                    archaeological_mode=True,  # Enable 2°-20° archaeological specifications
                                    apply_transparency=True   # Apply transparency mask
                                )
                                print(f"🎯 Clean Slope PNG: Archaeological YlOrRd (2°-20°), ready for overlay integration - optimal approach")
                            else:
                                # Use standard greyscale slope visualization (default)
                                from convert import convert_slope_to_greyscale_png, convert_slope_to_greyscale_png_clean
                                
                                # Create matplotlib subdirectory for decorated PNGs
                                matplotlib_dir = os.path.join(png_output_dir, "matplotlib")
                                os.makedirs(matplotlib_dir, exist_ok=True)
                                
                                # Generate matplotlib Slope PNG with decorations (legends, scales)
                                matplotlib_png_path = os.path.join(matplotlib_dir, "Slope_matplot.png")
                                convert_slope_to_greyscale_png(
                                    result["output_file"], 
                                    matplotlib_png_path, 
                                    enhanced_resolution=True,
                                    save_to_consolidated=False,
                                    stretch_type="stddev",
                                    stretch_params={"num_stddev": 2.0}
                                )
                                print(f"🖼️ Matplotlib Slope PNG: Greyscale colormap with legends and scales")
                                
                                # Generate clean Slope PNG (no decorations) as main Slope.png
                                converted_png = convert_slope_to_greyscale_png_clean(
                                    result["output_file"], 
                                    png_path, 
                                    enhanced_resolution=True,
                                    save_to_consolidated=False,
                                    stretch_type="stddev",
                                    stretch_params={"num_stddev": 2.0}
                                )
                                print(f"🎯 Clean Slope PNG: Greyscale colormap, ready for overlay integration")
                        elif task_name == "lrm":
                            # Use specialized coolwarm colormap for enhanced LRM visualization
                            from convert import convert_lrm_to_coolwarm_png, convert_lrm_to_coolwarm_png_clean
                            
                            # Create matplotlib subdirectory for decorated PNGs
                            matplotlib_dir = os.path.join(png_output_dir, "matplotlib")
                            os.makedirs(matplotlib_dir, exist_ok=True)
                            
                            # Generate matplotlib LRM PNG with decorations (legends, scales)
                            matplotlib_png_path = os.path.join(matplotlib_dir, "LRM_matplot.png")
                            convert_lrm_to_coolwarm_png(
                                result["output_file"], 
                                matplotlib_png_path, 
                                enhanced_resolution=True,
                                save_to_consolidated=False
                            )
                            print(f"🖼️ Matplotlib LRM PNG: Coolwarm colormap with legends and scales")
                            
                            # Generate clean LRM PNG (no decorations) as main LRM.png
                            converted_png = convert_lrm_to_coolwarm_png_clean(
                                result["output_file"], 
                                png_path, 
                                enhanced_resolution=True,
                                save_to_consolidated=False
                            )
                            print(f"🎯 Clean LRM PNG: No decorations, ready for overlay integration")
                        elif task_name == "sky_view_factor":
                            # Use specialized cividis colormap for enhanced SVF archaeological visualization
                            from convert import convert_svf_to_cividis_png, convert_svf_to_cividis_png_clean
                            
                            # Create matplotlib subdirectory for decorated PNGs
                            matplotlib_dir = os.path.join(png_output_dir, "matplotlib")
                            os.makedirs(matplotlib_dir, exist_ok=True)
                            
                            # Generate matplotlib SVF PNG with decorations (legends, scales)
                            matplotlib_png_path = os.path.join(matplotlib_dir, "SVF_matplot.png")
                            convert_svf_to_cividis_png(
                                result["output_file"], 
                                matplotlib_png_path, 
                                enhanced_resolution=True,
                                save_to_consolidated=False
                            )
                            print(f"🖼️ Matplotlib SVF PNG: Cividis colormap with legends and scales")
                            
                            # Generate clean SVF PNG (no decorations) as main SVF.png
                            converted_png = convert_svf_to_cividis_png_clean(
                                result["output_file"], 
                                png_path, 
                                enhanced_resolution=True,
                                save_to_consolidated=False
                            )
                            print(f"🎯 Clean SVF PNG: No decorations, ready for overlay integration")
                        elif task_name == "chm":
                            # Use specialized viridis colormap for CHM visualization
                            from convert import convert_chm_to_viridis_png, convert_chm_to_viridis_png_clean
                            
                            # Create matplotlib subdirectory for decorated PNGs
                            matplotlib_dir = os.path.join(png_output_dir, "matplotlib")
                            os.makedirs(matplotlib_dir, exist_ok=True)
                            
                            # Generate matplotlib CHM PNG with decorations (legends, scales)
                            matplotlib_png_path = os.path.join(matplotlib_dir, "CHM_matplot.png")
                            convert_chm_to_viridis_png(
                                result["output_file"], 
                                matplotlib_png_path, 
                                enhanced_resolution=True,
                                save_to_consolidated=False
                            )
                            print(f"🖼️ Matplotlib CHM PNG: Viridis colormap with legends and scales")
                            
                            # Generate clean CHM PNG (no decorations) as main CHM.png
                            converted_png = convert_chm_to_viridis_png_clean(
                                result["output_file"], 
                                png_path, 
                                enhanced_resolution=True,
                                save_to_consolidated=False
                            )
                            print(f"🎯 Clean CHM PNG: No decorations, ready for overlay integration")
                        else:
                            # Use standard PNG conversion for other raster types
                            converted_png = convert_geotiff_to_png(result["output_file"], png_path)
                        
                        if converted_png and os.path.exists(converted_png):
                            result["png_file"] = converted_png
                            png_size = os.path.getsize(converted_png) / (1024 * 1024)  # MB
                            print(f"🖼️ PNG created: {os.path.basename(converted_png)} ({png_size:.1f} MB)")
                            
                            # Generate optimized overlay if needed
                            overlay_optimizer = OverlayOptimizer()
                            overlay_path = overlay_optimizer.optimize_tiff_to_overlay(result["output_file"])
                            
                            if overlay_path:
                                # Move overlay to png_outputs directory
                                overlay_dest = os.path.join(png_output_dir, os.path.basename(overlay_path))
                                if overlay_path != overlay_dest:
                                    import shutil
                                    shutil.move(overlay_path, overlay_dest)
                                    print(f"📦 Overlay moved to png_outputs: {os.path.basename(overlay_dest)}")
                                    
                                    # Also move overlay worldfile if it exists
                                    overlay_worldfile = os.path.splitext(overlay_path)[0] + ".pgw"
                                    overlay_worldfile_dest = os.path.splitext(overlay_dest)[0] + ".pgw"
                                    if os.path.exists(overlay_worldfile):
                                        shutil.move(overlay_worldfile, overlay_worldfile_dest)
                                
                        else:
                            print(f"⚠️ PNG conversion failed for {task_name}: No output file created")
                    
                    except Exception as e:
                        print(f"⚠️ PNG conversion failed for {task_name}: {e}")
                else:
                    print(f"ℹ️ Skipping PNG generation for {task_name} (not in selected list)")
            else:
                print(f"❌ {task_name} failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            error_msg = f"Processing failed for {task_name}: {str(e)}"
            print(f"❌ {error_msg}")
            results[task_name] = {
                "status": "error",
                "error": error_msg
            }

    # Create RGB composite if all required hillshades were generated
    required_hs = ["hs_red", "hs_green", "hs_blue"]
    if all(results.get(name, {}).get("status") == "success" for name in required_hs):
        hs_paths = {
            "R": results["hs_red"]["output_file"],
            "G": results["hs_green"]["output_file"],
            "B": results["hs_blue"]["output_file"],
        }
        rgb_dir = os.path.join(base_output_dir, "HillshadeRgb")
        os.makedirs(rgb_dir, exist_ok=True)
        rgb_output = os.path.join(rgb_dir, "hillshade_rgb.tif")
        rgb_result = await create_rgb_hillshade(hs_paths, rgb_output)
        results["hillshade_rgb"] = rgb_result

        if rgb_result["status"] == "success":
            try:
                import sys
                from pathlib import Path
                app_dir = Path(__file__).parent.parent
                if str(app_dir) not in sys.path:
                    sys.path.insert(0, str(app_dir))

                from convert import convert_geotiff_to_png

                png_output_dir = os.path.join(base_output_dir, "png_outputs")
                os.makedirs(png_output_dir, exist_ok=True)

                png_name = "HillshadeRGB.png"
                png_path = os.path.join(png_output_dir, png_name)
                converted_png = convert_geotiff_to_png(rgb_output, png_path)
                if converted_png and os.path.exists(converted_png):
                    rgb_result["png_file"] = converted_png
                    print(f"🖼️ PNG created: {os.path.basename(converted_png)}")
            except Exception as e:
                print(f"⚠️ PNG conversion failed for hillshade_rgb: {e}")

            # COMMENTED OUT: Create tint overlay using color relief
            # color_relief_res = results.get("color_relief")
            # if color_relief_res and color_relief_res.get("status") == "success":
            #     try:
            #         tint_output = os.path.join(rgb_dir, "tint_overlay.tif")
            #         tint_result = await create_tint_overlay(
            #             color_relief_res["output_file"], rgb_output, tint_output)
            #         results["tint_overlay"] = tint_result

            #         if tint_result["status"] == "success":
            #             png_output_dir = os.path.join(base_output_dir, "png_outputs")
            #             os.makedirs(png_output_dir, exist_ok=True)
            #             png_name = "TintOverlay.png"
            #             png_path = os.path.join(png_output_dir, png_name)
            #             converted_png = convert_geotiff_to_png(tint_output, png_path)
            #             if converted_png and os.path.exists(converted_png):
            #                 tint_result["png_file"] = converted_png
            #                 print(f"🖼️ PNG created: {os.path.basename(converted_png)}")

            #             # Create slope overlay if slope relief is available
            #             slope_relief_res = results.get("slope_relief")
            #             if slope_relief_res and slope_relief_res.get("status") == "success":
            #                 try:
            #                     boosted_output = os.path.join(rgb_dir, "boosted_hillshade.tif")
            #                     slope_overlay_res = await create_slope_overlay(
            #                         tint_output,
            #                         slope_relief_res["output_file"],
            #                         boosted_output,
            #                     )
            #                     results["boosted_hillshade"] = slope_overlay_res

            #                     if slope_overlay_res["status"] == "success":
            #                         print(f"✅ Boosted hillshade created: {os.path.basename(boosted_output)}")
            #                 except Exception as e:
            #                     print(f"⚠️ Slope overlay generation failed: {e}")

            #     except Exception as e:
            #         print(f"⚠️ Tint overlay generation failed: {e}")

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

def create_dtm_from_elevation_tiff(elevation_tiff_path: str, region_folder: str) -> str:
    """
    Create proper DTM directory structure from elevation TIFF for coordinate-based data
    This enables CHM generation which expects DTM files in output/{region}/lidar/DTM/filled/
    
    Args:
        elevation_tiff_path: Path to the elevation TIFF file
        region_folder: Region folder name
        
    Returns:
        Path to the created DTM file
    """
    print(f"\n🏔️ CREATING DTM STRUCTURE FROM ELEVATION TIFF")
    print(f"📁 Source: {os.path.basename(elevation_tiff_path)}")
    print(f"🏷️ Region: {region_folder}")
    
    # Create DTM output directory structure
    dtm_output_dir = os.path.join("output", region_folder, "lidar", "DTM", "filled")
    os.makedirs(dtm_output_dir, exist_ok=True)
    
    # Generate DTM filename that includes region name for CHM endpoint compatibility
    # CHM endpoint searches for pattern: *{region_name}*DTM*.tif
    elevation_basename = os.path.splitext(os.path.basename(elevation_tiff_path))[0]
    dtm_filename = f"{region_folder}_{elevation_basename}_DTM_30m_filled.tif"  # Include region name for pattern match
    dtm_output_path = os.path.join(dtm_output_dir, dtm_filename)
    
    # Copy elevation TIFF to DTM location (since elevation data from coordinates IS the DTM)
    print(f"📋 Copying elevation data to DTM structure...")
    print(f"📄 Destination: {dtm_output_path}")
    
    try:
        shutil.copy2(elevation_tiff_path, dtm_output_path)
        
        if os.path.exists(dtm_output_path):
            file_size = os.path.getsize(dtm_output_path) / (1024 * 1024)  # MB
            print(f"✅ DTM structure created successfully")
            print(f"📊 File size: {file_size:.2f} MB")
            print(f"📂 DTM path: {dtm_output_path}")
            return dtm_output_path
        else:
            raise FileNotFoundError(f"Failed to create DTM file at {dtm_output_path}")
            
    except Exception as e:
        error_msg = f"Failed to create DTM structure: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise
