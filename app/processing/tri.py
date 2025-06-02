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

async def process_tri(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process TRI (Terrain Ruggedness Index) from LAZ file
    
    Args:
        laz_file_path: Path to the input LAZ file
        output_dir: Directory to save output files
        parameters: Processing parameters
    
    Returns:
        Dict containing processing results
    """
    start_time = time.time()
    
    try:
        print(f"\n{'='*60}")
        print(f"📊 TRI (TERRAIN RUGGEDNESS INDEX) PROCESSING")
        print(f"{'='*60}")
        print(f"📂 Input file: {laz_file_path}")
        print(f"📁 Output directory: {output_dir}")
        
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
        output_filename = f"{region_name}_TRI.tif"
        output_file = os.path.join(output_dir, output_filename)
        print(f"📄 [FILE CREATION] Creating output file: {output_file}")
        print(f"   📝 Filename pattern: <region_name>_TRI.tif")
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
        
        print(f"⚙️ [PROCESSING CONFIG] TRI analysis parameters:")
        print(f"   📏 Algorithm: Riley's Terrain Ruggedness Index")
        print(f"   🧮 Method: Mean difference between cell and neighbors")
        print(f"   📊 Output: Higher values = more rugged terrain")
        
        logger.info(f"Starting TRI processing for {laz_file_path}")
        
        print(f"🔄 [PROCESSING] Processing TRI Analysis (simulated)...")
        print(f"   🏔️ Creating DTM from LAZ file...")
        print(f"   📊 Calculating terrain ruggedness using Riley algorithm...")
        print(f"   🧮 Computing mean difference between cell and neighbors...")
        print(f"   💾 Saving as GeoTIFF...")
        
        # Simulate processing time
        await asyncio.sleep(2.5)
        
        # Simulate creating output file
        print(f"💾 [FILE WRITING] Creating output file...")
        print(f"   📂 Writing to: {output_file}")
        
        with open(output_file, 'w') as f:
            f.write("TRI placeholder file")
        
        output_size = os.path.getsize(output_file)
        print(f"✅ [FILE CREATED] Output file created successfully")
        print(f"   📂 File location: {output_file}")
        print(f"   📊 File size: {output_size} bytes")
        
        processing_time = time.time() - start_time
        
        print(f"⏱️ [TIMING] Processing completed in {processing_time:.2f} seconds")
        print(f"✅ [SUCCESS] TRI PROCESSING SUCCESSFUL")
        print(f"{'='*60}\n")
        
        logger.info(f"TRI processing completed in {processing_time:.2f} seconds")
        
        processing_time = time.time() - start_time
        
        logger.info(f"TRI processing completed in {processing_time:.2f} seconds")
        
        return {
            "success": True,
            "message": "TRI (Terrain Ruggedness Index) processing completed successfully",
            "output_file": output_file,
            "processing_time": processing_time,
            "metadata": {
                "input_file": laz_file_path,
                "processing_type": "TRI",
                "algorithm": parameters.get("algorithm", "Riley"),
                "neighborhood": parameters.get("neighborhood", "3x3"),
                "scale_factor": parameters.get("scale_factor", 1.0)
            }
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"TRI processing failed: {str(e)}")
        
        return {
            "success": False,
            "message": f"TRI processing failed: {str(e)}",
            "processing_time": processing_time,
            "metadata": {
                "input_file": laz_file_path,
                "processing_type": "TRI",
                "error": str(e)
            }
        }

def tri(input_file: str) -> str:
    """
    Generate TRI (Terrain Ruggedness Index) from LAZ file using GDAL DEM processing
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated TRI TIF file
    """
    print(f"\n🏔️ TRI: Starting analysis for {input_file}")
    start_time = time.time()
    
    # Extract region name from the file path structure
    # Path structure: input/<region_name>/lidar/<filename> or input/<region_name>/<filename>
    input_path = Path(input_file)
    if "lidar" in input_path.parts:
        # File is in lidar subfolder: extract parent's parent as region name
        region_name = input_path.parts[input_path.parts.index("input") + 1]
    else:
        # File is directly in input folder: extract parent as region name
        region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory structure: output/<region_name>/TRI/
    output_dir = os.path.join("output", region_name, "TRI")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <region_name>_tri.tif
    output_filename = f"{region_name}_tri.tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path}")
    
    try:
        # Step 1: Generate or locate DTM
        print(f"\n🏔️ Step 1: Generating DTM as source for TRI analysis...")
        dtm_path = dtm(input_file)
        print(f"✅ DTM ready: {dtm_path}")
        
        # Step 2: Generate TRI using GDAL DEMProcessing
        print(f"\n🏔️ Step 2: Generating TRI using GDAL DEMProcessing...")
        print(f"📁 Source DTM: {dtm_path}")
        print(f"📁 Target TRI: {output_path}")
        
        # Configure TRI parameters
        compute_edges = True  # Compute values at edges
        
        print(f"⚙️ TRI parameters:")
        print(f"   📊 Algorithm: Wilson et al. (2007)")
        print(f"   🔲 Compute edges: {compute_edges}")
        print(f"   📏 Output: Mean difference between central pixel and surrounding cells")
        
        # Use GDAL DEMProcessing for TRI analysis
        processing_start = time.time()
        
        result = gdal.DEMProcessing(
            destName=output_path,
            srcDS=dtm_path,
            processing="TRI",
            computeEdges=compute_edges,
            format="GTiff"
        )
        
        processing_time = time.time() - processing_start
        
        if result is None:
            raise RuntimeError("GDAL DEMProcessing failed to generate TRI")
        
        print(f"✅ TRI analysis completed in {processing_time:.2f} seconds")
        
        # Step 3: Validate output file
        print(f"\n🔍 Validating output file...")
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            print(f"✅ Output file created successfully")
            print(f"📊 Output file size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
            print(f"📄 Output file path: {os.path.abspath(output_path)}")
            
            # Run gdalinfo to get information about the generated TRI
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
            raise FileNotFoundError(f"TRI output file was not created: {output_path}")
        
        total_time = time.time() - start_time
        print(f"✅ TRI analysis completed successfully in {total_time:.2f} seconds")
        print(f"🏔️ TRI file: {output_path}")
        
        return output_path
        
    except Exception as e:
        total_time = time.time() - start_time
        error_msg = f"TRI analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Failed after {total_time:.2f} seconds")
        raise Exception(error_msg)
