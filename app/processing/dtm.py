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


def fill_nodata_enhanced(input_path, output_path, max_distance=15, smoothing_iter=2):
    """
    Optimized FillNodata using CreateCopy for better performance and proper error handling.
    
    Args:
        input_path: Path to input GeoTIFF with NoData areas
        output_path: Path for output filled GeoTIFF
        max_distance: Max search distance for interpolation (pixels)
        smoothing_iter: Number of 3x3 smoothing iterations (0-20)
    """
    from osgeo import gdal
    import numpy as np
    
    # Enable GDAL exceptions for better error handling
    gdal.UseExceptions()
    
    print(f"🔧 Optimized FillNodata processing:")
    print(f"   📁 Input: {input_path}")
    print(f"   📁 Output: {output_path}")
    print(f"   🎯 Max distance: {max_distance} pixels")
    print(f"   🌊 Smoothing iterations: {smoothing_iter}")
    
    try:
        # Open input dataset
        input_ds = gdal.Open(input_path, gdal.GA_ReadOnly)
        if input_ds is None:
            raise RuntimeError(f"Cannot open input file: {input_path}")
        
        # Get initial statistics and diagnostics
        input_band = input_ds.GetRasterBand(1)
        nodata_value = input_band.GetNoDataValue()
        print(f"   📊 NoData value: {nodata_value}")
        
        # Get statistics before filling
        stats_before = input_band.GetStatistics(True, True)
        print(f"   📈 Before filling - Min: {stats_before[0]:.2f}, Max: {stats_before[1]:.2f}")
        
        # Count missing pixels for diagnostics
        data_array = input_band.ReadAsArray()
        if nodata_value is not None:
            missing_pixels = np.sum(data_array == nodata_value)
        else:
            missing_pixels = np.sum(np.isnan(data_array))
        print(f"   🕳️ Missing pixels to fill: {missing_pixels:,}")
        
        if missing_pixels == 0:
            print(f"   ✅ No missing pixels found, skipping FillNodata")
            # Still create output copy for consistency
            driver = gdal.GetDriverByName('GTiff')
            output_ds = driver.CreateCopy(output_path, input_ds, options=['COMPRESS=LZW', 'TILED=YES'])
            output_ds.FlushCache()
            output_ds = None
            input_ds = None
            return
        
        # Use efficient CreateCopy approach (most efficient GDAL operation)
        driver = gdal.GetDriverByName('GTiff')
        output_ds = driver.CreateCopy(
            output_path, 
            input_ds, 
            options=['COMPRESS=LZW', 'TILED=YES', 'PREDICTOR=2']
        )
        if output_ds is None:
            raise RuntimeError(f"Cannot create output file: {output_path}")
        
        # Get output band for processing
        output_band = output_ds.GetRasterBand(1)
        
        # Perform FillNodata operation
        print(f"   🔄 Performing FillNodata interpolation...")
        fillnodata_start = time.time()
        
        result = gdal.FillNodata(
            targetBand=output_band,
            maskBand=None,  # Use nodata values as mask automatically
            maxSearchDist=max_distance,
            smoothingIterations=smoothing_iter
        )
        
        fillnodata_time = time.time() - fillnodata_start
        
        if result != gdal.CE_None:
            raise RuntimeError(f"FillNodata failed with error code: {result}")
        
        # Force write to disk
        output_ds.FlushCache()
        
        # Get statistics after filling for validation
        stats_after = output_band.GetStatistics(True, True)
        print(f"   📈 After filling - Min: {stats_after[0]:.2f}, Max: {stats_after[1]:.2f}")
        
        # Count remaining missing pixels for progress report
        filled_data = output_band.ReadAsArray()
        if nodata_value is not None:
            remaining_missing = np.sum(filled_data == nodata_value)
        else:
            remaining_missing = np.sum(np.isnan(filled_data))
        
        filled_pixels = missing_pixels - remaining_missing
        fill_percentage = (filled_pixels / missing_pixels * 100) if missing_pixels > 0 else 0
        
        print(f"   ✨ Filled {filled_pixels:,} pixels ({fill_percentage:.1f}%)")
        print(f"   📊 Remaining missing: {remaining_missing:,} pixels")
        print(f"   ✅ Optimized FillNodata completed in {fillnodata_time:.2f} seconds")
        
        # Proper cleanup
        output_band = None
        output_ds = None
        input_ds = None
        
        print(f"   💾 Output saved: {output_path}")
        
    except Exception as e:
        print(f"   ❌ FillNodata failed: {str(e)}")
        # Cleanup on failure
        try:
            if 'output_ds' in locals() and output_ds is not None:
                output_ds = None
            if 'input_ds' in locals() and input_ds is not None:
                input_ds = None
        except:
            pass
        raise e


