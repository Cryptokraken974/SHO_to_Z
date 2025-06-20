from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict
import json
from ..convert import convert_geotiff_to_png_base64
from ..processing.dtm import dtm
from ..processing.dsm import dsm
from ..processing.chm import chm
from ..processing.hillshade import hillshade, hillshade_315_45_08, hillshade_225_45_08, generate_hillshade_with_params
from ..processing.slope import slope
from ..processing.aspect import aspect
from ..processing.color_relief import color_relief
from ..processing.tpi import tpi
from ..processing.roughness import roughness
from ..processing.sky_view_factor import sky_view_factor
from ..processing.composites import generate_dtm_hillshade_blend
import os
import re
from pathlib import Path
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def is_coordinate_based_region(region_name: str) -> bool:
    coordinate_pattern = r'^\d+\.\d+[NS]_\d+\.\d+[EW]$'
    return bool(re.match(coordinate_pattern, region_name))

def resolve_laz_file_from_region(region_name: str, processing_type: str) -> str:
    """
    Resolve the LAZ file path from a region name and processing type.
    
    Args:
        region_name: Region identifier (can be coordinate-based like "12.34N_56.78W" or named region)
        processing_type: Type of processing/acquisition (e.g., "lidar", "elevation", etc.)
    
    Returns:
        str: Path to the LAZ file
        
    Raises:
        FileNotFoundError: If no LAZ file is found for the region
        ValueError: If multiple LAZ files are found and selection is ambiguous
    """
    logger.info(f"Resolving LAZ file for region: {region_name}, processing_type: {processing_type}")
    
    # Define possible directory patterns where LAZ files might be stored
    search_paths = [
        f"input/{region_name}/lidar",
        f"input/{region_name}/LAZ", 
        f"input/{region_name}",
        f"input/LAZ/{region_name}",
        f"data/laz/{region_name}",
        f"output/{region_name}/LAZ",
        f"output/{region_name}/lidar"
    ]
    
    # Also check for files with region name in filename
    filename_patterns = [
        f"*{region_name}*.laz",
        f"*{region_name}*.copc.laz"
    ]
    
    found_files = []
    
    # Search in directory patterns
    for search_path in search_paths:
        if os.path.exists(search_path):
            logger.debug(f"Searching in directory: {search_path}")
            
            # Look for LAZ files in this directory
            for pattern in ["*.laz", "*.copc.laz"]:
                laz_files = list(Path(search_path).glob(pattern))
                for laz_file in laz_files:
                    full_path = str(laz_file)
                    if full_path not in found_files:
                        found_files.append(full_path)
                        logger.debug(f"Found LAZ file: {full_path}")
    
    # Search by filename patterns in common directories
    base_dirs = ["input", "data/laz", "output"]
    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            for pattern in filename_patterns:
                matching_files = list(Path(base_dir).rglob(pattern))
                for laz_file in matching_files:
                    full_path = str(laz_file)
                    if full_path not in found_files:
                        found_files.append(full_path)
                        logger.debug(f"Found LAZ file by pattern: {full_path}")
    
    if not found_files:
        error_msg = f"No LAZ file found for region '{region_name}' with processing_type '{processing_type}'"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    if len(found_files) == 1:
        selected_file = found_files[0]
        logger.info(f"✅ Resolved LAZ file: {selected_file}")
        return selected_file
    
    # Multiple files found - try to select the best match
    logger.warning(f"Multiple LAZ files found for region '{region_name}': {found_files}")
    
    # Prioritization logic:
    # 1. Files in input directories
    # 2. Files with exact region name match
    # 3. Most recent files
    
    prioritized_files = []
    
    # Priority 1: Files in input directories
    input_files = [f for f in found_files if f.startswith("input/")]
    if input_files:
        prioritized_files.extend(input_files)
    
    # Priority 2: Files with exact region name in filename
    exact_matches = [f for f in found_files if region_name in os.path.basename(f)]
    for exact_match in exact_matches:
        if exact_match not in prioritized_files:
            prioritized_files.append(exact_match)
    
    # Add remaining files
    for file in found_files:
        if file not in prioritized_files:
            prioritized_files.append(file)
    
    # Select the first prioritized file
    selected_file = prioritized_files[0]
    logger.info(f"✅ Selected LAZ file from multiple options: {selected_file}")
    logger.info(f"Other options were: {prioritized_files[1:]}")
    
    return selected_file

