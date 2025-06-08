#!/usr/bin/env python3
"""
Test frontend region selection state - Check what FileManager is returning
"""

import requests
from urllib.parse import urlencode

def test_frontend_region_state():
    """Test what the frontend would have as selected region state"""
    print("🔍 Testing frontend region selection state simulation")
    
    # Simulate the scenario where we have no region selected (likely the issue)
    selectedRegion = None
    processingRegion = None
    selectedFile = None
    
    print(f"📊 selectedRegion: {selectedRegion}")
    print(f"📊 processingRegion: {processingRegion}")  
    print(f"📊 selectedFile: {selectedFile}")
    
    # This is what the frontend logic would do
    if not selectedRegion and not selectedFile:
        print("❌ NO REGION OR FILE SELECTED - This would trigger the warning")
        return False
        
    # If we had a region, this is what would happen
    if selectedRegion and processingRegion:
        print("✅ Region-based processing would work")
        data = {
            'region_name': processingRegion,
            'display_region_name': selectedRegion,
            'processing_type': 'dtm'
        }
        print(f"📤 Form data would be: {data}")
        return True
    elif selectedFile:
        print("✅ File-based processing would work")
        data = {
            'input_file': selectedFile
        }
        print(f"📤 Form data would be: {data}")
        return True
    else:
        print("❌ Neither condition met - would send empty form data")
        return False

def test_with_cui_region():
    """Test with CUI region selected"""
    print("\n🔍 Testing with CUI region selected")
    
    selectedRegion = "CUI_A01_10-04"
    processingRegion = "CUI_A01_10-04"  # This might be the issue
    selectedFile = None
    
    print(f"📊 selectedRegion: {selectedRegion}")
    print(f"📊 processingRegion: {processingRegion}")  
    print(f"📊 selectedFile: {selectedFile}")
    
    if selectedRegion and processingRegion:
        print("✅ Region-based processing would work")
        data = {
            'region_name': processingRegion,
            'display_region_name': selectedRegion,
            'processing_type': 'dtm'
        }
        print(f"📤 Form data would be: {data}")
        
        # Test the actual API call
        print("\n🧪 Testing actual API call...")
        try:
            response = requests.post("http://localhost:8000/api/dtm", data=data)
            print(f"📥 Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"📄 Response text: {response.text}")
            else:
                print("✅ API call successful!")
        except Exception as e:
            print(f"💥 Exception: {e}")
        
        return True
    else:
        print("❌ Region-based processing would fail")
        return False

if __name__ == "__main__":
    print("🔬 Frontend Region Selection State Test")
    print("=" * 60)
    
    test_frontend_region_state()
    test_with_cui_region()
