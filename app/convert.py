import base64
import io
from PIL import Image

def tif_to_png_base64(path: str) -> str:
    """Convert TIF image to PNG and return base64 string."""
    with Image.open(path) as img:
        with io.BytesIO() as buf:
            img.save(buf, format='PNG')
            return base64.b64encode(buf.getvalue()).decode('utf-8')
