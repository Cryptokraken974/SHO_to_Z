# Sentinel-2 specific overlay endpoint (must come before general overlay endpoint)
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import base64
import io
import glob
from PIL import Image, ImageDraw

router = APIRouter()

@router.get("/api/overlay/sentinel2/{region_band}")
async def get_sentinel2_overlay_data(region_band: str):
    """Get overlay data for a Sentinel-2 image including bounds and base64 encoded image"""
    print(f"\n🛰️ API CALL: /api/overlay/sentinel2/{region_band}")
    
    try:
        # Parse region_band format: "region_xxx_BAND_BXX" or "region_xxx_NDVI"
        # Examples: "region_10_12S_42_23W_RED_B04", "region_3_13S_58_29W_NIR_B08", "3.10S_57.70W_NDVI"
        # Strategy: Handle NDVI as special case (single part), otherwise split on last 2 parts for band
        parts = region_band.split('_')
        if len(parts) < 2:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid region_band format. Expected: region_xxx_BAND_BXX or region_xxx_NDVI"}
            )
        
        # Check if last part is NDVI (special case)
        if parts[-1] == 'NDVI':
            band_info = 'NDVI'
            region_name = '_'.join(parts[:-1])  # Everything except NDVI
        else:
            # Standard case: take last 2 parts as band_info (RED_B04, NIR_B08)
            if len(parts) < 3:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid region_band format. Expected: region_xxx_BAND_BXX or region_xxx_NDVI"}
                )
            band_info = '_'.join(parts[-2:])  # RED_B04 or NIR_B08
            region_name = '_'.join(parts[:-2])  # region_10_12S_42_23W
        
        print(f"🏷️ Region: {region_name}")
        print(f"📻 Band Info: {band_info}")
        
        # Use the new Sentinel-2 specific function
        from ..geo_utils import get_sentinel2_overlay_data_util
        
        # Call Sentinel-2 specific function with region_name and band_info
        overlay_data = get_sentinel2_overlay_data_util(region_name, band_info)
        
        if not overlay_data:
            print(f"❌ No overlay data found for Sentinel-2 {band_info} in region {region_name}")
            # Debug: Check what files exist and suggest alternatives
            from pathlib import Path
            s2_dir = Path("output") / region_name / "sentinel2"
            if s2_dir.exists():
                files = list(s2_dir.glob("*sentinel2*.png")) + list(s2_dir.glob("*NDVI*.png"))
                print(f"🔍 PNG files in Sentinel-2 directory: {[f.name for f in files]}")
                
                # Extract available bands for user guidance
                available_bands = set()
                for f in files:
                    if 'NDVI' in f.name:
                        available_bands.add('NDVI')
                    else:
                        parts = f.name.split('_')
                        if len(parts) >= 2:
                            band = '_'.join(parts[-2:]).replace('.png', '')
                            available_bands.add(band)
                
                error_msg = f"Sentinel2 {band_info} overlay data not found for region {region_name}"
                if available_bands:
                    error_msg += f". Available bands: {sorted(available_bands)}"
                    
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": error_msg,
                        "available_bands": sorted(available_bands),
                        "region": region_name,
                        "requested_band": band_info
                    }
                )
            else:
                print(f"🔍 Sentinel-2 directory doesn't exist: {s2_dir}")
            
            return JSONResponse(
                status_code=404,
                content={"error": f"Sentinel-2 {band_info} overlay data not found for region {region_name}"}
            )
        
        # Add Sentinel-2 specific metadata
        overlay_data.update({
            "band": band_info,
            "region": region_name,
            "source": "Sentinel-2"
        })
        
        print(f"✅ Sentinel-2 overlay data retrieved successfully")
        print(f"📍 Bounds: {overlay_data['bounds']}")
        
        return overlay_data
        
    except Exception as e:
        print(f"❌ Error in get_sentinel2_overlay_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.get("/api/overlay/{processing_type}/{filename}")
async def get_overlay_data(processing_type: str, filename: str):
    """Get overlay data for a processed image including bounds and base64 encoded image"""
    print(f"\n🗺️  API CALL: /api/overlay/{processing_type}/{filename}")
    
    try:
        from ..geo_utils import get_laz_overlay_data
        
        # Extract base filename (remove path and extension)
        base_filename = os.path.splitext(os.path.basename(filename))[0]
        if base_filename.endswith('.copc'):
            base_filename = base_filename[:-5]  # Remove .copc suffix
            
        print(f"📂 Base filename: {base_filename}")
        print(f"🔄 Processing type: {processing_type}")
        
        # Map API processing types to actual folder names
        type_mapping = {
            'laz_to_dem': 'DEM',
            'dtm': 'DTM',
            'dsm': 'DSM',
            'chm': 'CHM',
            'hillshade': 'Hillshade',
            'hillshade_315_45_08': 'Hillshade',
            'hillshade_225_45_08': 'Hillshade',
            'slope': 'Slope',
            'aspect': 'Aspect',
            'color_relief': 'ColorRelief',
            'lrm': 'LRM',
            'tpi': 'TPI',
            'roughness': 'Roughness'
        }
        
        # Get the actual folder name
        actual_processing_type = type_mapping.get(processing_type, processing_type.title())
        print(f"📁 Mapped processing type: {processing_type} -> {actual_processing_type}")
        
        # For hillshade variants, pass the original processing type for filename mapping
        filename_processing_type = processing_type if processing_type.startswith('hillshade_') else actual_processing_type
        
        overlay_data = get_laz_overlay_data(base_filename, actual_processing_type, filename_processing_type)
        
        if not overlay_data:
            print(f"❌ No overlay data found for {base_filename}/{actual_processing_type}")
            # Debug: List available directories
            output_base = f"output/{base_filename}"
            if os.path.exists(output_base):
                available_dirs = [d for d in os.listdir(output_base) if os.path.isdir(os.path.join(output_base, d))]
                print(f"🔍 Available directories: {available_dirs}")
            else:
                print(f"🔍 Output directory doesn't exist: {output_base}")
            
            return JSONResponse(
                status_code=404, 
                content={"error": "Overlay data not found or could not extract coordinates"}
            )
            
        print(f"✅ Overlay data retrieved successfully")
        print(f"📍 Bounds: {overlay_data['bounds']}")
        
        return overlay_data
        
    except Exception as e:
        print(f"❌ Error getting overlay data: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get overlay data: {str(e)}"}
        )

