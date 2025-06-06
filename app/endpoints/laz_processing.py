from fastapi import APIRouter, HTTPException, Form
from ..main import manager, settings
from fastapi.responses import JSONResponse
from ..convert import convert_geotiff_to_png_base64
from ..processing import dtm, dsm, chm, hillshade, hillshade_315_45_08, hillshade_225_45_08, slope, aspect, color_relief, tri, tpi, roughness

router = APIRouter()

def resolve_laz_file_from_region(region_name: str, processing_type: str) -> str:
    """
    Utility function to resolve LAZ file path from region name using the region mapping system.
    
    Args:
        region_name: The region name provided by the user
        processing_type: The type of processing being requested
        
    Returns:
        str: Path to the LAZ file
        
    Raises:
        ValueError: If no LAZ file can be found for the region
    """
    print(f"📍 Region-based processing: {region_name}")
    print(f"🔧 Processing type: {processing_type}")
    
    # Import region mapping system
    from ..region_config.region_mapping import region_mapper
    
    # Use region mapper to find the correct LAZ file
    input_file = region_mapper.find_laz_file_for_region(region_name)
    
    if not input_file:
        # List available regions for debugging
        available_regions = region_mapper.get_available_regions()
        print(f"❌ Available regions: {available_regions}")
        raise ValueError(f"No LAZ files found for region '{region_name}'. Available regions: {available_regions}")
    
    print(f"📥 Using LAZ file: {input_file}")
    return input_file

