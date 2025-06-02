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
        print(f"\n{'='*60}")
        print(f"🧭 ASPECT ANALYSIS PROCESSING")
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
        output_filename = f"{region_name}_Aspect.tif"
        output_file = os.path.join(output_dir, output_filename)
        print(f"📄 [FILE CREATION] Creating output file: {output_file}")
        print(f"   📝 Filename pattern: <region_name>_Aspect.tif")
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
        zero_for_flat = parameters.get("zero_for_flat", False)
        
        print(f"⚙️ [PROCESSING CONFIG] Aspect analysis parameters:")
        print(f"   🧭 Zero for flat areas: {zero_for_flat}")
        
        logger.info(f"Processing with zero_for_flat={zero_for_flat}")
        
        print(f"🔄 [PROCESSING] Processing Aspect Analysis (simulated)...")
        print(f"   🏔️ Creating DTM from LAZ file...")
        print(f"   🧭 Calculating aspect (compass direction of slope)...")
        print(f"   📐 Converting to degrees (0-360)...")
        print(f"   💾 Saving as GeoTIFF...")
        
        # Simulate processing time
        await asyncio.sleep(1.6)
        
        # Simulate creating output file
        print(f"💾 [FILE WRITING] Creating output file...")
        print(f"   📂 Writing to: {output_file}")
        
        with open(output_file, 'w') as f:
            f.write("Aspect placeholder file")
        
        output_size = os.path.getsize(output_file)
        print(f"✅ [FILE CREATED] Output file created successfully")
        print(f"   📂 File location: {output_file}")
        print(f"   📊 File size: {output_size} bytes")
        
        processing_time = time.time() - start_time
        
        print(f"⏱️ [TIMING] Processing completed in {processing_time:.2f} seconds")
        print(f"✅ [SUCCESS] ASPECT ANALYSIS PROCESSING SUCCESSFUL")
        print(f"{'='*60}\n")
        
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
        
    except FileNotFoundError as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        
        print(f"❌ FILE NOT FOUND ERROR after {processing_time:.2f}s")
        print(f"❌ Error: {error_msg}")
        print(f"{'='*60}\n")
        
        logger.error(f"File not found error in Aspect processing: {error_msg}")
        
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
        
        logger.error(f"Unexpected error in Aspect processing: {error_msg}")
        
        return {
            "success": False,
            "message": f"Aspect processing failed: {error_msg}",
            "error_type": type(e).__name__,
            "processing_time": processing_time,
            "input_file": laz_file_path
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
    
    # Extract region name from the file path structure
    # Path structure: input/<region_name>/lidar/<filename> or input/<region_name>/<filename>
    input_path = Path(input_file)
    if "lidar" in input_path.parts:
        # File is in lidar subfolder: extract parent's parent as region name
        region_name = input_path.parts[input_path.parts.index("input") + 1]
    else:
        # File is directly in input folder: extract parent as region name
        region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory structure: output/<region_name>/Aspect/
    output_dir = os.path.join("output", region_name, "Aspect")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <region_name>_aspect.tif
    output_filename = f"{region_name}_aspect.tif"
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


def validate_aspect_cache(aspect_path: str) -> bool:
    """
    Validate if aspect cache is still valid by checking if the file exists
    and is readable.
    
    Args:
        aspect_path: Path to the aspect TIF file
        
    Returns:
        True if cache is valid, False otherwise
    """
    try:
        if not os.path.exists(aspect_path):
            return False
        
        # Try to open with GDAL to ensure file is valid
        dataset = gdal.Open(aspect_path, gdal.GA_ReadOnly)
        if dataset is None:
            return False
        
        # Check if we can read basic properties
        band = dataset.GetRasterBand(1)
        if band is None:
            return False
        
        dataset = None  # Close the dataset
        return True
        
    except Exception:
        return False


def clear_aspect_cache(input_file: str = None) -> None:
    """
    Clear aspect cache files. If input_file is provided, clear cache for that specific file.
    If input_file is None, clear all aspect cache files.
    
    Args:
        input_file: Optional path to specific input file
    """
    if input_file:
        # Clear cache for specific file
        input_path = Path(input_file)
        if "lidar" in input_path.parts:
            region_name = input_path.parts[input_path.parts.index("input") + 1]
        else:
            region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(input_file))[0]
        
        aspect_dir = os.path.join("output", region_name, "Aspect")
        if os.path.exists(aspect_dir):
            import shutil
            shutil.rmtree(aspect_dir)
            print(f"🗑️ Cleared aspect cache for region: {region_name}")
    else:
        # Clear all aspect cache files
        output_base = "output"
        if os.path.exists(output_base):
            for region_dir in os.listdir(output_base):
                aspect_dir = os.path.join(output_base, region_dir, "Aspect")
                if os.path.exists(aspect_dir):
                    import shutil
                    shutil.rmtree(aspect_dir)
                    print(f"🗑️ Cleared aspect cache for region: {region_dir}")
        print(f"🗑️ Cleared all aspect cache files")


def get_aspect_cache_info() -> dict:
    """
    Get information about current aspect cache.
    
    Returns:
        Dictionary containing cache information
    """
    cache_info = {
        "regions": {},
        "total_files": 0,
        "total_size_mb": 0
    }
    
    output_base = "output"
    if not os.path.exists(output_base):
        return cache_info
    
    for region_dir in os.listdir(output_base):
        aspect_dir = os.path.join(output_base, region_dir, "Aspect")
        if os.path.exists(aspect_dir):
            files = [f for f in os.listdir(aspect_dir) if f.endswith('.tif')]
            total_size = sum(os.path.getsize(os.path.join(aspect_dir, f)) for f in files)
            
            cache_info["regions"][region_dir] = {
                "files": len(files),
                "size_mb": total_size / (1024 * 1024),
                "path": aspect_dir
            }
            
            cache_info["total_files"] += len(files)
            cache_info["total_size_mb"] += total_size / (1024 * 1024)
    
    return cache_info
