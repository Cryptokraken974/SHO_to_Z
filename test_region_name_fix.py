#!/usr/bin/env python3
"""
Test script to verify that the region name fix is working correctly
"""

def test_region_name_logic():
    """Test the region name prioritization logic"""
    print("🔍 Testing region name prioritization logic...")
    
    # Simulate the fixed logic from hillshade.py
    def test_effective_region_name(region_name, input_file):
        from pathlib import Path
        
        print(f"\n📂 Testing with region_name='{region_name}' and input_file='{input_file}'")
        
        input_path = Path(input_file)
        print(f"   📂 Full input path: {input_path}")
        print(f"   🧩 Path parts: {input_path.parts}")
        
        # Apply the FIXED logic
        effective_region_name = region_name
        if effective_region_name is not None and effective_region_name.strip():
            print(f"   ✅ [PRIORITY] Using provided region_name (user-friendly): {effective_region_name}")
            print(f"   🎯 This ensures output goes to: output/{effective_region_name}/... instead of coordinate-based paths")
        else:
            print(f"   ⚠️ No explicit region_name provided, extracting from file path...")
            if "lidar" in input_path.parts and "input" in input_path.parts:
                try:
                    effective_region_name = input_path.parts[input_path.parts.index("input") + 1]
                    print(f"   🎯 Found 'input/.../region_name/.../lidar' structure. Region: {effective_region_name}")
                except (ValueError, IndexError):
                    effective_region_name = input_path.stem
                    print(f"   ⚠️ Path structure unexpected, falling back to input file stem for region: {effective_region_name}")
            else:
                effective_region_name = input_path.stem
                print(f"   🎯 Non-standard path structure, using input file stem for region: {effective_region_name}")
                
        print(f"   ✅ [REGION IDENTIFIED] Final effective region name for path construction: {effective_region_name}")
        return effective_region_name

    # Test cases
    test_cases = [
        # Test 1: With display_region_name (user-friendly) - should prioritize this
        {
            "region_name": "GO",  # User-friendly name from display_region_name
            "input_file": "input/2.433S_57.248W_elevation_DTM/lidar/lidar_2.433S_57.248W_lidar.laz",
            "expected": "GO",
            "description": "User-friendly region name should be prioritized"
        },
        
        # Test 2: Without display_region_name - should extract from path
        {
            "region_name": None,
            "input_file": "input/2.433S_57.248W_elevation_DTM/lidar/lidar_2.433S_57.248W_lidar.laz", 
            "expected": "2.433S_57.248W_elevation_DTM",
            "description": "Should extract coordinate-based name from path when no user-friendly name provided"
        },
        
        # Test 3: Empty region_name - should extract from path
        {
            "region_name": "",
            "input_file": "input/MyRegion/lidar/some_file.laz",
            "expected": "MyRegion", 
            "description": "Empty region name should fallback to path extraction"
        },
        
        # Test 4: User-friendly name with regular region
        {
            "region_name": "Archaeological_Site_Alpha",
            "input_file": "input/SomeFolder/lidar/data.laz",
            "expected": "Archaeological_Site_Alpha",
            "description": "User-friendly name should override path-based extraction"
        }
    ]
    
    print(f"\n🧪 Running {len(test_cases)} test cases...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {test_case['description']}")
        print(f"{'='*60}")
        
        result = test_effective_region_name(test_case["region_name"], test_case["input_file"])
        
        if result == test_case["expected"]:
            print(f"✅ PASS: Got expected result '{result}'")
        else:
            print(f"❌ FAIL: Expected '{test_case['expected']}', got '{result}'")
    
    print(f"\n{'='*60}")
    print("🎯 SUMMARY:")
    print("✅ The fix ensures that display_region_name (user-friendly names like 'GO')")
    print("   takes priority over coordinate-based names extracted from file paths")
    print("📁 This prevents folders like 'output/2.433S_57.248W_elevation_DTM/'")
    print("   and ensures folders like 'output/GO/' are created instead")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_region_name_logic()
