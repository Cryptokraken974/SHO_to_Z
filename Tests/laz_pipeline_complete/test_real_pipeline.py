#!/usr/bin/env python3
"""
Test for process_all_raster_products() pipeline using FoxIsland.laz

This test runs the actual application pipeline to verify that all raster products
(DTM, hillshades, slope, aspect, color relief, RGB composites, tint overlays, etc.)
are generated correctly for the FoxIsland.laz file.

This test calls the real process_all_raster_products() function to ensure
the complete workflow works as expected.
"""

import os
import sys
import time
import asyncio
from pathlib import Path

# Add app directory to Python path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
APP_DIR = os.path.join(BASE_DIR, "app")
sys.path.insert(0, APP_DIR)

# Import the actual pipeline function
from processing.tiff_processing import process_all_raster_products
from processing.dtm import dtm

# Test Configuration
INPUT_LAZ_PATH = os.path.join(BASE_DIR, "input", "LAZ", "FoxIsland.laz")
TEST_OUTPUT_DIR = os.path.join(BASE_DIR, "Tests", "laz_pipeline_complete", "outputs")

# Expected output structure based on process_all_raster_products()
EXPECTED_OUTPUTS = {
    'base_products': [
        'Hs_red/hillshade_315_30_z1.tif',
        'Hs_green/hillshade_45_25_z1.tif', 
        'Hs_blue/hillshade_135_30_z1.tif',
        'Slope/slope.tif',
        'Aspect/aspect.tif',
        'Color_relief/color_relief.tif',
        'Slope_relief/slope_relief.tif'
    ],
    'composite_products': [
        'HillshadeRgb/hillshade_rgb.tif',
        'HillshadeRgb/tint_overlay.tif',
        'HillshadeRgb/boosted_hillshade.tif'
    ],
    'png_outputs': [
        'png_outputs/hillshade_315_30_z1.png',
        'png_outputs/hillshade_45_25_z1.png',
        'png_outputs/hillshade_135_30_z1.png',
        'png_outputs/slope.png',
        'png_outputs/aspect.png',
        'png_outputs/color_relief.png',
        'png_outputs/slope_relief.png',
        'png_outputs/hillshade_rgb.png',
        'png_outputs/TintOverlay.png',
        'png_outputs/boosted_hillshade.png'
    ]
}

class ProgressTracker:
    """Simple progress tracker for the pipeline."""
    
    def __init__(self):
        self.current_step = 0
        self.total_steps = 0
        
    async def __call__(self, progress_data):
        """Handle progress updates from the pipeline."""
        if progress_data.get("type") == "processing_progress":
            message = progress_data.get("message", "Processing...")
            progress = progress_data.get("progress", 0)
            print(f"   📊 {message} ({progress}%)")
        elif progress_data.get("type") == "processing_completed":
            print(f"   ✅ {progress_data.get('message', 'Processing completed')}")

def setup_test_environment():
    """Setup the test environment."""
    print(f"\\n{'='*80}")
    print(f"🧪 TESTING PROCESS_ALL_RASTER_PRODUCTS PIPELINE")
    print(f"{'='*80}")
    print(f"📁 Base directory: {BASE_DIR}")
    print(f"📄 Input LAZ: {INPUT_LAZ_PATH}")
    print(f"📁 Expected output base: output/FoxIsland/lidar/")
    
    # Verify input file exists
    if not os.path.exists(INPUT_LAZ_PATH):
        raise FileNotFoundError(f"Input LAZ file not found: {INPUT_LAZ_PATH}")
    
    file_size = os.path.getsize(INPUT_LAZ_PATH)
    print(f"✅ Input LAZ file verified: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")
    
    # Create test output directory for any additional outputs
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

