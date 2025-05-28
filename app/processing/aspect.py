import asyncio
import time
import os
import logging
import subprocess
from typing import Dict, Any
from osgeo import gdal
from .dtm import dtm

logger = logging.getLogger(__name__)

async def process_aspect(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Aspect analysis from LAZ file
    
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
        
        logger.info(f"Starting Aspect processing for {laz_file_path}")
        
        # Simulate processing time
        await asyncio.sleep(1.6)
        
        # TODO: Implement actual Aspect processing
        # This would typically involve:
        # 1. Creating DTM from LAZ file
        # 2. Calculating aspect (compass direction of slope)
        # 3. Converting to degrees (0-360)
        # 4. Saving as GeoTIFF
        
        # Generate output filename using new naming convention: <laz_filename_without_ext>_<processing_step>
        laz_basename = os.path.splitext(os.path.basename(laz_file_path))[0]
        output_filename = f"{laz_basename}_Aspect.tif"
        output_file = os.path.join(output_dir, output_filename)
        
        # Simulate creating output file
        with open(output_file, 'w') as f:
            f.write("Aspect placeholder file")
        
        processing_time = time.time() - start_time
        
        logger.info(f"Aspect processing completed in {processing_time:.2f} seconds")
        
        return {
            "success": True,
            "message": "Aspect processing completed successfully",
            "output_file": output_file,
            "processing_time": processing_time,
            "metadata": {
                "input_file": laz_file_path,
                "processing_type": "Aspect",
                "units": parameters.get("units", "degrees"),
                "north_reference": parameters.get("north_reference", "geographic"),
                "algorithm": parameters.get("algorithm", "Horn")
            }
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Aspect processing failed: {str(e)}")
        
        return {
            "success": False,
            "message": f"Aspect processing failed: {str(e)}",
            "processing_time": processing_time,
            "metadata": {
                "input_file": laz_file_path,
                "processing_type": "Aspect",
                "error": str(e)
            }
        }

def aspect(input_file: str) -> str:
    """
    Generate aspect analysis from LAZ file using GDAL DEM processing
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated aspect TIF file
    """
    print(f"\n🧭 ASPECT: Starting analysis for {input_file}")
    start_time = time.time()
    
    # Extract the base name without path and extension
    laz_basename = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory structure: output/<laz_basename>/Aspect/
    output_dir = os.path.join("output", laz_basename, "Aspect")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <laz_basename>_aspect.tif
    output_filename = f"{laz_basename}_aspect.tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path}")
    
    try:
        # Step 1: Generate or locate DTM
        print(f"\n🏔️ Step 1: Generating DTM as source for aspect analysis...")
        dtm_path = dtm(input_file)
        print(f"✅ DTM ready: {dtm_path}")
        
        # Step 2: Generate aspect using GDAL DEMProcessing
        print(f"\n🧭 Step 2: Generating aspect using GDAL DEMProcessing...")
        print(f"📁 Source DTM: {dtm_path}")
        print(f"📁 Target aspect: {output_path}")
        
        # Configure aspect parameters
        trigonometric = False  # Use compass direction (0°=North, 90°=East)
        zero_for_flat = False  # Don't use 0 for flat areas
        
        print(f"⚙️ Aspect parameters:")
        print(f"   🧭 Output format: compass degrees (0°=North)")
        print(f"   🔢 Range: 0-360 degrees")
        print(f"   📐 Trigonometric: {trigonometric}")
        print(f"   🎯 Zero for flat: {zero_for_flat}")
        
        # Use GDAL DEMProcessing for aspect analysis
        processing_start = time.time()
        
        result = gdal.DEMProcessing(
            destName=output_path,
            srcDS=dtm_path,
            processing="aspect",
            trigonometric=trigonometric,
            zeroForFlat=zero_for_flat,
            format="GTiff"
        )
        
        processing_time = time.time() - processing_start
        
        if result is None:
            raise RuntimeError("GDAL DEMProcessing failed to generate aspect")
        
        print(f"✅ Aspect analysis completed in {processing_time:.2f} seconds")
        
        # Step 3: Validate output file
        print(f"\n🔍 Validating output file...")
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            print(f"✅ Output file created successfully")
            print(f"📊 Output file size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
            print(f"📄 Output file path: {os.path.abspath(output_path)}")
            
            # Run gdalinfo to get information about the generated aspect
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
            raise FileNotFoundError(f"Aspect output file was not created: {output_path}")
        
        total_time = time.time() - start_time
        print(f"✅ ASPECT analysis completed successfully in {total_time:.2f} seconds")
        print(f"🧭 Aspect file: {output_path}")
        
        return output_path
        
    except Exception as e:
        total_time = time.time() - start_time
        error_msg = f"Aspect analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Failed after {total_time:.2f} seconds")
        raise Exception(error_msg)
