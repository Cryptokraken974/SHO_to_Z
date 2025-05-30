#!/usr/bin/env python3

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, 'app')

from processing.dtm import convert_las_to_dtm

def test_dtm():
    print("=" * 50)
    print("DEBUGGING DTM FUNCTION")
    print("=" * 50)
    
    input_file = 'input/foxisland/FoxIsland.laz'
    output_file = 'output/FoxIsland/DTM/FoxIsland_DTM_manual_debug.tif'
    
    # Remove existing file
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Removed existing file: {output_file}")
    
    print(f"About to call convert_las_to_dtm...")
    success, message = convert_las_to_dtm(input_file, output_file, 1.0)
    print(f"Function returned: success={success}, message={message}")
    
    # Check if file exists
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        print(f"Output file exists: {size} bytes")
    else:
        print(f"Output file does not exist!")

if __name__ == "__main__":
    test_dtm()