def create_dtm_fallback_pipeline(input_file: str, output_file: str, resolution: float = 1.0) -> Dict[str, Any]:
    """
    Create fallback DTM pipeline when JSON pipeline is not available
    """
    return {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": input_file
            },
            {
                "type": "filters.range",
                "limits": "Classification[2:2]"  # Ground points only
            },
            {
                "type": "writers.gdal",
                "filename": output_file,
                "resolution": resolution,
                "output_type": "mean",
                "nodata": -9999
            }
        ]
    }


def dtm(input_file: str, region_name: str = None) -> str:
    """
    Convert LAZ file to DTM (Digital Terrain Model) - Ground points only
    Implements caching to avoid regenerating DTM if it already exists and is up-to-date
    
    Args:
        input_file: Path to the input LAZ file
        region_name: The region name to use for the output directory (if None, uses LAZ filename)
        
    Returns:
        Path to the generated TIF file
    """
    print(f"\n🏔️ DTM: Starting conversion for {input_file}")
    start_time = time.time()
    
    # Check if input file exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input LAZ file not found: {input_file}")
    
    # Check if input file is readable
    if not os.access(input_file, os.R_OK):
        raise PermissionError(f"Input LAZ file is not readable: {input_file}")
    
    # Extract filename from the file path structure
    input_path = Path(input_file)
    file_stem = input_path.stem  # Get filename without extension (e.g., "OR_WizardIsland")
    
    # Use provided region_name for output directory if available, otherwise use LAZ filename
    output_folder_name = region_name if region_name else file_stem
    print(f"📁 Using output folder name: {output_folder_name} (from region_name: {region_name})")
    
    # Create output directory structure: output/<output_folder_name>/lidar/DTM/
    output_dir = os.path.join("output", output_folder_name, "lidar", "DTM")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <file_stem>_DTM.tif
    output_filename = f"{file_stem}_DTM.tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path}")
    
    # Check if DTM already exists and is up-to-date (caching optimization)
    if os.path.exists(output_path) and os.path.exists(input_file):
        try:
            # Compare modification times
            dtm_mtime = os.path.getmtime(output_path)
            laz_mtime = os.path.getmtime(input_file)
            
            if dtm_mtime > laz_mtime:
                # Validate the cached DTM file
                if validate_dtm_cache(output_path):
                    processing_time = time.time() - start_time
                    print(f"🚀 DTM cache hit! Using existing DTM file (created {time.ctime(dtm_mtime)})")
                    print(f"✅ DTM ready in {processing_time:.3f} seconds (cached)")
                    return output_path
                else:
                    print(f"⚠️ Cached DTM file failed validation, regenerating...")
            else:
                print(f"⏰ DTM file exists but is outdated. LAZ modified: {time.ctime(laz_mtime)}, DTM created: {time.ctime(dtm_mtime)}")
        except OSError as e:
            print(f"⚠️ Error checking file timestamps: {e}")
    elif os.path.exists(output_path):
        print(f"⚠️ DTM exists but input LAZ file not found, regenerating DTM")
    else:
        print(f"📝 No existing DTM found, generating new DTM")
    
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
    
    # Try JSON pipeline first, then fall back to hardcoded pipeline
    json_pipeline_path = os.path.join(os.path.dirname(__file__), "pipelines_json", "dtm.json")
    
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
            pipeline_str = pipeline_str.replace("input/default.laz", input_file)
            pipeline_str = pipeline_str.replace("output/default_DTM.tif", output_file)
            pipeline_str = pipeline_str.replace("2.0", str(resolution))
            pipeline_config = json.loads(pipeline_str)
            
            print(f"📋 Using JSON pipeline configuration")
            
            # Create temporary pipeline file for subprocess execution with timeout
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(pipeline_config, temp_file, indent=2)
                temp_pipeline_path = temp_file.name
            
            try:
                # Execute PDAL pipeline with timeout using subprocess
                print(f"🔄 Executing PDAL pipeline with 300 second timeout...")
                start_time = time.time()
                
                result = subprocess.run(
                    ['pdal', 'pipeline', temp_pipeline_path],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                execution_time = time.time() - start_time
                print(f"⏱️ PDAL execution completed in {execution_time:.2f} seconds")
                
                if result.returncode == 0:
                    if os.path.exists(output_file):
                        success = True
                        message = f"DTM generated successfully using JSON pipeline: {output_file}"
                        print(f"✅ {message}")
                    else:
                        raise Exception("Output file was not created")
                else:
                    raise Exception(f"PDAL failed with return code {result.returncode}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ PDAL pipeline timed out after 300 seconds")
                raise Exception("PDAL pipeline execution timed out")
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_pipeline_path)
                except:
                    pass
            
            if os.path.exists(output_file):
                success = True
                message = f"DTM generated successfully using JSON pipeline: {output_file}"
                print(f"✅ {message}")
            else:
                raise Exception("Output file was not created")
                
        except Exception as e:
            print(f"⚠️ JSON pipeline failed: {str(e)}")
            print(f"🔄 Falling back to hardcoded pipeline...")
    
    # Fall back to hardcoded pipeline if JSON failed or doesn't exist
    if not success:
        try:
            print(f"🔄 Using hardcoded DTM pipeline...")
            pipeline_config = create_dtm_fallback_pipeline(input_file, output_file, resolution)
            
            # Create temporary pipeline file for subprocess execution with timeout
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(pipeline_config, temp_file, indent=2)
                temp_pipeline_path = temp_file.name
            
            try:
                # Execute PDAL pipeline with timeout using subprocess
                print(f"🔄 Executing fallback PDAL pipeline with 300 second timeout...")
                start_time = time.time()
                
                result = subprocess.run(
                    ['pdal', 'pipeline', temp_pipeline_path],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                execution_time = time.time() - start_time
                print(f"⏱️ Fallback PDAL execution completed in {execution_time:.2f} seconds")
                
                if result.returncode == 0:
                    if os.path.exists(output_file):
                        success = True
                        message = f"DTM generated successfully using hardcoded pipeline: {output_file}"
                        print(f"✅ {message}")
                    else:
                        raise Exception("Output file was not created")
                else:
                    raise Exception(f"PDAL failed with return code {result.returncode}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ Fallback PDAL pipeline also timed out after 300 seconds")
                raise Exception("Both JSON and fallback PDAL pipelines timed out")
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_pipeline_path)
                except:
                    pass
                
        except Exception as e:
            success = False
            message = f"Both JSON and hardcoded pipelines failed: {str(e)}"
            print(f"❌ {message}")
    
    # If processing succeeded, apply additional post-processing
    if success and os.path.exists(output_file):
        print(f"\n🔧 Applying post-processing...")
        
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
        
        # Apply GDAL FillNodata to interpolate gaps in the DTM
        print(f"\n🔧 Applying GDAL FillNodata interpolation...")
        try:
            from osgeo import gdal
            
            # Apply our enhanced fill_nodata function
            filled_output_path = output_file.replace('.tif', '_filled.tif')
            fill_nodata_enhanced(output_file, filled_output_path, max_distance=100, smoothing_iter=2)
            
            # Replace original with filled version
            import shutil
            shutil.move(filled_output_path, output_file)
            print(f"✅ Enhanced FillNodata processing completed successfully")
                
        except ImportError:
            print(f"⚠️ GDAL Python bindings not available. Skipping FillNodata step.")
        except Exception as e:
            print(f"⚠️ Error during FillNodata processing: {str(e)}")
            # Fallback to original method if enhanced fails
            try:
                dataset = gdal.Open(output_file, gdal.GA_Update)
                if dataset is not None:
                    band = dataset.GetRasterBand(1)
                    mask_band = None
                    
                    print(f"   🔄 Falling back to basic FillNodata...")
                    print(f"   🎯 Max distance: 100 pixels")
                    print(f"   🌊 Smooth iterations: 2")
                    
                    fillnodata_start = time.time()
                    result = gdal.FillNodata(band, mask_band, maxSearchDist=100, smoothingIterations=2)
                    fillnodata_time = time.time() - fillnodata_start
                    
                    if result == 0:
                        print(f"✅ Basic FillNodata completed in {fillnodata_time:.2f} seconds")
                    else:
                        print(f"⚠️ Basic FillNodata returned error code: {result}")
                    
                    dataset = None
            except Exception as fallback_e:
                print(f"⚠️ Fallback FillNodata also failed: {str(fallback_e)}")
    
    return success, message


