from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Tuple, Dict, Union
import os
import glob
import re
from pathlib import Path

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
    ndvi_enabled = region.get("ndvi_enabled", False)
    
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
Source: {source}
NDVI Enabled: {str(ndvi_enabled).lower()}"""
    
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

def isRegionNDVI(region_name: str) -> bool:
    """Check if a region was created with NDVI enabled by reading its metadata.txt file or .settings.json file.
    
    Args:
        region_name: Name of the region to check
        
    Returns:
        True if the region was created with NDVI enabled, False otherwise
    """
    try:
        # First, try to read from metadata.txt file (preferred location)
        metadata_file = os.path.join("output", region_name, "metadata.txt")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                content = f.read()

            # Look for NDVI Enabled line
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('NDVI Enabled:'):
                    value = line.split('NDVI Enabled:')[1].strip().lower()
                    return value == 'true'
        
        # If metadata.txt doesn't exist or doesn't contain NDVI info,
        # check for .settings.json file in input/LAZ directory
        import json
        from pathlib import Path
        
        # Try to find corresponding LAZ file settings
        input_laz_dir = Path("input/LAZ")
        # Ensure directory exists
        input_laz_dir.mkdir(parents=True, exist_ok=True)
        
        if input_laz_dir.exists():
            # Look for any .settings.json file that matches the region name
            for settings_file in input_laz_dir.glob(f"{region_name}.settings.json"):
                try:
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                    return settings.get('ndvi_enabled', False)
                except Exception as e:
                    print(f"  ⚠️  Error reading settings file {settings_file}: {str(e)}")
                    continue
            
            # Also try pattern matching for similar filenames
            for settings_file in input_laz_dir.glob("*.settings.json"):
                try:
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                    # Check if the filename (without extension) matches the region name
                    settings_filename = settings.get('filename', '')
                    if settings_filename and Path(settings_filename).stem == region_name:
                        return settings.get('ndvi_enabled', False)
                except Exception as e:
                    continue
        
        # If no NDVI information found in either location, default to False
        return False
        
    except Exception as e:
        print(f"  ⚠️  Error reading NDVI status for {region_name}: {str(e)}")
        return False


@router.get("/api/list-regions")
async def list_regions(source: str = None, filter_type: str = None):
    """List all region subdirectories in the output directory and LAZ files from the input directory with coordinate metadata
    
    Args:
        source: Optional filter - 'input' for input folder only, 'output' for output folder only, None for both
        filter_type: Optional filter type - 'openai' for OpenAI analysis (requires rasters), None for general use
    """
    print(f"\n🔍 API CALL: GET /api/list-regions?source={source or 'all'}&filter_type={filter_type or 'general'}")
    print("📂 Backend folder scanning started:")
    print(f"  🎯 Source filter: {source or 'all folders'}")
    print(f"  🔧 Filter type: {filter_type or 'general (metadata.txt only)'}")
    
    input_dir = "input"
    
    print(f"  📁 Input directory: {input_dir}")
    
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
    
    # Third, check output directory for regions with metadata.txt files (coordinate-based regions, saved places, etc.)
    output_dir = "output"
    if (source is None or source == "output") and os.path.exists(output_dir):
        print(f"  🔍 Scanning output folder for metadata-based regions: {output_dir}")
        
        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            if os.path.isdir(item_path):
                metadata_file = os.path.join(item_path, "metadata.txt")
                lidar_folder = os.path.join(item_path, "lidar")
                
                # Apply different filtering logic based on filter_type
                if filter_type == "openai":
                    # For OpenAI analysis: Only include regions that have both metadata.txt AND lidar folder (rasters generated)
                    if os.path.exists(metadata_file) and os.path.exists(lidar_folder) and os.path.isdir(lidar_folder):
                        should_include_region = True
                    else:
                        should_include_region = False
                        if os.path.exists(metadata_file) and not (os.path.exists(lidar_folder) and os.path.isdir(lidar_folder)):
                            print(f"  ⏭️ Skipping region '{item}' for OpenAI analysis: has metadata but no raster data (missing lidar folder)")
                else:
                    # For general use: Include regions that have metadata.txt (regardless of lidar folder)
                    if os.path.exists(metadata_file):
                        should_include_region = True
                    else:
                        should_include_region = False
                
                if should_include_region:
                    # Check if this region is already in our list (avoid duplicates from input scan)
                    existing_region = next((r for r in regions_with_metadata if r["name"] == item), None)
                    
                    if not existing_region:
                        print(f"  📄 Found metadata-based region: {item}")
                        
                        # Read coordinates from metadata.txt
                        cached_data = _read_coordinates_from_metadata(item)
                        
                        region_info = {
                            "name": item,
                            "source": "output",
                            "folder_path": os.path.relpath(item_path),
                        }
                        
                        if cached_data:
                            if len(cached_data) == 3:
                                region_info["center_lat"], region_info["center_lng"], region_info["bounds"] = cached_data
                            elif len(cached_data) == 2:
                                region_info["center_lat"], region_info["center_lng"] = cached_data
                                region_info["bounds"] = None
                            
                            print(f"  📍 Loaded coordinates for {item}: ({region_info.get('center_lat')}, {region_info.get('center_lng')})")
                        else:
                            # If no coordinates in metadata, try to read source info
                            try:
                                with open(metadata_file, 'r') as f:
                                    content = f.read()
                                    
                                # Look for saved place metadata format
                                if "# Region Created from Saved Place" in content:
                                    region_info["region_type"] = "saved_place"
                                    print(f"  🏷️  Identified as saved place region: {item}")
                                
                                # Extract coordinates from different metadata formats
                                for line in content.split('\n'):
                                    line = line.strip()
                                    if line.startswith('Center Latitude:') and 'N/A' not in line:
                                        try:
                                            region_info["center_lat"] = float(line.split('Center Latitude:')[1].strip())
                                        except (ValueError, IndexError):
                                            pass
                                    elif line.startswith('Center Longitude:') and 'N/A' not in line:
                                        try:
                                            region_info["center_lng"] = float(line.split('Center Longitude:')[1].strip())
                                        except (ValueError, IndexError):
                                            pass
                                
                                if region_info.get("center_lat") and region_info.get("center_lng"):
                                    print(f"  📍 Extracted coordinates for {item}: ({region_info['center_lat']}, {region_info['center_lng']})")
                                    
                            except Exception as e:
                                print(f"  ⚠️  Error reading metadata for {item}: {e}")
                        
                        regions_with_metadata.append(region_info)
                    else:
                        print(f"  ↪️  Region {item} already found in input scan, skipping duplicate")
    else:
        print(f"  ⏭️ Skipping output folder scan (source={source}, exists={os.path.exists(output_dir)})")
        
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
                # File exists, check if it's an elevation API metadata file (should not be overwritten)
                with open(metadata_file, 'r') as f:
                    existing_content = f.read()
                
                # Check if this is an elevation API metadata file
                is_elevation_api_metadata = any(marker in existing_content for marker in [
                    "# Source: Elevation API",
                    "Buffer Distance (km):",
                    "# REQUESTED BOUNDS (WGS84 - EPSG:4326)",
                    "Download ID:"
                ])
                
                if is_elevation_api_metadata:
                    print(f"  🔒 Skipping elevation API metadata for {region_name} - preserving detailed bounds info")
                    metadata_skipped_count += 1
                    continue
                
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

@router.get("/api/regions/{region_name}/ndvi-status")
async def check_region_ndvi_status(region_name: str):
    """Check if a region was created with NDVI enabled.
    
    Args:
        region_name: Name of the region to check
        
    Returns:
        JSON object with NDVI status: {"ndvi_enabled": true/false, "region_name": "..."}
    """
    try:
        ndvi_enabled = isRegionNDVI(region_name)
        return {
            "ndvi_enabled": ndvi_enabled,
            "region_name": region_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check NDVI status: {str(e)}")

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
    """Delete a region by removing its input and output folders and associated LAZ files"""
    print(f"\n🗑️  API CALL: DELETE /api/delete-region/{region_name}")
    
    try:
        import shutil
        from pathlib import Path
        import glob
        
        # Define the paths to the region folders
        input_folder = Path("input") / region_name
        output_folder = Path("output") / region_name
        laz_input_dir = Path("input") / "LAZ"
        
        deleted_items = []
        
        # Delete input folder if it exists
        if input_folder.exists() and input_folder.is_dir():
            shutil.rmtree(input_folder)
            deleted_items.append({"type": "folder", "path": str(input_folder)})
        
        # Delete output folder if it exists
        if output_folder.exists() and output_folder.is_dir():
            shutil.rmtree(output_folder)
            deleted_items.append({"type": "folder", "path": str(output_folder)})
        
        # Find and delete LAZ files associated with this region
        # Search for LAZ files that match the region name
        if laz_input_dir.exists():
            # Look for exact matches and pattern matches
            laz_patterns = [
                f"{region_name}.laz",
                f"{region_name}.las", 
                f"*{region_name}*.laz",
                f"*{region_name}*.las"
            ]
            
            found_laz_files = []
            for pattern in laz_patterns:
                matching_files = list(laz_input_dir.glob(pattern))
                for laz_file in matching_files:
                    if laz_file.is_file() and laz_file not in found_laz_files:
                        found_laz_files.append(laz_file)
            
            # Delete found LAZ files
            for laz_file in found_laz_files:
                try:
                    laz_file.unlink()
                    deleted_items.append({"type": "laz_file", "path": str(laz_file)})
                    print(f"🗑️  Deleted LAZ file: {laz_file}")
                except Exception as laz_error:
                    print(f"⚠️  Warning: Could not delete LAZ file {laz_file}: {laz_error}")
        
        if deleted_items:
            # Organize deleted items for response
            deleted_folders = [item["path"] for item in deleted_items if item["type"] == "folder"]
            deleted_laz_files = [item["path"] for item in deleted_items if item["type"] == "laz_file"]
            
            return {
                "success": True,
                "message": f"Region '{region_name}' deleted successfully",
                "deleted_folders": deleted_folders,
                "deleted_laz_files": deleted_laz_files,
                "total_items_deleted": len(deleted_items)
            }
        else:
            return {
                "success": False,
                "message": f"Region '{region_name}' not found",
                "deleted_folders": [],
                "deleted_laz_files": []
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

@router.post("/api/create-region")
async def create_region(data: dict):
    """Create a region folder structure when saving a place
    
    Args:
        data: Dictionary containing region_name, coordinates, and metadata
    """
    try:
        region_name = data.get('region_name')
        coordinates = data.get('coordinates', {})
        place_name = data.get('place_name')
        ndvi_enabled = data.get('ndvi_enabled', False)
        
        if not region_name:
            raise HTTPException(status_code=400, detail="region_name is required")
        
        if not coordinates.get('lat') or not coordinates.get('lng'):
            raise HTTPException(status_code=400, detail="coordinates with lat and lng are required")
        
        # Sanitize region name for file system
        import re
        safe_region_name = re.sub(r'[<>:"/\\|?*]', '_', region_name)
        safe_region_name = safe_region_name.strip()
        
        if not safe_region_name:
            raise HTTPException(status_code=400, detail="Invalid region name")
        
        # Create input folder structure
        input_folder = Path("input") / safe_region_name
        input_folder.mkdir(parents=True, exist_ok=True)
        
        # Create output folder structure  
        output_folder = Path("output") / safe_region_name
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Create metadata file in output folder
        metadata_file = output_folder / "metadata.txt"
        
        # Handle bounds data if provided
        bounds_info = data.get('bounds', {})
        bounds_section = ""
        if bounds_info and all(k in bounds_info for k in ['north', 'south', 'east', 'west']):
            bounds_section = f"""
