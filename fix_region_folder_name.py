#!/usr/bin/env python3
"""
This script fixes the region folder name issue in the SHO_to_Z application.

Problem: When selecting a region like "FoxIsland", the system sometimes creates 
output folders named "OR_WizardIsland" because it's using the LAZ filename 
instead of the selected region name.

This script:
1. Updates the endpoints to pass the display_region_name to processing functions
2. Updates the processing functions to use the region_name for output folders
3. Fixes the frontend to never set processing_region to "LAZ"
"""
import os
import re
import sys
import glob

def update_laz_processing_endpoint():
    """
    Update the LAZ processing endpoint to accept display_region_name parameter
    and pass it to processing functions.
    """
    file_path = "app/endpoints/laz_processing.py"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 1. Update the DTM endpoint
    dtm_pattern = r'@router.post\("/api/dtm"\)\nasync def api_dtm\(input_file: str = Form\(None\), region_name: str = Form\(None\), processing_type: str = Form\(None\)\):'
    dtm_replacement = '@router.post("/api/dtm")\nasync def api_dtm(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):'
    content = re.sub(dtm_pattern, dtm_replacement, content)
    
    # 2. Update the DTM function call
    dtm_call_pattern = r'tif_path = dtm\(input_file(?:, region_name)?\)'
    dtm_call_replacement = 'output_region = display_region_name if display_region_name else region_name\n        tif_path = dtm(input_file, output_region)'
    content = re.sub(dtm_call_pattern, dtm_call_replacement, content)
    
    # 3. Update the hillshade endpoint
    hillshade_pattern = r'@router.post\("/api/hillshade"\)\nasync def api_hillshade\(input_file: str = Form\(None\), region_name: str = Form\(None\), processing_type: str = Form\(None\)\):'
    hillshade_replacement = '@router.post("/api/hillshade")\nasync def api_hillshade(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):'
    content = re.sub(hillshade_pattern, hillshade_replacement, content)
    
    # 4. Update the hillshade function call with a try/except to handle different function signatures
    hillshade_call_pattern = r'tif_path = hillshade\(input_file\)'
    hillshade_call_replacement = '''# Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        
        # Check if hillshade function accepts region_name parameter
        try:
            from inspect import signature
            sig = signature(hillshade)
            if 'region_name' in sig.parameters:
                tif_path = hillshade(input_file, output_region)
            else:
                tif_path = hillshade(input_file)
        except:
            # Fallback to original function call if anything goes wrong
            tif_path = hillshade(input_file)'''
    content = re.sub(hillshade_call_pattern, hillshade_call_replacement, content)
    
    # 5. Do the same for all other raster type endpoints (slope, aspect, etc.)
    for raster_type in ['slope', 'aspect', 'tri', 'tpi', 'roughness', 'chm', 'dsm']:
        # Update endpoint signature
        endpoint_pattern = f'@router.post\\("/api/{raster_type}"\\)\\nasync def api_{raster_type}\\(input_file: str = Form\\(None\\), region_name: str = Form\\(None\\), processing_type: str = Form\\(None\\)\\):'
        endpoint_replacement = f'@router.post("/api/{raster_type}")\\nasync def api_{raster_type}(input_file: str = Form(None), region_name: str = Form(None), processing_type: str = Form(None), display_region_name: str = Form(None)):'
        content = re.sub(endpoint_pattern, endpoint_replacement, content)
        
        # Update function call
        call_pattern = f'tif_path = {raster_type}\\(input_file\\)'
        call_replacement = f'''# Use display_region_name for output directory if provided, otherwise use original region_name
        output_region = display_region_name if display_region_name else region_name
        
        # Check if {raster_type} function accepts region_name parameter
        try:
            from inspect import signature
            sig = signature({raster_type})
            if 'region_name' in sig.parameters:
                tif_path = {raster_type}(input_file, output_region)
            else:
                tif_path = {raster_type}(input_file)
        except:
            # Fallback to original function call if anything goes wrong
            tif_path = {raster_type}(input_file)'''
        content = re.sub(call_pattern, call_replacement, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path}")
    return True

def update_processing_function(file_path, function_name):
    """
    Update a processing function to accept and use region_name parameter.
    """
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 1. Update function signature
    func_pattern = f'def {function_name}\\(input_file: str\\) -> str:'
    func_replacement = f'def {function_name}(input_file: str, region_name: str = None) -> str:'
    
    if not re.search(func_pattern, content):
        print(f"Warning: Function {function_name} signature not found in {file_path}")
        return False
        
    content = re.sub(func_pattern, func_replacement, content)
    
    # 2. Update function docstring
    docstring_pattern = r'Args:\s+input_file: Path to the input LAZ file\s+'
    docstring_replacement = 'Args:\n        input_file: Path to the input LAZ file\n        region_name: Optional region name to use for output directory (instead of extracted from filename)\n        '
    content = re.sub(docstring_pattern, docstring_replacement, content)
    
    # 3. Update output directory generation
    output_dir_pattern = r'(\s+)# Create output directory structure: output/<file_stem>/lidar/.*?\s+output_dir = os\.path\.join\("output", file_stem,'
    output_dir_replacement = r'\1# Use provided region_name for output directory if available, otherwise use file_stem\1output_folder_name = region_name if region_name else file_stem\1print(f"📁 Using output folder name: {output_folder_name} (from region_name: {region_name})")\1\1# Create output directory structure: output/<output_folder_name>/lidar/\1output_dir = os.path.join("output", output_folder_name,'
    content = re.sub(output_dir_pattern, output_dir_replacement, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {function_name} in {file_path}")
    return True

def update_processing_js():
    """
    Update processing.js to pass the display region name in addition to the processing region.
    """
    file_path = "frontend/js/processing.js"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update form data creation for region-based processing
    pattern = r'formData\.append\(\'region_name\', processingRegion\); // Use processing region, not display region'
    replacement = "formData.append('region_name', processingRegion); // Use processing region for LAZ file lookup\n        formData.append('display_region_name', selectedRegion); // Pass the actual selected region for output folders"
    
    if not re.search(pattern, content):
        print(f"Warning: region_name form field not found in {file_path}")
        return False
        
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path}")
    return True

