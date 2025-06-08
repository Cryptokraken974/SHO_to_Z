"""
Geospatial utilities for reading coordinate information from world files and GeoTIFF files.
"""
import os
import base64
import re
from typing import Dict, Tuple, Optional
from osgeo import gdal, osr

def read_world_file(world_file_path: str) -> Optional[Dict]:
    """
    Read world file and return transformation parameters.
    World file format:
    Line 1: pixel size in the x-direction in map units/pixel
    Line 2: rotation about y-axis
    Line 3: rotation about x-axis  
    Line 4: pixel size in the y-direction in map units (negative value)
    Line 5: x-coordinate of the center of the upper left pixel
    Line 6: y-coordinate of the center of the upper left pixel
    """
    try:
        if not os.path.exists(world_file_path):
            return None
            
        with open(world_file_path, 'r') as f:
            lines = [float(line.strip()) for line in f.readlines()]
            
        if len(lines) != 6:
            return None
            
        return {
            'pixel_size_x': lines[0],
            'rotation_y': lines[1], 
            'rotation_x': lines[2],
            'pixel_size_y': lines[3],
            'upper_left_x': lines[4],
            'upper_left_y': lines[5]
        }
    except Exception as e:
        print(f"Error reading world file {world_file_path}: {e}")
        return None

def get_image_bounds_from_world_file(world_file_path: str, image_width: int, image_height: int, src_epsg: int = None) -> Optional[Dict]:
    """
    Calculate geographic bounds of an image using its world file.
    Returns bounds in format: {'north': lat, 'south': lat, 'east': lng, 'west': lng}
    """
    world_data = read_world_file(world_file_path)
    if not world_data:
        return None
        
    # Calculate bounds
    upper_left_x = world_data['upper_left_x']
    upper_left_y = world_data['upper_left_y']
    pixel_size_x = world_data['pixel_size_x']
    pixel_size_y = world_data['pixel_size_y']  # Usually negative
    
    # Calculate corner coordinates in source projection
    west = upper_left_x
    east = upper_left_x + (image_width * pixel_size_x)
    north = upper_left_y
    south = upper_left_y + (image_height * pixel_size_y)  # pixel_size_y is negative
    
    print(f"🗺️  Image bounds in source projection:")
    print(f"   West: {west}, East: {east}")
    print(f"   North: {north}, South: {south}")
    
    # If we have EPSG code, transform to WGS84
    if src_epsg and src_epsg != 4326:
        try:
            print(f"🌍 Transforming from EPSG:{src_epsg} to WGS84...")
            
            # Create coordinate transformation
            source_srs = osr.SpatialReference()
            source_srs.ImportFromEPSG(src_epsg)
            
            target_srs = osr.SpatialReference()
            target_srs.ImportFromEPSG(4326)  # WGS84
            
            transform = osr.CoordinateTransformation(source_srs, target_srs)
            
            # Transform corner points
            sw_result = transform.TransformPoint(west, south)
            sw_lon, sw_lat = sw_result[0], sw_result[1]
            ne_result = transform.TransformPoint(east, north)
            ne_lon, ne_lat = ne_result[0], ne_result[1]
            nw_result = transform.TransformPoint(west, north)
            nw_lon, nw_lat = nw_result[0], nw_result[1]
            se_result = transform.TransformPoint(east, south)
            se_lon, se_lat = se_result[0], se_result[1]
            
            # Apply coordinate order correction based on EPSG code and axis order
            sw_lon, sw_lat, ne_lon, ne_lat, nw_lon, nw_lat, se_lon, se_lat = correct_coordinate_order(
                source_srs, src_epsg, sw_lon, sw_lat, ne_lon, ne_lat, nw_lon, nw_lat, se_lon, se_lat
            )
            
            # Get the actual bounds after transformation
            final_west = min(sw_lon, nw_lon, se_lon, ne_lon)
            final_east = max(sw_lon, nw_lon, se_lon, ne_lon)
            final_south = min(sw_lat, nw_lat, se_lat, ne_lat)
            final_north = max(sw_lat, nw_lat, se_lat, ne_lat)
            
            print(f"🌍 Transformed bounds (WGS84):")
            print(f"   West: {final_west}, East: {final_east}")
            print(f"   North: {final_north}, South: {final_south}")
            
        except Exception as e:
            print(f"❌ Error transforming coordinates: {e}")
            # Fall back to assuming WGS84
            final_west, final_east = west, east
            final_south, final_north = south, north
            
    else:
        # Assume coordinates are already in WGS84 or no transformation specified
        print(f"🌍 No transformation specified, using coordinates as-is")
        final_west, final_east = west, east
        final_south, final_north = south, north
    
    return {
        'north': final_north,
        'south': final_south,
        'east': final_east,
        'west': final_west,
        'center_lat': (final_north + final_south) / 2,
        'center_lng': (final_east + final_west) / 2,
        'source_epsg': src_epsg
    }

