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


async def process_aspect(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Aspect analysis from LAZ file with comprehensive logging
    
    Args:
        laz_file_path: Path to the input LAZ file
        output_dir: Directory to save output files
        parameters: Processing parameters
    
    Returns:
        Dict containing processing results
    """
    start_time = time.time()
    
    # Enhanced logging
    print(f"\n{'='*60}")
    print(f"🧭 ASPECT PROCESSING STARTING")
    print(f"\n{'='*60}")
    print(f"📁 Input LAZ file: {laz_file_path}")
    print(f"📂 Output directory: {output_dir}")
    print(f"⚙️ Parameters: {parameters}")
    print(f"🕐 Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    logger.info(f"Starting Aspect processing for {laz_file_path}")
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
        
        # Extract region name from the LAZ file path
        input_path = Path(laz_file_path)
        if "lidar" in input_path.parts:
            region_name = input_path.parts[input_path.parts.index("input") + 1]
        else:
            region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(laz_file_path))[0]
        
        print(f"🗺️ [REGION DETECTION] Extracted region name: {region_name}")
        
        # Generate output file path
        output_filename = f"{region_name}_aspect.tif"
        output_file_path = os.path.join(output_dir, output_filename)
        print(f"   📄 Output file will be: {output_file_path}")
        
        # Generate aspect using the synchronous function
        print(f"🔄 [ASPECT GENERATION] Calling aspect analysis...")
        aspect_start_time = time.time()
        
        try:
            # Run the aspect generation in a thread pool to keep it async
            loop = asyncio.get_event_loop()
            # Call the synchronous aspect function
            aspect_generated_path = await loop.run_in_executor(None, aspect, laz_file_path)
            
            aspect_processing_time = time.time() - aspect_start_time
            print(f"✅ [ASPECT GENERATED] Aspect analysis completed in {aspect_processing_time:.2f} seconds")
            print(f"   📄 Aspect output file from sync function: {aspect_generated_path}")

            # Verify the output file from sync function exists
            if not os.path.exists(aspect_generated_path):
                raise FileNotFoundError(f"Aspect output file from sync function not found: {aspect_generated_path}")

            # Copy to specified output directory if different
            # This is important because the sync function saves to its own default location
            final_output_path = output_file_path
            if aspect_generated_path != final_output_path:
                print(f"📋 [FILE COPY] Copying aspect to specified output directory...")
                print(f"   📁 From: {aspect_generated_path}")
                print(f"   📁 To: {final_output_path}")
                
                import shutil
                shutil.copy2(aspect_generated_path, final_output_path)
                
                if os.path.exists(final_output_path):
                    print(f"   ✅ Aspect copied successfully to {final_output_path}")
                else:
                    raise FileNotFoundError(f"Failed to copy aspect to {final_output_path}")
            else:
                print(f"   ℹ️ Aspect already in correct final location: {final_output_path}")
            
            # Get file size
            file_size = os.path.getsize(final_output_path)
            file_size_mb = file_size / (1024 * 1024)
            print(f"   📊 File size: {file_size_mb:.2f} MB")
            
            # Calculate total processing time
            total_time = time.time() - start_time
            
            # Log completion
            print(f"\n{'='*60}")
            print(f"✅ ASPECT PROCESSING COMPLETED")
            print(f"\n{'='*60}")
            print(f"⏱️ Total processing time: {total_time:.2f} seconds")
            print(f"📄 Final output: {final_output_path}")
            print(f"🕐 End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            logger.info(f"Aspect processing completed successfully in {total_time:.2f} seconds")
            logger.info(f"Output file: {final_output_path}")
            
            return {
                "success": True,
                "output_file": final_output_path,
                "processing_time": total_time,
                "aspect_time": aspect_processing_time,
                "region_name": region_name,
                "file_size_mb": file_size_mb,
                "message": f"Aspect processed successfully in {total_time:.2f} seconds"
            }
            
        except Exception as e:
            print(f"❌ [ASPECT ERROR] Aspect generation failed: {str(e)}")
            logger.error(f"Aspect generation failed: {str(e)}", exc_info=True)
            raise
            
    except Exception as e:
        total_time = time.time() - start_time
        error_msg = f"Aspect processing failed: {str(e)}"
        
        print(f"\n{'='*60}")
        print(f"❌ ASPECT PROCESSING FAILED")
        print(f"\n{'='*60}")
        print(f"⏱️ Time before failure: {total_time:.2f} seconds")
        print(f"❌ Error: {error_msg}")
        print(f"🕐 Failure time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.error(f"Aspect processing failed after {total_time:.2f} seconds: {str(e)}", exc_info=True)
        
        return {
            "success": False,
            "error": error_msg,
            "processing_time": total_time,
            "message": f"Aspect processing failed after {total_time:.2f} seconds"
        }


def aspect(input_file: str) -> str:
    """
    Generate aspect analysis from LAZ file (synchronous version)
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated aspect TIF file
    """
    print(f"\n🧭 Aspect (sync): Starting analysis for {input_file}")
    sync_start_time = time.time()
    
    # Extract region name from the file path structure
    input_path = Path(input_file)
    if "lidar" in input_path.parts:
        # e.g. input/<region_name>/lidar/<filename>
        region_name = input_path.parts[input_path.parts.index("input") + 1]
    else:
        # e.g. input/<region_name>/<filename> or input/<filename>
        region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(input_file))[0]
    
    # Create default output directory structure: output/<region_name>/Aspect/
    # This is where the synchronous function will save its output by default.
    default_output_dir = os.path.join("output", region_name, "Aspect")
    os.makedirs(default_output_dir, exist_ok=True)
    
    # Generate default output filename: <region_name>_aspect.tif
    default_output_filename = f"{region_name}_aspect.tif"
    default_output_path = os.path.join(default_output_dir, default_output_filename)
    
    print(f"📂 Default output directory (sync): {default_output_dir}")
    print(f"📄 Default output file (sync): {default_output_path}")
    
    try:
        # First, we need to generate or get the DTM
        print(f"🏔️ [DTM REQUIRED] Getting DTM for aspect calculation...")
        dtm_call_start_time = time.time()
        dtm_path = dtm(input_file) # Call the synchronous dtm function
        dtm_call_time = time.time() - dtm_call_start_time
        print(f"✅ DTM ready in {dtm_call_time:.2f} seconds: {dtm_path}")
        
        # Verify DTM file exists
        if not os.path.exists(dtm_path):
            raise FileNotFoundError(f"DTM file not found: {dtm_path}")
        
        # Generate aspect using GDAL DEM processing
        print(f"\n🔄 [GDAL ASPECT] Starting GDAL aspect calculation...")
        print(f"   📁 Input DTM: {dtm_path}")
        print(f"   📁 Output aspect: {default_output_path}")
        
        gdal_aspect_start_time = time.time()
        
        # Run gdaldem aspect
        # Ensure paths are strings for subprocess
        cmd = [
            'gdaldem', 'aspect',
            str(dtm_path),
            str(default_output_path),
            '-of', 'GTiff',
            '-compute_edges' # Computes aspect for pixels at the edge of the DEM
            # Add other parameters as needed, e.g. -alg ZevenbergenThorne
        ]
        
        print(f"   🖥️ Executing: {' '.join(cmd)}")
        
        # Using subprocess.run
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        gdal_aspect_time = time.time() - gdal_aspect_start_time
        
        if result.returncode == 0:
            print(f"✅ GDAL aspect completed successfully in {gdal_aspect_time:.2f} seconds")
            if result.stdout:
                print(f"   📋 GDAL output (stdout):\n{result.stdout.strip()}")
            if result.stderr: # GDAL often prints info to stderr
                print(f"   📋 GDAL output (stderr):\n{result.stderr.strip()}")
        else:
            error_msg = f"GDAL aspect failed with return code {result.returncode}"
            if result.stdout:
                error_msg += f"\nStdout: {result.stdout.strip()}"
            if result.stderr:
                error_msg += f"\nStderr: {result.stderr.strip()}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        # Verify output file was created
        if not os.path.exists(default_output_path):
            raise FileNotFoundError(f"Aspect output file was not created: {default_output_path}")
        
        # Get file information
        file_size = os.path.getsize(default_output_path)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n📊 [ASPECT INFO]")
        print(f"   📄 File: {default_output_path}")
        print(f"   📊 Size: {file_size_mb:.2f} MB")
        
        # Run gdalinfo to get detailed information
        print(f"\n📊 GDALINFO OUTPUT:")
        print(f"{'='*40}")
        try:
            gdalinfo_cmd = ['gdalinfo', str(default_output_path)]
            gdalinfo_result = subprocess.run(
                gdalinfo_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if gdalinfo_result.returncode == 0:
                print(gdalinfo_result.stdout)
            else:
                print(f"❌ gdalinfo failed with return code {gdalinfo_result.returncode}")
                if gdalinfo_result.stderr:
                    print(f"❌ Error: {gdalinfo_result.stderr.strip()}")
                    
        except FileNotFoundError:
            print(f"⚠️ gdalinfo command not found. Please ensure GDAL is installed and in PATH.")
        except subprocess.TimeoutExpired:
            print(f"⚠️ gdalinfo command timed out after 30 seconds.")
        except Exception as e_gdalinfo:
            print(f"⚠️ Error running gdalinfo: {str(e_gdalinfo)}")
        
        print(f"{'='*40}")
        
        # Calculate total processing time for the synchronous function
        total_sync_time = time.time() - sync_start_time
        
        print(f"✅ Aspect analysis (sync) completed successfully in {total_sync_time:.2f} seconds")
        print(f"   ⏱️ DTM call time: {dtm_call_time:.2f}s")
        print(f"   ⏱️ GDAL aspect calculation: {gdal_aspect_time:.2f}s")
        
        return str(default_output_path) # Return path to the generated file
        
    except subprocess.TimeoutExpired:
        total_sync_time = time.time() - sync_start_time
        error_msg = "Aspect calculation (sync) timed out after 5 minutes"
        print(f"❌ {error_msg} (total time: {total_sync_time:.2f}s)")
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)
        
    except Exception as e_sync:
        total_sync_time = time.time() - sync_start_time
        error_msg = f"Aspect calculation (sync) failed: {str(e_sync)}"
        print(f"❌ {error_msg} (total time: {total_sync_time:.2f}s)")
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)

