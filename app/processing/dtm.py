import asyncio
import time
import os
import logging
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional # Added Optional
import pdal

logger = logging.getLogger(__name__)

# Define the path to the JSON pipeline template
current_dir = os.path.dirname(os.path.abspath(__file__))
PDAL_PIPELINE_JSON_PATH = os.path.join(current_dir, "pipelines_json", "dtm.json")


def fill_nodata_enhanced(input_path, output_path, max_distance=20, smoothing_iter=2): # Default changed to 20
    """
    Optimized FillNodata using CreateCopy for better performance and proper error handling.
    
    Args:
        input_path: Path to input GeoTIFF with NoData areas
        output_path: Path for output filled GeoTIFF
        max_distance: Max search distance for interpolation (pixels). Default is 20.
        smoothing_iter: Number of 3x3 smoothing iterations (0-20)
    """
    from osgeo import gdal
    import numpy as np
    
    # Enable GDAL exceptions for better error handling
    gdal.UseExceptions()
    
    print(f"🔧 Optimized FillNodata processing:")
    print(f"   📁 Input: {input_path}")
    print(f"   📁 Output: {output_path}")
    print(f"   🎯 Max distance: {max_distance} pixels") # This will now show 20 when default is used
    print(f"   🌊 Smoothing iterations: {smoothing_iter}")
    
    try:
        # Open input dataset
        input_ds = gdal.Open(input_path, gdal.GA_ReadOnly)
        if input_ds is None:
            raise RuntimeError(f"Cannot open input file: {input_path}")
        
        input_band = input_ds.GetRasterBand(1)
        nodata_value = input_band.GetNoDataValue()
        print(f"   📊 NoData value: {nodata_value}")
        
        stats_before = input_band.GetStatistics(True, True)
        print(f"   📈 Before filling - Min: {stats_before[0]:.2f}, Max: {stats_before[1]:.2f}")
        
        data_array = input_band.ReadAsArray()
        if nodata_value is not None:
            missing_pixels = np.sum(data_array == nodata_value)
        else:
            missing_pixels = np.sum(np.isnan(data_array))
        print(f"   🕳️ Missing pixels to fill: {missing_pixels:,}")
        
        if missing_pixels == 0:
            print(f"   ✅ No missing pixels found, skipping FillNodata")
            driver = gdal.GetDriverByName('GTiff')
            output_ds = driver.CreateCopy(output_path, input_ds, options=['COMPRESS=LZW', 'TILED=YES'])
            output_ds.FlushCache()
            output_ds = None
            input_ds = None
            return
        
        driver = gdal.GetDriverByName('GTiff')
        output_ds = driver.CreateCopy(
            output_path, 
            input_ds, 
            options=['COMPRESS=LZW', 'TILED=YES', 'PREDICTOR=2']
        )
        if output_ds is None:
            raise RuntimeError(f"Cannot create output file: {output_path}")
        
        output_band = output_ds.GetRasterBand(1)
        
        print(f"   🔄 Performing FillNodata interpolation...")
        fillnodata_start = time.time()
        
        result = gdal.FillNodata(
            targetBand=output_band,
            maskBand=None,
            maxSearchDist=max_distance,
            smoothingIterations=smoothing_iter
        )
        
        fillnodata_time = time.time() - fillnodata_start
        
        if result != gdal.CE_None:
            raise RuntimeError(f"FillNodata failed with error code: {result}")
        
        output_ds.FlushCache()
        stats_after = output_band.GetStatistics(True, True)
        print(f"   📈 After filling - Min: {stats_after[0]:.2f}, Max: {stats_after[1]:.2f}")
        
        filled_data = output_band.ReadAsArray()
        if nodata_value is not None:
            remaining_missing = np.sum(filled_data == nodata_value)
        else:
            remaining_missing = np.sum(np.isnan(filled_data))
        
        filled_pixels = missing_pixels - remaining_missing
        fill_percentage = (filled_pixels / missing_pixels * 100) if missing_pixels > 0 else 0
        
        print(f"   ✨ Filled {filled_pixels:,} pixels ({fill_percentage:.1f}%)")
        print(f"   📊 Remaining missing: {remaining_missing:,} pixels")
        print(f"   ✅ Optimized FillNodata completed in {fillnodata_time:.2f} seconds")
        
        output_band = None
        output_ds = None
        input_ds = None
        
        print(f"   💾 Output saved: {output_path}")
        
    except Exception as e:
        print(f"   ❌ FillNodata failed: {str(e)}")
        try:
            if 'output_ds' in locals() and output_ds is not None: output_ds = None
            if 'input_ds' in locals() and input_ds is not None: input_ds = None
        except: pass
        raise e


