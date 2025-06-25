import asyncio
import time
import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from osgeo import gdal, ogr, osr
from .dtm import dtm

logger = logging.getLogger(__name__)

async def process_color_relief(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Color-relief from LAZ file
    """
    start_time = time.time()
    
    try:
        print(f"\n{'='*60}")
        print(f"🎨 COLOR RELIEF PROCESSING (Async Wrapper)")
        print(f"{'='*60}")
        print(f"📂 Input file: {laz_file_path}")
        print(f"📁 Base Output directory for this run: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Base output directory for async call ensured: {output_dir}")
        
        input_path_obj = Path(laz_file_path)
        derived_region_name = input_path_obj.stem
        try:
            if "input" in input_path_obj.parts:
                derived_region_name = input_path_obj.parts[input_path_obj.parts.index("input") + 1]
        except (ValueError, IndexError):
            logger.warning(f"Could not derive region_name from path {laz_file_path} using 'input' anchor. Defaulting to file stem '{derived_region_name}'.")
        
        print(f"Derived region_name for sync function override: {derived_region_name}")

        # Updated default ramp_name and added DTM resolution params
        ramp_name_param = parameters.get("ramp_name", "arch_subtle")
        dtm_resolution_param = parameters.get("dtm_resolution", 1.0)
        dtm_csf_cloth_resolution_param = parameters.get("dtm_csf_cloth_resolution", None)
        actual_csf_res_param = dtm_csf_cloth_resolution_param if dtm_csf_cloth_resolution_param is not None else dtm_resolution_param


        file_stem_for_log = Path(laz_file_path).stem
        tentative_output_filename = f"{file_stem_for_log}_ColorRelief_dtm{dtm_resolution_param}m_csf{actual_csf_res_param}m_{ramp_name_param}.tif"
        print(f"📄 Tentative output filename (for logging purposes): {tentative_output_filename}")
        logger.info(f"Async process_color_relief called with ramp: {ramp_name_param}, DTM Res: {dtm_resolution_param}m, CSF Res: {actual_csf_res_param}m for {laz_file_path}")

        if not os.path.exists(laz_file_path):
            error_msg = f"LAZ file not found: {laz_file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        print(f"🔄 Calling synchronous color_relief function with ramp '{ramp_name_param}', region_override '{derived_region_name}', DTM Res: {dtm_resolution_param}m, CSF Res: {actual_csf_res_param}m...")
        
        actual_output_file_path = color_relief(
            input_file=laz_file_path,
            ramp_name=ramp_name_param,
            region_name_override=derived_region_name,
            dtm_resolution=dtm_resolution_param, # Pass through
            dtm_csf_cloth_resolution=dtm_csf_cloth_resolution_param # Pass through
        )
        
        output_file = actual_output_file_path
        output_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
        
        processing_time = time.time() - start_time
        
        print(f"✅ Synchronous color_relief completed. Output: {output_file}")
        print(f"⏱️ Total Color Relief processing time (async wrapper): {processing_time:.2f} seconds")
        logger.info(f"Color-relief processing completed in {processing_time:.2f} seconds. Output: {output_file}")
        
        return {
            "success": True,
            "message": "Color-relief processing completed successfully",
            "output_file": output_file,
            "processing_time": processing_time,
            "metadata": {
                "input_file": laz_file_path,
                "processing_type": "Color-relief",
                "ramp_name": ramp_name_param,
                "dtm_resolution": dtm_resolution_param,
                "dtm_csf_cloth_resolution": actual_csf_res_param,
                "file_size_bytes": output_size
            }
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Color-relief processing failed in async wrapper: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Color-relief processing failed: {str(e)}",
            "processing_time": processing_time,
            "metadata": {"input_file": laz_file_path, "processing_type": "Color-relief", "error": str(e)}
        }

def create_color_table(color_table_path: str, min_elevation: float, max_elevation: float, ramp_name: str = "terrain") -> None:
    print(f"🎨 Creating color table (ramp: {ramp_name}) for elevation range: {min_elevation:.2f} to {max_elevation:.2f}")
    logger.info(f"Creating color table '{color_table_path}' with ramp '{ramp_name}' for range {min_elevation:.2f}-{max_elevation:.2f}")

    if ramp_name == "terrain":
        color_stops_config = [(0.0, "0 0 139"), (0.1, "0 100 255"), (0.2, "0 255 255"), (0.3, "0 255 0"), (0.5, "255 255 0"), (0.7, "255 165 0"), (0.9, "255 69 0"), (1.0, "255 255 255")]
    elif ramp_name == "arch_subtle":
        color_stops_config = [(0.0, "200 180 160"), (0.2, "220 200 180"), (0.4, "180 160 140"), (0.6, "230 210 190"), (0.8, "240 220 200"), (1.0, "255 245 235")]
    elif ramp_name == "archaeological_gentle":
        # 🟣 Gentler elevation-based color ramp with 5 soft color bands
        # Pale yellow -> orange -> salmon -> red -> light red (ascending elevation zones)
        color_stops_config = [
            (0.0, "255 250 220"),   # Pale cream/yellow (lowest elevation)
            (0.25, "255 228 181"),  # Soft peach/orange
            (0.5, "255 192 152"),   # Gentle salmon
            (0.75, "255 160 122"),  # Soft coral/light red
            (1.0, "255 140 105")    # Warm light red (highest elevation)
        ]
    elif ramp_name == "grayscale":
        color_stops_config = [(0.0, "0 0 0"), (1.0, "255 255 255")]
    else:
        logger.error(f"Unknown ramp_name: {ramp_name}")
        raise ValueError(f"Unknown ramp_name: {ramp_name}. Available: 'terrain', 'arch_subtle', 'archaeological_gentle', 'grayscale'.")

    elevation_range = max_elevation - min_elevation
    if abs(elevation_range) < 1e-6:
        print(f"⚠️ DTM is effectively flat. Creating simplified color table for ramp '{ramp_name}'.")
        logger.warning(f"DTM for {color_table_path} is flat. Using simplified color table.")
        with open(color_table_path, 'w') as f:
            target_rgb_idx = len(color_stops_config) // 2 if len(color_stops_config) > 1 else 0
            target_rgb = color_stops_config[target_rgb_idx][1]
            if ramp_name == "grayscale": target_rgb = "128 128 128"
            if ramp_name == "grayscale" and abs(min_elevation) < 1e-6 and abs(max_elevation) < 1e-6 : target_rgb = "0 0 0"

            f.write(f"{min_elevation:.2f} {target_rgb}\n")
            if elevation_range > 1e-9:
                 f.write(f"{max_elevation:.2f} {color_stops_config[-1][1]}\n")
        print(f"📊 Simplified color table created: {color_table_path}")
        return
    
    with open(color_table_path, 'w') as f:
        for percentage, rgb in color_stops_config:
            elevation = min_elevation + (percentage * elevation_range)
            f.write(f"{elevation:.2f} {rgb}\n")
    
    print(f"📊 Color table (ramp: {ramp_name}) created: {color_table_path}")

def color_relief(
    input_file: str,
    ramp_name: str = "arch_subtle", # Changed default to arch_subtle
    region_name_override: Optional[str] = None,
    dtm_resolution: float = 1.0,
    dtm_csf_cloth_resolution: Optional[float] = None
) -> str:
    gdal.UseExceptions()
    actual_csf_res = dtm_csf_cloth_resolution if dtm_csf_cloth_resolution is not None else dtm_resolution
    print(f"\n🎨 COLOR_RELIEF (Sync): Starting generation for {input_file} with ramp '{ramp_name}', DTM Res: {dtm_resolution}m, CSF Res: {actual_csf_res}m")
    logger.info(f"Sync color_relief for {input_file}, ramp: {ramp_name}, region_override: {region_name_override}, DTM Res: {dtm_resolution}m, CSF Res: {actual_csf_res}m")
    start_time = time.time()
    
    input_path = Path(input_file)
    file_stem = input_path.stem

    if region_name_override:
        effective_region_name = region_name_override
    elif "input" in input_path.parts and "lidar" in input_path.parts :
        try: effective_region_name = input_path.parts[input_path.parts.index("input") + 1]
        except (ValueError, IndexError): effective_region_name = file_stem
    elif "input" in input_path.parts :
        try: effective_region_name = input_path.parts[input_path.parts.index("input") + 1]
        except (ValueError, IndexError): effective_region_name = file_stem
    else:
        effective_region_name = input_path.parent.name if input_path.parent.name and input_path.parent.name != "." else file_stem
        if not effective_region_name : effective_region_name = file_stem
    logger.info(f"Effective region name for output: {effective_region_name}")
    
    output_dir = Path("output") / effective_region_name / "lidar" / "Color_Relief"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_filename = f"{file_stem}_ColorRelief_dtm{dtm_resolution}m_csf{actual_csf_res}m_{ramp_name}.tif"
    output_path_obj = output_dir / output_filename
    
    color_table_filename = f"{file_stem}_dtm{dtm_resolution}m_csf{actual_csf_res}m_color_table_{ramp_name}.txt"
    color_table_path_obj = output_dir / color_table_filename
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path_obj}")
    print(f"🎨 Color table file: {color_table_path_obj}")

    print(f"\n🏔️ Step 1: Generating/retrieving DTM (Res: {dtm_resolution}m, CSF: {actual_csf_res}m)...")
    dtm_path_str = dtm(
        input_file,
        region_name=effective_region_name,
        resolution=dtm_resolution,
        csf_cloth_resolution=dtm_csf_cloth_resolution
    )
    dtm_path_obj = Path(dtm_path_str)
    if not dtm_path_obj.exists():
        raise FileNotFoundError(f"DTM file not found at {dtm_path_obj} as reported by dtm()")
    print(f"✅ DTM ready: {dtm_path_obj}")

    if output_path_obj.exists() and dtm_path_obj.exists() and \
       output_path_obj.stat().st_mtime > dtm_path_obj.stat().st_mtime:
        print(f"   🚀 CACHE HIT for {output_path_obj}. Using existing file.")
        logger.info(f"Cache hit for color relief {output_path_obj}.")
        return str(output_path_obj)
    
    print(f"   ⏳ CACHE MISS for {output_path_obj}. Generating new color relief.")
    logger.info(f"Cache miss for {output_path_obj}. Generating.")

    try:
        print(f"\n🔍 Validating DTM ({dtm_path_obj}) with gdalinfo...")
        try:
            dtm_info_result = subprocess.run(['gdalinfo', str(dtm_path_obj)], capture_output=True, text=True, check=True, timeout=15)
        except Exception as e_gdalinfo:
            logger.error(f"gdalinfo validation failed for DTM {dtm_path_obj}: {e_gdalinfo}", exc_info=True)
            raise RuntimeError(f"gdalinfo validation failed for DTM {dtm_path_obj}: {e_gdalinfo}")
        print(f"✅ DTM ({dtm_path_obj}) validated.")

        print(f"\n📊 Step 2: Analyzing DTM statistics...")
        dtm_dataset = gdal.Open(str(dtm_path_obj))
        if dtm_dataset is None: raise RuntimeError(f"Failed to open DTM: {dtm_path_obj}")
        band = dtm_dataset.GetRasterBand(1)
        band.ComputeStatistics(False)
        min_elevation, max_elevation = band.GetMinimum(), band.GetMaximum()
        if min_elevation is None or max_elevation is None:
            stats_fallback = band.GetStatistics(True, True)
            min_elevation, max_elevation = stats_fallback[0], stats_fallback[1]
        dtm_dataset = None
        print(f"📊 DTM Stats: Min={min_elevation:.2f}, Max={max_elevation:.2f}")
        
        print(f"\n🎨 Step 3: Creating color table '{ramp_name}' for {color_table_path_obj}...")
        create_color_table(str(color_table_path_obj), min_elevation, max_elevation, ramp_name=ramp_name)
        
        if not color_table_path_obj.exists() or color_table_path_obj.stat().st_size == 0:
            raise RuntimeError(f"Color table file not created/empty: {color_table_path_obj}")
        
        print(f"\n🎨 Step 4: Generating color relief using GDAL DEMProcessing...")
        creation_options = ['COMPRESS=LZW', 'TILED=YES', 'PHOTOMETRIC=RGB']
        gdal_options = gdal.DEMProcessingOptions(colorFilename=str(color_table_path_obj), format="GTiff", creationOptions=creation_options)
        
        result_ds = gdal.DEMProcessing(destName=str(output_path_obj), srcDS=str(dtm_path_obj), processing="color-relief", options=gdal_options)
        
        if result_ds is None: raise RuntimeError(f"GDAL DEMProcessing returned None for: {output_path_obj}.")
        result_ds = None

        if not output_path_obj.exists() or output_path_obj.stat().st_size == 0:
            raise RuntimeError(f"GDAL DEMProcessing failed to create non-empty output: {output_path_obj}")

        print(f"✅ Color relief generation completed: {output_path_obj}")
        logger.info(f"Color relief generation completed for {output_path_obj}")
        
        total_time = time.time() - start_time
        print(f"✅ COLOR_RELIEF (Sync) completed successfully in {total_time:.2f} seconds")
        return str(output_path_obj)
        
    except Exception as e:
        total_time = time.time() - start_time
        error_msg = f"Color relief (sync) for '{input_file}', ramp '{ramp_name}', DTM res {dtm_resolution}m failed: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        if isinstance(e, RuntimeError): raise
        raise Exception(error_msg) from e
