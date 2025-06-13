#!/usr/bin/env python3
"""
Complete LAZ Processing Pipeline Test for FoxIsland.laz

This comprehensive test validates the entire LAZ processing workflow including:
1. DTM generation from LAZ
2. Multiple hillshades with different azimuths (315°, 45°, 135°)
3. RGB composite creation from the three hillshades
4. Color relief generation
5. Tint overlay (color relief + RGB hillshade)
6. Slope relief generation  
7. Final slope overlay (tint + slope blend)
8. PNG conversions for all outputs

This test replicates the complete workflow from process_all_raster_products()
to ensure the 3-hillshade RGB blending with color-relief tint and slope blending
works correctly for LAZ files.
"""

import os
import sys
import time
import json
import subprocess
import tempfile
import asyncio
from pathlib import Path
from osgeo import gdal
import numpy as np

# Enable GDAL exceptions
gdal.UseExceptions()

# Add app directory to Python path for imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
APP_DIR = os.path.join(BASE_DIR, "app")
sys.path.insert(0, APP_DIR)

# Test Configuration
INPUT_LAZ_PATH = os.path.join(BASE_DIR, "input", "LAZ", "FoxIsland.laz")
DTM_PIPELINE_PATH = os.path.join(APP_DIR, "processing", "pipelines_json", "dtm.json")
HILLSHADE_CONFIG_PATH = os.path.join(APP_DIR, "processing", "pipelines_json", "hillshade.json")

# Output paths
TEST_OUTPUT_DIR = os.path.join(BASE_DIR, "Tests", "laz_pipeline_complete", "outputs")
DTM_OUTPUT_PATH = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_DTM.tif")

# Hillshade outputs (matching the RGB configuration)
HS_RED_OUTPUT = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_Hillshade_315.tif")    # Red channel
HS_GREEN_OUTPUT = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_Hillshade_45.tif")   # Green channel  
HS_BLUE_OUTPUT = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_Hillshade_135.tif")   # Blue channel

# Composite and overlay outputs
RGB_COMPOSITE_OUTPUT = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_RGB_Composite.tif")
COLOR_RELIEF_OUTPUT = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_ColorRelief.tif")
TINT_OVERLAY_OUTPUT = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_TintOverlay.tif")
SLOPE_RELIEF_OUTPUT = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_SlopeRelief.tif")
FINAL_BLEND_OUTPUT = os.path.join(TEST_OUTPUT_DIR, "FoxIsland_FinalBlend.tif")

# PNG outputs
PNG_OUTPUTS = {
    'dtm': os.path.join(TEST_OUTPUT_DIR, "FoxIsland_DTM.png"),
    'hs_red': os.path.join(TEST_OUTPUT_DIR, "FoxIsland_Hillshade_315.png"),
    'hs_green': os.path.join(TEST_OUTPUT_DIR, "FoxIsland_Hillshade_45.png"),
    'hs_blue': os.path.join(TEST_OUTPUT_DIR, "FoxIsland_Hillshade_135.png"),
    'rgb_composite': os.path.join(TEST_OUTPUT_DIR, "FoxIsland_RGB_Composite.png"),
    'color_relief': os.path.join(TEST_OUTPUT_DIR, "FoxIsland_ColorRelief.png"),
    'tint_overlay': os.path.join(TEST_OUTPUT_DIR, "FoxIsland_TintOverlay.png"),
    'slope_relief': os.path.join(TEST_OUTPUT_DIR, "FoxIsland_SlopeRelief.png"),
    'final_blend': os.path.join(TEST_OUTPUT_DIR, "FoxIsland_FinalBlend.png")
}

