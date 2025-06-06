#!/usr/bin/env python3

"""
Script to update all remaining LAZ processing endpoints to use the new region mapping system.
"""

import re

def update_laz_processing_endpoints():
    file_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/app/endpoints/laz_processing.py"
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match the old region processing logic
    old_pattern = r"""        # Look for LAZ files in the region's lidar directory
        import glob
        from pathlib import Path
        laz_pattern = f"input/{region_name}/lidar/\*\.laz"
        laz_files = glob\.glob\(laz_pattern\)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/\*\.laz"
            laz_files = glob\.glob\(laz_pattern\)
        
        if not laz_files:
            # Fallback: look in LAZ directory for files matching the region name
            laz_pattern = f"input/LAZ/{region_name}\.laz"
            laz_files = glob\.glob\(laz_pattern\)
        
        if not laz_files:
            raise ValueError\(f"No LAZ files found in region {region_name}"\)        
        # Use the first LAZ file found
        input_file = laz_files\[0\]
        print\(f"📥 Using LAZ file: {input_file}"\)"""
    
    # New replacement logic
    new_replacement = """        # Region-based processing: find LAZ file in region using proper mapping
        input_file = resolve_laz_file_from_region(region_name, processing_type)"""
    
    # Find all remaining occurrences and replace them
    updated_content = re.sub(old_pattern, new_replacement, content, flags=re.MULTILINE)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write(updated_content)
    
    print("✅ Updated all remaining LAZ processing endpoints")

if __name__ == "__main__":
    update_laz_processing_endpoints()
