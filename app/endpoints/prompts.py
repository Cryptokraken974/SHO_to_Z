import os
import json
from fastapi import APIRouter, Query

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
        try:
            if file_path.endswith(".json"):
                # Parse JSON files and extract content
                with open(file_path, "r") as f:
                    prompt_data = json.load(f)
                content = prompt_data.get("content", json.dumps(prompt_data, indent=2))
            else:
                # For non-JSON files, read as text
                with open(file_path, "r") as f:
                    content = f.read()
            title = os.path.splitext(os.path.basename(file_path))[0]
            prompts.append({"title": title, "content": content})
        except Exception as e:
            print(f"Error reading prompt file {file_path}: {e}")
            continue

    return {"prompts": prompts}

@router.get("/api/prompts/workflow")
async def get_workflow_prompts(workflow: str = Query(default="workflow", description="Workflow type: 'workflow' or 'workflow_no_ndvi'")):
    """Get prompts from preprompt, prompt_modules, and specific workflow folder in correct order"""
    
    # Validate workflow parameter
    if workflow not in ["workflow", "workflow_no_ndvi"]:
        return {"error": "Invalid workflow type. Must be 'workflow' or 'workflow_no_ndvi'"}
    
    prompts = []
    include_ndvi = workflow == "workflow"  # Include NDVI only for the regular workflow
    
    # Define the correct order of prompt folders
    prompt_folders = [
        "preprompt",
        "prompt_modules/input_images", 
        "prompt_modules/visual_lexicon",
        workflow  # Either "workflow" or "workflow_no_ndvi"
    ]
    
    for folder in prompt_folders:
        folder_path = os.path.join(PROMPTS_DIR, folder)
        
        if not os.path.exists(folder_path):
            print(f"Warning: Prompt folder '{folder}' not found, skipping")
            continue
        
        # Get all JSON files from this folder
        folder_files = []
        for file in os.listdir(folder_path):
            if file.endswith(".json"):
                # Skip NDVI-related files if NDVI is disabled
                if not include_ndvi and file.lower() == "ndvi.json":
                    print(f"Skipping {file} for workflow_no_ndvi")
                    continue
                folder_files.append(os.path.join(folder_path, file))
        
        # Sort files within each folder alphabetically
        folder_files.sort()
        
        # Process files from this folder
        for file_path in folder_files:
            try:
                with open(file_path, "r") as f:
                    prompt_data = json.load(f)
                
                # Create descriptive title including folder name
                filename = os.path.splitext(os.path.basename(file_path))[0]
                folder_name = os.path.basename(folder)
                title = f"{folder_name}/{filename}"
                
                # Extract the actual content from the JSON structure
                content = prompt_data.get("content", "")
                if not content:
                    # Fallback to the raw JSON string if no content field
                    content = json.dumps(prompt_data, indent=2)
                
                prompts.append({"title": title, "content": content})
            except Exception as e:
                print(f"Error reading prompt file {file_path}: {e}")
                continue
    
    return {"prompts": prompts, "workflow": workflow, "ndvi_included": include_ndvi}