def get_image_bounds_from_geotiff(tiff_path: str) -> Optional[Dict]:
    """
    Extract geographic bounds directly from a GeoTIFF file.
    """
    try:
        dataset = gdal.Open(tiff_path)
        if not dataset:
            return None
            
        # Get geotransform
        geotransform = dataset.GetGeoTransform()
        if not geotransform:
            return None
            
        # Get image dimensions
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        
        # Extract transformation parameters
        upper_left_x = geotransform[0]
        pixel_size_x = geotransform[1]
        rotation_x = geotransform[2]
        upper_left_y = geotransform[3]
        rotation_y = geotransform[4]
        pixel_size_y = geotransform[5]
        
        # Calculate bounds in source projection
        west = upper_left_x
        east = upper_left_x + (width * pixel_size_x)
        north = upper_left_y
        south = upper_left_y + (height * pixel_size_y)
        
        # Get coordinate system info
        projection = dataset.GetProjection()
        srs = osr.SpatialReference()
        srs.ImportFromWkt(projection)
        
        epsg_code = None
        if srs.GetAttrValue('AUTHORITY', 0) == 'EPSG':
            epsg_code = int(srs.GetAttrValue('AUTHORITY', 1))
        
        print(f"🗺️  GeoTIFF bounds in source projection (EPSG:{epsg_code}):")
        print(f"   West: {west}, East: {east}")
        print(f"   North: {north}, South: {south}")
        
        dataset = None  # Close dataset
        
        # Transform to WGS84 if needed
        if epsg_code and epsg_code != 4326:
            try:
                print(f"🌍 Transforming from EPSG:{epsg_code} to WGS84...")
                
                # Create coordinate transformation
                target_srs = osr.SpatialReference()
                target_srs.ImportFromEPSG(4326)  # WGS84
                
                transform = osr.CoordinateTransformation(srs, target_srs)
                
                # Transform corner points
                print(f"🔄 Transforming corners:")
                sw_result = transform.TransformPoint(west, south)
                sw_lon, sw_lat = sw_result[0], sw_result[1]
                print(f"   SW: ({west}, {south}) -> ({sw_lon}, {sw_lat})")
                
                ne_result = transform.TransformPoint(east, north)
                ne_lon, ne_lat = ne_result[0], ne_result[1]
                print(f"   NE: ({east}, {north}) -> ({ne_lon}, {ne_lat})")
                
                nw_result = transform.TransformPoint(west, north)
                nw_lon, nw_lat = nw_result[0], nw_result[1]
                print(f"   NW: ({west}, {north}) -> ({nw_lon}, {nw_lat})")
                
                se_result = transform.TransformPoint(east, south)
                se_lon, se_lat = se_result[0], se_result[1]
                print(f"   SE: ({east}, {south}) -> ({se_lon}, {se_lat})")
                
                # Check if coordinates seem swapped
                # For Oregon, we expect longitude around -122 and latitude around 42
                # If we see latitude-like values in the "longitude" position, swap them
                avg_lon = (sw_lon + ne_lon + nw_lon + se_lon) / 4
                avg_lat = (sw_lat + ne_lat + nw_lat + se_lat) / 4
                
                print(f"🔍 Average transformed coordinates: lon={avg_lon}, lat={avg_lat}")
                
                # Check if the "longitude" values look like latitudes (positive values for US)
                # and "latitude" values look like longitudes (negative values for US West Coast)
                if (avg_lon > 0 and avg_lon < 90 and avg_lat < -90):
                    print("🔄 Coordinates appear to be in lat/lon order, swapping to lon/lat...")
                    # Swap the coordinates
                    sw_lon, sw_lat = sw_lat, sw_lon
                    ne_lon, ne_lat = ne_lat, ne_lon
                    nw_lon, nw_lat = nw_lat, nw_lon
                    se_lon, se_lat = se_lat, se_lon
                    print(f"   SW swapped: ({sw_lon}, {sw_lat})")
                    print(f"   NE swapped: ({ne_lon}, {ne_lat})")
                    print(f"   NW swapped: ({nw_lon}, {nw_lat})")
                    print(f"   SE swapped: ({se_lon}, {se_lat})")
                
                # Get the actual bounds after transformation
                final_west = min(sw_lon, nw_lon, se_lon, ne_lon)
                final_east = max(sw_lon, nw_lon, se_lon, ne_lon)
                final_south = min(sw_lat, nw_lat, se_lat, ne_lat)
                final_north = max(sw_lat, nw_lat, se_lat, ne_lat)
                
                print(f"🌍 Transformed bounds (WGS84):")
                print(f"   West: {final_west}, East: {final_east}")
                print(f"   North: {final_north}, South: {final_south}")
                
            except Exception as e:
                print(f"❌ Error transforming coordinates: {e}")
                # Fall back to source coordinates
                final_west, final_east = west, east
                final_south, final_north = south, north
        else:
            # Already in WGS84 or no transformation needed
            final_west, final_east = west, east
            final_south, final_north = south, north
        
        return {
            'north': final_north,
            'south': final_south,
            'east': final_east,
            'west': final_west,
            'center_lat': (final_north + final_south) / 2,
            'center_lng': (final_east + final_west) / 2,
            'projection': projection,
            'epsg': epsg_code
        }
        
    except Exception as e:
        print(f"Error reading GeoTIFF {tiff_path}: {e}")
        return None

