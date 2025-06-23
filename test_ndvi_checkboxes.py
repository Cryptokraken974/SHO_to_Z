#!/usr/bin/env python3
"""
Test NDVI Checkbox Visibility in Both Modals
Tests that NDVI checkboxes appear in both LAZ file and folder modals
"""

import requests
import json
from pathlib import Path

def test_laz_folder_ndvi_checkbox():
    """Test that NDVI checkbox is present in LAZ folder modal"""
    print("🧪 Testing LAZ Folder Modal NDVI Checkbox...")
    
    # Check if the LAZ folder modal HTML contains the NDVI checkbox
    modal_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/frontend/modules/modals/laz-folder-modal.html")
    
    if not modal_path.exists():
        print("❌ LAZ folder modal file not found")
        return False
    
    try:
        with open(modal_path, 'r') as f:
            content = f.read()
        
        # Check for NDVI checkbox elements
        ndvi_elements = [
            'laz-folder-ndvi-enabled',  # Checkbox ID
            'NDVI Enabled',             # Label text
            'Enable NDVI processing for vegetation analysis'  # Description
        ]
        
        missing_elements = []
        for element in ndvi_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing NDVI elements in folder modal: {missing_elements}")
            return False
        else:
            print("✅ LAZ folder modal contains NDVI checkbox")
            return True
            
    except Exception as e:
        print(f"❌ Error reading folder modal: {e}")
        return False

def test_laz_file_ndvi_checkbox():
    """Test that NDVI checkbox is present in LAZ file modal"""
    print("🧪 Testing LAZ File Modal NDVI Checkbox...")
    
    # Check if the LAZ file modal HTML contains the NDVI checkbox
    modal_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/frontend/modules/modals/laz-file-modal.html")
    
    if not modal_path.exists():
        print("❌ LAZ file modal file not found")
        return False
    
    try:
        with open(modal_path, 'r') as f:
            content = f.read()
        
        # Check for NDVI checkbox elements
        ndvi_elements = [
            'laz-ndvi-enabled',         # Checkbox ID
            'NDVI Enabled',             # Label text
            'Enable NDVI processing for vegetation analysis'  # Description
        ]
        
        missing_elements = []
        for element in ndvi_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing NDVI elements in file modal: {missing_elements}")
            return False
        else:
            print("✅ LAZ file modal contains NDVI checkbox")
            return True
            
    except Exception as e:
        print(f"❌ Error reading file modal: {e}")
        return False

def test_javascript_ndvi_handling():
    """Test that JavaScript properly handles NDVI transfer between modals"""
    print("🧪 Testing JavaScript NDVI Handling...")
    
    js_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/frontend/js/geotiff-left-panel.js")
    
    if not js_path.exists():
        print("❌ JavaScript file not found")
        return False
    
    try:
        with open(js_path, 'r') as f:
            content = f.read()
        
        # Check for NDVI handling code
        ndvi_code_elements = [
            'laz-folder-ndvi-enabled',      # Folder checkbox ID
            'laz-ndvi-enabled',             # File checkbox ID
            'folderNdviEnabled',            # Variable for folder NDVI
            'Transferred NDVI setting',     # Transfer log message
            'Folder NDVI enabled'           # Folder capture log message
        ]
        
        missing_elements = []
        for element in ndvi_code_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing NDVI handling code: {missing_elements}")
            return False
        else:
            print("✅ JavaScript contains NDVI transfer handling")
            return True
            
    except Exception as e:
        print(f"❌ Error reading JavaScript file: {e}")
        return False

def test_ndvi_upload_integration():
    """Test NDVI parameter is captured and sent to backend"""
    print("🧪 Testing NDVI Upload Integration...")
    
    js_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/frontend/js/geotiff-left-panel.js")
    
    try:
        with open(js_path, 'r') as f:
            content = f.read()
        
        # Check for NDVI upload integration
        upload_elements = [
            "const ndviCheckbox = document.getElementById('laz-ndvi-enabled')",
            "const ndviEnabled = ndviCheckbox ? ndviCheckbox.checked : false",
            "formData.append('ndvi_enabled', ndviEnabled.toString())",
            "console.log('📂 NDVI enabled:', ndviEnabled)"
        ]
        
        missing_elements = []
        for element in upload_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing NDVI upload integration: {missing_elements}")
            return False
        else:
            print("✅ JavaScript contains NDVI upload integration")
            return True
            
    except Exception as e:
        print(f"❌ Error reading JavaScript file: {e}")
        return False

def main():
    """Run all NDVI checkbox tests"""
    print("🎯 NDVI Checkbox Implementation Test")
    print("=" * 50)
    
    results = []
    
    # Test 1: LAZ folder modal has NDVI checkbox
    results.append(("LAZ Folder Modal NDVI Checkbox", test_laz_folder_ndvi_checkbox()))
    
    # Test 2: LAZ file modal has NDVI checkbox
    results.append(("LAZ File Modal NDVI Checkbox", test_laz_file_ndvi_checkbox()))
    
    # Test 3: JavaScript handles NDVI transfer
    results.append(("JavaScript NDVI Transfer", test_javascript_ndvi_handling()))
    
    # Test 4: NDVI upload integration
    results.append(("NDVI Upload Integration", test_ndvi_upload_integration()))
    
    # Print results summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All NDVI checkbox tests passed! Both modals have NDVI functionality.")
    else:
        print("⚠️ Some tests failed. Check the implementation.")

if __name__ == "__main__":
    main()
