"""
Geospatial utilities for reading coordinate information from world files and GeoTIFF files.
"""
import os
import base64
import re
from typing import Dict, Tuple, Optional
from osgeo import gdal, osr
from app.data_acquisition.utils.coordinates import BoundingBox

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
                
                # Check if coordinates seem swapped by examining coordinate ranges
                avg_lon = (sw_lon + ne_lon + nw_lon + se_lon) / 4
                avg_lat = (sw_lat + ne_lat + nw_lat + se_lat) / 4
                
                print(f"🔍 Average transformed coordinates: lon={avg_lon}, lat={avg_lat}")
                
                # Check if the coordinate values are in the wrong positions
                coords_swapped = False
                
                # Method 1: Check if longitude values are in typical latitude range while latitude values are extreme
                if (abs(avg_lon) <= 90 and abs(avg_lat) > 90):
                    print("🔄 Coordinates appear to be swapped (longitude in lat position), correcting...")
                    coords_swapped = True
                    
                # Method 2: Oregon-specific detection - check if lon/lat are in wrong positions
                # For Oregon: latitude should be ~42-46°N, longitude should be ~116-125°W
                elif (40 <= avg_lon <= 50 and -130 <= avg_lat <= -115):
                    print(f"🔄 Oregon coordinate swap detected: lon={avg_lon} (latitude range), lat={avg_lat} (longitude range)")
                    print("🔄 Swapping because longitude is in latitude range and latitude is in longitude range")
                    coords_swapped = True
                    
                # Method 3: General geographic inconsistency detection
                elif (abs(avg_lon) <= 90 and abs(avg_lat) <= 180):
                    # Check if lat/lon magnitudes suggest they're swapped
                    if abs(avg_lat) > abs(avg_lon) * 2:  # If lat magnitude is much larger than lon magnitude
                        print(f"🔄 Geographic inconsistency detected: lat={avg_lat}, lon={avg_lon}")
                        print("🔄 Latitude magnitude much larger than longitude - likely swapped")
                        coords_swapped = True
                        
                # Method 4: Check for extreme longitude values
                elif (abs(avg_lat) > 180 or abs(avg_lon) > 180):
                    print("🔄 Extreme coordinate values detected, checking for swap...")
                    if abs(avg_lon) <= 90 and abs(avg_lat) > 90:
                        coords_swapped = True
                
                if coords_swapped:
                    print("🔄 Swapping lat/lon coordinates...")
                    sw_lon, sw_lat = sw_lat, sw_lon
                    ne_lon, ne_lat = ne_lat, ne_lon
                    nw_lon, nw_lat = nw_lat, nw_lon
                    se_lon, se_lat = se_lat, se_lon
                    print(f"   SW corrected: ({sw_lon}, {sw_lat})")
                    print(f"   NE corrected: ({ne_lon}, {ne_lat})")
                    print(f"   NW corrected: ({nw_lon}, {nw_lat})")
                    print(f"   SE corrected: ({se_lon}, {se_lat})")
                
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
            'LRM': 'LRM',
            'TRI': 'TRI',
            'TPI': 'TPI',
            'Roughness': 'Roughness',
            'Sky_View_Factor': 'SkyViewFactor',
            'Tint_Overlay': 'TintOverlay'
        }
        
        # Map processing type to new consolidated PNG names (PRIORITY)
        consolidated_png_mapping = {
            'LRM': 'LRM.png',
            'Sky_View_Factor': 'SVF.png', 
            'Slope': 'Slope.png',
            'CHM': 'CHM.png',  # Add CHM support for consolidated PNG directory
            'chm': 'CHM.png',  # Add lowercase chm support (used by gallery)
            'Hillshade': 'HillshadeRGB.png',
            'HillshadeRGB': 'HillshadeRGB.png',  # Support direct mapping
            'Tint_Overlay': 'TintOverlay.png',
            'TintOverlay': 'TintOverlay.png',    # Support direct mapping
            'NDVI': None  # Special handling for NDVI - will use pattern matching
        }
        
        # Map processing types to their actual directory names and TIFF files
        directory_mapping = {
            'HillshadeRGB': ('HillshadeRgb', 'hillshade_rgb.tif'),
            'TintOverlay': ('HillshadeRgb', 'tint_overlay.tiff'),  # TintOverlay files are in HillshadeRgb directory
            'Sky_View_Factor': ('Sky_View_Factor', None),  # Will auto-detect TIFF file
            'LRM': ('Lrm', None),
            'Slope': ('Slope', None),
            'CHM': ('CHM', None),  # CHM files are in CHM directory, will auto-detect TIFF file
            'chm': ('CHM', None)   # Support lowercase chm (used by gallery)
        }
        
        filename_suffix = filename_mapping.get(mapping_key, mapping_key.title())
        
        # Add possible file paths in order of preference
        # Pattern 0: PRIORITY - PNG outputs consolidated directory (NEW STANDARD)
        png_outputs_dir = f"output/{base_filename}/lidar/png_outputs"
        if os.path.exists(png_outputs_dir):
            # First check for new consolidated PNG names (LRM.png, SVF.png, etc.)
            if processing_type in consolidated_png_mapping:
                consolidated_png_name = consolidated_png_mapping[processing_type]
                if consolidated_png_name is not None:  # Regular consolidated PNG
                    consolidated_png_path = f"{png_outputs_dir}/{consolidated_png_name}"
                    if os.path.exists(consolidated_png_path):
                        base_name = os.path.splitext(consolidated_png_name)[0]
                        possible_paths.append({
                            'png': consolidated_png_path,
                            'tiff': f"{png_outputs_dir}/{base_name}.tif",
                            'world': f"{png_outputs_dir}/{base_name}.wld",
                            'desc': f'Consolidated PNG ({consolidated_png_name}) - NEW STANDARD'
                        })
                        print(f"✅ Found consolidated PNG: {consolidated_png_path}")
                elif processing_type == 'NDVI':  # Special NDVI handling
                    import glob
                    # Look for Sentinel-2 NDVI files with timestamp pattern
                    ndvi_pattern = f"{png_outputs_dir}/{base_filename}_*_sentinel2_NDVI.png"
                    ndvi_files = glob.glob(ndvi_pattern)
                    if ndvi_files:
                        ndvi_png_path = ndvi_files[0]  # Use first match
                        base_name = os.path.splitext(os.path.basename(ndvi_png_path))[0]
                        possible_paths.append({
                            'png': ndvi_png_path,
                            'tiff': f"{png_outputs_dir}/{base_name}.tif",
                            'world': f"{png_outputs_dir}/{base_name}.wld",
                            'desc': f'Sentinel-2 NDVI PNG - NEW STANDARD'
                        })
                        print(f"✅ Found Sentinel-2 NDVI PNG: {ndvi_png_path}")
            
            # Then check for old elevation pattern
            png_outputs_pattern = f"{png_outputs_dir}/{base_filename}_elevation_{processing_type_lower}.png"
            if os.path.exists(png_outputs_pattern):
                base_name = os.path.splitext(os.path.basename(png_outputs_pattern))[0]
                possible_paths.append({
                    'png': png_outputs_pattern,
                    'tiff': f"{png_outputs_dir}/{base_name}.tif",
                    'world': f"{png_outputs_dir}/{base_name}.wld",
                    'desc': 'PNG outputs consolidated directory (OLD ELEVATION PATTERN)'
                })
            else:
                # Try alternative naming patterns in png_outputs
                import glob
                search_patterns = [
                    f"{png_outputs_dir}/{base_filename}_elevation_{processing_type_lower}*.png",
                    f"{png_outputs_dir}/*_elevation_{processing_type_lower}.png",
                    f"{png_outputs_dir}/{base_filename}_{filename_suffix}*.png"
                ]
                
                for pattern in search_patterns:
                    matching_files = glob.glob(pattern)
                    if matching_files:
                        png_file = matching_files[0]  # Use first match
                        base_name = os.path.splitext(os.path.basename(png_file))[0]
                        possible_paths.append({
                            'png': png_file,
                            'tiff': f"{png_outputs_dir}/{base_name}.tif",
                            'world': f"{png_outputs_dir}/{base_name}.wld",
                            'desc': 'PNG outputs consolidated directory (PATTERN MATCH)'
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
        
        # Try multiple directory structures for Sentinel-2 files
        search_dirs = [
            f"output/{folder_region_name}/sentinel2",  # Standard Sentinel-2 directory
            f"output/{folder_region_name}/lidar/png_outputs"  # PNG outputs directory (fallback)
        ]
        
        for output_dir in search_dirs:
            print(f"📂 Checking directory: {output_dir}")
            
            if not os.path.exists(output_dir):
                print(f"📂 Directory doesn't exist: {output_dir}")
                continue
            
            # Find actual files matching the pattern since they include timestamps
            import glob
            
            # Pattern variations for different file naming conventions
            if band_name == 'NDVI':
                # NDVI files can have multiple patterns:
                patterns = [
                    f"{output_dir}/{folder_region_name}_*_{band_name}.png",  # Standard: PRE_A05-01_20250528_NDVI.png
                    f"{output_dir}/{folder_region_name}_*_sentinel2_{band_name}.png",  # With sentinel2: PRE_A05-01_20250528_sentinel2_NDVI.png
                    f"{output_dir}/*_{band_name}.png"  # Fallback: any file ending with _NDVI.png
                ]
            else:
                # Regular bands have pattern: {folder_region_name}_*_sentinel2_{band_name}.png
                patterns = [
                    f"{output_dir}/{folder_region_name}_*_sentinel2_{band_name}.png",
                    f"{output_dir}/{folder_region_name}_*_{band_name}.png"
                ]
            
            png_files = []
            for pattern in patterns:
                print(f"🔍 PNG pattern: {pattern}")
                matches = glob.glob(pattern)
                if matches:
                    png_files.extend(matches)
                    print(f"📁 Found PNG files: {matches}")
                    break  # Use first successful pattern
            
            if png_files:
                # Sort files by modification time to get the most recent
                png_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)  
                png_path = png_files[0]  # Use the most recent file
                print(f"📄 Selected PNG: {png_path}")
                
                # For files in png_outputs, try TIFF in same directory first, then sentinel2 directory
                if 'png_outputs' in output_dir:
                    tiff_path = png_path.replace('.png', '.tif')
                    if not os.path.exists(tiff_path):
                        # Try sentinel2 directory for TIFF
                        sentinel2_dir = f"output/{folder_region_name}/sentinel2"
                        tiff_filename = os.path.basename(png_path).replace('.png', '.tif')
                        tiff_path = f"{sentinel2_dir}/{tiff_filename}"
                else:
                    tiff_path = png_path.replace('.png', '.tif')
                
                # World file path
                world_path = png_path.replace('.png', '.wld')
                
                print(f"🖼️  PNG path: {png_path}")
                print(f"🗺️  TIFF path: {tiff_path}")
                print(f"🌍 World file path: {world_path}")
                break  # Found files, exit directory search loop
                
        else:
            # No files found in any directory
            print(f"❌ No PNG files found for {band_name} in any search directory")
            # Debug: List what files actually exist
            for output_dir in search_dirs:
                if os.path.exists(output_dir):
                    files = os.listdir(output_dir)
                    print(f"🔍 Files in {output_dir}: {files}")
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
                        print(f"💡 Available Sentinel-2 bands in {output_dir}: {list(available_bands)}")
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
        # Map processing types to their actual directory names and TIFF files
        directory_mapping = {
            'HillshadeRGB': ('HillshadeRgb', 'hillshade_rgb.tif'),
            'TintOverlay': ('HillshadeRgb', 'tint_overlay.tif'),  # TintOverlay files are in HillshadeRgb directory
            'Sky_View_Factor': ('Sky_View_Factor', None),  # Will auto-detect TIFF file
            'LRM': ('Lrm', None),
            'Slope': ('Slope', None)
        }
        
        # Check if files exist
        print(f"📁 PNG exists: {os.path.exists(png_path)}")
        print(f"🗺️  TIFF exists: {os.path.exists(tiff_path)}")
        print(f"🌍 World file exists: {os.path.exists(world_path)}")
        
        if not os.path.exists(png_path):
            print(f"❌ PNG file not found: {png_path}")
            return None
        
        # If the expected TIFF file doesn't exist, try to find the original TIFF in the processing type directory
        original_tiff_path = tiff_path
        if not os.path.exists(tiff_path):
            print(f"🔍 PNG-adjacent TIFF not found, looking for original TIFF...")
            
            # Check if we have a directory mapping for this processing type
            if processing_type in directory_mapping:
                actual_dir, specific_tiff = directory_mapping[processing_type]
                tiff_dir = f"output/{base_filename}/lidar/{actual_dir}"
                print(f"📂 Using directory mapping: {processing_type} -> {actual_dir}")
                
                if os.path.exists(tiff_dir):
                    if specific_tiff:
                        # Look for a specific TIFF file
                        specific_tiff_path = f"{tiff_dir}/{specific_tiff}"
                        if os.path.exists(specific_tiff_path):
                            original_tiff_path = specific_tiff_path
                            print(f"✅ Found specific TIFF: {original_tiff_path}")
                        else:
                            print(f"❌ Specific TIFF not found: {specific_tiff_path}")
                    else:
                        # Auto-detect TIFF files in the directory
                        import glob
                        tiff_files = glob.glob(f"{tiff_dir}/*.tif")
                        if tiff_files:
                            original_tiff_path = tiff_files[0]  # Use the first TIFF found
                            print(f"✅ Found original TIFF: {original_tiff_path}")
                        else:
                            print(f"❌ No TIFF files found in {tiff_dir}")
                else:
                    print(f"❌ Mapped directory not found: {tiff_dir}")
            else:
                # Fallback to original logic for unmapped processing types
                tiff_dir = f"output/{base_filename}/lidar/{processing_type}"
                if os.path.exists(tiff_dir):
                    import glob
                    tiff_files = glob.glob(f"{tiff_dir}/*.tif")
                    if tiff_files:
                        original_tiff_path = tiff_files[0]  # Use the first TIFF found
                        print(f"✅ Found original TIFF: {original_tiff_path}")
                    else:
                        print(f"❌ No TIFF files found in {tiff_dir}")
                else:
                    print(f"❌ Processing type directory not found: {tiff_dir}")
        else:
            print(f"✅ Using expected TIFF path: {tiff_path}")
        
        # PRIORITY: Try to get bounds from metadata.txt file first (most reliable)
        bounds = _get_bounds_from_metadata(base_filename)
        if bounds:
            print(f"✅ Using bounds from metadata.txt: {bounds}")
        else:
            # Fallback: Try to get center from metadata and calculate bounds
            metadata_center = _get_center_from_metadata(base_filename)
            if metadata_center:
                print(f"✅ Center coordinates from metadata.txt: {metadata_center}")
                
                # Try to get actual image bounds from world file using the correct center
                if os.path.exists(world_path):
                    print("🗺️  Calculating actual image bounds from world file...")
                    # Get image dimensions from PNG
                    from PIL import Image
                    with Image.open(png_path) as img:
                        width, height = img.size
                    print(f"📏 Image dimensions: {width}x{height}")
                    
                    # Calculate bounds using world file transformation but validate with metadata center
                    bounds = get_image_bounds_from_world_file_with_center_validation(world_path, width, height, metadata_center)
                    if bounds:
                        print(f"✅ Bounds from world file with metadata validation: {bounds}")
                    else:
                        print("❌ Failed to extract bounds from world file with validation")
                
                # Fallback: use metadata center with reasonable buffer if world file fails
                if not bounds:
                    print("📄 Using metadata center with image-based buffer...")
                    # Calculate buffer based on image dimensions (assume 1 meter per pixel as default)
                    if os.path.exists(world_path):
                        world_data = read_world_file(world_path)
                        if world_data:
                            # Use actual pixel size from world file
                            pixel_size_x = abs(world_data['pixel_size_x'])
                            pixel_size_y = abs(world_data['pixel_size_y'])
                            
                            # Get image dimensions
                            from PIL import Image
                        with Image.open(png_path) as img:
                            width, height = img.size
                        
                        # Convert pixel dimensions to degrees (rough approximation)
                        # 1 degree ≈ 111,000 meters at equator
                        width_degrees = (width * pixel_size_x) / 111000.0
                        height_degrees = (height * pixel_size_y) / 111000.0
                        
                        bounds = {
                            'north': metadata_center['lat'] + height_degrees / 2,
                            'south': metadata_center['lat'] - height_degrees / 2,
                            'east': metadata_center['lng'] + width_degrees / 2,
                            'west': metadata_center['lng'] - width_degrees / 2,
                            'center_lat': metadata_center['lat'],
                            'center_lng': metadata_center['lng'],
                            'source': 'metadata.txt + world_file_dimensions'
                        }
                        print(f"✅ Calculated bounds from metadata center + world file dimensions: {bounds}")
                    else:
                        # Fallback with small fixed buffer
                        buffer = 0.01  # ~1km buffer at equator
                        bounds = {
                            'north': metadata_center['lat'] + buffer,
                            'south': metadata_center['lat'] - buffer,
                            'east': metadata_center['lng'] + buffer,
                            'west': metadata_center['lng'] - buffer,
                            'center_lat': metadata_center['lat'],
                            'center_lng': metadata_center['lng'],
                            'source': 'metadata.txt + fixed_buffer'
                        }
                        print(f"✅ Using metadata center with fixed buffer: {bounds}")
                        
        # Only try to get bounds from original TIFF if metadata was not found at all
        if not bounds and not metadata_center:
            print("📄 No metadata.txt found, trying other methods...")
            
            # Fallback: Try to get bounds from GeoTIFF, then world file
            epsg_code = None
            
            # Try the original TIFF path first (may be different from expected path)
            if os.path.exists(original_tiff_path):
                print(f"🗺️  Trying to extract bounds from GeoTIFF: {original_tiff_path}")
                bounds = get_image_bounds_from_geotiff(original_tiff_path)
                if bounds:
                    epsg_code = bounds.get('epsg')
                    print(f"✅ Bounds from GeoTIFF: {bounds}")
                else:
                    print("❌ Failed to extract bounds from GeoTIFF")
            elif os.path.exists(tiff_path):
                print(f"🗺️  Trying to extract bounds from expected GeoTIFF: {tiff_path}")
                bounds = get_image_bounds_from_geotiff(tiff_path)
                if bounds:
                    epsg_code = bounds.get('epsg')
                    print(f"✅ Bounds from GeoTIFF: {bounds}")
                else:
                    print("❌ Failed to extract bounds from GeoTIFF")
                
            if not bounds and os.path.exists(world_path):
                print("🌍 Trying to extract bounds from world file...")
                
                # 🎯 PRIORITY: Check for WGS84 world file first (created by coordinate transformation)
                wgs84_world_path = os.path.splitext(world_path)[0] + "_wgs84.wld"
                if os.path.exists(wgs84_world_path):
                    print(f"✅ Found WGS84 world file: {wgs84_world_path}")
                    
                    # Get image dimensions from PNG
                    from PIL import Image
                    with Image.open(png_path) as img:
                        width, height = img.size
                    print(f"📏 Image dimensions: {width}x{height}")
                    
                    # Use WGS84 world file directly (no coordinate transformation needed)
                    bounds = get_image_bounds_from_world_file(wgs84_world_path, width, height, src_epsg=4326)
                    if bounds:
                        print(f"✅ Bounds from WGS84 world file: {bounds}")
                    else:
                        print("❌ Failed to extract bounds from WGS84 world file")
                        
                # Fallback to original world file if WGS84 world file doesn't exist or failed
                if not bounds:
                    print(f"🔄 Using original world file: {world_path}")
                    
                    # Get image dimensions from PNG
                    from PIL import Image
                    with Image.open(png_path) as img:
                        width, height = img.size
                    print(f"📏 Image dimensions: {width}x{height}")
                    
                    bounds = get_image_bounds_from_world_file(world_path, width, height, epsg_code)
                    if bounds:
                        print(f"✅ Bounds from original world file: {bounds}")
                    else:
                        print("❌ Failed to extract bounds from original world file")
        elif bounds:
            print(f"✅ Skipping TIFF/world file reading - already have bounds from metadata")
        else:
            print(f"✅ Skipping TIFF/world file reading - have metadata center, using calculated bounds")
            
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

def _get_bounds_from_metadata(base_filename: str) -> Optional[Dict]:
    """
    Extract bounds from metadata.txt file. This is the most reliable source of coordinates.
    
    Args:
        base_filename: The base name of the region (e.g., 'ANDL2940C9715_2014') or full path to metadata.txt
    
    Returns:
        Dictionary with bounds information or None if not found
    """
    try:
        # Handle both full path and base filename
        if base_filename.endswith('metadata.txt'):
            metadata_path = base_filename
        elif base_filename.startswith('output/'):
            # Already includes output/ prefix
            metadata_path = f"{base_filename}/metadata.txt"
        else:
            # Base filename only
            metadata_path = f"output/{base_filename}/metadata.txt"
        
        if not os.path.exists(metadata_path):
            print(f"📄 Metadata file not found: {metadata_path}")
            return None
        
        print(f"📄 Reading metadata from: {metadata_path}")
        
        center_lat = None
        center_lng = None
        north_bound = None
        south_bound = None
        east_bound = None
        west_bound = None
        
        with open(metadata_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('Center Latitude:'):
                    center_lat = float(line.split(':')[1].strip())
                elif line.startswith('Center Longitude:'):
                    center_lng = float(line.split(':')[1].strip())
                elif line.startswith('North Bound:'):
                    north_bound = float(line.split(':')[1].strip())
                elif line.startswith('South Bound:'):
                    south_bound = float(line.split(':')[1].strip())
                elif line.startswith('East Bound:'):
                    east_bound = float(line.split(':')[1].strip())
                elif line.startswith('West Bound:'):
                    west_bound = float(line.split(':')[1].strip())
        
        # Prefer actual bounds if available, fallback to center + buffer
        if all(bound is not None for bound in [north_bound, south_bound, east_bound, west_bound]):
            bounds = {
                'north': north_bound,
                'south': south_bound,
                'east': east_bound,
                'west': west_bound,
                'center_lat': center_lat or (north_bound + south_bound) / 2,
                'center_lng': center_lng or (east_bound + west_bound) / 2,
                'source': 'metadata.txt_bounds'
            }
            
            print(f"✅ Extracted actual bounds from metadata.txt:")
            print(f"   Center: ({bounds['center_lat']:.6f}, {bounds['center_lng']:.6f})")
            print(f"   Bounds: N={bounds['north']:.6f}, S={bounds['south']:.6f}, E={bounds['east']:.6f}, W={bounds['west']:.6f}")
            
            return bounds
            
        elif center_lat is not None and center_lng is not None:
            # Fallback: Create bounds with a small buffer around the center point
            buffer = 0.01  # ~1km buffer at equator
            
            bounds = {
                'north': center_lat + buffer,
                'south': center_lat - buffer,
                'east': center_lng + buffer,
                'west': center_lng - buffer,
                'center_lat': center_lat,
                'center_lng': center_lng,
                'source': 'metadata.txt_center_buffered'
            }
            
            print(f"✅ Extracted center coordinates from metadata.txt (using buffer):")
            print(f"   Center: ({center_lat:.6f}, {center_lng:.6f})")
            print(f"   Bounds: N={bounds['north']:.6f}, S={bounds['south']:.6f}, E={bounds['east']:.6f}, W={bounds['west']:.6f}")
            
            return bounds
        else:
            print(f"❌ Could not find coordinates or bounds in metadata.txt")
            return None
            
    except Exception as e:
        print(f"❌ Error reading metadata.txt for {base_filename}: {e}")
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
            'LRM': 'LRM',
            'TRI': 'TRI',
            'TPI': 'TPI',
            'Roughness': 'Roughness',
            'Sky_View_Factor': 'SkyViewFactor'
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

def correct_coordinate_order(source_srs, epsg_code, sw_lon, sw_lat, ne_lon, ne_lat, nw_lon, nw_lat, se_lon, se_lat):
    """
    Correct coordinate order based on EPSG code and axis order conventions.
    Some coordinate systems have different axis orders (lat/lon vs lon/lat).
    """
    try:
        # Check if coordinates need to be swapped based on axis order
        axis_order = source_srs.GetAxisName(None, 0) if source_srs else None
        
        # For some EPSG codes, the axis order is lat/lon instead of lon/lat
        # This is common in many projected coordinate systems
        swap_needed = False
        
        # Check average coordinates to detect swapping
        avg_lon = (sw_lon + ne_lon + nw_lon + se_lon) / 4
        avg_lat = (sw_lat + ne_lat + nw_lat + se_lat) / 4
        
        if epsg_code:
            # EPSG codes that commonly use lat/lon order
            lat_lon_first_epsg = {4326}  # WGS84 geographic can vary by implementation
            
            # Check axis order from the SRS
            if source_srs and hasattr(source_srs, 'GetAxisName'):
                try:
                    first_axis = source_srs.GetAxisName(None, 0)
                    if first_axis and 'lat' in first_axis.lower():
                        swap_needed = True
                except:
                    pass
        
        # Oregon-specific detection (EPSG:2992 - Oregon State Plane)
        # For Oregon: latitude should be ~42-46°N, longitude should be ~116-125°W
        if (40 <= avg_lon <= 50 and -130 <= avg_lat <= -115):
            print(f"📐 Oregon coordinate swap detected in correction function: lon={avg_lon}, lat={avg_lat}")
            swap_needed = True
        
        # General coordinate swap detection
        elif (abs(avg_lon) <= 90 and abs(avg_lat) > 90):
            print(f"📐 General coordinate swap detected: lon={avg_lon}, lat={avg_lat}")
            swap_needed = True
        
        if swap_needed:
            print(f"📐 Swapping coordinate order for EPSG:{epsg_code}")
            return sw_lat, sw_lon, ne_lat, ne_lon, nw_lat, nw_lon, se_lat, se_lon
        else:
            return sw_lon, sw_lat, ne_lon, ne_lat, nw_lon, nw_lat, se_lon, se_lat
            
    except Exception as e:
        print(f"⚠️ Error in coordinate order correction: {e}")
        # Return original coordinates if correction fails
        return sw_lon, sw_lat, ne_lon, ne_lat, nw_lon, nw_lat, se_lon, se_lat

def _get_center_from_metadata(base_filename: str) -> Optional[Dict]:
    """
    Extract center coordinates from metadata.txt file.
    
    Args:
        base_filename: The base name of the region (e.g., 'ANDL2940C9715_2014')
    
    Returns:
        Dictionary with center coordinates or None if not found
    """
    try:
        # Look for metadata.txt file in the output directory
        metadata_path = f"output/{base_filename}/metadata.txt"
        
        if not os.path.exists(metadata_path):
            print(f"📄 Metadata file not found: {metadata_path}")
            return None
        
        print(f"📄 Reading center from metadata: {metadata_path}")
        
        center_lat = None
        center_lng = None
        
        with open(metadata_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('Center Latitude:'):
                    center_lat = float(line.split(':')[1].strip())
                elif line.startswith('Center Longitude:'):
                    center_lng = float(line.split(':')[1].strip())
        
        if center_lat is not None and center_lng is not None:
            return {'lat': center_lat, 'lng': center_lng}
        else:
            print(f"❌ Could not find both latitude and longitude in metadata.txt")
            return None
            
    except Exception as e:
        print(f"❌ Error reading metadata.txt for {base_filename}: {e}")
        return None

def get_image_bounds_from_world_file_with_center_validation(world_file_path: str, image_width: int, image_height: int, expected_center: Dict) -> Optional[Dict]:
    """
    Calculate geographic bounds using world file but validate the center matches expected coordinates.
    If the transformed coordinates are way off, we'll use the expected center with calculated dimensions.
    """
    try:
        world_data = read_world_file(world_file_path)
        if not world_data:
            return None
            
        # Calculate bounds using world file
        upper_left_x = world_data['upper_left_x']
        upper_left_y = world_data['upper_left_y']
        pixel_size_x = world_data['pixel_size_x']
        pixel_size_y = world_data['pixel_size_y']  # Usually negative
        
        # Calculate corner coordinates in source projection
        west = upper_left_x
        east = upper_left_x + (image_width * pixel_size_x)
        north = upper_left_y
        south = upper_left_y + (image_height * pixel_size_y)  # pixel_size_y is negative
        
        print(f"🗺️  World file bounds in source projection:")
        print(f"   West: {west}, East: {east}")
        print(f"   North: {north}, South: {south}")
        
        # Check if these coordinates look like they need transformation
        if (abs(west) > 180 or abs(east) > 180 or abs(north) > 90 or abs(south) > 90):
            print(f"🌍 Coordinates appear to be in projected system, but using metadata center instead")
            # Don't try to transform - use the expected center with calculated dimensions
            
            # Calculate image dimensions in degrees based on pixel sizes
            # Approximate conversion: assume pixel sizes are in meters, convert to degrees
            pixel_size_x_abs = abs(pixel_size_x)
            pixel_size_y_abs = abs(pixel_size_y)
            
            # Convert to degrees (rough approximation: 1 degree ≈ 111,000 meters)
            width_degrees = (image_width * pixel_size_x_abs) / 111000.0
            height_degrees = (image_height * pixel_size_y_abs) / 111000.0
            
            # Use expected center with calculated dimensions
            bounds = {
                'north': expected_center['lat'] + height_degrees / 2,
                'south': expected_center['lat'] - height_degrees / 2,
                'east': expected_center['lng'] + width_degrees / 2,
                'west': expected_center['lng'] - width_degrees / 2,
                'center_lat': expected_center['lat'],
                'center_lng': expected_center['lng'],
                'source': 'metadata_center + world_file_dimensions'
            }
            
            print(f"🎯 Using expected center with world file dimensions:")
            print(f"   Image size: {width_degrees:.6f}° x {height_degrees:.6f}°")
            print(f"   Bounds: N={bounds['north']:.6f}, S={bounds['south']:.6f}, E={bounds['east']:.6f}, W={bounds['west']:.6f}")
            
            return bounds
        else:
            # Coordinates look like they're already in WGS84, use them directly
            center_calculated = {
                'lat': (north + south) / 2,
                'lng': (east + west) / 2
            }
            
            # Validate the calculated center is reasonably close to expected center
            lat_diff = abs(center_calculated['lat'] - expected_center['lat'])
            lng_diff = abs(center_calculated['lng'] - expected_center['lng'])
            
            if lat_diff < 0.1 and lng_diff < 0.1:  # Within ~10km
                print(f"✅ World file center matches expected center")
                return {
                    'north': north,
                    'south': south,
                    'east': east,
                    'west': west,
                    'center_lat': center_calculated['lat'],
                    'center_lng': center_calculated['lng'],
                    'source': 'world_file_validated'
                }
            else:
                print(f"⚠️ World file center ({center_calculated['lat']:.6f}, {center_calculated['lng']:.6f}) differs from expected ({expected_center['lat']:.6f}, {expected_center['lng']:.6f})")
                print(f"   Using expected center with world file dimensions")
                
                # Use expected center but with world file dimensions
                width_degrees = abs(east - west)
                height_degrees = abs(north - south)
                
                return {
                    'north': expected_center['lat'] + height_degrees / 2,
                    'south': expected_center['lat'] - height_degrees / 2,
                    'east': expected_center['lng'] + width_degrees / 2,
                    'west': expected_center['lng'] - width_degrees / 2,
                    'center_lat': expected_center['lat'],
                    'center_lng': expected_center['lng'],
                    'source': 'metadata_center + world_file_dimensions'
                }
            
    except Exception as e:
        print(f"❌ Error in world file validation: {e}")
        return None


def intersect_bounding_boxes(b1: 'BoundingBox', b2: 'BoundingBox') -> Optional['BoundingBox']:
    """Return the intersection of two bounding boxes or None if they don't overlap."""
    west = max(b1.west, b2.west)
    east = min(b1.east, b2.east)
    south = max(b1.south, b2.south)
    north = min(b1.north, b2.north)

    if east <= west or north <= south:
        return None

    return BoundingBox(north=north, south=south, east=east, west=west)


def crop_geotiff_to_bbox(input_path: str, output_path: str, bbox: 'BoundingBox') -> bool:
    """Crop a GeoTIFF file to the specified bounding box using GDAL."""
    try:
        translate_options = gdal.TranslateOptions(
            projWin=[bbox.west, bbox.north, bbox.east, bbox.south],
            projWinSRS='EPSG:4326',
            format='GTiff',
            creationOptions=['COMPRESS=LZW', 'TILED=YES']
        )

        result = gdal.Translate(output_path, input_path, options=translate_options)
        if result is None:
            print(f"❌ GDAL cropping failed for {input_path}")
            return False

        print(f"✅ Cropped {input_path} to {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error cropping GeoTIFF {input_path}: {e}")
        return False