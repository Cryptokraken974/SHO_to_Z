#!/usr/bin/env python3
"""
Standalone Hillshade Test for FoxIsland.laz

This standalone test:
1. Reads FoxIsland.laz file
2. Generates DTM using the dtm.json pipeline from the app
3. Creates hillshade from the DTM using GDAL
4. Converts hillshade to PNG for visualization

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
DTM_OUTPUT_PATH = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_DTM.tif")
HILLSHADE_OUTPUT_PATH = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_Hillshade.tif")
PNG_OUTPUT_PATH = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_Hillshade.png")
DTM_FILLED_PATH = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_DTM_filled.tif") # New path for filled DTM
PNG_FILLED_DTM_OUTPUT_PATH = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_DTM_filled.png") # New path for filled DTM PNG

def setup_test_environment():
    """Setup the test environment and directories."""
    print(f"🏗️ Setting up test environment")
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

def load_and_modify_dtm_pipeline():
    """Load the DTM pipeline and modify it for our specific test."""
    print(f"\n📋 Loading DTM pipeline from {DTM_PIPELINE_PATH}")
    
    with open(DTM_PIPELINE_PATH, 'r') as f:
        pipeline_content = f.read()
    
    # Remove comments (PDAL doesn't handle JSON comments well)
    lines = pipeline_content.split('\n')
    clean_lines = [line for line in lines if not line.strip().startswith('//')]
    clean_content = '\n'.join(clean_lines)
    
    pipeline = json.loads(clean_content)
    
    # Modify the pipeline for our specific inputs/outputs
    # Replace the input file path
    pipeline["pipeline"][0] = INPUT_LAZ_PATH
    
    # Find and modify the writers.gdal stage
    for stage in pipeline["pipeline"]:
        if isinstance(stage, dict) and stage.get("type") == "writers.gdal":
            stage["filename"] = DTM_OUTPUT_PATH
            stage["resolution"] = 1.0  # Higher resolution for better quality
            break
    
    print(f"✅ Pipeline loaded and modified")
    print(f"   📥 Input: {os.path.basename(INPUT_LAZ_PATH)}")
    print(f"   📤 Output: {os.path.basename(DTM_OUTPUT_PATH)}")
    
    return pipeline

def generate_dtm_with_pdal(pipeline):
    """Generate DTM using PDAL with the modified pipeline."""
    print(f"\n🏔️ Generating DTM using PDAL")
    
    # Create temporary pipeline file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        json.dump(pipeline, temp_file, indent=2)
        temp_pipeline_path = temp_file.name
    
    try:
        # Run PDAL pipeline
        cmd = ["pdal", "pipeline", temp_pipeline_path]
        success, output = run_command(cmd, "PDAL DTM generation")
        
        if success and os.path.exists(DTM_OUTPUT_PATH):
            file_size = os.path.getsize(DTM_OUTPUT_PATH)
            print(f"✅ DTM generated successfully: {os.path.basename(DTM_OUTPUT_PATH)} ({file_size:,} bytes)")
            return True
        else:
            print(f"❌ DTM generation failed")
            return False
    
    finally:
        # Clean up temporary pipeline file
        if os.path.exists(temp_pipeline_path):
            os.unlink(temp_pipeline_path)

def get_raster_info(raster_path):
    """Get comprehensive information about a raster file."""
    print(f"\n📊 Analyzing raster: {os.path.basename(raster_path)}")
    
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
            'file_size': os.path.getsize(raster_path),
            'projection': projection
        }
        
        print(f"   📏 Dimensions: {width} x {height} pixels ({bands} band{'s' if bands > 1 else ''})")
        print(f"   📐 Pixel size: {info['pixel_width']:.6f} x {info['pixel_height']:.6f}")
        print(f"   📊 Value range: {min_val:.2f} to {max_val:.2f}")
        print(f"   📈 Statistics: mean={mean_val:.2f}, std={std_val:.2f}")
        print(f"   🕳️ Missing pixels: {missing_pixels:,}")
        print(f"   💾 File size: {info['file_size']:,} bytes")
        
        dataset = None  # Close dataset
        return info
        
    except Exception as e:
        print(f"❌ Error analyzing raster: {e}")
        return None

def fill_nodata_gaps(input_path, output_path, max_distance=15, smoothing_iterations=2):
    """Fill NoData gaps using GDAL's FillNodata algorithm."""
    print(f"\\n🔧 Filling NoData gaps in {os.path.basename(input_path)}")
    print(f"   📤 Output: {os.path.basename(output_path)}")
    print(f"   ⚙️ Max distance: {max_distance} pixels, Smoothing: {smoothing_iterations} iterations")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        # Open input raster
        src_ds = gdal.Open(input_path, gdal.GA_ReadOnly)
        if src_ds is None:
            raise RuntimeError(f"Cannot open input raster for gap filling: {input_path}")
        
        # Create the destination dataset as a copy of the source
        driver = gdal.GetDriverByName('GTiff')
        dst_ds = driver.CreateCopy(output_path, src_ds, options=[
            "COMPRESS=LZW", 
            "TILED=YES", 
            "PREDICTOR=2"
        ])
        if dst_ds is None:
            # Ensure src_ds is closed if dst_ds creation fails
            src_ds = None
            raise RuntimeError(f"Failed to create copy for gap filling: {output_path}")

        dst_band = dst_ds.GetRasterBand(1)
        
        mask_band = None # Fill all NoData values
        
        start_time = time.time()
        result = gdal.FillNodata(
            targetBand=dst_band, 
            maskBand=mask_band, 
            maxSearchDist=max_distance, 
            smoothingIterations=smoothing_iterations
        )
        duration = time.time() - start_time
        
        dst_ds.FlushCache() # Ensure changes are written

        if result == gdal.CE_None: # Success
            file_size = os.path.getsize(output_path)
            print(f"✅ Gap filling completed in {duration:.2f} seconds")
            print(f"   💾 Output size: {file_size:,} bytes")
            return True
        else:
            print(f"❌ Gap filling failed (GDAL error code: {result})")
            if os.path.exists(output_path):
                try: os.remove(output_path)
                except OSError as e_rm: print(f"   ⚠️ Could not remove failed output {output_path}: {e_rm}")
            return False
            
    except Exception as e:
        print(f"❌ Error in gap filling: {e}")
        if os.path.exists(output_path):
            try: os.remove(output_path)
            except OSError as e_rm: print(f"   ⚠️ Could not remove failed output {output_path}: {e_rm}")
        return False
    finally:
        if 'dst_ds' in locals() and dst_ds is not None:
            dst_ds = None 
        if 'src_ds' in locals() and src_ds is not None:
            src_ds = None

