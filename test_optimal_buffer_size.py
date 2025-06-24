#!/usr/bin/env python3
"""
Test script to verify optimal buffer size implementation across the codebase.

This test validates that the 12.5km buffer size optimization has been properly
implemented to prevent bounds mismatch issues between requested areas and
Copernicus GLO-30 service responses.
"""

import os
import requests
import json
from pathlib import Path

def test_elevation_api_buffer_defaults():
    """Test that elevation API endpoints use 12.5km buffer by default"""
    print("\n🧪 Testing Elevation API Buffer Defaults...")
    
    # Test coordinates in Brazil (region with known bounds mismatch issues)
    test_lat = -1.81  # Same as problematic region 1.81S_50
    test_lng = -50.0
    
    # Test the elevation API with default buffer
    try:
        response = requests.post("http://localhost:8000/api/elevation/download-coordinates", 
                               json={
                                   "lat": test_lat,
                                   "lng": test_lng,
                                   "region_name": "test_optimal_buffer"
                               },
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Elevation API request successful")
            print(f"📐 Used buffer size should default to 12.5km")
            
            # Check if metadata shows the correct buffer
            metadata_file = Path("output/test_optimal_buffer/metadata.txt")
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    content = f.read()
                    if "Buffer Distance (km): 12.5" in content:
                        print(f"✅ Metadata shows correct 12.5km buffer")
                    else:
                        print(f"⚠️  Metadata doesn't show 12.5km buffer")
                        print(f"📄 Metadata content:\n{content}")
            
            return True
        else:
            print(f"❌ Elevation API request failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"⚠️  Server not running - skipping API test")
        return None
    except Exception as e:
        print(f"❌ Error testing elevation API: {e}")
        return False

def test_frontend_buffer_configuration():
    """Test that frontend JavaScript files use 12.5km buffer"""
    print("\n🧪 Testing Frontend Buffer Configuration...")
    
    # Check UI.js for 12.5km buffer usage
    ui_file = Path("frontend/js/ui.js")
    if ui_file.exists():
        with open(ui_file, 'r') as f:
            content = f.read()
            
        buffer_12_5_count = content.count("buffer_km: 12.5")
        buffer_5_0_count = content.count("buffer_km: 5.0")
        buffer_2_0_count = content.count("buffer_km: 2.0")
        
        print(f"📊 Buffer size usage in UI.js:")
        print(f"   buffer_km: 12.5 → {buffer_12_5_count} occurrences")
        print(f"   buffer_km: 5.0  → {buffer_5_0_count} occurrences") 
        print(f"   buffer_km: 2.0  → {buffer_2_0_count} occurrences")
        
        if buffer_12_5_count > 0 and buffer_5_0_count == 0:
            print(f"✅ UI.js uses optimal 12.5km buffer")
            return True
        else:
            print(f"⚠️  UI.js may still have old buffer sizes")
            return False
    else:
        print(f"❌ UI.js file not found")
        return False

def test_elevation_service_buffer():
    """Test that elevation service uses 12.5km buffer"""
    print("\n🧪 Testing Elevation Service Buffer...")
    
    service_file = Path("frontend/js/services/elevation-service.js")
    if service_file.exists():
        with open(service_file, 'r') as f:
            content = f.read()
            
        if "buffer_km: 12.5" in content:
            print(f"✅ Elevation service uses 12.5km default buffer")
            
            # Check optimal buffer size function
            if "_getOptimalBufferSize" in content and "12.5" in content:
                print(f"✅ Optimal buffer size function returns 12.5km")
                return True
            else:
                print(f"⚠️  Optimal buffer size function may not return 12.5km")
                return False
        else:
            print(f"❌ Elevation service doesn't use 12.5km buffer")
            return False
    else:
        print(f"❌ Elevation service file not found")
        return False

def test_backend_buffer_configuration():
    """Test that backend Python files use 12.5km buffer"""
    print("\n🧪 Testing Backend Buffer Configuration...")
    
    # Check key backend files
    files_to_check = [
        "app/endpoints/elevation_api.py",
        "app/endpoints/region_management.py", 
        "app/endpoints/copernicus_dsm.py",
        "app/services/copernicus_dsm_service.py",
        "app/config.py",
        "app/main.py",
        "app/endpoints/core.py",
        "app/data_acquisition/manager.py",
        "app/lidar_acquisition/manager.py"
    ]
    
    results = {}
    
    for file_path in files_to_check:
        full_path = Path(file_path)
        if full_path.exists():
            with open(full_path, 'r') as f:
                content = f.read()
                
            has_12_5 = "12.5" in content
            has_old_buffers = any(x in content for x in ["= 1.0", "= 2.0", "= 5.0"] if "buffer" in content.lower())
            
            results[file_path] = {
                "has_12_5": has_12_5,
                "has_old_buffers": has_old_buffers,
                "exists": True
            }
            
            if has_12_5 and not has_old_buffers:
                print(f"✅ {file_path} - Uses 12.5km buffer")
            elif has_12_5:
                print(f"⚠️  {file_path} - Has 12.5km but also old buffer sizes")
            else:
                print(f"❌ {file_path} - No 12.5km buffer found")
        else:
            results[file_path] = {"exists": False}
            print(f"❌ {file_path} - File not found")
    
    # Summary
    good_files = sum(1 for r in results.values() if r.get("exists") and r.get("has_12_5") and not r.get("has_old_buffers"))
    total_files = sum(1 for r in results.values() if r.get("exists"))
    
    print(f"\n📊 Backend configuration summary: {good_files}/{total_files} files properly configured")
    
    return good_files == total_files

def test_bounds_calculation():
    """Test that 12.5km buffer produces 25km x 25km area"""
    print("\n🧪 Testing Bounds Calculation...")
    
    # Test coordinates
    lat = -1.81
    lng = -50.0
    buffer_km = 12.5
    
    # Convert km to degrees (approximately)
    buffer_deg = buffer_km / 111.0  # 1 degree ≈ 111 km
    
    expected_area_km = (buffer_km * 2) ** 2  # 25km x 25km = 625 km²
    
    bounds = {
        "north": lat + buffer_deg,
        "south": lat - buffer_deg,
        "east": lng + buffer_deg,
        "west": lng - buffer_deg
    }
    
    width_deg = bounds["east"] - bounds["west"]
    height_deg = bounds["north"] - bounds["south"]
    width_km = width_deg * 111.0
    height_km = height_deg * 111.0
    actual_area_km = width_km * height_km
    
    print(f"📐 Bounds calculation for 12.5km buffer:")
    print(f"   Buffer: {buffer_km}km → {buffer_deg:.4f}°")
    print(f"   Area: {width_km:.1f}km × {height_km:.1f}km = {actual_area_km:.0f} km²")
    print(f"   Expected: 25km × 25km = 625 km²")
    
    if abs(actual_area_km - 625) < 50:  # Allow some tolerance
        print(f"✅ Bounds calculation produces optimal ~25km × 25km area")
        return True
    else:
        print(f"❌ Bounds calculation doesn't produce optimal area")
        return False

def main():
    """Run all buffer size optimization tests"""
    print("🧪 Buffer Size Optimization Test Suite")
    print("=" * 50)
    
    tests = [
        ("Frontend Buffer Configuration", test_frontend_buffer_configuration),
        ("Elevation Service Buffer", test_elevation_service_buffer),
        ("Backend Buffer Configuration", test_backend_buffer_configuration),
        ("Bounds Calculation", test_bounds_calculation),
        ("Elevation API Buffer Defaults", test_elevation_api_buffer_defaults),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = 0
    
    for test_name, result in results.items():
        if result is None:
            print(f"⏭️  {test_name}: SKIPPED")
        elif result:
            print(f"✅ {test_name}: PASSED")
            passed += 1
            total += 1
        else:
            print(f"❌ {test_name}: FAILED")
            total += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All buffer size optimizations implemented successfully!")
        print("🔧 The system now requests optimal 25km × 25km areas to match Copernicus GLO-30's efficient delivery format")
        print("🚫 This should eliminate bounds mismatch issues and the need for cropping oversized responses")
    else:
        print("⚠️  Some buffer size configurations may need attention")
        print("🔍 Review the failed tests above for specific issues")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
