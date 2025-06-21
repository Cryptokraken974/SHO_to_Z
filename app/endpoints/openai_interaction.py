from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import os
import uuid

router = APIRouter(prefix="/api/openai", tags=["openai"])

LOG_DIR = Path("llm/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

RESPONSE_DIR = Path("llm/responses")
RESPONSE_DIR.mkdir(parents=True, exist_ok=True)

class SendPayload(BaseModel):
    prompt: str
    images: list[str] = []
    laz_name: str | None = None
    coordinates: dict | None = None
    model_name: str | None = None  # Optional: User-selected OpenAI model name

class LogPayload(BaseModel):
    laz_name: str | None = None
    coordinates: dict | None = None
    images: list[dict] = []
    prompt: str
    model_name: str | None = None  # Optional: OpenAI model name used for the request


class ResponsePayload(BaseModel):
    log_file: str | None = None
    response: str

@router.post("/send")
async def send_to_openai(payload: SendPayload):
    """Send prompt and images to OpenAI's chat model"""
    try:
        import openai  # type: ignore
        openai.api_key = os.getenv("OPENAI_API_KEY", "")

        # Prepare content array for multimodal input.
        # The content array combines text prompts and image URLs.
        # It starts with the text prompt, followed by image URL objects for each image.
        content_list = [{"type": "text", "text": payload.prompt}]
        for image_url in payload.images:
            content_list.append({"type": "image_url", "image_url": image_url})

        messages = [
            {
                "role": "user",
                "content": content_list  # Combined text and image inputs
            }
        ]
        # Use the model_name from the payload if provided, otherwise default to "gpt-4-vision-preview".
        # This allows the client to specify which OpenAI model to use for the API call.
        selected_model = payload.model_name or "gpt-4-vision-preview"
        response = openai.ChatCompletion.create(model=selected_model, messages=messages)
        content = response["choices"][0]["message"]["content"]
    except Exception as e:
        content = f"OpenAI call failed: {e}"
    return {"response": content}

@router.post("/log")
async def create_log(payload: LogPayload):
    """Create a log entry for an OpenAI request"""
    try:
        import datetime
        
        # payload.dict() includes all fields from LogPayload, including model_name if present.
        log_entry = payload.dict()
        
        # Generate a structured folder name: region_model_date_uuid
        region_name = payload.laz_name or "unknown_region"
        model_name = payload.model_name or "gpt-4-vision-preview"
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]  # Short UUID for readability
        
        # Create folder structure: llm/logs/OR_WizardIsland_gpt4vision_20250621_a1b2c3d4/
        clean_region = "".join(c for c in region_name if c.isalnum() or c in "_-")
        clean_model = "".join(c for c in model_name.replace("-", "").replace(".", "") if c.isalnum())
        
        folder_name = f"{clean_region}_{clean_model}_{date_str}_{unique_id}"
        log_folder = LOG_DIR / folder_name
        log_folder.mkdir(parents=True, exist_ok=True)
        
        # Save main log file
        log_filename = log_folder / "request_log.json"
        with open(log_filename, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2)
        
        return {"log_file": str(log_filename), "log_folder": str(log_folder)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write log: {e}")


@router.post("/response")
async def save_response(payload: ResponsePayload):
    """Save OpenAI response to file along with associated log file."""
    try:
        import datetime
        
        resp_entry = {"response": payload.response, "log_file": payload.log_file}
        
        # If we have a log_file path, try to derive a meaningful filename
        if payload.log_file and "logs/" in payload.log_file:
            # Extract folder name from log file path
            # e.g., "llm/logs/OR_WizardIsland_gpt4vision_20250621_a1b2c3d4/request_log.json"
            log_path = Path(payload.log_file)
            if len(log_path.parts) >= 3:  # has llm/logs/folder_name/
                folder_name = log_path.parts[-2]  # Get folder name
                filename = RESPONSE_DIR / f"{folder_name}_response.json"
            else:
                filename = RESPONSE_DIR / f"{uuid.uuid4().hex}.json"
        else:
            filename = RESPONSE_DIR / f"{uuid.uuid4().hex}.json"
            
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(resp_entry, f, indent=2)
        return {"response_file": str(filename)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write response: {e}")