def generate_hillshade(dtm_path, hillshade_path, azimuth=315, altitude=45, z_factor=1.0):
    """Generate hillshade from DTM using GDAL."""
    print(f"\n🌄 Generating hillshade from DTM")
    print(f"   📥 Input DTM: {os.path.basename(dtm_path)}")
    print(f"   📤 Output hillshade: {os.path.basename(hillshade_path)}")
    print(f"   ⚙️ Parameters: azimuth={azimuth}°, altitude={altitude}°, z_factor={z_factor}")
    
    # Verify input DTM exists
    if not os.path.exists(dtm_path):
        print(f"❌ Input DTM not found: {dtm_path}")
        return False
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(hillshade_path), exist_ok=True)
    
    try:
        # Try GDAL Python API first
        print(f"   🔄 Attempting GDAL Python API...")
        result = gdal.DEMProcessing(
            hillshade_path,
            dtm_path,
            'hillshade',
            azimuth=azimuth,
            altitude=altitude,
            zFactor=z_factor,
            computeEdges=True,  # Essential for edge pixels - prevents missing pixels
            format="GTiff",
            creationOptions=[
                "COMPRESS=LZW",
                "TILED=YES",
                "PREDICTOR=2"
            ]
        )
        
        if result == 1 and os.path.exists(hillshade_path):  # GDAL returns 1 for success
            file_size = os.path.getsize(hillshade_path)
            print(f"✅ Hillshade generated successfully: {os.path.basename(hillshade_path)} ({file_size:,} bytes)")
            return True
        else:
            print(f"⚠️ GDAL Python API failed, trying command line...")
            # Fallback to command line approach
            return generate_hillshade_cli(dtm_path, hillshade_path, azimuth, altitude, z_factor)
            
    except Exception as e:
        print(f"⚠️ GDAL Python API error: {e}")
        print(f"   🔄 Trying command line approach...")
        # Fallback to command line approach
        return generate_hillshade_cli(dtm_path, hillshade_path, azimuth, altitude, z_factor)

