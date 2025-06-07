"""
Cache management endpoints for LAZ metadata caching system.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
from ..services.laz_metadata_cache import get_metadata_cache
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cache", tags=["cache"])

@router.get("/metadata/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get statistics about the LAZ metadata cache.
    
    Returns:
        Dictionary with cache statistics including entry counts and file sizes
    """
    try:
        cache = get_metadata_cache()
        stats = cache.get_cache_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.get("/metadata/list")
async def list_cached_files() -> Dict[str, Any]:
    """List all files in the metadata cache.
    
    Returns:
        List of cached file information with metadata
    """
    try:
        cache = get_metadata_cache()
        files = cache.list_cached_files()
        
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
        
    except Exception as e:
        logger.error(f"Error listing cached files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list cached files: {str(e)}")

@router.get("/metadata/{file_path:path}")
async def get_cached_metadata(file_path: str) -> Dict[str, Any]:
    """Get cached metadata for a specific LAZ file.
    
    Args:
        file_path: Path to the LAZ file
        
    Returns:
        Cached metadata if available, or indication that cache miss occurred
    """
    try:
        cache = get_metadata_cache()
        metadata = cache.get_cached_metadata(file_path)
        
        if metadata is None:
            return {
                "success": False,
                "cached": False,
                "message": "No cached metadata found for this file"
            }
        
        return {
            "success": True,
            "cached": True,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Error getting cached metadata for {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cached metadata: {str(e)}")

@router.post("/metadata/refresh/{file_path:path}")
async def refresh_file_cache(file_path: str) -> Dict[str, Any]:
    """Force refresh cache for a specific LAZ file.
    
    Args:
        file_path: Path to the LAZ file
        
    Returns:
        Success status of cache refresh operation
    """
    try:
        cache = get_metadata_cache()
        success = cache.refresh_cache_for_file(file_path)
        
        if success:
            return {
                "success": True,
                "message": f"Cache refreshed for {file_path}. New metadata will be fetched on next access."
            }
        else:
            return {
                "success": False,
                "message": f"Failed to refresh cache for {file_path}"
            }
        
    except Exception as e:
        logger.error(f"Error refreshing cache for {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh cache: {str(e)}")

@router.post("/metadata/refresh-all")
async def refresh_all_cache() -> Dict[str, Any]:
    """Force refresh cache for all LAZ files.
    
    Returns:
        Success status of global cache refresh operation
    """
    try:
        cache = get_metadata_cache()
        success = cache.clear_cache()
        
        if success:
            return {
                "success": True,
                "message": "All cache entries cleared. New metadata will be fetched on next access."
            }
        else:
            return {
                "success": False,
                "message": "Failed to clear cache"
            }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.delete("/metadata/clear")
async def clear_cache() -> Dict[str, Any]:
    """Clear all cached metadata.
    
    Returns:
        Success status of cache clearing operation
    """
    try:
        cache = get_metadata_cache()
        success = cache.clear_cache()
        
        if success:
            return {
                "success": True,
                "message": "Cache cleared successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to clear cache"
            }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/metadata/validate")
async def validate_cache(
    file_path: Optional[str] = Query(None, description="Specific file to validate, or all files if not provided")
) -> Dict[str, Any]:
    """Validate cache entries against current file states.
    
    Args:
        file_path: Optional specific file to validate
        
    Returns:
        Validation results showing which cache entries are valid/invalid
    """
    try:
        cache = get_metadata_cache()
        
        if file_path:
            # Validate specific file
            metadata = cache.get_cached_metadata(file_path)
            if metadata is None:
                return {
                    "success": True,
                    "file_path": file_path,
                    "valid": False,
                    "message": "No cache entry found"
                }
            else:
                return {
                    "success": True,
                    "file_path": file_path,
                    "valid": True,
                    "metadata": metadata
                }
        else:
            # Validate all files
            all_files = cache.list_cached_files()
            validation_results = []
            
            for file_info in all_files:
                file_path = file_info["file_path"]
                metadata = cache.get_cached_metadata(file_path)
                validation_results.append({
                    "file_path": file_path,
                    "valid": metadata is not None,
                    "has_error": file_info.get("has_error", False),
                    "cache_timestamp": file_info.get("cache_timestamp")
                })
            
            valid_count = sum(1 for r in validation_results if r["valid"])
            total_count = len(validation_results)
            
            return {
                "success": True,
                "total_files": total_count,
                "valid_files": valid_count,
                "invalid_files": total_count - valid_count,
                "validation_results": validation_results
            }
        
    except Exception as e:
        logger.error(f"Error validating cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate cache: {str(e)}")
