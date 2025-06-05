@app.get("/api/pipelines/json")
async def list_json_pipelines():
    """List all available JSON pipelines"""
    print(f"\n🔧 API CALL: /api/pipelines/json")
    
    try:
        from .processing.json_processor import get_processor
        
        processor = get_processor()
        pipelines = processor.list_available_json_pipelines()
        
        print(f"✅ Found {len(pipelines)} JSON pipelines")
        
        return {
            "success": True,
            "pipelines": pipelines,
            "count": len(pipelines)
        }
        
    except Exception as e:
        print(f"❌ Error listing JSON pipelines: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "pipelines": []
        }

@app.get("/api/pipelines/json/{pipeline_name}")
async def get_json_pipeline_info(pipeline_name: str):
    """Get information about a specific JSON pipeline"""
    print(f"\n🔧 API CALL: /api/pipelines/json/{pipeline_name}")
    
    try:
        from .processing.json_processor import get_processor
        
        processor = get_processor()
        pipeline_info = processor.get_pipeline_info(pipeline_name)
        
        if pipeline_info:
            print(f"✅ Pipeline info retrieved for: {pipeline_name}")
            return {
                "success": True,
                "pipeline_name": pipeline_name,
                "pipeline": pipeline_info
            }
        else:
            print(f"❌ Pipeline not found: {pipeline_name}")
            return {
                "success": False,
                "error": f"Pipeline '{pipeline_name}' not found"
            }
        
    except Exception as e:
        print(f"❌ Error getting pipeline info: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/pipelines/toggle-json")
async def toggle_json_pipelines(data: dict):
    """Toggle JSON pipeline usage on/off"""
    print(f"\n🔧 API CALL: /api/pipelines/toggle-json")
    
    try:
        use_json = data.get("use_json", True)
        
        from .processing.json_processor import set_use_json_pipelines
        set_use_json_pipelines(use_json)
        
        print(f"✅ JSON pipeline usage set to: {use_json}")
        
        return {
            "success": True,
            "use_json_pipelines": use_json,
            "message": f"JSON pipelines {'enabled' if use_json else 'disabled'}"
        }
        
    except Exception as e:
        print(f"❌ Error toggling JSON pipelines: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