def clear_dtm_cache(input_file: str = None) -> None:
    """
    Clear DTM cache for a specific LAZ file or all DTM files
    
    Args:
        input_file: Path to specific LAZ file to clear cache for, or None to clear all
    """
    if input_file:
        # Clear cache for specific file
        input_path = Path(input_file)
        if "lidar" in input_path.parts:
            region_name = input_path.parts[input_path.parts.index("input") + 1]
        else:
            region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(input_file))[0]
        
        dtm_path = os.path.join("output", region_name, "DTM", f"{region_name}_DTM.tif")
        
        if os.path.exists(dtm_path):
            try:
                os.remove(dtm_path)
                print(f"🗑️ Cleared DTM cache for {region_name}")
            except OSError as e:
                print(f"⚠️ Failed to clear DTM cache: {e}")
        else:
            print(f"📭 No DTM cache found for {region_name}")
    else:
        # Clear all DTM caches
        import glob
        dtm_files = glob.glob("output/*/DTM/*_DTM.tif")
        
        cleared_count = 0
        for dtm_file in dtm_files:
            try:
                os.remove(dtm_file)
                cleared_count += 1
            except OSError as e:
                print(f"⚠️ Failed to remove {dtm_file}: {e}")
        
        print(f"🗑️ Cleared {cleared_count} DTM cache files")


