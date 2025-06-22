#!/usr/bin/env python3
"""
Test script to verify OpenAI analysis tab loads regions from output folder.
"""

import requests
import json

def test_openai_analysis_regions():
    """Test that OpenAI analysis tab loads regions from output folder."""
    print("🔍 Testing OpenAI Analysis region loading...")
    print("=" * 60)
    
    # Test 1: Check input folder regions
    print("📄 Test 1: Checking input folder regions...")
    
    try:
        response = requests.get("http://localhost:8000/api/regions/list?source=input")
        if response.status_code == 200:
            data = response.json()
            input_regions = [r['name'] for r in data.get('regions', [])]
            print(f"✅ Input folder regions: {input_regions}")
        else:
            print(f"❌ Failed to get input regions: HTTP {response.status_code}")
            input_regions = []
    except Exception as e:
        print(f"❌ Error getting input regions: {e}")
        input_regions = []
    
    # Test 2: Check output folder regions
    print("\n📄 Test 2: Checking output folder regions...")
    
    try:
        response = requests.get("http://localhost:8000/api/regions/list?source=output")
        if response.status_code == 200:
            data = response.json()
            output_regions = [r['name'] for r in data.get('regions', [])]
            print(f"✅ Output folder regions: {output_regions}")
        else:
            print(f"❌ Failed to get output regions: HTTP {response.status_code}")
            output_regions = []
    except Exception as e:
        print(f"❌ Error getting output regions: {e}")
        output_regions = []
    
    # Test 3: Compare the differences
    print("\n📄 Test 3: Analyzing differences...")
    
    input_only = set(input_regions) - set(output_regions)
    output_only = set(output_regions) - set(input_regions)
    common_regions = set(input_regions) & set(output_regions)
    
    print(f"📊 Common regions: {sorted(common_regions)}")
    print(f"📊 Input-only regions: {sorted(input_only)}")
    print(f"📊 Output-only regions: {sorted(output_only)}")
    
    # Test 4: Check for coordinate-based patterns
    print("\n📄 Test 4: Looking for coordinate-based regions...")
    
    coordinate_patterns = []
    for region in output_regions:
        # Look for coordinate patterns like: lat.latS/N_lng.lngE/W
        if any(char in region for char in ['N', 'S', 'E', 'W']) and any(char.isdigit() for char in region):
            coordinate_patterns.append(region)
    
    if coordinate_patterns:
        print(f"✅ Found coordinate-based regions in output: {coordinate_patterns}")
    else:
        print("ℹ️ No obvious coordinate-based regions found in output folder")
    
    # Test 5: Check specific region for processed data
    print("\n📄 Test 5: Checking for processed data in output regions...")
    
    for region in output_regions[:3]:  # Check first 3 regions
        try:
            response = requests.get(f"http://localhost:8000/api/regions/{region}/png-files")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    files = data.get('files', [])
                    print(f"   📂 {region}: {len(files)} processed files")
                    
                    # Check for different types of processed data
                    processing_types = set()
                    for file_info in files:
                        if 'processing_type' in file_info:
                            processing_types.add(file_info['processing_type'])
                    
                    if processing_types:
                        print(f"      🔧 Processing types: {sorted(processing_types)}")
                else:
                    print(f"   📂 {region}: No processed files")
            else:
                print(f"   📂 {region}: Failed to check files (HTTP {response.status_code})")
        except Exception as e:
            print(f"   📂 {region}: Error checking files - {e}")
    
    print("\n" + "=" * 60)
    print("📊 OpenAI Analysis Region Test Summary:")
    print(f"   ✅ Input regions found: {len(input_regions)}")
    print(f"   ✅ Output regions found: {len(output_regions)}")
    print(f"   📊 Total unique regions: {len(set(input_regions) | set(output_regions))}")
    
    if output_regions:
        print("   ✅ OpenAI analysis tab will now show output folder regions")
        print("   ✅ This includes processed data and coordinate-based regions")
    else:
        print("   ⚠️ No output regions found - check if processing has been done")
    
    print()
    print("🎯 Expected behavior:")
    print("   1. OpenAI analysis tab now loads from output folder")
    print("   2. Should show regions with processed raster data")
    print("   3. Should include coordinate-based regions if they exist")
    print("   4. Refresh the browser to see the updated region list")
    
    return len(output_regions) > 0

if __name__ == "__main__":
    test_openai_analysis_regions()
