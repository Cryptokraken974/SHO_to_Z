"""
GeoTIFF Service

Handles GeoTIFF file operations and conversions.
"""

from typing import Dict, Any, Optional, List
from .base_service import BaseService, SyncServiceMixin


class GeotiffService(BaseService, SyncServiceMixin):
    """Service for GeoTIFF file operations and conversions"""
    
    async def list_geotiff_files(self, region_name: Optional[str] = None) -> Dict[str, Any]:
        """List available GeoTIFF files"""
        params = {}
        if region_name:
            params['region_name'] = region_name
        
        return await self._get('/api/geotiff/list', params=params)
    
    async def get_geotiff_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a specific GeoTIFF file"""
        return await self._get(f'/api/geotiff/info', params={'file_path': file_path})
    
    async def convert_geotiff_to_png(self, file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Convert GeoTIFF to PNG format"""
        data = {'file_path': file_path}
        if output_path:
            data['output_path'] = output_path
        
        return await self._post('/api/geotiff/convert-to-png', json_data=data)
    
    async def get_geotiff_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata for a GeoTIFF file"""
        return await self._get('/api/geotiff/metadata', params={'file_path': file_path})
    
    async def crop_geotiff(self, file_path: str, bounds: Dict[str, float], output_path: Optional[str] = None) -> Dict[str, Any]:
        """Crop a GeoTIFF file to specified bounds"""
        data = {
            'file_path': file_path,
            'bounds': bounds
        }
        if output_path:
            data['output_path'] = output_path
        
        return await self._post('/api/geotiff/crop', json_data=data)
    
    async def resample_geotiff(self, file_path: str, resolution: float, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Resample a GeoTIFF file to a different resolution"""
        data = {
            'file_path': file_path,
            'resolution': resolution
        }
        if output_path:
            data['output_path'] = output_path
        
        return await self._post('/api/geotiff/resample', json_data=data)
    
    async def get_geotiff_statistics(self, file_path: str) -> Dict[str, Any]:
        """Get statistical information about a GeoTIFF file"""
        return await self._get('/api/geotiff/statistics', params={'file_path': file_path})
    
    async def convert_to_base64(self, file_path: str) -> Dict[str, Any]:
        """Convert GeoTIFF to base64 encoded PNG"""
        return await self._post('/api/geotiff/to-base64', json_data={'file_path': file_path})