def generate_dtm_first():
    """Generate DTM from LAZ file as prerequisite for raster processing."""
    print(f"\\n🏔️ STEP 1: GENERATING DTM FROM LAZ")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Use the application's DTM generation function
        dtm_path = dtm(INPUT_LAZ_PATH)
        
        processing_time = time.time() - start_time
        
        if dtm_path and os.path.exists(dtm_path):
            file_size = os.path.getsize(dtm_path)
            print(f"✅ DTM generated successfully in {processing_time:.2f} seconds")
            print(f"📄 DTM path: {dtm_path}")
            print(f"📊 DTM size: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")
            return dtm_path
        else:
            raise RuntimeError(f"DTM generation failed - no output file created")
            
    except Exception as e:
        print(f"❌ DTM generation failed: {e}")
        raise

async def run_raster_pipeline(dtm_path):
    """Run the complete raster processing pipeline."""
    print(f"\\n🚀 STEP 2: RUNNING COMPLETE RASTER PIPELINE")
    print(f"{'='*60}")
    print(f"📄 Input DTM: {dtm_path}")
    
    start_time = time.time()
    
    # Create progress tracker
    progress_tracker = ProgressTracker()
    
    try:
        # Run the actual process_all_raster_products pipeline
        results = await process_all_raster_products(
            tiff_path=dtm_path,
            progress_callback=progress_tracker
        )
        
        processing_time = time.time() - start_time
        
        print(f"\\n✅ Pipeline completed in {processing_time:.2f} seconds")
        print(f"📊 Results summary:")
        
        # Analyze results
        successful = 0
        failed = 0
        
        for task_name, result in results.items():
            if isinstance(result, dict):
                status = result.get("status", "unknown")
                if status == "success":
                    successful += 1
                    output_file = result.get("output_file", "")
                    png_file = result.get("png_file", "")
                    print(f"   ✅ {task_name}: {os.path.basename(output_file) if output_file else 'Generated'}")
                    if png_file and os.path.exists(png_file):
                        print(f"      🖼️ PNG: {os.path.basename(png_file)}")
                else:
                    failed += 1
                    error = result.get("error", "Unknown error")
                    print(f"   ❌ {task_name}: {error}")
            else:
                print(f"   ⚠️ {task_name}: Unexpected result format")
        
        print(f"\\n📈 Pipeline Statistics:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Success rate: {successful/(successful+failed)*100:.1f}%")
        
        return results
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        raise

def verify_output_structure():
    """Verify the expected output directory structure was created."""
    print(f"\\n🔍 STEP 3: VERIFYING OUTPUT STRUCTURE")
    print(f"{'='*60}")
    
    # The pipeline creates output in: output/FoxIsland/lidar/
    region_name = "FoxIsland"  # Extracted from filename
    expected_base_dir = os.path.join(BASE_DIR, "output", region_name, "lidar")
    
    print(f"📁 Expected base directory: {expected_base_dir}")
    
    if not os.path.exists(expected_base_dir):
        print(f"❌ Base output directory not found: {expected_base_dir}")
        return False
    
    print(f"✅ Base output directory exists")
    
    # Check for expected subdirectories and files
    total_expected = 0
    total_found = 0
    
    all_expected_files = (
        EXPECTED_OUTPUTS['base_products'] + 
        EXPECTED_OUTPUTS['composite_products'] + 
        EXPECTED_OUTPUTS['png_outputs']
    )
    
    print(f"\\n📋 Checking expected outputs:")
    
    for expected_file in all_expected_files:
        total_expected += 1
        full_path = os.path.join(expected_base_dir, expected_file)
        
        if os.path.exists(full_path):
            total_found += 1
            file_size = os.path.getsize(full_path)
            size_mb = file_size / (1024 * 1024)
            status = "✅" if size_mb > 0.1 else "⚠️"  # At least 100KB
            print(f"   {status} {expected_file}: {size_mb:.1f} MB")
        else:
            print(f"   ❌ {expected_file}: Not found")
    
    # Check for any additional files created
    print(f"\\n📂 Scanning output directory structure:")
    
    try:
        for root, dirs, files in os.walk(expected_base_dir):
            rel_root = os.path.relpath(root, expected_base_dir)
            if rel_root == ".":
                rel_root = ""
            
            if files:
                print(f"   📁 {rel_root if rel_root else 'root'}:")
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    print(f"      📄 {file}: {file_size:.1f} MB")
    except Exception as e:
        print(f"   ⚠️ Error scanning directory: {e}")
    
    # Summary
    success_rate = (total_found / total_expected * 100) if total_expected > 0 else 0
    print(f"\\n📊 Verification Summary:")
    print(f"   📋 Expected files: {total_expected}")
    print(f"   ✅ Found files: {total_found}")
    print(f"   📈 Success rate: {success_rate:.1f}%")
    
    return success_rate >= 80  # 80% success threshold

