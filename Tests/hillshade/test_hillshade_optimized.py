#!/usr/bin/env python3
"""
Optimized Standalone Hillshade Test for FoxIsland.laz

This enhanced version addresses the missing pixels issue by:
1. Testing different DTM generation parameters
2. Adding FillNodata processing to reduce gaps
3. Comparing multiple approaches for optimal quality

This test doesn't depend on any app modules and runs completely standalone.
"""

import os
import sys
import time
import json
import subprocess
import tempfile
from pathlib import Path
from osgeo import gdal

# Enable GDAL exceptions
gdal.UseExceptions()

# Test Configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_LAZ_PATH = os.path.join(BASE_DIR, "input", "LAZ", "FoxIsland.laz")
DTM_PIPELINE_PATH = os.path.join(BASE_DIR, "app", "processing", "pipelines_json", "dtm.json")

# Output paths
TEST_OUTPUT_DIR = os.path.join(BASE_DIR, "Tests", "hillshade", "outputs")
DTM_ORIGINAL_PATH = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_DTM_original.tif")
DTM_OPTIMIZED_PATH = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_DTM_optimized.tif")
DTM_FILLED_PATH = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_DTM_filled.tif")
HILLSHADE_OPTIMIZED_PATH = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_Hillshade_optimized.tif")
PNG_OPTIMIZED_PATH = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_Hillshade_optimized.png")

def setup_test_environment():
    """Setup the test environment and directories."""
    print(f"🏗️ Setting up optimized test environment")
    print(f"📁 Base directory: {BASE_DIR}")
    print(f"📁 Test output directory: {TEST_OUTPUT_DIR}")
    
    # Create output directory
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    
    # Verify input file exists
    if not os.path.exists(INPUT_LAZ_PATH):
        raise FileNotFoundError(f"Input LAZ file not found: {INPUT_LAZ_PATH}")
    
    file_size = os.path.getsize(INPUT_LAZ_PATH)
    print(f"✅ Input LAZ file found: {os.path.basename(INPUT_LAZ_PATH)} ({file_size:,} bytes)")
    
    # Verify DTM pipeline exists
    if not os.path.exists(DTM_PIPELINE_PATH):
        raise FileNotFoundError(f"DTM pipeline not found: {DTM_PIPELINE_PATH}")
    
    print(f"✅ DTM pipeline found: {os.path.basename(DTM_PIPELINE_PATH)}")

def run_command(cmd, description, cwd=None):
    """Run a command and return success status and output."""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            cwd=cwd
        )
        duration = time.time() - start_time
        print(f"✅ {description} completed in {duration:.2f} seconds")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"❌ {description} failed after {duration:.2f} seconds")
        print(f"Error: {e.stderr}")
        return False, e.stderr

def create_optimized_dtm_pipeline():
    """Create an optimized DTM pipeline to reduce missing pixels."""
    print(f"\n📋 Creating optimized DTM pipeline")
    
    # Load original pipeline
    with open(DTM_PIPELINE_PATH, 'r') as f:
        pipeline_content = f.read()
    
    # Remove comments
    lines = pipeline_content.split('\n')
    clean_lines = [line for line in lines if not line.strip().startswith('//')]
    clean_content = '\n'.join(clean_lines)
    
    pipeline = json.loads(clean_content)
    
    # Create optimized pipeline with better gap filling
    optimized_pipeline = {
        "pipeline": [
            INPUT_LAZ_PATH,
            {
                "type": "filters.outlier",
                "method": "statistical",
                "multiplier": 2.5,  # Less aggressive outlier removal
                "mean_k": 12  # More neighbors for better stats
            },
            {
                "type": "filters.range",
                "limits": "Classification![135:146],Z[-10:3000]"
            },
            {
                "type": "filters.range",
                "limits": "Classification[2:2]"  # Ground points only
            },
            {
                "type": "writers.gdal",
                "filename": DTM_OPTIMIZED_PATH,
                "resolution": 1.0,  # High resolution
                "output_type": "mean",  # Use mean instead of min for better interpolation
                "window_size": 3,  # Larger window for better interpolation
                "nodata": -9999,
                "gdaldriver": "GTiff",
                "gdalopts": [
                    "COMPRESS=LZW",
                    "TILED=YES",
                    "PREDICTOR=2"
                ]
            }
        ]
    }
    
    print(f"✅ Optimized pipeline created")
    print(f"   📥 Input: {os.path.basename(INPUT_LAZ_PATH)}")
    print(f"   📤 Output: {os.path.basename(DTM_OPTIMIZED_PATH)}")
    print(f"   ⚙️ Optimizations: mean output, larger window, less aggressive outlier removal")
    
    return optimized_pipeline

