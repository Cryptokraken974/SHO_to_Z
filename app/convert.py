from osgeo import gdal
import os
import time
from typing import Optional, Dict # Added Dict
import base64
import subprocess
import numpy as np # Added numpy
import logging
import tempfile # Added tempfile for base64 conversion temp file
from pathlib import Path # Added pathlib for Sentinel-2 processing

logger = logging.getLogger(__name__)

# Configure GDAL to prevent auxiliary file creation for PNG files
gdal.SetConfigOption('GDAL_PAM_ENABLED', 'NO')

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

        scale_options_list = ["-scale", str(src_min), str(src_max), "0", "255", "-ot", "Byte", "-co", "WORLDFILE=NO"]
        if enhanced_resolution:
             print(f"ℹ️ 'enhanced_resolution=True' noted. Scale options already incorporate robust stretching.")
        
        gdal.Translate(png_path, ds, format="PNG", options=scale_options_list)
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
