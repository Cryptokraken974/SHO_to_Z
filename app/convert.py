from osgeo import gdal, osr
import os
import time
from typing import Optional, Dict, Tuple # Added Dict and Tuple
import base64
import subprocess
import numpy as np # Added numpy
import logging
import tempfile # Added tempfile for base64 conversion temp file
from pathlib import Path # Added pathlib for Sentinel-2 processing
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PIL import Image

logger = logging.getLogger(__name__)

# Configure GDAL to prevent auxiliary file creation for PNG files
gdal.SetConfigOption('GDAL_PAM_ENABLED', 'NO')

def create_wgs84_world_file(original_world_file: str, tiff_path: str, png_path: str) -> bool:
    """
    Create a WGS84 world file for PNG overlay using the original LAZ request bounds.
    Instead of using GDAL's projected coordinates, this function reads the original
    LAZ request bounds from metadata.txt to ensure overlays match the original area.
    
    Args:
        original_world_file: Path to the original world file (in projected coordinates)
        tiff_path: Path to the source TIFF file (for image dimensions)
        png_path: Path to the PNG file (for output world file naming)
    
    Returns:
        True if WGS84 world file was created successfully
    """
    try:
        # First, try to find and read the original LAZ request bounds from metadata.txt
        print(f"🎯 Using original LAZ request bounds for world file generation...")
        
        # Extract region name from file path to find metadata.txt
        region_name = None
        path_parts = tiff_path.split(os.sep)
        if "output" in path_parts:
            output_idx = path_parts.index("output")
            if output_idx + 1 < len(path_parts):
                region_name = path_parts[output_idx + 1]
        
        if not region_name:
            print(f"❌ Could not extract region name from path: {tiff_path}")
            return False
            
        # Read metadata.txt for original request bounds
        metadata_path = os.path.join("output", region_name, "metadata.txt")
        if not os.path.exists(metadata_path):
            print(f"❌ No metadata.txt found at: {metadata_path}")
            return False
            
        print(f"📄 Reading original request bounds from: {metadata_path}")
        
        # Parse metadata.txt for bounds
        bounds = {}
        with open(metadata_path, 'r') as f:
            for line in f:
                line = line.strip()
                if 'North Bound:' in line:
                    bounds['north'] = float(line.split(':')[1].strip())
                elif 'South Bound:' in line:
                    bounds['south'] = float(line.split(':')[1].strip())
                elif 'East Bound:' in line:
                    bounds['east'] = float(line.split(':')[1].strip())
                elif 'West Bound:' in line:
                    bounds['west'] = float(line.split(':')[1].strip())
        
        if len(bounds) != 4:
            print(f"❌ Could not parse all bounds from metadata.txt")
            return False
            
        print(f"✅ Original LAZ request bounds:")
        print(f"   North: {bounds['north']:.8f}°")
        print(f"   South: {bounds['south']:.8f}°") 
        print(f"   East: {bounds['east']:.8f}°")
        print(f"   West: {bounds['west']:.8f}°")
        
        # Get image dimensions from TIFF
        ds = gdal.Open(tiff_path)
        if not ds:
            print(f"❌ Could not open TIFF: {tiff_path}")
            return False
            
        width = ds.RasterXSize
        height = ds.RasterYSize
        ds = None
        
        # Calculate pixel sizes using original LAZ request bounds
        width_degrees = abs(bounds['east'] - bounds['west'])
        height_degrees = abs(bounds['north'] - bounds['south'])
        
        pixel_size_x_wgs84 = width_degrees / width
        pixel_size_y_wgs84 = -height_degrees / height  # Negative for standard image coordinate system
        
        # Upper left corner coordinates
        ul_lon = bounds['west']
        ul_lat = bounds['north']
        
        print(f"🌍 Calculated world file parameters:")
        print(f"   Upper left longitude: {ul_lon:.8f}°")
        print(f"   Upper left latitude: {ul_lat:.8f}°")
        print(f"   Pixel size X (longitude): {pixel_size_x_wgs84:.10f}°")
        print(f"   Pixel size Y (latitude): {pixel_size_y_wgs84:.10f}°")
        print(f"   Image size: {width} × {height} pixels")
        
        # Create WGS84 world file
        wgs84_world_file = os.path.splitext(png_path)[0] + "_wgs84.wld"
        
        with open(wgs84_world_file, 'w') as f:
            f.write(f"{pixel_size_x_wgs84:.10f}\n")
            f.write(f"0.0000000000\n")  # rotation_y
            f.write(f"0.0000000000\n")  # rotation_x 
            f.write(f"{pixel_size_y_wgs84:.10f}\n")
            f.write(f"{ul_lon:.10f}\n")    # upper_left_x (longitude)
            f.write(f"{ul_lat:.10f}\n")    # upper_left_y (latitude)
            
        print(f"✅ Created WGS84 world file: {os.path.basename(wgs84_world_file)}")
        
        # Calculate and display coverage info for verification
        area_km2 = width_degrees * height_degrees * 111 * 111
        print(f"📏 Original request coverage: {width_degrees:.6f}° × {height_degrees:.6f}° ({area_km2:.3f} km²)")
        print(f"🎯 This matches the original LAZ area request perfectly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating WGS84 world file: {e}")
        return False