def get_laz_overlay_data(base_filename: str, processing_type: str, filename_processing_type: str = None) -> Optional[Dict]:
    """
    Get overlay data for LAZ-processed images (DTM, Hillshade, etc.) including bounds and base64 encoded image.
    
    Args:
        base_filename: The base name of the LAZ file (e.g., 'OR_WizardIsland', 'FoxIsland')
        processing_type: The folder name (e.g., 'Hillshade', 'DTM', 'Slope')
        filename_processing_type: The specific processing type for filename mapping (e.g., 'hillshade_315_45_08')
    """
    try:
        print(f"\n🔍 Getting LAZ overlay data for {base_filename}/{processing_type}")
        if filename_processing_type:
            print(f"🔍 Using filename processing type: {filename_processing_type}")
        
        # Try multiple possible directory structures and filename patterns
        possible_paths = []
        
        # Use filename_processing_type for mapping if provided, otherwise use processing_type
        mapping_key = filename_processing_type if filename_processing_type else processing_type
        
        # Pattern 1: Unified structure - output/{base_filename}/lidar/{processing_type}/{base_filename}_{suffix}.png
        output_dir1 = f"output/{base_filename}/lidar/{processing_type}"
        
        # Pattern 2: LAZ structure - output/LAZ/{base_filename}/{processing_type_lower}/{base_filename}_{processing_type_lower}_standard.png
        processing_type_lower = processing_type.lower()
        output_dir2 = f"output/LAZ/{base_filename}/{processing_type_lower}"
        
        # Pattern 3: Region PNG outputs - output/{base_filename}/lidar/png_outputs/{region_coords}_elevation_{processing_type_lower}.png
        output_dir3 = f"output/{base_filename}/lidar/png_outputs"
        
        # Map processing type to filename suffix
        filename_mapping = {
            'DEM': 'DEM',
            'DTM': 'DTM', 
            'DSM': 'DSM',
            'CHM': 'CHM',
            'Hillshade': 'Hillshade',
            'hillshade_315_45_08': 'Hillshade_315_45_08',
            'hillshade_225_45_08': 'Hillshade_225_45_08', 
            'Slope': 'Slope',
            'Aspect': 'Aspect',
            'Color_Relief': 'ColorRelief',
            'ColorRelief': 'ColorRelief',
            'TRI': 'TRI',
            'TPI': 'TPI',
            'Roughness': 'Roughness'
        }
        
        filename_suffix = filename_mapping.get(mapping_key, mapping_key.title())
        
        # Add possible file paths in order of preference
        # Pattern 0: PRIORITY - PNG outputs consolidated directory (NEW STANDARD)
        png_outputs_pattern = f"output/{base_filename}/lidar/png_outputs/{base_filename}_elevation_{processing_type_lower}.png"
        if os.path.exists(f"output/{base_filename}/lidar/png_outputs"):
            # Check for files in png_outputs with elevation pattern
            if os.path.exists(png_outputs_pattern):
                base_name = os.path.splitext(os.path.basename(png_outputs_pattern))[0]
                possible_paths.append({
                    'png': png_outputs_pattern,
                    'tiff': f"output/{base_filename}/lidar/png_outputs/{base_name}.tif",
                    'world': f"output/{base_filename}/lidar/png_outputs/{base_name}.wld",
                    'desc': 'PNG outputs consolidated directory (PRIORITY)'
                })
            else:
                # Try alternative naming patterns in png_outputs
                import glob
                search_patterns = [
                    f"output/{base_filename}/lidar/png_outputs/{base_filename}_elevation_{processing_type_lower}*.png",
                    f"output/{base_filename}/lidar/png_outputs/*_elevation_{processing_type_lower}.png",
                    f"output/{base_filename}/lidar/png_outputs/{base_filename}_{filename_suffix}*.png"
                ]
                
                for pattern in search_patterns:
                    matching_files = glob.glob(pattern)
                    if matching_files:
                        png_file = matching_files[0]  # Use first match
                        base_name = os.path.splitext(os.path.basename(png_file))[0]
                        possible_paths.append({
                            'png': png_file,
                            'tiff': f"output/{base_filename}/lidar/png_outputs/{base_name}.tif",
                            'world': f"output/{base_filename}/lidar/png_outputs/{base_name}.wld",
                            'desc': 'PNG outputs consolidated directory (FOUND)'
                        })
                        break

        # Pattern 1: New unified structure
        possible_paths.append({
            'png': f"{output_dir1}/{base_filename}_{filename_suffix}.png",
            'tiff': f"{output_dir1}/{base_filename}_{filename_suffix}.tif", 
            'world': f"{output_dir1}/{base_filename}_{filename_suffix}.wld",
            'desc': 'Unified structure'
        })
        
        # Pattern 2: LAZ processing structure
        possible_paths.append({
            'png': f"{output_dir2}/{base_filename}_{processing_type_lower}_standard.png",
            'tiff': f"{output_dir2}/{base_filename}_{processing_type_lower}_standard.tif",
            'world': f"{output_dir2}/{base_filename}_{processing_type_lower}_standard.wld", 
            'desc': 'LAZ processing structure'
        })
        
        # Pattern 3: Look for region-based files in png_outputs (try to find matching pattern)
        if os.path.exists(output_dir3):
            import glob
            # Look for files matching pattern: *_elevation_{processing_type}.png
            search_pattern = f"{output_dir3}/*_elevation_{processing_type_lower}.png"
            matching_files = glob.glob(search_pattern)
            
            if matching_files:
                # Use the first matching file
                png_file = matching_files[0]
                base_name = os.path.splitext(os.path.basename(png_file))[0]
                possible_paths.append({
                    'png': png_file,
                    'tiff': f"{output_dir3}/{base_name}.tif",
                    'world': f"{output_dir3}/{base_name}.wld",
                    'desc': 'Region PNG outputs structure'
                })

        # Pattern 4: Old scattered structure - output/{base_filename}/lidar/{processing_type}/{base_filename}_{processing_type}.png
        # This is for backwards compatibility with older processing results
        old_scattered_dir = f"output/{base_filename}/lidar/{processing_type}"
        if os.path.exists(old_scattered_dir):
            # Try different filename patterns for old structure
            old_patterns = [
                f"{old_scattered_dir}/{base_filename}_{processing_type}.png",
                f"{old_scattered_dir}/{base_filename}_{processing_type}_standard.png",
                f"{old_scattered_dir}/{base_filename}_{filename_suffix}.png",
                f"{old_scattered_dir}/{base_filename}_{filename_suffix}_standard.png"
            ]
            
            for pattern in old_patterns:
                if os.path.exists(pattern):
                    base_name = os.path.splitext(os.path.basename(pattern))[0]
                    possible_paths.append({
                        'png': pattern,
                        'tiff': f"{old_scattered_dir}/{base_name}.tif",
                        'world': f"{old_scattered_dir}/{base_name}.wld",
                        'desc': f'Old scattered structure ({processing_type} folder)'
                    })
                    break
        
        # Try each possible path until we find one that works
        for i, path_info in enumerate(possible_paths):
            png_path = path_info['png']
            tiff_path = path_info['tiff'] 
            world_path = path_info['world']
            desc = path_info['desc']
            
            print(f"\n🔍 Trying path {i+1}: {desc}")
            print(f"📂 PNG path: {png_path}")
            print(f"🗺️  TIFF path: {tiff_path}")
            print(f"🌍 World path: {world_path}")
            
            if os.path.exists(png_path):
                print(f"✅ Found PNG file: {png_path}")
                
                # Check for optimized overlay version first
                overlay_png_path = _get_optimized_overlay_path(png_path)
                if overlay_png_path and os.path.exists(overlay_png_path):
                    print(f"🎯 Using optimized overlay: {overlay_png_path}")
                    # Update paths to use optimized versions
                    overlay_tiff_path = overlay_png_path.replace('.png', '.tif')
                    overlay_world_path = overlay_png_path.replace('.png', '.wld')
                    return _process_overlay_files(overlay_png_path, overlay_tiff_path, overlay_world_path, processing_type, base_filename, is_optimized=True)
                else:
                    print(f"📂 Using original file: {png_path}")
                    return _process_overlay_files(png_path, tiff_path, world_path, processing_type, base_filename)
            else:
                print(f"❌ PNG file not found: {png_path}")
        
        # If no files found, debug what's actually available
        print(f"\n🔍 No overlay files found. Debugging available files...")
        debug_dirs = [
            f"output/{base_filename}",
            f"output/LAZ/{base_filename}",
            f"output/{base_filename}/lidar"
        ]
        
        for debug_dir in debug_dirs:
            if os.path.exists(debug_dir):
                print(f"📁 Available in {debug_dir}:")
                try:
                    for item in os.listdir(debug_dir):
                        item_path = os.path.join(debug_dir, item)
                        if os.path.isdir(item_path):
                            print(f"   📁 {item}/")
                        else:
                            print(f"   📄 {item}")
                except Exception as e:
                    print(f"   ❌ Error listing directory: {e}")
            else:
                print(f"📁 Directory does not exist: {debug_dir}")
        
        return None
        
    except Exception as e:
        print(f"❌ Error getting LAZ overlay data for {base_filename}/{processing_type}: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_sentinel2_overlay_data_util(region_name: str, band_name: str) -> Optional[Dict]:
    """
    Get overlay data for Sentinel-2 images including bounds and base64 encoded image.
    
    Args:
        region_name: The region name (e.g., 'region_13_96S_48_33W')
        band_name: The band name (e.g., 'RED_B04', 'NIR_B08', 'NDVI')
    """
    try:
        print(f"\n🛰️ Getting Sentinel-2 overlay data for {region_name}/{band_name}")
        
        # Convert region name format from API format to actual folder format
        # API format: region_5_99S_36_15W -> Folder format: 5.99S_36.15W
        folder_region_name = region_name
        if region_name.startswith('region_'):
            # Remove 'region_' prefix and convert underscores back to dots for coordinates
            folder_region_name = region_name[7:]  # Remove 'region_' prefix
            # Convert coordinate format: 5_99S_36_15W -> 5.99S_36.15W
            # Replace the first underscore with a dot, and the third underscore with a dot
            # Pattern: X_YYZ_AA_BBW -> X.YYZ_AA.BBW
            import re
            # Use regex to replace underscores in coordinate positions with dots
            # This will convert: 5_99S_36_15W -> 5.99S_36.15W
            folder_region_name = re.sub(r'^(\d+)_(\d+)([NS])_(\d+)_(\d+)([EW])$', r'\1.\2\3_\4.\5\6', folder_region_name)
        
        print(f"🔄 Converted region name: {region_name} -> {folder_region_name}")
        
        # Construct paths for Sentinel-2 files using the correct folder format
        # Structure: output/{folder_region_name}/sentinel2/{folder_region_name}_{timestamp}_sentinel2_{band_name}.png
        output_dir = f"output/{folder_region_name}/sentinel2"
        
        # Find actual files matching the pattern since they include timestamps
        import glob
        
        # Pattern: {folder_region_name}_*_sentinel2_{band_name}.png OR {folder_region_name}_*_{band_name}.png (for NDVI)
        if band_name == 'NDVI':
            # NDVI files have pattern: {folder_region_name}_*_NDVI.png
            png_pattern = f"{output_dir}/{folder_region_name}_*_{band_name}.png"
            tiff_pattern = f"{output_dir}/{folder_region_name}_*_{band_name}.tif"
        else:
            # Regular bands have pattern: {folder_region_name}_*_sentinel2_{band_name}.png
            png_pattern = f"{output_dir}/{folder_region_name}_*_sentinel2_{band_name}.png"
            tiff_pattern = f"{output_dir}/{folder_region_name}_*_sentinel2_{band_name}.tif"
        
        print(f"📂 Output directory: {output_dir}")
        print(f"🔍 PNG pattern: {png_pattern}")
        print(f"🔍 TIFF pattern: {tiff_pattern}")
        
        png_files = glob.glob(png_pattern)
        tiff_files = glob.glob(tiff_pattern)
        
        print(f"📁 Found PNG files: {png_files}")
        print(f"📁 Found TIFF files: {tiff_files}")
        
        if png_files:
            # Sort files by modification time to get the most recent
            png_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            png_path = png_files[0]  # Use the most recent file
            # Derive world file path from PNG (replace .png with .wld)
            world_path = png_path.replace('.png', '.wld')
            # Use corresponding TIF file if available
            if tiff_files:
                # Find matching TIF file with same timestamp
                png_basename = os.path.basename(png_path).replace('.png', '')
                matching_tiff = next((tf for tf in tiff_files if png_basename in tf), tiff_files[0])
                tiff_path = matching_tiff
            else:
                tiff_path = png_path.replace('.png', '.tif')
            
            print(f"📄 Selected files from {len(png_files)} available PNG files")
        else:
            print(f"❌ No PNG files found matching pattern: {png_pattern}")
            # Debug: List what files actually exist
            if os.path.exists(output_dir):
                files = os.listdir(output_dir)
                print(f"🔍 Files in directory: {files}")
                # Suggest available bands if any sentinel-2 files exist
                s2_files = [f for f in files if ('sentinel2' in f or 'NDVI' in f) and f.endswith('.png')]
                if s2_files:
                    available_bands = set()
                    for f in s2_files:
                        if 'NDVI' in f:
                            available_bands.add('NDVI')
                        else:
                            parts = f.split('_')
                            if len(parts) >= 2:
                                band = '_'.join(parts[-2:]).replace('.png', '')
                                available_bands.add(band)
                    print(f"💡 Available Sentinel-2 bands: {list(available_bands)}")
            else:
                print(f"📂 Directory doesn't exist: {output_dir}")
            return None
        
        print(f"🖼️  PNG path: {png_path}")
        print(f"🗺️  TIFF path: {tiff_path}")
        print(f"🌍 World file path: {world_path}")
        
        # Check for optimized overlay version first
        overlay_png_path = _get_optimized_overlay_path(png_path)
        is_optimized = False
        
        if overlay_png_path and os.path.exists(overlay_png_path):
            print(f"🎯 Using optimized Sentinel-2 overlay: {overlay_png_path}")
            # Update paths to use optimized versions
            png_path = overlay_png_path
            # World file for optimized overlay
            world_path = png_path.replace('.png', '.wld')
            # Keep original TIFF for bounds extraction
            is_optimized = True
        else:
            print(f"📂 Using original Sentinel-2 file: {png_path}")
        
        return _process_overlay_files(png_path, tiff_path, world_path, "sentinel-2", folder_region_name, band_name, region_name, is_optimized)
        
    except Exception as e:
        print(f"❌ Error getting Sentinel-2 overlay data for {region_name}/{band_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def parse_coordinate_folder_name(folder_name: str) -> Tuple[float, float]:
    """
    Parse coordinates from folder names like '11.31S_44.06W' or 'foxisland'
    Returns (latitude, longitude) as floats
    """
    # Pattern for coordinate-based folder names: lat.longDIR_lat.longDIR
    coord_pattern = r'(\d+\.\d+)([ns])_(\d+\.\d+)([ew])'
    match = re.match(coord_pattern, folder_name.lower())
    
    if match:
        lat_val, lat_dir, lng_val, lng_dir = match.groups()
        
        # Convert to signed values
        lat = float(lat_val) * (-1 if lat_dir.lower() == 's' else 1)
        lng = float(lng_val) * (-1 if lng_dir.lower() == 'w' else 1)
        
        return lat, lng
    else:
        raise ValueError(f"Cannot parse coordinates from folder name: {folder_name}")

def _get_optimized_overlay_path(original_png_path: str) -> Optional[str]:
    """
    Get the path to an optimized overlay version of a PNG file.
    
    Args:
        original_png_path: Path to the original PNG file
        
    Returns:
        Path to optimized overlay if it exists, None otherwise
    """
    try:
        # Extract directory and filename
        directory = os.path.dirname(original_png_path)
        filename = os.path.basename(original_png_path)
        
        # Create overlay filename with "_overlays" suffix
        if filename.endswith('.png'):
            overlay_filename = filename[:-4] + '_overlays.png'
        else:
            overlay_filename = filename + '_overlays'
        
        overlay_path = os.path.join(directory, overlay_filename)
        
        print(f"🔍 Checking for optimized overlay: {overlay_path}")
        return overlay_path if os.path.exists(overlay_path) else None
        
    except Exception as e:
        print(f"❌ Error checking for optimized overlay: {e}")
        return None

def _process_overlay_files(png_path: str, tiff_path: str, world_path: str, processing_type: str, base_filename: str, band_name: str = None, region_name: str = None, is_optimized: bool = False) -> Optional[Dict]:
    """
    Common function to process overlay files and extract bounds and image data.
    """
    try:
        # Check if files exist
        print(f"📁 PNG exists: {os.path.exists(png_path)}")
        print(f"🗺️  TIFF exists: {os.path.exists(tiff_path)}")
        print(f"🌍 World file exists: {os.path.exists(world_path)}")
        
        if not os.path.exists(png_path):
            print(f"❌ PNG file not found: {png_path}")
            return None
        
        # Try to get bounds from GeoTIFF first, then world file
        bounds = None
        epsg_code = None
        
        if os.path.exists(tiff_path):
            print("🗺️  Trying to extract bounds from GeoTIFF...")
            bounds = get_image_bounds_from_geotiff(tiff_path)
            if bounds:
                epsg_code = bounds.get('epsg')
                print(f"✅ Bounds from GeoTIFF: {bounds}")
            else:
                print("❌ Failed to extract bounds from GeoTIFF")
            
        if not bounds and os.path.exists(world_path):
            print("🌍 Trying to extract bounds from world file...")
            # Get image dimensions from PNG
            from PIL import Image
            with Image.open(png_path) as img:
                width, height = img.size
            print(f"📏 Image dimensions: {width}x{height}")
            
            # If we got EPSG from an associated TIFF, use it for world file transformation
            if not epsg_code:
                # Try to guess based on coordinates
                test_bounds = get_image_bounds_from_world_file(world_path, width, height, None)
                if test_bounds:
                    # Check if coordinates look like UTM (large numbers)
                    if (abs(test_bounds['west']) > 180 or abs(test_bounds['east']) > 180 or 
                        abs(test_bounds['north']) > 90 or abs(test_bounds['south']) > 90):
                        # Coordinates appear to be projected - try common UTM zones
                        # For US East Coast (like Maine): UTM Zone 19N
                        # For US West Coast (like Oregon): UTM Zone 10N
                        # Default to UTM Zone 19N for now
                        epsg_code = 32619
                        print(f"🔍 Coordinates appear projected, assuming UTM Zone 19N (EPSG:{epsg_code})")
                    else:
                        print(f"🔍 Coordinates appear to be in geographic (lat/lon) format")
            
            bounds = get_image_bounds_from_world_file(world_path, width, height, epsg_code)
            if bounds:
                print(f"✅ Bounds from world file: {bounds}")
            else:
                print("❌ Failed to extract bounds from world file")
            
        if not bounds:
            print("❌ No coordinate information found")
            return None
            
        # Read and encode PNG image
        print("🖼️  Reading and encoding PNG image...")
        with open(png_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            
        print(f"✅ Successfully prepared overlay data")
        result = {
            'bounds': bounds,
            'image_data': image_data,
            'processing_type': processing_type,
            'filename': base_filename,
            'is_optimized': is_optimized
        }
        
        # Add band and region info if available
        if band_name:
            result['band'] = band_name
        if region_name:
            result['region'] = region_name
        
        # Add optimization metadata
        if is_optimized:
            result['optimization_info'] = {
                'source': 'automatic_overlay_generation',
                'optimized_for_browser': True,
                'original_file': png_path.replace('_overlays.png', '.png')
            }
            
        return result
        
    except Exception as e:
        print(f"❌ Error processing overlay files: {e}")
        import traceback
        traceback.print_exc()
        return None

# Keep original function for backwards compatibility, but route to appropriate new function
def find_png_files(base_filename: str, processing_type: str, filename_processing_type: str = None) -> list:
    """
    Find PNG files for a specific region and processing type using the same fallback patterns as get_laz_overlay_data.
    
    Args:
        base_filename: The base name of the LAZ file (e.g., 'OR_WizardIsland', 'FoxIsland')
        processing_type: The folder name (e.g., 'Hillshade', 'DTM', 'Slope')
        filename_processing_type: The specific processing type for filename mapping (e.g., 'hillshade_315_45_08')
        
    Returns:
        List of found PNG file paths
    """
    try:
        print(f"\n🔍 Finding PNG files for {base_filename}/{processing_type}")
        
        found_png_files = []
        
        # Use filename_processing_type for mapping if provided, otherwise use processing_type
        mapping_key = filename_processing_type if filename_processing_type else processing_type
        
        # Pattern 1: Unified structure - output/{base_filename}/lidar/{processing_type}/{base_filename}_{suffix}.png
        output_dir1 = f"output/{base_filename}/lidar/{processing_type}"
        
        # Pattern 2: LAZ structure - output/LAZ/{base_filename}/{processing_type_lower}/{base_filename}_{processing_type_lower}_standard.png
        processing_type_lower = processing_type.lower()
        output_dir2 = f"output/LAZ/{base_filename}/{processing_type_lower}"
        
        # Pattern 3: Region PNG outputs - output/{base_filename}/lidar/png_outputs/{region_coords}_elevation_{processing_type_lower}.png
        output_dir3 = f"output/{base_filename}/lidar/png_outputs"
        
        # Map processing type to filename suffix
        filename_mapping = {
            'DEM': 'DEM',
            'DTM': 'DTM', 
            'DSM': 'DSM',
            'CHM': 'CHM',
            'Hillshade': 'Hillshade',
            'hillshade_315_45_08': 'Hillshade_315_45_08',
            'hillshade_225_45_08': 'Hillshade_225_45_08', 
            'Slope': 'Slope',
            'Aspect': 'Aspect',
            'Color_Relief': 'ColorRelief',
            'ColorRelief': 'ColorRelief',
            'TRI': 'TRI',
            'TPI': 'TPI',
            'Roughness': 'Roughness'
        }
        
        filename_suffix = filename_mapping.get(mapping_key, mapping_key.title())
        
        # Check Pattern 0: PRIORITY - PNG outputs consolidated directory (NEW STANDARD)
        png_outputs_pattern = f"output/{base_filename}/lidar/png_outputs/{base_filename}_elevation_{processing_type_lower}.png"
        if os.path.exists(f"output/{base_filename}/lidar/png_outputs"):
            if os.path.exists(png_outputs_pattern):
                found_png_files.append({
                    'path': png_outputs_pattern,
                    'desc': 'PNG outputs consolidated directory (PRIORITY)'
                })
            else:
                # Try alternative naming patterns in png_outputs
                import glob
                search_patterns = [
                    f"output/{base_filename}/lidar/png_outputs/{base_filename}_elevation_{processing_type_lower}*.png",
                    f"output/{base_filename}/lidar/png_outputs/*_elevation_{processing_type_lower}.png",
                    f"output/{base_filename}/lidar/png_outputs/{base_filename}_{filename_suffix}*.png"
                ]
                
                for pattern in search_patterns:
                    matching_files = glob.glob(pattern)
                    if matching_files:
                        for png_file in matching_files:
                            found_png_files.append({
                                'path': png_file,
                                'desc': 'PNG outputs consolidated directory (FOUND)'
                            })

        # Check Pattern 1: New unified structure
        unified_png = f"{output_dir1}/{base_filename}_{filename_suffix}.png"
        if os.path.exists(unified_png):
            found_png_files.append({
                'path': unified_png,
                'desc': 'Unified structure'
            })
        
        # Check Pattern 2: LAZ processing structure
        laz_png = f"{output_dir2}/{base_filename}_{processing_type_lower}_standard.png"
        if os.path.exists(laz_png):
            found_png_files.append({
                'path': laz_png,
                'desc': 'LAZ processing structure'
            })
        
        # Check Pattern 3: Look for region-based files in png_outputs
        if os.path.exists(output_dir3):
            import glob
            search_pattern = f"{output_dir3}/*_elevation_{processing_type_lower}.png"
            matching_files = glob.glob(search_pattern)
            
            if matching_files:
                for png_file in matching_files:
                    found_png_files.append({
                        'path': png_file,
                        'desc': 'Region PNG outputs structure'
                    })

        # Check Pattern 4: Old scattered structure
        old_scattered_dir = f"output/{base_filename}/lidar/{processing_type}"
        if os.path.exists(old_scattered_dir):
            old_patterns = [
                f"{old_scattered_dir}/{base_filename}_{processing_type}.png",
                f"{old_scattered_dir}/{base_filename}_{processing_type}_standard.png",
                f"{old_scattered_dir}/{base_filename}_{filename_suffix}.png",
                f"{old_scattered_dir}/{base_filename}_{filename_suffix}_standard.png"
            ]
            
            for pattern in old_patterns:
                if os.path.exists(pattern):
                    found_png_files.append({
                        'path': pattern,
                        'desc': f'Old scattered structure ({processing_type} folder)'
                    })
        
        # Format the result to return just the paths
        return [item['path'] for item in found_png_files]
        
    except Exception as e:
        print(f"❌ Error finding PNG files for {base_filename}/{processing_type}: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_image_overlay_data(base_filename: str, processing_type: str, filename_processing_type: str = None) -> Optional[Dict]:
    """
    DEPRECATED: Use get_laz_overlay_data or get_sentinel2_overlay_data instead.
    Get overlay data for a processed image including bounds and base64 encoded image.
    
    Args:
        base_filename: The base name of the LAZ file (e.g., 'OR_WizardIsland') or region (e.g., 'region_13_96S_48_33W')
        processing_type: The folder name (e.g., 'Hillshade', 'sentinel-2')
        filename_processing_type: The specific processing type for filename mapping (e.g., 'hillshade_315_45_08', 'RED_B04')
    """
    if processing_type == "sentinel-2":
        # Route to Sentinel-2 specific function
        return get_sentinel2_overlay_data_util(base_filename, filename_processing_type)
    else:
        # Route to LAZ processing function
        return get_laz_overlay_data(base_filename, processing_type, filename_processing_type)
