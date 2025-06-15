"""
Processing Service

Handles LIDAR processing operations including LAZ/LAS file processing,
DEM generation, and terrain analysis.
"""

from typing import Dict, Any, Optional, List
from .base_service import BaseService, SyncServiceMixin


class ProcessingService(BaseService, SyncServiceMixin):
    """Service for LIDAR processing operations"""
    
    # LAZ/LAS File Operations
    async def list_laz_files(self) -> Dict[str, Any]:
        """List all LAZ files in the input directory with metadata"""
        return await self._get('/api/list-laz-files')
    
    async def load_laz_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Load a LAZ/LAS file into the system"""
        import aiohttp
        form_data = aiohttp.FormData()
        form_data.add_field('file', file_data, filename=filename, content_type='application/octet-stream')
        
        return await self._post('/api/laz/load', form_data=form_data)
    
    async def get_laz_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a LAZ file"""
        return await self._get('/api/laz/info', params={'file_path': file_path})
    
    # DEM Processing
    async def convert_laz_to_dem(self, input_file: str) -> Dict[str, Any]:
        """Convert LAZ to DEM"""
        import aiohttp
        form_data = aiohttp.FormData()
        form_data.add_field('input_file', input_file)
        
        return await self._post('/api/laz_to_dem', form_data=form_data)
    
    async def generate_dtm(self, input_file: Optional[str] = None, region_name: Optional[str] = None, 
                          processing_type: Optional[str] = None, display_region_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate Digital Terrain Model (DTM) from LAZ data"""
        import aiohttp
        form_data = aiohttp.FormData()
        
        if input_file:
            form_data.add_field('input_file', input_file)
        if region_name:
            form_data.add_field('region_name', region_name)
        if processing_type:
            form_data.add_field('processing_type', processing_type)
        if display_region_name:
            form_data.add_field('display_region_name', display_region_name)
        
        return await self._post('/api/dtm', form_data=form_data)
    
    async def generate_dsm(self, input_file: Optional[str] = None, region_name: Optional[str] = None,
                          processing_type: Optional[str] = None, display_region_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate Digital Surface Model (DSM) from LAZ data"""
        import aiohttp
        form_data = aiohttp.FormData()
        
        if input_file:
            form_data.add_field('input_file', input_file)
        if region_name:
            form_data.add_field('region_name', region_name)
        if processing_type:
            form_data.add_field('processing_type', processing_type)
        if display_region_name:
            form_data.add_field('display_region_name', display_region_name)
        
        return await self._post('/api/dsm', form_data=form_data)
    
    async def generate_chm(self, input_file: Optional[str] = None, region_name: Optional[str] = None,
                          processing_type: Optional[str] = None, display_region_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate Canopy Height Model (CHM) from LAZ data"""
        import aiohttp
        form_data = aiohttp.FormData()
        
        if input_file:
            form_data.add_field('input_file', input_file)
        if region_name:
            form_data.add_field('region_name', region_name)
        if processing_type:
            form_data.add_field('processing_type', processing_type)
        if display_region_name:
            form_data.add_field('display_region_name', display_region_name)
        
        return await self._post('/api/chm', form_data=form_data)
    
    # Terrain Analysis
    async def generate_hillshade(self, input_file: Optional[str] = None, region_name: Optional[str] = None,
                                processing_type: Optional[str] = None, display_region_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate hillshade visualization"""
        import aiohttp
        form_data = aiohttp.FormData()
        
        if input_file:
            form_data.add_field('input_file', input_file)
        if region_name:
            form_data.add_field('region_name', region_name)
        if processing_type:
            form_data.add_field('processing_type', processing_type)
        if display_region_name:
            form_data.add_field('display_region_name', display_region_name)
        
        return await self._post('/api/hillshade', form_data=form_data)
    
    async def generate_slope(self, input_file: Optional[str] = None, region_name: Optional[str] = None,
                            processing_type: Optional[str] = None, display_region_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate slope analysis"""
        import aiohttp
        form_data = aiohttp.FormData()
        
        if input_file:
            form_data.add_field('input_file', input_file)
        if region_name:
            form_data.add_field('region_name', region_name)
        if processing_type:
            form_data.add_field('processing_type', processing_type)
        if display_region_name:
            form_data.add_field('display_region_name', display_region_name)
        
        return await self._post('/api/slope', form_data=form_data)
    
    async def generate_aspect(self, input_file: Optional[str] = None, region_name: Optional[str] = None,
                             processing_type: Optional[str] = None, display_region_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate aspect analysis"""
        import aiohttp
        form_data = aiohttp.FormData()
        
        if input_file:
            form_data.add_field('input_file', input_file)
        if region_name:
            form_data.add_field('region_name', region_name)
        if processing_type:
            form_data.add_field('processing_type', processing_type)
        if display_region_name:
            form_data.add_field('display_region_name', display_region_name)
        
        return await self._post('/api/aspect', form_data=form_data)
    
    async def generate_color_relief(self, input_file: Optional[str] = None, region_name: Optional[str] = None,
                                   processing_type: Optional[str] = None, display_region_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate color relief visualization"""
        import aiohttp
        form_data = aiohttp.FormData()
        
        if input_file:
            form_data.add_field('input_file', input_file)
        if region_name:
            form_data.add_field('region_name', region_name)
        if processing_type:
            form_data.add_field('processing_type', processing_type)
        if display_region_name:
            form_data.add_field('display_region_name', display_region_name)
        
        return await self._post('/api/color_relief', form_data=form_data)
    
    async def generate_tpi(self, input_file: Optional[str] = None, region_name: Optional[str] = None,
                          processing_type: Optional[str] = None, display_region_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate Topographic Position Index (TPI)"""
        import aiohttp
        form_data = aiohttp.FormData()
        
        if input_file:
            form_data.add_field('input_file', input_file)
        if region_name:
            form_data.add_field('region_name', region_name)
        if processing_type:
            form_data.add_field('processing_type', processing_type)
        if display_region_name:
            form_data.add_field('display_region_name', display_region_name)
        
        return await self._post('/api/tpi', form_data=form_data)
    
    async def generate_roughness(self, input_file: Optional[str] = None, region_name: Optional[str] = None,
                                processing_type: Optional[str] = None, display_region_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate terrain roughness analysis"""
        import aiohttp
        form_data = aiohttp.FormData()
        
        if input_file:
            form_data.add_field('input_file', input_file)
        if region_name:
            form_data.add_field('region_name', region_name)
        if processing_type:
            form_data.add_field('processing_type', processing_type)
        if display_region_name:
            form_data.add_field('display_region_name', display_region_name)
        
        return await self._post('/api/roughness', form_data=form_data)
    
    # Unified Raster Generation
    async def generate_all_rasters(self, region_name: str, batch_size: int = 4) -> Dict[str, Any]:
        """Generate all raster products for a region"""
        data = {
            'region_name': region_name,
            'batch_size': batch_size
        }
        return await self._post('/api/generate-rasters', json_data=data)
    
    # Processing Status and Monitoring
    async def get_processing_status(self, region_name: str) -> Dict[str, Any]:
        """Get processing status for a region"""
        return await self._get(f'/api/processing/status/{region_name}')
    
    async def cancel_processing(self, region_name: str) -> Dict[str, Any]:
        """Cancel ongoing processing for a region"""
        return await self._post(f'/api/processing/cancel/{region_name}')
    
    async def get_processing_history(self) -> Dict[str, Any]:
        """Get processing history"""
        return await self._get('/api/processing/history')
    
    # File Management
    async def delete_processed_files(self, region_name: str, file_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Delete processed files for a region"""
        data = {'region_name': region_name}
        if file_types:
            data['file_types'] = file_types
        
        return await self._delete('/api/processing/files', json_data=data)
    async def generate_sky_view_factor(self, input_file: Optional[str] = None, region_name: Optional[str] = None,
                                       processing_type: Optional[str] = None, display_region_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate Sky View Factor raster"""
        import aiohttp
        form_data = aiohttp.FormData()

        if input_file:
            form_data.add_field('input_file', input_file)
        if region_name:
            form_data.add_field('region_name', region_name)
        if processing_type:
            form_data.add_field('processing_type', processing_type)
        if display_region_name:
            form_data.add_field('display_region_name', display_region_name)

        return await self._post('/api/sky_view_factor', form_data=form_data)
