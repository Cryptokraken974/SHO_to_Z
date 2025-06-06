#!/usr/bin/env python3
"""
Apply LAZ directory fallback fix to all processing endpoints
"""

import re

def apply_laz_fix():
    file_path = "app/endpoints/laz_processing.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find LAZ file lookup sections that need the fix
    pattern = r'(laz_pattern = f"input/{region_name}/lidar/\*\.laz"\s+laz_files = glob\.glob\(laz_pattern\)\s+if not laz_files:\s+# Fallback: look directly in region directory\s+laz_pattern = f"input/{region_name}/\*\.laz"\s+laz_files = glob\.glob\(laz_pattern\)\s+if not laz_files:\s+raise ValueError\(f"No LAZ files found in region {region_name}"\))'
    
    # Replacement with the LAZ directory fallback
    replacement = r'''laz_pattern = f"input/{region_name}/lidar/*.laz"
        laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look directly in region directory
            laz_pattern = f"input/{region_name}/*.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            # Fallback: look in LAZ directory for files matching the region name
            laz_pattern = f"input/LAZ/{region_name}.laz"
            laz_files = glob.glob(laz_pattern)
        
        if not laz_files:
            raise ValueError(f"No LAZ files found in region {region_name}")'''
    
    # Apply the fix
    updated_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Count how many fixes were applied
    fixes_applied = len(re.findall(pattern, content, flags=re.MULTILINE | re.DOTALL))
    
    if fixes_applied > 0:
        with open(file_path, 'w') as f:
            f.write(updated_content)
        print(f"Applied LAZ directory fallback fix to {fixes_applied} endpoints")
    else:
        print("No endpoints found that need the fix")
    
    # Show current status
    laz_fallbacks = len(re.findall(r'input/LAZ/\{region_name\}\.laz', updated_content))
    print(f"Total endpoints with LAZ directory fallback: {laz_fallbacks}")

if __name__ == "__main__":
    apply_laz_fix()
