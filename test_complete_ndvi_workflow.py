#!/usr/bin/env python3
"""
Complete NDVI Workflow Test
Tests the complete NDVI workflow including both LAZ file and folder modals
"""

import requests
import json
from pathlib import Path
import tempfile

def test_complete_ndvi_folder_workflow():
    """Test complete NDVI workflow starting from folder modal"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Complete NDVI Folder Workflow...")
    
    # Create test LAZ files to simulate folder upload
    test_files = []
    test_content = b"Test LAZ file content for NDVI folder testing"
    
    try:
        # Test the upload endpoint with NDVI parameter (simulating folder workflow)
        files_data = []
        for i in range(2):  # Create 2 test files
            files_data.append(('files', (f'folder_test_{i}.laz', test_content, 'application/octet-stream')))
        
        form_data = {
            'ndvi_enabled': 'true'  # This should come from folder modal checkbox
        }
        
        response = requests.post(f"{base_url}/api/laz/upload", files=files_data, data=form_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Folder workflow LAZ upload with NDVI successful")
            print(f"   📁 Uploaded files: {len(result.get('files', []))}")
            
            # Verify settings files were created for each LAZ file
            laz_input_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ")
            settings_found = 0
            
            for i in range(2):
                settings_file = laz_input_path / f"folder_test_{i}.settings.json"
                if settings_file.exists():
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                    if settings.get('ndvi_enabled', False):
                        settings_found += 1
            
            if settings_found == 2:
                print("✅ All settings files created with NDVI enabled")
                return True
            else:
                print(f"❌ Only {settings_found}/2 settings files found with NDVI enabled")
                return False
        else:
            print(f"❌ Folder workflow upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing folder workflow: {e}")
        return False

def verify_modal_html_structure():
    """Verify both modals have proper NDVI checkbox structure"""
    print("🧪 Verifying Modal HTML Structure...")
    
    # Check LAZ file modal
    file_modal_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/frontend/modules/modals/laz-file-modal.html")
    folder_modal_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/frontend/modules/modals/laz-folder-modal.html")
    
    try:
        # Read both modal files
        with open(file_modal_path, 'r') as f:
            file_modal_content = f.read()
        
        with open(folder_modal_path, 'r') as f:
            folder_modal_content = f.read()
        
        # Verify file modal has NDVI checkbox
        file_modal_checks = [
            'id="laz-ndvi-enabled"' in file_modal_content,
            'NDVI Enabled' in file_modal_content,
            'Enable NDVI processing' in file_modal_content
        ]
        
        # Verify folder modal has NDVI checkbox
        folder_modal_checks = [
            'id="laz-folder-ndvi-enabled"' in folder_modal_content,
            'NDVI Enabled' in folder_modal_content,
            'Enable NDVI processing' in folder_modal_content
        ]
        
        if all(file_modal_checks) and all(folder_modal_checks):
            print("✅ Both modals have proper NDVI checkbox structure")
            print("   📄 File modal: laz-ndvi-enabled checkbox present")
            print("   📁 Folder modal: laz-folder-ndvi-enabled checkbox present")
            return True
        else:
            print("❌ Modal structure issues found")
            if not all(file_modal_checks):
                print("   📄 File modal missing NDVI elements")
            if not all(folder_modal_checks):
                print("   📁 Folder modal missing NDVI elements")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying modal structure: {e}")
        return False

def verify_javascript_integration():
    """Verify JavaScript properly handles NDVI in both workflows"""
    print("🧪 Verifying JavaScript Integration...")
    
    js_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/frontend/js/geotiff-left-panel.js")
    
    try:
        with open(js_path, 'r') as f:
            js_content = f.read()
        
        # Check for key integration points
        integration_checks = [
            # Folder modal NDVI capture
            "document.getElementById('laz-folder-ndvi-enabled')" in js_content,
            "folderNdviEnabled" in js_content,
            
            # Transfer between modals
            "fileNdviCheckbox.checked = folderNdviEnabled" in js_content,
            "Transferred NDVI setting to file modal" in js_content,
            
            # File modal NDVI capture for upload
            "document.getElementById('laz-ndvi-enabled')" in js_content,
            "formData.append('ndvi_enabled'" in js_content,
            
            # Logging for debugging
            "Folder NDVI enabled:" in js_content,
            "NDVI enabled:" in js_content
        ]
        
        passed_checks = sum(integration_checks)
        total_checks = len(integration_checks)
        
        if passed_checks == total_checks:
            print("✅ JavaScript integration complete")
            print(f"   ✓ All {total_checks}/{total_checks} integration points found")
            return True
        else:
            print(f"❌ JavaScript integration incomplete: {passed_checks}/{total_checks} checks passed")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying JavaScript integration: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    print("🧹 Cleaning up test files...")
    
    laz_input_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ")
    cleaned = 0
    
    # Remove test LAZ files and settings
    for i in range(2):
        test_laz = laz_input_path / f"folder_test_{i}.laz"
        test_settings = laz_input_path / f"folder_test_{i}.settings.json"
        
        if test_laz.exists():
            test_laz.unlink()
            cleaned += 1
        
        if test_settings.exists():
            test_settings.unlink()
            cleaned += 1
    
    print(f"   ✅ Cleaned {cleaned} test files")

def main():
    """Run complete NDVI workflow tests"""
    print("🎯 Complete NDVI Workflow Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test 1: Modal HTML structure
    results.append(("Modal HTML Structure", verify_modal_html_structure()))
    
    # Test 2: JavaScript integration
    results.append(("JavaScript Integration", verify_javascript_integration()))
    
    # Test 3: Complete folder workflow
    results.append(("Complete Folder Workflow", test_complete_ndvi_folder_workflow()))
    
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
        print("🎉 Complete NDVI workflow implemented successfully!")
        print("   📁 Folder modal → File modal → Backend upload all working")
        print("   🌿 NDVI setting preserved throughout entire workflow")
    else:
        print("⚠️ Some workflow tests failed. Check the implementation.")
    
    # Cleanup
    cleanup_test_files()

if __name__ == "__main__":
    main()
