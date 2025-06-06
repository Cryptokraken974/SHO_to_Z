#!/usr/bin/env python3
"""
Test script to verify the region folder name fix.
"""
import os
import sys
import requests
from pathlib import Path

def test_dtm_api_with_region_names():
    """Test DTM API with different region name scenarios."""
    print("\n🧪 Testing DTM API with different region name scenarios...\n")
    
    # Test cases
    test_cases = [
        {
            "region_name": "FoxIsland",
            "display_region_name": "FoxIsland",
            "expected_folder": "FoxIsland"
        },
        {
            "region_name": "LAZ",  # This is the problematic case
            "display_region_name": "FoxIsland",
            "expected_folder": "FoxIsland"
        },
        {
            "region_name": "OR_WizardIsland",
            "display_region_name": "WizardIsland",
            "expected_folder": "WizardIsland"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"Test Case #{i+1}: {test_case}")
        
        # Prepare form data
        form_data = {
            "region_name": test_case["region_name"],
            "display_region_name": test_case["display_region_name"],
            "processing_type": "dtm"
        }
        
        # Call the API
        print(f"📤 Sending request to /api/dtm with:")
        print(f"   - region_name: {form_data['region_name']}")
        print(f"   - display_region_name: {form_data['display_region_name']}")
        
        try:
            response = requests.post("http://localhost:8000/api/dtm", data=form_data, timeout=30)
            response.raise_for_status()
            
            # Check if response has expected format
            if response.headers.get('content-type') == 'application/json':
                data = response.json()
                print(f"✅ API call successful")
                
                # Check output directory structure
                expected_dir = os.path.join("output", test_case["expected_folder"])
                if os.path.exists(expected_dir):
                    print(f"✅ Output directory created as expected: {expected_dir}")
                    
                    # Check for DTM subfolder
                    dtm_dir = os.path.join(expected_dir, "lidar", "DTM")
                    if os.path.exists(dtm_dir):
                        print(f"✅ DTM directory exists: {dtm_dir}")
                        
                        # List files in DTM directory
                        files = os.listdir(dtm_dir)
                        if files:
                            print(f"✅ Files created in DTM directory: {files}")
                        else:
                            print(f"❌ No files found in DTM directory")
                    else:
                        print(f"❌ DTM directory not found: {dtm_dir}")
                else:
                    print(f"❌ Expected output directory not found: {expected_dir}")
            else:
                print(f"❌ API response is not JSON: {response.headers.get('content-type')}")
                print(f"Response content: {response.text[:200]}...")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API call failed: {e}")
        
        print("\n" + "-" * 50 + "\n")

if __name__ == "__main__":
    test_dtm_api_with_region_names()
