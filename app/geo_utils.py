"""
Geospatial utilities for reading coordinate information from world files and GeoTIFF files.
"""
import os
import base64
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

def get_image_overlay_data(base_filename: str, processing_type: str, filename_processing_type: str = None) -> Optional[Dict]:
    """
    Get overlay data for a processed image including bounds and base64 encoded image.
    
    Args:
        base_filename: The base name of the LAZ file (e.g., 'OR_WizardIsland')
        processing_type: The folder name (e.g., 'Hillshade')
        filename_processing_type: The specific processing type for filename mapping (e.g., 'hillshade_315_45_08')
    """
    try:
        print(f"\n🔍 Getting overlay data for {base_filename}/{processing_type}")
        if filename_processing_type:
            print(f"🔍 Using filename processing type: {filename_processing_type}")
        
        # Construct paths - processing_type should already be the correct folder name
        output_dir = f"output/{base_filename}/{processing_type}"
        
        # Use filename_processing_type for mapping if provided, otherwise use processing_type
        mapping_key = filename_processing_type if filename_processing_type else processing_type
        
        # Map processing type to filename suffix - based on actual file naming convention
        filename_mapping = {
            'DEM': 'DEM',           # FoxIsland_DEM.png
            'DTM': 'DTM',           # FoxIsland_DTM.png
            'DSM': 'DSM',           # FoxIsland_DSM.png
            'CHM': 'CHM',           # FoxIsland_CHM.png
            'Hillshade': 'hillshade_standard',   # FoxIsland_hillshade_standard.png
            'hillshade_315_45_08': 'hillshade_315_45_08',   # FoxIsland_hillshade_315_45_08.png
            'hillshade_225_45_08': 'hillshade_225_45_08',   # FoxIsland_hillshade_225_45_08.png
            'Slope': 'slope',           # FoxIsland_slope.png
            'Aspect': 'aspect',         # FoxIsland_aspect.png
            'ColorRelief': 'color_relief', # FoxIsland_color_relief.png
            'TRI': 'tri',               # FoxIsland_tri.png
            'TPI': 'tpi',               # FoxIsland_tpi.png
            'Roughness': 'roughness'    # FoxIsland_roughness.png
        }
        
        filename_suffix = filename_mapping.get(mapping_key, mapping_key.lower())
        
        png_path = f"{output_dir}/{base_filename}_{filename_suffix}.png"
        tiff_path = f"{output_dir}/{base_filename}_{filename_suffix}.tif"
        world_path = f"{output_dir}/{base_filename}_{filename_suffix}.wld"
        
        print(f"📂 Output directory: {output_dir}")
        print(f"🖼️  PNG path: {png_path}")
        print(f"🗺️  TIFF path: {tiff_path}")
        print(f"🌍 World file path: {world_path}")
        
        # Check if files exist
        print(f"📁 Directory exists: {os.path.exists(output_dir)}")
        print(f"🖼️  PNG exists: {os.path.exists(png_path)}")
        print(f"🗺️  TIFF exists: {os.path.exists(tiff_path)}")
        print(f"🌍 World file exists: {os.path.exists(world_path)}")
        
        if not os.path.exists(png_path):
            # Debug: List what files actually exist
            if os.path.exists(output_dir):
                files = os.listdir(output_dir)
                print(f"🔍 Files in directory: {files}")
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
        return {
            'bounds': bounds,
            'image_data': image_data,
            'processing_type': processing_type,
            'filename': base_filename
        }
        
    except Exception as e:
        print(f"❌ Error getting overlay data for {base_filename}/{processing_type}: {e}")
        import traceback
        traceback.print_exc()
        return None
