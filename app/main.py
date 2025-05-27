from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .convert import tif_to_png_base64
from .processing import laz_to_dtm, hillshade, slope, aspect, color_relief, tri, tpi, roughness

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    with open("frontend/index.html") as f:
        return f.read()

# Utility to handle image generation endpoints
def handle_generation(generator):
    tif_path = generator.generate()
    image_b64 = tif_to_png_base64(tif_path)
    return {"image": image_b64}

@app.post("/api/laz_to_dtm")
async def api_laz_to_dtm():
    return handle_generation(laz_to_dtm)

@app.post("/api/hillshade")
async def api_hillshade():
    return handle_generation(hillshade)

@app.post("/api/slope")
async def api_slope():
    return handle_generation(slope)

@app.post("/api/aspect")
async def api_aspect():
    return handle_generation(aspect)

@app.post("/api/color_relief")
async def api_color_relief():
    return handle_generation(color_relief)

@app.post("/api/tri")
async def api_tri():
    return handle_generation(tri)

@app.post("/api/tpi")
async def api_tpi():
    return handle_generation(tpi)

@app.post("/api/roughness")
async def api_roughness():
    return handle_generation(roughness)

@app.post("/api/chat")
async def api_chat(data: dict):
    prompt = data.get("prompt", "")
    model = data.get("model", "")
    # Placeholder response; integrate with real LLM here
    response = f"Model {model} says: {prompt}"
    return {"response": response}
