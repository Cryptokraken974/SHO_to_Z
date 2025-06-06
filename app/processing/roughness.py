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

async def process_roughness(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Roughness analysis from LAZ file
    
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
        
        logger.info(f"Starting Roughness processing for {laz_file_path}")
        
        # Simulate processing time
        await asyncio.sleep(2.0)
        
        # TODO: Implement actual Roughness processing
        # This would typically involve:
        # 1. Creating DTM from LAZ file
        # 2. Calculating surface roughness using various methods
        # 3. Computing standard deviation of elevation
        # 4. Saving as GeoTIFF
        
        # Extract region name from the file path structure
        input_path = Path(laz_file_path)
        if "lidar" in input_path.parts:
            region_name = input_path.parts[input_path.parts.index("input") + 1]
        else:
            region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(laz_file_path))[0]
        
        # Generate output filename using new naming convention: <region_name>_<processing_step>
        output_filename = f"{region_name}_Roughness.tif"
        output_file = os.path.join(output_dir, output_filename)
        
        # Simulate creating output file
        with open(output_file, 'w') as f:
            f.write("Roughness placeholder file")
        
        processing_time = time.time() - start_time
        
        logger.info(f"Roughness processing completed in {processing_time:.2f} seconds")
        
        return {
            "success": True,
            "message": "Roughness processing completed successfully",
            "output_file": output_file,
            "processing_time": processing_time,
            "metadata": {
                "input_file": laz_file_path,
                "processing_type": "Roughness",
                "method": parameters.get("method", "standard_deviation"),
                "window_size": parameters.get("window_size", 3),
                "scale_factor": parameters.get("scale_factor", 1.0)
            }
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Roughness processing failed: {str(e)}")
        
        return {
            "success": False,
            "message": f"Roughness processing failed: {str(e)}",
            "processing_time": processing_time,
            "metadata": {
                "input_file": laz_file_path,
                "processing_type": "Roughness",
                "error": str(e)
            }
        }

def roughness(input_file: str, region_name: str = None) -> str:
    """
    Generate surface roughness analysis from LAZ file using GDAL DEM processing
    
    Args:
        input_file: Path to the input LAZ file
        region_name: Optional region name to use for output directory (instead of extracted from filename)
        Returns:
        Path to the generated roughness TIF file
    """
    print(f"\n🌊 ROUGHNESS: Starting analysis for {input_file}")
    start_time = time.time()
    
    # Extract file stem for consistent directory structure
    # Path structure: input/<region_name>/lidar/<filename> or input/<region_name>/<filename>
    input_path = Path(input_file)
    file_stem = input_path.stem  # Get filename without extension (e.g., "OR_WizardIsland")
    
    # Only extract region_name from file path if it wasn't provided as a parameter
    if region_name is None:
        if "lidar" in input_path.parts:
            # File is in lidar subfolder: extract parent's parent as region name
            region_name = input_path.parts[input_path.parts.index("input") + 1]
        else:
            # File is directly in input folder: extract parent as region name
            region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(input_file))[0]
    
    # Use provided region_name for output directory if available, otherwise use file_stem
    
    output_folder_name = region_name if region_name else file_stem
    
    print(f"📁 Using output folder name: {output_folder_name} (from region_name: {region_name})")
    
    
    
    # Create output directory structure: output/<output_folder_name>/lidar/
    
    output_dir = os.path.join("output", output_folder_name, "lidar", "Roughness")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <file_stem>_Roughness.tif
    output_filename = f"{file_stem}_Roughness.tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path}")
    
    try:
        # Step 1: Generate or locate DTM
        print(f"\n🏔️ Step 1: Generating DTM as source for roughness analysis...")
        dtm_path = dtm(input_file, region_name)
        print(f"✅ DTM ready: {dtm_path}")
        
        # Step 2: Generate roughness using GDAL DEMProcessing
        print(f"\n🌊 Step 2: Generating roughness using GDAL DEMProcessing...")
        print(f"📁 Source DTM: {dtm_path}")
        print(f"📁 Target roughness: {output_path}")
        
        # Configure roughness parameters
        compute_edges = True  # Compute values at edges
        
        print(f"⚙️ Roughness parameters:")
        print(f"   📊 Algorithm: Largest inter-cell difference of central pixel and neighbors")
        print(f"   🔲 Compute edges: {compute_edges}")
        print(f"   📏 Output: Maximum elevation difference in 3x3 window")
        
        # Use GDAL DEMProcessing for roughness analysis
        processing_start = time.time()
        
        result = gdal.DEMProcessing(
            destName=output_path,
            srcDS=dtm_path,
            processing="Roughness",
            computeEdges=compute_edges,
            format="GTiff"
        )
        
        processing_time = time.time() - processing_start
        
        if result is None:
            raise RuntimeError("GDAL DEMProcessing failed to generate roughness")
        
        print(f"✅ Roughness analysis completed in {processing_time:.2f} seconds")
        
        # Step 3: Validate output file
        print(f"\n🔍 Validating output file...")
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            print(f"✅ Output file created successfully")
            print(f"📊 Output file size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
            print(f"📄 Output file path: {os.path.abspath(output_path)}")
            
            # Run gdalinfo to get information about the generated roughness
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
            raise FileNotFoundError(f"Roughness output file was not created: {output_path}")
        
        total_time = time.time() - start_time
        print(f"✅ ROUGHNESS analysis completed successfully in {total_time:.2f} seconds")
        print(f"🌊 Roughness file: {output_path}")
        
        return output_path
        
    except Exception as e:
        total_time = time.time() - start_time
        error_msg = f"Roughness analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Failed after {total_time:.2f} seconds")
        raise Exception(error_msg)
