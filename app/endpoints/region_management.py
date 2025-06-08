from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import os
import glob
import re

router = APIRouter()

def _read_coordinates_from_metadata(region_name: str) -> tuple[float, float] | None:
    """Read existing coordinates from a region's metadata.txt file if it exists.
    
    Returns:
        tuple[float, float] | None: (lat, lng) if found, None if not found or file doesn't exist
    """
    try:
        metadata_file = os.path.join("output", region_name, "metadata.txt")
        if not os.path.exists(metadata_file):
            return None
            
        with open(metadata_file, 'r') as f:
            content = f.read()
            
        # Look for coordinate lines in the metadata
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('Center Latitude:') and 'N/A' not in line:
                lat_line = line
                # Find the corresponding longitude line
                for lng_line in content.split('\n'):
                    lng_line = lng_line.strip()
                    if lng_line.startswith('Center Longitude:') and 'N/A' not in lng_line:
                        try:
                            lat = float(lat_line.split('Center Latitude:')[1].strip())
                            lng = float(lng_line.split('Center Longitude:')[1].strip())
                            print(f"  📍 Found cached coordinates for {region_name}: ({lat}, {lng})")
                            return (lat, lng)
                        except (ValueError, IndexError):
                            continue
                        break
                break
        return None
    except Exception as e:
        print(f"  ⚠️  Error reading cached coordinates for {region_name}: {str(e)}")
        return None