North Bound: {bounds_info['north']}
South Bound: {bounds_info['south']}
East Bound: {bounds_info['east']}
West Bound: {bounds_info['west']}"""
        
        metadata_content = f"""# Region Created from Saved Place
# Created: {data.get('created_at', 'Unknown')}
# Original Place Name: {place_name or safe_region_name}

Region Name: {safe_region_name}
Display Name: {place_name or safe_region_name}
Center Latitude: {coordinates['lat']}
Center Longitude: {coordinates['lng']}{bounds_section}
Source: saved_place
NDVI Enabled: {str(ndvi_enabled).lower()}
Created: {data.get('created_at', 'Unknown')}

# This region was created by saving a place location
# You can add elevation data, LAZ files, or satellite imagery to the input folder
"""
        
        with open(metadata_file, 'w') as f:
            f.write(metadata_content)
        
        print(f"✅ Created region folder structure for: {safe_region_name}")
        print(f"   📁 Input folder: {input_folder}")
        print(f"   📁 Output folder: {output_folder}")
        print(f"   📄 Metadata file: {metadata_file}")
        
        response_content = {
            "success": True,
            "message": f"Region '{safe_region_name}' created successfully",
            "region_name": safe_region_name,
            "input_folder": str(input_folder),
            "output_folder": str(output_folder),
            "metadata_file": str(metadata_file)
        }
            
        return JSONResponse(content=response_content)
        
    except Exception as e:
        print(f"❌ Error creating region: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create region: {str(e)}")

# ============================================================================
# REGION METADATA API ENDPOINTS
# ============================================================================

@router.get("/api/regions/{region_name}/png-files")
async def get_region_png_files(region_name: str):
    """Get available PNG files for a specific region"""
    try:
        print(f"\n📸 API CALL: /api/regions/{region_name}/png-files")
        
        # Check both input and output directories for PNG files
        png_files = []
        base_dirs = ["input", "output"]
        
        for base_dir in base_dirs:
            region_dir = Path(base_dir) / region_name
            if not region_dir.exists():
                continue
                
            print(f"🔍 Scanning {region_dir} for PNG files...")
            
            # Search for PNG files in various subdirectories
            png_patterns = [
                "**/*.png",
                "**/png_outputs/*.png",
                "**/lidar/**/*.png",
                "**/sentinel2/**/*.png"
            ]
            
            found_files = []
            for pattern in png_patterns:
                matches = list(region_dir.glob(pattern))
                found_files.extend(matches)
            
            # Remove duplicates and process files
            unique_files = list(set(found_files))
            
            for png_file in unique_files:
                try:
                    # Get relative path from region directory
                    relative_path = png_file.relative_to(region_dir)
                    file_size_mb = round(png_file.stat().st_size / (1024 * 1024), 2)
                    
                    # Try to determine processing type from file path
                    processing_type = "unknown"
                    display_name = png_file.stem
                    
                    # Skip files that are clearly not LIDAR processing results (apply globally)
                    filename = png_file.name
                    skip_patterns = [
                        "colorized_dem",     # Visualization files like colorized_dem.png
                        "elevation_colorized", # Colorized elevation files
                        "visualization",     # General visualization files
                        "preview",          # Preview files
                        "thumbnail",        # Thumbnail files
                        "_raw",            # Raw unprocessed files
                        "_temp"            # Temporary files
                        # Note: _sentinel2_ pattern removed to allow NDVI files
                    ]
                    
                    # Special handling for Sentinel-2 files: only allow NDVI
                    if "_sentinel2_" in filename.lower():
                        if "ndvi" not in filename.lower():
                            print(f"  🛰️ Skipping non-NDVI Sentinel-2 file: {filename}")
                            continue
                        # If it's NDVI, allow it to continue
                    
                    if any(pattern in filename.lower() for pattern in skip_patterns):
                        print(f"  ⏭️ Skipping visualization/non-processing file: {filename}")
                        continue
                    
                    # Extract processing type from path patterns
                    path_parts = relative_path.parts
                    if "png_outputs" in path_parts:
                        # Pattern: lidar/png_outputs/filename_elevation_type.png
                        filename = png_file.stem
                        if "_sentinel2_NDVI" in filename:
                            processing_type = "ndvi"
                            display_name = "NDVI (Normalized Difference Vegetation Index)"
                        elif "_elevation_" in filename:
                            processing_type = filename.split("_elevation_")[-1]
                            display_name = processing_type.replace("_", " ").title()
                        elif filename.endswith("_hillshade"):
                            processing_type = "hillshade"
                            display_name = "Hillshade"
                        elif filename.endswith("_slope"):
                            processing_type = "slope"
                            display_name = "Slope"
                        elif filename.endswith("_aspect"):
                            processing_type = "aspect"
                            display_name = "Aspect"
                        # Skip Sentinel-2 files - they belong in the satellite gallery, not raster gallery
                        elif "_sentinel2_" in filename:
                            print(f"  🛰️ Skipping Sentinel-2 file for raster gallery: {filename}")
                            continue
                        else:
                                # Try to extract processing type from filename patterns
                                # Pattern: regionname_processtype.png or regionname_date_processtype.png
                                filename_parts = filename.split('_')
                                if len(filename_parts) >= 2:
                                    # Take the last part as processing type
                                    last_part = filename_parts[-1].lower()
                                    type_mapping = {
                                        'hillshade': 'hillshade',
                                        'slope': 'slope', 
                                        'aspect': 'aspect',
                                        'chm': 'chm',
                                        'dtm': 'dtm',
                                        'dsm': 'dsm',
                                        'lrm': 'lrm',
                                        'tpi': 'tpi',
                                        'tri': 'tri',
                                        'roughness': 'roughness',
                                        'ndvi': 'ndvi'  # Include NDVI in raster gallery
                                    }
                                    processing_type = type_mapping.get(last_part, None)
                                    if processing_type:
                                        if last_part == 'ndvi':
                                            display_name = "NDVI (Normalized Difference Vegetation Index)"
                                        else:
                                            display_name = last_part.replace("_", " ").title()
                                    else:
                                        # Skip files with unknown processing types
                                        print(f"  ⏭️ Skipping file with unknown processing type: {filename} (last_part: {last_part})")
                                        continue
                                else:
                                    # Direct processing type names (e.g., TintOverlay.png, HillshadeRGB.png, LRM.png, SVF.png)
                                    direct_type_mapping = {
                                        'tintoverlay': 'tint_overlay',
                                        'hillshadergb': 'hillshade_rgb', 
                                        'lrm': 'lrm',
                                        'svf': 'sky_view_factor',
                                        'slope': 'slope',
                                        'aspect': 'aspect',
                                        'chm': 'chm',
                                        'dtm': 'dtm',
                                        'dsm': 'dsm',
                                        'roughness': 'roughness',
                                        'tpi': 'tpi',
                                        'tri': 'tri'
                                    }
                                    filename_lower = filename.lower()
                                    processing_type = direct_type_mapping.get(filename_lower, None)
                                    if processing_type:
                                        display_name = filename.replace("_", " ").replace("RGB", " RGB").replace("SVF", "Sky View Factor")
                                        print(f"  🔍 Direct mapping: {filename} -> {processing_type} ({display_name})")
                                    else:
                                        # Skip files that don't match any known processing type
                                        print(f"  ⏭️ Skipping file with unmapped processing type: {filename}")
                                        continue
                    elif "lidar" in path_parts:
                        # Pattern: lidar/ProcessingType/filename.png
                        for i, part in enumerate(path_parts):
                            if part == "lidar" and i + 1 < len(path_parts):
                                processing_type = path_parts[i + 1].lower()
                                display_name = path_parts[i + 1]
                                break
                    elif "sentinel2" in path_parts:
                        # Skip Sentinel-2 files - they belong in the satellite gallery, not raster gallery
                        print(f"  🛰️ Skipping Sentinel-2 file for raster gallery: {png_file.name}")
                        continue
                    
                    png_files.append({
                        "file_path": str(png_file),
                        "relative_path": str(relative_path),
                        "file_name": png_file.name,
                        "file_size_mb": file_size_mb,
                        "processing_type": processing_type,
                        "display_name": display_name,
                        "source_dir": base_dir
                    })
                    
                except Exception as e:
                    print(f"⚠️ Error processing PNG file {png_file}: {e}")
                    continue
        
        print(f"📸 Found {len(png_files)} PNG files for region {region_name}")
        
        # Sort by processing type and file name
        png_files.sort(key=lambda x: (x["processing_type"], x["file_name"]))
        
        return {
            "success": True,
            "region_name": region_name,
            "png_files": png_files,
            "total_files": len(png_files)
        }
        
    except Exception as e:
        print(f"❌ Error getting PNG files for region {region_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get PNG files: {str(e)}")

# ============================================================================
# REGION METADATA API ENDPOINTS  
# ============================================================================

async def _auto_download_dsm_for_region(region_name: str, lat: float, lng: float) -> Dict:
    """
    Automatically download SRTM DSM data for a coordinate-based region
    
    Args:
        region_name: Name of the region
        lat: Latitude of the center point
        lng: Longitude of the center point
        
    Returns:
        Dictionary with download results
    """
    try:
        from ..services.true_dsm_service import true_dsm_service
        
        print(f"🏔️ Auto-downloading SRTM DSM data for region: {region_name}")
        print(f"📍 Coordinates: ({lat}, {lng})")
        
        # Download SRTM DSM with default settings (12.5km buffer, 1-arcsecond resolution)
        result = await true_dsm_service.get_srtm_dsm_for_region(
            lat=lat,
            lng=lng,
            region_name=region_name,
            buffer_km=12.5,
            resolution=1  # SRTM 1-arcsecond (~30m)
        )
        
        if result.get('success'):
            print(f"✅ Successfully auto-downloaded SRTM DSM for region: {region_name}")
            print(f"📁 SRTM DSM file saved to: {result.get('file_path')}")
            return {
                "success": True,
                "dsm_downloaded": True,
                "dsm_file": result.get('file_path'),
                "method": result.get('method', 'unknown')
            }
        else:
            print(f"⚠️ Failed to auto-download DSM for region: {region_name}")
            print(f"🔍 Error: {result.get('error')}")
            return {
                "success": True,  # Don't fail region creation if DSM download fails
                "dsm_downloaded": False,
                "error": result.get('error')
            }
            
    except Exception as e:
        print(f"❌ Error in auto DSM download for region {region_name}: {str(e)}")
        return {
            "success": True,  # Don't fail region creation if DSM download fails
            "dsm_downloaded": False,
            "error": str(e)
        }

@router.post("/api/regions/{region_name}/download-dsm")
async def download_dsm_for_region(region_name: str, data: dict = None):
    """
    Download SRTM DSM data for an existing region
    
    Args:
        region_name: Name of the region
        data: Optional parameters including buffer_km and resolution
    """
    try:
        print(f"\n🌍 API CALL: POST /api/regions/{region_name}/download-dsm")
        
        # Check if region exists and has coordinates
        metadata_data = _read_coordinates_from_metadata(region_name)
        if not metadata_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Region '{region_name}' not found or has no coordinate information"
            )
        
        # Extract coordinates
        if len(metadata_data) >= 2:
            lat, lng = metadata_data[0], metadata_data[1]
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Region '{region_name}' does not have valid coordinates"
            )
        
        # Get optional parameters
        buffer_km = 12.5
        resolution = "30m"
        
        if data:
            buffer_km = data.get('buffer_km', 12.5)
            resolution = data.get('resolution', '30m')
            
            # Validate parameters
            if not (0.1 <= buffer_km <= 50.0):
                raise HTTPException(status_code=400, detail="buffer_km must be between 0.1 and 50.0")
            
            if resolution not in ['30m', '90m']:
                raise HTTPException(status_code=400, detail="resolution must be '30m' or '90m'")
        
        print(f"📍 Region coordinates: ({lat}, {lng})")
        print(f"📏 Buffer: {buffer_km} km")
        print(f"🔍 Resolution: {resolution}")
        
        # Import the SRTM DSM service
        from ..services.true_dsm_service import true_dsm_service
        
        # Download SRTM DSM data
        result = await true_dsm_service.get_srtm_dsm_for_region(
            lat=lat,
            lng=lng,
            region_name=region_name,
            buffer_km=buffer_km,
            resolution=1  # SRTM 1-arcsecond (~30m)
        )
        
        if result.get('success'):
            print(f"✅ Successfully downloaded SRTM DSM for region: {region_name}")
            
            return JSONResponse(content={
                "success": True,
                "message": f"SRTM DSM (True Surface Model) downloaded successfully for region '{region_name}'",
                "region_name": region_name,
                "dsm_file": result.get('file_path'),
                "method": result.get('method'),
                "tiles_downloaded": result.get('tiles_downloaded'),
                "metadata": result.get('metadata'),
                "parameters": {
                    "buffer_km": buffer_km,
                    "resolution": resolution,
                    "coordinates": {"lat": lat, "lng": lng}
                }
            })
        else:
            print(f"❌ Failed to download DSM for region: {region_name}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to download DSM: {result.get('error', 'Unknown error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error downloading DSM for region {region_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

