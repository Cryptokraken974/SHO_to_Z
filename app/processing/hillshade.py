import asyncio
import time
import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional # Added Optional
from osgeo import gdal
from .dtm import dtm

logger = logging.getLogger(__name__)

async def process_hillshade(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process hillshade from LAZ file with comprehensive logging.
    
    Args:
        laz_file_path: Path to the input LAZ file
        output_dir: Directory to save output files
        parameters: Processing parameters
    
    Returns:
        Dict containing processing results
    """
    start_time = time.time()
    
    print(f"{'='*60}")
    print(f"🏔️ HILLSHADE PROCESSING STARTING")
    print(f"{'='*60}")
    print(f"📂 Input file: {laz_file_path}")
    print(f"📁 Output directory: {output_dir}")
    print(f"⚙️ Parameters: {parameters}")
    
    logger.info(f"Starting Hillshade processing for {laz_file_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Parameters: {parameters}")
    
    try:
        # Create output directory if it doesn't exist
        print(f"📁 [FOLDER CREATION] Creating output directory if needed...")
        print(f"   🔍 Checking if directory exists: {output_dir}")
        
        if os.path.exists(output_dir):
            print(f"   ✅ Directory already exists: {output_dir}")
        else:
            print(f"   🆕 Directory doesn't exist, creating: {output_dir}")
            
        os.makedirs(output_dir, exist_ok=True)
        print(f"   ✅ [FOLDER CREATED] Output directory ready: {output_dir}")
        logger.info(f"Output directory created/verified: {output_dir}")
        
        # Extract region name from file path for consistent naming
        print(f"🔍 [REGION EXTRACTION] Extracting region name from file path...")
        input_path = Path(laz_file_path)
        print(f"   📂 Full input path: {input_path}")
        print(f"   🧩 Path parts: {input_path.parts}")
        
        if "lidar" in input_path.parts:
            region_name = input_path.parts[input_path.parts.index("input") + 1]
            print(f"   🎯 Found 'lidar' in path, extracted region: {region_name}")
        else:
            region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(laz_file_path))[0]
            print(f"   🎯 No 'lidar' in path, extracted region: {region_name}")
            
        print(f"   ✅ [REGION IDENTIFIED] Using region name: {region_name}")
        
        # Generate output filename using new naming convention
        output_filename = f"{region_name}_Hillshade.tif"
        output_file = os.path.join(output_dir, output_filename)
        print(f"📄 [FILE CREATION] Creating output file: {output_file}")
        print(f"   📝 Filename pattern: <region_name>_Hillshade.tif")
        print(f"   🏷️ Generated filename: {output_filename}")

        # Check if input file exists
        print(f"🔍 [FILE VALIDATION] Validating input file...")
        if not os.path.exists(laz_file_path):
            error_msg = f"LAZ file not found: {laz_file_path}"
            print(f"❌ [VALIDATION ERROR] {error_msg}")
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        file_size = os.path.getsize(laz_file_path)
        print(f"✅ [FILE VALIDATED] Input file exists: {laz_file_path}")
        print(f"📊 [FILE INFO] File size: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")
        logger.info(f"Input file validated - Size: {file_size} bytes")
        
        # Get parameters with defaults
        azimuth = parameters.get("azimuth", 315)
        altitude = parameters.get("altitude", 45)
        
        print(f"⚙️ [PROCESSING CONFIG] Hillshade parameters:")
        print(f"   🧭 Azimuth: {azimuth}°")
        print(f"   📐 Altitude: {altitude}°")
        
        logger.info(f"Processing with azimuth={azimuth}, altitude={altitude}")
        
        print(f"🔄 [PROCESSING] Processing Hillshade (simulated)...")
        print(f"   🌄 Calculating terrain relief...")
        print(f"   ☀️ Applying lighting model...")
        print(f"   🎨 Generating shaded relief...")
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Simulate creating output file
        print(f"💾 [FILE WRITING] Creating output file...")
        print(f"   📂 Writing to: {output_file}")
        
        with open(output_file, 'w') as f:
            f.write("Hillshade placeholder file")
        
        output_size = os.path.getsize(output_file)
        print(f"✅ [FILE CREATED] Output file created successfully")
        print(f"   📂 File location: {output_file}")
        print(f"   📊 File size: {output_size} bytes")
        
        processing_time = time.time() - start_time
        
        print(f"⏱️ [TIMING] Processing completed in {processing_time:.2f} seconds")
        print(f"✅ [SUCCESS] HILLSHADE PROCESSING SUCCESSFUL")
        print(f"{'='*60}\n")
        
        logger.info(f"Hillshade processing completed in {processing_time:.2f} seconds")
        logger.info(f"Output file created: {output_file}")
        
        return {
            "success": True,
            "message": "Hillshade processing completed successfully",
            "output_file": output_file,
            "processing_time": processing_time,
            "input_file": laz_file_path,
            "parameters_used": {
                "azimuth": azimuth,
                "altitude": altitude
            },
            "file_info": {
                "input_size_bytes": file_size,
                "output_size_bytes": output_size
            }
        }
        
    except FileNotFoundError as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        
        print(f"❌ FILE NOT FOUND ERROR after {processing_time:.2f}s")
        print(f"❌ Error: {error_msg}")
        print(f"{'='*60}\n")
        
        logger.error(f"File not found error in Hillshade processing: {error_msg}")
        
        return {
            "success": False,
            "message": error_msg,
            "error_type": "FileNotFoundError",
            "processing_time": processing_time,
            "input_file": laz_file_path
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        
        print(f"❌ UNEXPECTED ERROR after {processing_time:.2f}s")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Error message: {error_msg}")
        print(f"{'='*60}\n")
        
        logger.error(f"Unexpected error in Hillshade processing: {error_msg}", exc_info=True)
        
        return {
            "success": False,
            "message": f"Processing failed: {error_msg}",
            "error_type": type(e).__name__,
            "processing_time": processing_time,
            "input_file": laz_file_path
        }

def generate_hillshade_with_params(
    input_file: str,
    azimuth: float,
    altitude: float,
    z_factor: float,
    suffix: str = "",
    region_name: str = None,
    dtm_resolution: float = 1.0,
    dtm_csf_cloth_resolution: Optional[float] = None
) -> str:
    """
    Generate hillshade with comprehensive logging of all file/folder operations.
    """
    start_time = time.time()
    
    print(f"\n{'='*70}")
    print(f"🏔️ HILLSHADE GENERATION WITH PARAMETERS")
    print(f"{'='*70}")
    print(f"📂 Input file: {input_file}")
    print(f"⚙️ Parameters: azimuth={azimuth}°, altitude={altitude}°, z_factor={z_factor}")
    print(f"🏷️ Suffix: '{suffix}' (empty = default naming)")
    print(f"⚙️ DTM Params: Resolution={dtm_resolution}m, CSF Cloth Resolution={dtm_csf_cloth_resolution if dtm_csf_cloth_resolution is not None else dtm_resolution}m")
    logger.info(f"Generate hillshade for {input_file}. DTM Res: {dtm_resolution}m, CSF Res: {dtm_csf_cloth_resolution}. Hillshade: az={azimuth},alt={altitude},z={z_factor},suffix='{suffix}'")

    # Use provided region_name or extract from file path if not provided
    print(f"\n🔍 [REGION EXTRACTION] Determining region name...")
    input_path = Path(input_file)
    print(f"   📂 Full input path: {input_path}")
    print(f"   🧩 Path parts: {input_path.parts}")
    
    # 🎯 PRIORITY FIX: Use provided region_name (display_region_name) to ensure user-friendly folder names
    # This prevents coordinate-based folder creation like "2.433S_57.248W_elevation_DTM"
    effective_region_name = region_name
    if effective_region_name is not None and effective_region_name.strip():
        print(f"   ✅ [PRIORITY] Using provided region_name (user-friendly): {effective_region_name}")
        print(f"   🎯 This ensures output goes to: output/{effective_region_name}/... instead of coordinate-based paths")
    else:
        print(f"   ⚠️ No explicit region_name provided, extracting from file path...")
        if "lidar" in input_path.parts and "input" in input_path.parts:
            try:
                effective_region_name = input_path.parts[input_path.parts.index("input") + 1]
                print(f"   🎯 Found 'input/.../region_name/.../lidar' structure. Region: {effective_region_name}")
            except (ValueError, IndexError):
                effective_region_name = input_path.stem # Fallback to stem if path is unusual
                print(f"   ⚠️ Path structure unexpected, falling back to input file stem for region: {effective_region_name}")
        else:
            effective_region_name = input_path.stem # Fallback if not standard project structure
            print(f"   🎯 Non-standard path structure, using input file stem for region: {effective_region_name}")
        
    print(f"   ✅ [REGION IDENTIFIED] Final effective region name for path construction: {effective_region_name}")

    # 🔍 QUALITY MODE INTEGRATION: Check for clean LAZ file
    actual_input_file = input_file
    quality_mode_used = False
    
    print(f"\n🔍 [QUALITY MODE CHECK] Checking for clean LAZ file...")
    # Look for clean LAZ file in output/{region}/cropped/{region}_cropped.las
    potential_clean_laz_patterns = [
        os.path.join("output", effective_region_name, "cropped", f"{effective_region_name}_cropped.las"),
        os.path.join("output", effective_region_name, "cropped", f"{input_path.stem}_cropped.las"),
        os.path.join("output", effective_region_name, "lidar", "cropped", f"{effective_region_name}_cropped.las"),
        os.path.join("output", effective_region_name, "lidar", "cropped", f"{input_path.stem}_cropped.las")
    ]
    
    for clean_laz_path in potential_clean_laz_patterns:
        if os.path.exists(clean_laz_path):
            print(f"   🎯 QUALITY MODE: Found clean LAZ file: {clean_laz_path}")
            logger.info(f"Quality mode activated: Using clean LAZ file {clean_laz_path} instead of {input_file}")
            actual_input_file = clean_laz_path
            quality_mode_used = True
            break
    
    if not quality_mode_used:
        print(f"   📋 STANDARD MODE: Using original LAZ file (no clean LAZ found)")
        logger.info(f"Standard mode: No clean LAZ file found, using original {input_file}")

    # Create output directory structure using the effective_region_name
    print(f"\n📁 [FOLDER CREATION] Setting up output directory structure...")
    output_dir = os.path.join("output", effective_region_name, "lidar", "Hillshade")
    print(f"   🏗️ Target directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    print(f"   ✅ [FOLDER CREATED/VERIFIED] Output directory ready: {output_dir}")

    # Generate output filename
    # Filename should incorporate DTM resolution for clarity and cache differentiation
    print(f"\n📄 [FILE NAMING] Generating output filename...")
    laz_file_stem = Path(input_file).stem
    actual_csf_res = dtm_csf_cloth_resolution if dtm_csf_cloth_resolution is not None else dtm_resolution

    base_name_for_hillshade = f"{laz_file_stem}_dtm{dtm_resolution}m_csf{actual_csf_res}m_Hillshade"
    if quality_mode_used:
        base_name_for_hillshade += "_clean"
    output_filename = f"{base_name_for_hillshade}_{suffix}.tif" if suffix else f"{base_name_for_hillshade}.tif"

    output_path = os.path.join(output_dir, output_filename)
    print(f"   📄 Generated filename: {output_filename}")
    print(f"   📂 Full output path: {output_path}")
    print(f"   📄 Actual input file: {actual_input_file}")
    if quality_mode_used:
        print(f"   ✨ Quality mode: Clean Hillshade will be generated from clean DTM")
    
    # DTM Generation Call (use actual input file for quality mode)
    # The dtm() function is called with region_name=effective_region_name to ensure its outputs also follow this.
    print(f"\n🏔️ [STEP 1] DTM Generation/Location using DTM Resolution: {dtm_resolution}m, CSF Cloth Res: {dtm_csf_cloth_resolution if dtm_csf_cloth_resolution is not None else dtm_resolution}m...")
    dtm_path = dtm(
        actual_input_file,  # Use actual input file (clean LAZ if available)
        region_name=effective_region_name, # Pass the determined region name
        resolution=dtm_resolution,
        csf_cloth_resolution=dtm_csf_cloth_resolution
    )
    if not dtm_path or "failed" in dtm_path.lower() or not os.path.exists(dtm_path): # dtm() returns path or error string
        logger.error(f"DTM generation failed. Returned path: {dtm_path}")
        raise FileNotFoundError(f"DTM generation failed or DTM file not found: {dtm_path}")
    print(f"   ✅ [DTM READY] DTM available at: {dtm_path}")
    logger.info(f"DTM for hillshade generated at: {dtm_path}")

    # Caching Check (after DTM generation, as DTM itself is cached)
    print(f"\n🗄️ [CACHE CHECK] Checking for existing hillshade file {output_path}...")
    if os.path.exists(output_path) and os.path.exists(dtm_path): # dtm_path must exist here
        print(f"   📄 Found existing hillshade file: {output_path}")
        try:
            hillshade_mtime = os.path.getmtime(output_path)
            dtm_file_mtime = os.path.getmtime(dtm_path) # Compare against the DTM file used
            
            print(f"   ⏰ Hillshade modified: {time.ctime(hillshade_mtime)}")
            print(f"   ⏰ DTM file modified: {time.ctime(dtm_file_mtime)}")
            
            if hillshade_mtime > dtm_file_mtime:
                processing_time_cache = time.time() - start_time
                print(f"   🚀 [CACHE HIT] Using existing hillshade file (newer than source DTM).")
                print(f"   ✅ Hillshade ready in {processing_time_cache:.3f} seconds (cached).")
                print(f"{'='*70}\n")
                logger.info(f"Cache hit for hillshade: {output_path}")
                return output_path
            else:
                print(f"   ⚠️ [CACHE MISS] Hillshade is outdated or DTM is newer. Will regenerate hillshade.")
                logger.info(f"Cache miss for hillshade {output_path}, DTM is newer or hillshade outdated.")
        except OSError as e:
            print(f"   ⚠️ Error checking file timestamps: {e}. Proceeding with regeneration.")
            logger.warning(f"Error checking timestamps for hillshade {output_path}: {e}. Regenerating.")
    else:
        if os.path.exists(output_path): # Exists, but DTM path might have had an issue (though checked above)
             print(f"   ⚠️ Hillshade exists but DTM path invalid or DTM missing. Will attempt regeneration.")
             logger.warning(f"Hillshade {output_path} exists but DTM path {dtm_path} was problematic. Regenerating.")
        else:
            print(f"   📝 No existing hillshade found. Will generate new hillshade at {output_path}.")
            logger.info(f"No existing hillshade {output_path}. Generating.")

    try:
        # Step 2: Generate hillshade using GDAL DEMProcessing
        print(f"\n🌄 [STEP 2] Generating hillshade using GDAL DEMProcessing...")
        print(f"   📁 Source DTM: {dtm_path}")
        print(f"   📁 Target hillshade: {output_path}")
        
        print(f"   ⚙️ Hillshade parameters: Azimuth={azimuth}°, Altitude={altitude}°, Z-factor={z_factor}, Scale=1.0")
        
        gdal_processing_start_time = time.time()
        gdal_options = gdal.DEMProcessingOptions(
            azimuth=azimuth,
            altitude=altitude,
            zFactor=z_factor,
            scale=1.0, # Default scale, can be parameterized if needed
            computeEdges=True,
            format="GTiff",
            creationOptions=['COMPRESS=LZW', 'TILED=YES', 'PREDICTOR=2', 'BIGTIFF=IF_SAFER']
        )

        result_ds = gdal.DEMProcessing(
            destName=output_path,
            srcDS=dtm_path, # Can be path or GDAL Dataset object
            processing="hillshade",
            options=gdal_options
        )
        
        gdal_processing_time = time.time() - gdal_processing_start_time
        
        if result_ds is None: # DEMProcessing returns None on failure with older GDAL, or raises exception with newer.
            logger.error(f"GDAL DEMProcessing failed to generate hillshade for {dtm_path}. Result was None.")
            raise RuntimeError(f"GDAL DEMProcessing failed to generate hillshade for {dtm_path}. Output may not be valid.")
        
        result_ds = None # Close the dataset
        print(f"   ✅ GDAL DEMProcessing completed in {gdal_processing_time:.2f} seconds.")
        
        # Step 3: Validate output file
        print(f"\n🔍 [STEP 3] Validating output file {output_path}...")
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0: # Basic check
            output_size = os.path.getsize(output_path)
            output_size_mb = output_size / (1024**2)
            print(f"   ✅ Output file created successfully.")
            print(f"   📊 Output file size: {output_size:,} bytes ({output_size_mb:.2f} MB).")
            print(f"   📄 Output file path: {os.path.abspath(output_path)}")
            logger.info(f"Hillshade successfully generated: {output_path}, Size: {output_size_mb:.2f} MB")
        else:
            logger.error(f"Hillshade output file {output_path} was not created or is empty.")
            raise FileNotFoundError(f"Hillshade output file was not created or is empty: {output_path}")
        
        total_processing_time = time.time() - start_time
        print(f"\n✅ TOTAL HILLSHADE generation completed successfully in {total_processing_time:.2f} seconds.")
        print(f"🌄 Hillshade file: {output_path}")
        
        # 🎯 QUALITY MODE PNG GENERATION: Generate PNG for clean Hillshade if quality mode was used
        if quality_mode_used:
            print(f"\n🖼️ QUALITY MODE: Generating PNG for clean Hillshade")
            try:
                from ..convert import convert_geotiff_to_png
                
                # Create png_outputs directory structure
                tif_dir = os.path.dirname(output_path)
                base_output_dir = os.path.dirname(tif_dir)  # Go up from Hillshade/ to lidar/
                png_output_dir = os.path.join(base_output_dir, "png_outputs")
                os.makedirs(png_output_dir, exist_ok=True)
                
                # Generate PNG with standard filename
                png_path = os.path.join(png_output_dir, "Hillshade.png")
                convert_geotiff_to_png(
                    output_path, 
                    png_path, 
                    enhanced_resolution=True,
                    save_to_consolidated=False,  # Already in the right directory
                    stretch_type="stddev",
                    stretch_params={"percentile_low": 2, "percentile_high": 98}
                )
                print(f"✅ Quality mode Hillshade PNG file created: {png_path}")
                logger.info(f"Quality mode Hillshade PNG generated: {png_path}")
            except Exception as png_error:
                print(f"⚠️ Quality mode Hillshade PNG generation failed: {png_error}")
                logger.warning(f"Quality mode Hillshade PNG generation failed: {png_error}")
        
        print(f"{'='*70}\n")
        
        return output_path
        
    except Exception as e:
        total_processing_time = time.time() - start_time
        error_msg = f"Hillshade generation for {input_file} failed after {total_processing_time:.2f} seconds: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        print(f"{'='*70}\n")
        raise Exception(error_msg) # Re-raise to be caught by calling functions / API endpoints

def hillshade(
    input_file: str,
    region_name: str = None,
    dtm_resolution: float = 1.0,
    dtm_csf_cloth_resolution: Optional[float] = None
) -> str:
    """
    Generate standard hillshade from LAZ file (default parameters: Az315, Alt45, Z1).
    """
    logger.info(f"Standard hillshade called for {input_file}, DTM Res: {dtm_resolution}m, CSF Res: {dtm_csf_cloth_resolution}")
    return generate_hillshade_with_params(
        input_file,
        315.0,
        45.0,
        1.0,
        "standard_az315_alt45_z1",
        region_name,
        dtm_resolution=dtm_resolution,
        dtm_csf_cloth_resolution=dtm_csf_cloth_resolution
    )

def hillshade_315_45_08(
    input_file: str,
    region_name: str = None,
    dtm_resolution: float = 1.0,
    dtm_csf_cloth_resolution: Optional[float] = None
) -> str:
    """
    Generate hillshade with 315° azimuth, 45° altitude, 0.8 z-factor.
    """
    logger.info(f"Hillshade Az315 Alt45 Z0.8 called for {input_file}, DTM Res: {dtm_resolution}m, CSF Res: {dtm_csf_cloth_resolution}")
    return generate_hillshade_with_params(
        input_file,
        315.0,
        45.0,
        0.8,
        "az315_alt45_z0p8",
        region_name,
        dtm_resolution=dtm_resolution,
        dtm_csf_cloth_resolution=dtm_csf_cloth_resolution
    )

def hillshade_225_45_08(
    input_file: str,
    region_name: str = None,
    dtm_resolution: float = 1.0,
    dtm_csf_cloth_resolution: Optional[float] = None
) -> str:
    """
    Generate hillshade with 225° azimuth, 45° altitude, 0.8 z-factor.
    """
    logger.info(f"Hillshade Az225 Alt45 Z0.8 called for {input_file}, DTM Res: {dtm_resolution}m, CSF Res: {dtm_csf_cloth_resolution}")
    return generate_hillshade_with_params(
        input_file,
        225.0,
        45.0,
        0.8,
        "225_45_08",
        region_name,
        dtm_resolution=dtm_resolution,
        dtm_csf_cloth_resolution=dtm_csf_cloth_resolution
    )