def _generate_metadata_content(region: dict) -> str:
    """Generate metadata content for a region based on its type and available coordinate information."""
    from datetime import datetime
    
    region_name = region.get("name", "Unknown")
    source = region.get("source", "unknown")
    file_path = region.get("file_path", "")
    
    # Determine the source type for better metadata
    if file_path.lower().endswith(('.laz', '.las')):
        source_type = "LAZ file analysis"
    elif source == "input" and "S_" in region_name and "W" in region_name:
        source_type = "Coordinate-based folder"
    else:
        source_type = source
    
    # Start with basic metadata
    content = f"""# Region Metadata
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Source: {source_type}

Region Name: {region_name}
Source: {source}"""
    
    if file_path:
        content += f"""
File Path: {file_path}"""
    
    # Add coordinate information if available
    center_lat = region.get("center_lat")
    center_lng = region.get("center_lng")
    
    if center_lat is not None and center_lng is not None:
        content += f"""

# Coordinate Information (from {source_type})
Center Latitude: {center_lat}
Center Longitude: {center_lng}"""
        
        # Add bounds if this was from LAZ analysis
        if file_path.lower().endswith(('.laz', '.las')):
            content += f"""

# Additional Information
Source CRS: Will be populated during LAZ processing
Native Bounds: Will be populated during LAZ processing"""
    else:
        content += f"""

# Coordinate Information
Center Latitude: N/A
Center Longitude: N/A"""
    
    return content

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
            
            # First, check if coordinates are already cached in metadata.txt
            cached_coords = _read_coordinates_from_metadata(file_name)
            if cached_coords:
                region_info["center_lat"], region_info["center_lng"] = cached_coords
            elif "foxisland" in filename:
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
                    print(f"No coordinate match found for filename: '{filename}' - will need LAZ analysis")
            
            regions_with_metadata.append(region_info)
    else:
        print(f"  ⏭️ Skipping input folder scan (source={source}, exists={os.path.exists(input_dir)})")
        
    regions_with_metadata.sort(key=lambda x: x["name"])
    
    # Second pass: Perform LAZ analysis for regions without coordinates
    print(f"\n🔍 Analyzing LAZ files without cached coordinates...")
    for region in regions_with_metadata:
        if (region.get("source") == "input" and 
            region.get("file_path") and 
            region["file_path"].lower().endswith(('.laz', '.las')) and
            region.get("center_lat") is None):
            
            file_name = os.path.basename(region["file_path"])
            print(f"  🔬 Analyzing LAZ file: {file_name}")
            
            try:
                import requests
                response = requests.get(f'http://localhost:8000/api/laz/bounds-wgs84/{file_name}', timeout=30)
                if response.status_code == 200:
                    bounds_data = response.json()
                    if bounds_data and "center" in bounds_data:
                        center = bounds_data["center"]
                        region["center_lat"] = center["lat"]
                        region["center_lng"] = center["lng"]
                        print(f"  ✅ Extracted coordinates from LAZ analysis for '{file_name}': ({center['lat']}, {center['lng']})")
                else:
                    print(f"  ❌ LAZ bounds analysis failed for {file_name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"  ❌ Error analyzing LAZ file {file_name}: {str(e)}")

    # Create metadata.txt files with coordinate information for all found regions
    print(f"\n📄 Creating metadata.txt files with coordinates for regions...")
    for region in regions_with_metadata:
        region_name = region.get("name")
        if region_name:
            # Create output directory path for this region
            output_dir = os.path.join("output", region_name)
            os.makedirs(output_dir, exist_ok=True)
            
            # Create metadata.txt file path
            metadata_file = os.path.join(output_dir, "metadata.txt")
            
            try:
                # Generate metadata content based on region type
                metadata_content = _generate_metadata_content(region)
                
                # Write metadata to file
                with open(metadata_file, 'w') as f:
                    f.write(metadata_content)
                    
                if region.get("center_lat") and region.get("center_lng"):
                    print(f"  ✅ Created metadata.txt with coordinates for region: {region_name} ({region['center_lat']}, {region['center_lng']})")
                else:
                    print(f"  ✅ Created metadata.txt for region: {region_name} (coordinates extracted from LAZ analysis)")
                    
            except Exception as e:
                print(f"  ❌ Failed to create metadata.txt for region {region_name}: {str(e)}")
                # Create empty file as fallback
                try:
                    with open(metadata_file, 'w') as f:
                        f.write(f"# Region: {region_name}\n# Error occurred while extracting coordinates: {str(e)}\n")
                except:
                    pass
    
    print(f"\n✅ Backend scan complete:")
    print(f"  📊 Total regions found: {len(regions_with_metadata)}")
    for region in regions_with_metadata:
        coords = f"({region.get('center_lat', 'N/A')}, {region.get('center_lng', 'N/A')})" if region.get('center_lat') else "(no coords)"
        print(f"    📁 {region['name']} [{region['source']}] {coords}")
    
    return {"regions": regions_with_metadata}

@router.get("/api/get_spatial_metadata")
async def get_spatial_metadata(filePath: str):
    """Extract spatial metadata (coordinates) from a LAZ file path
    
    Args:
        filePath: The file path of the LAZ file (e.g., "input/region/lidar_14.87S_39.38W_lidar.laz")
    
    Returns:
        JSON object with latitude and longitude: {"latitude": -14.87, "longitude": -39.38}
    """
    print(f"\n🌍 API CALL: GET /api/get_spatial_metadata?filePath={filePath}")
    
    try:
        # Get just the filename from the path
        filename = os.path.basename(filePath).lower()
        print(f"🔍 Extracting coordinates from filename: {filename}")
        
        # Try multiple coordinate patterns
        patterns = [
            # Pattern: lidar_14.87S_39.38W_lidar.laz or lidar_14.87S_39.38W.laz
            r'lidar_(\d+\.\d+)([ns])_(\d+\.\d+)([ew])',
            # Pattern: 14.87S_39.38W.laz  
            r'(\d+\.\d+)([ns])_(\d+\.\d+)([ew])',
            # Pattern for files with underscores: some_14.87S_39.38W_something.laz
            r'.*_(\d+\.\d+)([ns])_(\d+\.\d+)([ew]).*'
        ]
        
        latitude = None
        longitude = None
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                lat_val, lat_dir, lng_val, lng_dir = match.groups()
                latitude = float(lat_val) * (-1 if lat_dir.lower() == 's' else 1)
                longitude = float(lng_val) * (-1 if lng_dir.lower() == 'w' else 1)
                print(f"✅ Extracted coordinates: {latitude}, {longitude}")
                break
        
        if latitude is not None and longitude is not None:
            return {
                "latitude": latitude,
                "longitude": longitude
            }
        
        # Check if there's a metadata file in the same directory
        file_dir = os.path.dirname(filePath)
        if os.path.exists(file_dir):
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
                                latitude = float(lat)
                                longitude = float(lng)
                                print(f"✅ Extracted coordinates from metadata: {latitude}, {longitude}")
                                return {
                                    "latitude": latitude,
                                    "longitude": longitude
                                }
                except Exception as e:
                    print(f"⚠️  Error reading metadata file: {e}")
        
        # If no coordinates found, return an error
        print(f"❌ No coordinates found in filename: {filename}")
        raise HTTPException(
            status_code=404, 
            detail=f"No spatial metadata found for file: {os.path.basename(filePath)}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error extracting spatial metadata: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to extract spatial metadata: {str(e)}"
        )

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
    from ..main import manager
    if region_name:
        progress_data['region_name'] = region_name
    await manager.send_progress_update(progress_data)

# ============================================================================
# SAVED PLACES API ENDPOINTS
# ============================================================================

# ============================================================================
# REGION METADATA API ENDPOINTS
# ============================================================================

@router.post("/api/save-region-metadata")
async def save_region_metadata(data: dict):
    """Save simple coordinate-only metadata for a selected region
    
    Args:
        data: Dictionary containing region_name and metadata
    """
    try:
        region_name = data.get('region_name')
        metadata = data.get('metadata')
        
        if not region_name or not metadata:
            raise HTTPException(status_code=400, detail="region_name and metadata are required")
        
        # Create output directory for the region
        output_dir = os.path.join("output", region_name)
        os.makedirs(output_dir, exist_ok=True)
        
        # Create simple metadata file with just coordinates
        metadata_path = os.path.join(output_dir, "metadata.txt")
        
        metadata_content = f"""# Region Selection Metadata
# Created: {metadata.get('creation_time', 'Unknown')}
# Source: {metadata.get('source', 'region_selection')}

Region Name: {metadata.get('region_name', region_name)}
Display Name: {metadata.get('display_name', region_name)}
Center Latitude: {metadata.get('center_latitude', 'N/A')}
Center Longitude: {metadata.get('center_longitude', 'N/A')}
"""
        
        with open(metadata_path, 'w') as f:
            f.write(metadata_content)
        
        print(f"✅ Created simple metadata file: {metadata_path}")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Metadata saved for region {region_name}",
            "file_path": metadata_path
        })
        
    except Exception as e:
        print(f"❌ Error saving metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save metadata: {str(e)}")

# ============================================================================

