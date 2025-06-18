from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Tuple, Dict, Union
import os
import glob
import re

router = APIRouter()

def _read_coordinates_from_metadata(region_name: str) -> Union[Tuple[float, float, Optional[Dict[str, float]]], Tuple[float, float], None]:
    """Read existing coordinates and bounds from a region's metadata.txt file.

    Returns:
        Union[Tuple[float, float, Optional[Dict[str, float]]], Tuple[float, float], None]:
        - (lat, lng, bounds_dict) if center coordinates and all bounds are found.
        - (lat, lng, None) if only center coordinates are found.
        - None if coordinates are not found or file doesn't exist.
    """
    try:
        metadata_file = os.path.join("output", region_name, "metadata.txt")
        if not os.path.exists(metadata_file):
            return None

        with open(metadata_file, 'r') as f:
            content = f.read()

        lat = None
        lng = None
        bounds: Dict[str, Optional[float]] = {"north": None, "south": None, "east": None, "west": None}

        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Center Latitude:') and 'N/A' not in line:
                try:
                    lat = float(line.split('Center Latitude:')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith('Center Longitude:') and 'N/A' not in line:
                try:
                    lng = float(line.split('Center Longitude:')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith('North Bound:') and 'N/A' not in line:
                try:
                    bounds["north"] = float(line.split('North Bound:')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith('South Bound:') and 'N/A' not in line:
                try:
                    bounds["south"] = float(line.split('South Bound:')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith('East Bound:') and 'N/A' not in line:
                try:
                    bounds["east"] = float(line.split('East Bound:')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith('West Bound:') and 'N/A' not in line:
                try:
                    bounds["west"] = float(line.split('West Bound:')[1].strip())
                except (ValueError, IndexError):
                    pass

        if lat is not None and lng is not None:
            if all(bounds[k] is not None for k in bounds):
                # All bounds are valid floats
                print(f"  📍 Found cached coordinates and bounds for {region_name}: ({lat}, {lng}), Bounds: {bounds}")
                return lat, lng, {k: float(v) for k, v in bounds.items() if v is not None} # Ensure type checker is happy
            else:
                # Only coordinates found
                print(f"  📍 Found cached coordinates for {region_name}: ({lat}, {lng}) (no complete bounds)")
                return lat, lng, None

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

        # Add bounds information if available in the region dict
        bounds_info = region.get("bounds")
        if isinstance(bounds_info, dict) and all(k in bounds_info for k in ["north", "south", "east", "west"]):
            content += f"""
North Bound: {bounds_info['north']}
South Bound: {bounds_info['south']}
East Bound: {bounds_info['east']}
West Bound: {bounds_info['west']}"""
        elif file_path.lower().endswith(('.laz', '.las')):
            # If it's a LAZ file and specific bounds aren't available yet, keep placeholder
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
            cached_data = _read_coordinates_from_metadata(file_name)
            if cached_data:
                if len(cached_data) == 3:
                    region_info["center_lat"], region_info["center_lng"], region_info["bounds"] = cached_data
                elif len(cached_data) == 2: # Should ideally not happen with the new func, but good for safety
                    region_info["center_lat"], region_info["center_lng"] = cached_data
                    region_info["bounds"] = None # Explicitly set to None
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
    
    # Second pass: Skip automatic LAZ analysis during app startup to prevent unwanted processing
    # LAZ coordinates will be extracted when files are explicitly selected or processed by the user
    print(f"\n⏭️ Skipping automatic LAZ analysis during startup to prevent unwanted processing...")
    laz_files_count = 0
    for region in regions_with_metadata:
        if (region.get("source") == "input" and 
            region.get("file_path") and 
            region["file_path"].lower().endswith(('.laz', '.las')) and
            region.get("center_lat") is None):
            
            file_name = os.path.basename(region["file_path"])
            laz_files_count += 1
            print(f"  📋 LAZ file found (analysis deferred): {file_name}")
            
            # Set placeholder coordinates instead of triggering automatic analysis
            # These will be populated when the user explicitly selects the region
            region["center_lat"] = None
            region["center_lng"] = None
            
    if laz_files_count > 0:
        print(f"  ℹ️  Found {laz_files_count} LAZ file(s) - coordinates will be extracted when explicitly requested")

    # Create or update metadata.txt files only when necessary
    print(f"\n📄 Checking metadata.txt files for regions...")
    metadata_created_count = 0
    metadata_updated_count = 0
    metadata_skipped_count = 0
    
    for region in regions_with_metadata:
        region_name = region.get("name")
        if region_name:
            # Create output directory path for this region
            output_dir = os.path.join("output", region_name)
            os.makedirs(output_dir, exist_ok=True)
            
            # Create metadata.txt file path
            metadata_file = os.path.join(output_dir, "metadata.txt")
            
            should_create_metadata = False
            should_update_coordinates = False
            
            # Check if metadata file exists
            if not os.path.exists(metadata_file):
                should_create_metadata = True
                print(f"  📄 Metadata file missing for {region_name} - will create")
            else:
                # File exists, check if it has coordinates and bounds
                existing_data = _read_coordinates_from_metadata(region_name)
                has_existing_coords = False
                has_existing_bounds = False

                if existing_data:
                    if len(existing_data) >= 2 and existing_data[0] is not None and existing_data[1] is not None:
                        has_existing_coords = True
                    if len(existing_data) == 3 and existing_data[2] is not None:
                        has_existing_bounds = True

                # Determine if metadata needs update based on current region info vs existing file
                # Update if:
                # 1. File has no coords, but region_info has them.
                # 2. File has no bounds, but region_info has them.
                # 3. Coords in file don't match region_info (e.g. updated from LAZ analysis).
                # 4. Bounds in file don't match region_info.

                needs_coord_update = region.get("center_lat") is not None and region.get("center_lng") is not None and \
                                     (not has_existing_coords or \
                                      (existing_data and (existing_data[0] != region.get("center_lat") or existing_data[1] != region.get("center_lng"))))

                needs_bounds_update = region.get("bounds") is not None and \
                                      (not has_existing_bounds or \
                                       (existing_data and len(existing_data) == 3 and existing_data[2] != region.get("bounds")))

                if needs_coord_update or needs_bounds_update:
                    should_update_coordinates = True # This variable name is a bit misleading now, it means "update metadata file"
                    if needs_coord_update and needs_bounds_update:
                        print(f"  📝 Metadata for {region_name} needs update for coordinates and bounds - will update")
                    elif needs_coord_update:
                        print(f"  📝 Metadata for {region_name} needs update for coordinates - will update")
                    elif needs_bounds_update:
                         print(f"  📝 Metadata for {region_name} needs update for bounds - will update")
                else:
                    metadata_skipped_count += 1
                    print(f"  ✅ Metadata for {region_name} already up-to-date - skipping")
            
            # Only create or update if necessary
            if should_create_metadata or should_update_coordinates:
                try:
                    # Generate metadata content based on region type
                    metadata_content = _generate_metadata_content(region)
                    
                    # Write metadata to file
                    with open(metadata_file, 'w') as f:
                        f.write(metadata_content)
                    
                    if should_create_metadata:
                        metadata_created_count += 1
                        if region.get("center_lat") and region.get("center_lng"):
                            print(f"  ✅ Created metadata.txt with coordinates for region: {region_name} ({region['center_lat']}, {region['center_lng']})")
                        else:
                            print(f"  ✅ Created metadata.txt for region: {region_name} (no coordinates available)")
                    elif should_update_coordinates:
                        metadata_updated_count += 1
                        print(f"  ✅ Updated metadata.txt with coordinates for region: {region_name} ({region['center_lat']}, {region['center_lng']})")
                        
                except Exception as e:
                    print(f"  ❌ Failed to create/update metadata.txt for region {region_name}: {str(e)}")
                    # Create empty file as fallback if it doesn't exist
                    if should_create_metadata:
                        try:
                            with open(metadata_file, 'w') as f:
                                f.write(f"# Region: {region_name}\n# Error occurred while extracting coordinates: {str(e)}\n")
                        except:
                            pass
    
    print(f"\n📊 Metadata file summary:")
    print(f"  ✅ Created: {metadata_created_count}")
    print(f"  📝 Updated: {metadata_updated_count}") 
    print(f"  ⏭️ Skipped: {metadata_skipped_count}")
    
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