def create_dtm_fallback_pipeline(input_file: str, output_file: str, resolution: float = 1.0) -> Dict[str, Any]:
    logger.info(f"Creating fallback PMF pipeline for {input_file} with resolution {resolution}m.")
    return {
        "pipeline": [
            input_file,
            {"type": "filters.outlier", "method": "statistical", "multiplier": 2.5, "mean_k": 8},
            {"type": "filters.assign", "assignment": "Classification[:]=0"},
            {"type": "filters.pmf", "max_window_size": 16, "slope": 1, "initial_distance": 0.15, "max_distance": 2.0, "returns": "last,only"},
            {"type": "filters.range", "limits": "Classification[2:2]"},
            {"type": "writers.gdal", "filename": output_file, "resolution": resolution, "output_type": "min", "nodata": -9999, "gdaldriver": "GTiff"}
        ]
    }

def create_dtm_simple_pipeline(input_file: str, output_file: str, resolution: float = 1.0) -> Dict[str, Any]:
    """Create a simple DTM pipeline without advanced ground classification - uses existing ground points only"""
    logger.info(f"Creating simple DTM pipeline for {input_file} with resolution {resolution}m.")
    return {
        "pipeline": [
            input_file,
            {"type": "filters.outlier", "method": "statistical", "multiplier": 3, "mean_k": 8},
            {"type": "filters.range", "limits": "Classification[2:2]"},  # Use only pre-classified ground points
            {"type": "writers.gdal", "filename": output_file, "resolution": resolution, "output_type": "mean", "nodata": -9999, "gdaldriver": "GTiff"}
        ]
    }

def create_dtm_adaptive_pipeline(input_file: str, output_file: str, resolution: float = 1.0) -> Dict[str, Any]:
    logger.info(f"Creating adaptive SMRF pipeline for {input_file} with resolution {resolution}m.")
    return {
        "pipeline": [
            input_file,
            {"type": "filters.outlier", "method": "statistical", "multiplier": 3, "mean_k": 8},
            {"type": "filters.assign", "assignment": "Classification[:]=0"},
            {"type": "filters.smrf", "slope": 0.2, "window": 16, "threshold": 0.45, "scalar": 1.2},
            {"type": "filters.range", "limits": "Classification[2:2]"},
            {"type": "writers.gdal", "filename": output_file, "resolution": resolution, "output_type": "min", "nodata": -9999, "gdaldriver": "GTiff"}
        ]
    }

