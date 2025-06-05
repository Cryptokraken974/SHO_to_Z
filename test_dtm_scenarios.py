#!/usr/bin/env python3

import requests
import json

def test_dtm_api_scenarios():
    """Test various DTM API scenarios to identify what causes 400 errors"""
    base_url = "http://localhost:8000/api/dtm"
    
    # Test scenarios
    test_cases = [
        {
            "name": "Valid LAZ file",
            "data": {"input_file": "input/LAZ/OR_WizardIsland.laz"},
            "expected": 200
        },
        {
            "name": "Non-existent LAZ file", 
            "data": {"input_file": "input/LAZ/nonexistent.laz"},
            "expected": 400
        },
        {
            "name": "Empty input_file",
            "data": {"input_file": ""},
            "expected": 400
        },
        {
            "name": "No parameters",
            "data": {},
            "expected": 400
        },
        {
            "name": "Region without LAZ files",
            "data": {"region_name": "nonexistent_region", "processing_type": "dtm"},
            "expected": 400
        },
        {
            "name": "Missing processing_type with region",
            "data": {"region_name": "some_region"},
            "expected": 400
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"📦 Data: {test_case['data']}")
        
        try:
            response = requests.post(base_url, data=test_case['data'], timeout=10)
            
            print(f"📊 Status: {response.status_code} (expected: {test_case['expected']})")
            
            if response.status_code == test_case['expected']:
                print(f"✅ Test passed")
            else:
                print(f"❌ Test failed - unexpected status code")
            
            if response.status_code != 200:
                print(f"📄 Error response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_dtm_api_scenarios()