def setup_test_environment():
    """Setup the test environment and directories."""
    print(f"\\n{'='*80}")
    print(f"🏗️ SETTING UP COMPLETE LAZ PIPELINE TEST")
    print(f"{'='*80}")
    print(f"📁 Base directory: {BASE_DIR}")
    print(f"📁 Test output directory: {TEST_OUTPUT_DIR}")
    print(f"📄 Input LAZ: {os.path.basename(INPUT_LAZ_PATH)}")
    
    # Create output directory
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    
    # Verify input file exists
    if not os.path.exists(INPUT_LAZ_PATH):
        raise FileNotFoundError(f"Input LAZ file not found: {INPUT_LAZ_PATH}")
    
    # Verify pipeline files exist
    if not os.path.exists(DTM_PIPELINE_PATH):
        raise FileNotFoundError(f"DTM pipeline not found: {DTM_PIPELINE_PATH}")
        
    if not os.path.exists(HILLSHADE_CONFIG_PATH):
        raise FileNotFoundError(f"Hillshade config not found: {HILLSHADE_CONFIG_PATH}")
    
    file_size = os.path.getsize(INPUT_LAZ_PATH)
    print(f"✅ Input LAZ file verified: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")

def load_and_modify_dtm_pipeline():
    """Load and modify the DTM pipeline for the test."""
    print(f"\\n🔧 Loading DTM pipeline from {DTM_PIPELINE_PATH}")
    
    with open(DTM_PIPELINE_PATH, 'r') as f:
        pipeline = json.load(f)
    
    # Modify input filename
    pipeline[0]["filename"] = INPUT_LAZ_PATH
    
    # Modify output filename  
    for stage in pipeline:
        if "filename" in stage and "writers.gdal" in stage.get("type", ""):
            stage["filename"] = DTM_OUTPUT_PATH
    
    print(f"✅ DTM pipeline loaded and configured")
    print(f"   📥 Input: {os.path.basename(INPUT_LAZ_PATH)}")
    print(f"   📤 Output: {os.path.basename(DTM_OUTPUT_PATH)}")
    
    return pipeline

