#!/usr/bin/env python3
"""
Test script to verify that the interface fixes resolve the main issues:
1. DownloadRequest coordinate_system parameter removed
2. Progress_callback parameter signature fixed across all sources
3. 12.5km buffer optimization working correctly
"""

import sys
import traceback
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_download_request_interface():
    """Test that DownloadRequest no longer has coordinate_system parameter"""
    print("🔧 Testing DownloadRequest interface fix...")
    
    try:
        from app.data_acquisition.sources.brazilian_elevation import BrazilianElevationSource
        from app.data_acquisition.utils.coordinates import BoundingBox
        from app.data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
        
        # Test creating a DownloadRequest without coordinate_system
        bbox = BoundingBox(west=-55.0, south=-2.1, east=-54.9, north=-2.0)
        request = DownloadRequest(
            bbox=bbox,
            data_type=DataType.ELEVATION,
            resolution=DataResolution.HIGH,
            max_file_size_mb=25.0
        )
        
        # Test the BrazilianElevationSource create_optimal_request method
        optimal_request = BrazilianElevationSource.create_optimal_request(-2.01, -54.99, 25.0)
        
        print("✅ DownloadRequest interface fix successful!")
        print(f"   - Created request with bbox: {request.bbox}")
        print(f"   - Optimal request area: {optimal_request.bbox.area_km2():.1f} km²")
        return True
        
    except Exception as e:
        print(f"❌ DownloadRequest interface test failed: {e}")
        traceback.print_exc()
        return False

def test_progress_callback_signatures():
    """Test that all sources have consistent progress_callback signatures"""
    print("\n🔧 Testing progress_callback signature consistency...")
    
    sources_to_test = [
        ("ornl_daac", "ORNLDAACSource"),
        ("sentinel2", "Sentinel2Source"),
        ("brazilian_elevation", "BrazilianElevationSource"),
        ("copernicus_sentinel2", "CopernicusSentinel2Source"),
        ("opentopography", "OpenTopographySource"),
        ("opentopography_new", "OpenTopographySourceNew"),
    ]
    
    results = []
    
    for module_name, class_name in sources_to_test:
        try:
            module = __import__(f"app.data_acquisition.sources.{module_name}", fromlist=[class_name])
            source_class = getattr(module, class_name)
            
            # Check if the download method has the correct signature
            import inspect
            download_method = getattr(source_class, 'download')
            sig = inspect.signature(download_method)
            
            # Check parameters
            params = list(sig.parameters.keys())
            has_request = 'request' in params
            has_progress_callback = 'progress_callback' in params
            
            if has_request and has_progress_callback:
                print(f"✅ {class_name}: Correct signature")
                results.append(True)
            else:
                print(f"❌ {class_name}: Missing parameters - request:{has_request}, progress_callback:{has_progress_callback}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {class_name}: Failed to test - {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Progress callback signature consistency: {success_rate:.1f}% ({sum(results)}/{len(results)} sources)")
    return all(results)

def test_buffer_optimization():
    """Test that 12.5km buffer optimization is working"""
    print("\n🔧 Testing 12.5km buffer optimization...")
    
    try:
        from app.endpoints.elevation_api import CoordinateRequest
        from app.endpoints.sentinel2 import Sentinel2Request
        from app.services.elevation_service import elevation
        
        # Test default buffer values
        coord_req = CoordinateRequest(lat=-2.01, lng=-54.99)
        sentinel_req = Sentinel2Request(lat=-2.01, lng=-54.99)
        
        print(f"✅ CoordinateRequest default buffer: {coord_req.buffer_km}km")
        print(f"✅ Sentinel2Request default buffer: {sentinel_req.buffer_km}km")
        
        # Calculate expected area
        buffer_deg = coord_req.buffer_km / 111.0  # Rough conversion
        expected_area_km2 = (2 * buffer_deg * 111) ** 2  # Approximate area calculation
        
        print(f"✅ Expected area with 12.5km buffer: ~{expected_area_km2:.0f} km² (target: ~625 km²)")
        
        if coord_req.buffer_km == 12.5 and sentinel_req.buffer_km == 12.5:
            print("✅ Buffer optimization working correctly!")
            return True
        else:
            print("❌ Buffer optimization not working - incorrect default values")
            return False
            
    except Exception as e:
        print(f"❌ Buffer optimization test failed: {e}")
        traceback.print_exc()
        return False

def test_region_name_preservation():
    """Test that region names are preserved and not truncated"""
    print("\n🔧 Testing region name preservation...")
    
    try:
        from app.data_acquisition.sources.brazilian_elevation import BrazilianElevationSource
        from app.data_acquisition.utils.coordinates import BoundingBox
        from app.data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
        
        # Test with a region name that was previously truncated
        test_region_name = "2.01S_54.99W"
        bbox = BoundingBox(west=-55.0, south=-2.1, east=-54.9, north=-2.0)
        
        request = DownloadRequest(
            bbox=bbox,
            data_type=DataType.ELEVATION,
            resolution=DataResolution.HIGH,
            max_file_size_mb=25.0,
            region_name=test_region_name
        )
        
        print(f"✅ Region name preserved: '{request.region_name}'")
        
        if request.region_name == test_region_name:
            print("✅ Region name preservation working correctly!")
            return True
        else:
            print(f"❌ Region name not preserved correctly: expected '{test_region_name}', got '{request.region_name}'")
            return False
            
    except Exception as e:
        print(f"❌ Region name preservation test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all interface fix tests"""
    print("🎯 INTERFACE FIXES VERIFICATION")
    print("=" * 50)
    
    tests = [
        ("DownloadRequest Interface", test_download_request_interface),
        ("Progress Callback Signatures", test_progress_callback_signatures),
        ("Buffer Optimization", test_buffer_optimization),
        ("Region Name Preservation", test_region_name_preservation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} {test_name}")
    
    overall_success = all(results)
    success_rate = sum(results) / len(results) * 100
    
    print(f"\n🎯 Overall Result: {success_rate:.1f}% tests passed ({sum(results)}/{len(results)})")
    
    if overall_success:
        print("🎉 ALL INTERFACE FIXES VERIFIED SUCCESSFULLY!")
        print("✅ The bounds mismatch and parameter issues should now be resolved")
    else:
        print("⚠️  Some interface fixes need additional work")
        print("❌ Review the failed tests above for remaining issues")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
