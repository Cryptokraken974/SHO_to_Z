"""
Region mapping configuration for LAZ file processing.

This module provides mapping between user-friendly region names and their
corresponding LAZ files, handling various naming conventions and aliases.
"""

import os
import glob
from typing import Dict, Optional, List
from pathlib import Path


class RegionMapping:
    """Handles mapping between region names and LAZ files."""
    
    def __init__(self):
        """Initialize the region mapping with known aliases and file patterns."""
        # Direct region name to LAZ file mappings
        self.region_to_laz_mapping = {
            # User-friendly name -> LAZ file name (without extension)
            "FoxIsland": "FoxIsland",
            "OR_WizardIsland": "OR_WizardIsland", 
            "WizardIsland": "OR_WizardIsland",  # Alias
            "Wizard Island": "OR_WizardIsland",  # Space-separated alias
        }
        
        # Known LAZ file patterns in different directories
        self.laz_search_patterns = [
            "input/{region_name}/lidar/*.laz",
            "input/{region_name}/*.laz", 
            "input/LAZ/{laz_filename}.laz",
            "input/LAZ/{region_name}.laz",
        ]
    
    def find_laz_file_for_region(self, region_name: str) -> Optional[str]:
        """
        Find the appropriate LAZ file for a given region name.
        
        Args:
            region_name: The user-provided region name
            
        Returns:
            Path to the LAZ file if found, None otherwise
        """
        if not region_name:
            return None
            
        print(f"🔍 Searching for LAZ file for region: '{region_name}'")
        
        # Special case for "LAZ" - this is typically a frontend error
        # where the processing_region is set to the directory name "LAZ" instead of the actual region
        if region_name == "LAZ":
            print(f"⚠️ Warning: 'LAZ' is a directory name, not a region name. This indicates a frontend issue.")
            print(f"⚠️ Checking if there's a default LAZ file to use...")
            
            # Look for any LAZ file in the LAZ directory, use first one found
            laz_files = glob.glob("input/LAZ/*.laz")
            if laz_files:
                print(f"  ✅ Found LAZ file: {laz_files[0]}")
                return laz_files[0]
        
        # Step 1: Check if we have a direct mapping
        mapped_laz_name = self.region_to_laz_mapping.get(region_name)
        if mapped_laz_name:
            print(f"📋 Found mapping: '{region_name}' -> '{mapped_laz_name}'")
            # Try to find the mapped LAZ file
            laz_file = self._search_laz_file_by_patterns(mapped_laz_name, region_name)
            if laz_file:
                return laz_file
        
        # Step 2: Try direct search with the region name
        print(f"🔍 Trying direct search for region: '{region_name}'")
        laz_file = self._search_laz_file_by_patterns(region_name, region_name)
        if laz_file:
            return laz_file
            
        # Step 3: Try case-insensitive search in LAZ directory
        print(f"🔍 Trying case-insensitive search in LAZ directory")
        laz_file = self._case_insensitive_laz_search(region_name)
        if laz_file:
            return laz_file
            
        print(f"❌ No LAZ file found for region: '{region_name}'")
        return None
    
    def _search_laz_file_by_patterns(self, laz_filename: str, region_name: str) -> Optional[str]:
        """Search for LAZ file using predefined patterns."""
        for pattern_template in self.laz_search_patterns:
            pattern = pattern_template.format(
                region_name=region_name,
                laz_filename=laz_filename
            )
            print(f"  🔍 Trying pattern: {pattern}")
            
            laz_files = glob.glob(pattern)
            if laz_files:
                laz_file = laz_files[0]  # Use first match
                print(f"  ✅ Found LAZ file: {laz_file}")
                return laz_file
        
        return None
    
    def _case_insensitive_laz_search(self, region_name: str) -> Optional[str]:
        """Perform case-insensitive search in the LAZ directory."""
        laz_dir = "input/LAZ"
        if not os.path.exists(laz_dir):
            return None
            
        try:
            # Get all LAZ files in the directory
            laz_files = []
            for ext in ["*.laz", "*.LAZ"]:
                laz_files.extend(glob.glob(os.path.join(laz_dir, ext)))
            
            # Try case-insensitive matching
            region_lower = region_name.lower()
            for laz_file in laz_files:
                filename = os.path.splitext(os.path.basename(laz_file))[0].lower()
                if filename == region_lower:
                    print(f"  ✅ Found case-insensitive match: {laz_file}")
                    return laz_file
                    
        except Exception as e:
            print(f"  ❌ Error in case-insensitive search: {e}")
        
        return None
    
    def get_available_regions(self) -> List[str]:
        """Get list of all available region names that have LAZ files."""
        available_regions = []
        
        # Check LAZ directory for files
        laz_dir = "input/LAZ"
        if os.path.exists(laz_dir):
            for ext in ["*.laz", "*.LAZ"]:
                laz_files = glob.glob(os.path.join(laz_dir, ext))
                for laz_file in laz_files:
                    filename = os.path.splitext(os.path.basename(laz_file))[0]
                    available_regions.append(filename)
        
        # Add known mappings
        available_regions.extend(self.region_to_laz_mapping.keys())
        
        return list(set(available_regions))
    
    def add_region_mapping(self, region_name: str, laz_filename: str):
        """Add a new region to LAZ file mapping."""
        self.region_to_laz_mapping[region_name] = laz_filename
        print(f"📋 Added region mapping: '{region_name}' -> '{laz_filename}'")


# Global instance
region_mapper = RegionMapping()