def get_dtm_cache_info() -> dict:
    """
    Get information about current DTM cache status
    
    Returns:
        Dictionary with cache statistics
    """
    import glob
    
    dtm_files = glob.glob("output/*/DTM/*_DTM.tif")
    
    cache_info = {
        "total_cached_dtms": len(dtm_files),
        "cached_files": []
    }
    
    total_size = 0
    for dtm_file in dtm_files:
        try:
            file_stat = os.stat(dtm_file)
            size_mb = file_stat.st_size / (1024 * 1024)
            total_size += size_mb
            
            cache_info["cached_files"].append({
                "file": dtm_file,
                "size_mb": round(size_mb, 2),
                "created": time.ctime(file_stat.st_mtime)
            })
        except OSError:
            continue
    
    cache_info["total_size_mb"] = round(total_size, 2)
    
    return cache_info


def validate_dtm_cache(dtm_path: str) -> bool:
    """
    Validate that a cached DTM file is properly formatted and not corrupted
    
    Args:
        dtm_path: Path to the DTM file to validate
        
    Returns:
        True if DTM is valid, False otherwise
    """
    try:
        from osgeo import gdal
        
        # Try to open the DTM file
        dataset = gdal.Open(dtm_path, gdal.GA_ReadOnly)
        if dataset is None:
            print(f"⚠️ DTM validation failed: Cannot open {dtm_path}")
            return False
        
        # Check basic properties
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        bands = dataset.RasterCount
        
        if width <= 0 or height <= 0 or bands != 1:
            print(f"⚠️ DTM validation failed: Invalid dimensions {width}x{height}, bands={bands}")
            dataset = None
            return False
        
        # Check that we can read the first band
        band = dataset.GetRasterBand(1)
        if band is None:
            print(f"⚠️ DTM validation failed: Cannot access raster band")
            dataset = None
            return False
        
        # Check data type
        data_type = band.DataType
        if data_type not in [gdal.GDT_Float32, gdal.GDT_Float64, gdal.GDT_Int16, gdal.GDT_Int32]:
            print(f"⚠️ DTM validation failed: Unexpected data type {data_type}")
            dataset = None
            return False
        
        # Clean up
        dataset = None
        return True
        
    except ImportError:
        print(f"⚠️ GDAL not available for DTM validation, assuming valid")
        return True
    except Exception as e:
        print(f"⚠️ DTM validation failed with error: {e}")
        return False


def get_cache_statistics() -> str:
    """
    Generate a formatted report of DTM cache performance and usage
    
    Returns:
        Formatted string with cache statistics
    """
    cache_info = get_dtm_cache_info()
    
    report = []
    report.append("📊 DTM CACHE STATISTICS")
    report.append("=" * 50)
    report.append(f"🗂️ Total cached DTMs: {cache_info['total_cached_dtms']}")
    report.append(f"💾 Total cache size: {cache_info['total_size_mb']} MB")
    
    if cache_info['cached_files']:
        report.append("\n📁 Cached Files:")
        for i, file_info in enumerate(cache_info['cached_files'], 1):
            basename = os.path.basename(file_info['file'])
            report.append(f"   {i}. {basename}")
            report.append(f"      Size: {file_info['size_mb']} MB")
            report.append(f"      Created: {file_info['created']}")
    else:
        report.append("\n📭 No DTM files currently cached")
    
    # Calculate potential time savings
    if cache_info['total_cached_dtms'] > 0:
        # Estimate: each DTM would take ~20 seconds to generate
        estimated_savings = (cache_info['total_cached_dtms'] - 1) * 20
        report.append(f"\n⚡ Estimated time saved by caching: {estimated_savings} seconds")
        report.append(f"🚀 Performance improvement: ~{cache_info['total_cached_dtms']}x faster for repeated operations")
    
    return "\n".join(report)


