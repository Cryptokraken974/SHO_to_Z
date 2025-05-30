from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import glob
import base64

from .convert import convert_geotiff_to_png_base64
from .processing import laz_to_dem, dtm, dsm, chm, hillshade, slope, aspect, color_relief, tri, tpi, roughness

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    with open("frontend/index.html") as f:
        return f.read()

@app.get("/api/list-laz-files")
async def list_laz_files():
    """List all LAZ files in the input directory"""
    input_dir = "input"
    
    # Create input directory if it doesn't exist
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        return {"files": []}
    
    # Find all LAZ files (including .laz and .copc.laz)
    laz_patterns = [
        os.path.join(input_dir, "**/*.laz"),
        os.path.join(input_dir, "**/*.LAZ"),
        os.path.join(input_dir, "**/*.copc.laz")
    ]
    
    files = []
    for pattern in laz_patterns:
        files.extend(glob.glob(pattern, recursive=True))
    
    # Convert to relative paths and remove duplicates
    relative_files = list(set([os.path.relpath(f) for f in files]))
    relative_files.sort()
    
    return {"files": relative_files}

# Utility to handle image generation endpoints
def handle_generation(generator):
    tif_path = generator.generate()
    image_b64 = convert_geotiff_to_png_base64(tif_path)
    return {"image": image_b64}