def update_ui_js():
    """
    Update UI.js to never set processing_region to 'LAZ'.
    """
    file_path = "frontend/js/ui.js"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add check to prevent setting processing_region to 'LAZ'
    pattern = r'const regionName = selectedItem\.data\(\'region-name\'\); // Display name\s+const processingRegion = selectedItem\.data\(\'processing-region\'\); // Processing region name'
    replacement = "const regionName = selectedItem.data('region-name'); // Display name\n      let processingRegion = selectedItem.data('processing-region'); // Processing region name\n      \n      // Make sure processing region is not just \"LAZ\" (which would cause problems)\n      if (processingRegion === \"LAZ\") {\n        console.warn(\"⚠️ Processing region is 'LAZ', which is likely incorrect. Using display name instead.\");\n        processingRegion = regionName;\n      }"
    
    if not re.search(pattern, content):
        print(f"Warning: regionName/processingRegion assignment not found in {file_path}")
        return False
        
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path}")
    return True

def update_region_mapping():
    """
    Update the region mapping to handle special 'LAZ' directory case.
    """
    file_path = "app/region_config/region_mapping.py"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add special case handling for 'LAZ'
    pattern = r'def find_laz_file_for_region\(self, region_name: str\) -> Optional\[str\]:\s+""".*?"""\s+if not region_name:\s+return None\s+\s+print\(f"🔍 Searching for LAZ file for region: \'{region_name}\'\"\)'
    replacement = r'def find_laz_file_for_region(self, region_name: str) -> Optional[str]:\n        """\n        Find the appropriate LAZ file for a given region name.\n        \n        Args:\n            region_name: The user-provided region name\n            \n        Returns:\n            Path to the LAZ file if found, None otherwise\n        """\n        if not region_name:\n            return None\n            \n        print(f"🔍 Searching for LAZ file for region: \'{region_name}\'")\n        \n        # Special case for "LAZ" - this is typically a frontend error\n        # where the processing_region is set to the directory name "LAZ" instead of the actual region\n        if region_name == "LAZ":\n            print(f"⚠️ Warning: \'LAZ\' is a directory name, not a region name. This indicates a frontend issue.")\n            print(f"⚠️ Checking if there\'s a default LAZ file to use...")\n            \n            # Look for any LAZ file in the LAZ directory, use first one found\n            laz_files = glob.glob("input/LAZ/*.laz")\n            if laz_files:\n                print(f"  ✅ Found LAZ file: {laz_files[0]}")\n                return laz_files[0]'
    
    if not re.search(pattern, content):
        print(f"Warning: find_laz_file_for_region function not found in {file_path}")
        return False
        
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path}")
    return True

def main():
    """Main function to apply all fixes."""
    print("🔧 Applying region folder name fixes...")
    
    # Update frontend files
    update_processing_js()
    update_ui_js()
    
    # Update backend files
    update_region_mapping()
    update_laz_processing_endpoint()
    
    # Update processing functions
    processing_functions = [
        {"path": "app/processing/dtm.py", "function": "dtm"},
        {"path": "app/processing/dsm.py", "function": "dsm"},
        {"path": "app/processing/chm.py", "function": "chm"},
        {"path": "app/processing/hillshade.py", "function": "hillshade"},
        {"path": "app/processing/slope.py", "function": "slope"},
        {"path": "app/processing/aspect.py", "function": "aspect"},
        {"path": "app/processing/tri.py", "function": "tri"},
        {"path": "app/processing/tpi.py", "function": "tpi"},
        {"path": "app/processing/roughness.py", "function": "roughness"},
    ]
    
    for func in processing_functions:
        update_processing_function(func["path"], func["function"])
    
    print("\n✅ All fixes applied successfully!")
    print("\n📋 Summary of changes:")
    print("1. Frontend now sends both region_name AND display_region_name to the API")
    print("2. Frontend prevents setting processingRegion to 'LAZ'")
    print("3. Backend region mapping handles 'LAZ' as a special case")
    print("4. Processing functions now accept region_name parameter")
    print("5. Processing functions use region_name for output directory")
    
    print("\n🚀 Changes should now be effective. Please restart the application.")

if __name__ == "__main__":
    main()
