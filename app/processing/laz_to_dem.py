import pdal
import json
import os
import time
from typing import Tuple

def laz_to_dem(input_file: str) -> str:
    """
    Convert LAZ file to DEM (Digital Elevation Model)
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated TIF file
    """
    print(f"\n🚀 LAZ_TO_DEM: Starting conversion for {input_file}")
    start_time = time.time()
    
    # Extract the base name without path and extension
    laz_basename = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory structure: output/<laz_basename>/
    output_dir = os.path.join("output", laz_basename)
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <laz_basename>_DEM.tif
    output_filename = f"{laz_basename}_DEM.tif"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Output file: {output_path}")
    
    # Set default resolution
    resolution = 1.0
    
    # Call the conversion function with detailed logging
    success, message = convert_las_to_dem(input_file, output_path, resolution)
    
    processing_time = time.time() - start_time
    
    if success:
        print(f"✅ DEM conversion completed successfully in {processing_time:.2f} seconds")
        print(f"📊 Message: {message}")
        return output_path
    else:
        print(f"❌ DEM conversion failed after {processing_time:.2f} seconds")
        print(f"❌ Error: {message}")
        raise Exception(f"DEM conversion failed: {message}")

def convert_las_to_dem(input_file: str, output_file: str, resolution: float = 1.0) -> Tuple[bool, str]:
    """
    Convert LAZ file to DEM using PDAL with comprehensive logging
    
    Args:
        input_file: Path to the input LAZ file
        output_file: Path to the output TIF file
        resolution: Grid resolution for DEM generation
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    print(f"\n{'='*60}")
    print(f"🎯 PDAL LAZ TO DEM CONVERSION")
    print(f"{'='*60}")
    print(f"📁 Input LAZ file: {input_file}")
    print(f"📁 Output TIF file: {output_file}")
    print(f"📏 Resolution: {resolution} units")
    print(f"🕐 Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Validate input file
    print(f"\n🔍 Validating input file...")
    if not os.path.exists(input_file):
        error_msg = f"Input file not found: {input_file}"
        print(f"❌ {error_msg}")
        return False, error_msg
    
    file_size = os.path.getsize(input_file)
    print(f"✅ Input file validated")
    print(f"📊 File size: {file_size:,} bytes ({file_size / (1024**2):.2f} MB)")
    
    # Create PDAL pipeline
    print(f"\n🔧 Creating PDAL pipeline...")
    pipeline = {
        "pipeline": [
            input_file,
            {
                "type": "writers.gdal",
                "filename": output_file,
                "resolution": resolution,
                "output_type": "mean",
                "nodata": -9999,
                "gdaldriver": "GTiff"
            }
        ]
    }
    
    print(f"🗂️ GDAL Writer Parameters:")
    print(f"   📄 Output file: {output_file}")
    print(f"   📏 Resolution: {resolution} units")
    print(f"   📊 Output type: mean")
    print(f"   🚫 NoData value: -9999")
    print(f"   💾 GDAL driver: GTiff")
    
    print(f"\n⚙️ Full Pipeline Configuration:")
    pipeline_formatted = json.dumps(pipeline, indent=4)
    print(f"{pipeline_formatted}")
    
    # Execute PDAL pipeline
    print(f"\n🚀 Executing PDAL pipeline...")
    pipeline_json = json.dumps(pipeline)
    pdal_pipeline = pdal.Pipeline(pipeline_json)
    
    try:
        print(f"   🔄 Running PDAL execution...")
        execution_start = time.time()
        
        count = pdal_pipeline.execute()
        
        execution_time = time.time() - execution_start
        print(f"   ✅ PDAL execution completed in {execution_time:.2f} seconds")
        print(f"   📊 Total points processed: {count:,}")
        
        # Validate output file
        print(f"\n🔍 Validating output file...")
        if os.path.exists(output_file):
            output_size = os.path.getsize(output_file)
            print(f"✅ Output file created successfully")
            print(f"📊 Output file size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
            
            # Additional file info
            print(f"📄 Output file path: {os.path.abspath(output_file)}")
            
            success_msg = f"DEM generated successfully at {output_file}"
            print(f"✅ {success_msg}")
            print(f"{'='*60}\n")
            
            return True, success_msg
        else:
            error_msg = "Output file was not created"
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg
            
    except RuntimeError as e:
        error_msg = f"PDAL execution failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Error type: RuntimeError")
        print(f"❌ Full error: {str(e)}")
        print(f"{'='*60}\n")
        return False, error_msg
    
    except Exception as e:
        error_msg = f"Unexpected error during PDAL execution: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Full error: {str(e)}")
        print(f"{'='*60}\n")
        return False, error_msg