def generate_hillshade_cli(dtm_path, hillshade_path, azimuth=315, altitude=45, z_factor=1.0):
    """Generate hillshade using gdaldem command line tool."""
    print(f"   🔄 Using gdaldem command line tool...")
    
    cmd = [
        "gdaldem", "hillshade",
        "-az", str(azimuth),
        "-alt", str(altitude),
        "-z", str(z_factor),
        "-compute_edges",  # Command line equivalent of computeEdges=True
        "-co", "COMPRESS=LZW",
        "-co", "TILED=YES",
        "-co", "PREDICTOR=2",
        dtm_path,
        hillshade_path
    ]
    
    success, output = run_command(cmd, f"gdaldem hillshade generation")
    
    if success and os.path.exists(hillshade_path):
        file_size = os.path.getsize(hillshade_path)
        print(f"✅ Hillshade generated successfully: {os.path.basename(hillshade_path)} ({file_size:,} bytes)")
        return True
    else:
        print(f"❌ Command line hillshade generation also failed")
        return False

def convert_tiff_to_png(tiff_path, png_path):
    """Convert TIFF to PNG using GDAL with enhanced quality settings."""
    print(f"\n🎨 Converting TIFF to PNG")
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

def run_complete_workflow():
    """Run the complete workflow: LAZ -> DTM -> Fill Gaps -> Hillshade -> PNG."""
    print(f"\\n{'='*80}")
    print(f"🧪 STANDALONE HILLSHADE TEST - COMPLETE WORKFLOW")
    print(f"{'='*80}")
    
    overall_start_time = time.time()
    
    try:
        # Step 1: Setup environment
        setup_test_environment()
        
        # Step 2: Load and modify DTM pipeline
        pipeline = load_and_modify_dtm_pipeline()
        
        # Step 3: Generate DTM using PDAL
        print(f"\n{'='*60}")
        print(f"🏔️ STEP 1: DTM GENERATION")
        print(f"{'='*60}")
        
        dtm_success = generate_dtm_with_pdal(pipeline)
        if not dtm_success:
            raise RuntimeError("DTM generation failed")
        
        # Analyze DTM
        dtm_info = get_raster_info(DTM_OUTPUT_PATH)
        if dtm_info is None:
            raise RuntimeError("Failed to analyze DTM")

        # Step 3.5: Fill NoData gaps in DTM
        print(f"\\n{'='*60}")
        print(f"🔧 STEP 1.5: DTM GAP FILLING")
        print(f"{'='*60}")
        
        dtm_for_hillshade_path = DTM_OUTPUT_PATH # Default to original DTM
        dtm_for_hillshade_info = dtm_info

        fill_success = fill_nodata_gaps(DTM_OUTPUT_PATH, DTM_FILLED_PATH) # Uses defaults: max_distance=15, smoothing_iterations=2
        if not fill_success:
            print(f"⚠️ Gap filling failed, proceeding with original DTM ({os.path.basename(DTM_OUTPUT_PATH)}) for hillshade.")
        else:
            dtm_filled_info = get_raster_info(DTM_FILLED_PATH)
            if dtm_filled_info is None:
                print(f"⚠️ Failed to analyze gap-filled DTM, proceeding with original DTM ({os.path.basename(DTM_OUTPUT_PATH)}).")
            else:
                print(f"✅ Using gap-filled DTM ({os.path.basename(DTM_FILLED_PATH)}) for hillshade.")
                dtm_for_hillshade_path = DTM_FILLED_PATH
                dtm_for_hillshade_info = dtm_filled_info
        
        # Step 4: Generate hillshade (using potentially filled DTM)
        print(f"\\n{'='*60}")
        print(f"🌄 STEP 2: HILLSHADE GENERATION")
        print(f"{'='*60}")
        print(f"   ⚙️ Using DTM: {os.path.basename(dtm_for_hillshade_path)}") # Clarify which DTM is used
        
        hillshade_success = generate_hillshade(dtm_for_hillshade_path, HILLSHADE_OUTPUT_PATH)
        if not hillshade_success:
            raise RuntimeError("Hillshade generation failed")
        
        # Analyze hillshade
        hillshade_info = get_raster_info(HILLSHADE_OUTPUT_PATH)
        if hillshade_info is None:
            raise RuntimeError("Failed to analyze hillshade")
        
        # Step 5: Convert to PNG
        print(f"\n{'='*60}")
        print(f"🎨 STEP 3: PNG CONVERSION")
        print(f"{'='*60}")
        
        png_success = convert_tiff_to_png(HILLSHADE_OUTPUT_PATH, PNG_OUTPUT_PATH)
        if not png_success:
            raise RuntimeError("PNG conversion failed")
        
        # Step 5.5: Convert filled DTM to PNG (if it exists and was used)
        if fill_success and dtm_for_hillshade_path == DTM_FILLED_PATH:
            print(f"\\n{'='*60}")
            print(f"🎨 STEP 3.5: FILLED DTM PNG CONVERSION")
            print(f"{'='*60}")
            png_filled_dtm_success = convert_tiff_to_png(DTM_FILLED_PATH, PNG_FILLED_DTM_OUTPUT_PATH)
            if not png_filled_dtm_success:
                print(f"⚠️ Filled DTM PNG conversion failed. Continuing without it.")
        else:
            png_filled_dtm_success = False # To avoid undefined variable later

        # Final summary
        total_time = time.time() - overall_start_time
        
        print(f"\n{'='*80}")
        print(f"🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        print(f"{'='*80}")
        print(f"⏱️ Total processing time: {total_time:.2f} seconds")
        print(f"📊 Results summary:")
        print(f"   🏔️ Original DTM: {dtm_info['width']}x{dtm_info['height']} pixels, {dtm_info['missing_pixels']:,} missing pixels")
        if fill_success and 'dtm_filled_info' in locals() and dtm_filled_info is not None:
             print(f"   🔧 Filled DTM: {dtm_filled_info['width']}x{dtm_filled_info['height']} pixels, {dtm_filled_info['missing_pixels']:,} missing pixels")
        elif fill_success: # fill_success was true, but dtm_filled_info was None
            print(f"   🔧 Filled DTM: Analysis failed, but gap filling was attempted.")
        else: # fill_success was false
            print(f"   🔧 Filled DTM: Gap filling failed or was skipped.")

        print(f"   🌄 Hillshade (from {os.path.basename(dtm_for_hillshade_path)}): {hillshade_info['width']}x{hillshade_info['height']} pixels, {hillshade_info['missing_pixels']:,} missing pixels")
        print(f"   🎨 PNG: {os.path.basename(PNG_OUTPUT_PATH)} ({os.path.getsize(PNG_OUTPUT_PATH):,} bytes)")
        if png_filled_dtm_success and os.path.exists(PNG_FILLED_DTM_OUTPUT_PATH):
            print(f"   🖼️ Filled DTM PNG: {os.path.basename(PNG_FILLED_DTM_OUTPUT_PATH)} ({os.path.getsize(PNG_FILLED_DTM_OUTPUT_PATH):,} bytes)")

        print(f"\\n📁 Output files located in: {TEST_OUTPUT_DIR}")
        print(f"   📄 {os.path.basename(DTM_OUTPUT_PATH)} (Original DTM)")
        if os.path.exists(DTM_FILLED_PATH):
            print(f"   📄 {os.path.basename(DTM_FILLED_PATH)} (Filled DTM)")
        if os.path.exists(PNG_FILLED_DTM_OUTPUT_PATH):
            print(f"   🖼️ {os.path.basename(PNG_FILLED_DTM_OUTPUT_PATH)} (Filled DTM PNG)")
        print(f"   📄 {os.path.basename(HILLSHADE_OUTPUT_PATH)}")
        print(f"   📄 {os.path.basename(PNG_OUTPUT_PATH)}")
        
        # Quality assessment
        if hillshade_info['missing_pixels'] == 0:
            print(f"✅ Quality Assessment: EXCELLENT - No missing pixels in hillshade")
        elif hillshade_info['missing_pixels'] < 100:
            print(f"⚠️ Quality Assessment: GOOD - Minimal missing pixels ({hillshade_info['missing_pixels']})")
        else:
            print(f"❌ Quality Assessment: POOR - Too many missing pixels ({hillshade_info['missing_pixels']})")
        
        return True
        
    except Exception as e:
        total_time = time.time() - overall_start_time
        print(f"\n{'='*80}")
        print(f"❌ WORKFLOW FAILED!")
        print(f"{'='*80}")
        print(f"⏱️ Time before failure: {total_time:.2f} seconds")
        print(f"💥 Error: {e}")
        return False

def main():
    """Main function."""
    print(f"🧪 Standalone Hillshade Test")
    print(f"Version: 1.0")
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
    
    # Run the workflow
    success = run_complete_workflow()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