async def process_dtm(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process DTM (Digital Terrain Model) from LAZ file with comprehensive logging
    
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
    print(f"🏔️ DTM PROCESSING STARTING")
    print(f"{'='*60}")
    print(f"📁 Input LAZ file: {laz_file_path}")
    print(f"📂 Output directory: {output_dir}")
    print(f"⚙️ Parameters: {parameters}")
    print(f"🕐 Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    logger.info(f"Starting DTM processing for {laz_file_path}")
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
        
        # Extract region name and filename from the LAZ file path
        input_path = Path(laz_file_path)
        file_stem = input_path.stem  # Get filename without extension (e.g., "OR_WizardIsland")
        
        if "lidar" in input_path.parts:
            region_name = input_path.parts[input_path.parts.index("input") + 1]
        else:
            region_name = input_path.parent.name if input_path.parent.name != "input" else file_stem
        
        print(f"🗺️ [REGION DETECTION] Extracted region name: {region_name}")
        print(f"📄 [FILE DETECTION] Extracted file stem: {file_stem}")
        
        # Generate DTM using the synchronous function
        print(f"🔄 [DTM GENERATION] Calling DTM conversion...")
        dtm_start_time = time.time()
        
        try:
            # Run the DTM generation in a thread pool to keep it async
            loop = asyncio.get_event_loop()
            dtm_output_path = await loop.run_in_executor(None, dtm, laz_file_path)
            
            dtm_processing_time = time.time() - dtm_start_time
            print(f"✅ [DTM GENERATED] DTM conversion completed in {dtm_processing_time:.2f} seconds")
            print(f"   📄 DTM output file: {dtm_output_path}")
            
            # Verify the output file exists
            if not os.path.exists(dtm_output_path):
                raise FileNotFoundError(f"DTM output file not found: {dtm_output_path}")
            
            # Get file size
            file_size = os.path.getsize(dtm_output_path)
            file_size_mb = file_size / (1024 * 1024)
            print(f"   📊 File size: {file_size_mb:.2f} MB")
            
            # Copy to specified output directory if different
            output_filename = f"{file_stem}_DTM.tif"
            final_output_path = os.path.join(output_dir, output_filename)
            
            if dtm_output_path != final_output_path:
                print(f"📋 [FILE COPY] Copying DTM to specified output directory...")
                print(f"   📁 From: {dtm_output_path}")
                print(f"   📁 To: {final_output_path}")
                
                import shutil
                shutil.copy2(dtm_output_path, final_output_path)
                
                if os.path.exists(final_output_path):
                    print(f"   ✅ DTM copied successfully")
                else:
                    raise FileNotFoundError(f"Failed to copy DTM to {final_output_path}")
            else:
                final_output_path = dtm_output_path
                print(f"   ℹ️ DTM already in correct location")
            
            # Calculate total processing time
            total_time = time.time() - start_time
            
            # Log completion
            print(f"\n{'='*60}")
            print(f"✅ DTM PROCESSING COMPLETED")
            print(f"{'='*60}")
            print(f"⏱️ Total processing time: {total_time:.2f} seconds")
            print(f"📄 Final output: {final_output_path}")
            print(f"🕐 End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            logger.info(f"DTM processing completed successfully in {total_time:.2f} seconds")
            logger.info(f"Output file: {final_output_path}")
            
            return {
                "success": True,
                "output_file": final_output_path,
                "processing_time": total_time,
                "dtm_time": dtm_processing_time,
                "region_name": region_name,
                "file_size_mb": file_size_mb,
                "message": f"DTM processed successfully in {total_time:.2f} seconds"
            }
            
        except Exception as e:
            print(f"❌ [DTM ERROR] DTM generation failed: {str(e)}")
            logger.error(f"DTM generation failed: {str(e)}")
            raise
            
    except Exception as e:
        total_time = time.time() - start_time
        error_msg = f"DTM processing failed: {str(e)}"
        
        print(f"\n{'='*60}")
        print(f"❌ DTM PROCESSING FAILED")
        print(f"{'='*60}")
        print(f"⏱️ Time before failure: {total_time:.2f} seconds")
        print(f"❌ Error: {error_msg}")
        print(f"🕐 Failure time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.error(f"DTM processing failed after {total_time:.2f} seconds: {str(e)}")
        
        return {
            "success": False,
            "error": error_msg,
            "processing_time": total_time,
            "message": f"DTM processing failed after {total_time:.2f} seconds"
        }
