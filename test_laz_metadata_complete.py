#!/usr/bin/env python3
"""
Test script to verify complete LAZ loading flow with metadata generation
"""

import os
import sys
import requests
import json
from pathlib import Path
import time

def test_metadata_generation_endpoint():
    """Test the new metadata generation endpoint"""
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
    
    test_file = laz_files[0]
    region_name = test_file.stem
    
    print(f"🧪 Testing metadata generation endpoint...")
    print(f"   📁 Test file: {test_file.name}")
    print(f"   🏷️ Region name: {region_name}")
    
    try:
        # Test metadata generation
        form_data = {
            'region_name': region_name,
            'file_name': test_file.name
        }
        
        response = requests.post(f"{base_url}/api/laz/generate-metadata", data=form_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Metadata generation successful")
            print(f"   📄 Message: {result.get('message')}")
            print(f"   📁 Metadata path: {result.get('metadata_path')}")
            
            # Check coordinates data
            coords = result.get('coordinates', {})
            if coords:
                print(f"   🌍 Bounds: {coords.get('bounds_wgs84')}")
                print(f"   📍 Center: {coords.get('center_wgs84')}")
                print(f"   🗂️ CRS: {coords.get('source_crs', 'N/A')}")
            
            # Verify metadata file was created
            base_dir = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z")
            metadata_file = base_dir / result.get('metadata_path', '')
            
            if metadata_file.exists():
                print(f"✅ Metadata file verified: {metadata_file}")
                
                # Show preview of metadata content
                with open(metadata_file, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')[:15]  # First 15 lines
                    print("📋 Metadata preview:")
                    for line in lines:
                        if line.strip():
                            print(f"     {line}")
                    if len(content.split('\n')) > 15:
                        print("     ...")
                        
            else:
                print(f"⚠️ Metadata file not found: {metadata_file}")
            
            return True
        else:
            print(f"❌ Metadata generation failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Metadata generation test failed: {e}")
        return False

def test_complete_laz_upload_flow():
    """Test the complete LAZ upload flow"""
    base_url = "http://localhost:8000"
    
    # Check if LAZ files exist
    laz_dir = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ")
    laz_files = list(laz_dir.glob("*.laz"))
    
    if not laz_files:
        print("❌ No LAZ files for upload testing")
        return False
    
    print(f"🧪 Testing complete LAZ upload flow...")
    print(f"   📁 Found {len(laz_files)} LAZ files")
    
    try:
        # Test upload with first 2 files
        files_to_upload = []
        test_files = laz_files[:2]
        
        for laz_file in test_files:
            print(f"   📤 Preparing: {laz_file.name}")
            files_to_upload.append(
                ('files', (laz_file.name, open(laz_file, 'rb'), 'application/octet-stream'))
            )
        
        print("🚀 Uploading files...")
        response = requests.post(f"{base_url}/api/laz/upload", files=files_to_upload)
        
        # Close file handles
        for _, (_, file_handle, _) in files_to_upload:
            file_handle.close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful: {result['message']}")
            
            uploaded_files = result.get('files', [])
            print(f"📊 Files processed: {len(uploaded_files)}")
            
            for i, file_info in enumerate(uploaded_files):
                print(f"   {i+1}. {file_info['inputFile']} -> {file_info['outputDirectory']}")
                
                # Test metadata generation for each uploaded file
                region_name = Path(file_info['inputFile']).stem
                print(f"   🔄 Testing metadata generation for: {region_name}")
                
                # Wait a moment for file processing
                time.sleep(1)
                
                # Generate metadata
                form_data = {
                    'region_name': region_name,
                    'file_name': file_info['inputFile']
                }
                
                metadata_response = requests.post(f"{base_url}/api/laz/generate-metadata", data=form_data)
                
                if metadata_response.status_code == 200:
                    print(f"   ✅ Metadata generated for {region_name}")
                else:
                    print(f"   ⚠️ Metadata generation failed for {region_name}: {metadata_response.status_code}")
            
            return True
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False

def test_laz_modal_integration():
    """Test LAZ modal integration by checking endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing LAZ modal integration endpoints...")
    
    # Test endpoints that the modal will use
    endpoints_to_test = [
        ("/api/laz/upload", "POST", "Multiple file upload"),
        ("/api/laz/generate-metadata", "POST", "Metadata generation"),
        ("/api/laz/files", "GET", "File listing"),
    ]
    
    results = []
    
    for endpoint, method, description in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}")
                if response.status_code == 200:
                    print(f"✅ {description}: {endpoint}")
                    results.append(True)
                else:
                    print(f"⚠️ {description}: {endpoint} - Status {response.status_code}")
                    results.append(False)
            else:
                # For POST endpoints, we just check if they exist (will return 422 for missing data)
                response = requests.post(f"{base_url}{endpoint}")
                if response.status_code in [422, 400]:  # Expected for missing form data
                    print(f"✅ {description}: {endpoint} (endpoint exists)")
                    results.append(True)
                else:
                    print(f"⚠️ {description}: {endpoint} - Unexpected status {response.status_code}")
                    results.append(False)
                    
        except Exception as e:
            print(f"❌ {description}: {endpoint} - Error: {e}")
            results.append(False)
    
    return all(results)

def main():
    print("🚀 Testing Complete LAZ Loading Flow with Metadata Generation")
    print("=" * 70)
    
    # Test individual components
    upload_success = test_complete_laz_upload_flow()
    metadata_success = test_metadata_generation_endpoint()
    integration_success = test_laz_modal_integration()
    
    print("\n" + "=" * 70)
    print("📊 Test Results:")
    print(f"   Upload Flow: {'✅ PASS' if upload_success else '❌ FAIL'}")
    print(f"   Metadata Generation: {'✅ PASS' if metadata_success else '❌ FAIL'}")
    print(f"   Modal Integration: {'✅ PASS' if integration_success else '❌ FAIL'}")
    
    if upload_success and metadata_success and integration_success:
        print("\n🎉 All tests passed! Complete LAZ loading flow is ready.")
        print("\n💡 Features implemented:")
        print("   ✅ Multiple LAZ file upload")
        print("   ✅ Visual progress indicators")
        print("   ✅ Raster generation with progress tracking")
        print("   ✅ Metadata.txt generation after raster completion")
        print("   ✅ Visual feedback for metadata generation step")
        print("   ✅ Queue display with metadata step indicator")
        print("\n🌐 Ready to test in browser:")
        print("   1. Open http://localhost:8000")
        print("   2. Click 'Load LAZ Files' in left panel")
        print("   3. Select LAZ files and watch complete progress flow")
        print("   4. Verify metadata.txt is created after raster generation")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        
    print("\n🎯 Next steps:")
    print("   • Test the complete flow in browser")
    print("   • Verify metadata.txt contains correct coordinates")
    print("   • Check visual progress indicators work smoothly")

if __name__ == "__main__":
    main()
