from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import os
import uuid
import base64
import base64

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
    temp_folder_name: str | None = None  # Optional: Name of temp folder containing saved images

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
    """Send prompt and images to OpenAI's chat model and automatically create log entries"""
    try:
        from openai import OpenAI
        import datetime
        import shutil
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

        # Prepare content array for multimodal input.
        # The content array combines text prompts and image URLs.
        # It starts with the text prompt, followed by image URL objects for each image.
        content_list = [{"type": "text", "text": payload.prompt}]
        for image_url in payload.images:
            # OpenAI expects the image URL to be in a specific format
            content_list.append({
                "type": "image_url", 
                "image_url": {
                    "url": image_url  # This can be either a data URL or HTTP URL
                }
            })

        messages = [
            {
                "role": "user",
                "content": content_list  # Combined text and image inputs
            }
        ]
        # Use the model_name from the payload if provided, otherwise default to "gpt-4o-mini".
        # This allows the client to specify which OpenAI model to use for the API call.
        selected_model = payload.model_name or "gpt-4o-mini"
        
        response = client.chat.completions.create(
            model=selected_model, 
            messages=messages
        )
        content = response.choices[0].message.content
        
        # Automatically create log entry after successful OpenAI response
        region_name = payload.laz_name or "unknown_region"
        model_name = payload.model_name or "gpt-4o-mini"
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        # Create folder structure: llm/logs/OR_WizardIsland_gpt4omini_20250621_a1b2c3d4/
        clean_region = "".join(c for c in region_name if c.isalnum() or c in "_-")
        clean_model = "".join(c for c in model_name.replace("-", "").replace(".", "") if c.isalnum())
        
        folder_name = f"{clean_region}_{clean_model}_{date_str}_{unique_id}"
        log_folder = LOG_DIR / folder_name
        log_folder.mkdir(parents=True, exist_ok=True)
        
        # Prepare log entry with images (convert file paths to proper format)
        log_entry = {
            "laz_name": payload.laz_name,
            "coordinates": payload.coordinates,
            "images": [],
            "prompt": payload.prompt,
            "model_name": payload.model_name
        }
        
        # Check if there's a specific temp folder to use for images
        if payload.temp_folder_name:
            temp_folder = LOG_DIR / payload.temp_folder_name
            sent_images_folder = temp_folder / "sent_images"
            
            if sent_images_folder.exists():
                # Move the sent_images folder to the final log folder
                final_images_folder = log_folder / "sent_images"
                shutil.move(str(sent_images_folder), str(final_images_folder))
                
                # Create image entries for the log
                if final_images_folder.exists():
                    for img_file in final_images_folder.glob("*.png"):
                        log_entry["images"].append({
                            "name": img_file.stem.lower().replace("-", "_"),
                            "path": str(Path("llm/logs") / folder_name / "sent_images" / img_file.name),
                            "filename": img_file.name,
                            "size": img_file.stat().st_size
                        })
                
                # Clean up temp folder
                try:
                    temp_folder.rmdir()  # Will only work if empty
                except OSError:
                    pass  # Folder not empty, leave it
        else:
            # Fallback: Check if there are any temp image folders to rename and link
            temp_pattern = f"{clean_region}_temp_*"
            temp_folders = list(LOG_DIR.glob(temp_pattern))
            
            if temp_folders:
                # Use the most recent temp folder
                temp_folder = max(temp_folders, key=lambda p: p.stat().st_mtime)
                sent_images_folder = temp_folder / "sent_images"
                
                if sent_images_folder.exists():
                    # Move the sent_images folder to the final log folder
                    final_images_folder = log_folder / "sent_images"
                    shutil.move(str(sent_images_folder), str(final_images_folder))
                    
                    # Create image entries for the log
                    if final_images_folder.exists():
                        for img_file in final_images_folder.glob("*.png"):
                            log_entry["images"].append({
                                "name": img_file.stem.lower().replace("-", "_"),
                                "path": str(Path("llm/logs") / folder_name / "sent_images" / img_file.name),
                                "filename": img_file.name,
                                "size": img_file.stat().st_size
                            })
                
                # Clean up temp folder
                try:
                    temp_folder.rmdir()  # Will only work if empty
                except OSError:
                    pass  # Folder not empty, leave it
        
        # Save main log file
        log_filename = log_folder / "request_log.json"
        with open(log_filename, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2)
        
        # Also create a response file for the Results tab
        response_entry = {
            "response": content,
            "log_file": str(Path("llm/logs") / folder_name / "request_log.json")
        }
        
        response_filename = RESPONSE_DIR / f"{folder_name}_response.json"
        with open(response_filename, "w", encoding="utf-8") as f:
            json.dump(response_entry, f, indent=2)
        
        return {
            "response": content,
            "log_file": str(log_filename),
            "log_folder": str(log_folder),
            "response_file": str(response_filename)
        }
        
    except Exception as e:
        content = f"OpenAI call failed: {e}"
        return {"response": content, "error": str(e)}

