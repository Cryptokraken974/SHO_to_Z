from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import os

router = APIRouter(prefix="/api/visual_lexicon", tags=["visual_lexicon"])

# Define the directory for visual lexicon files
VISUAL_LEXICON_DIR = Path("llm/prompts/prompt_modules/visual_lexicon")

@router.get("/anomaly_types")
async def get_anomaly_types():
    """
    Extract all anomaly names from the visual lexicon JSON files.
    Returns a list of anomaly types that can be used for filtering.
    """
    try:
        if not VISUAL_LEXICON_DIR.exists() or not VISUAL_LEXICON_DIR.is_dir():
            raise HTTPException(
                status_code=404, 
                detail=f"Visual lexicon directory not found: {VISUAL_LEXICON_DIR}"
            )

        anomaly_types = []
        
        # Iterate through all JSON files in the visual lexicon directory
        for json_file in VISUAL_LEXICON_DIR.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract anomaly_name if it exists
                if "anomaly_name" in data:
                    anomaly_name = data["anomaly_name"]
                    if anomaly_name not in anomaly_types:
                        anomaly_types.append(anomaly_name)
                        
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse JSON file {json_file.name}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Error reading file {json_file.name}: {e}")
                continue
        
        # Sort alphabetically for consistent ordering
        anomaly_types.sort()
        
        return {
            "success": True,
            "anomaly_types": anomaly_types,
            "total_count": len(anomaly_types)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to extract anomaly types: {str(e)}"
        )

@router.get("/anomaly_details/{anomaly_name}")
async def get_anomaly_details(anomaly_name: str):
    """
    Get detailed information about a specific anomaly type.
    """
    try:
        if not VISUAL_LEXICON_DIR.exists():
            raise HTTPException(
                status_code=404,
                detail="Visual lexicon directory not found"
            )
        
        # Search for the anomaly in all JSON files
        for json_file in VISUAL_LEXICON_DIR.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get("anomaly_name") == anomaly_name:
                    return {
                        "success": True,
                        "anomaly_details": data,
                        "source_file": json_file.name
                    }
                    
            except json.JSONDecodeError:
                continue
            except Exception:
                continue
        
        raise HTTPException(
            status_code=404,
            detail=f"Anomaly type '{anomaly_name}' not found in visual lexicon"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get anomaly details: {str(e)}"
        )

@router.get("/all_anomaly_data")
async def get_all_anomaly_data():
    """
    Get complete data for all anomaly types in the visual lexicon.
    Useful for frontend caching and comprehensive filtering.
    """
    try:
        if not VISUAL_LEXICON_DIR.exists():
            raise HTTPException(
                status_code=404,
                detail="Visual lexicon directory not found"
            )
        
        all_anomalies = {}
        
        for json_file in VISUAL_LEXICON_DIR.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                anomaly_name = data.get("anomaly_name")
                if anomaly_name:
                    all_anomalies[anomaly_name] = {
                        "data": data,
                        "source_file": json_file.name
                    }
                    
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse JSON file {json_file.name}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Error reading file {json_file.name}: {e}")
                continue
        
        return {
            "success": True,
            "anomalies": all_anomalies,
            "total_count": len(all_anomalies)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get all anomaly data: {str(e)}"
        )