def generate_dtm_with_pdal(pipeline):
    """Generate DTM using PDAL with the configured pipeline."""
    print(f"\\n🏔️ Generating DTM using PDAL...")
    start_time = time.time()
    
    # Write temporary pipeline file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(pipeline, f, indent=2)
        temp_pipeline_path = f.name
    
    try:
        print(f"📄 Temporary pipeline: {temp_pipeline_path}")
        
        # Execute PDAL pipeline
        cmd = ["pdal", "pipeline", temp_pipeline_path]
        print(f"🚀 Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        processing_time = time.time() - start_time
        print(f"✅ PDAL execution completed in {processing_time:.2f} seconds")
        
        if result.stdout:
            print(f"📝 PDAL stdout: {result.stdout}")
        if result.stderr:
            print(f"⚠️ PDAL stderr: {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ PDAL execution failed with return code {e.returncode}")
        print(f"❌ Error: {e.stderr}")
        return False
    finally:
        # Clean up temporary file
        os.unlink(temp_pipeline_path)
    
    # Verify output file was created
    if not os.path.exists(DTM_OUTPUT_PATH):
        print(f"❌ DTM output file was not created: {DTM_OUTPUT_PATH}")
        return False
        
    output_size = os.path.getsize(DTM_OUTPUT_PATH)
    print(f"✅ DTM generated successfully: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
    
    return True

def load_hillshade_config():
    """Load hillshade configuration for RGB composite."""
    print(f"\\n🌄 Loading hillshade configuration...")
    
    with open(HILLSHADE_CONFIG_PATH, 'r') as f:
        config = json.load(f)
    
    print(f"✅ Hillshade configuration loaded: {len(config)} hillshade definitions")
    
    # Display the RGB channel assignments
    for hs in config:
        channel = "Red" if hs["azimuth"] == 315 else "Green" if hs["azimuth"] == 45 else "Blue" if hs["azimuth"] == 135 else "Unknown"
        print(f"   🎨 {channel} Channel: {hs['azimuth']}° azimuth, {hs['altitude']}° altitude")
    
    return config

def generate_hillshade(input_dtm, output_path, azimuth, altitude, z_factor=1.0):
    """Generate a single hillshade using GDAL."""
    print(f"\\n🌄 Generating hillshade: {azimuth}° azimuth, {altitude}° altitude")
    print(f"   📥 Input DTM: {os.path.basename(input_dtm)}")
    print(f"   📤 Output: {os.path.basename(output_path)}")
    
    start_time = time.time()
    
    # Use GDAL DEMProcessing for hillshade generation
    result = gdal.DEMProcessing(
        destName=output_path,
        srcDS=input_dtm,
        processing="hillshade",
        azimuth=azimuth,
        altitude=altitude,
        zFactor=z_factor,
        scale=1.0,
        computeEdges=True,
        format="GTiff"
    )
    
    processing_time = time.time() - start_time
    
    if result is None:
        print(f"❌ Hillshade generation failed")
        return False
    
    if not os.path.exists(output_path):
        print(f"❌ Hillshade output file was not created: {output_path}")
        return False
        
    output_size = os.path.getsize(output_path)
    print(f"✅ Hillshade generated in {processing_time:.2f} seconds: {output_size:,} bytes")
    
    return True

def create_rgb_composite(red_path, green_path, blue_path, output_path):
    """Create RGB composite from three hillshade TIFFs."""
    print(f"\\n🌈 Creating RGB composite...")
    print(f"   🔴 Red channel: {os.path.basename(red_path)}")
    print(f"   🟢 Green channel: {os.path.basename(green_path)}")
    print(f"   🔵 Blue channel: {os.path.basename(blue_path)}")
    print(f"   📤 Output: {os.path.basename(output_path)}")
    
    start_time = time.time()
    
    try:
        # Read the three hillshade images
        arrays = {}
        geo = proj = None
        
        for band, path in [('R', red_path), ('G', green_path), ('B', blue_path)]:
            ds = gdal.Open(path)
            if ds is None:
                raise FileNotFoundError(f"Hillshade file not found: {path}")
            
            arr = ds.ReadAsArray().astype(np.float32)
            arrays[band] = arr
            
            if geo is None:
                geo = ds.GetGeoTransform()
                proj = ds.GetProjection()
            
            ds = None
        
        # Normalize each channel to 0-255
        def normalize(a):
            return ((a - a.min()) / (a.max() - a.min()) * 255.0).astype(np.uint8)
        
        rgb = np.stack([normalize(arrays['R']), normalize(arrays['G']), normalize(arrays['B'])], axis=-1)
        
        # Save as 3-band GeoTIFF
        driver = gdal.GetDriverByName('GTiff')
        h, w, bands = rgb.shape
        
        out_ds = driver.Create(output_path, w, h, bands, gdal.GDT_Byte)
        out_ds.SetGeoTransform(geo)
        out_ds.SetProjection(proj)
        
        for i in range(bands):
            out_band = out_ds.GetRasterBand(i + 1)
            out_band.WriteArray(rgb[:, :, i])
            out_band.FlushCache()
        
        out_ds = None
        
        processing_time = time.time() - start_time
        output_size = os.path.getsize(output_path)
        print(f"✅ RGB composite created in {processing_time:.2f} seconds: {output_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ RGB composite creation failed: {e}")
        return False

def generate_color_relief(input_dtm, output_path):
    """Generate color relief from DTM."""
    print(f"\\n🎨 Generating color relief...")
    print(f"   📥 Input DTM: {os.path.basename(input_dtm)}")
    print(f"   📤 Output: {os.path.basename(output_path)}")
    
    start_time = time.time()
    
    try:
        # Get DTM statistics for color table
        ds = gdal.Open(input_dtm)
        band = ds.GetRasterBand(1)
        stats = band.GetStatistics(True, True)
        min_elevation, max_elevation = stats[0], stats[1]
        ds = None
        
        print(f"   📊 Elevation range: {min_elevation:.2f} to {max_elevation:.2f}")
        
        # Create color table
        color_table_path = os.path.join(TEST_OUTPUT_DIR, "color_table.txt")
        
        # Define terrain color ramp
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
            for ratio, rgb in color_stops:
                elevation = min_elevation + ratio * (max_elevation - min_elevation)
                f.write(f"{elevation} {rgb}\\n")
        
        print(f"   🎨 Color table created: {len(color_stops)} color stops")
        
        # Generate color relief using GDAL
        result = gdal.DEMProcessing(
            destName=output_path,
            srcDS=input_dtm,
            processing="color-relief",
            colorFilename=color_table_path,
            format="GTiff"
        )
        
        if result is None:
            raise RuntimeError("GDAL color relief generation failed")
        
        processing_time = time.time() - start_time
        output_size = os.path.getsize(output_path)
        print(f"✅ Color relief generated in {processing_time:.2f} seconds: {output_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Color relief generation failed: {e}")
        return False

def create_tint_overlay(color_relief_path, rgb_composite_path, output_path):
    """Create tint overlay by combining color relief with RGB composite."""
    print(f"\\n🎭 Creating tint overlay...")
    print(f"   🎨 Color relief: {os.path.basename(color_relief_path)}")
    print(f"   🌈 RGB composite: {os.path.basename(rgb_composite_path)}")
    print(f"   📤 Output: {os.path.basename(output_path)}")
    
    start_time = time.time()
    
    try:
        # Read color relief (RGB)
        ds_color = gdal.Open(color_relief_path)
        if ds_color is None:
            raise FileNotFoundError(f"Color relief not found: {color_relief_path}")
        
        color = ds_color.ReadAsArray().astype(np.float32)  # shape (bands, H, W)
        geo = ds_color.GetGeoTransform()
        proj = ds_color.GetProjection()
        ds_color = None
        
        # Ensure 3-band format
        if color.ndim == 2:
            color = np.stack([color, color, color])
        
        # Read RGB composite
        ds_rgb = gdal.Open(rgb_composite_path)
        if ds_rgb is None:
            raise FileNotFoundError(f"RGB composite not found: {rgb_composite_path}")
        
        rgb = ds_rgb.ReadAsArray().astype(np.float32)
        ds_rgb = None
        
        # Convert RGB to intensity (grayscale)
        if rgb.ndim == 3:
            intensity = np.mean(rgb, axis=0)
        else:
            intensity = rgb
        
        # Normalize intensity to 0-1
        if intensity.max() > intensity.min():
            intensity_norm = (intensity - intensity.min()) / (intensity.max() - intensity.min())
        else:
            intensity_norm = np.zeros_like(intensity)
        
        # Apply tint by multiplying each color band by intensity
        tinted = color * intensity_norm
        tinted = np.clip(tinted, 0, 255).astype(np.uint8)
        
        # Save as 3-band GeoTIFF
        driver = gdal.GetDriverByName('GTiff')
        bands, h, w = tinted.shape
        
        out_ds = driver.Create(output_path, w, h, bands, gdal.GDT_Byte)
        out_ds.SetGeoTransform(geo)
        out_ds.SetProjection(proj)
        
        for i in range(bands):
            out_band = out_ds.GetRasterBand(i + 1)
            out_band.WriteArray(tinted[i])
            out_band.FlushCache()
        
        out_ds = None
        
        processing_time = time.time() - start_time
        output_size = os.path.getsize(output_path)
        print(f"✅ Tint overlay created in {processing_time:.2f} seconds: {output_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Tint overlay creation failed: {e}")
        return False

def generate_slope_relief(input_dtm, output_path):
    """Generate slope relief from DTM."""
    print(f"\\n📐 Generating slope relief...")
    print(f"   📥 Input DTM: {os.path.basename(input_dtm)}")
    print(f"   📤 Output: {os.path.basename(output_path)}")
    
    start_time = time.time()
    
    try:
        # Generate slope using GDAL
        result = gdal.DEMProcessing(
            destName=output_path,
            srcDS=input_dtm,
            processing="slope",
            format="GTiff"
        )
        
        if result is None:
            raise RuntimeError("GDAL slope generation failed")
        
        processing_time = time.time() - start_time
        output_size = os.path.getsize(output_path)
        print(f"✅ Slope relief generated in {processing_time:.2f} seconds: {output_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Slope relief generation failed: {e}")
        return False

def create_slope_overlay(tint_overlay_path, slope_relief_path, output_path, beta=0.5):
    """Create final blend by combining tint overlay with slope relief."""
    print(f"\\n🏔️ Creating final slope overlay...")
    print(f"   🎭 Tint overlay: {os.path.basename(tint_overlay_path)}")
    print(f"   📐 Slope relief: {os.path.basename(slope_relief_path)}")
    print(f"   📤 Output: {os.path.basename(output_path)}")
    print(f"   ⚖️ Blend factor (beta): {beta}")
    
    start_time = time.time()
    
    try:
        # Read tint overlay
        ds_tint = gdal.Open(tint_overlay_path)
        if ds_tint is None:
            raise FileNotFoundError(f"Tint overlay not found: {tint_overlay_path}")
        
        tint = ds_tint.ReadAsArray().astype(np.float32) / 255.0
        geo = ds_tint.GetGeoTransform()
        proj = ds_tint.GetProjection()
        ds_tint = None
        
        # Read slope relief
        ds_slope = gdal.Open(slope_relief_path)
        if ds_slope is None:
            raise FileNotFoundError(f"Slope relief not found: {slope_relief_path}")
        
        slope = ds_slope.ReadAsArray().astype(np.float32) / 255.0
        ds_slope = None
        
        # Ensure slope matches tint dimensions
        if slope.ndim == 2 and tint.ndim == 3:
            slope = np.stack([slope, slope, slope])
        
        if tint.shape != slope.shape:
            raise ValueError("Tint overlay and slope relief dimensions do not match")
        
        # Blend: final = tint * (1 - beta) + slope * beta
        final = tint * (1 - beta) + slope * beta
        final = np.clip(final * 255, 0, 255).astype(np.uint8)
        
        # Save as 3-band GeoTIFF
        driver = gdal.GetDriverByName('GTiff')
        if final.ndim == 3:
            bands, h, w = final.shape
        else:
            h, w = final.shape
            bands = 1
            final = final.reshape(1, h, w)
        
        out_ds = driver.Create(output_path, w, h, bands, gdal.GDT_Byte)
        out_ds.SetGeoTransform(geo)
        out_ds.SetProjection(proj)
        
        for i in range(bands):
            out_band = out_ds.GetRasterBand(i + 1)
            out_band.WriteArray(final[i])
            out_band.FlushCache()
        
        out_ds = None
        
        processing_time = time.time() - start_time
        output_size = os.path.getsize(output_path)
        print(f"✅ Final slope overlay created in {processing_time:.2f} seconds: {output_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Slope overlay creation failed: {e}")
        return False

def convert_tiff_to_png(tiff_path, png_path):
    """Convert TIFF to PNG for visualization."""
    print(f"🖼️ Converting {os.path.basename(tiff_path)} to PNG...")
    
    start_time = time.time()
    
    try:
        # Use GDAL translate for conversion
        ds = gdal.Translate(png_path, tiff_path, format='PNG')
        if ds is None:
            return False
        ds = None
        
        if not os.path.exists(png_path):
            return False
        
        processing_time = time.time() - start_time
        output_size = os.path.getsize(png_path)
        print(f"   ✅ PNG created in {processing_time:.2f} seconds: {output_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ PNG conversion failed: {e}")
        return False

def analyze_raster_info(raster_path):
    """Analyze and display raster information."""
    try:
        ds = gdal.Open(raster_path)
        if ds is None:
            return None
        
        width = ds.RasterXSize
        height = ds.RasterYSize
        bands = ds.RasterCount
        
        info = {
            'width': width,
            'height': height,
            'bands': bands,
            'projection': ds.GetProjection(),
            'geotransform': ds.GetGeoTransform()
        }
        
        ds = None
        return info
        
    except Exception as e:
        print(f"⚠️ Failed to analyze raster {raster_path}: {e}")
        return None

def run_complete_laz_pipeline():
    """Run the complete LAZ processing pipeline test."""
    print(f"\\n{'='*80}")
    print(f"🧪 COMPLETE LAZ PROCESSING PIPELINE TEST")
    print(f"{'='*80}")
    
    overall_start_time = time.time()
    
    try:
        # Step 1: Setup environment
        setup_test_environment()
        
        # Step 2: Generate DTM
        print(f"\\n{'='*60}")
        print(f"🏔️ STEP 1: DTM GENERATION")
        print(f"{'='*60}")
        
        pipeline = load_and_modify_dtm_pipeline()
        dtm_success = generate_dtm_with_pdal(pipeline)
        if not dtm_success:
            raise RuntimeError("DTM generation failed")
        
        # Step 3: Load hillshade configuration
        print(f"\\n{'='*60}")
        print(f"🌄 STEP 2: MULTIPLE HILLSHADE GENERATION")
        print(f"{'='*60}")
        
        hillshade_config = load_hillshade_config()
        
        # Generate the three hillshades for RGB channels
        hillshade_outputs = {}
        for hs_def in hillshade_config:
            if hs_def["name"] == "hs_red":
                output_path = HS_RED_OUTPUT
            elif hs_def["name"] == "hs_green":
                output_path = HS_GREEN_OUTPUT
            elif hs_def["name"] == "hs_blue":
                output_path = HS_BLUE_OUTPUT
            else:
                continue
                
            success = generate_hillshade(
                DTM_OUTPUT_PATH, 
                output_path,
                hs_def["azimuth"],
                hs_def["altitude"]
            )
            
            if not success:
                raise RuntimeError(f"Hillshade generation failed for {hs_def['name']}")
            
            hillshade_outputs[hs_def["name"]] = output_path
        
        # Step 4: Create RGB composite
        print(f"\\n{'='*60}")
        print(f"🌈 STEP 3: RGB COMPOSITE CREATION")
        print(f"{'='*60}")
        
        rgb_success = create_rgb_composite(
            HS_RED_OUTPUT, HS_GREEN_OUTPUT, HS_BLUE_OUTPUT, RGB_COMPOSITE_OUTPUT
        )
        if not rgb_success:
            raise RuntimeError("RGB composite creation failed")
        
        # Step 5: Generate color relief
        print(f"\\n{'='*60}")
        print(f"🎨 STEP 4: COLOR RELIEF GENERATION")
        print(f"{'='*60}")
        
        color_relief_success = generate_color_relief(DTM_OUTPUT_PATH, COLOR_RELIEF_OUTPUT)
        if not color_relief_success:
            raise RuntimeError("Color relief generation failed")
        
        # Step 6: Create tint overlay
        print(f"\\n{'='*60}")
        print(f"🎭 STEP 5: TINT OVERLAY CREATION")
        print(f"{'='*60}")
        
        tint_success = create_tint_overlay(COLOR_RELIEF_OUTPUT, RGB_COMPOSITE_OUTPUT, TINT_OVERLAY_OUTPUT)
        if not tint_success:
            raise RuntimeError("Tint overlay creation failed")
        
        # Step 7: Generate slope relief
        print(f"\\n{'='*60}")
        print(f"📐 STEP 6: SLOPE RELIEF GENERATION")
        print(f"{'='*60}")
        
        slope_success = generate_slope_relief(DTM_OUTPUT_PATH, SLOPE_RELIEF_OUTPUT)
        if not slope_success:
            raise RuntimeError("Slope relief generation failed")
        
        # Step 8: Create final slope overlay
        print(f"\\n{'='*60}")
        print(f"🏔️ STEP 7: FINAL SLOPE OVERLAY BLEND")
        print(f"{'='*60}")
        
        final_blend_success = create_slope_overlay(TINT_OVERLAY_OUTPUT, SLOPE_RELIEF_OUTPUT, FINAL_BLEND_OUTPUT)
        if not final_blend_success:
            raise RuntimeError("Final slope overlay creation failed")
        
        # Step 9: Convert all to PNG
        print(f"\\n{'='*60}")
        print(f"🖼️ STEP 8: PNG CONVERSION")
        print(f"{'='*60}")
        
        png_conversions = [
            (DTM_OUTPUT_PATH, PNG_OUTPUTS['dtm']),
            (HS_RED_OUTPUT, PNG_OUTPUTS['hs_red']),
            (HS_GREEN_OUTPUT, PNG_OUTPUTS['hs_green']),
            (HS_BLUE_OUTPUT, PNG_OUTPUTS['hs_blue']),
            (RGB_COMPOSITE_OUTPUT, PNG_OUTPUTS['rgb_composite']),
            (COLOR_RELIEF_OUTPUT, PNG_OUTPUTS['color_relief']),
            (TINT_OVERLAY_OUTPUT, PNG_OUTPUTS['tint_overlay']),
            (SLOPE_RELIEF_OUTPUT, PNG_OUTPUTS['slope_relief']),
            (FINAL_BLEND_OUTPUT, PNG_OUTPUTS['final_blend'])
        ]
        
        png_success_count = 0
        for tiff_path, png_path in png_conversions:
            if os.path.exists(tiff_path):
                if convert_tiff_to_png(tiff_path, png_path):
                    png_success_count += 1
        
        # Final summary
        total_time = time.time() - overall_start_time
        
        print(f"\\n{'='*80}")
        print(f"🎉 COMPLETE LAZ PIPELINE TEST SUCCESSFUL!")
        print(f"{'='*80}")
        print(f"⏱️ Total processing time: {total_time:.2f} seconds")
        print(f"\\n📊 PROCESSING RESULTS:")
        
        # Analyze each output
        outputs_to_analyze = [
            ("DTM", DTM_OUTPUT_PATH),
            ("Hillshade 315° (Red)", HS_RED_OUTPUT),
            ("Hillshade 45° (Green)", HS_GREEN_OUTPUT), 
            ("Hillshade 135° (Blue)", HS_BLUE_OUTPUT),
            ("RGB Composite", RGB_COMPOSITE_OUTPUT),
            ("Color Relief", COLOR_RELIEF_OUTPUT),
            ("Tint Overlay", TINT_OVERLAY_OUTPUT),
            ("Slope Relief", SLOPE_RELIEF_OUTPUT),
            ("Final Blend", FINAL_BLEND_OUTPUT)
        ]
        
        for name, path in outputs_to_analyze:
            if os.path.exists(path):
                size = os.path.getsize(path)
                info = analyze_raster_info(path)
                if info:
                    print(f"   ✅ {name}: {info['width']}x{info['height']} pixels, {info['bands']} bands, {size:,} bytes")
                else:
                    print(f"   ✅ {name}: {size:,} bytes")
            else:
                print(f"   ❌ {name}: File not found")
        
        print(f"\\n🖼️ PNG CONVERSIONS: {png_success_count}/{len(png_conversions)} successful")
        
        print(f"\\n📁 All output files located in: {TEST_OUTPUT_DIR}")
        
        print(f"\\n🔄 WORKFLOW VERIFICATION:")
        print(f"   ✅ LAZ → DTM: Complete")
        print(f"   ✅ DTM → 3 Hillshades (315°, 45°, 135°): Complete")
        print(f"   ✅ 3 Hillshades → RGB Composite: Complete")
        print(f"   ✅ DTM → Color Relief: Complete")
        print(f"   ✅ Color Relief + RGB → Tint Overlay: Complete")
        print(f"   ✅ DTM → Slope Relief: Complete")
        print(f"   ✅ Tint + Slope → Final Blend: Complete")
        print(f"   ✅ All → PNG Visualizations: {png_success_count}/{len(png_conversions)}")
        
        return True
        
    except Exception as e:
        total_time = time.time() - overall_start_time
        print(f"\\n{'='*80}")
        print(f"❌ COMPLETE LAZ PIPELINE TEST FAILED!")
        print(f"{'='*80}")
        print(f"⏱️ Time before failure: {total_time:.2f} seconds")
        print(f"💥 Error: {e}")
        return False

if __name__ == "__main__":
    success = run_complete_laz_pipeline()
    sys.exit(0 if success else 1)
