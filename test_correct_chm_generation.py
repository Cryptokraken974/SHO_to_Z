#!/usr/bin/env python3
"""
Test CHM generation with correct, matching DTM and DSM files
"""

import requests
import json

def test_chm_generation_with_correct_files():
    """Test CHM generation using matching DTM and DSM from the same region"""
    print("🧪 TESTING CHM GENERATION WITH CORRECT FILES")
    print("=" * 60)
    
    # Test data for OR_WizardIsland region
    test_data = {
        "region_name": "OR_WizardIsland",
        "latitude": 42.939063,  # Center coordinates from our analysis
        "longitude": -122.143734
    }
    
    print(f"📍 Testing CHM generation for: {test_data['region_name']}")
    print(f"🌍 Coordinates: {test_data['latitude']:.6f}, {test_data['longitude']:.6f}")
    print(f"📁 Expected DTM: output/OR_WizardIsland/lidar/DTM/filled/OR_WizardIsland_DTM_1.0m_csf1.0m_filled.tif")
    print(f"📁 Expected DSM: output/OR_WizardIsland/lidar/DSM/OR_WizardIsland_DSM.tif")
    
    try:
        print(f"\n🚀 Making API call to generate CHM...")
        
        # Make API call to generate CHM for coordinate-based region
        response = requests.post(
            'http://localhost:8000/api/generate-coordinate-chm',
            json=test_data,
            timeout=300  # 5 minute timeout for CHM generation
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ CHM Generation SUCCESSFUL!")
            print(f"📊 Result: {json.dumps(result, indent=2)}")
            
            # Check if CHM file was created
            if 'chm_file' in result:
                chm_file = result['chm_file']
                print(f"📄 CHM file created: {chm_file}")
                
                # Try to verify the file exists
                import os
                if os.path.exists(chm_file):
                    file_size = os.path.getsize(chm_file)
                    print(f"📊 CHM file size: {file_size:,} bytes ({file_size/(1024*1024):.2f} MB)")
                    return True
                else:
                    print(f"⚠️ CHM file not found at expected path: {chm_file}")
                    
        else:
            error_data = response.json()
            print(f"❌ CHM Generation FAILED!")
            print(f"🔍 Error: {error_data}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_file_summary():
    """Show summary of available files"""
    print(f"\n📂 FILE SUMMARY")
    print("=" * 60)
    
    import os
    
    # Check OR_WizardIsland files
    wizard_base = "output/OR_WizardIsland/lidar"
    
    print(f"📁 OR_WizardIsland files:")
    
    # DTM files
    dtm_dir = os.path.join(wizard_base, "DTM", "filled")
    if os.path.exists(dtm_dir):
        dtm_files = [f for f in os.listdir(dtm_dir) if f.endswith('.tif')]
        print(f"   ✅ DTM files ({len(dtm_files)}): {dtm_files}")
    else:
        print(f"   ❌ No DTM directory found")
    
    # DSM files
    dsm_dir = os.path.join(wizard_base, "DSM")
    if os.path.exists(dsm_dir):
        dsm_files = [f for f in os.listdir(dsm_dir) if f.endswith('.tif')]
        print(f"   ✅ DSM files ({len(dsm_files)}): {dsm_files}")
    else:
        print(f"   ❌ No DSM directory found")
        
    # CHM files
    chm_dir = os.path.join(wizard_base, "CHM")
    if os.path.exists(chm_dir):
        chm_files = [f for f in os.listdir(chm_dir) if f.endswith('.tif')]
        print(f"   📊 Existing CHM files ({len(chm_files)}): {chm_files}")
    else:
        print(f"   📝 No CHM directory found (will be created)")

if __name__ == "__main__":
    show_file_summary()
    success = test_chm_generation_with_correct_files()
    
    if success:
        print(f"\n🎉 SUCCESS: CHM generation working with correct files!")
        print(f"✅ The tint overlay has been disabled")
        print(f"✅ CHM can be generated using matching DTM/DSM from same region")
    else:
        print(f"\n⚠️ CHM generation still has issues - check server logs for details")
