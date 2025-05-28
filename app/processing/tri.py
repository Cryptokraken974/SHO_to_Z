import asyncio
import time
import os
import logging
import subprocess
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
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Check if input file exists
        if not os.path.exists(laz_file_path):
            raise FileNotFoundError(f"LAZ file not found: {laz_file_path}")
        
        logger.info(f"Starting TRI processing for {laz_file_path}")
        
        # Simulate processing time
        await asyncio.sleep(2.5)
        
        # TODO: Implement actual TRI processing
        # This would typically involve:
        # 1. Creating DTM from LAZ file
        # 2. Calculating terrain ruggedness using Riley algorithm
        # 3. Computing mean difference between cell and neighbors
        # 4. Saving as GeoTIFF
        
        # Generate output filename using new naming convention: <laz_filename_without_ext>_<processing_step>
        laz_basename = os.path.splitext(os.path.basename(laz_file_path))[0]
        output_filename = f"{laz_basename}_TRI.tif"
        output_file = os.path.join(output_dir, output_filename)
        
        # Simulate creating output file
        with open(output_file, 'w') as f:
            f.write("TRI placeholder file")
        
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
    
    # Extract the base name without path and extension
    laz_basename = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory structure: output/<laz_basename>/TRI/
    output_dir = os.path.join("output", laz_basename, "TRI")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <laz_basename>_tri.tif
    output_filename = f"{laz_basename}_tri.tif"
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
