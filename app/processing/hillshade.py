import asyncio
import time
import os
import logging
import subprocess
from typing import Dict, Any
from osgeo import gdal
from .dtm import dtm

logger = logging.getLogger(__name__)

async def process_hillshade(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Hillshade from LAZ file
    
    Args:
        laz_file_path: Path to the input LAZ file
        output_dir: Directory to save output files
        parameters: Processing parameters
    
    Returns:
        Dict containing processing results
    """
    start_time = time.time()
    
    # Enhanced logging
    print(f"\n{'='*50}")
    print(f"🚀 STARTING HILLSHADE PROCESSING")
    print(f"{'='*50}")
    print(f"📁 Input LAZ file: {laz_file_path}")
    print(f"📂 Output directory: {output_dir}")
    print(f"⚙️ Parameters: {parameters}")
    print(f"🕐 Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    logger.info(f"Starting Hillshade processing for {laz_file_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Parameters: {parameters}")
    
    try:
        # Create output directory if it doesn't exist
        print(f"📁 Creating output directory if needed...")
        os.makedirs(output_dir, exist_ok=True)
        print(f"✅ Output directory ready: {output_dir}")
        logger.info(f"Output directory created/verified: {output_dir}")
        
        # Check if input file exists
        print(f"🔍 Validating input file...")
        if not os.path.exists(laz_file_path):
            error_msg = f"LAZ file not found: {laz_file_path}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        file_size = os.path.getsize(laz_file_path)
        print(f"✅ Input file validated: {laz_file_path}")
        print(f"📊 File size: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")
        logger.info(f"Input file validated - Size: {file_size} bytes")
        
        # Get parameters with defaults
        azimuth = parameters.get("azimuth", 315)
        altitude = parameters.get("altitude", 45)
        
        print(f"⚙️ Hillshade parameters:")
        print(f"   🧭 Azimuth: {azimuth}°")
        print(f"   📐 Altitude: {altitude}°")
        
        logger.info(f"Processing with azimuth={azimuth}, altitude={altitude}")
        
        print(f"🔄 Processing Hillshade (simulated)...")
        print(f"   🌄 Calculating terrain relief...")
        print(f"   ☀️ Applying lighting model...")
        print(f"   🎨 Generating shaded relief...")
        
        # Simulate processing time
        await asyncio.sleep(2.5)
        print(f"⏳ Hillshade processing simulation completed")
        
        # TODO: Implement actual hillshade processing
        # This would typically involve:
        # 1. Reading LAZ file and creating DEM
        # 2. Calculating slope and aspect
        # 3. Applying hillshade algorithm with lighting parameters
        # 4. Saving as GeoTIFF
        
        # Generate output filename using new naming convention: <laz_filename_without_ext>_<processing_step>
        laz_basename = os.path.splitext(os.path.basename(laz_file_path))[0]
        output_filename = f"{laz_basename}_Hillshade.tif"
        output_file = os.path.join(output_dir, output_filename)
        print(f"📄 Creating output file: {output_file}")
        
        # Simulate creating output file
        with open(output_file, 'w') as f:
            f.write("Hillshade placeholder file")
        
        output_size = os.path.getsize(output_file)
        print(f"✅ Output file created successfully")
        print(f"📊 Output file size: {output_size} bytes")
        
        processing_time = time.time() - start_time
        
        print(f"⏱️ Processing completed in {processing_time:.2f} seconds")
        print(f"✅ HILLSHADE PROCESSING SUCCESSFUL")
        print(f"{'='*50}\n")
        
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
        print(f"{'='*50}\n")
        
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
        print(f"{'='*50}\n")
        
        logger.error(f"Unexpected error in Hillshade processing: {error_msg}", exc_info=True)
        
        return {
            "success": False,
            "message": f"Processing failed: {error_msg}",
            "error_type": type(e).__name__,
            "processing_time": processing_time,
            "input_file": laz_file_path
        }

def generate_hillshade_with_params(input_file: str, azimuth: float, altitude: float, z_factor: float, suffix: str = "") -> str:
    """
    Generate hillshade from LAZ file with specific parameters
    
    Args:
        input_file: Path to the input LAZ file
        azimuth: Light source azimuth in degrees
        altitude: Light source altitude in degrees  
        z_factor: Vertical exaggeration factor
        suffix: Optional suffix for the output filename
        
    Returns:
        Path to the generated hillshade TIF file
    """
    print(f"\n🌄 HILLSHADE: Starting generation for {input_file}")
    print(f"⚙️ Parameters: Azimuth={azimuth}°, Altitude={altitude}°, Z-factor={z_factor}")
    start_time = time.time()
    
    # Extract the base name without path and extension
    laz_basename = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory structure: output/<laz_basename>/Hillshade/
    output_dir = os.path.join("output", laz_basename, "Hillshade")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename with suffix if provided
    if suffix:
        output_filename = f"{laz_basename}_hillshade_{suffix}.tif"
    else:
        output_filename = f"{laz_basename}_hillshade.tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path}")
    
    # Check if hillshade already exists and is up-to-date (caching optimization)
    if os.path.exists(output_path) and os.path.exists(input_file):
        try:
            # Compare modification times
            hillshade_mtime = os.path.getmtime(output_path)
            laz_mtime = os.path.getmtime(input_file)
            
            if hillshade_mtime > laz_mtime:
                processing_time = time.time() - start_time
                print(f"🚀 Hillshade cache hit! Using existing file (created {time.ctime(hillshade_mtime)})")
                print(f"✅ Hillshade ready in {processing_time:.3f} seconds (cached)")
                return output_path
            else:
                print(f"⏰ Hillshade exists but is outdated. LAZ modified: {time.ctime(laz_mtime)}, Hillshade created: {time.ctime(hillshade_mtime)}")
        except OSError as e:
            print(f"⚠️ Error checking file timestamps: {e}")
    elif os.path.exists(output_path):
        print(f"⚠️ Hillshade exists but input LAZ file not found, regenerating hillshade")
    else:
        print(f"📝 No existing hillshade found, generating new hillshade")
    
    try:
        # Step 1: Generate or locate DTM
        print(f"\n🏔️ Step 1: Generating DTM as source for hillshade...")
        dtm_path = dtm(input_file)
        print(f"✅ DTM ready: {dtm_path}")
        
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

def hillshade(input_file: str) -> str:
    """
    Generate standard hillshade from LAZ file (default parameters)
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated hillshade TIF file
    """
    return generate_hillshade_with_params(input_file, 315.0, 45.0, 1.0, "standard")

def hillshade_315_45_08(input_file: str) -> str:
    """
    Generate hillshade with 315° azimuth, 45° altitude, 0.8 z-factor
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated hillshade TIF file
    """
    return generate_hillshade_with_params(input_file, 315.0, 45.0, 0.8, "315_45_08")

def hillshade_225_45_08(input_file: str) -> str:
    """
    Generate hillshade with 225° azimuth, 45° altitude, 0.8 z-factor
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated hillshade TIF file
    """
    return generate_hillshade_with_params(input_file, 225.0, 45.0, 0.8, "225_45_08")