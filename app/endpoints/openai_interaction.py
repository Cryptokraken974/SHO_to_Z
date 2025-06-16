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

class LogPayload(BaseModel):
    laz_name: str | None = None
    coordinates: dict | None = None
    images: list[dict] = []
    prompt: str


class ResponsePayload(BaseModel):
    log_file: str | None = None
    response: str

@router.post("/send")
async def send_to_openai(payload: SendPayload):
    """Send prompt and images to OpenAI's chat model"""
    try:
        import openai  # type: ignore
        openai.api_key = os.getenv("OPENAI_API_KEY", "")
        messages = [
            {"role": "user", "content": payload.prompt}
        ]
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        content = response["choices"][0]["message"]["content"]
    except Exception as e:
        content = f"OpenAI call failed: {e}"
    return {"response": content}

@router.post("/log")
async def create_log(payload: LogPayload):
    """Create a log entry for an OpenAI request"""
    try:
        log_entry = payload.dict()
        filename = LOG_DIR / f"{uuid.uuid4().hex}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2)
        return {"log_file": str(filename)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write log: {e}")


@router.post("/response")
async def save_response(payload: ResponsePayload):
    """Save OpenAI response to file along with associated log file."""
    try:
        resp_entry = {"response": payload.response, "log_file": payload.log_file}
        filename = RESPONSE_DIR / f"{uuid.uuid4().hex}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(resp_entry, f, indent=2)
        return {"response_file": str(filename)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write response: {e}")
