#!/usr/bin/env python3
"""
Standalone Test Script for FoxIsland.laz Raster Generation

This script tests the complete raster generation workflow for FoxIsland.laz
to identify issues with PNG output directory structure and verify proper
output to the consolidated png_outputs directory.

Usage:
    python test_foxisland_raster_generation.py
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Import processing modules
from processing.dtm import dtm
from processing.dsm import dsm
from processing.hillshade import hillshade, hillshade_315_45_08
from processing.slope import slope
from processing.aspect import aspect
from processing.tri import tri
from processing.tpi import tpi
from processing.roughness import roughness
from convert import convert_geotiff_to_png
from geo_utils import find_png_files

# Configuration
LAZ_FILE_PATH = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ/FoxIsland.laz"
REGION_NAME = "FoxIsland"
BASE_OUTPUT_DIR = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output"

# Define processing functions to test
PROCESSING_FUNCTIONS = [
    ("DTM", dtm),
    ("DSM", dsm),
    ("Hillshade", hillshade),
    ("Hillshade 315-45-08", hillshade_315_45_08),
    ("Slope", slope),
    ("Aspect", aspect),
    ("TRI", tri),
    ("TPI", tpi),
    ("Roughness", roughness),
]

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*80}")
    print(f"🧪 {title}")
    print(f"{'='*80}")

def print_step(step_num, total_steps, description):
    """Print a formatted step"""
    print(f"\n📋 Step {step_num}/{total_steps}: {description}")
    print(f"{'—'*60}")

def verify_laz_file():
    """Verify the LAZ file exists and is readable"""
    print_step(1, 7, "Verifying LAZ File")
    
    if not os.path.exists(LAZ_FILE_PATH):
        print(f"❌ LAZ file not found: {LAZ_FILE_PATH}")
        return False
    
    file_size = os.path.getsize(LAZ_FILE_PATH)
    print(f"✅ LAZ file found: {LAZ_FILE_PATH}")
    print(f"📊 File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    # Check if file is readable
    try:
        with open(LAZ_FILE_PATH, 'rb') as f:
            f.read(1024)  # Read first KB to test accessibility
        print(f"✅ LAZ file is readable")
        return True
    except Exception as e:
        print(f"❌ Cannot read LAZ file: {e}")
        return False

def check_output_directories():
    """Check and create output directory structure"""
    print_step(2, 7, "Checking Output Directory Structure")
    
    region_output_dir = Path(BASE_OUTPUT_DIR) / REGION_NAME
    lidar_dir = region_output_dir / "lidar"
    png_outputs_dir = lidar_dir / "png_outputs"
    
    print(f"📁 Expected region output: {region_output_dir}")
    print(f"📁 Expected lidar directory: {lidar_dir}")
    print(f"📁 Expected PNG outputs directory: {png_outputs_dir}")
    
    # Create directories if they don't exist
    try:
        png_outputs_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created/verified PNG outputs directory: {png_outputs_dir}")
        
        # List current structure
        if region_output_dir.exists():
            print(f"\n📂 Current structure under {region_output_dir}:")
            for item in region_output_dir.rglob("*"):
                if item.is_dir():
                    print(f"   📁 {item.relative_to(region_output_dir)}/")
                else:
                    print(f"   📄 {item.relative_to(region_output_dir)}")
        else:
            print(f"📂 No existing output structure found for {REGION_NAME}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating directories: {e}")
        return False

async def test_raster_generation():
    """Test raster generation for all processing types"""
    print_step(3, 7, "Testing Raster Generation")
    
    results = {}
    
    for process_name, process_func in PROCESSING_FUNCTIONS:
        print(f"\n🔄 Processing {process_name}...")
        start_time = time.time()
        
        try:
            # Generate the raster
            tif_path = process_func(LAZ_FILE_PATH)
            elapsed = time.time() - start_time
            
            if os.path.exists(tif_path):
                file_size = os.path.getsize(tif_path)
                print(f"   ✅ Generated: {tif_path}")
                print(f"   📊 File size: {file_size:,} bytes")
                print(f"   ⏱️  Processing time: {elapsed:.2f} seconds")
                
                results[process_name] = {
                    "success": True,
                    "tif_path": tif_path,
                    "file_size": file_size,
                    "processing_time": elapsed
                }
            else:
                print(f"   ❌ TIF file not found: {tif_path}")
                results[process_name] = {"success": False, "error": "TIF file not generated"}
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ Processing failed: {e}")
            print(f"   ⏱️  Failed after: {elapsed:.2f} seconds")
            results[process_name] = {"success": False, "error": str(e), "processing_time": elapsed}
    
    return results

def test_png_conversion(raster_results):
    """Test PNG conversion for successfully generated TIFs"""
    print_step(4, 7, "Testing PNG Conversion")
    
    png_results = {}
    
    for process_name, result in raster_results.items():
        if not result.get("success"):
            print(f"⏩ Skipping {process_name} - TIF not available")
            continue
            
        print(f"\n🖼️  Converting {process_name} to PNG...")
        start_time = time.time()
        
        try:
            tif_path = result["tif_path"]
            png_path = convert_geotiff_to_png(tif_path)
            elapsed = time.time() - start_time
            
            if os.path.exists(png_path):
                file_size = os.path.getsize(png_path)
                print(f"   ✅ Generated PNG: {png_path}")
                print(f"   📊 File size: {file_size:,} bytes")
                print(f"   ⏱️  Conversion time: {elapsed:.2f} seconds")
                
                png_results[process_name] = {
                    "success": True,
                    "png_path": png_path,
                    "file_size": file_size,
                    "conversion_time": elapsed
                }
            else:
                print(f"   ❌ PNG file not found: {png_path}")
                png_results[process_name] = {"success": False, "error": "PNG file not generated"}
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ PNG conversion failed: {e}")
            print(f"   ⏱️  Failed after: {elapsed:.2f} seconds")
            png_results[process_name] = {"success": False, "error": str(e), "conversion_time": elapsed}
    
    return png_results

def test_png_discovery():
    """Test PNG file discovery using geo_utils"""
    print_step(5, 7, "Testing PNG File Discovery")
    
    print(f"🔍 Testing PNG discovery for region: {REGION_NAME}")
    
    try:
        # Test each processing type
        for process_name, _ in PROCESSING_FUNCTIONS:
            processing_type = process_name.lower().replace(" ", "_").replace("-", "_")
            print(f"\n🔎 Searching for {process_name} PNG files...")
            
            # Use geo_utils to find PNG files
            png_files = find_png_files(REGION_NAME, processing_type)
            
            if png_files:
                print(f"   ✅ Found {len(png_files)} PNG file(s):")
                for png_file in png_files:
                    file_size = os.path.getsize(png_file) if os.path.exists(png_file) else 0
                    print(f"      📄 {png_file} ({file_size:,} bytes)")
            else:
                print(f"   ⚠️  No PNG files found for {process_name}")
                
    except Exception as e:
        print(f"❌ PNG discovery failed: {e}")

def test_consolidated_png_outputs():
    """Test if PNGs are correctly saved to the consolidated png_outputs directory"""
    print_step(6, 7, "Testing Consolidated PNG Outputs")
    
    consolidated_dir = Path(BASE_OUTPUT_DIR) / REGION_NAME / "lidar" / "png_outputs"
    print(f"🔍 Checking consolidated PNG outputs directory: {consolidated_dir}")
    
    if not consolidated_dir.exists():
        print(f"❌ Consolidated PNG outputs directory not found: {consolidated_dir}")
        return False
    
    # Count expected PNGs (one for each successful processing type)
    expected_count = len(PROCESSING_FUNCTIONS)
    
    # Find all PNGs in the consolidated directory
    png_files = list(consolidated_dir.glob("*.png"))
    found_count = len(png_files)
    
    print(f"📊 Found {found_count}/{expected_count} expected PNG files in consolidated directory")
    
    # Check each processing type for consolidated PNG
    consolidated_results = {}
    for process_name, _ in PROCESSING_FUNCTIONS:
        processing_type = process_name.lower().replace(" ", "_").replace("-", "_")
        expected_pattern = f"{REGION_NAME}_elevation_{processing_type}.png"
        expected_path = consolidated_dir / expected_pattern
        
        if expected_path.exists():
            file_size = os.path.getsize(expected_path)
            print(f"   ✅ Found consolidated PNG for {process_name}: {expected_path.name} ({file_size:,} bytes)")
            consolidated_results[process_name] = {
                "success": True,
                "path": str(expected_path),
                "size": file_size
            }
        else:
            print(f"   ❌ Missing consolidated PNG for {process_name}: {expected_pattern}")
            consolidated_results[process_name] = {
                "success": False,
                "expected_path": str(expected_path)
            }
    
    # Check for worldfiles (.pgw) alongside PNGs
    worldfile_count = len(list(consolidated_dir.glob("*.pgw")))
    print(f"📊 Found {worldfile_count}/{found_count} worldfiles (.pgw) for the consolidated PNGs")
    
    success_rate = sum(1 for r in consolidated_results.values() if r.get("success")) / expected_count * 100
    print(f"📊 Consolidated PNG success rate: {success_rate:.1f}%")
    
    return consolidated_results

def generate_summary_report(raster_results, png_results, consolidated_results=None):
    """Generate a comprehensive summary report"""
    print_step(7, 7, "Summary Report")
    
    total_processes = len(PROCESSING_FUNCTIONS)
    successful_tifs = sum(1 for r in raster_results.values() if r.get("success"))
    successful_pngs = sum(1 for r in png_results.values() if r.get("success"))
    
    print(f"\n📊 PROCESSING SUMMARY")
    print(f"{'—'*40}")
    print(f"Total processing types tested: {total_processes}")
    print(f"Successful TIF generations: {successful_tifs}/{total_processes}")
    print(f"Successful PNG conversions: {successful_pngs}/{successful_tifs}")
    print(f"Overall success rate: {(successful_pngs / total_processes * 100):.1f}%")
    
    # TIF Results
    print(f"\n📊 TIF GENERATION RESULTS")
    print(f"{'—'*40}")
    for process_name, result in raster_results.items():
        status = "✅ SUCCESS" if result.get("success") else "❌ FAILED"
        time_str = f" ({result.get('processing_time', 0):.2f}s)" if 'processing_time' in result else ""
        print(f"{status:12} | {process_name:20} {time_str}")
        if not result.get("success") and "error" in result:
            print(f"             | Error: {result['error']}")
    
    # PNG Results
    if png_results:
        print(f"\n🖼️  PNG CONVERSION RESULTS")
        print(f"{'—'*40}")
        for process_name, result in png_results.items():
            status = "✅ SUCCESS" if result.get("success") else "❌ FAILED"
            time_str = f" ({result.get('conversion_time', 0):.2f}s)" if 'conversion_time' in result else ""
            print(f"{status:12} | {process_name:20} {time_str}")
            if not result.get("success") and "error" in result:
                print(f"             | Error: {result['error']}")
    
    # Output directory structure
    print(f"\n📁 OUTPUT DIRECTORY STRUCTURE")
    print(f"{'—'*40}")
    region_output_dir = Path(BASE_OUTPUT_DIR) / REGION_NAME
    if region_output_dir.exists():
        print(f"Region directory: {region_output_dir}")
        for item in sorted(region_output_dir.rglob("*")):
            if item.is_file():
                size = os.path.getsize(item)
                relative_path = item.relative_to(region_output_dir)
                print(f"  📄 {relative_path} ({size:,} bytes)")
            elif item != region_output_dir:
                relative_path = item.relative_to(region_output_dir)
                print(f"  📁 {relative_path}/")
    else:
        print("❌ No output directory created")
    
    # Check PNG outputs directory specifically
    png_outputs_dir = region_output_dir / "lidar" / "png_outputs"
    if png_outputs_dir.exists():
        png_files = list(png_outputs_dir.glob("*.png"))
        print(f"\n🖼️  PNG_OUTPUTS DIRECTORY ({png_outputs_dir})")
        print(f"{'—'*40}")
        if png_files:
            print(f"Found {len(png_files)} PNG files:")
            for png_file in sorted(png_files):
                size = os.path.getsize(png_file)
                print(f"  📄 {png_file.name} ({size:,} bytes)")
        else:
            print("📂 Directory exists but no PNG files found")
    else:
        print(f"\n⚠️  PNG_OUTPUTS DIRECTORY NOT FOUND")
        print(f"Expected: {png_outputs_dir}")
    
    # Consolidated PNG Results
    if consolidated_results is not None:
        print(f"\n📊 CONSOLIDATED PNG RESULTS")
        print(f"{'—'*40}")
        for process_name, result in consolidated_results.items():
            status = "✅ SUCCESS" if result.get("success") else "❌ FAILED"
            if result.get("success"):
                print(f"{status:12} | {process_name:20} - {result['path']}")
            else:
                print(f"{status:12} | {process_name:20} - Missing: {result.get('expected_path')}")
    
async def main():
    """Main test function"""
    print_header("FoxIsland.laz Raster Generation Test")
    print(f"🎯 Target LAZ file: {LAZ_FILE_PATH}")
    print(f"🏷️  Region name: {REGION_NAME}")
    print(f"📁 Base output directory: {BASE_OUTPUT_DIR}")
    
    # Step 1: Verify LAZ file
    if not verify_laz_file():
        print("\n❌ Test aborted: LAZ file verification failed")
        return False
    
    # Step 2: Check output directories
    if not check_output_directories():
        print("\n❌ Test aborted: Output directory setup failed")
        return False
    
    # Step 3: Test raster generation
    raster_results = await test_raster_generation()
    
    # Step 4: Test PNG conversion
    png_results = test_png_conversion(raster_results)
    
    # Step 5: Test PNG discovery
    test_png_discovery()
    
    # Step 6: Test consolidated PNG outputs
    consolidated_results = test_consolidated_png_outputs()
    
    # Step 7: Generate summary
    generate_summary_report(raster_results, png_results, consolidated_results)
    
    # Final assessment
    successful_processes = sum(1 for r in png_results.values() if r.get("success"))
    total_processes = len([r for r in raster_results.values() if r.get("success")])
    
    if successful_processes == total_processes and total_processes > 0:
        print(f"\n✅ TEST COMPLETED SUCCESSFULLY")
        print(f"All {successful_processes} processing types completed with PNG outputs")
        return True
    elif successful_processes > 0:
        print(f"\n⚠️  TEST PARTIALLY SUCCESSFUL")
        print(f"{successful_processes}/{total_processes} processing types completed")
        return True
    else:
        print(f"\n❌ TEST FAILED")
        print(f"No processing types completed successfully")
        return False

if __name__ == "__main__":
    print(f"🚀 Starting FoxIsland.laz Raster Generation Test...")
    print(f"⏰ Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    try:
        # Run the async test
        success = asyncio.run(main())
        
        elapsed = time.time() - start_time
        print(f"\n⏰ Total test time: {elapsed:.2f} seconds")
        
        if success:
            print(f"🎉 Test completed successfully!")
            sys.exit(0)
        else:
            print(f"⚠️  Test completed with issues")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n💥 Test failed with exception after {elapsed:.2f} seconds:")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
