"""
Overlay Service

Handles overlay data operations for image visualization and mapping.
"""

from typing import Dict, Any, Optional, List
from .base_service import BaseService, SyncServiceMixin


class OverlayService(BaseService, SyncServiceMixin):
    """Service for overlay data operations"""
    
    async def get_overlay_data(self, processing_type: str, filename: str) -> Dict[str, Any]:
        """Get overlay data for a processed image including bounds and base64 encoded image"""
        return await self._get(f'/api/overlay/{processing_type}/{filename}')
    
    async def get_raster_overlay_data(self, region_name: str, processing_type: str) -> Dict[str, Any]:
        """Get overlay data for raster-processed images from regions"""
        return await self._get(f'/api/overlay/raster/{region_name}/{processing_type}')
    
    async def get_sentinel2_overlay_data(self, region_band: str) -> Dict[str, Any]:
        """Get overlay data for a Sentinel-2 image including bounds and base64 encoded image"""
        return await self._get(f'/api/overlay/sentinel2/{region_band}')
    
    async def get_test_overlay(self, filename: str) -> Dict[str, Any]:
        """Get test overlay data"""
        return await self._get(f'/api/test-overlay/{filename}')
    
    async def create_overlay_from_geotiff(self, file_path: str, bounds: Dict[str, float]) -> Dict[str, Any]:
        """Create overlay from GeoTIFF file"""
        data = {
            'file_path': file_path,
            'bounds': bounds
        }
        return await self._post('/api/overlay/create-from-geotiff', json_data=data)
    
    async def get_overlay_bounds(self, region_name: str, processing_type: str) -> Dict[str, Any]:
        """Get overlay bounds for a specific region and processing type"""
        return await self._get(f'/api/overlay/bounds/{region_name}/{processing_type}')
    
    async def list_available_overlays(self, region_name: Optional[str] = None) -> Dict[str, Any]:
        """List all available overlays, optionally filtered by region"""
        params = {}
        if region_name:
            params['region_name'] = region_name
        
        return await self._get('/api/overlay/list', params=params)
    
    async def get_overlay_metadata(self, overlay_id: str) -> Dict[str, Any]:
        """Get metadata for a specific overlay"""
        return await self._get(f'/api/overlay/metadata/{overlay_id}')
    
    async def update_overlay_opacity(self, overlay_id: str, opacity: float) -> Dict[str, Any]:
        """Update overlay opacity"""
        data = {'opacity': opacity}
        return await self._put(f'/api/overlay/{overlay_id}/opacity', json_data=data)
    
    async def toggle_overlay_visibility(self, overlay_id: str, visible: bool) -> Dict[str, Any]:
        """Toggle overlay visibility"""
        data = {'visible': visible}
        return await self._put(f'/api/overlay/{overlay_id}/visibility', json_data=data)
    
    async def delete_overlay(self, overlay_id: str) -> Dict[str, Any]:
        """Delete an overlay"""
        return await self._delete(f'/api/overlay/{overlay_id}')
    
    async def create_composite_overlay(self, overlay_ids: List[str], output_name: str) -> Dict[str, Any]:
        """Create a composite overlay from multiple overlays"""
        data = {
            'overlay_ids': overlay_ids,
            'output_name': output_name
        }
        return await self._post('/api/overlay/composite', json_data=data)
    
    async def export_overlay(self, overlay_id: str, format: str = 'png') -> Dict[str, Any]:
        """Export overlay to specified format"""
        params = {'format': format}
        return await self._get(f'/api/overlay/{overlay_id}/export', params=params)
    
    async def get_overlay_statistics(self, overlay_id: str) -> Dict[str, Any]:
        """Get statistical information about an overlay"""
        return await self._get(f'/api/overlay/{overlay_id}/statistics')
    
    async def apply_color_ramp(self, overlay_id: str, color_ramp: str) -> Dict[str, Any]:
        """Apply color ramp to an overlay"""
        data = {'color_ramp': color_ramp}
        return await self._put(f'/api/overlay/{overlay_id}/color-ramp', json_data=data)
    
    async def crop_overlay(self, overlay_id: str, bounds: Dict[str, float]) -> Dict[str, Any]:
        """Crop an overlay to specified bounds"""
        data = {'bounds': bounds}
        return await self._post(f'/api/overlay/{overlay_id}/crop', json_data=data)