@app.post("/api/laz_to_dem")
async def api_laz_to_dem(input_file: str = Form(...)):
    """Convert LAZ to DEM"""
    print(f"\n🎯 API CALL: /api/laz_to_dem")
    print(f"📥 Input file: {input_file}")
    
    try:
        # Import the synchronous function
        from .processing.laz_to_dem import laz_to_dem
        
        # Call the synchronous function directly
        tif_path = laz_to_dem(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
            
    except Exception as e:
        print(f"❌ Error in api_laz_to_dem: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/dtm")
async def api_dtm(input_file: str = Form(...)):
    """Convert LAZ to DTM (ground points only)"""
    print(f"\n🎯 API CALL: /api/dtm")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = dtm(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_dtm: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/dsm")
async def api_dsm(input_file: str = Form(...)):
    """Convert LAZ to DSM (surface points)"""
    print(f"\n🎯 API CALL: /api/dsm")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = dsm(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_dsm: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/chm")
async def api_chm(input_file: str = Form(...)):
    """Generate CHM (Canopy Height Model) from LAZ file"""
    print(f"\n🎯 API CALL: /api/chm")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = chm(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_chm: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/hillshade")
async def api_hillshade(input_file: str = Form(...)):
    """Generate hillshade from LAZ file"""
    print(f"\n🎯 API CALL: /api/hillshade")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = hillshade(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_hillshade: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@app.post("/api/slope")
async def api_slope(input_file: str = Form(...)):
    """Generate slope from LAZ file"""
    print(f"\n🎯 API CALL: /api/slope")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = slope(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_slope: {str(e)}")
        raise

@app.post("/api/aspect")
async def api_aspect(input_file: str = Form(...)):
    """Generate aspect from LAZ file"""
    print(f"\n🎯 API CALL: /api/aspect")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = aspect(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_aspect: {str(e)}")
        raise

@app.post("/api/color_relief")
async def api_color_relief(input_file: str = Form(...)):
    """Generate color relief from LAZ file"""
    print(f"\n🎯 API CALL: /api/color_relief")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = color_relief(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_color_relief: {str(e)}")
        raise

@app.post("/api/tri")
async def api_tri(input_file: str = Form(...)):
    """Generate TRI from LAZ file"""
    print(f"\n🎯 API CALL: /api/tri")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = tri(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_tri: {str(e)}")
        raise

@app.post("/api/tpi")
async def api_tpi(input_file: str = Form(...)):
    """Generate TPI from LAZ file"""
    print(f"\n🎯 API CALL: /api/tpi")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = tpi(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_tpi: {str(e)}")
        raise

@app.post("/api/roughness")
async def api_roughness(input_file: str = Form(...)):
    """Generate roughness from LAZ file"""
    print(f"\n🎯 API CALL: /api/roughness")
    print(f"📥 Input file: {input_file}")
    
    try:
        tif_path = roughness(input_file)
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_roughness: {str(e)}")
        raise

@app.post("/api/chat")
async def api_chat(data: dict):
    prompt = data.get("prompt", "")
    model = data.get("model", "")
    # Placeholder response; integrate with real LLM here
    response = f"Model {model} says: {prompt}"
    return {"response": response}

@app.get("/api/overlay/{processing_type}/{filename}")
async def get_overlay_data(processing_type: str, filename: str):
    """Get overlay data for a processed image including bounds and base64 encoded image"""
    print(f"\n🗺️  API CALL: /api/overlay/{processing_type}/{filename}")
    
    try:
        from .geo_utils import get_image_overlay_data
        
        # Extract base filename (remove path and extension)
        base_filename = os.path.splitext(os.path.basename(filename))[0]
        if base_filename.endswith('.copc'):
            base_filename = base_filename[:-5]  # Remove .copc suffix
            
        print(f"📂 Base filename: {base_filename}")
        print(f"🔄 Processing type: {processing_type}")
        
        # Map API processing types to actual folder names
        type_mapping = {
            'laz_to_dem': 'DEM',
            'dtm': 'DTM',
            'hillshade': 'Hillshade',
            'slope': 'Slope',
            'aspect': 'Aspect',
            'color_relief': 'ColorRelief',
            'tri': 'TRI',
            'tpi': 'TPI',
            'roughness': 'Roughness'
        }
        
        # Get the actual folder name
        actual_processing_type = type_mapping.get(processing_type, processing_type.title())
        print(f"📁 Mapped processing type: {processing_type} -> {actual_processing_type}")
        
        overlay_data = get_image_overlay_data(base_filename, actual_processing_type)
        
        if not overlay_data:
            print(f"❌ No overlay data found for {base_filename}/{actual_processing_type}")
            # Debug: List available directories
            output_base = f"output/{base_filename}"
            if os.path.exists(output_base):
                available_dirs = [d for d in os.listdir(output_base) if os.path.isdir(os.path.join(output_base, d))]
                print(f"🔍 Available directories: {available_dirs}")
            else:
                print(f"🔍 Output directory doesn't exist: {output_base}")
            
            return JSONResponse(
                status_code=404, 
                content={"error": "Overlay data not found or could not extract coordinates"}
            )
            
        print(f"✅ Overlay data retrieved successfully")
        print(f"📍 Bounds: {overlay_data['bounds']}")
        
        return overlay_data
        
    except Exception as e:
        print(f"❌ Error getting overlay data: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get overlay data: {str(e)}"}
        )

@app.get("/api/test-overlay/{filename}")
async def get_test_overlay(filename: str):
    """Create a simple black overlay at the LAZ file coordinates for testing"""
    print(f"\n🧪 TEST OVERLAY: /api/test-overlay/{filename}")
    
    try:
        from PIL import Image, ImageDraw
        import io
        
        # Map known LAZ files to their approximate coordinates in WGS84
        laz_coordinates = {
            'FoxIsland.laz': {
                'center_lat': 44.4268,
                'center_lng': -68.2048,
                'size_deg': 0.01  # ~1km at this latitude
            },
            'OR_WizardIsland.laz': {
                'center_lat': 42.9446,
                'center_lng': -122.1090,
                'size_deg': 0.01  # ~1km at this latitude
            }
        }
        
        # Extract base filename
        base_filename = os.path.splitext(os.path.basename(filename))[0]
        if base_filename.endswith('.copc'):
            base_filename = base_filename[:-5]
            
        print(f"📂 Base filename: {base_filename}")
        
        # Find matching LAZ file
        matching_coords = None
        for laz_file, coords in laz_coordinates.items():
            if base_filename in laz_file or laz_file.replace('.laz', '') in base_filename:
                matching_coords = coords
                break
                
        if not matching_coords:
            print(f"❌ No coordinates found for {base_filename}")
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "No test coordinates available for this file"}
            )
            
        print(f"📍 Using coordinates: {matching_coords}")
        
        # Calculate bounds
        half_size = matching_coords['size_deg'] / 2
        bounds = {
            'north': matching_coords['center_lat'] + half_size,
            'south': matching_coords['center_lat'] - half_size,
            'east': matching_coords['center_lng'] + half_size,
            'west': matching_coords['center_lng'] - half_size,
            'center_lat': matching_coords['center_lat'],
            'center_lng': matching_coords['center_lng']
        }
        
        print(f"🗺️  Test bounds: {bounds}")
        
        # Create a simple black square image
        img_size = 200
        img = Image.new('RGBA', (img_size, img_size), (0, 0, 0, 128))  # Semi-transparent black
        
        # Add a red border for visibility
        draw = ImageDraw.Draw(img)
        border_width = 5
        draw.rectangle([0, 0, img_size-1, img_size-1], outline=(255, 0, 0, 255), width=border_width)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        print(f"✅ Created test overlay image ({len(image_data)} chars)")
        
        return {
            'success': True,
            'bounds': bounds,
            'image_data': image_data,
            'processing_type': 'test',
            'filename': base_filename
        }
        
    except Exception as e:
        print(f"❌ Error creating test overlay: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to create test overlay: {str(e)}"}
        )

@app.get("/api/pipelines/json")
async def list_json_pipelines():
    """List all available JSON pipelines"""
    print(f"\n🔧 API CALL: /api/pipelines/json")
    
    try:
        from .processing.json_processor import get_processor
        
        processor = get_processor()
        pipelines = processor.list_available_json_pipelines()
        
        print(f"✅ Found {len(pipelines)} JSON pipelines")
        
        return {
            "success": True,
            "pipelines": pipelines,
            "count": len(pipelines)
        }
        
    except Exception as e:
        print(f"❌ Error listing JSON pipelines: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "pipelines": []
        }

@app.get("/api/pipelines/json/{pipeline_name}")
async def get_json_pipeline_info(pipeline_name: str):
    """Get information about a specific JSON pipeline"""
    print(f"\n🔧 API CALL: /api/pipelines/json/{pipeline_name}")
    
    try:
        from .processing.json_processor import get_processor
        
        processor = get_processor()
        pipeline_info = processor.get_pipeline_info(pipeline_name)
        
        if pipeline_info:
            print(f"✅ Pipeline info retrieved for: {pipeline_name}")
            return {
                "success": True,
                "pipeline_name": pipeline_name,
                "pipeline": pipeline_info
            }
        else:
            print(f"❌ Pipeline not found: {pipeline_name}")
            return {
                "success": False,
                "error": f"Pipeline '{pipeline_name}' not found"
            }
        
    except Exception as e:
        print(f"❌ Error getting pipeline info: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/pipelines/toggle-json")
async def toggle_json_pipelines(data: dict):
    """Toggle JSON pipeline usage on/off"""
    print(f"\n🔧 API CALL: /api/pipelines/toggle-json")
    
    try:
        use_json = data.get("use_json", True)
        
        from .processing.json_processor import set_use_json_pipelines
        set_use_json_pipelines(use_json)
        
        print(f"✅ JSON pipeline usage set to: {use_json}")
        
        return {
            "success": True,
            "use_json_pipelines": use_json,
            "message": f"JSON pipelines {'enabled' if use_json else 'disabled'}"
        }
        
    except Exception as e:
        print(f"❌ Error toggling JSON pipelines: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


