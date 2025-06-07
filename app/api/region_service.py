"""
Region Service

Handles region management operations including listing and deleting regions.
"""

from typing import Dict, List, Optional, Any
from .base_service import BaseService, SyncServiceMixin
import logging

logger = logging.getLogger(__name__)


class RegionService(BaseService, SyncServiceMixin):
    """Service for region management operations"""
    
    async def list_regions(self, source: Optional[str] = None) -> Dict[str, Any]:
        """
        List all available regions
        
        Args:
            source: Optional source filter for regions
            
        Returns:
            Dictionary containing list of regions with metadata
            
        Raises:
            ServiceError: If the request fails
        """
        logger.info(f"Listing regions with source filter: {source}")
        
        params = {}
        if source:
            params['source'] = source
            
        try:
            response = await self._get('/api/list-regions', params=params)
            logger.info(f"Successfully retrieved {len(response.get('regions', []))} regions")
            return response
        except Exception as e:
            logger.error(f"Failed to list regions: {e}")
            raise
    
    def list_regions_sync(self, source: Optional[str] = None) -> Dict[str, Any]:
        """Synchronous version of list_regions"""
        return self._run_async(self.list_regions(source))
    
    async def delete_region(self, region_name: str) -> Dict[str, Any]:
        """
        Delete a specific region
        
        Args:
            region_name: Name of the region to delete
            
        Returns:
            Confirmation message
            
        Raises:
            ServiceError: If the request fails
        """
        logger.info(f"Deleting region: {region_name}")
        
        if not region_name or not region_name.strip():
            raise ValueError("Region name cannot be empty")
        
        try:
            response = await self._delete(f'/api/delete-region/{region_name}')
            logger.info(f"Successfully deleted region: {region_name}")
            return response
        except Exception as e:
            logger.error(f"Failed to delete region {region_name}: {e}")
            raise
    
    def delete_region_sync(self, region_name: str) -> Dict[str, Any]:
        """Synchronous version of delete_region"""
        return self._run_async(self.delete_region(region_name))
    
    async def get_region_info(self, region_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific region
        
        Args:
            region_name: Name of the region
            
        Returns:
            Region metadata and information
        """
        logger.info(f"Getting info for region: {region_name}")
        
        try:
            # This assumes there's an endpoint for getting region info
            # If not available, this could be extracted from list_regions
            response = await self._get(f'/api/regions/{region_name}')
            return response
        except Exception as e:
            logger.warning(f"Direct region info not available, falling back to list filter")
            # Fallback: get from list_regions and filter
            regions_response = await self.list_regions()
            regions = regions_response.get('regions', [])
            
            for region in regions:
                if region.get('name') == region_name:
                    return {'region': region}
            
            raise ValueError(f"Region '{region_name}' not found")
    
    def get_region_info_sync(self, region_name: str) -> Dict[str, Any]:
        """Synchronous version of get_region_info"""
        return self._run_async(self.get_region_info(region_name))
    
    async def search_regions(self, query: str, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Search regions by name or other criteria
        
        Args:
            query: Search query string
            source: Optional source filter
            
        Returns:
            Filtered list of regions matching the query
        """
        logger.info(f"Searching regions with query: '{query}', source: {source}")
        
        # Get all regions first
        all_regions = await self.list_regions(source=source)
        regions = all_regions.get('regions', [])
        
        # Filter regions based on query
        query_lower = query.lower()
        filtered_regions = []
        
        for region in regions:
            region_name = region.get('name', '').lower()
            region_display = region.get('display_name', '').lower()
            
            if (query_lower in region_name or 
                query_lower in region_display):
                filtered_regions.append(region)
        
        logger.info(f"Found {len(filtered_regions)} regions matching query '{query}'")
        
        return {
            'regions': filtered_regions,
            'total': len(filtered_regions),
            'query': query,
            'source': source
        }
    
    def search_regions_sync(self, query: str, source: Optional[str] = None) -> Dict[str, Any]:
        """Synchronous version of search_regions"""
        return self._run_async(self.search_regions(query, source))