@router.get("/api/overlay/raster/{region_name}/{processing_type}")
async def get_raster_overlay_data(region_name: str, processing_type: str):
    """Get overlay data for raster-processed images from regions including bounds and base64 encoded image"""
    print(f"\n🗺️  API CALL: /api/overlay/raster/{region_name}/{processing_type}")
    
    try:
        from ..geo_utils import get_laz_overlay_data, get_sentinel2_overlay_data_util
        
        print(f"📂 Region name: {region_name}")
        print(f"🔄 Processing type: {processing_type}")
        print(f"🔍 Current working directory: {os.getcwd()}")
        
        # Check if this is a Sentinel-2 processing type
        if processing_type.startswith("sentinel2_"):
            print(f"🛰️ Handling Sentinel-2 processing type: {processing_type}")
            
            # Map processing type to band identifier
            sentinel2_mapping = {
                "sentinel2_ndvi": "NDVI",
                "sentinel2_red": "RED_B04", 
                "sentinel2_nir": "NIR_B08"
            }
            
            band_type = sentinel2_mapping.get(processing_type)
            if not band_type:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": f"Unknown Sentinel-2 processing type: {processing_type}"}
                )
            
            # Use Sentinel-2 specific overlay function
            print(f"🔄 Calling get_sentinel2_overlay_data_util({region_name}, {band_type})")
            overlay_data = get_sentinel2_overlay_data_util(region_name, band_type)
            
            if not overlay_data:
                print(f"❌ No Sentinel-2 overlay data found for {region_name}/{band_type}")
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "error": f"No Sentinel-2 {band_type} data found for region {region_name}"}
                )
            
            print(f"✅ Successfully prepared Sentinel-2 overlay data")
            result = {
                'success': True,
                'bounds': overlay_data['bounds'],
                'image_data': overlay_data['image_data'],
                'processing_type': processing_type,
                'region_name': region_name,
                'filename': overlay_data.get('filename', f"{region_name}_{band_type}"),
                'is_optimized': overlay_data.get('is_optimized', False)
            }
            
            # Add optimization metadata if available
            if overlay_data.get('optimization_info'):
                result['optimization_info'] = overlay_data['optimization_info']
            
            return result
        
        # Handle LIDAR/elevation processing types - NEW APPROACH
        # First, try direct PNG file lookup in png_outputs folder
        png_outputs_dir = f"output/{region_name}/lidar/png_outputs"
        if os.path.exists(png_outputs_dir):
            print(f"🔍 Looking for PNG files in: {png_outputs_dir}")
            
            # Map processing types to possible PNG filenames
            filename_mapping = {
                "tint_overlay": ["TintOverlay.png", "tint_overlay.png"],
                "hillshade_rgb": ["HillshadeRGB.png", "hillshade_rgb.png"],
                "lrm": ["LRM.png", "lrm.png"],
                "sky_view_factor": ["SVF.png", "Sky_View_Factor.png", "sky_view_factor.png"],
                "slope": ["Slope.png", "slope.png"],
                "aspect": ["Aspect.png", "aspect.png"],
                "chm": ["CHM.png", "Chm.png", "chm.png"],            "hillshade": ["Hillshade.png", "hillshade.png"],
            "roughness": ["Roughness.png", "roughness.png"],
            "color_relief": ["Color_Relief.png", "color_relief.png"],
            "tpi": ["TPI.png", "tpi.png"],
            "tri": ["TRI.png", "tri.png"],
            "ndvi": ["NDVI.png", "ndvi.png"]  # Add NDVI support
        }
            
            # Find the actual PNG file
            png_file_path = None
            possible_names = filename_mapping.get(processing_type, [f"{processing_type}.png", f"{processing_type.title()}.png"])
            
            for filename in possible_names:
                full_path = os.path.join(png_outputs_dir, filename)
                if os.path.exists(full_path):
                    png_file_path = full_path
                    print(f"✅ Found PNG file: {png_file_path}")
                    break
            
            if png_file_path:
                # Read bounds from metadata.txt
                metadata_path = f"output/{region_name}/metadata.txt"
                bounds = None
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            content = f.read()
                        
                        # Extract bounds from metadata
                        bounds_dict = {}
                        for line in content.split('\n'):
                            line = line.strip()
                            if line.startswith('North Bound:'):
                                bounds_dict['north'] = float(line.split(':')[1].strip())
                            elif line.startswith('South Bound:'):
                                bounds_dict['south'] = float(line.split(':')[1].strip())
                            elif line.startswith('East Bound:'):
                                bounds_dict['east'] = float(line.split(':')[1].strip())
                            elif line.startswith('West Bound:'):
                                bounds_dict['west'] = float(line.split(':')[1].strip())
                        
                        if all(k in bounds_dict for k in ['north', 'south', 'east', 'west']):
                            bounds = bounds_dict
                            print(f"✅ Found bounds in metadata: {bounds}")
                    except Exception as e:
                        print(f"⚠️ Error reading bounds from metadata: {e}")
                
                if bounds:
                    # Read and encode PNG image
                    try:
                        with open(png_file_path, 'rb') as f:
                            image_data = base64.b64encode(f.read()).decode('utf-8')
                        
                        result = {
                            'success': True,
                            'bounds': bounds,
                            'image_data': image_data,
                            'processing_type': processing_type,
                            'region_name': region_name,
                            'filename': os.path.basename(png_file_path),
                            'is_optimized': False
                        }
                        
                        print(f"✅ Successfully prepared PNG overlay data from png_outputs")
                        return result
                        
                    except Exception as e:
                        print(f"❌ Error reading PNG file: {e}")
                else:
                    print(f"❌ No bounds found in metadata for region {region_name}")
        
        # Fallback to original approach if PNG files not found in png_outputs
        # Map frontend processing types to backend processing types
        processing_type_mapping = {
            "lrm": "LRM",
            "sky_view_factor": "Sky_View_Factor", 
            "slope": "Slope",
            "hillshade_rgb": "HillshadeRGB",
            "hillshadergb": "HillshadeRGB",  # Support direct mapping
            "tint_overlay": "TintOverlay",
            "tintoverlay": "TintOverlay",    # Support direct mapping
            "aspect": "Aspect",
            "dtm": "DTM",
            "dsm": "DSM",
            "dem": "DEM",
            "chm": "CHM",
            "hillshade": "Hillshade",
            "color_relief": "Color_Relief",
            "tri": "TRI",
            "tpi": "TPI",
            "roughness": "Roughness",
            "ndvi": "NDVI"  # Add NDVI mapping
        }
        
        # Convert frontend processing type to backend processing type
        backend_processing_type = processing_type_mapping.get(processing_type.lower(), processing_type.title())
        print(f"🔄 Mapped processing type: {processing_type} -> {backend_processing_type}")
        
        # Check if the PNG file exists before calling the function
        expected_png_path = f"output/{region_name}/lidar/png_outputs/{backend_processing_type}.png"
        print(f"🔍 Checking expected PNG path: {expected_png_path}")
        print(f"📁 PNG exists: {os.path.exists(expected_png_path)}")
        
        # Use the updated geo_utils function that prioritizes metadata.txt
        print(f"🔄 Calling get_laz_overlay_data({region_name}, {backend_processing_type})")
        overlay_data = get_laz_overlay_data(region_name, backend_processing_type)
        print(f"🔍 Function returned: {overlay_data is not None}")
        
        if not overlay_data:
            print(f"❌ No overlay data found for {region_name}/{processing_type}")
            # Debug: List available directories
            output_base = f"output/{region_name}"
            if os.path.exists(output_base):
                available_dirs = [d for d in os.listdir(output_base) if os.path.isdir(os.path.join(output_base, d))]
                print(f"🔍 Available directories in {output_base}: {available_dirs}")
                png_dir = f"{output_base}/lidar/png_outputs"
                if os.path.exists(png_dir):
                    png_files = [f for f in os.listdir(png_dir) if f.endswith('.png')]
                    print(f"🔍 Available PNG files in {png_dir}: {png_files}")
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"No overlay data found for {processing_type} in region {region_name}"}
            )
        
        print(f"✅ Successfully prepared raster overlay data")
        result = {
            'success': True,
            'bounds': overlay_data['bounds'],
            'image_data': overlay_data['image_data'],
            'processing_type': processing_type,
            'region_name': region_name,
            'filename': overlay_data.get('filename', region_name),
            'is_optimized': overlay_data.get('is_optimized', False)
        }
        
        # Add optimization metadata if available
        if overlay_data.get('optimization_info'):
            result['optimization_info'] = overlay_data['optimization_info']
        
        return result
        
    except Exception as e:
        print(f"❌ Error getting raster overlay data: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to get raster overlay data: {str(e)}"}
        )

