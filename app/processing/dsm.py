import asyncio
import time
import os
import logging
import subprocess
import json
from pathlib import Path
from typing import Dict, Any
import pdal

logger = logging.getLogger(__name__)


def create_dsm_fallback_pipeline(input_file: str, output_file: str, resolution: float = 1.0) -> Dict[str, Any]:
    """
    Create fallback DSM pipeline when JSON pipeline is not available
    """
    return {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": input_file
            },
            {
                "type": "filters.range",
                "limits": "returnnumber[1:1]"  # First returns for surface model
            },
            {
                "type": "writers.gdal",
                "filename": output_file,
                "resolution": resolution,
                "output_type": "max",  # DSM uses maximum for surface features
                "nodata": -9999
            }
        ]
    }


def dsm(input_file: str, region_name: str = None) -> str:
    """
    Convert LAZ file to DSM (Digital Surface Model) - All surface features including vegetation, buildings
    Implements caching to avoid regenerating DSM if it already exists and is up-to-date
    
    Args:
        input_file: Path to the input LAZ file
        region_name: Optional region name to use for output directory (instead of extracted from filename)
        Returns:
        Path to the generated TIF file
    """
    print(f"\n🏗️ DSM: Starting conversion for {input_file}")
    start_time = time.time()
    
    # Check if input file exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input LAZ file not found: {input_file}")
    
    # Check if input file is readable
    if not os.access(input_file, os.R_OK):
        raise PermissionError(f"Input LAZ file is not readable: {input_file}")
    
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
    
    # 🔍 QUALITY MODE INTEGRATION: Check for clean LAZ file
    actual_input_file = input_file
    quality_mode_used = False
    
    # Look for clean LAZ file in output/{region}/cropped/{region}_cropped.las
    potential_clean_laz_patterns = [
        os.path.join("output", output_folder_name, "cropped", f"{output_folder_name}_cropped.las"),
        os.path.join("output", output_folder_name, "cropped", f"{file_stem}_cropped.las"),
        os.path.join("output", output_folder_name, "lidar", "cropped", f"{output_folder_name}_cropped.las"),
        os.path.join("output", output_folder_name, "lidar", "cropped", f"{file_stem}_cropped.las")
    ]
    
    for clean_laz_path in potential_clean_laz_patterns:
        if os.path.exists(clean_laz_path):
            print(f"🎯 QUALITY MODE: Found clean LAZ file: {clean_laz_path}")
            logger.info(f"Quality mode activated: Using clean LAZ file {clean_laz_path} instead of {input_file}")
            actual_input_file = clean_laz_path
            quality_mode_used = True
            break
    
    if not quality_mode_used:
        print(f"📋 STANDARD MODE: Using original LAZ file (no clean LAZ found)")
        logger.info(f"Standard mode: No clean LAZ file found, using original {input_file}")
    
    # Create output directory structure: output/<output_folder_name>/lidar/
    output_dir = os.path.join("output", output_folder_name, "lidar", "DSM")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <file_stem>_DSM.tif (add _clean suffix if quality mode)
    output_filename = f"{file_stem}_DSM"
    if quality_mode_used:
        output_filename += "_clean"
    output_filename += ".tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Actual input file: {actual_input_file}")
    print(f"📄 Output file: {output_path}")
    if quality_mode_used:
        print(f"✨ Quality mode: Clean DSM will be generated")
    
    # Check if DSM already exists and is up-to-date (caching optimization)
    if os.path.exists(output_path) and os.path.exists(actual_input_file):
        try:
            # Compare modification times
            dsm_mtime = os.path.getmtime(output_path)
            laz_mtime = os.path.getmtime(actual_input_file)
            
            if dsm_mtime > laz_mtime:
                # Validate the cached DSM file
                if validate_dsm_cache(output_path):
                    processing_time = time.time() - start_time
                    print(f"🚀 DSM cache hit! Using existing DSM file (created {time.ctime(dsm_mtime)})")
                    print(f"✅ DSM ready in {processing_time:.3f} seconds (cached)")
                    return output_path
                else:
                    print(f"⚠️ Cached DSM file failed validation, regenerating...")
            else:
                print(f"⏰ DSM file exists but is outdated. LAZ modified: {time.ctime(laz_mtime)}, DSM created: {time.ctime(dsm_mtime)}")
        except OSError as e:
            print(f"⚠️ Error checking file timestamps: {e}")
    elif os.path.exists(output_path):
        print(f"⚠️ DSM exists but input LAZ file not found, regenerating DSM")
    else:
        print(f"📝 No existing DSM found, generating new DSM")
    
    # Set default resolution
    resolution = 1.0
    
    # Call the conversion function with detailed logging
    success, message = convert_las_to_dsm(actual_input_file, output_path, resolution)
    
    processing_time = time.time() - start_time
    
    if success:
        print(f"✅ DSM conversion completed successfully in {processing_time:.2f} seconds")
        print(f"📊 Message: {message}")
        
        # 🎯 QUALITY MODE PNG GENERATION: Generate PNG for clean DSM if quality mode was used
        if quality_mode_used:
            print(f"\n🖼️ QUALITY MODE: Generating PNG for clean DSM")
            try:
                from ..convert import convert_geotiff_to_png
                
                # Create png_outputs directory structure
                tif_dir = os.path.dirname(output_path)
                base_output_dir = os.path.dirname(tif_dir)  # Go up from DSM/ to lidar/
                png_output_dir = os.path.join(base_output_dir, "png_outputs")
                os.makedirs(png_output_dir, exist_ok=True)
                
                # Generate PNG with standard filename
                png_path = os.path.join(png_output_dir, "DSM.png")
                convert_geotiff_to_png(
                    output_path, 
                    png_path, 
                    enhanced_resolution=True,
                    save_to_consolidated=False,  # Already in the right directory
                    stretch_type="stddev",
                    stretch_params={"percentile_low": 2, "percentile_high": 98}
                )
                print(f"✅ Quality mode DSM PNG file created: {png_path}")
                logger.info(f"Quality mode DSM PNG generated: {png_path}")
            except Exception as png_error:
                print(f"⚠️ Quality mode DSM PNG generation failed: {png_error}")
                logger.warning(f"Quality mode DSM PNG generation failed: {png_error}")
        
        return output_path
    else:
        print(f"❌ DSM conversion failed after {processing_time:.2f} seconds")
        print(f"❌ Error: {message}")
        raise Exception(f"DSM conversion failed: {message}")


