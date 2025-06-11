"""
Data Acquisition Service

Provides data acquisition workflow functionality including:
- Configuration management
- Data availability checking
- Acquisition operations
- Download size estimation
- Acquisition history tracking
- Storage statistics and cleanup
"""

from typing import Dict, Any, List, Optional, Union
import logging
from pathlib import Path

from .base_service import BaseService, ServiceError

logger = logging.getLogger(__name__)


class DataAcquisitionService(BaseService):
    """Service for data acquisition workflow operations"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        
    async def get_config(self) -> Dict[str, Any]:
        """
        Get data acquisition configuration
        
        Returns:
            Dict containing acquisition configuration
        """
        try:
            return await self._make_request('GET', '/api/config')
        except Exception as e:
            logger.error(f"Failed to get acquisition config: {e}")
            raise ServiceError(f"Configuration retrieval failed: {str(e)}")
    
    async def check_data_availability(
        self, 
        location: Dict[str, Any], 
        data_types: List[str],
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Check data availability for given location and criteria
        
        Args:
            location: Geographic location (lat, lon, bounds)
            data_types: List of data types to check (elevation, lidar, satellite)
            date_range: Optional date range for temporal data
            
        Returns:
            Dict containing availability information
        """
        try:
            payload = {
                "location": location,
                "data_types": data_types
            }
            if date_range:
                payload["date_range"] = date_range
                
            return await self._make_request('POST', '/api/check-data-availability', json_data=payload)
        except Exception as e:
            logger.error(f"Failed to check data availability: {e}")
            raise ServiceError(f"Data availability check failed: {str(e)}")
    
    async def acquire_data(
        self,
        location: Dict[str, Any],
        data_types: List[str],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Acquire data for given location and types
        
        Args:
            location: Geographic location (lat, lon, bounds)
            data_types: List of data types to acquire
            parameters: Optional acquisition parameters
            
        Returns:
            Dict containing acquisition results
        """
        try:
            payload = {
                "location": location,
                "data_types": data_types
            }
            if parameters:
                payload["parameters"] = parameters
                
            return await self._make_request('POST', '/api/acquire-data', json_data=payload)
        except Exception as e:
            logger.error(f"Failed to acquire data: {e}")
            raise ServiceError(f"Data acquisition failed: {str(e)}")
    
    async def estimate_download_size(
        self,
        location: Dict[str, Any],
        data_types: List[str],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimate download size for data acquisition
        
        Args:
            location: Geographic location
            data_types: List of data types
            parameters: Optional parameters affecting size
            
        Returns:
            Dict containing size estimates
        """
        try:
            payload = {
                "location": location,
                "data_types": data_types
            }
            if parameters:
                payload["parameters"] = parameters
                
            return await self._make_request('POST', '/api/estimate-download-size', json_data=payload)
        except Exception as e:
            logger.error(f"Failed to estimate download size: {e}")
            raise ServiceError(f"Download size estimation failed: {str(e)}")
    
    async def get_acquisition_history(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        data_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get acquisition history
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            data_type: Filter by data type
            
        Returns:
            Dict containing acquisition history
        """
        try:
            params = {}
            if limit is not None:
                params['limit'] = limit
            if offset is not None:
                params['offset'] = offset
            if data_type:
                params['data_type'] = data_type
                
            return await self._make_request('GET', '/api/acquisition-history', params=params)
        except Exception as e:
            logger.error(f"Failed to get acquisition history: {e}")
            raise ServiceError(f"Acquisition history retrieval failed: {str(e)}")
    
    async def cleanup_cache(
        self,
        older_than_days: Optional[int] = None,
        data_type: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Clean up cached acquisition data
        
        Args:
            older_than_days: Remove data older than specified days
            data_type: Clean up specific data type only
            dry_run: If True, only report what would be cleaned
            
        Returns:
            Dict containing cleanup results
        """
        try:
            payload = {
                "dry_run": dry_run
            }
            if older_than_days is not None:
                payload["older_than_days"] = older_than_days
            if data_type:
                payload["data_type"] = data_type
                
            return await self._make_request('POST', '/api/cleanup-cache', json_data=payload)
        except Exception as e:
            logger.error(f"Failed to cleanup cache: {e}")
            raise ServiceError(f"Cache cleanup failed: {str(e)}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for acquired data
        
        Returns:
            Dict containing storage statistics
        """
        try:
            return await self._make_request('GET', '/api/storage-stats')
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            raise ServiceError(f"Storage statistics retrieval failed: {str(e)}")
    
    # Convenience methods for common workflows
    async def get_full_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status including config, storage, and history
        
        Returns:
            Dict containing full system status
        """
        try:
            config = await self.get_config()
            storage_stats = await self.get_storage_stats()
            recent_history = await self.get_acquisition_history(limit=10)
            
            return {
                "config": config,
                "storage": storage_stats,
                "recent_acquisitions": recent_history,
                "timestamp": storage_stats.get("timestamp")
            }
        except Exception as e:
            logger.error(f"Failed to get full system status: {e}")
            raise ServiceError(f"System status retrieval failed: {str(e)}")
    
    async def plan_acquisition(
        self,
        location: Dict[str, Any],
        data_types: List[str],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Plan data acquisition by checking availability and estimating size
        
        Args:
            location: Geographic location
            data_types: List of data types to acquire
            parameters: Optional acquisition parameters
            
        Returns:
            Dict containing acquisition plan
        """
        try:
            # Check availability
            availability = await self.check_data_availability(location, data_types)
            
            # Estimate size for available data
            size_estimate = await self.estimate_download_size(location, data_types, parameters)
            
            # Get current storage stats for capacity planning
            storage_stats = await self.get_storage_stats()
            
            return {
                "location": location,
                "data_types": data_types,
                "parameters": parameters,
                "availability": availability,
                "size_estimate": size_estimate,
                "storage_stats": storage_stats,
                "feasible": self._assess_feasibility(size_estimate, storage_stats)
            }
        except Exception as e:
            logger.error(f"Failed to plan acquisition: {e}")
            raise ServiceError(f"Acquisition planning failed: {str(e)}")
    
    async def execute_planned_acquisition(
        self,
        location: Dict[str, Any],
        data_types: List[str],
        parameters: Optional[Dict[str, Any]] = None,
        auto_cleanup: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a complete acquisition workflow
        
        Args:
            location: Geographic location
            data_types: List of data types to acquire
            parameters: Optional acquisition parameters
            auto_cleanup: If True, cleanup old data before acquisition
            
        Returns:
            Dict containing acquisition results
        """
        try:
            # Optional cleanup
            if auto_cleanup:
                cleanup_result = await self.cleanup_cache(older_than_days=30)
                logger.info(f"Pre-acquisition cleanup: {cleanup_result}")
            
            # Plan the acquisition
            plan = await self.plan_acquisition(location, data_types, parameters)
            
            if not plan.get("feasible", False):
                return {
                    "success": False,
                    "message": "Acquisition not feasible",
                    "plan": plan
                }
            
            # Execute the acquisition
            result = await self.acquire_data(location, data_types, parameters)
            
            # Get updated storage stats
            final_storage = await self.get_storage_stats()
            
            return {
                "success": result.get("success", False),
                "plan": plan,
                "acquisition_result": result,
                "final_storage": final_storage,
                "cleanup_performed": auto_cleanup
            }
            
        except Exception as e:
            logger.error(f"Failed to execute planned acquisition: {e}")
            raise ServiceError(f"Planned acquisition execution failed: {str(e)}")
    
    def _assess_feasibility(
        self, 
        size_estimate: Dict[str, Any], 
        storage_stats: Dict[str, Any]
    ) -> bool:
        """
        Assess if acquisition is feasible based on size and storage
        
        Args:
            size_estimate: Size estimation result
            storage_stats: Current storage statistics
            
        Returns:
            True if acquisition appears feasible
        """
        try:
            estimated_mb = size_estimate.get("total_size_mb", 0)
            available_mb = storage_stats.get("available_space_mb", 0)
            
            # Require at least 20% buffer
            required_mb = estimated_mb * 1.2
            
            return available_mb >= required_mb
        except:
            # If we can't assess, assume feasible and let the acquisition handle it
            return True
