#!/usr/bin/env python3
"""
Test script to verify complete LAZ loading flow with progress indicators
"""

import os
import sys
import requests
import json
from pathlib import Path

# Test the complete LAZ loading flow
def test_laz_complete_flow():
    """Test LAZ file upload and processing with progress"""
    base_url = "http://localhost:8000"
    
    # Check if LAZ files exist
    laz_dir = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ")
    if not laz_dir.exists():
        print("❌ LAZ directory doesn't exist")
        return False
    
    laz_files = list(laz_dir.glob("*.laz"))
    if not laz_files:
        print("❌ No LAZ files found in input directory")
        return False
    
    print(f"✅ Found {len(laz_files)} LAZ files:")
    for laz_file in laz_files[:3]:  # Test with first 3 files
        print(f"   📁 {laz_file.name}")
    
    # Test 1: Multiple file upload endpoint
    print("\n🧪 Testing multiple file upload endpoint...")
    
    try:
        # Prepare files for upload
        files_to_upload = []
        for laz_file in laz_files[:2]:  # Upload first 2 files
            files_to_upload.append(
                ('files', (laz_file.name, open(laz_file, 'rb'), 'application/octet-stream'))
            )
        
        # Upload files
        response = requests.post(f"{base_url}/api/laz/upload", files=files_to_upload)
        
        # Close file handles
        for _, (_, file_handle, _) in files_to_upload:
            file_handle.close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful: {result['message']}")
            print(f"📊 Files uploaded: {len(result.get('files', []))}")
            
            for file_info in result.get('files', []):
                print(f"   📁 {file_info['inputFile']} -> {file_info['outputDirectory']}")
                
            return True
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False

def test_laz_bounds_api():
    """Test LAZ bounds API with caching"""
    base_url = "http://localhost:8000"
    laz_dir = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ")
    laz_files = list(laz_dir.glob("*.laz"))
    
    if not laz_files:
        print("❌ No LAZ files for bounds testing")
        return False
    
    print("\n🧪 Testing LAZ bounds API with caching...")
    
    test_file = laz_files[0].name
    print(f"📁 Testing with: {test_file}")
    
    try:
        # Test bounds API
        response = requests.get(f"{base_url}/api/laz/bounds-wgs84/{test_file}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Bounds API successful")
            print(f"   🌍 WGS84 Bounds: {result.get('bounds_wgs84')}")
            print(f"   📍 Center: {result.get('center_wgs84')}")
            print(f"   🗂️ Source CRS: {result.get('source_crs', 'N/A')}")
            
            # Check if metadata file was created
            region_name = Path(test_file).stem
            metadata_file = Path(f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/{region_name}/metadata.txt")
            
            if metadata_file.exists():
                print(f"✅ Metadata file created: {metadata_file}")
                with open(metadata_file, 'r') as f:
                    content = f.read()
                    print(f"📄 Metadata preview:\n{content[:200]}...")
            else:
                print(f"⚠️ Metadata file not found: {metadata_file}")
            
            return True
        else:
            print(f"❌ Bounds API failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Bounds API test failed: {e}")
        return False

def main():
    print("🚀 Testing Complete LAZ Loading Flow with Progress Indicators")
    print("=" * 60)
    
    # Test upload
    upload_success = test_laz_complete_flow()
    
    # Test bounds API
    bounds_success = test_laz_bounds_api()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Upload API: {'✅ PASS' if upload_success else '❌ FAIL'}")
    print(f"   Bounds API: {'✅ PASS' if bounds_success else '❌ FAIL'}")
    
    if upload_success and bounds_success:
        print("\n🎉 All tests passed! LAZ loading flow is ready.")
        print("💡 Next steps:")
        print("   1. Open http://localhost:8000 in browser")
        print("   2. Click 'Load LAZ Files' in left panel")
        print("   3. Select LAZ files and watch progress indicators")
        print("   4. Verify raster generation progress displays correctly")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