def generate_optimized_dtm(pipeline):
    """Generate optimized DTM using PDAL."""
    print(f"\n🏔️ Generating optimized DTM using PDAL")
    
    # Create temporary pipeline file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        json.dump(pipeline, temp_file, indent=2)
        temp_pipeline_path = temp_file.name
    
    try:
        # Run PDAL pipeline
        cmd = ["pdal", "pipeline", temp_pipeline_path]
        success, output = run_command(cmd, "PDAL optimized DTM generation")
        
        if success and os.path.exists(DTM_OPTIMIZED_PATH):
            file_size = os.path.getsize(DTM_OPTIMIZED_PATH)
            print(f"✅ Optimized DTM generated: {os.path.basename(DTM_OPTIMIZED_PATH)} ({file_size:,} bytes)")
            return True
        else:
            print(f"❌ Optimized DTM generation failed")
            return False
    
    finally:
        # Clean up temporary pipeline file
        if os.path.exists(temp_pipeline_path):
            os.unlink(temp_pipeline_path)

def fill_nodata_gaps(input_path, output_path, max_distance=10):
    """Fill NoData gaps using GDAL's FillNodata algorithm."""
    print(f"\n🔧 Filling NoData gaps")
    print(f"   📥 Input: {os.path.basename(input_path)}")
    print(f"   📤 Output: {os.path.basename(output_path)}")
    print(f"   ⚙️ Max distance: {max_distance} pixels")
    
    try:
        # Open input raster
        src_ds = gdal.Open(input_path, gdal.GA_ReadOnly)
        if src_ds is None:
            raise RuntimeError(f"Cannot open input raster: {input_path}")
        
        # Create output raster (copy of input)
        driver = gdal.GetDriverByName('GTiff')
        dst_ds = driver.CreateCopy(output_path, src_ds, options=[
            "COMPRESS=LZW",
            "TILED=YES",
            "PREDICTOR=2"
        ])
        
        if dst_ds is None:
            raise RuntimeError(f"Cannot create output raster: {output_path}")
        
        # Get the band to process
        src_band = src_ds.GetRasterBand(1)
        dst_band = dst_ds.GetRasterBand(1)
        
        # Create mask band (areas to fill)
        mask_array = src_band.ReadAsArray()
        import numpy as np
        mask_band = None
        
        # Apply FillNodata algorithm
        start_time = time.time()
        result = gdal.FillNodata(
            targetBand=dst_band,
            maskBand=mask_band,
            maxSearchDist=max_distance,
            smoothingIterations=2
        )
        
        duration = time.time() - start_time
        
        if result == gdal.CE_None:
            file_size = os.path.getsize(output_path)
            print(f"✅ Gap filling completed in {duration:.2f} seconds")
            print(f"   💾 Output size: {file_size:,} bytes")
            
            # Close datasets
            dst_ds = None
            src_ds = None
            return True
        else:
            print(f"❌ Gap filling failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in gap filling: {e}")
        return False
    finally:
        # Ensure datasets are closed
        if 'dst_ds' in locals() and dst_ds is not None:
            dst_ds = None
        if 'src_ds' in locals() and src_ds is not None:
            src_ds = None

