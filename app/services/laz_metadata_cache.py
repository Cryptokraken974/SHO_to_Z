"""
Metadata caching system for LAZ files.

This module provides persistent caching of LAZ file metadata including coordinates,
bounds, and other spatial information to optimize region loading performance.
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import hashlib
import logging

logger = logging.getLogger(__name__)

class LAZMetadataCache:
    """Persistent cache for LAZ file metadata."""
    
    def __init__(self, cache_dir: str = "cache"):
        """Initialize the metadata cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # SQLite database for metadata storage
        self.db_path = self.cache_dir / "laz_metadata.db"
        self._init_database()
        
        # JSON fallback cache file
        self.json_cache_path = self.cache_dir / "laz_metadata_cache.json"
        
    def _init_database(self):
        """Initialize SQLite database for metadata storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS laz_metadata (
                    file_path TEXT PRIMARY KEY,
                    file_size INTEGER,
                    last_modified REAL,
                    cache_timestamp TEXT,
                    center_lat REAL,
                    center_lng REAL,
                    bounds_north REAL,
                    bounds_south REAL,
                    bounds_east REAL,
                    bounds_west REAL,
                    source_epsg INTEGER,
                    metadata_hash TEXT,
                    error_message TEXT
                )
            """)
            
            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_path ON laz_metadata(file_path)
            """)
            
            # Create index for cache validation
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_modified ON laz_metadata(last_modified)
            """)
            
            conn.commit()
    
    def _get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Get file statistics for cache validation.
        
        Args:
            file_path: Path to the LAZ file
            
        Returns:
            Dictionary with file size and modification time
        """
        try:
            full_path = Path(file_path)
            if not full_path.exists():
                # Try relative path from project root
                full_path = Path("input/LAZ") / Path(file_path).name
                if not full_path.exists():
                    return {"error": f"File not found: {file_path}"}
            
            stat = full_path.stat()
            return {
                "file_size": stat.st_size,
                "last_modified": stat.st_mtime,
                "exists": True
            }
        except Exception as e:
            logger.error(f"Error getting file stats for {file_path}: {e}")
            return {"error": str(e)}
    
    def _generate_metadata_hash(self, metadata: Dict[str, Any]) -> str:
        """Generate hash for metadata integrity verification.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            SHA256 hash of the metadata
        """
        # Create a stable string representation of the metadata
        stable_data = {
            "center_lat": metadata.get("center_lat"),
            "center_lng": metadata.get("center_lng"),
            "bounds": metadata.get("bounds"),
            "source_epsg": metadata.get("source_epsg")
        }
        
        data_str = json.dumps(stable_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def get_cached_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get cached metadata for a LAZ file.
        
        Args:
            file_path: Path to the LAZ file
            
        Returns:
            Cached metadata dictionary or None if not cached/invalid
        """
        try:
            # Get current file stats for validation
            file_stats = self._get_file_stats(file_path)
            if "error" in file_stats:
                logger.warning(f"Cannot validate cache for {file_path}: {file_stats['error']}")
                return None
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM laz_metadata WHERE file_path = ?",
                    (file_path,)
                )
                row = cursor.fetchone()
                
                if not row:
                    logger.debug(f"No cached metadata found for {file_path}")
                    return None
                
                # Validate cache freshness
                cached_size = row["file_size"]
                cached_modified = row["last_modified"]
                current_size = file_stats["file_size"]
                current_modified = file_stats["last_modified"]
                
                if cached_size != current_size or abs(cached_modified - current_modified) > 1:
                    logger.info(f"Cache invalid for {file_path} (file modified)")
                    self._invalidate_cache_entry(file_path)
                    return None
                
                # Build metadata dict from row
                metadata = {
                    "center": {
                        "lat": row["center_lat"],
                        "lng": row["center_lng"]
                    },
                    "bounds": {
                        "north": row["bounds_north"],
                        "south": row["bounds_south"],
                        "east": row["bounds_east"],
                        "west": row["bounds_west"]
                    },
                    "source_epsg": row["source_epsg"],
                    "cache_timestamp": row["cache_timestamp"],
                    "file_path": row["file_path"]
                }
                
                # Check for error state
                if row["error_message"]:
                    metadata["error"] = row["error_message"]
                
                logger.debug(f"Retrieved cached metadata for {file_path}")
                return metadata
                
        except Exception as e:
            logger.error(f"Error retrieving cached metadata for {file_path}: {e}")
            return None
    
    def cache_metadata(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """Cache metadata for a LAZ file.
        
        Args:
            file_path: Path to the LAZ file
            metadata: Metadata to cache
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            # Get file stats
            file_stats = self._get_file_stats(file_path)
            if "error" in file_stats:
                logger.error(f"Cannot cache metadata for {file_path}: {file_stats['error']}")
                return False
            
            # Generate metadata hash
            metadata_hash = self._generate_metadata_hash(metadata)
            
            # Extract values with defaults
            center = metadata.get("center", {})
            bounds = metadata.get("bounds", {})
            error_message = metadata.get("error")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO laz_metadata (
                        file_path, file_size, last_modified, cache_timestamp,
                        center_lat, center_lng, bounds_north, bounds_south,
                        bounds_east, bounds_west, source_epsg, metadata_hash,
                        error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_path,
                    file_stats["file_size"],
                    file_stats["last_modified"],
                    datetime.now(timezone.utc).isoformat(),
                    center.get("lat"),
                    center.get("lng"),
                    bounds.get("north"),
                    bounds.get("south"),
                    bounds.get("east"),
                    bounds.get("west"),
                    metadata.get("source_epsg"),
                    metadata_hash,
                    error_message
                ))
                conn.commit()
            
            logger.info(f"Cached metadata for {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching metadata for {file_path}: {e}")
            return False
    
    def _invalidate_cache_entry(self, file_path: str):
        """Remove cache entry for a specific file.
        
        Args:
            file_path: Path to the LAZ file
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM laz_metadata WHERE file_path = ?", (file_path,))
                conn.commit()
            logger.debug(f"Invalidated cache entry for {file_path}")
        except Exception as e:
            logger.error(f"Error invalidating cache for {file_path}: {e}")
    
    def clear_cache(self) -> bool:
        """Clear all cached metadata.
        
        Returns:
            True if successfully cleared, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM laz_metadata")
                conn.commit()
            
            # Also remove JSON fallback cache if it exists
            if self.json_cache_path.exists():
                self.json_cache_path.unlink()
            
            logger.info("Cleared all cached metadata")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) as total FROM laz_metadata")
                total = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) as errors FROM laz_metadata WHERE error_message IS NOT NULL")
                errors = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT MIN(cache_timestamp) as oldest, MAX(cache_timestamp) as newest 
                    FROM laz_metadata
                """)
                row = cursor.fetchone()
                oldest = row[0]
                newest = row[1]
            
            return {
                "total_entries": total,
                "error_entries": errors,
                "valid_entries": total - errors,
                "oldest_entry": oldest,
                "newest_entry": newest,
                "cache_file_size_mb": round(self.db_path.stat().st_size / (1024 * 1024), 2) if self.db_path.exists() else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    def refresh_cache_for_file(self, file_path: str) -> bool:
        """Force refresh cache for a specific file.
        
        Args:
            file_path: Path to the LAZ file
            
        Returns:
            True if successfully refreshed, False otherwise
        """
        # Invalidate existing cache
        self._invalidate_cache_entry(file_path)
        
        # The actual coordinate fetching will be handled by the existing LAZ coordinate system
        # This method just ensures the cache is ready for new data
        logger.info(f"Prepared cache refresh for {file_path}")
        return True
    
    def list_cached_files(self) -> List[Dict[str, Any]]:
        """List all files in the cache.
        
        Returns:
            List of cached file information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT file_path, cache_timestamp, center_lat, center_lng,
                           error_message, file_size, last_modified
                    FROM laz_metadata
                    ORDER BY cache_timestamp DESC
                """)
                
                files = []
                for row in cursor.fetchall():
                    files.append({
                        "file_path": row["file_path"],
                        "cache_timestamp": row["cache_timestamp"],
                        "center_lat": row["center_lat"],
                        "center_lng": row["center_lng"],
                        "has_error": bool(row["error_message"]),
                        "error_message": row["error_message"],
                        "file_size_mb": round(row["file_size"] / (1024 * 1024), 2) if row["file_size"] else 0,
                        "last_modified": datetime.fromtimestamp(row["last_modified"]).isoformat() if row["last_modified"] else None
                    })
                
                return files
                
        except Exception as e:
            logger.error(f"Error listing cached files: {e}")
            return []

# Global cache instance
_cache_instance = None

def get_metadata_cache() -> LAZMetadataCache:
    """Get the global metadata cache instance.
    
    Returns:
        LAZMetadataCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LAZMetadataCache()
    return _cache_instance
