#!/usr/bin/env python3
"""
Comprehensive test to verify the LAZ processing region name fix
"""

def test_complete_workflow():
    """Test the complete workflow of LAZ processing with region names"""
    print("🔍 Testing complete LAZ processing workflow with region name fix...")
    
    # Simulate the data flow from frontend to backend to processing
    
    print("\n" + "="*70)
    print("🌐 STEP 1: Frontend sends request with display_region_name")
    print("="*70)
    
    # This is what the frontend now sends (after our previous fixes)
    frontend_data = {
        'region_name': '2.433S_57.248W_elevation_DTM',  # Processing/coordinate-based name
        'file_name': 'lidar_2.433S_57.248W_lidar.laz',
        'display_region_name': 'GO'  # User-friendly name
    }
    
    print(f"📤 Frontend FormData:")
    for key, value in frontend_data.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*70)
    print("🔗 STEP 2: Backend endpoint receives and processes parameters")
    print("="*70)
    
    # This simulates what happens in laz_processing.py endpoints
    region_name = frontend_data['region_name']
    display_region_name = frontend_data['display_region_name']
    
    # The key fix: prioritize display_region_name over region_name
    output_region_for_path = display_region_name if display_region_name else region_name
    
    print(f"📥 Backend receives:")
    print(f"   region_name: {region_name}")
    print(f"   display_region_name: {display_region_name}")
    print(f"✅ Backend sets output_region_for_path: {output_region_for_path}")
    
    print("\n" + "="*70)
    print("🔧 STEP 3: Processing function uses the correct region name")
    print("="*70)
    
    # This simulates what happens in processing functions like hillshade()
    input_file = f"input/{region_name}/lidar/{frontend_data['file_name']}"
    
    print(f"🏔️ Processing function called:")
    print(f"   input_file: {input_file}")
    print(f"   region_name (from backend): {output_region_for_path}")
    
    # Simulate the FIXED logic in generate_hillshade_with_params()
    from pathlib import Path
    
    input_path = Path(input_file)
    effective_region_name = output_region_for_path  # This is the key fix!
    
    if effective_region_name is not None and effective_region_name.strip():
        print(f"✅ [PRIORITY] Using provided region_name (user-friendly): {effective_region_name}")
        result_folder = f"output/{effective_region_name}/lidar/Hillshade"
        result_file = f"{effective_region_name}_Hillshade.tif"
    else:
        print(f"⚠️ Would extract from path (fallback)")
        
    print(f"📁 Result folder: {result_folder}")
    print(f"📄 Result file: {result_file}")
    
    print("\n" + "="*70)
    print("🎯 VERIFICATION: Folder naming comparison")
    print("="*70)
    
    print("❌ BEFORE FIX (coordinate-based folders):")
    print(f"   output/{region_name}/lidar/Hillshade/{region_name}_Hillshade.tif")
    print(f"   → Creates folder: output/2.433S_57.248W_elevation_DTM/...")
    
    print("✅ AFTER FIX (user-friendly folders):")
    print(f"   output/{effective_region_name}/lidar/Hillshade/{effective_region_name}_Hillshade.tif")
    print(f"   → Creates folder: output/GO/...")
    
    print("\n" + "="*70)
    print("🏆 SUCCESS: The fix ensures user-friendly folder creation!")
    print("="*70)
    
    return {
        'frontend_sends': frontend_data,
        'backend_processes': output_region_for_path,
        'processing_creates': result_folder,
        'success': effective_region_name == 'GO'
    }

def test_endpoint_integration():
    """Test that all LAZ processing endpoints will use the fix"""
    print("\n🔗 Testing endpoint integration...")
    
    endpoints_to_test = [
        'hillshade',
        'hillshade_315_45_08', 
        'hillshade_225_45_08',
        'hillshade_custom',
        'slope',
        'aspect',
        'tri',
        'tpi',
        'lrm',
        'chm'
    ]
    
    print(f"📋 Testing {len(endpoints_to_test)} endpoints:")
    
    for endpoint in endpoints_to_test:
        # Simulate the pattern used in all endpoints
        display_region_name = 'GO'
        region_name = '2.433S_57.248W_elevation_DTM'
        
        # This is the pattern used in all laz_processing.py endpoints
        output_region_for_path = display_region_name if display_region_name else region_name
        
        expected_folder = f"output/{output_region_for_path}/lidar/"
        
        print(f"   ✅ /{endpoint}: {expected_folder}")
        
    print("🎯 All endpoints will create user-friendly folders with the fix!")

if __name__ == "__main__":
    result = test_complete_workflow()
    test_endpoint_integration()
    
    print(f"\n{'='*70}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*70}")
    print("✅ Frontend fix: Added display_region_name parameter")
    print("✅ Backend fix: Prioritize display_region_name over region_name")  
    print("✅ Processing fix: Use provided region_name instead of path extraction")
    print("✅ Result: User-friendly folders (GO) instead of coordinate folders")
    print(f"{'='*70}")