def get_raster_info(raster_path, name="Raster"):
    """Get comprehensive information about a raster file."""
    print(f"\n📊 Analyzing {name}: {os.path.basename(raster_path)}")
    
    try:
        dataset = gdal.Open(raster_path, gdal.GA_ReadOnly)
        if dataset is None:
            raise RuntimeError(f"Cannot open raster: {raster_path}")
        
        # Get basic properties
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        bands = dataset.RasterCount
        
        # Get geospatial information
        geotransform = dataset.GetGeoTransform()
        projection = dataset.GetProjection()
        
        # Get band statistics
        band = dataset.GetRasterBand(1)
        nodata_value = band.GetNoDataValue()
        
        # Calculate statistics
        band.ComputeStatistics(False)
        min_val, max_val, mean_val, std_val = band.GetStatistics(True, True)
        
        # Count missing pixels if nodata is defined
        missing_pixels = 0
        if nodata_value is not None:
            data_array = band.ReadAsArray()
            import numpy as np
            missing_pixels = np.sum(data_array == nodata_value)
        
        total_pixels = width * height
        coverage_percent = ((total_pixels - missing_pixels) / total_pixels) * 100
        
        info = {
            'width': width,
            'height': height,
            'bands': bands,
            'pixel_width': geotransform[1],
            'pixel_height': abs(geotransform[5]),
            'min_value': min_val,
            'max_value': max_val,
            'mean_value': mean_val,
            'std_value': std_val,
            'nodata_value': nodata_value,
            'missing_pixels': missing_pixels,
            'total_pixels': total_pixels,
            'coverage_percent': coverage_percent,
            'file_size': os.path.getsize(raster_path),
            'projection': projection
        }
        
        print(f"   📏 Dimensions: {width} x {height} pixels ({bands} band{'s' if bands > 1 else ''})")
        print(f"   📐 Pixel size: {info['pixel_width']:.6f} x {info['pixel_height']:.6f}")
        print(f"   📊 Value range: {min_val:.2f} to {max_val:.2f}")
        print(f"   📈 Statistics: mean={mean_val:.2f}, std={std_val:.2f}")
        print(f"   🕳️ Missing pixels: {missing_pixels:,} / {total_pixels:,} ({coverage_percent:.1f}% coverage)")
        print(f"   💾 File size: {info['file_size']:,} bytes")
        
        dataset = None  # Close dataset
        return info
        
    except Exception as e:
        print(f"❌ Error analyzing raster: {e}")
        return None

def generate_hillshade_optimized(dtm_path, hillshade_path, azimuth=315, altitude=45, z_factor=1.0):
    """Generate hillshade with optimized parameters."""
    print(f"\n🌄 Generating optimized hillshade")
    print(f"   📥 Input DTM: {os.path.basename(dtm_path)}")
    print(f"   📤 Output hillshade: {os.path.basename(hillshade_path)}")
    print(f"   ⚙️ Parameters: azimuth={azimuth}°, altitude={altitude}°, z_factor={z_factor}")
    
    if not os.path.exists(dtm_path):
        print(f"❌ Input DTM not found: {dtm_path}")
        return False
    
    os.makedirs(os.path.dirname(hillshade_path), exist_ok=True)
    
    # Use command line approach (more reliable)
    cmd = [
        "gdaldem", "hillshade",
        "-az", str(azimuth),
        "-alt", str(altitude),
        "-z", str(z_factor),
        "-compute_edges",  # Prevent edge pixel issues
        "-co", "COMPRESS=LZW",
        "-co", "TILED=YES",
        "-co", "PREDICTOR=2",
        dtm_path,
        hillshade_path
    ]
    
    success, output = run_command(cmd, f"Optimized hillshade generation")
    
    if success and os.path.exists(hillshade_path):
        file_size = os.path.getsize(hillshade_path)
        print(f"✅ Optimized hillshade generated: {os.path.basename(hillshade_path)} ({file_size:,} bytes)")
        return True
    else:
        print(f"❌ Optimized hillshade generation failed")
        return False

