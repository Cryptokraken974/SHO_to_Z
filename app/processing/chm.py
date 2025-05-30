import asyncio
import time
import os
import logging
import subprocess
from typing import Dict, Any
from osgeo import gdal
from osgeo_utils import gdal_calc
from .dtm import dtm
from .dsm import dsm

logger = logging.getLogger(__name__)

async def process_chm(laz_file_path: str, output_dir: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process CHM (Canopy Height Model) generation from LAZ file using DSM - DTM calculation
    
    Args:
        laz_file_path: Path to the input LAZ file
        output_dir: Directory to save the CHM output
        parameters: Processing parameters
        
    Returns:
        Dictionary with processing results
    """
    start_time = time.time()
    
    try:
        logger.info(f"🌳 Starting CHM processing for {laz_file_path}")
        
        # Use the main chm function for processing
        chm_path = chm(laz_file_path)
        
        processing_time = time.time() - start_time
        logger.info(f"✅ CHM processing completed in {processing_time:.2f} seconds")
        
        return {
            "success": True,
            "message": "CHM (Canopy Height Model) processing completed successfully",
            "processing_time": processing_time,
            "output_file": chm_path
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"CHM processing failed after {processing_time:.2f} seconds: {str(e)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "message": error_msg,
            "processing_time": processing_time,
            "error": str(e)
        }

def chm(input_file: str) -> str:
    """
    Generate CHM (Canopy Height Model) from LAZ file using DSM - DTM calculation
    CHM represents vegetation height by subtracting terrain from surface
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated CHM TIF file
    """
    print(f"\n🌳 CHM: Starting generation for {input_file}")
    start_time = time.time()
    
    # Extract the base name without path and extension
    laz_basename = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory structure: output/<laz_basename>/CHM/
    output_dir = os.path.join("output", laz_basename, "CHM")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <laz_basename>_CHM.tif
    output_filename = f"{laz_basename}_CHM.tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path}")
    
    # Check if CHM already exists and is up-to-date (caching optimization)
    if os.path.exists(output_path) and os.path.exists(input_file):
        try:
            # Compare modification times
            chm_mtime = os.path.getmtime(output_path)
            laz_mtime = os.path.getmtime(input_file)
            
            if chm_mtime > laz_mtime:
                # Validate the cached CHM file
                if validate_chm_cache(output_path):
                    processing_time = time.time() - start_time
                    print(f"🚀 CHM cache hit! Using existing CHM file (created {time.ctime(chm_mtime)})")
                    print(f"✅ CHM ready in {processing_time:.3f} seconds (cached)")
                    return output_path
                else:
                    print(f"⚠️ Cached CHM file failed validation, regenerating...")
            else:
                print(f"⏰ CHM file exists but is outdated. LAZ modified: {time.ctime(laz_mtime)}, CHM created: {time.ctime(chm_mtime)}")
        except OSError as e:
            print(f"⚠️ Error checking file timestamps: {e}")
    elif os.path.exists(output_path):
        print(f"⚠️ CHM exists but input LAZ file not found, regenerating CHM")
    else:
        print(f"📝 No existing CHM found, generating new CHM")
    
    try:
        # Step 1: Generate or locate DSM
        print(f"\n🏗️ Step 1: Generating DSM for CHM calculation...")
        dsm_path = dsm(input_file)
        print(f"✅ DSM ready: {dsm_path}")
        
        # Step 2: Generate or locate DTM
        print(f"\n🏔️ Step 2: Generating DTM for CHM calculation...")
        dtm_path = dtm(input_file)
        print(f"✅ DTM ready: {dtm_path}")
        
        # Step 3: Calculate CHM using gdal_calc (DSM - DTM)
        print(f"\n🌳 Step 3: Calculating CHM using gdal_calc (DSM - DTM)...")
        print(f"📁 DSM file: {dsm_path}")
        print(f"📁 DTM file: {dtm_path}")
        print(f"📁 Output CHM: {output_path}")
        
        # Ensure paths are absolute
        dsm_abs_path = os.path.abspath(dsm_path)
        dtm_abs_path = os.path.abspath(dtm_path)
        output_abs_path = os.path.abspath(output_path)
        
        # Verify input files exist and get their info
        if not os.path.exists(dsm_abs_path):
            raise FileNotFoundError(f"DSM file not found: {dsm_abs_path}")
        if not os.path.exists(dtm_abs_path):
            raise FileNotFoundError(f"DTM file not found: {dtm_abs_path}")
        
        # Check dimensions and spatial properties
        dsm_dataset = gdal.Open(dsm_abs_path, gdal.GA_ReadOnly)
        dtm_dataset = gdal.Open(dtm_abs_path, gdal.GA_ReadOnly)
        
        if dsm_dataset is None or dtm_dataset is None:
            raise RuntimeError("Failed to open DSM or DTM files")
        
        dsm_width, dsm_height = dsm_dataset.RasterXSize, dsm_dataset.RasterYSize
        dtm_width, dtm_height = dtm_dataset.RasterXSize, dtm_dataset.RasterYSize
        
        print(f"📐 DSM dimensions: {dsm_width} x {dsm_height}")
        print(f"📐 DTM dimensions: {dtm_width} x {dtm_height}")
        
        # Get geotransforms to check spatial alignment
        dsm_geotransform = dsm_dataset.GetGeoTransform()
        dtm_geotransform = dtm_dataset.GetGeoTransform()
        
        dsm_dataset = None
        dtm_dataset = None
        
        # Check if dimensions match
        if dsm_width != dtm_width or dsm_height != dtm_height:
            print(f"⚠️ Dimension mismatch detected!")
            print(f"   DSM: {dsm_width} x {dsm_height}")
            print(f"   DTM: {dtm_width} x {dtm_height}")
            print(f"🔧 Resampling DTM to match DSM extent...")
            
            # Create a resampled DTM that matches DSM extent
            resampled_dtm_path = dtm_abs_path.replace('.tif', '_resampled_for_chm.tif')
            
            # Use gdalwarp to resample DTM to match DSM
            resample_cmd = [
                "gdalwarp",
                "-tr", str(dsm_geotransform[1]), str(abs(dsm_geotransform[5])),  # Use DSM pixel size
                "-te", str(dsm_geotransform[0]),  # xmin
                       str(dsm_geotransform[3] + dsm_height * dsm_geotransform[5]),  # ymin  
                       str(dsm_geotransform[0] + dsm_width * dsm_geotransform[1]),   # xmax
                       str(dsm_geotransform[3]),  # ymax
                "-r", "bilinear",  # Resampling method
                "-of", "GTiff",
                "-overwrite",
                dtm_abs_path,
                resampled_dtm_path
            ]
            
            print(f"🔧 Running: {' '.join(resample_cmd)}")
            try:
                result = subprocess.run(resample_cmd, capture_output=True, text=True, check=True)
                if result.stdout:
                    print(f"📋 Resample output: {result.stdout.strip()}")
                
                # Update DTM path to use resampled version
                dtm_abs_path = resampled_dtm_path
                print(f"✅ DTM resampled successfully: {dtm_abs_path}")
                
            except subprocess.CalledProcessError as e:
                print(f"❌ DTM resampling failed: {e}")
                if e.stderr:
                    print(f"❌ Error: {e.stderr}")
                raise RuntimeError(f"Failed to resample DTM: {e}")
        else:
            print(f"✅ DSM and DTM dimensions match")
        
        print(f"📁 DSM absolute path: {dsm_abs_path}")
        print(f"📁 DTM absolute path: {dtm_abs_path}")
        print(f"📁 CHM absolute path: {output_abs_path}")
        
        # Use gdal_calc to calculate DSM - DTM
        print(f"⚙️ CHM calculation parameters:")
        print(f"   📊 Formula: DSM - DTM")
        print(f"   🚫 NoData value: -9999")
        print(f"   📏 Output type: Float32")
        
        calc_start = time.time()
        
        try:
            # Method 1: Try using gdal_calc Python API
            print(f"🔧 Attempting CHM calculation using gdal_calc.Calc()...")
            ds = gdal_calc.Calc(
                calc="A-B",
                A=dsm_abs_path,
                B=dtm_abs_path,
                outfile=output_abs_path,
                NoDataValue=-9999,
                type="Float32",
                format="GTiff",
                overwrite=True,
                quiet=False
            )
            
            calc_time = time.time() - calc_start
            
            if ds is None:
                raise RuntimeError("gdal_calc.Calc() returned None")
                
            # Close the dataset
            ds = None
            print(f"✅ CHM calculation completed using Python API in {calc_time:.2f} seconds")
            
        except Exception as api_error:
            print(f"⚠️ Python API failed: {str(api_error)}")
            print(f"🔄 Trying alternative method with command line gdal_calc.py...")
            
            # Method 2: Fallback to command line gdal_calc.py
            try:
                cmd = [
                    "gdal_calc.py",
                    "-A", dsm_abs_path,
                    "-B", dtm_abs_path,
                    "--outfile", output_abs_path,
                    "--calc", "A-B",
                    "--NoDataValue", "-9999",
                    "--type", "Float32",
                    "--format", "GTiff",
                    "--overwrite"
                ]
                
                print(f"🔧 Running command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                calc_time = time.time() - calc_start
                print(f"✅ CHM calculation completed using command line in {calc_time:.2f} seconds")
                
                if result.stdout:
                    print(f"📋 Command output: {result.stdout.strip()}")
                    
            except subprocess.CalledProcessError as cmd_error:
                print(f"❌ Command line gdal_calc.py also failed: {str(cmd_error)}")
                if cmd_error.stderr:
                    print(f"❌ Error output: {cmd_error.stderr}")
                raise RuntimeError(f"Both gdal_calc methods failed. API error: {api_error}, CMD error: {cmd_error}")
            except FileNotFoundError:
                print(f"❌ gdal_calc.py command not found in PATH")
                raise RuntimeError(f"gdal_calc.py not available and Python API failed: {api_error}")
        
        # Step 4: Validate output file
        print(f"\n🔍 Validating CHM output file...")
        if os.path.exists(output_abs_path):
            output_size = os.path.getsize(output_abs_path)
            print(f"✅ CHM file created successfully")
            print(f"📊 CHM file size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
            print(f"📄 CHM file path: {output_abs_path}")
            
            # Get CHM statistics
            print(f"\n📊 CHM Statistics:")
            try:
                chm_dataset = gdal.Open(output_abs_path, gdal.GA_ReadOnly)
                if chm_dataset:
                    band = chm_dataset.GetRasterBand(1)
                    stats = band.GetStatistics(False, True)  # Force calculation
                    min_height, max_height = stats[0], stats[1]
                    mean_height, std_height = stats[2], stats[3]
                    
                    print(f"   📏 Min height: {min_height:.2f}m")
                    print(f"   📏 Max height: {max_height:.2f}m") 
                    print(f"   📏 Mean height: {mean_height:.2f}m")
                    print(f"   📏 Std deviation: {std_height:.2f}m")
                    print(f"   📐 Height range: {max_height - min_height:.2f}m")
                    
                    # Check for reasonable CHM values
                    if max_height > 100:
                        print(f"⚠️ Warning: Maximum height ({max_height:.2f}m) seems unusually high")
                    if min_height < -10:
                        print(f"⚠️ Warning: Minimum height ({min_height:.2f}m) seems unusually low")
                    
                    chm_dataset = None
                else:
                    print(f"⚠️ Could not open CHM file for statistics")
            except Exception as e:
                print(f"⚠️ Error getting CHM statistics: {e}")
        else:
            raise RuntimeError(f"CHM file was not created: {output_path}")
        
        total_time = time.time() - start_time
        print(f"\n✅ CHM generation completed successfully in {total_time:.2f} seconds")
        print(f"🌳 CHM represents vegetation/structure height above ground")
        print(f"📊 Values: Positive=above ground, Zero=ground level, Negative=below DTM")
        
        return output_path
        
    except Exception as e:
        total_time = time.time() - start_time
        print(f"❌ CHM generation failed after {total_time:.2f} seconds")
        print(f"❌ Error: {str(e)}")
        raise Exception(f"CHM generation failed: {str(e)}")

def validate_chm_cache(chm_path: str) -> bool:
    """
    Validate that a cached CHM file is properly formatted and not corrupted
    
    Args:
        chm_path: Path to the CHM file to validate
        
    Returns:
        True if CHM is valid, False otherwise
    """
    try:
        from osgeo import gdal
        
        # Try to open the CHM file
        dataset = gdal.Open(chm_path, gdal.GA_ReadOnly)
        if dataset is None:
            print(f"⚠️ CHM validation failed: Cannot open {chm_path}")
            return False
        
        # Check basic properties
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        bands = dataset.RasterCount
        
        if width <= 0 or height <= 0 or bands != 1:
            print(f"⚠️ CHM validation failed: Invalid dimensions {width}x{height}, bands={bands}")
            dataset = None
            return False
        
        # Check that we can read the first band
        band = dataset.GetRasterBand(1)
        if band is None:
            print(f"⚠️ CHM validation failed: Cannot access raster band")
            dataset = None
            return False
        
        # Check data type
        data_type = band.DataType
        if data_type not in [gdal.GDT_Float32, gdal.GDT_Float64, gdal.GDT_Int16, gdal.GDT_Int32]:
            print(f"⚠️ CHM validation failed: Unexpected data type {data_type}")
            dataset = None
            return False
        
        # Clean up
        dataset = None
        return True
        
    except ImportError:
        print(f"⚠️ GDAL not available for CHM validation, assuming valid")
        return True
    except Exception as e:
        print(f"⚠️ CHM validation failed with error: {e}")
        return False

def clear_chm_cache(input_file: str = None) -> None:
    """
    Clear CHM cache files
    
    Args:
        input_file: If provided, clear cache only for this specific file.
                   If None, clear all CHM cache files.
    """
    import glob
    
    if input_file:
        # Clear cache for specific file
        laz_basename = os.path.splitext(os.path.basename(input_file))[0]
        chm_pattern = f"output/{laz_basename}/CHM/*_CHM.tif"
        chm_files = glob.glob(chm_pattern)
        print(f"🗑️ Clearing CHM cache for {input_file}")
    else:
        # Clear all CHM cache files
        chm_files = glob.glob("output/*/CHM/*_CHM.tif")
        print(f"🗑️ Clearing all CHM cache files")
    
    if chm_files:
        cleared_count = 0
        for chm_file in chm_files:
            try:
                os.remove(chm_file)
                cleared_count += 1
            except OSError as e:
                print(f"⚠️ Failed to remove {chm_file}: {e}")
        
        print(f"🗑️ Cleared {cleared_count} CHM cache files")
    else:
        print(f"📭 No CHM cache files found to clear")

def get_chm_cache_info() -> dict:
    """
    Get information about current CHM cache status
    
    Returns:
        Dictionary with cache statistics
    """
    import glob
    
    chm_files = glob.glob("output/*/CHM/*_CHM.tif")
    
    cache_info = {
        "total_cached_chms": len(chm_files),
        "cached_files": []
    }
    
    total_size = 0
    for chm_file in chm_files:
        try:
            file_stat = os.stat(chm_file)
            size_mb = file_stat.st_size / (1024 * 1024)
            total_size += size_mb
            
            cache_info["cached_files"].append({
                "file": chm_file,
                "size_mb": round(size_mb, 2),
                "created": time.ctime(file_stat.st_mtime)
            })
        except OSError:
            continue
    
    cache_info["total_size_mb"] = round(total_size, 2)
    
    return cache_info
