from typing import Dict, Any, List, Optional
from .base_service import BaseService, SyncServiceMixin

class OpenAIService(BaseService, SyncServiceMixin):
    """Service for sending prompts and images to OpenAI and logging the request."""

    async def send_prompt(
        self,
        prompt: str,
        images: List[str],
        laz_name: Optional[str] = None,
        coordinates: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        data = {
            "prompt": prompt,
            "images": images,
            "laz_name": laz_name,
            "coordinates": coordinates,
        }
        response = await self._post("/api/openai/send", json_data=data)
        # prepare log payload with image size info
        log_images = [
            {"path": img, "size": len(img) if isinstance(img, str) else 0}
            for img in images
        ]
        log_payload = {
            "laz_name": laz_name,
            "coordinates": coordinates,
            "images": log_images,
            "prompt": prompt,
        }
        await self._post("/api/openai/log", json_data=log_payload)
        return response