@router.post("/log")
async def create_log(payload: LogPayload):
    """Create a log entry for an OpenAI request"""
    try:
        import datetime
        import shutil
        
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
        
        # Check if there are any temp image folders to rename
        # Look for existing temp folders with the same region
        temp_pattern = f"{clean_region}_temp_*"
        temp_folders = list(LOG_DIR.glob(temp_pattern))
        
        if temp_folders:
            # Use the most recent temp folder
            temp_folder = max(temp_folders, key=lambda p: p.stat().st_mtime)
            sent_images_folder = temp_folder / "sent_images"
            
            if sent_images_folder.exists():
                # Move the sent_images folder to the final log folder
                final_images_folder = log_folder / "sent_images"
                shutil.move(str(sent_images_folder), str(final_images_folder))
                
                # Update image paths in the log entry
                if "images" in log_entry:
                    updated_images = []
                    for img in log_entry["images"]:
                        if isinstance(img, dict) and "path" in img:
                            # Update path to reflect new folder location
                            old_path = Path(img["path"])
                            new_path = final_images_folder / old_path.name
                            img["path"] = str(new_path.relative_to(Path.cwd()))
                        updated_images.append(img)
                    log_entry["images"] = updated_images
            
            # Clean up temp folder
            try:
                temp_folder.rmdir()  # Will only work if empty
            except OSError:
                pass  # Folder not empty, leave it
        
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
        
        # Store the response directly without wrapping it in a "response" object
        resp_entry = payload.response.copy() if isinstance(payload.response, dict) else payload.response
        # Add the log_file reference at the root level
        if isinstance(resp_entry, dict):
            resp_entry["log_file"] = payload.log_file
        else:
            # If response is not a dict, create a wrapper with both fields
            resp_entry = {"analysis_data": payload.response, "log_file": payload.log_file}
        
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

@router.post("/save_images")
async def save_images_for_analysis(payload: dict):
    """Save base64 images to the file system for OpenAI analysis"""
    try:
        region_name = payload.get("region_name", "unknown_region") 
        images_data = payload.get("images", [])  # List of {name: str, data: str (base64)}
        
        if not images_data:
            return {"saved_images": [], "image_folder": None}
        
        # Generate folder structure similar to log creation
        import datetime
        clean_region = "".join(c for c in region_name if c.isalnum() or c in "_-")
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        # Create a temporary folder name (will be updated when log is created)
        temp_folder_name = f"{clean_region}_temp_{date_str}_{unique_id}"
        images_folder = LOG_DIR / temp_folder_name / "sent_images"
        images_folder.mkdir(parents=True, exist_ok=True)
        
        saved_images = []
        
        for img_data in images_data:
            img_name = img_data.get("name", "unknown")
            img_base64 = img_data.get("data", "")
            
            # Handle data URL format (data:image/png;base64,...)
            if img_base64.startswith("data:image/"):
                img_base64 = img_base64.split(",", 1)[1]
            
            try:
                # Decode base64 image
                img_bytes = base64.b64decode(img_base64)
                
                # Save image file
                img_filename = f"{img_name}.png"
                img_path = images_folder / img_filename
                
                with open(img_path, "wb") as f:
                    f.write(img_bytes)
                
                saved_images.append({
                    "name": img_name,
                    "path": str(img_path.relative_to(Path.cwd())),  # Relative path from project root
                    "filename": img_filename,
                    "size": len(img_bytes)
                })
                
            except Exception as e:
                print(f"Error saving image {img_name}: {e}")
                continue
        
        return {
            "saved_images": saved_images,
            "image_folder": str(images_folder.relative_to(Path.cwd())),
            "temp_folder_name": temp_folder_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save images: {e}")
