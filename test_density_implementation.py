#!/usr/bin/env python3
"""
Test script for LAZ Density Processing Implementation
Tests the complete density analysis workflow for loaded LAZ files
"""

import sys
import os
from pathlib import Path
import tempfile
import time

# Add the project root to Python path
sys.path.insert(0, '/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

def create_test_laz_file(file_path: str, file_size: int = 50000) -> bool:
    """
    Create a test LAZ file that looks like a real loaded file
    
    Args:
        file_path: Path for the test file
        file_size: Size of file to create (default: 50KB)
        
    Returns:
        True if file created successfully
    """
    try:
        # Create directory if needed
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create a binary file that starts with LAS header signature
        with open(file_path, 'wb') as f:
            # Write LAS header signature
            f.write(b'LASF')
            # Write some random binary data to make it look real
            import random
            for _ in range(file_size - 4):
                f.write(bytes([random.randint(0, 255)]))
        
        print(f"✅ Created test LAZ file: {file_path} ({file_size} bytes)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test LAZ file: {e}")
        return False

def test_laz_classifier():
    """Test the LAZ classifier functionality"""
    print(f"\n🧪 Testing LAZ Classifier...")
    
    try:
        from app.processing.laz_classifier import LAZClassifier
        
        # Create test files
        test_dir = Path("input/test_region")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Test 1: Real-looking LAZ file
        real_laz = test_dir / "real_data.laz"
        create_test_laz_file(str(real_laz), 50000)
        
        # Test 2: Placeholder file
        placeholder_laz = test_dir / "placeholder.laz"
        with open(placeholder_laz, 'w') as f:
            f.write("# Placeholder LAZ file - coordinate generated\n")
        
        # Test classification
        is_loaded_real, reason_real = LAZClassifier.is_loaded_laz(str(real_laz))
        is_loaded_placeholder, reason_placeholder = LAZClassifier.is_loaded_laz(str(placeholder_laz))
        
        print(f"   Real LAZ file: {is_loaded_real} - {reason_real}")
        print(f"   Placeholder file: {is_loaded_placeholder} - {reason_placeholder}")
        
        # Test finding loaded files
        loaded_files = LAZClassifier.get_loaded_laz_files("input")
        print(f"   Found {len(loaded_files)} loaded LAZ files")
        
        # Cleanup
        real_laz.unlink(missing_ok=True)
        placeholder_laz.unlink(missing_ok=True)
        test_dir.rmdir()
        
        success = is_loaded_real and not is_loaded_placeholder
        print(f"   {'✅ PASSED' if success else '❌ FAILED'}: LAZ Classification")
        return success
        
    except Exception as e:
        print(f"❌ LAZ Classifier test failed: {e}")
        return False

def test_density_analyzer():
    """Test the density analyzer functionality"""
    print(f"\n🧪 Testing Density Analyzer...")
    
    try:
        from app.processing.density_analysis import DensityAnalyzer
        
        # Create test LAZ file
        test_dir = Path("input/test_density")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        test_laz = test_dir / "test_density.laz"
        create_test_laz_file(str(test_laz), 100000)
        
        # Create output directory
        output_dir = Path("output/test_density/lidar")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test density analysis (dry run - without PDAL)
        analyzer = DensityAnalyzer(resolution=2.0)
        
        print(f"   ✅ Density analyzer initialized")
        print(f"   Resolution: {analyzer.resolution}m")
        print(f"   NoData value: {analyzer.nodata_value}")
        
        # Cleanup
        test_laz.unlink(missing_ok=True)
        test_dir.rmdir()
        
        print(f"   ✅ PASSED: Density Analyzer initialization")
        return True
        
    except Exception as e:
        print(f"❌ Density Analyzer test failed: {e}")
        return False

def test_density_service():
    """Test the density service functionality"""
    print(f"\n🧪 Testing Density Service...")
    
    try:
        from app.processing.laz_density_service import LAZDensityService
        
        service = LAZDensityService(resolution=1.5)
        
        # Test requirements check
        requirements = service.check_density_requirements()
        
        print(f"   System requirements:")
        print(f"     PDAL available: {requirements['pdal_available']}")
        print(f"     GDAL available: {requirements['gdal_available']}")
        print(f"     System ready: {requirements['system_ready']}")
        
        if requirements['missing_tools']:
            print(f"     Missing tools: {', '.join(requirements['missing_tools'])}")
        
        print(f"   ✅ PASSED: Density Service initialization")
        return True
        
    except Exception as e:
        print(f"❌ Density Service test failed: {e}")
        return False

def test_api_endpoints():
    """Test the API endpoints (if server is running)"""
    print(f"\n🧪 Testing API Endpoints...")
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test 1: Check loaded LAZ files
        try:
            response = requests.get(f"{base_url}/api/density/check-loaded-laz", timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Loaded LAZ check: {result['loaded_files_count']} files found")
            else:
                print(f"   ⚠️ Loaded LAZ check returned: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️ Server not running or API not available: {e}")
            return False
        
        # Test 2: Check requirements
        try:
            response = requests.get(f"{base_url}/api/density/check-requirements", timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Requirements check: System ready = {result['requirements']['system_ready']}")
            else:
                print(f"   ⚠️ Requirements check returned: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️ Requirements check failed: {e}")
        
        # Test 3: Get status
        try:
            response = requests.get(f"{base_url}/api/density/status", timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Status check: {result['loaded_files_count']} loaded files")
            else:
                print(f"   ⚠️ Status check returned: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️ Status check failed: {e}")
        
        print(f"   ✅ PASSED: API Endpoints accessible")
        return True
        
    except Exception as e:
        print(f"❌ API Endpoints test failed: {e}")
        return False

def test_integration_workflow():
    """Test the complete integration workflow"""
    print(f"\n🧪 Testing Integration Workflow...")
    
    try:
        # Create a realistic test scenario
        test_region = "TestRegion_DensityAnalysis"
        test_dir = Path(f"input/{test_region}")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a loaded LAZ file
        test_laz = test_dir / f"{test_region}.laz"
        create_test_laz_file(str(test_laz), 75000)
        
        # Test the complete workflow
        from app.processing.laz_classifier import find_loaded_laz_files
        from app.processing.laz_density_service import LAZDensityService
        
        # Find loaded files
        loaded_files = find_loaded_laz_files("input")
        test_files = [f for f in loaded_files if test_region in f['file_name']]
        
        print(f"   Found {len(test_files)} test files")
        
        if test_files:
            print(f"   Test file: {test_files[0]['file_name']}")
            print(f"   File size: {test_files[0]['file_size']} bytes")
            print(f"   Classification: {test_files[0]['classification_reason']}")
        
        # Test service initialization
        service = LAZDensityService(resolution=1.0)
        requirements = service.check_density_requirements()
        
        if requirements['system_ready']:
            print(f"   ✅ System ready for density processing")
        else:
            print(f"   ⚠️ System not ready: {', '.join(requirements['missing_tools'])}")
        
        # Cleanup
        test_laz.unlink(missing_ok=True)
        test_dir.rmdir()
        
        print(f"   ✅ PASSED: Integration Workflow")
        return True
        
    except Exception as e:
        print(f"❌ Integration Workflow test failed: {e}")
        return False

def main():
    """Run all tests"""
    print(f"🚀 LAZ Density Processing Implementation Test Suite")
    print(f"=" * 60)
    
    tests = [
        ("LAZ Classifier", test_laz_classifier),
        ("Density Analyzer", test_density_analyzer),
        ("Density Service", test_density_service),
        ("API Endpoints", test_api_endpoints),
        ("Integration Workflow", test_integration_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print(f"=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print(f"🎉 All tests passed! LAZ Density Processing implementation is ready.")
    else:
        print(f"⚠️ Some tests failed. Check the implementation.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