@router.post("/api/laz_to_dem")
async def api_laz_to_dem(input_file: str = Form(...)):
    """Convert LAZ to DEM"""
    print(f"\n🎯 API CALL: /api/laz_to_dem")
    print(f"📥 Input file: {input_file}")
    
    try:
        # Import the synchronous function
        from ..processing.laz_to_dem import laz_to_dem
        
        # Call the synchronous function directly
        tif_path = laz_to_dem(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
            
    except Exception as e:
        print(f"❌ Error in api_laz_to_dem: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise
        print(f"❌ Error type: {type(e).__name__}")
        raise

@router.post("/api/dtm")
async def api_dtm(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):
    """Convert LAZ to DTM (ground points only) - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/dtm")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        # Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        tif_path = dtm(input_file, output_region)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        print(f"❌ Error in api_dtm: {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        raise HTTPException(status_code=404, detail=error_msg)
    except (ValueError, PermissionError) as e:
        error_msg = f"Invalid input: {str(e)}"
        print(f"❌ Error in api_dtm: {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"DTM processing failed: {str(e)}"
        print(f"❌ Error in api_dtm: {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/api/dsm")
async def api_dsm(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):
    """Convert LAZ to DSM (surface points) - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/dsm")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        # Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        
        # Check if dsm function accepts region_name parameter
        try:
            from inspect import signature
            sig = signature(dsm)
            if 'region_name' in sig.parameters:
                tif_path = dsm(input_file, output_region)
            else:
                tif_path = dsm(input_file)
        except:
            # Fallback to original function call if anything goes wrong
            tif_path = dsm(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        print(f"❌ Error in api_dsm: {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        raise HTTPException(status_code=404, detail=error_msg)
    except (ValueError, PermissionError) as e:
        error_msg = f"Invalid input: {str(e)}"
        print(f"❌ Error in api_dsm: {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"DSM processing failed: {str(e)}"
        print(f"❌ Error in api_dsm: {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/api/chm")
async def api_chm(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):
    """Generate CHM (Canopy Height Model) from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/chm")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        # Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        
        # Check if chm function accepts region_name parameter
        try:
            from inspect import signature
            sig = signature(chm)
            if 'region_name' in sig.parameters:
                tif_path = chm(input_file, output_region)
            else:
                tif_path = chm(input_file)
        except:
            # Fallback to original function call if anything goes wrong
            tif_path = chm(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_chm: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@router.post("/api/hillshade")
async def api_hillshade(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):
    """Generate hillshade from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/hillshade")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        # Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        
        # Check if hillshade function accepts region_name parameter
        try:
            from inspect import signature
            sig = signature(hillshade)
            if 'region_name' in sig.parameters:
                tif_path = hillshade(input_file, output_region)
            else:
                tif_path = hillshade(input_file)
        except:
            # Fallback to original function call if anything goes wrong
            tif_path = hillshade(input_file)
        output_region = display_region_name if display_region_name else region_name
        
        # Check if hillshade function accepts region_name parameter
        try:
            from inspect import signature
            sig = signature(hillshade)
            if 'region_name' in sig.parameters:
                tif_path = hillshade(input_file, output_region)
            else:
                tif_path = hillshade(input_file)
        except:
            # Fallback to original function call if anything goes wrong
            tif_path = hillshade(input_file)
            
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_hillshade: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@router.post("/api/hillshade_315_45_08")
async def api_hillshade_315_45_08(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):
    """Generate hillshade with 315° azimuth, 45° altitude, 0.8 z-factor - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/hillshade_315_45_08")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        # Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        tif_path = hillshade_315_45_08(input_file, output_region)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_hillshade_315_45_08: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@router.post("/api/hillshade_225_45_08")
async def api_hillshade_225_45_08(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):
    """Generate hillshade with 225° azimuth, 45° altitude, 0.8 z-factor - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/hillshade_225_45_08")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        # Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        tif_path = hillshade_225_45_08(input_file, output_region)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_hillshade_225_45_08: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@router.post("/api/slope")
async def api_slope(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):
    """Generate slope from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/slope")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")

    try:
        # Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        
        # Check if slope function accepts region_name parameter
        try:
            from inspect import signature
            sig = signature(slope)
            if 'region_name' in sig.parameters:
                tif_path = slope(input_file, output_region)
            else:
                tif_path = slope(input_file)
        except:
            # Fallback to original function call if anything goes wrong
            tif_path = slope(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_slope: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@router.post("/api/aspect")
async def api_aspect(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):
    """Generate aspect from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/aspect")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        # Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        
        # Check if aspect function accepts region_name parameter
        try:
            from inspect import signature
            sig = signature(aspect)
            if 'region_name' in sig.parameters:
                tif_path = aspect(input_file, output_region)
            else:
                tif_path = aspect(input_file)
        except:
            # Fallback to original function call if anything goes wrong
            tif_path = aspect(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_aspect: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@router.post("/api/color_relief")
async def api_color_relief(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None)):
    """Generate color relief from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/color_relief")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        tif_path = color_relief(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_color_relief: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@router.post("/api/tri")
async def api_tri(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):
    """Generate TRI from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/tri")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        # Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        
        # Check if tri function accepts region_name parameter
        try:
            from inspect import signature
            sig = signature(tri)
            if 'region_name' in sig.parameters:
                tif_path = tri(input_file, output_region)
            else:
                tif_path = tri(input_file)
        except:
            # Fallback to original function call if anything goes wrong
            tif_path = tri(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_tri: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@router.post("/api/tpi")
async def api_tpi(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):
    """Generate TPI from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/tpi")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        # Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        
        # Check if tpi function accepts region_name parameter
        try:
            from inspect import signature
            sig = signature(tpi)
            if 'region_name' in sig.parameters:
                tif_path = tpi(input_file, output_region)
            else:
                tif_path = tpi(input_file)
        except:
            # Fallback to original function call if anything goes wrong
            tif_path = tpi(input_file)
        print(f"✅ TIF generated: {tif_path}")
        
        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")
        
        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_tpi: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise

@router.post("/api/roughness")
async def api_roughness(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):
    """Generate roughness from LAZ file - supports both region-based and LAZ file processing"""
    print(f"\n🎯 API CALL: /api/roughness")
    
    # Determine processing mode: region-based or LAZ file-based
    if region_name and processing_type:
        # Region-based processing: find LAZ file in region
        print(f"📍 Region-based processing: {region_name}")
        print(f"🔧 Processing type: {processing_type}")
        
        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)
        
    elif input_file:
        # LAZ file-based processing (legacy support)
        print(f"📥 LAZ file-based processing: {input_file}")
        
    else:
        raise ValueError("Either 'input_file' or both 'region_name' and 'processing_type' must be provided")
    
    try:
        # Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        
        # Check if roughness function accepts region_name parameter
        try:
            from inspect import signature
            sig = signature(roughness)
            if 'region_name' in sig.parameters:
                tif_path = roughness(input_file, output_region)
            else:
                tif_path = roughness(input_file)
        except:
            # Fallback to original function call if anything goes wrong
            tif_path = roughness(input_file)
        print(f"✅ TIF generated: {tif_path}")

        image_b64 = convert_geotiff_to_png_base64(tif_path)
        print(f"✅ Base64 conversion complete")

        return {"image": image_b64}
    except Exception as e:
        print(f"❌ Error in api_roughness: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise
