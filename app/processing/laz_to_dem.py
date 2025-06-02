# filepath: /Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/app/processing/laz_to_dem.py
import pdal
import json
import os
import time
from pathlib import Path
from typing import Tuple, Dict, Any

def create_dem_fallback_pipeline(input_file: str, output_file: str, resolution: float = 1.0) -> Dict[str, Any]:
    """
    Create fallback DEM pipeline when JSON pipeline is not available
    """
    return {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": input_file
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

def laz_to_dem(input_file: str) -> str:
    """
    Convert LAZ file to DEM (Digital Elevation Model)
    
    Args:
        input_file: Path to the input LAZ file
        
    Returns:
        Path to the generated TIF file
    """
    print(f"\n�� LAZ_TO_DEM: Starting conversion for {input_file}")
    start_time = time.time()
    
    # Extract region name from the file path structure
    # Path structure: input/<region_name>/lidar/<filename> or input/<region_name>/<filename>
    input_path = Path(input_file)
    if "lidar" in input_path.parts:
        # File is in lidar subfolder: extract parent's parent as region name
        region_name = input_path.parts[input_path.parts.index("input") + 1]
    else:
        # File is directly in input folder: extract parent as region name
        region_name = input_path.parent.name if input_path.parent.name != "input" else os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory structure: output/<region_name>/DEM/
    output_dir = os.path.join("output", region_name, "DEM")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename: <region_name>_DEM.tif
    output_filename = f"{region_name}_DEM.tif"
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
    Convert LAZ file to DEM using PDAL
    
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
    
    # Try JSON pipeline first, then fall back to hardcoded pipeline
    json_pipeline_path = os.path.join(os.path.dirname(__file__), "pipelines_json", "laz_to_dem.json")
    
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
            pipeline_str = pipeline_str.replace("output/default_DEM.tif", output_file)
            pipeline_str = pipeline_str.replace("DEFAULT_RESOLUTION", str(resolution))
            pipeline_config = json.loads(pipeline_str)
            
            print(f"📋 Using JSON pipeline configuration")
            pipeline = pdal.Pipeline(json.dumps(pipeline_config))
            
            # Execute pipeline
            pipeline.execute()
            
            if os.path.exists(output_file):
                success = True
                message = f"DEM generated successfully using JSON pipeline: {output_file}"
                print(f"✅ {message}")
            else:
                raise Exception("Output file was not created")
                
        except Exception as e:
            print(f"⚠️ JSON pipeline failed: {str(e)}")
            print(f"🔄 Falling back to hardcoded pipeline...")
    
    # Fall back to hardcoded pipeline if JSON failed or doesn't exist
    if not success:
        try:
            print(f"🔄 Using hardcoded DEM pipeline...")
            pipeline_config = create_dem_fallback_pipeline(input_file, output_file, resolution)
            pipeline = pdal.Pipeline(json.dumps(pipeline_config))
            
            # Execute pipeline
            pipeline.execute()
            
            if os.path.exists(output_file):
                success = True
                message = f"DEM generated successfully using hardcoded pipeline: {output_file}"
                print(f"✅ {message}")
            else:
                raise Exception("Output file was not created")
                
        except Exception as e:
            success = False
            message = f"Both JSON and hardcoded pipelines failed: {str(e)}"
            print(f"❌ {message}")
    
    return success, message