def convert_to_png_optimized(tiff_path, png_path):
    """Convert TIFF to PNG with enhanced settings."""
    print(f"\n🎨 Converting to optimized PNG")
    print(f"   📥 Input TIFF: {os.path.basename(tiff_path)}")
    print(f"   📤 Output PNG: {os.path.basename(png_path)}")
    
    try:
        # Open the input TIFF
        dataset = gdal.Open(tiff_path, gdal.GA_ReadOnly)
        if dataset is None:
            raise RuntimeError(f"Cannot open TIFF: {tiff_path}")
        
        # Get band statistics for proper scaling
        band = dataset.GetRasterBand(1)
        band.ComputeStatistics(False)
        min_val, max_val, mean_val, std_val = band.GetStatistics(True, True)
        
        print(f"   📊 TIFF value range: {min_val:.1f} to {max_val:.1f}")
        
        # Enhanced PNG conversion with proper scaling
        scale_options = [
            "-of", "PNG",
            "-scale", str(min_val), str(max_val), "0", "255",
            "-co", "WORLDFILE=YES"  # Create world file for georeferencing
        ]
        
        # Use gdal.Translate for conversion
        result = gdal.Translate(png_path, dataset, options=scale_options)
        
        if result is not None and os.path.exists(png_path):
            file_size = os.path.getsize(png_path)
            print(f"✅ PNG conversion successful: {os.path.basename(png_path)} ({file_size:,} bytes)")
            
            # Check for world file
            world_file = os.path.splitext(png_path)[0] + ".pgw"
            if os.path.exists(world_file):
                print(f"   🌍 World file created: {os.path.basename(world_file)}")
            
            return True
        else:
            print(f"❌ PNG conversion failed")
            return False
            
    except Exception as e:
        print(f"❌ Error converting to PNG: {e}")
        return False
    finally:
        if 'dataset' in locals() and dataset is not None:
            dataset = None

