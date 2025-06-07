"""
Saved Places Service

Handles saved places management operations.
"""

from typing import Dict, Any, Optional, List
from .base_service import BaseService, SyncServiceMixin


class SavedPlacesService(BaseService, SyncServiceMixin):
    """Service for saved places management operations"""
    
    async def get_saved_places(self) -> Dict[str, Any]:
        """Get all saved places from JSON storage"""
        return await self._get('/api/saved-places')
    
    async def save_place(self, place_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a new place"""
        return await self._post('/api/saved-places', json_data=place_data)
    
    async def update_place(self, place_id: str, place_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing place"""
        return await self._put(f'/api/saved-places/{place_id}', json_data=place_data)
    
    async def delete_place(self, place_id: str) -> Dict[str, Any]:
        """Delete a specific saved place"""
        return await self._delete(f'/api/saved-places/{place_id}')
    
    async def export_saved_places(self) -> Dict[str, Any]:
        """Export saved places as downloadable JSON file"""
        return await self._get('/api/saved-places/export')
    
    async def import_saved_places(self, places_data: List[Dict[str, Any]], merge: bool = True) -> Dict[str, Any]:
        """Import saved places from JSON data"""
        data = {
            'places': places_data,
            'merge': merge
        }
        return await self._post('/api/saved-places/import', json_data=data)
    
    async def search_places(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search saved places by query and optional filters"""
        params = {'query': query}
        if filters:
            params.update(filters)
        
        return await self._get('/api/saved-places/search', params=params)
    
    async def get_place_by_id(self, place_id: str) -> Dict[str, Any]:
        """Get a specific place by ID"""
        return await self._get(f'/api/saved-places/{place_id}')
    
    async def get_places_by_category(self, category: str) -> Dict[str, Any]:
        """Get places filtered by category"""
        return await self._get('/api/saved-places/category', params={'category': category})
    
    async def get_places_near_coordinates(self, latitude: float, longitude: float, radius_km: float = 10.0) -> Dict[str, Any]:
        """Get places near specified coordinates"""
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'radius_km': radius_km
        }
        return await self._get('/api/saved-places/nearby', params=params)
    
    async def add_place_note(self, place_id: str, note: str) -> Dict[str, Any]:
        """Add a note to a saved place"""
        data = {'note': note}
        return await self._post(f'/api/saved-places/{place_id}/notes', json_data=data)
    
    async def update_place_coordinates(self, place_id: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """Update coordinates for a saved place"""
        data = {
            'latitude': latitude,
            'longitude': longitude
        }
        return await self._put(f'/api/saved-places/{place_id}/coordinates', json_data=data)
    
    async def add_place_to_collection(self, place_id: str, collection_name: str) -> Dict[str, Any]:
        """Add a place to a collection"""
        data = {'collection_name': collection_name}
        return await self._post(f'/api/saved-places/{place_id}/collections', json_data=data)
    
    async def remove_place_from_collection(self, place_id: str, collection_name: str) -> Dict[str, Any]:
        """Remove a place from a collection"""
        return await self._delete(f'/api/saved-places/{place_id}/collections/{collection_name}')
    
    async def get_collections(self) -> Dict[str, Any]:
        """Get all place collections"""
        return await self._get('/api/saved-places/collections')
    
    async def create_collection(self, collection_name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new place collection"""
        data = {'name': collection_name}
        if description:
            data['description'] = description
        
        return await self._post('/api/saved-places/collections', json_data=data)
    
    async def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete a place collection"""
        return await self._delete(f'/api/saved-places/collections/{collection_name}')
    
    async def backup_places(self) -> Dict[str, Any]:
        """Create a backup of all saved places"""
        return await self._post('/api/saved-places/backup')
    
    async def restore_places(self, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Restore saved places from backup"""
        return await self._post('/api/saved-places/restore', json_data=backup_data)
