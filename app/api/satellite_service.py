"""
Satellite Service

Handles satellite data operations including Sentinel-2 data acquisition and processing.
"""

from typing import Dict, Any, Optional, List
from .base_service import BaseService, SyncServiceMixin


class SatelliteService(BaseService, SyncServiceMixin):
    """Service for satellite data operations"""
    
    async def download_sentinel2_data(self,
                                     start_date: str,
                                     end_date: str,
                                     latitude: Optional[float] = None, # Made optional
                                     longitude: Optional[float] = None, # Made optional
                                     bounding_box: Optional[Dict[str, float]] = None, # New parameter
                                     bands: Optional[List[str]] = None,
                                     cloud_cover_max: Optional[float] = None,
                                     region_name: Optional[str] = None) -> Dict[str, Any]:
        """Download Sentinel-2 data for specified coordinates/bounding box and date range"""
        data = {
            'start_date': start_date,
            'end_date': end_date
        }

        if bounding_box and \
           all(k in bounding_box for k in ["north", "south", "east", "west"])):
            data['north_bound'] = bounding_box.get("north")
            data['south_bound'] = bounding_box.get("south")
            data['east_bound'] = bounding_box.get("east")
            data['west_bound'] = bounding_box.get("west")
        elif latitude is not None and longitude is not None:
            data['latitude'] = latitude
            data['longitude'] = longitude
            # If buffer_km was also part of the Pydantic model and meant to be passed,
            # it would be added here. Assuming for now it's handled by the endpoint's default
            # if not part of an explicit bounding_box.
        else:
            # This service method now requires either bbox or lat/lng.
            # The endpoint has primary responsibility for validation,
            # but this service method could also raise an error.
            # For now, assume the endpoint ensures one is passed.
            # Consider raising ValueError here if neither is provided.
            pass # Or raise ValueError("Either bounding_box or latitude/longitude must be provided to SatelliteService.download_sentinel2_data")

        if bands:
            data['bands'] = bands
        if cloud_cover_max is not None:
            data['cloud_cover_max'] = cloud_cover_max
        if region_name is not None:
            data['region_name'] = region_name
        
        # Assuming buffer_km is still part of the Sentinel2Request model on the endpoint
        # and if not using explicit bounds, the endpoint calculates bbox using lat, lng, buffer_km.
        # If buffer_km needs to be passed explicitly when lat/lng are used, add it here.
        # For example, if the endpoint's Sentinel2Request still has buffer_km and it's not used to construct explicit bounds,
        # it might be passed if lat/long are used:
        # if 'latitude' in data and 'buffer_km_from_original_request_if_any' in original_params:
        #    data['buffer_km'] = original_params['buffer_km_from_original_request_if_any']


        return await self._post('/api/download-sentinel2', json_data=data)
    
    async def convert_sentinel2_images(self, region_name: str) -> Dict[str, Any]:
        """Convert downloaded Sentinel-2 TIF files to PNG for display"""
        import aiohttp
        form_data = aiohttp.FormData()
        form_data.add_field('region_name', region_name)
        
        return await self._post('/api/convert-sentinel2', form_data=form_data)
    
    async def get_sentinel2_metadata(self, region_name: str) -> Dict[str, Any]:
        """Get metadata for Sentinel-2 data in a region"""
        return await self._get(f'/api/sentinel2/metadata/{region_name}')
    
    async def list_sentinel2_scenes(self, region_name: Optional[str] = None) -> Dict[str, Any]:
        """List available Sentinel-2 scenes"""
        params = {}
        if region_name:
            params['region_name'] = region_name
        
        return await self._get('/api/sentinel2/scenes', params=params)
    
    async def search_sentinel2_scenes(self, latitude: float, longitude: float, start_date: str,
                                     end_date: str, cloud_cover_max: Optional[float] = None) -> Dict[str, Any]:
        """Search for Sentinel-2 scenes matching criteria"""
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': start_date,
            'end_date': end_date
        }
        
        if cloud_cover_max is not None:
            params['cloud_cover_max'] = cloud_cover_max
        
        return await self._get('/api/sentinel2/search', params=params)
    
    async def download_sentinel2_scene(self, scene_id: str, bands: Optional[List[str]] = None) -> Dict[str, Any]:
        """Download a specific Sentinel-2 scene"""
        data = {'scene_id': scene_id}
        if bands:
            data['bands'] = bands
        
        return await self._post('/api/sentinel2/download-scene', json_data=data)
    
    async def process_sentinel2_bands(self, region_name: str, processing_type: str = 'ndvi') -> Dict[str, Any]:
        """Process Sentinel-2 bands for vegetation indices or other analysis"""
        data = {
            'region_name': region_name,
            'processing_type': processing_type
        }
        return await self._post('/api/sentinel2/process-bands', json_data=data)
    
    async def calculate_ndvi(self, region_name: str, red_band_path: str, nir_band_path: str) -> Dict[str, Any]:
        """Calculate NDVI from red and NIR bands"""
        data = {
            'region_name': region_name,
            'red_band_path': red_band_path,
            'nir_band_path': nir_band_path
        }
        return await self._post('/api/sentinel2/calculate-ndvi', json_data=data)
    
    async def calculate_ndwi(self, region_name: str, green_band_path: str, nir_band_path: str) -> Dict[str, Any]:
        """Calculate NDWI (Normalized Difference Water Index)"""
        data = {
            'region_name': region_name,
            'green_band_path': green_band_path,
            'nir_band_path': nir_band_path
        }
        return await self._post('/api/sentinel2/calculate-ndwi', json_data=data)
    
    async def create_rgb_composite(self, region_name: str, red_band: str, green_band: str, blue_band: str) -> Dict[str, Any]:
        """Create RGB composite from Sentinel-2 bands"""
        data = {
            'region_name': region_name,
            'red_band': red_band,
            'green_band': green_band,
            'blue_band': blue_band
        }
        return await self._post('/api/sentinel2/rgb-composite', json_data=data)
    
    async def get_satellite_coverage(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get satellite coverage information for coordinates"""
        params = {
            'latitude': latitude,
            'longitude': longitude
        }
        return await self._get('/api/satellite/coverage', params=params)
    
    async def get_acquisition_schedule(self, latitude: float, longitude: float, days_ahead: int = 30) -> Dict[str, Any]:
        """Get upcoming satellite acquisition schedule for coordinates"""
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'days_ahead': days_ahead
        }
        return await self._get('/api/satellite/schedule', params=params)
    
    async def delete_satellite_data(self, region_name: str, data_type: Optional[str] = None) -> Dict[str, Any]:
        """Delete satellite data for a region"""
        data = {'region_name': region_name}
        if data_type:
            data['data_type'] = data_type
        
        return await self._delete('/api/satellite/data', json_data=data)
    
    async def get_satellite_statistics(self, region_name: str) -> Dict[str, Any]:
        """Get statistics for satellite data in a region"""
        return await self._get(f'/api/satellite/statistics/{region_name}')
    
    async def export_satellite_data(self, region_name: str, format: str = 'geotiff') -> Dict[str, Any]:
        """Export satellite data in specified format"""
        params = {'format': format}
        return await self._get(f'/api/satellite/export/{region_name}', params=params)
    
    async def apply_atmospheric_correction(self, scene_id: str, method: str = 'sen2cor') -> Dict[str, Any]:
        """Apply atmospheric correction to Sentinel-2 data"""
        data = {
            'scene_id': scene_id,
            'method': method
        }
        return await self._post('/api/sentinel2/atmospheric-correction', json_data=data)
    
    async def mask_clouds(self, scene_id: str, threshold: float = 0.3) -> Dict[str, Any]:
        """Apply cloud masking to Sentinel-2 data"""
        data = {
            'scene_id': scene_id,
            'threshold': threshold
        }
        return await self._post('/api/sentinel2/cloud-mask', json_data=data)
