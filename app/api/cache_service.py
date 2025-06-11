"""
Cache Management Service

Provides cache management functionality for LAZ metadata and other cached data including:
- Cache statistics and monitoring
- Cache validation and cleanup
- Metadata refresh operations
- Cache performance metrics
"""

from typing import Dict, Any, List, Optional
import logging
from pathlib import Path

from .base_service import BaseService, ServiceError

logger = logging.getLogger(__name__)


class CacheService(BaseService):
    """Service for cache management operations"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics including total entries, size, and performance metrics
        
        Returns:
            Dict containing cache statistics
        """
        try:
            return await self._make_request('GET', '/metadata/stats')
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            raise ServiceError(f"Cache statistics retrieval failed: {str(e)}")
    
    async def list_cached_metadata(self) -> Dict[str, Any]:
        """
        List all cached metadata entries
        
        Returns:
            Dict containing list of cached metadata
        """
        try:
            return await self._make_request('GET', '/metadata/list')
        except Exception as e:
            logger.error(f"Failed to list cached metadata: {e}")
            raise ServiceError(f"Cache listing failed: {str(e)}")
    
    async def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a specific file from cache
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict containing file metadata
        """
        try:
            # URL encode the file path to handle special characters
            encoded_path = file_path.replace('/', '%2F').replace('\\', '%2F')
            return await self._make_request('GET', f'/metadata/{encoded_path}')
        except Exception as e:
            logger.error(f"Failed to get metadata for {file_path}: {e}")
            raise ServiceError(f"Metadata retrieval failed for {file_path}: {str(e)}")
    
    async def refresh_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Refresh metadata for a specific file
        
        Args:
            file_path: Path to the file to refresh
            
        Returns:
            Dict containing refresh operation result
        """
        try:
            # URL encode the file path to handle special characters
            encoded_path = file_path.replace('/', '%2F').replace('\\', '%2F')
            return await self._make_request('POST', f'/metadata/refresh/{encoded_path}')
        except Exception as e:
            logger.error(f"Failed to refresh metadata for {file_path}: {e}")
            raise ServiceError(f"Metadata refresh failed for {file_path}: {str(e)}")
    
    async def refresh_all_metadata(self) -> Dict[str, Any]:
        """
        Refresh all cached metadata
        
        Returns:
            Dict containing refresh operation result
        """
        try:
            return await self._make_request('POST', '/metadata/refresh-all')
        except Exception as e:
            logger.error(f"Failed to refresh all metadata: {e}")
            raise ServiceError(f"Bulk metadata refresh failed: {str(e)}")
    
    async def clear_cache(self) -> Dict[str, Any]:
        """
        Clear all cached data
        
        Returns:
            Dict containing clear operation result
        """
        try:
            return await self._make_request('DELETE', '/metadata/clear')
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise ServiceError(f"Cache clear operation failed: {str(e)}")
    
    async def validate_cache(self) -> Dict[str, Any]:
        """
        Validate cache integrity and consistency
        
        Returns:
            Dict containing validation results
        """
        try:
            return await self._make_request('GET', '/metadata/validate')
        except Exception as e:
            logger.error(f"Failed to validate cache: {e}")
            raise ServiceError(f"Cache validation failed: {str(e)}")
    
    # Convenience methods for common operations
    async def get_cache_health(self) -> Dict[str, Any]:
        """
        Get comprehensive cache health information
        
        Returns:
            Dict containing cache health metrics
        """
        try:
            stats = await self.get_cache_stats()
            validation = await self.validate_cache()
            
            return {
                "stats": stats,
                "validation": validation,
                "healthy": validation.get("valid", False),
                "timestamp": stats.get("timestamp")
            }
        except Exception as e:
            logger.error(f"Failed to get cache health: {e}")
            raise ServiceError(f"Cache health check failed: {str(e)}")
    
    async def optimize_cache(self) -> Dict[str, Any]:
        """
        Optimize cache by validating and refreshing stale entries
        
        Returns:
            Dict containing optimization results
        """
        try:
            # First validate the cache
            validation_result = await self.validate_cache()
            
            # If validation finds issues, refresh all metadata
            if not validation_result.get("valid", False):
                logger.info("Cache validation failed, refreshing all metadata")
                refresh_result = await self.refresh_all_metadata()
                
                # Validate again after refresh
                final_validation = await self.validate_cache()
                
                return {
                    "optimization_performed": True,
                    "initial_validation": validation_result,
                    "refresh_result": refresh_result,
                    "final_validation": final_validation,
                    "success": final_validation.get("valid", False)
                }
            else:
                return {
                    "optimization_performed": False,
                    "validation": validation_result,
                    "message": "Cache is already healthy, no optimization needed"
                }
                
        except Exception as e:
            logger.error(f"Failed to optimize cache: {e}")
            raise ServiceError(f"Cache optimization failed: {str(e)}")
    
    async def get_file_cache_status(self, file_path: str) -> Dict[str, Any]:
        """
        Get cache status for a specific file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict containing file cache status
        """
        try:
            metadata = await self.get_metadata(file_path)
            stats = await self.get_cache_stats()
            
            return {
                "file_path": file_path,
                "cached": metadata.get("success", False),
                "metadata": metadata,
                "cache_stats": stats
            }
        except ServiceError:
            # File might not be cached
            return {
                "file_path": file_path,
                "cached": False,
                "metadata": None,
                "cache_stats": await self.get_cache_stats()
            }
        except Exception as e:
            logger.error(f"Failed to get file cache status for {file_path}: {e}")
            raise ServiceError(f"File cache status check failed: {str(e)}")
