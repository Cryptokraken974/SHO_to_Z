import asyncio
import time
import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any
from osgeo import gdal
from .dtm import dtm

logger = logging.getLogger(__name__)

async def process_color_relief(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Color-relief from LAZ file
    
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
        print(f"🎨 COLOR RELIEF PROCESSING")
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
        output_filename = f"{region_name}_ColorRelief.tif"
        output_file = os.path.join(output_dir, output_filename)
        print(f"📄 [FILE CREATION] Creating output file: {output_file}")
        print(f"   📝 Filename pattern: <region_name>_ColorRelief.tif")
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
        color_ramp = parameters.get("color_ramp", "elevation")
        min_elevation = parameters.get("min_elevation", "auto")
        max_elevation = parameters.get("max_elevation", "auto")
        
        print(f"⚙️ [PROCESSING CONFIG] Color relief parameters:")
        print(f"   🎨 Color ramp: {color_ramp}")
        print(f"   📏 Min elevation: {min_elevation}")
        print(f"   📏 Max elevation: {max_elevation}")
        
        logger.info(f"Processing with color_ramp={color_ramp}, min_elevation={min_elevation}, max_elevation={max_elevation}")
        
        print(f"🔄 [PROCESSING] Processing Color Relief (simulated)...")
        print(f"   🏔️ Creating DTM from LAZ file...")
        print(f"   🎨 Applying color ramp based on elevation...")
        print(f"   🖼️ Creating visualization with color mapping...")
        print(f"   💾 Saving as GeoTIFF...")
        
        # Simulate processing time
        await asyncio.sleep(2.2)
        
        # Simulate creating output file
        print(f"💾 [FILE WRITING] Creating output file...")
        print(f"   📂 Writing to: {output_file}")
        
        with open(output_file, 'w') as f:
            f.write("Color-relief placeholder file")
        
        output_size = os.path.getsize(output_file)
        print(f"✅ [FILE CREATED] Output file created successfully")
        print(f"   📂 File location: {output_file}")
        print(f"   📊 File size: {output_size} bytes")
        
        processing_time = time.time() - start_time
        
        print(f"⏱️ [TIMING] Processing completed in {processing_time:.2f} seconds")
        print(f"✅ [SUCCESS] COLOR RELIEF PROCESSING SUCCESSFUL")
        print(f"{'='*60}\n")
        
        # Simulate creating output file
        with open(output_file, 'w') as f:
            f.write("Color-relief placeholder file")
        
        processing_time = time.time() - start_time
        
        logger.info(f"Color-relief processing completed in {processing_time:.2f} seconds")
        
        return {
            "success": True,
            "message": "Color-relief processing completed successfully",
            "output_file": output_file,
            "processing_time": processing_time,
            "metadata": {
                "input_file": laz_file_path,
                "processing_type": "Color-relief",
                "color_ramp": parameters.get("color_ramp", "elevation"),
                "min_elevation": parameters.get("min_elevation", "auto"),
                "max_elevation": parameters.get("max_elevation", "auto")
            }
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Color-relief processing failed: {str(e)}")
        
        return {
            "success": False,
            "message": f"Color-relief processing failed: {str(e)}",
            "processing_time": processing_time,
            "metadata": {
                "input_file": laz_file_path,
                "processing_type": "Color-relief",
                "error": str(e)
            }
        }

def create_color_table(color_table_path: str, min_elevation: float, max_elevation: float) -> None:
    """
    Create a color table file for terrain elevation visualization
    
    Args:
        color_table_path: Path where to save the color table file
        min_elevation: Minimum elevation value
        max_elevation: Maximum elevation value
    """
    # Create a terrain-like color ramp from blue (low) to red (high)
    elevation_range = max_elevation - min_elevation
    
    # Define color stops as percentages of the elevation range
    color_stops = [
        (0.0, "0 0 139"),      # Dark blue (deep water/low)
        (0.1, "0 100 255"),    # Blue (water)
        (0.2, "0 255 255"),    # Cyan (shallow water)
        (0.3, "0 255 0"),      # Green (low land)
        (0.5, "255 255 0"),    # Yellow (medium elevation)
        (0.7, "255 165 0"),    # Orange (higher elevation)
        (0.9, "255 69 0"),     # Red-orange (high elevation)
        (1.0, "255 255 255")   # White (peaks)
    ]
    
    with open(color_table_path, 'w') as f:
        for percentage, rgb in color_stops:
            elevation = min_elevation + (percentage * elevation_range)
            f.write(f"{elevation} {rgb}\n")
    
    print(f"📊 Color table created: {color_table_path}")
    print(f"   📏 Elevation range: {min_elevation:.2f} to {max_elevation:.2f}")


def color_relief(input_file: str) -> str:
    """
    Generate color relief from LAZ file using GDAL DEM processing
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated color relief TIF file
    """
    print(f"\n🎨 COLOR_RELIEF: Starting generation for {input_file}")
    start_time = time.time()
    
    # Extract file stem for consistent directory structure
    # Path structure: input/<region_name>/lidar/<filename> or input/<region_name>/<filename>
    input_path = Path(input_file)
    if "lidar" in input_path.parts:
        # File is in lidar subfolder: extract parent's parent as region name
        region_name = input_path.parts[input_path.parts.index("input") + 1]
    else:
        # File is directly in input folder: extract parent as region name
        region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(input_file))[0]
    
    file_stem = input_path.stem  # Get filename without extension (e.g., "OR_WizardIsland")
    
    # Create output directory structure: output/LAZ/<file_stem>/color_relief/
    output_dir = os.path.join("output", "LAZ", file_stem, "color_relief")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <file_stem>_ColorRelief.tif
    output_filename = f"{file_stem}_ColorRelief.tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path}")
    
    try:
        # Step 1: Generate or locate DTM
        print(f"\n🏔️ Step 1: Generating DTM as source for color relief...")
        dtm_path = dtm(input_file)
        print(f"✅ DTM ready: {dtm_path}")
        
        # Step 2: Get DTM statistics to create appropriate color table
        print(f"\n📊 Step 2: Analyzing DTM statistics...")
        dtm_dataset = gdal.Open(dtm_path)
        if dtm_dataset is None:
            raise RuntimeError(f"Failed to open DTM file: {dtm_path}")
        
        band = dtm_dataset.GetRasterBand(1)
        stats = band.GetStatistics(False, True)  # Force calculation of stats
        min_elevation, max_elevation = stats[0], stats[1]
        
        print(f"📊 DTM Statistics:")
        print(f"   📏 Min elevation: {min_elevation:.2f}")
        print(f"   📏 Max elevation: {max_elevation:.2f}")
        print(f"   📐 Range: {max_elevation - min_elevation:.2f}")
        
        dtm_dataset = None  # Close dataset
        
        # Step 3: Create color table
        print(f"\n🎨 Step 3: Creating color table...")
        color_table_path = os.path.join(output_dir, f"{file_stem}_color_table.txt")
        create_color_table(color_table_path, min_elevation, max_elevation)
        
        # Step 4: Generate color relief using GDAL DEMProcessing
        print(f"\n🎨 Step 4: Generating color relief using GDAL DEMProcessing...")
        print(f"📁 Source DTM: {dtm_path}")
        print(f"📁 Color table: {color_table_path}")
        print(f"📁 Target color relief: {output_path}")
        
        # Configure color relief parameters
        print(f"⚙️ Color relief parameters:")
        print(f"   🎨 Color table: Custom terrain ramp")
        print(f"   📊 Format: RGB TIFF")
        print(f"   🌈 Colors: Blue→Cyan→Green→Yellow→Orange→Red→White")
        
        # Use GDAL DEMProcessing for color relief generation
        processing_start = time.time()
        
        result = gdal.DEMProcessing(
            destName=output_path,
            srcDS=dtm_path,
            processing="color-relief",
            colorFilename=color_table_path,
            format="GTiff"
        )
        
        processing_time = time.time() - processing_start
        
        if result is None:
            raise RuntimeError("GDAL DEMProcessing failed to generate color relief")
        
        print(f"✅ Color relief generation completed in {processing_time:.2f} seconds")
        
        # Step 5: Validate output file
        print(f"\n🔍 Validating output file...")
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            print(f"✅ Output file created successfully")
            print(f"📊 Output file size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
            print(f"📄 Output file path: {os.path.abspath(output_path)}")
            
            # Run gdalinfo to get information about the generated color relief
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
            raise FileNotFoundError(f"Color relief output file was not created: {output_path}")
        
        total_time = time.time() - start_time
        print(f"✅ COLOR RELIEF generation completed successfully in {total_time:.2f} seconds")
        print(f"🎨 Color relief file: {output_path}")
        
        return output_path
        
    except Exception as e:
        total_time = time.time() - start_time
        error_msg = f"Color relief generation failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Failed after {total_time:.2f} seconds")
        raise Exception(error_msg)
