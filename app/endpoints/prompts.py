import os
import json
from fastapi import APIRouter

router = APIRouter()

PROMPTS_DIR = "llm/prompts"

@router.get("/api/prompts/all")
async def get_all_prompts():
    prompts = []
    file_paths = []
    for root, _, files in os.walk(PROMPTS_DIR):
        for file in files:
            if file.endswith(".json"):
                file_paths.append(os.path.join(root, file))

    file_paths.sort() # Sort alphabetically

    for file_path in file_paths:
        with open(file_path, "r") as f:
            content = f.read()
        title = os.path.splitext(os.path.basename(file_path))[0]
        prompts.append({"title": title, "content": content})

    return {"prompts": prompts}
