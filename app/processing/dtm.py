import asyncio
import time
import os
import logging
import subprocess
from typing import Dict, Any
import pdal

from .pipelines import create_laz_to_dtm_pipeline, get_pipeline_json, print_pipeline_info

logger = logging.getLogger(__name__)

async def process_dtm(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process DTM (Digital Terrain Model) from LAZ file
    
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
    print(f"🚀 STARTING DTM PROCESSING")
    print(f"{'='*50}")
    print(f"📁 Input LAZ file: {laz_file_path}")
    print(f"📂 Output directory: {output_dir}")
    print(f"⚙️ Parameters: {parameters}")
    print(f"🕐 Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    logger.info(f"Starting DTM processing for {laz_file_path}")
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
        
        print(f"🔄 Processing DTM (simulated)...")
        print(f"   🌍 Filtering ground points...")
        print(f"   📐 Creating terrain model...")
        print(f"   🗺️ Generating raster...")
        
        # Simulate processing time
        await asyncio.sleep(2)
        print(f"⏳ DTM processing simulation completed")
        
        # TODO: Implement actual DTM processing
        # This would typically involve:
        # 1. Reading LAZ file with laspy
        # 2. Filtering points to ground returns only
        # 3. Creating a DEM using interpolation
        # 4. Saving as GeoTIFF
        
        # Generate output filename using new naming convention: <laz_filename_without_ext>_<processing_step>
        laz_basename = os.path.splitext(os.path.basename(laz_file_path))[0]
        output_filename = f"{laz_basename}_DTM.tif"
        output_file = os.path.join(output_dir, output_filename)
        print(f"📄 Creating output file: {output_file}")
        
        # Simulate creating output file
        with open(output_file, 'w') as f:
            f.write("DTM placeholder file")
        
        output_size = os.path.getsize(output_file)
        print(f"✅ Output file created successfully")
        print(f"📊 Output file size: {output_size} bytes")
        
        processing_time = time.time() - start_time
        
        print(f"⏱️ Processing completed in {processing_time:.2f} seconds")
        print(f"✅ DTM PROCESSING SUCCESSFUL")
        print(f"{'='*50}\n")
        
        logger.info(f"DTM processing completed in {processing_time:.2f} seconds")
        logger.info(f"Output file created: {output_file}")
        
        return {
            "success": True,
            "message": "DTM processing completed successfully",
            "output_file": output_file,
            "processing_time": processing_time,
            "input_file": laz_file_path,
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
        
        logger.error(f"File not found error in DTM processing: {error_msg}")
        
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
        
        logger.error(f"Unexpected error in DTM processing: {error_msg}", exc_info=True)
        
        return {
            "success": False,
            "message": f"Processing failed: {error_msg}",
            "error_type": type(e).__name__,
            "processing_time": processing_time,
            "input_file": laz_file_path
        }
        
        return {
            "success": True,
            "message": "DTM processing completed successfully",
            "output_file": output_file,
            "processing_time": processing_time,
            "metadata": {
                "input_file": laz_file_path,
                "processing_type": "DTM",
                "resolution": parameters.get("resolution", "1.0m"),
                "interpolation_method": parameters.get("interpolation", "IDW")
            }
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"DTM processing failed: {str(e)}")
        
        return {
            "success": False,
            "message": f"DTM processing failed: {str(e)}",
            "processing_time": processing_time,
            "metadata": {
                "input_file": laz_file_path,
                "processing_type": "DTM",
                "error": str(e)
            }
        }

def dtm(input_file: str) -> str:
    """
    Convert LAZ file to DTM (Digital Terrain Model) - Ground points only
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated TIF file
    """
    print(f"\n🏔️ DTM: Starting conversion for {input_file}")
    start_time = time.time()
    
    # Extract the base name without path and extension
    laz_basename = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory structure: output/<laz_basename>/DTM/
    output_dir = os.path.join("output", laz_basename, "DTM")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <laz_basename>_DTM.tif
    output_filename = f"{laz_basename}_DTM.tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path}")
    
    # Set default resolution
    resolution = 1.0
    
    # Call the conversion function with detailed logging
    success, message = convert_las_to_dtm(input_file, output_path, resolution)
    
    processing_time = time.time() - start_time
    
    if success:
        print(f"✅ DTM conversion completed successfully in {processing_time:.2f} seconds")
        print(f"📊 Message: {message}")
        return output_path
    else:
        print(f"❌ DTM conversion failed after {processing_time:.2f} seconds")
        print(f"❌ Error: {message}")
        raise Exception(f"DTM conversion failed: {message}")

def convert_las_to_dtm(input_file: str, output_file: str, resolution: float = 1.0) -> tuple[bool, str]:
    """
    Convert LAZ file to DTM using PDAL with ground point filtering
    
    Args:
        input_file: Path to the input LAZ file
        output_file: Path to the output TIF file
        resolution: Grid resolution for DTM generation
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    print(f"\n{'='*60}")
    print(f"🎯 PDAL LAZ TO DTM CONVERSION")
    print(f"{'='*60}")
    print(f"📁 Input LAZ file: {input_file}")
    print(f"📁 Output TIF file: {output_file}")
    print(f"📏 Resolution: {resolution} units")
    print(f"🕐 Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Validate input file
    print(f"\n🔍 Validating input file...")
    if not os.path.exists(input_file):
        error_msg = f"Input file not found: {input_file}"
        print(f"❌ {error_msg}")
        return False, error_msg
    
    file_size = os.path.getsize(input_file)
    print(f"✅ Input file validated")
    print(f"📊 File size: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")
    
    # Create PDAL pipeline for DTM (ground points only)
    print(f"\n🔧 Creating PDAL DTM pipeline...")
    pipeline = create_laz_to_dtm_pipeline(
        input_file=input_file,
        output_file=output_file,
        resolution=resolution,
        nodata=-9999,
        ground_only=True
    )
    
    print(f"🗂️ DTM Pipeline Parameters:")
    print(f"   📄 Output file: {output_file}")
    print(f"   📏 Resolution: {resolution} units")
    print(f"   📊 Output type: min (ground surface)")
    print(f"   🚫 NoData value: -9999")
    print(f"   🌍 Ground points only: Classification 2")
    print(f"   💾 GDAL driver: GTiff")
    
    print_pipeline_info(pipeline, "LAZ to DTM Pipeline")
    
    # Execute PDAL pipeline
    print(f"\n🚀 Executing PDAL pipeline...")
    pipeline_json = get_pipeline_json(pipeline)
    pdal_pipeline = pdal.Pipeline(pipeline_json)
    
    try:
        print(f"   🔄 Running PDAL execution...")
        execution_start = time.time()
        
        count = pdal_pipeline.execute()
        
        execution_time = time.time() - execution_start
        print(f"   ✅ PDAL execution completed in {execution_time:.2f} seconds")
        print(f"   📊 Total points processed: {count:,}")
        
        # Validate output file
        print(f"\n🔍 Validating output file...")
        if os.path.exists(output_file):
            output_size = os.path.getsize(output_file)
            print(f"✅ Output file created successfully")
            print(f"📊 Output file size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
            
            # Additional file info
            print(f"📄 Output file path: {os.path.abspath(output_file)}")
            
            # Run gdalinfo to get detailed information about the generated DTM
            print(f"\n📊 GDALINFO OUTPUT:")
            print(f"{'='*40}")
            try:
                gdalinfo_result = subprocess.run(
                    ['gdalinfo', output_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if gdalinfo_result.returncode == 0:
                    print(gdalinfo_result.stdout)
                else:
                    print(f"❌ gdalinfo failed with return code {gdalinfo_result.returncode}")
                    print(f"❌ Error: {gdalinfo_result.stderr}")
                    
            except FileNotFoundError:
                print(f"⚠️ gdalinfo command not found. Please ensure GDAL is installed and in PATH.")
            except subprocess.TimeoutExpired:
                print(f"⚠️ gdalinfo command timed out after 30 seconds.")
            except Exception as e:
                print(f"⚠️ Error running gdalinfo: {str(e)}")
            
            print(f"{'='*40}")
            
            success_msg = f"DTM generated successfully at {output_file}"
            print(f"✅ {success_msg}")
            print(f"{'='*60}\n")
            
            return True, success_msg
        else:
            error_msg = "Output file was not created"
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg
            
    except RuntimeError as e:
        error_msg = f"PDAL execution failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Error type: RuntimeError")
        print(f"❌ Full error: {str(e)}")
        print(f"{'='*60}\n")
        return False, error_msg
    
    except Exception as e:
        error_msg = f"Unexpected error during PDAL execution: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Full error: {str(e)}")
        print(f"{'='*60}\n")
        return False, error_msg
