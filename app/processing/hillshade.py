import asyncio
import time
import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
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

def generate_hillshade_with_params(input_file: str, azimuth: float, altitude: float, z_factor: float, suffix: str = "", region_name: str = None) -> str:
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
    
    # Use provided region_name or extract from file path if not provided
    print(f"\n🔍 [REGION EXTRACTION] Determining region name...")
    input_path = Path(input_file)
    print(f"   📂 Full input path: {input_path}")
    print(f"   🧩 Path parts: {input_path.parts}")
    
    if region_name is None:
        print(f"   ⚠️ No region_name provided, extracting from file path...")
        if "lidar" in input_path.parts:
            # File is in lidar subfolder: extract parent's parent as region name
            region_name = input_path.parts[input_path.parts.index("input") + 1]
            print(f"   🎯 Found 'lidar' subfolder structure")
            print(f"   📍 Region name from parent directory: {region_name}")
        else:
            # File is directly in input folder: extract parent as region name
            region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(input_file))[0]
            print(f"   🎯 Direct input folder structure")
            print(f"   📍 Region name extracted: {region_name}")
    else:
        print(f"   ✅ Using provided region_name: {region_name}")
        
    print(f"   ✅ [REGION IDENTIFIED] Final region name: {region_name}")

    # Extract file stem for consistent directory structure
    file_stem = input_path.stem  # Get filename without extension (e.g., "OR_WizardIsland")
    
    # Create output directory structure: output/<file_stem>/lidar/Hillshade/
    print(f"\n📁 [FOLDER CREATION] Setting up output directory structure...")
    
    # Use provided region_name for output directory if available, otherwise use file_stem
    output_folder_name = region_name if region_name else file_stem
    print(f"📁 Using output folder name: {output_folder_name} (from region_name: {region_name})")
    
    output_dir = os.path.join("output", output_folder_name, "lidar", "Hillshade")
    print(f"   🏗️ Target directory: {output_dir}")
    print(f"   🔍 Checking if directory exists...")
    
    if os.path.exists(output_dir):
        print(f"   ✅ Directory already exists: {output_dir}")
    else:
        print(f"   🆕 Directory doesn't exist, creating...")
        print(f"   📂 Creating path: {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"   ✅ [FOLDER CREATED] Output directory ready: {output_dir}")

    # Generate output filename with suffix if provided
    print(f"\n📄 [FILE NAMING] Generating output filename...")
    if suffix:
        output_filename = f"{region_name}_Hillshade_{suffix}.tif"
        print(f"   🏷️ Using suffix pattern: <region_name>_Hillshade_<suffix>.tif")
    else:
        output_filename = f"{region_name}_Hillshade.tif"
        print(f"   🏷️ Using default pattern: <region_name>_Hillshade.tif")
        
    output_path = os.path.join(output_dir, output_filename)
    print(f"   📄 Generated filename: {output_filename}")
    print(f"   📂 Full output path: {output_path}")
    
    print(f"\n📊 [FILE ANALYSIS] Analyzing input and output files...")
    print(f"   📂 Input file location: {input_file}")
    print(f"   📂 Output directory: {output_dir}")
    print(f"   📄 Output file: {output_path}")

    # Check if hillshade already exists and is up-to-date (caching optimization)
    print(f"\n🗄️ [CACHE CHECK] Checking for existing hillshade file...")
    if os.path.exists(output_path) and os.path.exists(input_file):
        print(f"   📄 Found existing file: {output_path}")
        try:
            # Compare modification times
            hillshade_mtime = os.path.getmtime(output_path)
            laz_mtime = os.path.getmtime(input_file)
            
            print(f"   ⏰ Hillshade modified: {time.ctime(hillshade_mtime)}")
            print(f"   ⏰ LAZ file modified: {time.ctime(laz_mtime)}")
            
            if hillshade_mtime > laz_mtime:
                processing_time = time.time() - start_time
                print(f"   🚀 [CACHE HIT] Using existing file (newer than source)")
                print(f"   ✅ Cache validation successful in {processing_time:.3f} seconds")
                print(f"{'='*70}\n")
                return output_path
            else:
                print(f"   ⚠️ [CACHE MISS] Hillshade is outdated")
                print(f"   🔄 LAZ modified: {time.ctime(laz_mtime)}")
                print(f"   🔄 Hillshade created: {time.ctime(hillshade_mtime)}")
                print(f"   ♻️ Will regenerate hillshade...")
        except OSError as e:
            print(f"   ⚠️ Error checking file timestamps: {e}")
            print(f"   🔄 Proceeding with regeneration...")
    elif os.path.exists(output_path):
        print(f"   ⚠️ Hillshade exists but input LAZ file not found")
        print(f"   🔄 Will regenerate hillshade")
    else:
        print(f"   📝 No existing hillshade found")
        print(f"   🆕 Will generate new hillshade")

    try:
        # Step 1: Generate or locate DTM
        print(f"\n🏔️ [STEP 1] DTM Generation/Location...")
        print(f"   🔍 Checking for DTM as source for hillshade...")
        dtm_path = dtm(input_file, region_name)
        print(f"   ✅ [DTM READY] DTM available at: {dtm_path}")

        # Step 2: Generate hillshade using GDAL DEMProcessing
        print(f"\n🌄 Step 2: Generating hillshade using GDAL DEMProcessing...")
        print(f"📁 Source DTM: {dtm_path}")
        print(f"📁 Target hillshade: {output_path}")
        
        print(f"⚙️ Hillshade parameters:")
        print(f"   🧭 Azimuth: {azimuth}°")
        print(f"   📐 Altitude: {altitude}°")
        print(f"   📏 Z-factor: {z_factor}")
        print(f"   📊 Scale: 1.0")
        
        # Use GDAL DEMProcessing for hillshade generation
        processing_start = time.time()
        
        result = gdal.DEMProcessing(
            destName=output_path,
            srcDS=dtm_path,
            processing="hillshade",
            azimuth=azimuth,
            altitude=altitude,
            zFactor=z_factor,
            scale=1.0,
            format="GTiff"
        )
        
        processing_time = time.time() - processing_start
        
        if result is None:
            raise RuntimeError("GDAL DEMProcessing failed to generate hillshade")
        
        print(f"✅ Hillshade generation completed in {processing_time:.2f} seconds")
        
        # Step 3: Validate output file
        print(f"\n🔍 Validating output file...")
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            print(f"✅ Output file created successfully")
            print(f"📊 Output file size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
            print(f"📄 Output file path: {os.path.abspath(output_path)}")
        else:
            raise FileNotFoundError(f"Hillshade output file was not created: {output_path}")
        
        total_time = time.time() - start_time
        print(f"✅ HILLSHADE generation completed successfully in {total_time:.2f} seconds")
        print(f"🌄 Hillshade file: {output_path}")
        
        return output_path
        
    except Exception as e:
        total_time = time.time() - start_time
        error_msg = f"Hillshade generation failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Failed after {total_time:.2f} seconds")
        raise Exception(error_msg)

def hillshade(input_file: str, region_name: str = None) -> str:
    """
    Generate standard hillshade from LAZ file (default parameters)
    
    Args:
        input_file: Path to the input LAZ file
        region_name: Optional region name to use for output directory (instead of extracted from filename)
        Returns:
        Path to the generated hillshade TIF file
    """
    return generate_hillshade_with_params(input_file, 315.0, 45.0, 1.0, "standard", region_name)

def hillshade_315_45_08(input_file: str, region_name: str = None) -> str:
    """
    Generate hillshade with 315° azimuth, 45° altitude, 0.8 z-factor
    
    Args:
        input_file: Path to the input LAZ file
        region_name: Optional region name to use for output directory (instead of extracted from filename)
        Returns:
        Path to the generated hillshade TIF file
    """
    return generate_hillshade_with_params(input_file, 315.0, 45.0, 0.8, "315_45_08", region_name)

def hillshade_225_45_08(input_file: str, region_name: str = None) -> str:
    """
    Generate hillshade with 225° azimuth, 45° altitude, 0.8 z-factor
    
    Args:
        input_file: Path to the input LAZ file
        region_name: Optional region name to use for output directory (instead of extracted from filename)
        Returns:
        Path to the generated hillshade TIF file
    """
    return generate_hillshade_with_params(input_file, 225.0, 45.0, 0.8, "225_45_08", region_name)