async def generate_rasters(request: RasterGenerationRequest):
    """Generate raster products from elevation TIFF files in a region"""
    try:
        print(f"\n🎨 API CALL: /api/generate-rasters")
        print(f"🏷️ Region: {request.region_name}")
        
        # Import the raster generation service
        from ..api_raster_generation import generate_rasters_for_region
        
        # Create progress callback that sends updates via WebSocket
        async def progress_callback(update):
            await manager.send_progress_update({
                "source": "raster_generation",
                "region_name": request.region_name,
                **update
            })
        
        # Send initial progress update
        await progress_callback({
            "type": "raster_generation_started",
            "message": f"Starting raster generation for region: {request.region_name}",
            "progress": 0
        })
        
        # Generate raster products
        result = await generate_rasters_for_region(request.region_name)
        
        if result['success']:
            # Send completion update
            await progress_callback({
                "type": "raster_generation_completed",
                "message": f"Raster generation completed successfully for {request.region_name}",
                "progress": 100,
                "products_generated": result['products_generated'],
                "total_products": result['total_products']
            })
            
            return {
                "success": True,
                "region_name": request.region_name,
                "products_generated": result['products_generated'],
                "png_outputs": result['png_outputs'],
                "total_products": result['total_products'],
                "processing_time": result['processing_time'],
                "message": f"Generated {result['total_products']} raster products for region {request.region_name}",
                "errors": result.get('errors', [])
            }
        else:
            # Send error update
            error_messages = result.get('errors', ['Unknown error'])
            error_text = '; '.join(error_messages)
            await progress_callback({
                "type": "raster_generation_error",
                "message": f"Raster generation failed: {error_text}",
                "progress": 0
            })
            
            raise HTTPException(
                status_code=400,
                detail=error_text
            )
    
    except HTTPException:
        raise
    except Exception as e:
        # Send error update via WebSocket if possible
        try:
            await manager.send_progress_update({
                "source": "raster_generation",
                "region_name": request.region_name,
                "type": "raster_generation_error",
                "message": f"Raster generation error: {str(e)}"
            })
        except:
            pass
        
        print(f"❌ Error in generate_rasters: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Raster generation failed: {str(e)}")