def dtm(input_file: str, region_name: str = None, resolution: float = 1.0, csf_cloth_resolution: Optional[float] = None) -> str:
    if csf_cloth_resolution is None:
        csf_cloth_resolution = resolution
        logger.info(f"CSF cloth resolution not specified, defaulting to DTM resolution: {csf_cloth_resolution}m for {input_file}.")
    
    print(f"\n🏔️ DTM: Starting conversion for {input_file} (Res: {resolution}m, CSF Cloth: {csf_cloth_resolution}m)")
    logger.info(f"DTM processing for {input_file} with DTM resolution {resolution}m and CSF cloth resolution {csf_cloth_resolution}m.")
    start_time = time.time()
    
    if not os.path.exists(input_file): raise FileNotFoundError(f"Input LAZ file not found: {input_file}")
    if not os.access(input_file, os.R_OK): raise PermissionError(f"Input LAZ file is not readable: {input_file}")
    
    input_path = Path(input_file)
    file_stem = input_path.stem
    output_folder_name = region_name if region_name else file_stem
    output_dir = os.path.join("output", output_folder_name, "lidar", "DTM")
    os.makedirs(output_dir, exist_ok=True)
    
    # Define raw and filled DTM output paths
    raw_dtm_subfolder = os.path.join(output_dir, "raw")
    filled_dtm_subfolder = os.path.join(output_dir, "filled")
    os.makedirs(raw_dtm_subfolder, exist_ok=True)
    os.makedirs(filled_dtm_subfolder, exist_ok=True)

    output_filename_base = f"{file_stem}_DTM_{resolution}m_csf{csf_cloth_resolution}m"
    output_path_dtm_raw = os.path.join(raw_dtm_subfolder, f"{output_filename_base}_raw.tif")
    output_path_dtm_filled = os.path.join(filled_dtm_subfolder, f"{output_filename_base}_filled.tif")
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Raw DTM file: {output_path_dtm_raw}")
    print(f"📄 Filled DTM file: {output_path_dtm_filled}")

    # --- DTM Generation ---
    if os.path.exists(output_path_dtm_raw) and os.path.exists(input_file) and \
       os.path.getmtime(output_path_dtm_raw) > os.path.getmtime(input_file) and \
       validate_dtm_cache(output_path_dtm_raw):
        print(f"🚀 Raw DTM cache hit for {output_path_dtm_raw}. Using existing file.")
        logger.info(f"Raw DTM cache hit for {output_path_dtm_raw}.")
        raw_dtm_generated_path = output_path_dtm_raw
    else:
        print(f"📝 Generating new raw DTM: {output_path_dtm_raw}")
        success, message = convert_las_to_dtm(input_file, output_path_dtm_raw, resolution, csf_cloth_resolution)
        if not success:
            raise Exception(f"DTM generation failed for {output_path_dtm_raw}: {message}")
        raw_dtm_generated_path = output_path_dtm_raw
        print(f"✅ Raw DTM generated: {raw_dtm_generated_path}")

    # --- NoData Filling ---
    if os.path.exists(output_path_dtm_filled) and \
       os.path.getmtime(output_path_dtm_filled) > os.path.getmtime(raw_dtm_generated_path) and \
       validate_dtm_cache(output_path_dtm_filled):
        print(f"🚀 Filled DTM cache hit for {output_path_dtm_filled}. Using existing file.")
        logger.info(f"Filled DTM cache hit for {output_path_dtm_filled}.")
        final_dtm_path = output_path_dtm_filled
    else:
        print(f"🔄 Filling NoData for {raw_dtm_generated_path} -> {output_path_dtm_filled}")
        logger.info(f"Filling NoData for {raw_dtm_generated_path} (Res: {resolution}m, CSF: {csf_cloth_resolution}m). Using default max_distance from function definition.")
        fill_nodata_enhanced(
            input_path=raw_dtm_generated_path,
            output_path=output_path_dtm_filled,
            # max_search_distance is now taken from function default (20)
            smoothing_iter=3
        )
        if not os.path.exists(output_path_dtm_filled):
            raise Exception(f"NoData filling failed to create output: {output_path_dtm_filled}")
        final_dtm_path = output_path_dtm_filled
        print(f"✅ NoData filling complete: {final_dtm_path}")

    # --- Sentinel-2 Cropping (Optional) ---
    try:
        from ..geo_utils import get_image_bounds_from_geotiff, crop_geotiff_to_bbox, intersect_bounding_boxes
        from ..data_acquisition.utils.coordinates import BoundingBox
        sentinel_dir = Path("input") / output_folder_name / "sentinel2"
        sentinel_tifs = list(sentinel_dir.glob("*.tif"))
        if sentinel_tifs:
            sentinel_tifs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            sentinel_tif = sentinel_tifs[0]
            print(f"Found Sentinel-2 tile for potential cropping: {sentinel_tif}")

            dtm_bounds = get_image_bounds_from_geotiff(final_dtm_path)
            s2_bounds = get_image_bounds_from_geotiff(str(sentinel_tif))
            if dtm_bounds and s2_bounds:
                dtm_bb = BoundingBox(north=dtm_bounds['north'], south=dtm_bounds['south'], east=dtm_bounds['east'], west=dtm_bounds['west'])
                s2_bb = BoundingBox(north=s2_bounds['north'], south=s2_bounds['south'], east=s2_bounds['east'], west=s2_bounds['west'])
                inter = intersect_bounding_boxes(dtm_bb, s2_bb)
                if inter:
                    print(f"✂️ Cropping DTM {final_dtm_path} to Sentinel-2 footprint.")
                    temp_crop_filename = Path(final_dtm_path).stem + "_crop.tif"
                    temp_crop_path = Path(final_dtm_path).with_name(temp_crop_filename)

                    if crop_geotiff_to_bbox(final_dtm_path, str(temp_crop_path), inter):
                        os.replace(temp_crop_path, final_dtm_path)
                        print(f"✅ DTM cropped successfully to {final_dtm_path}.")
                    else:
                        print(f"⚠️ DTM cropping to Sentinel-2 footprint failed for {final_dtm_path}.")
                else:
                    print(f"ℹ️ DTM {final_dtm_path} and Sentinel-2 tile {sentinel_tif} do not overlap. No cropping needed.")
            else:
                print(f"⚠️ Could not get bounds for DTM or Sentinel-2 tile. Skipping cropping for {final_dtm_path}.")
        else:
            print(f"ℹ️ No Sentinel-2 tiles found in {sentinel_dir}. Skipping DTM cropping for {final_dtm_path}.")
    except Exception as e:
        print(f"⚠️ DTM cropping failed for {final_dtm_path}: {e}")
        logger.warning(f"DTM cropping failed for {final_dtm_path}: {e}", exc_info=True)
    
    processing_time_total = time.time() - start_time
    print(f"✅ DTM processing for {input_file} completed in {processing_time_total:.2f} seconds. Final DTM: {final_dtm_path}")
    return final_dtm_path


def convert_las_to_dtm(input_file: str, output_file: str, resolution: float = 1.0, csf_cloth_resolution: float = 1.0) -> tuple[bool, str]:
    print(f"\n{'='*60}")
    print(f"🎯 PDAL LAZ TO DTM CONVERSION")
    print(f"{'='*60}")
    print(f"📁 Input LAZ file: {input_file}")
    print(f"📁 Output TIF file: {output_file}")
    print(f"📏 DTM Resolution: {resolution}m")
    print(f"👕 CSF Cloth Resolution: {csf_cloth_resolution}m")
    print(f"🕐 Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"convert_las_to_dtm: Input: {input_file}, Output: {output_file}, Res: {resolution}, CSF Cloth Res: {csf_cloth_resolution}")
    
    message = ""
    pipeline_executed_successfully = False
    
    print(f"🔄 Attempt 1: Using main JSON pipeline (CSF based) from: {PDAL_PIPELINE_JSON_PATH}")
    logger.info(f"Attempting main CSF pipeline for {input_file}.")
    try:
        if not os.path.exists(PDAL_PIPELINE_JSON_PATH):
            raise FileNotFoundError(f"Main PDAL JSON pipeline template not found at {PDAL_PIPELINE_JSON_PATH}")

        with open(PDAL_PIPELINE_JSON_PATH, 'r') as f:
            pipeline_json_str_template = f.read()

        pipeline_str = pipeline_json_str_template.replace("input/default.laz", input_file)
        pipeline_str = pipeline_str.replace("output/default_DTM.tif", output_file)
        pipeline_str = pipeline_str.replace("__RESOLUTION__", str(resolution))
        pipeline_str = pipeline_str.replace("__CLOTH_RESOLUTION__", str(csf_cloth_resolution))
        pipeline_str = pipeline_str.replace('"resolution": "2.0"', f'"resolution": "{str(resolution)}"')
        pipeline_config = json.loads(pipeline_str)

        print(f"📋 Using main JSON pipeline configuration (CSF)")

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(pipeline_config, temp_file, indent=2)
            temp_pipeline_path = temp_file.name

        try:
            print(f"🔄 Executing main PDAL pipeline (CSF) with 300 second timeout...")
            pdal_start_time = time.time()
            result = subprocess.run(['pdal', 'pipeline', temp_pipeline_path], capture_output=True, text=True, timeout=300)
            pdal_execution_time = time.time() - pdal_start_time
            print(f"⏱️ Main PDAL pipeline (CSF) execution completed in {pdal_execution_time:.2f} seconds.")
            
            if result.returncode == 0 and os.path.exists(output_file):
                pipeline_executed_successfully = True
                message = f"DTM generated successfully using main CSF JSON pipeline: {output_file}"
            elif result.returncode != 0:
                message = f"Main CSF PDAL pipeline failed. RC: {result.returncode}. Stderr: {result.stderr}"
            else:
                message = f"Main CSF PDAL pipeline reported success, but output file {output_file} was not created."
        except subprocess.TimeoutExpired:
            message = f"Main CSF PDAL pipeline timed out for {input_file}."
            logger.warning(message)
        except Exception as e:
            message = f"Main CSF PDAL pipeline execution error: {str(e)}"
            logger.warning(message, exc_info=True)
        finally:
            try: os.unlink(temp_pipeline_path)
            except Exception as e_unlink: logger.error(f"Failed to delete temp pipeline file {temp_pipeline_path}: {e_unlink}")
    except Exception as e:
        message = f"Error setting up/reading main JSON pipeline: {str(e)}"
        logger.error(message, exc_info=True)

    if not pipeline_executed_successfully:
        print(f"\n🔄 Attempt 2: Main CSF pipeline failed ({message}). Trying fallback PMF pipeline.")
        logger.info(f"Main CSF pipeline failed for {input_file}. Trying fallback PMF. Prev error: {message}")
        try:
            pipeline_config = create_dtm_fallback_pipeline(input_file, output_file, resolution)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(pipeline_config, temp_file, indent=2)
                temp_pipeline_path = temp_file.name
            try:
                result = subprocess.run(['pdal', 'pipeline', temp_pipeline_path], capture_output=True, text=True, timeout=120)  # Reduced timeout for PMF
                if result.returncode == 0 and os.path.exists(output_file):
                    pipeline_executed_successfully = True
                    message = f"DTM generated successfully using fallback PMF pipeline: {output_file}"
                elif result.returncode != 0:
                    message = f"Fallback PMF PDAL pipeline failed. RC: {result.returncode}. Stderr: {result.stderr}"
                else:
                    message = f"Fallback PMF PDAL pipeline reported success, but output file {output_file} was not created."
            except subprocess.TimeoutExpired:
                message = f"Fallback PMF PDAL pipeline timed out for {input_file}."
                logger.warning(message)
            except Exception as e:
                message = f"Fallback PMF PDAL pipeline execution error: {str(e)}"
                logger.warning(message, exc_info=True)
            finally:
                try: os.unlink(temp_pipeline_path)
                except Exception as e_unlink: logger.error(f"Failed to delete temp fallback pipeline file {temp_pipeline_path}: {e_unlink}")
        except Exception as e:
            prev_message = message
            message = f"Error setting up fallback PMF pipeline: {str(e)}. Previous error: {prev_message}"
            logger.error(message, exc_info=True)

    if not pipeline_executed_successfully:
        print(f"\n🔄 Attempt 3: Fallback PMF pipeline failed ({message}). Trying adaptive SMRF pipeline.")
        logger.info(f"Fallback PMF pipeline failed for {input_file}. Trying adaptive SMRF. Prev error: {message}")
        try:
            pipeline_config = create_dtm_adaptive_pipeline(input_file, output_file, resolution)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(pipeline_config, temp_file, indent=2)
                temp_pipeline_path = temp_file.name
            try:
                result = subprocess.run(['pdal', 'pipeline', temp_pipeline_path], capture_output=True, text=True, timeout=300)
                if result.returncode == 0 and os.path.exists(output_file):
                    pipeline_executed_successfully = True
                    message = f"DTM generated successfully using adaptive SMRF pipeline: {output_file}"
                elif result.returncode != 0:
                    message = f"Adaptive SMRF PDAL pipeline failed. RC: {result.returncode}. Stderr: {result.stderr}"
                else:
                    message = f"Adaptive SMRF PDAL pipeline reported success, but output file {output_file} was not created."
            except subprocess.TimeoutExpired:
                message = f"Adaptive SMRF PDAL pipeline timed out for {input_file}."
                logger.warning(message)
            except Exception as e:
                message = f"Adaptive SMRF PDAL pipeline execution error: {str(e)}"
                logger.warning(message, exc_info=True)
            finally:
                try: os.unlink(temp_pipeline_path)
                except Exception as e_unlink: logger.error(f"Failed to delete temp adaptive pipeline file {temp_pipeline_path}: {e_unlink}")
        except Exception as e:
            prev_message = message
            message = f"Error setting up adaptive SMRF pipeline: {str(e)}. Previous error: {prev_message}"
            logger.error(message, exc_info=True)

    if not pipeline_executed_successfully:
        print(f"\n🔄 Attempt 4: All advanced pipelines failed ({message}). Trying simple ground-only pipeline.")
        logger.info(f"All advanced pipelines failed for {input_file}. Trying simple ground-only pipeline. Prev error: {message}")
        try:
            pipeline_config = create_dtm_simple_pipeline(input_file, output_file, resolution)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(pipeline_config, temp_file, indent=2)
                temp_pipeline_path = temp_file.name
            try:
                result = subprocess.run(['pdal', 'pipeline', temp_pipeline_path], capture_output=True, text=True, timeout=300)
                if result.returncode == 0 and os.path.exists(output_file):
                    pipeline_executed_successfully = True
                    message = f"DTM generated successfully using simple ground-only pipeline: {output_file}"
                elif result.returncode != 0:
                    message = f"Simple ground-only PDAL pipeline failed. RC: {result.returncode}. Stderr: {result.stderr}"
                else:
                    message = f"Simple ground-only PDAL pipeline reported success, but output file {output_file} was not created."
            except subprocess.TimeoutExpired:
                message = f"Simple ground-only PDAL pipeline timed out for {input_file}."
                logger.warning(message)
            except Exception as e:
                message = f"Simple ground-only PDAL pipeline execution error: {str(e)}"
                logger.warning(message, exc_info=True)
            finally:
                try: os.unlink(temp_pipeline_path)
                except Exception as e_unlink: logger.error(f"Failed to delete temp simple pipeline file {temp_pipeline_path}: {e_unlink}")
        except Exception as e:
            prev_message = message
            message = f"Error setting up simple ground-only pipeline: {str(e)}. Previous error: {prev_message}"
            logger.error(message, exc_info=True)

    success = pipeline_executed_successfully
    print(f"{'='*60}")
    if success:
        print(f"✅ DTM generation successful: {output_file}. Message: {message}")
        logger.info(f"DTM generation successful for {input_file}, output at {output_file}. Message: {message}")
    else:
        print(f"❌ DTM generation failed for {input_file}. Final message: {message}")
        logger.error(f"DTM generation failed for {input_file}. Final message: {message}")
    print(f"🕐 End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    return success, message

def clear_dtm_cache(input_file: str = None, resolution: Optional[float] = None, csf_cloth_resolution: Optional[float] = None) -> None:
    if input_file:
        input_path = Path(input_file)
        file_stem = input_path.stem
        region_name = input_path.parts[input_path.parts.index("input") + 1] if "lidar" in input_path.parts else (input_path.parent.name if input_path.parent.name != "input" else file_stem)
        
        actual_csf_res = csf_cloth_resolution if csf_cloth_resolution is not None else resolution
        dtm_filename_pattern = f"{file_stem}_DTM_{resolution}m_csf{actual_csf_res}m_*.tif" if resolution is not None else f"{file_stem}_DTM*.tif"

        output_dir_base = Path("output") / region_name / "lidar" / "DTM"
        patterns_to_check = [output_dir_base / "raw" / dtm_filename_pattern, output_dir_base / "filled" / dtm_filename_pattern]
        
        files_to_remove = []
        import glob
        for pattern in patterns_to_check:
            files_to_remove.extend(glob.glob(str(pattern)))
        
        cleared_count = 0
        for f_path in files_to_remove:
            if os.path.exists(f_path):
                try: os.remove(f_path); print(f"🗑️ Cleared DTM cache file: {f_path}"); cleared_count +=1
                except OSError as e: print(f"⚠️ Failed to clear DTM cache file {f_path}: {e}")
        if not files_to_remove: print(f"📭 No DTM cache found matching pattern for {file_stem} in {output_dir_base}")
        elif cleared_count == 0 : print(f"📭 No DTM cache files actually removed despite matching pattern for {file_stem} in {output_dir_base}")


    else:
        import glob
        base_output_dir = Path("output")
        pattern_suffix = f"_DTM_{resolution}m_csf{csf_cloth_resolution if csf_cloth_resolution is not None else resolution}m_*.tif" if resolution is not None else "_DTM*.tif"

        all_dtm_files = list(base_output_dir.glob(f"*/lidar/DTM/raw/*{pattern_suffix}")) + \
                        list(base_output_dir.glob(f"*/lidar/DTM/filled/*{pattern_suffix}"))

        cleared_count = 0
        if not all_dtm_files:
            print(f"📭 No DTM cache files found matching criteria (Res: {resolution}m, CSF: {csf_cloth_resolution}m if specified).")
            return
        for dtm_file in all_dtm_files:
            try: os.remove(dtm_file); cleared_count += 1
            except OSError as e: print(f"⚠️ Failed to remove {dtm_file}: {e}")
        print(f"🗑️ Cleared {cleared_count} DTM cache files matching criteria.")

def get_dtm_cache_info(resolution: Optional[float] = None, csf_cloth_resolution: Optional[float] = None) -> dict:
    import glob
    base_output_dir = Path("output")
    actual_csf_res = csf_cloth_resolution if csf_cloth_resolution is not None and resolution is not None else resolution
    pattern_suffix = f"_DTM_{resolution}m_csf{actual_csf_res}m_*.tif" if resolution is not None else "_DTM*.tif"

    all_dtm_files = list(base_output_dir.glob(f"*/lidar/DTM/raw/*{pattern_suffix}")) + \
                    list(base_output_dir.glob(f"*/lidar/DTM/filled/*{pattern_suffix}"))
    
    cache_info = {"total_cached_dtms": len(all_dtm_files), "filter_criteria": {"resolution": resolution, "csf_cloth_resolution": actual_csf_res if resolution else None}, "cached_files": []}
    total_size = 0
    for dtm_file_path_obj in all_dtm_files:
        dtm_file = str(dtm_file_path_obj)
        try:
            file_stat = os.stat(dtm_file)
            size_mb = file_stat.st_size / (1024 * 1024)
            total_size += size_mb
            cache_info["cached_files"].append({"file": dtm_file, "size_mb": round(size_mb, 2), "created": time.ctime(file_stat.st_mtime)})
        except OSError: continue
    cache_info["total_size_mb"] = round(total_size, 2)
    return cache_info

def validate_dtm_cache(dtm_path: str) -> bool:
    try:
        from osgeo import gdal
        gdal.UseExceptions()
        dataset = gdal.Open(dtm_path, gdal.GA_ReadOnly)
        if dataset is None: return False
        if dataset.RasterXSize <= 0 or dataset.RasterYSize <= 0 or dataset.RasterCount != 1: dataset = None; return False
        band = dataset.GetRasterBand(1)
        if band is None: dataset = None; return False
        try: band.ReadRaster(0, 0, min(dataset.RasterXSize, 5), min(dataset.RasterYSize, 5))
        except RuntimeError: dataset = None; return False
        dataset = None
        return True
    except Exception: return False # Broad exception for any GDAL/OS issue

def get_cache_statistics(resolution: Optional[float] = None, csf_cloth_resolution: Optional[float] = None) -> str:
    cache_info = get_dtm_cache_info(resolution=resolution, csf_cloth_resolution=csf_cloth_resolution)
    report = [f"📊 DTM CACHE STATISTICS (Filter: Res={resolution}m, CSF={csf_cloth_resolution if csf_cloth_resolution is not None and resolution is not None else resolution}m)" if resolution is not None else "📊 DTM CACHE STATISTICS (No filter)"]
    report.append("=" * 70)
    report.append(f"🗂️ Total cached DTMs (matching filter): {cache_info['total_cached_dtms']}")
    report.append(f"💾 Total cache size (matching filter): {cache_info['total_size_mb']:.2f} MB")
    if cache_info['cached_files']:
        report.append("\n📁 Cached Files (matching filter):")
        for i, file_info in enumerate(cache_info['cached_files'], 1):
            try: region_part = Path(file_info['file']).parts[-5]
            except IndexError: region_part = "UnknownRegion"
            report.append(f"   {i}. {region_part}/{Path(file_info['file']).parent.name}/{Path(file_info['file']).name} (Size: {file_info['size_mb']:.2f} MB, Created: {file_info['created']})")
    else: report.append("\n📭 No DTM files currently cached matching the filter criteria.")
    if cache_info['total_cached_dtms'] > 0:
        estimated_min_savings, estimated_max_savings = cache_info['total_cached_dtms'] * 20, cache_info['total_cached_dtms'] * 120
        report.append(f"\n⚡ Estimated time saved by caching: {estimated_min_savings/60:.1f} to {estimated_max_savings/60:.1f} minutes (approx.)")
    report.append("=" * 70)
    return "\n".join(report)

async def process_dtm(laz_file_path: str, output_dir_param: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    start_time_main_process = time.time()
    dtm_resolution = parameters.get("resolution", 1.0)
    csf_resolution = parameters.get("csf_cloth_resolution", None)

    print(f"\n{'='*60}\n🏔️ DTM PROCESSING STARTING (Async Wrapper)\n{'='*60}")
    print(f"📁 Input LAZ: {laz_file_path}\n📂 Base Output: {output_dir_param}")
    print(f"⚙️ Params: Res={dtm_resolution}m, CSF Cloth={csf_resolution if csf_resolution is not None else 'Default to Res'}")
    logger.info(f"Async DTM for {laz_file_path}. Base out: {output_dir_param}. Res={dtm_resolution}, CSF={csf_resolution}")
    
    try:
        input_path_obj = Path(laz_file_path)
        region_name_from_output_dir = Path(output_dir_param).name
        
        print(f"🗺️ Region from output_dir: {region_name_from_output_dir}, File stem: {input_path_obj.stem}")
        
        loop = asyncio.get_event_loop()
        final_dtm_path = await loop.run_in_executor(None, dtm, laz_file_path, region_name_from_output_dir, dtm_resolution, csf_resolution)
            
        if "failed" in final_dtm_path.lower() or "error" in final_dtm_path.lower() or not os.path.exists(final_dtm_path):
            raise Exception(f"DTM generation function error or file not found: {final_dtm_path}")
            
        file_size_mb = os.path.getsize(final_dtm_path) / (1024 * 1024)
        total_time = time.time() - start_time_main_process
        print(f"✅ Async DTM processing complete. Output: {final_dtm_path}, Size: {file_size_mb:.2f}MB, Time: {total_time:.2f}s")
            
        return {
            "success": True, "output_file": final_dtm_path, "processing_time": total_time,
            "region_name": region_name_from_output_dir, "file_size_mb": file_size_mb,
            "parameters_used": {"resolution": dtm_resolution, "csf_cloth_resolution": csf_resolution if csf_resolution is not None else dtm_resolution},
            "message": f"DTM processed successfully in {total_time:.2f} seconds."
        }
    except Exception as e:
        total_time = time.time() - start_time_main_process
        error_msg = f"DTM processing failed in async wrapper: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "error": error_msg, "processing_time": total_time, "message": error_msg}

# Simplified cache/utility functions for brevity in this overwrite, assuming full versions are more complex if needed.
# The primary goal here is the dtm() and fill_nodata_enhanced() logic.