@router.get("/api/test-overlay/{filename}")
async def get_test_overlay(filename: str):
    """Create a simple black overlay at the LAZ file coordinates for testing"""
    print(f"\n🧪 TEST OVERLAY: /api/test-overlay/{filename}")
    
    try:
        from PIL import Image, ImageDraw
        import io
        
        # Map known LAZ files to their approximate coordinates in WGS84
        laz_coordinates = {
            'FoxIsland.laz': {
                'center_lat': 44.4268,
                'center_lng': -68.2048,
                'size_deg': 0.01  # ~1km at this latitude
            },
            'OR_WizardIsland.laz': {
                'center_lat': 42.9446,
                'center_lng': -122.1090,
                'size_deg': 0.01  # ~1km at this latitude
            }
        }
        
        # Extract base filename
        base_filename = os.path.splitext(os.path.basename(filename))[0]
        if base_filename.endswith('.copc'):
            base_filename = base_filename[:-5]
            
        print(f"📂 Base filename: {base_filename}")
        
        # Find matching LAZ file
        matching_coords = None
        for laz_file, coords in laz_coordinates.items():
            if base_filename in laz_file or laz_file.replace('.laz', '') in base_filename:
                matching_coords = coords
                break
                
        if not matching_coords:
            print(f"❌ No coordinates found for {base_filename}")
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "No test coordinates available for this file"}
            )
            
        print(f"📍 Using coordinates: {matching_coords}")
        
        # Calculate bounds
        half_size = matching_coords['size_deg'] / 2
        bounds = {
            'north': matching_coords['center_lat'] + half_size,
            'south': matching_coords['center_lat'] - half_size,
            'east': matching_coords['center_lng'] + half_size,
            'west': matching_coords['center_lng'] - half_size,
            'center_lat': matching_coords['center_lat'],
            'center_lng': matching_coords['center_lng']
        }
        
        print(f"🗺️  Test bounds: {bounds}")
        
        # Create a simple black square image
        img_size = 200
        img = Image.new('RGBA', (img_size, img_size), (0, 0, 0, 128))  # Semi-transparent black
        
        # Add a red border for visibility
        draw = ImageDraw.Draw(img)
        border_width = 5
        draw.rectangle([0, 0, img_size-1, img_size-1], outline=(255, 0, 0, 255), width=border_width)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        print(f"✅ Created test overlay image ({len(image_data)} chars)")
        
        return {
            'success': True,
            'bounds': bounds,
            'image_data': image_data,
            'processing_type': 'test',
            'filename': base_filename
        }
        
    except Exception as e:
        print(f"❌ Error creating test overlay: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to create test overlay: {str(e)}"}
        )
