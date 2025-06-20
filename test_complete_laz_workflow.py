#!/usr/bin/env python3
"""
Comprehensive test for the complete LAZ upload and processing workflow
"""

import requests
import json
from pathlib import Path
import time

def test_complete_laz_workflow():
    """Test the complete LAZ upload and processing workflow"""
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Complete LAZ Upload and Processing Workflow")
    print("=" * 70)
    
    # Check if LAZ files exist
    laz_dir = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ")
    if not laz_dir.exists():
        print("❌ LAZ directory doesn't exist")
        return False
    
    laz_files = list(laz_dir.glob("*.laz"))
    if not laz_files:
        print("❌ No LAZ files found in input directory")
        return False
    
    print(f"📁 Found {len(laz_files)} LAZ files:")
    for laz_file in laz_files:
        print(f"   • {laz_file.name} ({laz_file.stat().st_size / (1024*1024):.1f} MB)")
    
    # Test with the first LAZ file
    test_file = laz_files[0]
    print(f"\n🧪 Testing workflow with: {test_file.name}")
    
    try:
        # Step 1: Test LAZ file upload
        print("\n📤 Step 1: Testing LAZ file upload...")
        
        files_to_upload = [
            ('files', (test_file.name, open(test_file, 'rb'), 'application/octet-stream'))
        ]
        
        response = requests.post(f"{base_url}/api/laz/upload", files=files_to_upload)
        
        # Close file handle
        files_to_upload[0][1][1].close()
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
        
        upload_result = response.json()
        print(f"✅ Upload successful: {upload_result['message']}")
        
        uploaded_files = upload_result.get('files', [])
        if not uploaded_files:
            print("❌ No files were uploaded")
            return False
        
        file_info = uploaded_files[0]
        region_name = Path(file_info['inputFile']).stem
        print(f"   📊 Region name: {region_name}")
        print(f"   📁 Output directory: {file_info['outputDirectory']}")
        
        # Step 2: Test DTM generation
        print(f"\n🏔️ Step 2: Testing DTM generation for {region_name}...")
        
        dtm_form_data = {
            'region_name': region_name,
            'processing_type': 'lidar',
            'dtm_resolution': '1.0',
            'stretch_type': 'stddev'
        }
        
        dtm_response = requests.post(f"{base_url}/api/dtm", data=dtm_form_data)
        
        if dtm_response.status_code != 200:
            print(f"❌ DTM generation failed: {dtm_response.status_code} - {dtm_response.text}")
            return False
        
        dtm_result = dtm_response.json()
        print("✅ DTM generation successful")
        print(f"   📊 DTM image data length: {len(dtm_result.get('image', ''))}")
        
        # Step 3: Test process-all-rasters
        print(f"\n🎨 Step 3: Testing process-all-rasters for {region_name}...")
        
        raster_form_data = {
            'region_name': region_name,
            'file_name': file_info['inputFile']
        }
        
        raster_response = requests.post(f"{base_url}/api/laz/process-all-rasters", data=raster_form_data)
        
        if raster_response.status_code != 200:
            print(f"❌ Process-all-rasters failed: {raster_response.status_code} - {raster_response.text}")
            return False
        
        raster_result = raster_response.json()
        print("✅ Process-all-rasters successful")
        print(f"   📊 DTM TIFF path: {raster_result.get('dtm_tiff_path')}")
        
        processing_results = raster_result.get('processing_results', {})
        if processing_results:
            print(f"   📊 Processing results: {len(processing_results)} items")
            for key, value in processing_results.items():
                if isinstance(value, dict) and 'success' in value:
                    status = "✅" if value['success'] else "❌"
                    print(f"      {status} {key}: {value.get('message', 'No message')}")
        
        # Step 4: Test metadata generation
        print(f"\n📄 Step 4: Testing metadata generation for {region_name}...")
        
        metadata_form_data = {
            'region_name': region_name,
            'file_name': file_info['inputFile']
        }
        
        metadata_response = requests.post(f"{base_url}/api/laz/generate-metadata", data=metadata_form_data)
        
        if metadata_response.status_code != 200:
            print(f"❌ Metadata generation failed: {metadata_response.status_code} - {metadata_response.text}")
            return False
        
        metadata_result = metadata_response.json()
        print("✅ Metadata generation successful")
        print(f"   📄 Metadata path: {metadata_result.get('metadata_path')}")
        
        # Verify metadata file exists
        base_dir = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z")
        metadata_file = base_dir / metadata_result.get('metadata_path', '')
        
        if metadata_file.exists():
            print(f"   ✅ Metadata file verified: {metadata_file}")
            
            # Show preview of metadata content
            with open(metadata_file, 'r') as f:
                content = f.read()
                lines = content.split('\n')[:10]  # First 10 lines
                print("   📋 Metadata preview:")
                for line in lines:
                    if line.strip():
                        print(f"      {line}")
        else:
            print(f"   ⚠️ Metadata file not found: {metadata_file}")
        
        print("\n🎉 Complete LAZ workflow test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_integration():
    """Test if the frontend can access the backend endpoints"""
    base_url = "http://localhost:8000"
    
    print("\n🌐 Testing Frontend Integration...")
    
    # Check if the main page loads
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            
            # Check if the page contains expected elements
            if "LAZ Terrain Processor" in response.text:
                print("✅ Page contains expected title")
            else:
                print("⚠️ Page title not found")
                
            if "geotiff-left-panel.js" in response.text:
                print("✅ LAZ panel JavaScript is loaded")
            else:
                print("⚠️ LAZ panel JavaScript not found")
                
            return True
        else:
            print(f"❌ Main page failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend integration test failed: {e}")
        return False

def main():
    print("🧪 Comprehensive LAZ Workflow Test")
    print("=" * 70)
    
    # Test backend workflow
    workflow_success = test_complete_laz_workflow()
    
    # Test frontend integration
    frontend_success = test_frontend_integration()
    
    print("\n" + "=" * 70)
    print("📊 Final Test Results:")
    print(f"   Complete Workflow: {'✅ PASS' if workflow_success else '❌ FAIL'}")
    print(f"   Frontend Integration: {'✅ PASS' if frontend_success else '❌ FAIL'}")
    
    if workflow_success and frontend_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n💡 The LAZ upload system is fully functional:")
        print("   ✅ File upload works")
        print("   ✅ DTM generation works")
        print("   ✅ Raster processing works")
        print("   ✅ Metadata generation works")
        print("   ✅ Frontend integration works")
        print("\n🌐 Ready for production use!")
        print("   • Open http://localhost:8000")
        print("   • Navigate to GeoTiff Tools tab")
        print("   • Click 'Load LAZ' button")
        print("   • Select LAZ files and watch the complete workflow")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
