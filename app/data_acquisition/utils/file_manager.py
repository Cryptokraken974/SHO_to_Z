"""File management utilities for data acquisition."""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

@dataclass
class FileInfo:
    """Information about a managed file."""
    path: Path
    size_mb: float
    created_at: datetime
    data_type: str
    source: str
    metadata: Dict = None

class FileManager:
    """Manages downloaded and processed data files."""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.cache_dir = self.base_dir / "cache"
        self.downloads_dir = self.base_dir / "downloads"
        self.processed_dir = self.base_dir / "processed"
        
        # Only create base directory, not subdirectories
        # Subdirectories will be created only when needed
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.base_dir / "file_index.json"
        self._load_index()
    
    def _load_index(self):
        """Load file index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                    self.file_index = {
                        path: FileInfo(
                            path=Path(info['path']),
                            size_mb=info['size_mb'],
                            created_at=datetime.fromisoformat(info['created_at']),
                            data_type=info['data_type'],
                            source=info['source'],
                            metadata=info.get('metadata', {})
                        )
                        for path, info in data.items()
                    }
            except Exception:
                self.file_index = {}
        else:
            self.file_index = {}
    
    def _save_index(self):
        """Save file index to disk."""
        data = {
            str(path): {
                'path': str(info.path),
                'size_mb': info.size_mb,
                'created_at': info.created_at.isoformat(),
                'data_type': info.data_type,
                'source': info.source,
                'metadata': info.metadata or {}
            }
            for path, info in self.file_index.items()
        }
        
        with open(self.index_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_file(self, data_type_or_path, path_or_data_type, metadata_or_source, metadata=None):
        """
        Flexible register_file method that can handle different argument patterns
        
        Patterns:
        1. register_file(file_path, data_type, source, metadata) - original
        2. register_file(data_type, file_path, metadata_dict) - test expected
        """
        # Check if first argument looks like a path or data type
        if isinstance(data_type_or_path, (str, Path)) and ("/" in str(data_type_or_path) or Path(data_type_or_path).exists()):
            # Pattern 1: register_file(file_path, data_type, source, metadata)
            return self._register_file_original(data_type_or_path, path_or_data_type, metadata_or_source, metadata)
        else:
            # Pattern 2: register_file(data_type, file_path, metadata_dict)
            data_type = data_type_or_path
            file_path = path_or_data_type
            metadata_dict = metadata_or_source if isinstance(metadata_or_source, dict) else {}
            source = metadata_dict.get("source", "unknown")
            return self._register_file_original(file_path, data_type, source, metadata_dict)
        """Register a file in the management system."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        size_mb = file_path.stat().st_size / (1024 * 1024)
        
        file_info = FileInfo(
            path=file_path,
            size_mb=size_mb,
            created_at=datetime.now(),
            data_type=data_type,
            source=source,
            metadata=metadata or {}
        )
        
        self.file_index[str(file_path)] = file_info
        self._save_index()
        
        return file_info
    
    def register_file(self, data_type_or_path, path_or_data_type, metadata_or_source, metadata=None):
        """
        Flexible register_file method that can handle different argument patterns
        
        Patterns:
        1. register_file(file_path, data_type, source, metadata) - original
        2. register_file(data_type, file_path, metadata_dict) - test expected
        """
        # Check if first argument looks like a path or data type
        if isinstance(data_type_or_path, (str, Path)) and ("/" in str(data_type_or_path) or Path(data_type_or_path).exists()):
            # Pattern 1: register_file(file_path, data_type, source, metadata)
            return self._register_file_original(data_type_or_path, path_or_data_type, metadata_or_source, metadata)
        else:
            # Pattern 2: register_file(data_type, file_path, metadata_dict)
            data_type = data_type_or_path
            file_path = path_or_data_type
            metadata_dict = metadata_or_source if isinstance(metadata_or_source, dict) else {}
            source = metadata_dict.get("source", "unknown")
            return self._register_file_original(file_path, data_type, source, metadata_dict)
    
    def _register_file_original(self, file_path: Union[str, Path], data_type: str, 
                     source: str, metadata: Dict = None) -> FileInfo:
        """Original register_file implementation."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        size_mb = file_path.stat().st_size / (1024 * 1024)
        
        file_info = FileInfo(
            path=file_path,
            size_mb=size_mb,
            created_at=datetime.now(),
            data_type=data_type,
            source=source,
            metadata=metadata or {}
        )
        
        self.file_index[str(file_path)] = file_info
        self._save_index()
        
        return file_info
    
    def get_organized_path(self, data_type: str, source: str, 
                          bbox_hash: str, extension: str = "tif") -> Path:
        """Get organized file path for storing data."""
        # Create organized directory structure only when needed
        org_dir = self.downloads_dir / data_type / source
        # Note: Directory creation moved to when file is actually being written
        
        # Generate filename with bbox hash
        filename = f"{source}_{data_type}_{bbox_hash}.{extension}"
        return org_dir / filename
    
    def move_to_organized_storage(self, temp_path: Union[str, Path], 
                                data_type: str, source: str, 
                                bbox_hash: str) -> Path:
        """Move file from temporary location to organized storage."""
        temp_path = Path(temp_path)
        extension = temp_path.suffix.lstrip('.')
        
        organized_path = self.get_organized_path(data_type, source, bbox_hash, extension)
        
        # Create directory only when actually moving the file
        organized_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(temp_path), str(organized_path))
        
        # Update index if file was registered
        if str(temp_path) in self.file_index:
            file_info = self.file_index.pop(str(temp_path))
            file_info.path = organized_path
            self.file_index[str(organized_path)] = file_info
            self._save_index()
        
        return organized_path
    
    def find_files(self, data_type: Optional[str] = None, 
                  source: Optional[str] = None) -> List[FileInfo]:
        """Find files matching criteria."""
        results = []
        
        for file_info in self.file_index.values():
            if data_type and file_info.data_type != data_type:
                continue
            if source and file_info.source != source:
                continue
            
            # Check if file still exists
            if file_info.path.exists():
                results.append(file_info)
            else:
                # Remove from index if file doesn't exist
                self.file_index.pop(str(file_info.path), None)
        
        # Save index if we removed any files
        if len(results) != len(self.file_index):
            self._save_index()
        
        return results
    
    def get_file_info(self, file_path: Union[str, Path]) -> Optional[FileInfo]:
        """Get information about a specific file."""
        return self.file_index.get(str(file_path))
    
    def delete_file(self, file_path: Union[str, Path]) -> bool:
        """Delete a file and remove from index."""
        file_path = Path(file_path)
        
        try:
            if file_path.exists():
                file_path.unlink()
            
            # Remove from index
            self.file_index.pop(str(file_path), None)
            self._save_index()
            
            return True
        except Exception:
            return False
    
    def cleanup_old_files(self, days_old: int = 30) -> List[str]:
        """Clean up files older than specified days."""
        cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        deleted_files = []
        
        for file_path, file_info in list(self.file_index.items()):
            if file_info.created_at.timestamp() < cutoff_date:
                if self.delete_file(file_info.path):
                    deleted_files.append(file_path)
        
        return deleted_files
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics."""
        total_files = len(self.file_index)
        total_size_mb = sum(info.size_mb for info in self.file_index.values())
        
        # Count by data type
        by_type = {}
        for info in self.file_index.values():
            data_type = info.data_type
            if data_type not in by_type:
                by_type[data_type] = {'count': 0, 'size_mb': 0}
            by_type[data_type]['count'] += 1
            by_type[data_type]['size_mb'] += info.size_mb
        
        # Count by source
        by_source = {}
        for info in self.file_index.values():
            source = info.source
            if source not in by_source:
                by_source[source] = {'count': 0, 'size_mb': 0}
            by_source[source]['count'] += 1
            by_source[source]['size_mb'] += info.size_mb
        
        return {
            'total_files': total_files,
            'total_size_mb': total_size_mb,
            'total_size_gb': total_size_mb / 1024,
            'by_data_type': by_type,
            'by_source': by_source,
            'storage_dirs': {
                'cache': str(self.cache_dir),
                'downloads': str(self.downloads_dir),
                'processed': str(self.processed_dir)
            }
        }
    
    @staticmethod
    def generate_bbox_hash(west: float, south: float, east: float, north: float) -> str:
        """Generate hash for bounding box coordinates."""
        bbox_str = f"{west}_{south}_{east}_{north}"
        return hashlib.md5(bbox_str.encode()).hexdigest()[:8]