def convert_las_to_dsm(input_file: str, output_file: str, resolution: float = 1.0) -> tuple[bool, str]:
    """
    Convert LAZ file to DSM using PDAL with surface point filtering
    
    Args:
        input_file: Path to the input LAZ file
        region_name: Optional region name to use for output directory (instead of extracted from filename)
        output_file: Path to the output TIF file
        resolution: Grid resolution for DSM generation
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    print(f"\n{'='*60}")
    print(f"🎯 PDAL LAZ TO DSM CONVERSION")
    print(f"{'='*60}")
    print(f"📁 Input LAZ file: {input_file}")
    print(f"📁 Output TIF file: {output_file}")
    print(f"📏 Resolution: {resolution} units")
    print(f"🕐 Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Try JSON pipeline first, then fall back to hardcoded pipeline
    json_pipeline_path = os.path.join(os.path.dirname(__file__), "pipelines_json", "dsm.json")
    
    success = False
    message = ""
    
    # First try JSON pipeline
    if os.path.exists(json_pipeline_path):
        print(f"🔄 Attempting to use JSON pipeline: {json_pipeline_path}")
        try:
            # Load and adapt JSON pipeline
            with open(json_pipeline_path, 'r') as f:
                pipeline_config = json.load(f)
            
            # Replace placeholders with actual file paths
            pipeline_str = json.dumps(pipeline_config)
            pipeline_str = pipeline_str.replace("LEVEL2_24304A_20150414_S004/LEVEL2_24304A_20150414_S004.las", input_file)
            pipeline_str = pipeline_str.replace("dsm.tif", output_file)
            pipeline_str = pipeline_str.replace("0.5", str(resolution))
            pipeline_config = json.loads(pipeline_str)
            
            print(f"📋 Using JSON pipeline configuration")
            pipeline = pdal.Pipeline(json.dumps(pipeline_config))
            
            # Execute pipeline
            pipeline.execute()
            
            if os.path.exists(output_file):
                success = True
                message = f"DSM generated successfully using JSON pipeline: {output_file}"
                print(f"✅ {message}")
            else:
                raise Exception("Output file was not created")
                
        except Exception as e:
            print(f"⚠️ JSON pipeline failed: {str(e)}")
            print(f"🔄 Falling back to hardcoded pipeline...")
    
    # Fall back to hardcoded pipeline if JSON failed or doesn't exist
    if not success:
        try:
            print(f"🔄 Using hardcoded DSM pipeline...")
            pipeline_config = create_dsm_fallback_pipeline(input_file, output_file, resolution)
            pipeline = pdal.Pipeline(json.dumps(pipeline_config))
            
            # Execute pipeline
            pipeline.execute()
            
            if os.path.exists(output_file):
                success = True
                message = f"DSM generated successfully using hardcoded pipeline: {output_file}"
                print(f"✅ {message}")
            else:
                raise Exception("Output file was not created")
                
        except Exception as e:
            success = False
            message = f"Both JSON and hardcoded pipelines failed: {str(e)}"
            print(f"❌ {message}")
    
    # If processing succeeded, apply additional post-processing
    if success and os.path.exists(output_file):
        print(f"\n🔧 Applying post-processing...")
        
        # Run gdalinfo to get detailed information about the generated DSM
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
        
        # Note: DSM typically doesn't need FillNodata as much as DTM since it represents surface features
        print(f"🏗️ DSM processing complete - surface features preserved")
    
    return success, message


def validate_dsm_cache(dsm_path: str) -> bool:
    """
    Validate that a cached DSM file is properly formatted and not corrupted
    
    Args:
        dsm_path: Path to the DSM file to validate
        
    Returns:
        True if DSM is valid, False otherwise
    """
    try:
        from osgeo import gdal
        
        # Try to open the DSM file
        dataset = gdal.Open(dsm_path, gdal.GA_ReadOnly)
        if dataset is None:
            print(f"⚠️ DSM validation failed: Cannot open {dsm_path}")
            return False
        
        # Check basic properties
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        bands = dataset.RasterCount
        
        if width <= 0 or height <= 0 or bands != 1:
            print(f"⚠️ DSM validation failed: Invalid dimensions {width}x{height}, bands={bands}")
            dataset = None
            return False
        
        # Check that we can read the first band
        band = dataset.GetRasterBand(1)
        if band is None:
            print(f"⚠️ DSM validation failed: Cannot access raster band")
            dataset = None
            return False
        
        # Check data type
        data_type = band.DataType
        if data_type not in [gdal.GDT_Float32, gdal.GDT_Float64, gdal.GDT_Int16, gdal.GDT_Int32]:
            print(f"⚠️ DSM validation failed: Unexpected data type {data_type}")
            dataset = None
            return False
        
        # Clean up
        dataset = None
        return True
        
    except ImportError:
        print(f"⚠️ GDAL not available for DSM validation, assuming valid")
        return True
    except Exception as e:
        print(f"⚠️ DSM validation failed with error: {e}")
        return False


async def process_dsm(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process DSM analysis from LAZ file
    
    Args:
        laz_file_path: Path to the input LAZ file
        output_dir: Directory to save output files
        parameters: Processing parameters
    
    Returns:
        Dict containing processing results
    """
    start_time = time.time()
    
    print(f"\n{'='*50}")
    print(f"🚀 STARTING DSM PROCESSING")
    print(f"{'='*50}")
    print(f"📁 Input LAZ file: {laz_file_path}")
    print(f"📂 Output directory: {output_dir}")
    print(f"⚙️ Parameters: {parameters}")
    print(f"🕐 Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    logger.info(f"Starting DSM processing for {laz_file_path}")
    
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
        resolution = parameters.get("resolution", 1.0)
        
        print(f"⚙️ DSM parameters:")
        print(f"   📏 Resolution: {resolution}")
        
        logger.info(f"Processing with resolution={resolution}")
        
        # Call the main DSM function
        print(f"🔄 Processing DSM...")
        dsm_path = dsm(laz_file_path)
        
        processing_time = time.time() - start_time
        
        # Get output file size
        output_size = os.path.getsize(dsm_path) if os.path.exists(dsm_path) else 0
        
        print(f"✅ DSM PROCESSING COMPLETED")
        print(f"⏱️ Total processing time: {processing_time:.2f} seconds")
        print(f"📄 Output file: {dsm_path}")
        print(f"📊 Output size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
        print(f"{'='*50}\n")
        
        logger.info(f"DSM processing completed in {processing_time:.2f} seconds")
        logger.info(f"Output file created: {dsm_path}")
        
        return {
            "success": True,
            "message": "DSM processing completed successfully",
            "output_file": dsm_path,
            "processing_time": processing_time,
            "input_file": laz_file_path,
            "parameters_used": {
                "resolution": resolution
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
        
        logger.error(f"File not found error in DSM processing: {error_msg}")
        
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
        
        logger.error(f"Unexpected error in DSM processing: {error_msg}", exc_info=True)
        
        return {
            "success": False,
            "message": f"Processing failed: {error_msg}",
            "error_type": type(e).__name__,
            "processing_time": processing_time,
            "input_file": laz_file_path
        }
