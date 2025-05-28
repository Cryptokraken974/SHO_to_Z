import asyncio
import time
import os
import logging
import subprocess
from typing import Dict, Any
from osgeo import gdal
from .dtm import dtm

logger = logging.getLogger(__name__)

async def process_slope(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Slope analysis from LAZ file
    
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
    print(f"🚀 STARTING SLOPE PROCESSING")
    print(f"{'='*50}")
    print(f"📁 Input LAZ file: {laz_file_path}")
    print(f"📂 Output directory: {output_dir}")
    print(f"⚙️ Parameters: {parameters}")
    print(f"🕐 Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    logger.info(f"Starting Slope processing for {laz_file_path}")
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
        units = parameters.get("units", "degrees")
        
        print(f"⚙️ Slope parameters:")
        print(f"   📐 Units: {units}")
        
        logger.info(f"Processing with units={units}")
        
        print(f"🔄 Processing Slope (simulated)...")
        print(f"   📊 Calculating elevation gradients...")
        print(f"   📐 Computing slope angles...")
        print(f"   📏 Converting to {units}...")
        
        # Simulate processing time
        await asyncio.sleep(2.2)
        print(f"⏳ Slope processing simulation completed")
        
        # Generate output filename using new naming convention: <laz_filename_without_ext>_<processing_step>
        laz_basename = os.path.splitext(os.path.basename(laz_file_path))[0]
        output_filename = f"{laz_basename}_Slope.tif"
        output_file = os.path.join(output_dir, output_filename)
        print(f"📄 Creating output file: {output_file}")
        
        # Simulate creating output file
        with open(output_file, 'w') as f:
            f.write("Slope placeholder file")
        
        output_size = os.path.getsize(output_file)
        print(f"✅ Output file created successfully")
        print(f"📊 Output file size: {output_size} bytes")
        
        processing_time = time.time() - start_time
        
        print(f"⏱️ Processing completed in {processing_time:.2f} seconds")
        print(f"✅ SLOPE PROCESSING SUCCESSFUL")
        print(f"{'='*50}\n")
        
        logger.info(f"Slope processing completed in {processing_time:.2f} seconds")
        logger.info(f"Output file created: {output_file}")
        
        return {
            "success": True,
            "message": "Slope processing completed successfully",
            "output_file": output_file,
            "processing_time": processing_time,
            "input_file": laz_file_path,
            "parameters_used": {
                "units": units
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
        
        logger.error(f"File not found error in Slope processing: {error_msg}")
        
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
        
        logger.error(f"Unexpected error in Slope processing: {error_msg}", exc_info=True)
        
        return {
            "success": False,
            "message": f"Processing failed: {error_msg}",
            "error_type": type(e).__name__,
            "processing_time": processing_time,
            "input_file": laz_file_path
        }

def slope(input_file: str) -> str:
    """
    Generate slope analysis from LAZ file using GDAL DEM processing
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated slope TIF file
    """
    print(f"\n📐 SLOPE: Starting analysis for {input_file}")
    start_time = time.time()
    
    # Extract the base name without path and extension
    laz_basename = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory structure: output/<laz_basename>/Slope/
    output_dir = os.path.join("output", laz_basename, "Slope")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <laz_basename>_slope.tif
    output_filename = f"{laz_basename}_slope.tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path}")
    
    try:
        # Step 1: Generate or locate DTM
        print(f"\n🏔️ Step 1: Generating DTM as source for slope analysis...")
        dtm_path = dtm(input_file)
        print(f"✅ DTM ready: {dtm_path}")
        
        # Step 2: Generate slope using GDAL DEMProcessing
        print(f"\n📐 Step 2: Generating slope using GDAL DEMProcessing...")
        print(f"📁 Source DTM: {dtm_path}")
        print(f"📁 Target slope: {output_path}")
        
        # Configure slope parameters
        compute_edges = True  # Compute values at edges
        scale = 1.0          # Scale factor for degrees
        
        print(f"⚙️ Slope parameters:")
        print(f"   📊 Output format: degrees")
        print(f"   🔢 Scale factor: {scale}")
        print(f"   🔲 Compute edges: {compute_edges}")
        
        # Use GDAL DEMProcessing for slope analysis
        processing_start = time.time()
        
        result = gdal.DEMProcessing(
            destName=output_path,
            srcDS=dtm_path,
            processing="slope",
            computeEdges=compute_edges,
            scale=scale,
            format="GTiff"
        )
        
        processing_time = time.time() - processing_start
        
        if result is None:
            raise RuntimeError("GDAL DEMProcessing failed to generate slope")
        
        print(f"✅ Slope analysis completed in {processing_time:.2f} seconds")
        
        # Step 3: Validate output file
        print(f"\n🔍 Validating output file...")
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            print(f"✅ Output file created successfully")
            print(f"📊 Output file size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
            print(f"📄 Output file path: {os.path.abspath(output_path)}")
            
            # Run gdalinfo to get information about the generated slope
            print(f"\n📊 GDALINFO OUTPUT:")
            print(f"{'='*40}")
            try:
                gdalinfo_result = subprocess.run(
                    ['gdalinfo', output_path],
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
            
        else:
            raise FileNotFoundError(f"Slope output file was not created: {output_path}")
        
        total_time = time.time() - start_time
        print(f"✅ SLOPE analysis completed successfully in {total_time:.2f} seconds")
        print(f"📐 Slope file: {output_path}")
        
        return output_path
        
    except Exception as e:
        total_time = time.time() - start_time
        error_msg = f"Slope analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Failed after {total_time:.2f} seconds")
        raise Exception(error_msg)
