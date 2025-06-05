from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import os
import glob
import re
from ..main import manager, settings

router = APIRouter()

@router.get("/api/list-regions")
async def list_regions(source: str = None):
    """List all region subdirectories in the output directory and LAZ files from the input directory with coordinate metadata
    
    Args:
        source: Optional filter - 'input' for input folder only, 'output' for output folder only, None for both
    """
    print(f"\n🔍 API CALL: GET /api/list-regions?source={source or 'all'}")
    print("📂 Backend folder scanning started:")
    
    input_dir = "input"
    
    print(f"  📁 Input directory: {input_dir}")
    print(f"  🎯 Source filter: {source or 'all folders'}")
    
    regions_with_metadata = []
    
 
    
    # Second, check input directory for LAZ files and Sentinel-2 folders (only if source allows)
    if (source is None or source == "input") and os.path.exists(input_dir):
        print(f"  🔍 Scanning input folder: {input_dir}")
        # First, find Sentinel-2 download folders (folders with coordinate patterns in their names)
        import re
        coord_folder_pattern = r'(\d+\.\d+)([ns])_(\d+\.\d+)([ew])'
        
        for item in os.listdir(input_dir):
            item_path = os.path.join(input_dir, item)
            if os.path.isdir(item_path):
                # Check if folder name matches coordinate pattern (e.g., "11.31S_44.06W")
                match = re.search(coord_folder_pattern, item, re.IGNORECASE)
                if match:
                    lat_val, lat_dir, lng_val, lng_dir = match.groups()
                    lat = float(lat_val) * (-1 if lat_dir.lower() == 's' else 1)
                    lng = float(lng_val) * (-1 if lng_dir.lower() == 'w' else 1)
                    
                    region_info = {
                        "name": item,
                        "source": "input", 
                        "folder_path": os.path.relpath(item_path),
                        "center_lat": lat,
                        "center_lng": lng
                    }
                    regions_with_metadata.append(region_info)
                    print(f"Found Sentinel-2 folder '{item}' with coordinates: {lat}, {lng}")
        
        # Then, find all LAZ files (including .laz and .copc.laz)
        print(f"  🔍 Searching for LAZ files in: {input_dir}")
        laz_patterns = [
            os.path.join(input_dir, "**/*.laz"),
            os.path.join(input_dir, "**/*.LAZ"),
            os.path.join(input_dir, "**/*.copc.laz")
        ]
        
        files = []
        for pattern in laz_patterns:
            files.extend(glob.glob(pattern, recursive=True))
        
        # Convert to relative paths and remove duplicates
        relative_files = list(set([os.path.relpath(f) for f in files]))
        relative_files.sort()
        
        print(f"  📊 Found {len(relative_files)} LAZ files: {relative_files}")
        
        # Extract coordinate metadata for each file
        for file_path in relative_files:
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            # Use the parent directory as the region name for processing
            parent_dir = os.path.basename(os.path.dirname(file_path))
            region_info = {
                "name": file_name,  # Display name (filename without extension)
                "region_name": parent_dir,  # Actual region name for processing (directory name)
                "source": "input", 
                "file_path": file_path
            }
            
            # Check for OpenTopography metadata file
            file_dir = os.path.dirname(file_path)
            metadata_files = glob.glob(os.path.join(file_dir, "metadata_*.txt"))
            
            if metadata_files:
                try:
                    with open(metadata_files[0], 'r') as f:
                        content = f.read()
                        # Extract center coordinates from metadata
                        for line in content.split('\n'):
                            if line.startswith('# Center:'):
                                coords_str = line.split('# Center:')[1].strip()
                                lat, lng = coords_str.split(', ')
                                region_info["center_lat"] = float(lat)
                                region_info["center_lng"] = float(lng)
                                break
                except Exception as e:
                    print(f"Error reading metadata for {file_path}: {e}")
            
            # Add hardcoded coordinates for demo files
            filename = os.path.basename(file_path).lower()
            if "foxisland" in filename:
                region_info["center_lat"] = 44.4268
                region_info["center_lng"] = -68.2048
            elif "wizardisland" in filename or "or_wizardisland" in filename:
                region_info["center_lat"] = 42.9446
                region_info["center_lng"] = -122.1090
            else:
                # Try to extract coordinates from filename pattern like "lidar_14.87S_39.38W" or "lidar_23.46S_45.99W_lidar.laz"
                coord_pattern = r'lidar_(\d+\.\d+)([ns])_(\d+\.\d+)([ew])'
                print(f"Trying to extract coordinates from filename: '{filename}'")
                match = re.search(coord_pattern, filename, re.IGNORECASE)
                if match:
                    lat_val, lat_dir, lng_val, lng_dir = match.groups()
                    lat = float(lat_val) * (-1 if lat_dir.lower() == 's' else 1)
                    lng = float(lng_val) * (-1 if lng_dir.lower() == 'w' else 1)
                    region_info["center_lat"] = lat
                    region_info["center_lng"] = lng
                    print(f"Extracted coordinates from filename '{filename}': {lat}, {lng}")
                else:
                    print(f"No coordinate match found for filename: '{filename}'")
            
            regions_with_metadata.append(region_info)
    else:
        print(f"  ⏭️ Skipping input folder scan (source={source}, exists={os.path.exists(input_dir)})")
        
    regions_with_metadata.sort(key=lambda x: x["name"])
    
    print(f"\n✅ Backend scan complete:")
    print(f"  📊 Total regions found: {len(regions_with_metadata)}")
    for region in regions_with_metadata:
        coords = f"({region.get('center_lat', 'N/A')}, {region.get('center_lng', 'N/A')})" if region.get('center_lat') else "(no coords)"
        print(f"    📁 {region['name']} [{region['source']}] {coords}")
    
    return {"regions": regions_with_metadata}

@router.delete("/api/delete-region/{region_name}")
async def delete_region(region_name: str):
    """Delete a region by removing its input and output folders"""
    print(f"\n🗑️  API CALL: DELETE /api/delete-region/{region_name}")
    
    try:
        import shutil
        from pathlib import Path
        
        # Define the paths to the region folders
        input_folder = Path("input") / region_name
        output_folder = Path("output") / region_name
        
        deleted_folders = []
        
        # Delete input folder if it exists
        if input_folder.exists() and input_folder.is_dir():
            shutil.rmtree(input_folder)
            deleted_folders.append(str(input_folder))
        
        # Delete output folder if it exists
        if output_folder.exists() and output_folder.is_dir():
            shutil.rmtree(output_folder)
            deleted_folders.append(str(output_folder))
        
        if deleted_folders:
            return {
                "success": True,
                "message": f"Region '{region_name}' deleted successfully",
                "deleted_folders": deleted_folders
            }
        else:
            return {
                "success": False,
                "message": f"Region '{region_name}' not found",
                "deleted_folders": []
            }
    except Exception as e:
        import traceback
        print(f"Error deleting region {region_name}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to delete region: {str(e)}")

async def progress_callback_wrapper(progress_data: dict, region_name: Optional[str] = None):
    """Wraps the progress callback to include region_name if available."""
    if region_name:
        progress_data['region_name'] = region_name
    await manager.send_progress_update(progress_data)

# ============================================================================
# SAVED PLACES API ENDPOINTS
# ============================================================================