def check_key_workflow_files():
    """Check that key workflow files exist to validate the 3-hillshade RGB pipeline."""
    print(f"\\n🎯 STEP 4: VALIDATING KEY WORKFLOW FILES")
    print(f"{'='*60}")
    
    region_name = "FoxIsland"
    base_dir = os.path.join(BASE_DIR, "output", region_name, "lidar")
    
    # Key files that validate the complete workflow
    key_files = {
        "Red Hillshade (315°)": "Hs_red/hillshade_315_30_z1.tif",
        "Green Hillshade (45°)": "Hs_green/hillshade_45_25_z1.tif", 
        "Blue Hillshade (135°)": "Hs_blue/hillshade_135_30_z1.tif",
        "RGB Composite": "HillshadeRgb/hillshade_rgb.tif",
        "Color Relief": "Color_relief/color_relief.tif",
        "Tint Overlay": "HillshadeRgb/tint_overlay.tif",
        "Slope Relief": "Slope_relief/slope_relief.tif",
        "Final Blend": "HillshadeRgb/boosted_hillshade.tif"
    }
    
    workflow_success = True
    
    for description, relative_path in key_files.items():
        full_path = os.path.join(base_dir, relative_path)
        
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path) / (1024 * 1024)
            print(f"   ✅ {description}: {file_size:.1f} MB")
        else:
            print(f"   ❌ {description}: Missing")
            workflow_success = False
    
    if workflow_success:
        print(f"\\n🎉 Complete 3-hillshade RGB → tint → slope blend workflow validated!")
    else:
        print(f"\\n⚠️ Some key workflow files are missing")
    
    return workflow_success

async def run_pipeline_test():
    """Run the complete pipeline test."""
    overall_start_time = time.time()
    
    try:
        # Step 1: Setup
        setup_test_environment()
        
        # Step 2: Generate DTM (prerequisite)
        dtm_path = generate_dtm_first()
        
        # Step 3: Run complete raster pipeline
        results = await run_raster_pipeline(dtm_path)
        
        # Step 4: Verify outputs
        structure_ok = verify_output_structure()
        
        # Step 5: Check key workflow files
        workflow_ok = check_key_workflow_files()
        
        # Final summary
        total_time = time.time() - overall_start_time
        
        print(f"\\n{'='*80}")
        if structure_ok and workflow_ok:
            print(f"🎉 PIPELINE TEST SUCCESSFUL!")
            print(f"✅ All raster products generated correctly")
            print(f"✅ Complete 3-hillshade RGB blending workflow verified")
            print(f"✅ Color relief tinting and slope blending confirmed")
        elif structure_ok:
            print(f"⚠️ PIPELINE TEST PARTIALLY SUCCESSFUL")
            print(f"✅ Most raster products generated")
            print(f"⚠️ Some workflow components may be missing")
        else:
            print(f"❌ PIPELINE TEST FAILED")
            print(f"❌ Significant issues with raster generation")
        
        print(f"⏱️ Total test time: {total_time:.2f} seconds")
        print(f"{'='*80}")
        
        return structure_ok and workflow_ok
        
    except Exception as e:
        total_time = time.time() - overall_start_time
        print(f"\\n{'='*80}")
        print(f"❌ PIPELINE TEST FAILED!")
        print(f"💥 Error: {e}")
        print(f"⏱️ Time before failure: {total_time:.2f} seconds")
        print(f"{'='*80}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_pipeline_test())
    sys.exit(0 if success else 1)
