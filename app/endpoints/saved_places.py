from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import os
import json

router = APIRouter()

@router.get("/api/saved-places")
async def get_saved_places():
    """Get all saved places from JSON storage"""
    print(f"\n📍 API CALL: GET /api/saved-places")
    
    try:
        saved_places_file = os.path.join(os.path.dirname(__file__), "data", "saved_places.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(saved_places_file), exist_ok=True)
        
        if os.path.exists(saved_places_file):
            with open(saved_places_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                places = data.get('places', [])
        else:
            places = []
            
        print(f"📍 Loaded {len(places)} saved places")
        return {"places": places}
        
    except Exception as e:
        print(f"❌ Error loading saved places: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to load saved places: {str(e)}"}
        )

@router.post("/api/saved-places")
async def save_places(request: Request):
    """Save places data to JSON storage"""
    print(f"\n💾 API CALL: POST /api/saved-places")
    
    try:
        # Get request data
        data = await request.json()
        places = data.get('places', [])
        
        print(f"💾 Saving {len(places)} places")
        
        # Validate places data
        for place in places:
            if not all(key in place for key in ['id', 'name', 'lat', 'lng']):
                raise ValueError("Invalid place data - missing required fields")
            
            # Validate coordinates
            if not (-90 <= place['lat'] <= 90):
                raise ValueError(f"Invalid latitude: {place['lat']}")
            if not (-180 <= place['lng'] <= 180):
                raise ValueError(f"Invalid longitude: {place['lng']}")
        
        # Save to file
        saved_places_file = os.path.join(os.path.dirname(__file__), "data", "saved_places.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(saved_places_file), exist_ok=True)
        
        # Prepare data with metadata
        save_data = {
            "places": places,
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        with open(saved_places_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(places)} places successfully")
        return {"success": True, "message": f"Saved {len(places)} places successfully"}
        
    except Exception as e:
        print(f"❌ Error saving places: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to save places: {str(e)}"}
        )

@router.delete("/api/saved-places/{place_id}")
async def delete_saved_place(place_id: str):
    """Delete a specific saved place"""
    print(f"\n🗑️  API CALL: DELETE /api/saved-places/{place_id}")
    
    try:
        saved_places_file = os.path.join(os.path.dirname(__file__), "data", "saved_places.json")
        
        if not os.path.exists(saved_places_file):
            return JSONResponse(
                status_code=404,
                content={"error": "No saved places found"}
            )
        
        # Load current places
        with open(saved_places_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            places = data.get('places', [])
        
        # Find and remove the place
        original_count = len(places)
        places = [place for place in places if place.get('id') != place_id]
        
        if len(places) == original_count:
            return JSONResponse(
                status_code=404,
                content={"error": f"Place with ID {place_id} not found"}
            )
        
        # Save updated places
        save_data = {
            "places": places,
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        with open(saved_places_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Deleted place {place_id} successfully")
        return {"success": True, "message": f"Place deleted successfully", "remaining_count": len(places)}
        
    except Exception as e:
        print(f"❌ Error deleting place: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to delete place: {str(e)}"}
        )

@router.get("/api/saved-places/export")
async def export_saved_places():
    """Export saved places as downloadable JSON file"""
    print(f"\n📤 API CALL: GET /api/saved-places/export")
    
    try:
        saved_places_file = os.path.join(os.path.dirname(__file__), "data", "saved_places.json")
        
        if not os.path.exists(saved_places_file):
            places = []
        else:
            with open(saved_places_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                places = data.get('places', [])
        
        # Create export data
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "format_version": "1.0",
            "total_places": len(places),
            "places": places
        }
        
        # Create filename with current date
        filename = f"saved_places_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        print(f"📤 Exporting {len(places)} places")
        
        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/json"
            }
        )
        
    except Exception as e:
        print(f"❌ Error exporting places: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to export places: {str(e)}"}
        )

# ============================================================================
# END SAVED PLACES API ENDPOINTS
# ============================================================================


