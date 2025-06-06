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
    print(f"\n{'='*60}")
    print(f"📐 SLOPE PROCESSING STARTING")
    print(f"{'='*60}")
    print(f"📁 Input LAZ file: {laz_file_path}")
    print(f"📂 Output directory: {output_dir}")
    print(f"⚙️ Parameters: {parameters}")
    print(f"🕐 Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    logger.info(f"Starting Slope processing for {laz_file_path}")
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
        output_filename = f"{region_name}_Slope.tif"
        output_file = os.path.join(output_dir, output_filename)
        print(f"📄 [FILE CREATION] Creating output file: {output_file}")
        print(f"   📝 Filename pattern: <region_name>_Slope.tif")
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
        
        # Extract region name from the file path structure
        input_path = Path(laz_file_path)
        if "lidar" in input_path.parts:
            region_name = input_path.parts[input_path.parts.index("input") + 1]
        else:
            region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(laz_file_path))[0]
        
        # Generate output filename using new naming convention: <region_name>_<processing_step>
        output_filename = f"{region_name}_Slope.tif"
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
        print(f"{'='*60}\n")
        
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
        print(f"{'='*60}\n")
        
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
        print(f"{'='*60}\n")
        
        logger.error(f"Unexpected error in Slope processing: {error_msg}", exc_info=True)
        
        return {
            "success": False,
            "message": f"Processing failed: {error_msg}",
            "error_type": type(e).__name__,
            "processing_time": processing_time,
            "input_file": laz_file_path
        }

def slope(input_file: str, region_name: str = None) -> str:
    """
    Generate slope analysis from LAZ file using GDAL DEM processing
    
    Args:
        input_file: Path to the input LAZ file
        region_name: Optional region name to use for output directory (instead of extracted from filename)
        Returns:
        Path to the generated slope TIF file
    """
    print(f"\n📐 SLOPE: Starting analysis for {input_file}")
    start_time = time.time()
    
    # Extract filename from the file path structure
    input_path = Path(input_file)
    file_stem = input_path.stem  # Get filename without extension (e.g., "OR_WizardIsland")
    
    # Use provided region_name for output directory if available, otherwise use file_stem
    
    output_folder_name = region_name if region_name else file_stem
    
    print(f"📁 Using output folder name: {output_folder_name} (from region_name: {region_name})")
    
    
    
    # Create output directory structure: output/<output_folder_name>/lidar/
    
    output_dir = os.path.join("output", output_folder_name, "lidar", "Slope")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <file_stem>_Slope.tif
    output_filename = f"{file_stem}_Slope.tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path}")
    
    try:
        # Step 1: Generate or locate DTM
        print(f"\n🏔️ Step 1: Generating DTM as source for slope analysis...")
        dtm_path = dtm(input_file, region_name)
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
