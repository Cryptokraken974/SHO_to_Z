"""
Elevation Service

Handles elevation data operations including optimal elevation data acquisition,
terrain analysis, and elevation model processing.
"""

from typing import Dict, Any, Optional, List
from .base_service import BaseService, SyncServiceMixin


class ElevationService(BaseService, SyncServiceMixin):
    """Service for elevation data operations"""
    
    async def get_elevation_status(self) -> Dict[str, Any]:
        """Get status of optimal elevation system with quality findings"""
        return await self._get('/api/elevation/status')
    
    async def get_elevation_datasets(self) -> Dict[str, Any]:
        """Get information about available elevation datasets with quality rankings"""
        return await self._get('/api/elevation/datasets')
    
    async def get_terrain_recommendations(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get terrain-based dataset recommendations for coordinates"""
        params = {
            'latitude': latitude,
            'longitude': longitude
        }
        return await self._get('/api/elevation/terrain-recommendations', params=params)
    
    async def get_optimal_elevation_data(self, latitude: float, longitude: float, area_km: float = 25.0) -> Dict[str, Any]:
        """Get optimal elevation data using integrated quality findings"""
        data = {
            'latitude': latitude,
            'longitude': longitude,
            'area_km': area_km
        }
        return await self._post('/api/elevation/optimal', json_data=data)
    
    async def get_brazilian_elevation_data(self, latitude: float, longitude: float, area_km: float = 25.0) -> Dict[str, Any]:
        """Get optimal elevation specifically for Brazilian regions"""
        data = {
            'latitude': latitude,
            'longitude': longitude,
            'area_km': area_km
        }
        return await self._post('/api/elevation/brazilian', json_data=data)
    
    async def download_elevation_data(self, latitude: float, longitude: float, area_km: float = 25.0) -> Dict[str, Any]:
        """Download optimal elevation data using the integrated API"""
        data = {
            'latitude': latitude,
            'longitude': longitude,
            'area_km': area_km
        }
        return await self._post('/api/elevation/download', json_data=data)
    
    async def download_all_elevation_data(self) -> Dict[str, Any]:
        """Download optimal elevation data for multiple Brazilian regions"""
        return await self._post('/api/elevation/download-all')
    
    async def acquire_elevation_data(self, latitude: float, longitude: float, area_km: float = 25.0, 
                                   source: Optional[str] = None) -> Dict[str, Any]:
        """Acquire elevation data from specified or optimal source"""
        data = {
            'latitude': latitude,
            'longitude': longitude,
            'area_km': area_km
        }
        if source:
            data['source'] = source
        
        return await self._post('/api/acquire-data', json_data=data)
    
    async def check_elevation_availability(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Check what elevation data is available for given coordinates"""
        data = {
            'latitude': latitude,
            'longitude': longitude
        }
        return await self._post('/api/check-data-availability', json_data=data)
    
    async def estimate_download_size(self, latitude: float, longitude: float, area_km: float = 25.0) -> Dict[str, Any]:
        """Estimate download size for elevation data"""
        data = {
            'latitude': latitude,
            'longitude': longitude,
            'area_km': area_km
        }
        return await self._post('/api/estimate-download-size', json_data=data)
    
    async def get_elevation_profile(self, start_lat: float, start_lng: float, end_lat: float, end_lng: float, 
                                   num_points: int = 100) -> Dict[str, Any]:
        """Get elevation profile along a line"""
        data = {
            'start_lat': start_lat,
            'start_lng': start_lng,
            'end_lat': end_lat,
            'end_lng': end_lng,
            'num_points': num_points
        }
        return await self._post('/api/elevation/profile', json_data=data)
    
    async def get_elevation_at_point(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get elevation value at a specific point"""
        params = {
            'latitude': latitude,
            'longitude': longitude
        }
        return await self._get('/api/elevation/point', params=params)
    
    async def create_elevation_contours(self, region_name: str, interval: float = 10.0) -> Dict[str, Any]:
        """Create elevation contour lines"""
        data = {
            'region_name': region_name,
            'interval': interval
        }
        return await self._post('/api/elevation/contours', json_data=data)
    
    async def calculate_viewshed(self, observer_lat: float, observer_lng: float, observer_height: float = 1.7,
                                target_height: float = 0.0, max_distance: float = 10.0) -> Dict[str, Any]:
        """Calculate viewshed analysis"""
        data = {
            'observer_lat': observer_lat,
            'observer_lng': observer_lng,
            'observer_height': observer_height,
            'target_height': target_height,
            'max_distance': max_distance
        }
        return await self._post('/api/elevation/viewshed', json_data=data)
    
    async def calculate_watershed(self, pour_point_lat: float, pour_point_lng: float) -> Dict[str, Any]:
        """Calculate watershed delineation"""
        data = {
            'pour_point_lat': pour_point_lat,
            'pour_point_lng': pour_point_lng
        }
        return await self._post('/api/elevation/watershed', json_data=data)
    
    async def get_elevation_statistics(self, region_name: str) -> Dict[str, Any]:
        """Get elevation statistics for a region"""
        return await self._get(f'/api/elevation/statistics/{region_name}')
    
    async def compare_elevation_sources(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Compare elevation data quality from different sources"""
        data = {
            'latitude': latitude,
            'longitude': longitude
        }
        return await self._post('/api/elevation/compare-sources', json_data=data)
    
    async def get_acquisition_history(self) -> Dict[str, Any]:
        """Get history of elevation data acquisitions"""
        return await self._get('/api/acquisition-history')
    
    async def cleanup_elevation_cache(self, older_than_days: int = 30) -> Dict[str, Any]:
        """Clean up elevation cache older than specified days"""
        return await self._post('/api/cleanup-cache', json_data={'older_than_days': older_than_days})
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get elevation data storage statistics"""
        return await self._get('/api/storage-stats')
    
    async def resample_elevation_data(self, region_name: str, target_resolution: float) -> Dict[str, Any]:
        """Resample elevation data to target resolution"""
        data = {
            'region_name': region_name,
            'target_resolution': target_resolution
        }
        return await self._post('/api/elevation/resample', json_data=data)
