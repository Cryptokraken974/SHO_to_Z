from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import os

router = APIRouter(prefix="/api/results", tags=["results"])

# Define the directory for response logs based on the existing structure
# (assuming this script is run from a context where 'llm/responses' is a valid relative path)
RESPONSE_DIR = Path("llm/responses")
LOG_DIR = Path("llm/logs")

@router.get("/list")
async def list_result_logs():
    """
    Lists all available OpenAI response log files.
    These are the files stored in the 'llm/responses/' directory.
    """
    if not RESPONSE_DIR.exists() or not RESPONSE_DIR.is_dir():
        raise HTTPException(status_code=404, detail=f"Results directory not found: {RESPONSE_DIR}")

    try:
        # List .json files in the directory
        log_files = [f.name for f in RESPONSE_DIR.glob("*.json") if f.is_file()]
        return {"logs": log_files}
    except Exception as e:
        # Log the exception for server-side debugging if possible
        # For now, just raise an HTTPException
        print(f"Error reading results directory {RESPONSE_DIR}: {e}") # Or use a proper logger
        raise HTTPException(status_code=500, detail=f"Failed to list result logs: {str(e)}")

# Placeholder for other endpoints to be added later
@router.get("/get/{log_filename}")
async def get_result_log_detail(log_filename: str):
    """
    Fetches the content of a specific response log
    and its associated request log.
    """
    response_log_path = RESPONSE_DIR / log_filename

    if not response_log_path.exists() or not response_log_path.is_file():
        raise HTTPException(status_code=404, detail=f"Response log file not found: {log_filename}")

    try:
        with open(response_log_path, 'r', encoding='utf-8') as f:
            response_data = json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in response log: {log_filename}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading response log {log_filename}: {str(e)}")

    request_log_file_path_str = response_data.get("log_file")
    if not request_log_file_path_str:
        raise HTTPException(status_code=404, detail=f"Path to request log ('log_file') not found in response log: {log_filename}")

    # Handle both old and new log file path formats
    # New format: "llm/logs/OR_WizardIsland_gpt4vision_20250621_test001/request_log.json"
    # Old format: "llm/logs/<uuid>.json"
    request_log_path = Path(request_log_file_path_str)

    # Check if the path exists as-is (relative to project root)
    if not request_log_path.exists():
        # Try relative to current working directory
        cwd_path = Path.cwd() / request_log_path
        if cwd_path.exists():
            request_log_path = cwd_path
        else:
            # If it's just a filename, try in LOG_DIR
            potential_path_in_log_dir = LOG_DIR / request_log_path.name
            if potential_path_in_log_dir.exists():
                request_log_path = potential_path_in_log_dir
            else:
                raise HTTPException(status_code=404, detail=f"Associated request log file not found at {request_log_file_path_str}. Checked paths: {request_log_path}, {cwd_path}, {potential_path_in_log_dir}")
    
    # Ensure it's a file
    if not request_log_path.is_file():
        raise HTTPException(status_code=404, detail=f"Path exists but is not a file: {request_log_path}")

    try:
        with open(request_log_path, 'r', encoding='utf-8') as f:
            request_data = json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in request log: {request_log_path.name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading request log {request_log_path.name}: {str(e)}")

    combined_data = {
        "response_filename": log_filename,
        "openai_response": response_data.get("response"),
        "request_log_filename": request_log_path.name,
        "original_prompt": request_data.get("prompt"),
        "input_images": request_data.get("images", []),
        "laz_name": request_data.get("laz_name"),
        "coordinates": request_data.get("coordinates"),
        "model_name": request_data.get("model_name")
    }

    return combined_data

@router.get("/get_all")
async def get_all_results_summary():
    """
    Fetches and aggregates data from all response and request logs.
    Provides a summary focused on archaeological insights.
    """
    if not RESPONSE_DIR.exists() or not RESPONSE_DIR.is_dir():
        # This check is also in list_result_logs, but good to have here too
        # if this endpoint is called directly.
        raise HTTPException(status_code=404, detail=f"Results directory not found: {RESPONSE_DIR}")

    all_log_files = [f for f in RESPONSE_DIR.glob("*.json") if f.is_file()]

    aggregated_data = {
        "total_results": 0,
        "unique_regions": set(), # Using a set to store unique region identifiers
        "model_usage_counts": {},
        "keyword_counts": {
            "anomaly": 0,
            "structure": 0,
            "feature": 0,
            "artifact": 0,
            "remains": 0,
            "interpretation": 0
            # Add more keywords as needed
        },
        "detailed_results": [] # Optional: could add summaries of each result if needed
    }

    processed_files_count = 0

    for response_log_path in all_log_files:
        try:
            with open(response_log_path, 'r', encoding='utf-8') as f:
                response_data = json.load(f)

            request_log_file_path_str = response_data.get("log_file")
            if not request_log_file_path_str:
                # Log this error but continue with other files
                print(f"Warning: 'log_file' not found in {response_log_path.name}. Skipping this log.")
                continue

            request_log_path = Path(request_log_file_path_str)

            # Simplified path resolution for aggregation, assuming structure is consistent
            # More robust path checking can be added if issues arise from varied log_file formats
            if not request_log_path.is_file():
                potential_path_in_log_dir = LOG_DIR / request_log_path.name
                if potential_path_in_log_dir.is_file():
                    request_log_path = potential_path_in_log_dir
                else:
                    print(f"Warning: Request log {request_log_file_path_str} for {response_log_path.name} not found. Skipping.")
                    continue

            with open(request_log_path, 'r', encoding='utf-8') as f:
                request_data = json.load(f)

            processed_files_count += 1

            # Aggregate unique regions
            laz_name = request_data.get("laz_name")
            coordinates = request_data.get("coordinates")
            if laz_name:
                aggregated_data["unique_regions"].add(laz_name)
            elif coordinates and isinstance(coordinates, dict):
                # Create a string representation for coordinates to add to set
                coord_str = f"lat:{coordinates.get('lat', 'N/A')},lon:{coordinates.get('lng', 'N/A')}"
                aggregated_data["unique_regions"].add(coord_str)

            # Count model usage
            model_name = request_data.get("model_name", "Unknown")
            aggregated_data["model_usage_counts"][model_name] = aggregated_data["model_usage_counts"].get(model_name, 0) + 1

            # Search for keywords in OpenAI response
            openai_response_text = response_data.get("response", "").lower() # Case-insensitive search
            for keyword in aggregated_data["keyword_counts"].keys():
                if keyword in openai_response_text:
                    aggregated_data["keyword_counts"][keyword] += 1

            # Optionally, add some per-result summary to "detailed_results" if desired
            # For now, keeping it simple.

        except json.JSONDecodeError as e:
            print(f"Warning: JSON decode error in {response_log_path.name} or its request log. Error: {e}. Skipping.")
            continue
        except Exception as e:
            print(f"Warning: Error processing log file {response_log_path.name}. Error: {e}. Skipping.")
            continue

    aggregated_data["total_results"] = processed_files_count
    # Convert set of unique regions to a list for JSON serialization
    aggregated_data["unique_regions"] = list(aggregated_data["unique_regions"])

    return aggregated_data