def _parse_stretch_params(stretch_params_json: Optional[str]) -> Optional[Dict[str, float]]:
    parsed_stretch_params = None
    if stretch_params_json:
        try:
            parsed_stretch_params = json.loads(stretch_params_json)
            if not isinstance(parsed_stretch_params, dict):
                logger.warning(f"stretch_params_json did not decode to a dict. Got: {type(parsed_stretch_params)}. Using None.")
                parsed_stretch_params = None
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in stretch_params_json: {stretch_params_json}. Error: {e}. Using None.")
    return parsed_stretch_params

@router.post("/api/laz_to_dem")
async def api_laz_to_dem(
    input_file: str = Form(...),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Convert LAZ to DEM (uses DSM processing internally for now)."""
    print(f"\n🎯 API CALL: /api/laz_to_dem")
    logger.info(f"/api/laz_to_dem called with input_file: {input_file}, stretch_type: {stretch_type}, stretch_params_json: {stretch_params_json}")
    
    try:
        from ..processing.dsm import dsm
        tif_path = dsm(input_file)
        print(f"✅ DEM (DSM) TIF generated: {tif_path}")

        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError in api_laz_to_dem: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in api_laz_to_dem: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"DEM processing failed: {str(e)}")

@router.post("/api/dtm")
async def api_dtm(
    input_file: str = Form(None),
    region_name: str = Form(None),
    processing_type: str = Form(None),
    display_region_name: str = Form(None),
    dtm_resolution: float = Form(1.0),
    dtm_csf_cloth_resolution: Optional[float] = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Convert LAZ to DTM (ground points only)"""
    print(f"\n🎯 API CALL: /api/dtm")
    logger.info(f"/api/dtm called with: region_name={region_name}, input_file={input_file}, dtm_res={dtm_resolution}, csf_res={dtm_csf_cloth_resolution}, stretch={stretch_type}")
    
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        output_region_for_path = display_region_name if display_region_name else region_name
        tif_path = dtm(
            effective_input_file,
            output_region_for_path,
            resolution=dtm_resolution,
            csf_cloth_resolution=dtm_csf_cloth_resolution
        )
        print(f"✅ DTM TIF generated: {tif_path}")
        
        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError in api_dtm: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except (ValueError, PermissionError) as e:
        logger.error(f"ValueError/PermissionError in api_dtm: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in api_dtm: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"DTM processing failed: {str(e)}")

@router.post("/api/dsm")
async def api_dsm(
    input_file: str = Form(None),
    region_name: str = Form(None),
    processing_type: str = Form(None),
    display_region_name: str = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Convert LAZ to DSM (surface points)"""
    print(f"\n🎯 API CALL: /api/dsm")
    logger.info(f"/api/dsm called with: region_name={region_name}, input_file={input_file}, stretch={stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        output_region = display_region_name if display_region_name else region_name
        tif_path = dsm(effective_input_file, output_region)
        print(f"✅ DSM TIF generated: {tif_path}")

        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError in api_dsm: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except (ValueError, PermissionError) as e:
        logger.error(f"ValueError/PermissionError in api_dsm: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in api_dsm: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"DSM processing failed: {str(e)}")

@router.post("/api/chm")
async def api_chm(
    input_file: str = Form(None),
    region_name: str = Form(None),
    processing_type: str = Form(None),
    display_region_name: str = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate CHM (Canopy Height Model) from LAZ file"""
    print(f"\n🎯 API CALL: /api/chm")
    logger.info(f"/api/chm called with: region_name={region_name}, input_file={input_file}, stretch={stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        output_region = display_region_name if display_region_name else region_name
        tif_path = chm(effective_input_file, output_region)
        print(f"✅ CHM TIF generated: {tif_path}")

        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        
        # Generate permanent PNG file for the raster gallery
        try:
            from convert import convert_geotiff_to_png
            import os
            
            # Create png_outputs directory structure
            tif_dir = os.path.dirname(tif_path)
            base_output_dir = os.path.dirname(tif_dir)  # Go up from CHM/ to lidar/
            png_output_dir = os.path.join(base_output_dir, "png_outputs")
            os.makedirs(png_output_dir, exist_ok=True)
            
            # Generate PNG with standard filename
            png_path = os.path.join(png_output_dir, "CHM.png")
            convert_geotiff_to_png(
                tif_path, 
                png_path, 
                enhanced_resolution=True,
                save_to_consolidated=False,  # Already in the right directory
                stretch_type=stretch_type if stretch_type else "stddev",
                stretch_params=parsed_stretch_params
            )
            print(f"✅ CHM PNG file created: {png_path}")
        except Exception as png_error:
            print(f"⚠️ CHM PNG generation failed: {png_error}")
            # Continue anyway since base64 conversion might still work

        # Generate base64 for immediate display
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except Exception as e:
        logger.error(f"Error in api_chm: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"CHM processing failed: {str(e)}")

@router.post("/api/hillshade")
async def api_hillshade(
    input_file: str = Form(None),
    region_name: str = Form(None),
    processing_type: str = Form(None),
    display_region_name: str = Form(None),
    dtm_resolution: float = Form(1.0),
    dtm_csf_cloth_resolution: Optional[float] = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate standard hillshade from LAZ file"""
    print(f"\n🎯 API CALL: /api/hillshade")
    logger.info(f"/api/hillshade called for region: {region_name}, file: {input_file}, dtm_res: {dtm_resolution}, csf_res: {dtm_csf_cloth_resolution}, stretch: {stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        output_region_for_path = display_region_name if display_region_name else region_name
        tif_path = hillshade(
            effective_input_file,
            output_region_for_path,
            dtm_resolution=dtm_resolution,
            dtm_csf_cloth_resolution=dtm_csf_cloth_resolution
        )
        print(f"✅ Standard Hillshade TIF generated: {tif_path}")
        
        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError in api_hillshade: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"ValueError in api_hillshade: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in api_hillshade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Standard hillshade processing failed: {str(e)}")

@router.post("/api/hillshade_315_45_08")
async def api_hillshade_315_45_08(
    input_file: str = Form(None),
    region_name: str = Form(None),
    processing_type: str = Form(None),
    display_region_name: str = Form(None),
    dtm_resolution: float = Form(1.0),
    dtm_csf_cloth_resolution: Optional[float] = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate hillshade (Az315, Alt45, Z0.8)"""
    print(f"\n🎯 API CALL: /api/hillshade_315_45_08")
    logger.info(f"/api/hillshade_315_45_08 called for region: {region_name}, file: {input_file}, dtm_res: {dtm_resolution}, csf_res: {dtm_csf_cloth_resolution}, stretch: {stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        output_region_for_path = display_region_name if display_region_name else region_name
        tif_path = hillshade_315_45_08(
            effective_input_file,
            output_region_for_path,
            dtm_resolution=dtm_resolution,
            dtm_csf_cloth_resolution=dtm_csf_cloth_resolution
        )
        print(f"✅ Hillshade Az315 Alt45 Z0.8 TIF generated: {tif_path}")
        
        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError in api_hillshade_315_45_08: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"ValueError in api_hillshade_315_45_08: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in api_hillshade_315_45_08: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Hillshade 315_45_08 processing failed: {str(e)}")

@router.post("/api/hillshade_225_45_08")
async def api_hillshade_225_45_08(
    input_file: str = Form(None),
    region_name: str = Form(None),
    processing_type: str = Form(None),
    display_region_name: str = Form(None),
    dtm_resolution: float = Form(1.0),
    dtm_csf_cloth_resolution: Optional[float] = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate hillshade (Az225, Alt45, Z0.8)"""
    print(f"\n🎯 API CALL: /api/hillshade_225_45_08")
    logger.info(f"/api/hillshade_225_45_08 called for region: {region_name}, file: {input_file}, dtm_res: {dtm_resolution}, csf_res: {dtm_csf_cloth_resolution}, stretch: {stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        output_region_for_path = display_region_name if display_region_name else region_name
        tif_path = hillshade_225_45_08(
            effective_input_file,
            output_region_for_path,
            dtm_resolution=dtm_resolution,
            dtm_csf_cloth_resolution=dtm_csf_cloth_resolution
        )
        print(f"✅ Hillshade Az225 Alt45 Z0.8 TIF generated: {tif_path}")
        
        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError in api_hillshade_225_45_08: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"ValueError in api_hillshade_225_45_08: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in api_hillshade_225_45_08: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Hillshade 225_45_08 processing failed: {str(e)}")

@router.post("/api/hillshade_custom")
async def api_hillshade_custom(
    input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None),
    display_region_name: str = Form(None), azimuth: float = Form(315.0),
    altitude: float = Form(45.0), z_factor: float = Form(1.0),
    dtm_resolution: float = Form(1.0), dtm_csf_cloth_resolution: Optional[float] = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate hillshade with custom azimuth, altitude, z-factor, and DTM resolution."""
    print(f"\n🎯 API CALL: /api/hillshade_custom")
    logger.info(f"/api/hillshade_custom called for region: {region_name}, file: {input_file}, az: {azimuth}, alt: {altitude}, z: {z_factor}, dtm_res: {dtm_resolution}, csf_res: {dtm_csf_cloth_resolution}, stretch: {stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not effective_input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        output_region_name_for_path = display_region_name if display_region_name else region_name
        custom_suffix = f"custom_az{int(azimuth)}_alt{int(altitude)}_z{str(z_factor).replace('.', 'p')}"
        tif_path = generate_hillshade_with_params(
            input_file=effective_input_file, azimuth=azimuth, altitude=altitude, z_factor=z_factor,
            suffix=custom_suffix, region_name=output_region_name_for_path,
            dtm_resolution=dtm_resolution, dtm_csf_cloth_resolution=dtm_csf_cloth_resolution
        )
        print(f"✅ Custom Hillshade TIF generated: {tif_path}")
        
        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError in api_hillshade_custom: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"ValueError in api_hillshade_custom: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in api_hillshade_custom: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Hillshade custom processing failed: {str(e)}")

@router.post("/api/composite_dtm_hillshade_blend")
async def api_composite_dtm_hillshade_blend(
    input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None),
    display_region_name: str = Form(None), dtm_resolution: float = Form(1.0),
    dtm_csf_cloth_resolution: Optional[float] = Form(None), hillshade_azimuth: float = Form(315.0),
    hillshade_altitude: float = Form(45.0), hillshade_z_factor: float = Form(1.0),
    hillshade_suffix: str = Form("standard"), blend_factor: float = Form(0.6),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate a blended DTM (color relief) and Hillshade composite."""
    print(f"\n🎯 API CALL: /api/composite_dtm_hillshade_blend")
    logger.info(f"/api/composite_dtm_hillshade_blend called for region: {region_name}, file: {input_file}, dtm_res: {dtm_resolution}, csf_res: {dtm_csf_cloth_resolution}, hs_az: {hillshade_azimuth}, blend: {blend_factor}, stretch: {stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not effective_input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        output_region_name_for_path = display_region_name if display_region_name else region_name
        tif_path = generate_dtm_hillshade_blend(
            laz_input_file=effective_input_file, region_name_for_output=output_region_name_for_path,
            dtm_resolution=dtm_resolution, dtm_csf_cloth_resolution=dtm_csf_cloth_resolution,
            hillshade_azimuth=hillshade_azimuth, hillshade_altitude=hillshade_altitude,
            hillshade_z_factor=hillshade_z_factor, hillshade_suffix=hillshade_suffix,
            blend_factor=blend_factor
        )
        print(f"✅ DTM-Hillshade Blend Composite TIF generated: {tif_path}")
        
        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete for composite")
        return {"image": image_b64}
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError in api_composite_dtm_hillshade_blend: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"ValueError in api_composite_dtm_hillshade_blend: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in api_composite_dtm_hillshade_blend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"DTM-Hillshade Blend composite processing failed: {str(e)}")

@router.post("/api/slope")
async def api_slope(
    input_file: str = Form(None), region_name: str = Form(None),
    processing_type: str = Form(None), display_region_name: str = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate slope from LAZ file"""
    print(f"\n🎯 API CALL: /api/slope")
    logger.info(f"/api/slope called for region: {region_name}, file: {input_file}, stretch: {stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        output_region = display_region_name if display_region_name else region_name
        tif_path = slope(effective_input_file, output_region)
        print(f"✅ Slope TIF generated: {tif_path}")

        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except Exception as e:
        logger.error(f"Error in api_slope: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Slope processing failed: {str(e)}")

@router.post("/api/aspect")
async def api_aspect(
    input_file: str = Form(None), region_name: str = Form(None),
    processing_type: str = Form(None), display_region_name: str = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate aspect from LAZ file"""
    print(f"\n🎯 API CALL: /api/aspect")
    logger.info(f"/api/aspect called for region: {region_name}, file: {input_file}, stretch: {stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        output_region = display_region_name if display_region_name else region_name
        tif_path = aspect(effective_input_file, output_region)
        print(f"✅ Aspect TIF generated: {tif_path}")

        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except Exception as e:
        logger.error(f"Error in api_aspect: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Aspect processing failed: {str(e)}")

@router.post("/api/color_relief")
async def api_color_relief(
    input_file: str = Form(None),
    region_name: str = Form(None),
    processing_type: str = Form(None),
    display_region_name: str = Form(None),
    ramp_name: str = Form("arch_subtle"),
    dtm_resolution: float = Form(1.0),
    dtm_csf_cloth_resolution: Optional[float] = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate color relief from LAZ file"""
    print(f"\n🎯 API CALL: /api/color_relief")
    logger.info(f"/api/color_relief called for region: {region_name}, file: {input_file}, ramp: {ramp_name}, dtm_res: {dtm_resolution}, csf_res: {dtm_csf_cloth_resolution}, stretch: {stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        output_region_name_for_path = display_region_name if display_region_name else region_name
        # Call the underlying async process_color_relief which then calls the sync color_relief
        # This ensures parameters are passed down correctly as process_color_relief expects a dict
        from ..processing.color_relief import process_color_relief as process_color_relief_async

        # The process_color_relief async function expects output_dir and parameters dict
        # output_dir for the async wrapper is typically "output/REGION_NAME"
        # and it then constructs subdirectories.
        # For consistency, we'll use the same output_region_name_for_path for the base output_dir.
        base_output_dir_for_async = os.path.join("output", output_region_name_for_path)

        processing_params = {
            "ramp_name": ramp_name,
            "dtm_resolution": dtm_resolution,
            "dtm_csf_cloth_resolution": dtm_csf_cloth_resolution
        }

        result_dict = await process_color_relief_async(
            laz_file_path=effective_input_file,
            output_dir=base_output_dir_for_async, # Base output directory
            parameters=processing_params
        )

        if not result_dict.get("success"):
            raise Exception(result_dict.get("message", "Color relief processing failed in async wrapper."))

        tif_path = result_dict["output_file"]
        print(f"✅ Color Relief TIF generated with ramp '{ramp_name}': {tif_path}")

        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except Exception as e:
        logger.error(f"Error in api_color_relief: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Color Relief processing failed: {str(e)}")

@router.post("/api/tpi")
async def api_tpi(
    input_file: str = Form(None), region_name: str = Form(None),
    processing_type: str = Form(None), display_region_name: str = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate TPI from LAZ file"""
    print(f"\n🎯 API CALL: /api/tpi")
    logger.info(f"/api/tpi called for region: {region_name}, file: {input_file}, stretch: {stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        output_region = display_region_name if display_region_name else region_name
        tif_path = tpi(effective_input_file, output_region)
        print(f"✅ TPI TIF generated: {tif_path}")

        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except Exception as e:
        logger.error(f"Error in api_tpi: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TPI processing failed: {str(e)}")

@router.post("/api/roughness")
async def api_roughness(
    input_file: str = Form(None), region_name: str = Form(None),
    processing_type: str = Form(None), display_region_name: str = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate roughness from LAZ file"""
    print(f"\n🎯 API CALL: /api/roughness")
    logger.info(f"/api/roughness called for region: {region_name}, file: {input_file}, stretch: {stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        output_region = display_region_name if display_region_name else region_name
        tif_path = roughness(effective_input_file, output_region)
        print(f"✅ Roughness TIF generated: {tif_path}")

        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except Exception as e:
        logger.error(f"Error in api_roughness: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Roughness processing failed: {str(e)}")

@router.post("/api/sky_view_factor")
async def api_sky_view_factor(
    input_file: str = Form(None), region_name: str = Form(None),
    processing_type: str = Form(None), display_region_name: str = Form(None),
    stretch_type: Optional[str] = Form("stddev"),
    stretch_params_json: Optional[str] = Form(None)
):
    """Generate Sky View Factor from LAZ file"""
    print(f"\n🎯 API CALL: /api/sky_view_factor")
    logger.info(f"/api/sky_view_factor called for region: {region_name}, file: {input_file}, stretch: {stretch_type}")
    effective_input_file = input_file
    if region_name and processing_type:
        effective_input_file = resolve_laz_file_from_region(region_name, processing_type)
    elif not input_file:
        raise HTTPException(status_code=400, detail="Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        output_region = display_region_name if display_region_name else region_name
        tif_path = sky_view_factor(effective_input_file, output_region)
        print(f"✅ SVF TIF generated: {tif_path}")

        parsed_stretch_params = _parse_stretch_params(stretch_params_json)
        image_b64 = convert_geotiff_to_png_base64(
            tif_path,
            stretch_type=stretch_type if stretch_type else "stddev",
            stretch_params=parsed_stretch_params
        )
        print(f"✅ Base64 conversion complete")
        return {"image": image_b64}
    except Exception as e:
        logger.error(f"Error in api_sky_view_factor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sky View Factor processing failed: {str(e)}")
