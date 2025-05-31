"""
Caching utilities for data acquisition
"""

import os
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class DataCache:
    """Handles caching of downloaded and processed data"""
    
    def __init__(self, cache_dir: str):
        """
        Initialize the cache
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        self.metadata_file = os.path.join(cache_dir, "cache_metadata.json")
        
        # Note: Cache directory will be created only when actually needed
        
        # Load existing metadata
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
        
        return {
            "entries": {},
            "created": datetime.now().isoformat(),
            "last_cleanup": datetime.now().isoformat()
        }
    
    def _save_metadata(self):
        """Save cache metadata to file"""
        try:
            # Create cache directory only when actually saving metadata
            os.makedirs(self.cache_dir, exist_ok=True)
            
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _generate_cache_key_hash(self, cache_key: str) -> str:
        """Generate a hash for the cache key to use as filename"""
        return hashlib.md5(cache_key.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from cache
        
        Args:
            cache_key: Unique key for the cached data
            
        Returns:
            Cached data if found and valid, None otherwise
        """
        key_hash = self._generate_cache_key_hash(cache_key)
        
        # Check if entry exists in metadata
        if key_hash not in self.metadata["entries"]:
            return None
        
        entry = self.metadata["entries"][key_hash]
        
        # Check if entry has expired (24 hours by default)
        created_time = datetime.fromisoformat(entry["created"])
        if datetime.now() - created_time > timedelta(hours=24):
            logger.info(f"Cache entry expired for key: {cache_key}")
            self.invalidate(cache_key)
            return None
        
        # Load cached data
        cache_file = os.path.join(self.cache_dir, f"{key_hash}.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                
                # Update access time
                entry["last_accessed"] = datetime.now().isoformat()
                self._save_metadata()
                
                logger.info(f"Cache hit for key: {cache_key}")
                return data
                
            except Exception as e:
                logger.error(f"Failed to load cached data for {cache_key}: {e}")
                self.invalidate(cache_key)
        
        return None
    
    def store(self, cache_key: str, data: Dict[str, Any], 
              metadata: Optional[Dict[str, Any]] = None):
        """
        Store data in cache (alias for put method)
        
        Args:
            cache_key: Unique key for the data
            data: Data to cache
            metadata: Optional metadata about the cached data
        """
        return self.put(cache_key, data, metadata)
    
    def put(self, cache_key: str, data: Dict[str, Any], 
            metadata: Optional[Dict[str, Any]] = None):
        """
        Store data in cache
        
        Args:
            cache_key: Unique key for the data
            data: Data to cache
            metadata: Optional metadata about the cached data
        """
        key_hash = self._generate_cache_key_hash(cache_key)
        cache_file = os.path.join(self.cache_dir, f"{key_hash}.pkl")
        
        try:
            # Create cache directory only when actually storing data
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Save data to pickle file
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Update metadata
            self.metadata["entries"][key_hash] = {
                "original_key": cache_key,
                "created": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "file_size": os.path.getsize(cache_file),
                "metadata": metadata or {}
            }
            
            self._save_metadata()
            logger.info(f"Data cached for key: {cache_key}")
            
        except Exception as e:
            logger.error(f"Failed to cache data for {cache_key}: {e}")
            # Clean up partial file
            if os.path.exists(cache_file):
                os.remove(cache_file)
    
    def invalidate(self, cache_key: str):
        """
        Remove data from cache
        
        Args:
            cache_key: Key of data to remove
        """
        key_hash = self._generate_cache_key_hash(cache_key)
        
        # Remove from metadata
        if key_hash in self.metadata["entries"]:
            del self.metadata["entries"][key_hash]
            self._save_metadata()
        
        # Remove cache file
        cache_file = os.path.join(self.cache_dir, f"{key_hash}.pkl")
        if os.path.exists(cache_file):
            os.remove(cache_file)
        
        logger.info(f"Cache invalidated for key: {cache_key}")
    
    def cleanup(self, older_than_days: int = 30):
        """
        Clean up old cache entries
        
        Args:
            older_than_days: Remove entries older than this many days
        """
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        keys_to_remove = []
        
        for key_hash, entry in self.metadata["entries"].items():
            created_time = datetime.fromisoformat(entry["created"])
            if created_time < cutoff_date:
                keys_to_remove.append(key_hash)
        
        # Remove old entries
        for key_hash in keys_to_remove:
            cache_file = os.path.join(self.cache_dir, f"{key_hash}.pkl")
            if os.path.exists(cache_file):
                os.remove(cache_file)
            del self.metadata["entries"][key_hash]
        
        # Update cleanup timestamp
        self.metadata["last_cleanup"] = datetime.now().isoformat()
        self._save_metadata()
        
        logger.info(f"Cache cleanup completed. Removed {len(keys_to_remove)} entries.")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        total_entries = len(self.metadata["entries"])
        total_size = sum(entry.get("file_size", 0) for entry in self.metadata["entries"].values())
        
        # Calculate age distribution
        now = datetime.now()
        age_buckets = {"<1h": 0, "1h-1d": 0, "1d-7d": 0, ">7d": 0}
        
        for entry in self.metadata["entries"].values():
            created_time = datetime.fromisoformat(entry["created"])
            age = now - created_time
            
            if age < timedelta(hours=1):
                age_buckets["<1h"] += 1
            elif age < timedelta(days=1):
                age_buckets["1h-1d"] += 1
            elif age < timedelta(days=7):
                age_buckets["1d-7d"] += 1
            else:
                age_buckets[">7d"] += 1
        
        return {
            "total_entries": total_entries,
            "total_items": total_entries,  # Alias for compatibility
            "total_size_mb": total_size / (1024 * 1024),
            "age_distribution": age_buckets,
            "cache_dir": self.cache_dir,
            "last_cleanup": self.metadata.get("last_cleanup")
        }
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get list of all cached entries
        
        Returns:
            List of cache entry information
        """
        history = []
        for key_hash, entry in self.metadata["entries"].items():
            history.append({
                "key": entry.get("original_key", "unknown"),
                "created": entry["created"],
                "last_accessed": entry["last_accessed"],
                "size_mb": entry.get("file_size", 0) / (1024 * 1024),
                "metadata": entry.get("metadata", {})
            })
        
        # Sort by creation time (newest first)
        history.sort(key=lambda x: x["created"], reverse=True)
        return history
