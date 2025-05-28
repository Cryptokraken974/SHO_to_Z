from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import glob

from .convert import convert_geotiff_to_png_base64
from .processing import laz_to_dem, dtm, hillshade, slope, aspect, color_relief, tri, tpi, roughness

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
