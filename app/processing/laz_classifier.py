"""
LAZ File Classification Module
Determines whether LAZ files are uploaded/loaded vs coordinate-generated
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

class LAZClassifier:
    """
    Classifies LAZ files as loaded/uploaded vs coordinate-generated
    """
    
    @staticmethod
    def is_loaded_laz(laz_file_path: str) -> Tuple[bool, str]:
        """
        Determine if LAZ file is loaded/uploaded (vs coordinate-generated)
        
        Args:
            laz_file_path: Path to LAZ file
            
        Returns:
            Tuple of (is_loaded: bool, reason: str)
        """
        try:
            file_path = Path(laz_file_path)
            
            # Check 1: File existence
            if not file_path.exists():
                return False, "File does not exist"
            
            # Check 2: File size (coordinate-generated files are typically very small or empty)
            file_size = file_path.stat().st_size
            if file_size < 1024:  # Less than 1KB indicates placeholder/mock file
                return False, f"File too small ({file_size} bytes) - likely coordinate-generated"
            
            # Check 3: File content check for placeholder text
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('#') and 'placeholder' in first_line.lower():
                        return False, "Contains placeholder text - coordinate-generated"
            except:
                # If we can't read as text, it's likely a real binary LAZ file
                pass
            
            # Check 4: Directory structure patterns
            path_parts = file_path.parts
            
            # Coordinate-generated files often have predictable naming patterns
            filename = file_path.name.lower()
            if any(pattern in filename for pattern in ['lidar_', '_temp_', 'mock_', 'placeholder_']):
                return False, f"Filename pattern indicates coordinate-generated: {filename}"
            
            # Check 5: Look for associated processing metadata
            parent_dir = file_path.parent
            
            # Check for upload indicators
            upload_indicators = ['uploaded', 'loaded', 'user_data']
            if any(indicator in str(parent_dir).lower() for indicator in upload_indicators):
                return True, "Directory indicates uploaded file"
            
            # Check 6: File age vs coordinate pattern
            # Coordinate-generated files are typically created very recently
            import time
            file_age_hours = (time.time() - file_path.stat().st_mtime) / 3600
            
            if file_age_hours < 0.1 and file_size < 10000:  # Less than 6 minutes old and small
                return False, f"Recently created small file ({file_age_hours:.1f}h old, {file_size} bytes)"
            
            # Check 7: Magic number check for real LAZ files
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    # LAZ files should start with LAS header signature
                    if len(header) >= 4:
                        # LAS files start with "LASF"
                        if header == b'LASF':
                            return True, "Valid LAZ/LAS header detected - real file"
                        elif header.startswith(b'#'):
                            return False, "Text file with # comment - placeholder"
            except:
                pass
            
            # Default: If file is reasonably sized and doesn't match coordinate patterns
            if file_size > 10000:  # > 10KB
                return True, f"File size ({file_size} bytes) indicates real data"
            
            return False, "Unable to determine - assuming coordinate-generated"
            
        except Exception as e:
            return False, f"Error during classification: {str(e)}"
    
    @staticmethod
    def get_loaded_laz_files(directory: str) -> List[Dict[str, Any]]:
        """
        Find all loaded LAZ files in a directory
        
        Args:
            directory: Directory to search
            
        Returns:
            List of dictionaries with file info and classification
        """
        loaded_files = []
        
        try:
            search_path = Path(directory)
            if not search_path.exists():
                return loaded_files
            
            # Find all LAZ files recursively
            laz_files = list(search_path.rglob("*.laz")) + list(search_path.rglob("*.LAZ"))
            
            for laz_file in laz_files:
                is_loaded, reason = LAZClassifier.is_loaded_laz(str(laz_file))
                
                if is_loaded:
                    file_info = {
                        "file_path": str(laz_file),
                        "file_name": laz_file.name,
                        "file_size": laz_file.stat().st_size,
                        "region_name": LAZClassifier._extract_region_name(str(laz_file)),
                        "classification_reason": reason,
                        "is_loaded": True
                    }
                    loaded_files.append(file_info)
                    print(f"✅ Loaded LAZ found: {laz_file.name} - {reason}")
                else:
                    print(f"⏭️ Skipping coordinate-generated: {laz_file.name} - {reason}")
            
            return loaded_files
            
        except Exception as e:
            print(f"❌ Error searching for loaded LAZ files: {e}")
            return loaded_files
    
    @staticmethod
    def _extract_region_name(laz_file_path: str) -> str:
        """Extract region name from LAZ file path"""
        file_path = Path(laz_file_path)
        
        # Try to extract from path structure
        if "input" in file_path.parts:
            try:
                input_index = file_path.parts.index("input")
                if input_index + 1 < len(file_path.parts):
                    return file_path.parts[input_index + 1]
            except (ValueError, IndexError):
                pass
        
        # Fallback to filename
        return file_path.stem

def find_loaded_laz_files(search_directory: str = "input") -> List[Dict[str, Any]]:
    """
    Convenience function to find loaded LAZ files
    
    Args:
        search_directory: Directory to search (default: "input")
        
    Returns:
        List of loaded LAZ file information
    """
    return LAZClassifier.get_loaded_laz_files(search_directory)