def convert_geotiff_to_png(
    tif_path: str,
    png_path: Optional[str] = None,
    enhanced_resolution: bool = True,
    save_to_consolidated: bool = True,
    stretch_type: str = "stddev", # Changed default to stddev
    stretch_params: Optional[Dict[str, float]] = None
) -> str:
    """
    Convert GeoTIFF file to PNG file with proper scaling and worldfile preservation.
    Allows different contrast stretching methods.
    Default stretch_type is now "stddev".
    """
    print(f"\n🎨 GEOTIFF TO PNG: Starting conversion for '{tif_path}' with stretch: '{stretch_type}'")
    logger.info(f"Starting GeoTIFF to PNG conversion for {tif_path} with stretch_type: {stretch_type}, params: {stretch_params}")
    
    start_time = time.time()
    
    try:
        if png_path is None:
            tif_basename = os.path.splitext(tif_path)[0]
            png_path = f"{tif_basename}.png"
        
        print(f"📁 Output PNG will be: {png_path}")
        
        output_dir = os.path.dirname(png_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 Created output directory: {output_dir}")
        
        ds = gdal.Open(tif_path)
        if ds is None:
            error_msg = f"GDAL failed to open TIF file: {tif_path}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        print(f"📏 Raster dimensions: {ds.RasterXSize}x{ds.RasterYSize} pixels")
        
        band = ds.GetRasterBand(1)
        if band is None:
            ds = None
            error_msg = f"Failed to get band 1 from TIF file: {tif_path}"
            logger.error(error_msg)
            raise Exception(error_msg)

        try:
            stats = band.GetStatistics(False, True)
        except RuntimeError as e:
            logger.warning(f"Exact statistics computation failed for {tif_path}: {e}. Trying approximate.")
            stats = band.GetStatistics(True, True)

        actual_min, actual_max, mean_val, std_val = stats[0], stats[1], stats[2], stats[3]
        print(f"📊 Actual Data range: Min={actual_min:.2f}, Max={actual_max:.2f}, Mean={mean_val:.2f}, StdDev={std_val:.2f}")

        src_min, src_max = actual_min, actual_max

        if stretch_type == "stddev":
            num_stddev = 2.0
            if stretch_params and "num_stddev" in stretch_params:
                num_stddev = stretch_params["num_stddev"]
            
            src_min = mean_val - (num_stddev * std_val)
            src_max = mean_val + (num_stddev * std_val)
            src_min = max(src_min, actual_min)
            src_max = min(src_max, actual_max)
            print(f"🎨 Applying stddev stretch ({num_stddev} stddevs): Scale Min={src_min:.2f}, Scale Max={src_max:.2f}")
            logger.info(f"Stddev stretch: num_stddev={num_stddev}. Calculated src_min={src_min:.2f}, src_max={src_max:.2f}")

        elif stretch_type == "percentclip":
            low_cut_val = stretch_params.get("low_cut", 2.0) if stretch_params else 2.0
            high_cut_val = stretch_params.get("high_cut", 2.0) if stretch_params else 2.0
            logger.info(f"Attempting 'percentclip' with low_cut={low_cut_val}%, high_cut={high_cut_val}%.")
            try:
                data_array = band.ReadAsArray()
                if data_array is not None and data_array.size > 0:
                    if np.all(np.isnan(data_array)) or actual_min == actual_max:
                        logger.warning(f"'percentclip' data is all NaN or flat. Using actual min/max: {actual_min}-{actual_max}")
                        src_min, src_max = actual_min, actual_max
                    else:
                        valid_data = data_array[~np.isnan(data_array)]
                        if valid_data.size > 0:
                            src_min = np.percentile(valid_data, low_cut_val)
                            src_max = np.percentile(valid_data, 100.0 - high_cut_val)
                        else:
                            src_min, src_max = actual_min, actual_max

                        src_min = max(src_min, actual_min)
                        src_max = min(src_max, actual_max)
                        if src_min >= src_max:
                            src_min, src_max = actual_min, actual_max
                            logger.warning(f"Percentile calculation invalid (min>=max). Reverted to actual min/max for {tif_path}")
                        print(f"🎨 Applying percent clip ({low_cut_val}% - {100-high_cut_val}%): Scale Min={src_min:.2f}, Scale Max={src_max:.2f}")
                        logger.info(f"Percent clip success: low={low_cut_val}%, high={high_cut_val}%. Scale src_min={src_min:.2f}, src_max={src_max:.2f}")
                else:
                    logger.warning("Could not read band data for 'percentclip'. Using 'minmax'.")
                    src_min, src_max = actual_min, actual_max
            except Exception as e_pc:
                logger.error(f"Error during 'percentclip' numpy processing for {tif_path}: {e_pc}. Using 'minmax'.", exc_info=True)
                src_min, src_max = actual_min, actual_max

        elif stretch_type == "minmax":
            print(f"🎨 Applying minmax stretch: Scale Min={actual_min:.2f}, Scale Max={actual_max:.2f}")
            logger.info(f"Minmax stretch: Using actual_min={actual_min:.2f}, actual_max={actual_max:.2f}")

        else:
            logger.warning(f"Unknown stretch_type '{stretch_type}'. Defaulting to 'stddev' (new function default).")
            print(f"⚠️ Unknown stretch_type '{stretch_type}'. Defaulting to 'stddev'.")
            # Apply stddev logic if type is unknown and it's now the default
            num_stddev = 2.0
            if stretch_params and "num_stddev" in stretch_params: num_stddev = stretch_params["num_stddev"]
            src_min = mean_val - (num_stddev * std_val)
            src_max = mean_val + (num_stddev * std_val)
            src_min = max(src_min, actual_min)
            src_max = min(src_max, actual_max)
            print(f"🎨 Applying stddev stretch ({num_stddev} stddevs): Scale Min={src_min:.2f}, Scale Max={src_max:.2f}")
            logger.info(f"Stddev stretch (fallback from unknown): num_stddev={num_stddev}. Calculated src_min={src_min:.2f}, src_max={src_max:.2f}")


        if src_min >= src_max:
            logger.warning(f"Final calculated scale min ({src_min:.2f}) >= scale max ({src_max:.2f}). Adjusting.")
            if actual_min < actual_max:
                src_min, src_max = actual_min, actual_max
            else:
                src_min = actual_min
                src_max = actual_min + 1e-6
                if src_min >= src_max: src_max = src_min + np.finfo(float).eps
            if src_min >= src_max:
                src_min, src_max = 0, 255
                logger.error(f"Fatal: Could not ensure src_min < src_max for {tif_path}. Defaulting to 0-255 scale.")
            print(f"   Adjusted scale due to min>=max: Min={src_min:.2f}, Max={src_max:.2f}")

        scale_options_list = ["-scale", str(src_min), str(src_max), "0", "255", "-ot", "Byte", "-co", "WORLDFILE=YES"]
        if enhanced_resolution:
             print(f"ℹ️ 'enhanced_resolution=True' noted. Scale options already incorporate robust stretching.")
        
        print(f"🌍 World file generation enabled - creating .pgw file for georeferencing")
        gdal.Translate(png_path, ds, format="PNG", options=scale_options_list)
        
        # 🌍 CREATE WGS84 WORLD FILE FOR PROPER LEAFLET COMPATIBILITY
        # World files created by GDAL are in the source projection (UTM, Lambert, etc.)
        # Leaflet needs WGS84 coordinates, so we transform them
        world_file_path = os.path.splitext(png_path)[0] + ".wld"  # PNG creates .wld files
        if os.path.exists(world_file_path):
            print(f"🔄 Transforming world file coordinates to WGS84 for Leaflet compatibility...")
            success = create_wgs84_world_file(world_file_path, tif_path, png_path)
            if success:
                print(f"✅ WGS84 world file created for proper overlay scaling")
            else:
                print(f"⚠️ WGS84 transformation failed, keeping original world file")
        
        ds = None
        
        if save_to_consolidated:
            try:
                path_parts = tif_path.split(os.sep)
                region_name = "UnknownRegion"; processing_type = "UnknownType"
                if "output" in path_parts:
                    idx = path_parts.index("output")
                    if idx + 1 < len(path_parts): region_name = path_parts[idx+1]
                    if idx + 3 < len(path_parts): processing_type = path_parts[idx+3]

                consolidated_dir = os.path.join("output", region_name, "lidar", "png_outputs")
                os.makedirs(consolidated_dir, exist_ok=True)
                
                # Check if the PNG is already being created directly in png_outputs directory
                png_normalized = os.path.normpath(png_path)
                consolidated_normalized = os.path.normpath(consolidated_dir)
                
                if consolidated_normalized in png_normalized:
                    print(f"ℹ️ PNG already in png_outputs directory, skipping duplicate consolidated copy: {png_path}")
                else:
                    base_tif_name = os.path.splitext(os.path.basename(tif_path))[0]
                    consolidated_png_name = f"{base_tif_name}.png"
                    consolidated_png_path = os.path.join(consolidated_dir, consolidated_png_name)

                    import shutil
                    shutil.copy2(png_path, consolidated_png_path)

                    worldfile_ext = ".pgw"
                    worldfile_path = os.path.splitext(png_path)[0] + worldfile_ext
                    if not os.path.exists(worldfile_path):
                        worldfile_ext = ".wld"
                        worldfile_path = os.path.splitext(png_path)[0] + worldfile_ext

                    if os.path.exists(worldfile_path):
                        consolidated_worldfile_path = os.path.splitext(consolidated_png_path)[0] + worldfile_ext
                        shutil.copy2(worldfile_path, consolidated_worldfile_path)

                    consolidated_tiff_path = os.path.splitext(consolidated_png_path)[0] + "_source.tif"
                    if os.path.exists(tif_path) and not os.path.exists(consolidated_tiff_path) :
                        # shutil.copy2(tif_path, consolidated_tiff_path)
                        logger.info(f"Copied source TIF to consolidated: {consolidated_tiff_path}")

                    print(f"✅ Copied PNG and associated files to consolidated directory: {consolidated_png_path}")
            except Exception as e_consol:
                logger.warning(f"Failed to save PNG to consolidated directory for {tif_path}: {e_consol}", exc_info=True)
        
        processing_time = time.time() - start_time
        print(f"✅ GeoTIFF to PNG conversion (stretch: {stretch_type}) completed in {processing_time:.2f} seconds. PNG: {png_path}")
        return png_path
        
    except Exception as e:
        error_msg = f"GeoTIFF to PNG conversion failed for {tif_path}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)

def convert_geotiff_to_png_base64(
    tif_path: str,
    stretch_type: str = "stddev", # Changed default to stddev
    stretch_params: Optional[Dict[str, float]] = None
) -> str:
    """
    Convert GeoTIFF file to PNG and return as base64 encoded string.
    Default stretch_type is now "stddev".
    """
    print(f"\n🖼️ CONVERT TIF TO BASE64 PNG (Stretch: {stretch_type}) for {tif_path}")
    logger.info(f"Converting {tif_path} to base64 PNG with stretch {stretch_type}, params {stretch_params}")
    
    start_time = time.time()
    temp_png_path = None
    
    try:
        temp_dir = tempfile.gettempdir()
        temp_png_filename = f"{os.path.splitext(os.path.basename(tif_path))[0]}_{int(time.time()*1000)}.png"
        temp_png_path = os.path.join(temp_dir, temp_png_filename)

        png_path_used = convert_geotiff_to_png(
            tif_path, png_path=temp_png_path, save_to_consolidated=False,
            stretch_type=stretch_type, stretch_params=stretch_params
        )
        
        print(f"🔄 Converting PNG {png_path_used} to base64...")
        with open(png_path_used, 'rb') as png_file:
            png_data = png_file.read()
            base64_data = base64.b64encode(png_data).decode('utf-8')
        
        total_time = time.time() - start_time
        print(f"✅ Base64 conversion completed. Total time: {total_time:.2f} seconds")
        return base64_data
        
    except Exception as e:
        error_msg = f"TIF to PNG base64 conversion failed for {tif_path}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)
    finally:
        if temp_png_path and os.path.exists(temp_png_path):
            try:
                os.remove(temp_png_path)
                worldfile_pgw = os.path.splitext(temp_png_path)[0] + ".pgw"
                if os.path.exists(worldfile_pgw): os.remove(worldfile_pgw)
                worldfile_wld = os.path.splitext(temp_png_path)[0] + ".wld"
                if os.path.exists(worldfile_wld): os.remove(worldfile_wld)
            except OSError as e_remove:
                logger.warning(f"Could not remove temporary PNG or worldfile for {temp_png_path}: {e_remove}")

def convert_sentinel2_to_png(data_dir: str, region_name: str) -> dict:
    print(f"\n🛰️ SENTINEL-2 TO PNG: Starting conversion")
    logger.info(f"Starting Sentinel-2 to PNG conversion for region {region_name} in {data_dir}")
    results = {'success': False, 'files': [], 'errors': []}
    try:
        input_dir = Path(data_dir) / "sentinel2"
        if not input_dir.exists():
            logger.warning(f"Sentinel2 subfolder not found in {data_dir}, checking directly in input directory.")
            input_dir = Path(data_dir)
            if not input_dir.exists():
                results['errors'].append(f"Input directory does not exist: {data_dir}"); return results
        
        output_dir = Path("output") / region_name / "sentinel2"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        tif_files = list(input_dir.glob("*.tif")) + list(input_dir.glob("*.tiff"))
        if not tif_files:
            results['errors'].append(f"No TIF files found in {input_dir}"); return results
        
        tif_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_tif = tif_files[0]
        logger.info(f"Processing most recent Sentinel-2 TIF: {latest_tif.name}")
        
        try:
            from .geo_utils import get_image_bounds_from_geotiff, crop_geotiff_to_bbox, intersect_bounding_boxes
            from app.data_acquisition.utils.coordinates import BoundingBox
            dtm_output_base = Path("output") / region_name / "lidar" / "DTM"
            dtm_candidates = list(dtm_output_base.glob("filled/*_DTM_filled_*.tif")) + \
                             list(dtm_output_base.glob("raw/*_DTM_raw_*.tif")) + \
                             list(dtm_output_base.glob("*_DTM.tif"))
            if dtm_candidates:
                dtm_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                dtm_tif_to_crop_against = dtm_candidates[0]
                logger.info(f"Attempting to crop Sentinel-2 {latest_tif} against DTM {dtm_tif_to_crop_against}")
                s2_bounds = get_image_bounds_from_geotiff(str(latest_tif))
                dtm_bounds_for_crop = get_image_bounds_from_geotiff(str(dtm_tif_to_crop_against))
                if s2_bounds and dtm_bounds_for_crop:
                    s2_bb = BoundingBox(**{k: s2_bounds[k] for k in ['north','south','east','west']})
                    dtm_bb_crop = BoundingBox(**{k: dtm_bounds_for_crop[k] for k in ['north','south','east','west']})
                    inter = intersect_bounding_boxes(s2_bb, dtm_bb_crop)
                    if inter:
                        tmp_crop = latest_tif.with_name(latest_tif.stem + "_crop.tif")
                        if crop_geotiff_to_bbox(str(latest_tif), str(tmp_crop), inter):
                            os.replace(tmp_crop, latest_tif)
                            logger.info(f"Successfully cropped {latest_tif.name} to DTM extent.")
                        else: logger.warning(f"Cropping {latest_tif.name} failed.")
                    else: logger.info(f"Sentinel-2 {latest_tif.name} and DTM {dtm_tif_to_crop_against.name} do not intersect.")
                else: logger.warning(f"Could not get bounds for S2 or DTM for cropping. S2: {s2_bounds}, DTM: {dtm_bounds_for_crop}")
            else: logger.info(f"No DTM found for region {region_name} for S2 cropping.")
        except Exception as e: logger.warning(f"Sentinel-2 cropping failed for {latest_tif.name}: {e}", exc_info=True)

        src_ds_s2 = gdal.Open(str(latest_tif))
        if src_ds_s2 is None: results['errors'].append(f"Failed to open S2 TIF: {latest_tif.name}"); return results
        num_bands = src_ds_s2.RasterCount
        src_ds_s2 = None

        bands_to_process = []
        if num_bands >= 4: bands_to_process = [("RED_B04", 1, "RED_B04"), ("NIR_B08", 4, "NIR_B08")]
        elif num_bands == 1: bands_to_process = [("GRAY", 1, "GRAY")]
        else: results['errors'].append(f"Unsupported band count ({num_bands}) in S2 TIF: {latest_tif.name}"); return results

        extracted_band_paths = {}
        for band_name, band_num, file_suffix in bands_to_process:
            try:
                base_name = latest_tif.stem
                band_tif_path = output_dir / f"{base_name}_{file_suffix}.tif"
                # Extract band TIF but don't create PNG for individual bands - only NDVI PNG will be generated
                if extract_sentinel2_band(str(latest_tif), str(band_tif_path), band_num):
                    extracted_band_paths[band_name] = str(band_tif_path)
                    print(f"✅ Extracted {band_name} band to {band_tif_path} (PNG will not be generated)")
                else: results['errors'].append(f"Failed to extract {band_name} from {latest_tif.name}")
            except Exception as e_band: results['errors'].append(f"Error processing band {band_name}: {e_band}")

        if "RED_B04" in extracted_band_paths and "NIR_B08" in extracted_band_paths:
            # Check if NDVI is enabled for this region before processing
            try:
                from .endpoints.region_management import isRegionNDVI
                ndvi_enabled = isRegionNDVI(region_name)
                print(f"🔍 NDVI status for region {region_name}: {'enabled' if ndvi_enabled else 'disabled'}")
                
                if ndvi_enabled:
                    print(f"🌱 NDVI is enabled - proceeding with NDVI calculation for {region_name}")
                    from .processing.ndvi_processing import NDVIProcessor
                    ndvi_tif_path = output_dir / f"{latest_tif.stem}_NDVI.tif"
                    if NDVIProcessor().calculate_ndvi(extracted_band_paths["RED_B04"], extracted_band_paths["NIR_B08"], str(ndvi_tif_path)) and os.path.exists(ndvi_tif_path):
                        # Create NDVI PNG in png_outputs directory for consistency
                        png_outputs_dir = Path("output") / region_name / "lidar" / "png_outputs"
                        png_outputs_dir.mkdir(parents=True, exist_ok=True)
                        ndvi_png_path = png_outputs_dir / f"{latest_tif.stem}_NDVI.png"
                        
                        actual_ndvi_png = convert_geotiff_to_png(str(ndvi_tif_path), str(ndvi_png_path))
                        if os.path.exists(actual_ndvi_png):
                            results['files'].append({'band': 'NDVI', 'tif_path': str(ndvi_tif_path), 'png_path': actual_ndvi_png, 'size_mb': os.path.getsize(actual_ndvi_png)/(1024*1024)})
                            
                            # 🛰️ Trigger satellite gallery refresh - NDVI processing completed
                            results['ndvi_completed'] = True
                            results['trigger_satellite_refresh'] = region_name
                            print(f"✅ NDVI PNG processing completed - satellite gallery should refresh for region: {region_name}")
                        else: results['errors'].append("Failed to create PNG for NDVI")
                    else: results['errors'].append(f"Failed to calculate NDVI from {latest_tif.stem}")
                else:
                    print(f"🚫 NDVI is disabled for region {region_name} - skipping NDVI calculation")
                    
            except Exception as ndvi_e: results['errors'].append(f"Error processing NDVI: {ndvi_e}")
        results['success'] = len(results['files']) > 0 and not results['errors']
    except Exception as e: results['errors'].append(f"S2 conversion main error: {e}")
    logger.info(f"S2 to PNG conversion finished. Success: {results['success']}. Files: {len(results['files'])}, Errors: {len(results['errors'])}")
    return results

def extract_sentinel2_band(input_tif: str, output_tif: str, band_number: int) -> bool:
    try:
        logger.info(f"Extracting band {band_number} from {input_tif} to {output_tif}")
        cmd = ['gdal_translate', '-b', str(band_number), input_tif, output_tif, '-co', 'COMPRESS=LZW', '-co', 'TILED=YES']
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0 and os.path.exists(output_tif) and os.path.getsize(output_tif) > 0: return True
        else: logger.error(f"gdal_translate for band {band_number} failed or output empty. RC: {result.returncode}. Stderr: {result.stderr}"); return False
    except Exception as e: logger.error(f"Exception during band extraction {input_tif} b{band_number}: {e}", exc_info=True); return False

def convert_chm_to_viridis_png(
    tif_path: str,
    png_path: Optional[str] = None,
    enhanced_resolution: bool = True,
    save_to_consolidated: bool = True
) -> str:
    """
    Convert CHM GeoTIFF to PNG with viridis colormap and min-max normalization.
    Specifically designed for Canopy Height Model visualization.
    
    Args:
        tif_path: Path to CHM TIF file
        png_path: Optional output PNG path  
        enhanced_resolution: Use enhanced processing
        save_to_consolidated: Copy to consolidated directory
        
    Returns:
        Path to generated PNG file
    """
    print(f"\n🌳 CHM VIRIDIS COLORIZATION: {os.path.basename(tif_path)}")
    logger.info(f"CHM viridis colorization for {tif_path}")
    
    start_time = time.time()
    
    try:
        # Generate output path if not provided
        if png_path is None:
            png_path = os.path.splitext(tif_path)[0] + "_viridis.png"
        
        # Ensure output directory exists
        output_dir = os.path.dirname(png_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 Created output directory: {output_dir}")
        
        # Open and read CHM data
        ds = gdal.Open(tif_path)
        if ds is None:
            raise Exception(f"Failed to open CHM TIF: {tif_path}")
        
        band = ds.GetRasterBand(1)
        chm_data = band.ReadAsArray()
        
        # Get georeference info for world file
        geotransform = ds.GetGeoTransform()
        width = ds.RasterXSize
        height = ds.RasterYSize
        
        ds = None
        band = None
        
        print(f"📏 CHM dimensions: {width}x{height} pixels")
        print(f"📊 CHM data range: {np.nanmin(chm_data):.2f} to {np.nanmax(chm_data):.2f} meters")
        
        # Handle NoData values
        nodata_mask = chm_data == -9999
        chm_data[nodata_mask] = np.nan
        
        # Min-max normalization across entire image
        valid_data = chm_data[~np.isnan(chm_data)]
        if len(valid_data) == 0:
            print("⚠️ No valid CHM data found")
            # Create empty image
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, 'No CHM Data Available', ha='center', va='center', 
                   fontsize=16, transform=ax.transAxes)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        else:
            # Apply min-max scaling
            data_min = np.nanmin(valid_data)
            data_max = np.nanmax(valid_data)
            
            print(f"🎨 Applying min-max normalization:")
            print(f"   Min height: {data_min:.2f}m (dark purple)")
            print(f"   Max height: {data_max:.2f}m (bright yellow-green)")
            
            # Normalize to 0-1 range
            if data_max > data_min:
                normalized_data = (chm_data - data_min) / (data_max - data_min)
            else:
                normalized_data = np.zeros_like(chm_data)
            
            # Create figure with high quality settings
            if enhanced_resolution:
                fig, ax = plt.subplots(figsize=(16, 12), dpi=300)
            else:
                fig, ax = plt.subplots(figsize=(12, 10), dpi=150)
            
            # Apply viridis colormap
            # Low canopy (0) = dark purple (#440154)
            # High vegetation (1) = bright yellow-green (#fde725)
            cmap = plt.cm.viridis
            
            # Create masked array to handle NaN values
            masked_data = np.ma.masked_where(np.isnan(normalized_data), normalized_data)
            
            # Display with viridis colormap
            im = ax.imshow(masked_data, cmap=cmap, vmin=0, vmax=1, 
                          aspect='equal', interpolation='nearest')
            
            # Add colorbar with meaningful labels
            cbar = plt.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
            cbar.set_label('Canopy Height (m)', rotation=270, labelpad=20, fontsize=12)
            
            # Set colorbar ticks to show actual height values
            if data_max > data_min:
                tick_positions = np.linspace(0, 1, 6)
                tick_labels = [f"{data_min + pos * (data_max - data_min):.1f}" 
                              for pos in tick_positions]
                cbar.set_ticks(tick_positions)
                cbar.set_ticklabels(tick_labels)
            
            # Set title and remove axes for clean visualization
            ax.set_title(f"CHM - Canopy Height Model\n{os.path.basename(tif_path)}", 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel("Pixels (East)", fontsize=10)
            ax.set_ylabel("Pixels (North)", fontsize=10)
            
            # Add explanatory text
            textstr = f'Colormap: Viridis\nDark purple: Low canopy areas\nBright yellow-green: High vegetation\nRange: {data_min:.1f}m - {data_max:.1f}m'
            props = dict(boxstyle='round', facecolor='white', alpha=0.8)
            ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=props)
        
        # Save PNG with high quality
        plt.tight_layout()
        if enhanced_resolution:
            plt.savefig(png_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', format='PNG')
        else:
            plt.savefig(png_path, dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', format='PNG')
        
        plt.close()
        
        # Create world file for georeferencing
        if geotransform:
            world_file_path = os.path.splitext(png_path)[0] + ".pgw"
            with open(world_file_path, 'w') as f:
                f.write(f"{geotransform[1]:.10f}\n")  # pixel size x
                f.write(f"{geotransform[2]:.10f}\n")  # rotation y
                f.write(f"{geotransform[4]:.10f}\n")  # rotation x
                f.write(f"{geotransform[5]:.10f}\n")  # pixel size y (negative)
                f.write(f"{geotransform[0]:.10f}\n")  # top left x
                f.write(f"{geotransform[3]:.10f}\n")  # top left y
            print(f"🌍 Created world file: {os.path.basename(world_file_path)}")
        
        # Transform world file to WGS84 if possible
        world_file_path = os.path.splitext(png_path)[0] + ".pgw"
        if os.path.exists(world_file_path):
            success = create_wgs84_world_file(world_file_path, tif_path, png_path)
            if success:
                print(f"✅ WGS84 world file created for proper overlay scaling")
        
        # Copy to consolidated directory if requested
        if save_to_consolidated:
            try:
                path_parts = tif_path.split(os.sep)
                region_name = "UnknownRegion"
                if "output" in path_parts:
                    idx = path_parts.index("output")
                    if idx + 1 < len(path_parts): 
                        region_name = path_parts[idx+1]
                
                consolidated_dir = os.path.join("output", region_name, "lidar", "png_outputs")
                os.makedirs(consolidated_dir, exist_ok=True)
                
                # Check if PNG is already in the target directory
                png_normalized = os.path.normpath(png_path)
                consolidated_normalized = os.path.normpath(consolidated_dir)
                
                if consolidated_normalized not in png_normalized:
                    import shutil
                    consolidated_png_path = os.path.join(consolidated_dir, "CHM_viridis.png")
                    shutil.copy2(png_path, consolidated_png_path)
                    
                    # Copy world files too
                    for ext in [".pgw", ".wld", "_wgs84.wld"]:
                        src_world = os.path.splitext(png_path)[0] + ext
                        if os.path.exists(src_world):
                            dst_world = os.path.splitext(consolidated_png_path)[0] + ext
                            shutil.copy2(src_world, dst_world)
                    
                    print(f"✅ Copied CHM viridis PNG to consolidated directory")
                
            except Exception as e:
                logger.warning(f"Failed to copy CHM PNG to consolidated directory: {e}")
        
        processing_time = time.time() - start_time
        print(f"✅ CHM viridis colorization completed in {processing_time:.2f} seconds")
        print(f"🌈 Result: {os.path.basename(png_path)}")
        
        return png_path
        
    except Exception as e:
        error_msg = f"CHM viridis colorization failed for {tif_path}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)

def convert_lrm_to_coolwarm_png(
    tif_path: str,
    png_path: Optional[str] = None,
    enhanced_resolution: bool = True,
    save_to_consolidated: bool = True,
    percentile_clip: Tuple[float, float] = (2.0, 98.0),
    enhanced_normalization_mode: bool = False
) -> str:
    """
    Convert LRM GeoTIFF to PNG with enhanced coolwarm diverging colormap and advanced contrast stretching.
    Specifically designed for Local Relief Model visualization for archaeological analysis.
    
    Args:
        tif_path: Path to LRM TIF file
        png_path: Optional output PNG path  
        enhanced_resolution: Use enhanced processing
        save_to_consolidated: Copy to consolidated directory
        percentile_clip: Tuple of (min_percentile, max_percentile) for contrast stretching
        enhanced_normalization_mode: Whether the input data is already normalized to [-1, 1]
        
    Returns:
        Path to generated PNG file
    """
    print(f"\n🌄 ENHANCED LRM COOLWARM COLORIZATION: {os.path.basename(tif_path)}")
    logger.info(f"Enhanced LRM coolwarm colorization for {tif_path}")
    
    start_time = time.time()
    
    try:
        # Generate output path if not provided
        if png_path is None:
            png_path = os.path.splitext(tif_path)[0] + "_enhanced_coolwarm.png"
        
        # Ensure output directory exists
        output_dir = os.path.dirname(png_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 Created output directory: {output_dir}")
        
        # Open and read LRM data
        ds = gdal.Open(tif_path)
        if ds is None:
            raise Exception(f"Failed to open LRM TIF: {tif_path}")
        
        band = ds.GetRasterBand(1)
        lrm_data = band.ReadAsArray()
        
        # Get georeference info for world file
        geotransform = ds.GetGeoTransform()
        width = ds.RasterXSize
        height = ds.RasterYSize
        
        ds = None
        band = None
        
        print(f"📏 LRM dimensions: {width}x{height} pixels")
        print(f"📊 LRM data range: {np.nanmin(lrm_data):.3f} to {np.nanmax(lrm_data):.3f} meters")
        
        # Handle NoData values
        nodata_mask = lrm_data == -9999
        lrm_data[nodata_mask] = np.nan
        
        # Apply enhanced contrast stretching based on normalization mode
        valid_data = lrm_data[~np.isnan(lrm_data)]
        if len(valid_data) == 0:
            print("⚠️ No valid LRM data found")
            # Create empty image
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, 'No LRM Data Available', ha='center', va='center', 
                   fontsize=16, transform=ax.transAxes)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        else:
            if enhanced_normalization_mode:
                # Data is already normalized to [-1, 1], use directly
                print(f"🎨 Using pre-normalized data (enhanced normalization mode)")
                print(f"   📊 Data range: {np.nanmin(valid_data):.3f} to {np.nanmax(valid_data):.3f}")
                normalized_data = np.clip(lrm_data, -1, 1)
                max_abs_value = 1.0  # For colorbar labels
            else:
                # Apply standard percentile-based clipping and normalization
                p_min, p_max = np.percentile(valid_data, percentile_clip)
                
                print(f"🎨 Applying percentile-based contrast stretching ({percentile_clip[0]}%-{percentile_clip[1]}%):")
                print(f"   P{percentile_clip[0]}: {p_min:.3f}m (blue - depressions)")
                print(f"   P{percentile_clip[1]}: {p_max:.3f}m (red - elevated terrain)")
                print(f"   Center (0): White (neutral relief)")
                
                # Clip data to percentile range
                lrm_clipped = np.clip(lrm_data, p_min, p_max)
                
                # Normalize to symmetric range around zero for diverging colormap
                # Find the maximum absolute value to create symmetric scaling
                max_abs_value = max(abs(p_min), abs(p_max))
                
                if max_abs_value > 0:
                    normalized_data = lrm_clipped / max_abs_value
                    # Ensure the range is exactly [-1, 1] for proper colormap application
                    normalized_data = np.clip(normalized_data, -1, 1)
                else:
                    normalized_data = np.zeros_like(lrm_clipped)
            
            # Create figure with high quality settings
            if enhanced_resolution:
                fig, ax = plt.subplots(figsize=(16, 12), dpi=300)
            else:
                fig, ax = plt.subplots(figsize=(12, 10), dpi=150)
            
            # Apply coolwarm diverging colormap
            # Blue (negative, -1) = depressions/valleys
            # White (zero, 0) = neutral/flat areas  
            # Red (positive, +1) = elevated terrain/ridges
            cmap = plt.cm.coolwarm
            
            # Create masked array to handle NaN values
            masked_data = np.ma.masked_where(np.isnan(normalized_data), normalized_data)
            
            # Display with coolwarm colormap
            im = ax.imshow(masked_data, cmap=cmap, vmin=-1, vmax=1, 
                          aspect='equal', interpolation='nearest')
            
            # Add colorbar with meaningful labels for archaeological interpretation
            cbar = plt.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
            cbar.set_label('Local Relief (m)', rotation=270, labelpad=20, fontsize=12)
            
            # Set colorbar ticks to show actual relief values
            tick_positions = np.linspace(-1, 1, 7)  # -1, -0.67, -0.33, 0, 0.33, 0.67, 1
            tick_labels = [f"{pos * max_abs_value:.2f}" for pos in tick_positions]
            cbar.set_ticks(tick_positions)
            cbar.set_ticklabels(tick_labels)
            
            # Set title and labels for archaeological context
            title_suffix = " (Enhanced)" if enhanced_normalization_mode else ""
            ax.set_title(f"LRM - Local Relief Model (Archaeological Enhancement){title_suffix}\n{os.path.basename(tif_path)}", 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel("Pixels (East)", fontsize=10)
            ax.set_ylabel("Pixels (North)", fontsize=10)
            
            # Add explanatory text for archaeological interpretation
            textstr = f'Colormap: Coolwarm Diverging\nBlue: Depressions/valleys (potential features)\nWhite: Neutral relief\nRed: Elevated terrain/ridges\nRange: {p_min:.2f}m to {p_max:.2f}m\nClipped: {percentile_clip[0]}%-{percentile_clip[1]}% percentiles'
            props = dict(boxstyle='round', facecolor='white', alpha=0.8)
            ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=props)
        
        # Save PNG with high quality
        plt.tight_layout()
        if enhanced_resolution:
            plt.savefig(png_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', format='PNG')
        else:
            plt.savefig(png_path, dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', format='PNG')
        
        plt.close()
        
        # Create world file for georeferencing
        if geotransform:
            world_file_path = os.path.splitext(png_path)[0] + ".pgw"
            with open(world_file_path, 'w') as f:
                f.write(f"{geotransform[1]:.10f}\n")  # pixel size x
                f.write(f"{geotransform[2]:.10f}\n")  # rotation y
                f.write(f"{geotransform[4]:.10f}\n")  # rotation x
                f.write(f"{geotransform[5]:.10f}\n")  # pixel size y (negative)
                f.write(f"{geotransform[0]:.10f}\n")  # top left x
                f.write(f"{geotransform[3]:.10f}\n")  # top left y
            print(f"🌍 Created world file: {os.path.basename(world_file_path)}")
        
        # Transform world file to WGS84 if possible
        world_file_path = os.path.splitext(png_path)[0] + ".pgw"
        if os.path.exists(world_file_path):
            success = create_wgs84_world_file(world_file_path, tif_path, png_path)
            if success:
                print(f"✅ WGS84 world file created for proper overlay scaling")
        
        # Copy to consolidated directory if requested
        if save_to_consolidated:
            try:
                path_parts = tif_path.split(os.sep)
                region_name = "UnknownRegion"
                if "output" in path_parts:
                    idx = path_parts.index("output")
                    if idx + 1 < len(path_parts): 
                        region_name = path_parts[idx+1]
                
                consolidated_dir = os.path.join("output", region_name, "lidar", "png_outputs")
                os.makedirs(consolidated_dir, exist_ok=True)
                
                # Check if PNG is already in the target directory
                png_normalized = os.path.normpath(png_path)
                consolidated_normalized = os.path.normpath(consolidated_dir)
                
                if consolidated_normalized not in png_normalized:
                    import shutil
                    consolidated_png_path = os.path.join(consolidated_dir, "LRM_coolwarm.png")
                    shutil.copy2(png_path, consolidated_png_path)
                    
                    # Copy world files too
                    for ext in [".pgw", ".wld", "_wgs84.wld"]:
                        src_world = os.path.splitext(png_path)[0] + ext
                        if os.path.exists(src_world):
                            dst_world = os.path.splitext(consolidated_png_path)[0] + ext
                            shutil.copy2(src_world, dst_world)
                    
                    print(f"✅ Copied LRM coolwarm PNG to consolidated directory")
                
            except Exception as e:
                logger.warning(f"Failed to copy LRM PNG to consolidated directory: {e}")
        
        processing_time = time.time() - start_time
        print(f"✅ LRM coolwarm colorization completed in {processing_time:.2f} seconds")
        print(f"🌈 Result: {os.path.basename(png_path)}")
        
        return png_path
        
    except Exception as e:
        error_msg = f"LRM coolwarm colorization failed for {tif_path}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)

def convert_slope_to_inferno_png(
    tif_path: str,
    png_path: Optional[str] = None,
    enhanced_resolution: bool = True,
    save_to_consolidated: bool = True,
    max_slope_degrees: float = 60.0
) -> str:
    """
    Convert Slope GeoTIFF to PNG with inferno colormap and 0-60 degree linear rescaling.
    Specifically designed for archaeological terrain analysis where slope-defined anomalies 
    like causeway edges, terraces, or hillside platforms need to be highlighted.
    
    Args:
        tif_path: Path to Slope TIF file
        png_path: Optional output PNG path  
        enhanced_resolution: Use enhanced processing
        save_to_consolidated: Copy to consolidated directory
        max_slope_degrees: Maximum slope angle for linear rescaling (default: 60.0)
        
    Returns:
        Path to generated PNG file
    """
    print(f"\n🔥 ENHANCED SLOPE INFERNO COLORIZATION: {os.path.basename(tif_path)}")
    logger.info(f"Enhanced slope inferno colorization for {tif_path}")
    
    start_time = time.time()
    
    try:
        # Generate output path if not provided
        if png_path is None:
            png_path = os.path.splitext(tif_path)[0] + "_inferno.png"
        
        # Ensure output directory exists
        output_dir = os.path.dirname(png_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 Created output directory: {output_dir}")
        
        # Open and read Slope data
        ds = gdal.Open(tif_path)
        if ds is None:
            raise Exception(f"Failed to open Slope TIF: {tif_path}")
        
        band = ds.GetRasterBand(1)
        slope_data = band.ReadAsArray()
        
        # Get georeference info for world file
        geotransform = ds.GetGeoTransform()
        width = ds.RasterXSize
        height = ds.RasterYSize
        
        ds = None
        band = None
        
        print(f"📏 Slope dimensions: {width}x{height} pixels")
        print(f"📊 Slope data range: {np.nanmin(slope_data):.2f}° to {np.nanmax(slope_data):.2f}°")
        
        # Handle NoData values
        nodata_mask = slope_data == -9999
        slope_data[nodata_mask] = np.nan
        
        # Apply enhanced slope visualization for archaeological analysis
        valid_data = slope_data[~np.isnan(slope_data)]
        if len(valid_data) == 0:
            print("⚠️ No valid slope data found")
            # Create empty image
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, 'No Slope Data Available', ha='center', va='center', 
                   fontsize=16, transform=ax.transAxes)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        else:
            # Enhanced linear rescaling from 0 to max_slope_degrees
            actual_min = np.nanmin(valid_data)
            actual_max = np.nanmax(valid_data)
            
            print(f"🎨 Applying enhanced linear rescaling (0° to {max_slope_degrees}°):")
            print(f"   📊 Actual data range: {actual_min:.2f}° to {actual_max:.2f}°")
            print(f"   📐 Target range: 0° to {max_slope_degrees}°")
            print(f"   🔥 Colormap: Inferno (dark for flat, bright for steep)")
            
            # Clip slopes to the archaeological analysis range (0-60 degrees typical)
            slope_clipped = np.clip(slope_data, 0, max_slope_degrees)
            
            # Linear rescaling to [0, 1] range for optimal inferno colormap application
            normalized_data = slope_clipped / max_slope_degrees
            
            # Ensure normalized data is properly bounded
            normalized_data = np.clip(normalized_data, 0, 1)
            
            print(f"   ✅ Normalized range: {np.nanmin(normalized_data[~np.isnan(normalized_data)]):.3f} to {np.nanmax(normalized_data[~np.isnan(normalized_data)]):.3f}")
            
            # Create figure with high quality settings
            if enhanced_resolution:
                fig, ax = plt.subplots(figsize=(16, 12), dpi=300)
            else:
                fig, ax = plt.subplots(figsize=(12, 10), dpi=150)
            
            # Apply inferno colormap for archaeological slope analysis
            # Dark purple/black (0) = flat areas (0°)
            # Bright yellow/white (1) = steep terrain (60°+)
            # Perfect for highlighting slope-defined archaeological features
            cmap = plt.cm.inferno
            
            # Create masked array to handle NaN values
            masked_data = np.ma.masked_where(np.isnan(normalized_data), normalized_data)
            
            # Display with inferno colormap
            im = ax.imshow(masked_data, cmap=cmap, vmin=0, vmax=1, 
                          aspect='equal', interpolation='nearest')
            
            # Add colorbar with meaningful labels for archaeological interpretation
            cbar = plt.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
            cbar.set_label('Slope Angle (degrees)', rotation=270, labelpad=20, fontsize=12)
            
            # Set colorbar ticks to show actual slope values
            tick_positions = np.linspace(0, 1, 7)  # 0, 0.17, 0.33, 0.5, 0.67, 0.83, 1.0
            tick_labels = [f"{pos * max_slope_degrees:.0f}°" for pos in tick_positions]
            cbar.set_ticks(tick_positions)
            cbar.set_ticklabels(tick_labels)
            
            # Set title and labels for archaeological context
            ax.set_title(f"Slope Analysis - Inferno Enhanced (Archaeological)\n{os.path.basename(tif_path)}", 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel("Pixels (East)", fontsize=10)
            ax.set_ylabel("Pixels (North)", fontsize=10)
            
            # Add explanatory text for archaeological interpretation
            flat_areas_pct = np.sum(slope_clipped < 5) / np.sum(~np.isnan(slope_clipped)) * 100
            moderate_areas_pct = np.sum((slope_clipped >= 5) & (slope_clipped < 20)) / np.sum(~np.isnan(slope_clipped)) * 100
            steep_areas_pct = np.sum(slope_clipped >= 20) / np.sum(~np.isnan(slope_clipped)) * 100
            
            textstr = f'Colormap: Inferno\nDark: Flat areas (0°-5°) - {flat_areas_pct:.1f}%\nMedium: Moderate slopes (5°-20°) - {moderate_areas_pct:.1f}%\nBright: Steep terrain (20°+) - {steep_areas_pct:.1f}%\nRange: 0° to {max_slope_degrees}°\nHighlights: Terraces, scarps, causeway edges'
            props = dict(boxstyle='round', facecolor='white', alpha=0.8)
            ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=props)
        
        # Save PNG with high quality
        plt.tight_layout()
        if enhanced_resolution:
            plt.savefig(png_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', format='PNG')
        else:
            plt.savefig(png_path, dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', format='PNG')
        
        plt.close()
        
        # Create world file for georeferencing
        if geotransform:
            world_file_path = os.path.splitext(png_path)[0] + ".pgw"
            with open(world_file_path, 'w') as f:
                f.write(f"{geotransform[1]:.10f}\n")  # pixel size x
                f.write(f"{geotransform[2]:.10f}\n")  # rotation y
                f.write(f"{geotransform[4]:.10f}\n")  # rotation x
                f.write(f"{geotransform[5]:.10f}\n")  # pixel size y (negative)
                f.write(f"{geotransform[0]:.10f}\n")  # top left x
                f.write(f"{geotransform[3]:.10f}\n")  # top left y
            print(f"🌍 Created world file: {os.path.basename(world_file_path)}")
        
        # Transform world file to WGS84 if possible
        world_file_path = os.path.splitext(png_path)[0] + ".pgw"
        if os.path.exists(world_file_path):
            success = create_wgs84_world_file(world_file_path, tif_path, png_path)
            if success:
                print(f"✅ WGS84 world file created for proper overlay scaling")
        
        # Copy to consolidated directory if requested
        if save_to_consolidated:
            try:
                path_parts = tif_path.split(os.sep)
                region_name = "UnknownRegion"
                if "output" in path_parts:
                    idx = path_parts.index("output")
                    if idx + 1 < len(path_parts): 
                        region_name = path_parts[idx+1]
                
                consolidated_dir = os.path.join("output", region_name, "lidar", "png_outputs")
                os.makedirs(consolidated_dir, exist_ok=True)
                
                # Check if PNG is already in the target directory
                png_normalized = os.path.normpath(png_path)
                consolidated_normalized = os.path.normpath(consolidated_dir)
                
                if consolidated_normalized not in png_normalized:
                    import shutil
                    consolidated_png_path = os.path.join(consolidated_dir, "Slope_inferno.png")
                    shutil.copy2(png_path, consolidated_png_path)
                    
                    # Copy world files too
                    for ext in [".pgw", ".wld", "_wgs84.wld"]:
                        src_world = os.path.splitext(png_path)[0] + ext
                        if os.path.exists(src_world):
                            dst_world = os.path.splitext(consolidated_png_path)[0] + ext
                            shutil.copy2(src_world, dst_world)
                    
                    print(f"✅ Copied slope inferno PNG to consolidated directory")
                
            except Exception as e:
                logger.warning(f"Failed to copy slope PNG to consolidated directory: {e}")
        
        processing_time = time.time() - start_time
        print(f"✅ Slope inferno colorization completed in {processing_time:.2f} seconds")
        print(f"🔥 Result: {os.path.basename(png_path)}")
        
        return png_path
        
    except Exception as e:
        error_msg = f"Slope inferno colorization failed for {tif_path}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)