def run_optimized_workflow():
    """Run the optimized workflow with gap filling."""
    print(f"\n{'='*80}")
    print(f"🧪 OPTIMIZED HILLSHADE TEST - ENHANCED WORKFLOW")
    print(f"{'='*80}")
    
    overall_start_time = time.time()
    
    try:
        # Step 1: Setup environment
        setup_test_environment()
        
        # Step 2: Create optimized DTM pipeline
        optimized_pipeline = create_optimized_dtm_pipeline()
        
        # Step 3: Generate optimized DTM
        print(f"\n{'='*60}")
        print(f"🏔️ STEP 1: OPTIMIZED DTM GENERATION")
        print(f"{'='*60}")
        
        dtm_success = generate_optimized_dtm(optimized_pipeline)
        if not dtm_success:
            raise RuntimeError("Optimized DTM generation failed")
        
        # Analyze optimized DTM
        dtm_optimized_info = get_raster_info(DTM_OPTIMIZED_PATH, "Optimized DTM")
        if dtm_optimized_info is None:
            raise RuntimeError("Failed to analyze optimized DTM")
        
        # Step 4: Fill NoData gaps
        print(f"\n{'='*60}")
        print(f"🔧 STEP 2: GAP FILLING")
        print(f"{'='*60}")
        
        fill_success = fill_nodata_gaps(DTM_OPTIMIZED_PATH, DTM_FILLED_PATH, max_distance=15)
        if not fill_success:
            print(f"⚠️ Gap filling failed, using optimized DTM without filling")
            dtm_final_path = DTM_OPTIMIZED_PATH
            dtm_final_info = dtm_optimized_info
        else:
            dtm_final_path = DTM_FILLED_PATH
            dtm_final_info = get_raster_info(DTM_FILLED_PATH, "Gap-filled DTM")
            if dtm_final_info is None:
                raise RuntimeError("Failed to analyze gap-filled DTM")
        
        # Step 5: Generate optimized hillshade
        print(f"\n{'='*60}")
        print(f"🌄 STEP 3: OPTIMIZED HILLSHADE GENERATION")
        print(f"{'='*60}")
        
        hillshade_success = generate_hillshade_optimized(dtm_final_path, HILLSHADE_OPTIMIZED_PATH)
        if not hillshade_success:
            raise RuntimeError("Optimized hillshade generation failed")
        
        # Analyze optimized hillshade
        hillshade_optimized_info = get_raster_info(HILLSHADE_OPTIMIZED_PATH, "Optimized Hillshade")
        if hillshade_optimized_info is None:
            raise RuntimeError("Failed to analyze optimized hillshade")
        
        # Step 6: Convert to optimized PNG
        print(f"\n{'='*60}")
        print(f"🎨 STEP 4: OPTIMIZED PNG CONVERSION")
        print(f"{'='*60}")
        
        png_success = convert_to_png_optimized(HILLSHADE_OPTIMIZED_PATH, PNG_OPTIMIZED_PATH)
        if not png_success:
            raise RuntimeError("Optimized PNG conversion failed")
        
        # Final summary
        total_time = time.time() - overall_start_time
        
        print(f"\n{'='*80}")
        print(f"🎉 OPTIMIZED WORKFLOW COMPLETED!")
        print(f"{'='*80}")
        print(f"⏱️ Total processing time: {total_time:.2f} seconds")
        print(f"📊 Optimization results:")
        print(f"   🏔️ Optimized DTM: {dtm_optimized_info['coverage_percent']:.1f}% coverage ({dtm_optimized_info['missing_pixels']:,} missing)")
        print(f"   🔧 Gap-filled DTM: {dtm_final_info['coverage_percent']:.1f}% coverage ({dtm_final_info['missing_pixels']:,} missing)")
        print(f"   🌄 Final Hillshade: {hillshade_optimized_info['coverage_percent']:.1f}% coverage ({hillshade_optimized_info['missing_pixels']:,} missing)")
        print(f"   🎨 PNG: {os.path.basename(PNG_OPTIMIZED_PATH)} ({os.path.getsize(PNG_OPTIMIZED_PATH):,} bytes)")
        
        # Quality improvement assessment
        original_missing = 19618  # From previous test results
        optimized_missing = hillshade_optimized_info['missing_pixels']
        improvement = original_missing - optimized_missing
        improvement_percent = (improvement / original_missing) * 100 if original_missing > 0 else 0
        
        print(f"\n📈 Quality Improvement:")
        print(f"   📉 Missing pixels reduced: {original_missing:,} → {optimized_missing:,}")
        print(f"   📊 Improvement: {improvement:,} pixels ({improvement_percent:.1f}%)")
        
        if optimized_missing == 0:
            print(f"✅ Quality Assessment: EXCELLENT - No missing pixels!")
        elif optimized_missing < 1000:
            print(f"✅ Quality Assessment: VERY GOOD - Minimal missing pixels")
        elif optimized_missing < 5000:
            print(f"⚠️ Quality Assessment: GOOD - Acceptable missing pixels")
        else:
            print(f"❌ Quality Assessment: NEEDS IMPROVEMENT - Still many missing pixels")
        
        print(f"\n📁 Optimized output files located in: {TEST_OUTPUT_DIR}")
        print(f"   📄 {os.path.basename(DTM_OPTIMIZED_PATH)}")
        if fill_success:
            print(f"   📄 {os.path.basename(DTM_FILLED_PATH)}")
        print(f"   📄 {os.path.basename(HILLSHADE_OPTIMIZED_PATH)}")
        print(f"   📄 {os.path.basename(PNG_OPTIMIZED_PATH)}")
        
        return True
        
    except Exception as e:
        total_time = time.time() - overall_start_time
        print(f"\n{'='*80}")
        print(f"❌ OPTIMIZED WORKFLOW FAILED!")
        print(f"{'='*80}")
        print(f"⏱️ Time before failure: {total_time:.2f} seconds")
        print(f"💥 Error: {e}")
        return False

def main():
    """Main function."""
    print(f"🧪 Optimized Standalone Hillshade Test")
    print(f"Version: 2.0 - Gap Filling Enhanced")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    
    # Check GDAL availability
    try:
        print(f"GDAL: {gdal.__version__}")
    except:
        print(f"❌ GDAL not available")
        return 1
    
    # Check PDAL availability
    try:
        result = subprocess.run(["pdal", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"PDAL: Available")
        else:
            print(f"❌ PDAL not available")
            return 1
    except FileNotFoundError:
        print(f"❌ PDAL not found in PATH")
        return 1
    
    # Run the optimized workflow
    success = run_optimized_workflow()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
