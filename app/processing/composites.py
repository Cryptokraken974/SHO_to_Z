# app/processing/composites.py
import os
import numpy as np
import rasterio
from rasterio.enums import Resampling
from PIL import Image, ImageEnhance
import tempfile
from pathlib import Path
import time
import logging

from .dtm import dtm as get_dtm_path # To get/generate DTM
from .hillshade import generate_hillshade_with_params # To get/generate Hillshade
from .color_relief import color_relief as get_color_relief_dtm_path # To generate colorized DTM

logger = logging.getLogger(__name__)

def generate_dtm_hillshade_blend(
    laz_input_file: str,
    region_name_for_output: str, # Used for naming and pathing conventions
    dtm_resolution: float = 1.0,
    dtm_csf_cloth_resolution: float = None, # Will default to dtm_resolution in dtm_processing
    hillshade_azimuth: float = 315.0,
    hillshade_altitude: float = 45.0,
    hillshade_z_factor: float = 1.0,
    hillshade_suffix: str = "standard", # Suffix for the hillshade component
    blend_factor: float = 0.6, # 0.0 = full hillshade, 1.0 = full color DTM
    # output_resolution_factor: float = 1.0 # Factor to scale output resolution (e.g., 0.5 for half resolution) - Not implemented yet
) -> str:
    """
    Generates a blended DTM and Hillshade composite GeoTIFF.
    The DTM is first colorized using the standard color_relief logic.
    This colorized DTM is then blended with a specified hillshade.
    Output paths will follow conventions like:
    output/<region_name_for_output>/lidar/Composites/<input_stem>_DTM{res}m_CSF{csf_res}_HS_az{az}_alt{alt}_z{z}_blend.tif
    """
    print(f"
🎨 COMPOSITE: Starting DTM-Hillshade Blend for LAZ: {laz_input_file}")
    logger.info(f"Starting DTM-Hillshade Blend for LAZ: {laz_input_file}, Region: {region_name_for_output}")
    start_time = time.time()

    laz_path = Path(laz_input_file)
    input_file_stem = laz_path.stem

    # Determine csf_cloth_resolution if None
    actual_csf_cloth_resolution = dtm_csf_cloth_resolution if dtm_csf_cloth_resolution is not None else dtm_resolution

    print(f"Parameters: DTM Res={dtm_resolution}m, CSF Res={actual_csf_cloth_resolution}m, HS Az={hillshade_azimuth}, HS Alt={hillshade_altitude}, HS Z={hillshade_z_factor}, Blend Factor={blend_factor}")
    logger.info(f"Composite Params: DTM Res={dtm_resolution}m, CSF Res={actual_csf_cloth_resolution}m, HS Az={hillshade_azimuth}, HS Alt={hillshade_altitude}, HS Z={hillshade_z_factor}, Blend Factor={blend_factor}")

    # --- Step 1: Generate Colorized DTM (RGB TIFF) ---
    # The color_relief function takes the LAZ file as input and generates the DTM internally.
    # Its output is already an RGB TIFF.
    # TODO: The current `color_relief.py` does not accept dtm_resolution or csf_cloth_resolution.
    # It will use the defaults set within the `dtm()` function it calls.
    # This means the DTM used for color_relief might have a different resolution profile
    # than the DTM used for the hillshade if different parameters are passed here.
    # For true consistency, color_relief.py would need to be updated to accept these.
    # For now, we proceed, and the DTM for color relief will use dtm() defaults or its own logic.
    print(f"🎨 Step 1: Generating Colorized DTM (RGB) from {laz_input_file}...")
    logger.info("Generating Colorized DTM for composite.")
    try:
        # Assuming color_relief is called with region_name_for_output so its internal DTM call
        # also uses this for pathing, ensuring cache hits if DTM was already made by hillshade's DTM call later.
        # The `color_relief` function expects `region_name` as its second arg.
        color_dtm_path_str = get_color_relief_dtm_path(laz_input_file, region_name_for_output)
        color_dtm_path = Path(color_dtm_path_str)
        if not color_dtm_path.exists():
            logger.error(f"Colorized DTM not found at {color_dtm_path} after generation call.")
            raise FileNotFoundError(f"Colorized DTM not found at {color_dtm_path} after generation call.")
    except Exception as e:
        print(f"❌ Error generating colorized DTM: {e}")
        logger.error(f"Error generating colorized DTM: {e}", exc_info=True)
        raise
    print(f"✅ Colorized DTM (RGB) path: {color_dtm_path}")
    logger.info(f"Colorized DTM path: {color_dtm_path}")

    # --- Step 2: Generate Hillshade ---
    # generate_hillshade_with_params takes the LAZ file as input and specific dtm resolution params
    print(f"🌄 Step 2: Generating Hillshade from {laz_input_file}...")
    logger.info("Generating Hillshade for composite.")
    try:
        hillshade_path_str = generate_hillshade_with_params(
            input_file=laz_input_file,
            azimuth=hillshade_azimuth,
            altitude=hillshade_altitude,
            z_factor=hillshade_z_factor,
            suffix=hillshade_suffix,
            region_name=region_name_for_output, # For consistent output pathing
            dtm_resolution=dtm_resolution,
            dtm_csf_cloth_resolution=actual_csf_cloth_resolution
        )
        hillshade_path = Path(hillshade_path_str)
        if not hillshade_path.exists():
            logger.error(f"Hillshade not found at {hillshade_path} after generation call.")
            raise FileNotFoundError(f"Hillshade not found at {hillshade_path} after generation call.")
    except Exception as e:
        print(f"❌ Error generating hillshade: {e}")
        logger.error(f"Error generating hillshade: {e}", exc_info=True)
        raise
    print(f"✅ Hillshade path: {hillshade_path}")
    logger.info(f"Hillshade path: {hillshade_path}")

    # --- Step 3: Blend Color DTM and Hillshade ---
    print(f"🔄 Step 3: Blending {color_dtm_path.name} and {hillshade_path.name}...")
    logger.info(f"Blending {color_dtm_path.name} and {hillshade_path.name}")

    try:
        with rasterio.open(color_dtm_path) as color_src, rasterio.open(hillshade_path) as hs_src:
            if color_src.count < 3:
                msg = f"Colorized DTM {color_dtm_path} is not RGB (has {color_src.count} bands)."
                logger.error(msg)
                raise ValueError(msg)

            # Read hillshade and resample to color_dtm's shape/transform if they differ
            # This ensures pixel-wise operations are aligned.
            hillshade_data_resampled = hs_src.read(
                1, # Read first band of hillshade
                out_shape=(color_src.height, color_src.width), # Match shape of color_dtm
                resampling=Resampling.bilinear # Use bilinear for continuous data
            )

            # Normalize hillshade data to 0-1 range for blending
            hs_min, hs_max = np.min(hillshade_data_resampled), np.max(hillshade_data_resampled)
            if hs_max == hs_min: # Avoid division by zero if hillshade is flat
                hillshade_norm = np.full_like(hillshade_data_resampled, 0.5, dtype=np.float32)
            else:
                hillshade_norm = (hillshade_data_resampled - hs_min) / (hs_max - hs_min)

            # Prepare output profile based on color_dtm (which is RGB)
            profile = color_src.profile.copy() # Important to copy
            profile.update(
                count=3, # Ensure output is 3-band RGB
                driver='GTiff',
                compress='lzw',
                tiled=True,
                photometric='RGB' # Explicitly set photometric for RGB
            )
            if 'interleave' in profile: # Not always compatible with LZW + RGB
                del profile['interleave']


            # Define output path for the composite
            composite_output_dir = Path("output") / region_name_for_output / "lidar" / "Composites"
            composite_output_dir.mkdir(parents=True, exist_ok=True)

            # Construct a descriptive filename for the composite
            hs_params_suffix = f"HS_az{int(hillshade_azimuth)}_alt{int(hillshade_altitude)}_z{str(hillshade_z_factor).replace('.', 'p')}"
            blend_filename = f"{input_file_stem}_DTM{dtm_resolution}m_CSF{actual_csf_cloth_resolution}m_{hs_params_suffix}_blend{str(blend_factor).replace('.','p')}.tif"
            composite_output_path = composite_output_dir / blend_filename

            print(f"💾 Output composite path: {composite_output_path}")
            logger.info(f"Saving blended composite to: {composite_output_path}")

            with rasterio.open(composite_output_path, 'w', **profile) as dst:
                for i in range(1, 4): # Iterate R, G, B bands (1, 2, 3)
                    color_band_data = color_src.read(i).astype(np.float32) # Read as float32 for calculations

                    # Blending: Modulate brightness of color by hillshade
                    # Formula: Output = Color * ( (1-blend_factor) + blend_factor * Hillshade_Normalized )
                    # Or: Output = Color * ( (Hillshade_Normalized * weight_hs) + (1 - weight_hs) )
                    # Let blend_factor control visibility of color_dtm (0.0 = all hillshade brightness, 1.0 = all color_dtm brightness)
                    # So, if blend_factor = 0.6 (more color):
                    # color_weight = blend_factor
                    # shade_effect_on_color = (1-blend_factor) -> how much hillshade modulates the color
                    # blended_band = color_band_data * ( (1-shade_effect_on_color) + shade_effect_on_color * hillshade_norm )
                    # blended_band = color_band_data * ( blend_factor + (1-blend_factor) * hillshade_norm)

                    # A common GIS approach: (Color * (1-alpha)) + (Color * Hillshade_norm * alpha)
                    # where alpha is hillshade transparency (0 = opaque hillshade, 1 = transparent hillshade)
                    # Let's map blend_factor to hillshade influence:
                    # hillshade_influence = 1.0 - blend_factor
                    # So, if blend_factor = 0.6 (color is 60% dominant), hillshade_influence = 0.4

                    # Output = Color * (1 - Hillshade_Influence) + (Color * Hillshade_Norm) * Hillshade_Influence
                    # Output = Color * blend_factor + Color * Hillshade_Norm * (1 - blend_factor)
                    # Output = Color * (blend_factor + Hillshade_Norm * (1 - blend_factor))

                    blended_band = color_band_data * (blend_factor + hillshade_norm * (1.0 - blend_factor))

                    blended_band = np.clip(blended_band, 0, 255) # Clip to valid 8-bit range
                    dst.write(blended_band.astype(np.uint8), i) # Write as uint8

        total_time = time.time() - start_time
        print(f"✅ Composite DTM-Hillshade blend generated successfully in {total_time:.2f}s: {composite_output_path}")
        logger.info(f"Composite DTM-Hillshade blend generated successfully: {composite_output_path}")
        return str(composite_output_path)

    except Exception as e:
        print(f"❌ Error blending DTM and Hillshade: {e}")
        logger.error(f"Error blending DTM and Hillshade: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    # This example usage section is for direct module testing and might require adjustments
    # to paths and availability of test data to run correctly.
    # It also assumes that the dependent functions (dtm, hillshade, color_relief)
    # are correctly set up and accessible in this environment.

    # Configure basic logging for testing if run directly
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("Testing DTM-Hillshade Blend Generation (Example)...")

    # --- IMPORTANT ---
    # For this test to work, you NEED:
    # 1. A valid LAZ file at the specified `test_laz_file_path`.
    # 2. The `dtm.py`, `hillshade.py`, and `color_relief.py` modules to be functional
    #    and correctly located relative to this `composites.py` file for the imports to work.
    # 3. The `output` directory structure to be writable.
    #
    # Replace with a path to an actual LAZ file in your project structure.
    # Example: test_laz_file_path = "input/YOUR_REGION/lidar/YOUR_FILE.laz"
    # Ensure that 'YOUR_REGION' is a directory under 'input/' that contains 'lidar/YOUR_FILE.laz'.

    # As a placeholder, this points to a non-existent file.
    # The test will likely fail unless this path is updated to a real LAZ file.
    test_laz_file_path = "input/TestRegionForComposites/lidar/sample.laz"
    test_region_name = "TestRegionForComposites"

    # Create dummy LAZ for basic path testing if it doesn't exist
    # WARNING: This dummy LAZ is NOT processable by PDAL.
    # For a real test, replace `test_laz_file_path` with a path to a valid LAZ file.
    dummy_laz_path_obj = Path(test_laz_file_path)
    if not dummy_laz_path_obj.exists():
        print(f"Test LAZ file not found at: {test_laz_file_path}")
        print("Please update 'test_laz_file_path' in composites.py __main__ to a valid LAZ file for testing.")
        # dummy_laz_path_obj.parent.mkdir(parents=True, exist_ok=True)
        # with open(dummy_laz_path_obj, "w") as f:
        #     f.write("This is not a valid LAZ file.")
        # print(f"Created a placeholder file for testing structure: {dummy_laz_path_obj}")
        # print("WARNING: The placeholder LAZ is not valid. Processing will likely fail with PDAL errors.")
        # print("Replace with a real LAZ file for meaningful testing of the composite generation.")
    else:
        print(f"Using existing test LAZ file: {test_laz_file_path}")

        # Only proceed if the file seems somewhat plausible (e.g. ends in .laz or .las)
        if test_laz_file_path.lower().endswith((".laz", ".las")):
            try:
                print(f"Attempting composite generation for: {test_laz_file_path}")
                output_composite = generate_dtm_hillshade_blend(
                    laz_input_file=test_laz_file_path,
                    region_name_for_output=test_region_name,
                    dtm_resolution=1.0,
                    dtm_csf_cloth_resolution=1.0, # Explicitly set for testing
                    hillshade_azimuth=315,
                    hillshade_altitude=45,
                    hillshade_z_factor=1.0,
                    hillshade_suffix="test_hs",
                    blend_factor=0.5
                )
                print(f"Test composite generation function executed. Output (if successful): {output_composite}")
            except FileNotFoundError as fnf_error:
                print(f"Test execution FileNotFoundError: {fnf_error}. This might be due to an invalid test LAZ or issues in dependent DTM/Hillshade/ColorRelief steps.")
            except Exception as e:
                print(f"Test execution failed: {e}")
                print("This could be due to various reasons, including:")
                print("- Invalid or non-existent LAZ input file.")
                print("- Errors within the dtm, hillshade, or color_relief processing functions.")
                print("- PDAL or GDAL related issues if those tools are not configured or encounter errors.")
                import traceback
                traceback.print_exc()
        else:
            print("The specified test_laz_file_path does not appear to be a LAZ or LAS file. Skipping example run.")

    print("End of DTM-Hillshade Blend Generation Test.")
    pass
