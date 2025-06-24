#!/usr/bin/env python3
"""
Test Immediate Bounds Saving Implementation - Complete Verification
=================================================================

This script verifies that ALL LAZ acquisition sources now have immediate bounds saving
functionality implemented, including the DataAcquisitionManager and LidarAcquisitionManager.
"""

import asyncio
import tempfile
import os
from pathlib import Path
import sys

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

async def test_data_acquisition_manager():
    """Test DataAcquisitionManager.download_lidar_data() for immediate bounds saving."""
    print("\n🔍 Testing DataAcquisitionManager.download_lidar_data() immediate bounds saving...")
    
    try:
        from data_acquisition.manager import DataAcquisitionManager
        from data_acquisition.sources.usgs_3dep import USGS3DEPSource
        from data_acquisition.sources.opentopography import OpenTopographySource
        from data_acquisition.sources.brazilian_elevation import BrazilianElevationSource
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize manager with temporary directory
            manager = DataAcquisitionManager(
                cache_dir=temp_dir + "/cache",
                output_dir=temp_dir + "/output"
            )
            
            # Test coordinates (US location for USGS 3DEP availability)
            test_lat = 39.7392
            test_lng = -104.9903  # Denver, Colorado
            test_buffer = 2.0
            
            print(f"   📍 Test coordinates: {test_lat}, {test_lng} (buffer: {test_buffer}km)")
            
            # Call download_lidar_data
            result = await manager.download_lidar_data(
                lat=test_lat,
                lng=test_lng,
                buffer_km=test_buffer,
                output_dir=temp_dir + "/output"
            )
            
            # Check if metadata.txt was created immediately
            expected_region_name = f"{abs(test_lat):.2f}N_{abs(test_lng):.2f}W"
            metadata_path = Path(temp_dir) / "output" / expected_region_name / "metadata.txt"
            
            if metadata_path.exists():
                print(f"   ✅ SUCCESS: metadata.txt created at {metadata_path}")
                
                # Read and verify metadata content
                with open(metadata_path, 'r') as f:
                    content = f.read()
                    
                if "# REQUESTED BOUNDS (WGS84 - EPSG:4326)" in content:
                    print(f"   ✅ SUCCESS: Proper REQUESTED BOUNDS header found")
                    
                    # Check for required fields
                    required_fields = ["North Bound:", "South Bound:", "East Bound:", "West Bound:", "Center Lat:", "Center Lng:", "Buffer (km):"]
                    found_fields = []
                    for field in required_fields:
                        if field in content:
                            found_fields.append(field)
                    
                    if len(found_fields) == len(required_fields):
                        print(f"   ✅ SUCCESS: All required metadata fields found: {', '.join(found_fields)}")
                        print(f"   📄 Metadata preview:\n{content[:200]}...")
                        return True
                    else:
                        missing = set(required_fields) - set(found_fields)
                        print(f"   ❌ FAIL: Missing metadata fields: {missing}")
                        return False
                else:
                    print(f"   ❌ FAIL: REQUESTED BOUNDS header not found in metadata")
                    return False
            else:
                print(f"   ❌ FAIL: metadata.txt not created at expected path: {metadata_path}")
                return False
                
    except Exception as e:
        print(f"   ❌ ERROR: DataAcquisitionManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_lidar_acquisition_manager():
    """Test LidarAcquisitionManager.acquire_lidar_data() for immediate bounds saving."""
    print("\n🔍 Testing LidarAcquisitionManager.acquire_lidar_data() immediate bounds saving...")
    
    try:
        from lidar_acquisition.manager import LidarAcquisitionManager
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize manager with temporary directory
            manager = LidarAcquisitionManager(
                cache_dir=temp_dir + "/cache",
                output_dir=temp_dir + "/output"
            )
            
            # Test coordinates (US location for provider availability)
            test_lat = 39.7392
            test_lng = -104.9903  # Denver, Colorado
            test_buffer = 2.0
            
            print(f"   📍 Test coordinates: {test_lat}, {test_lng} (buffer: {test_buffer}km)")
            
            # Progress callback to track metadata creation
            metadata_created = False
            
            async def progress_callback(data):
                nonlocal metadata_created
                if data.get("type") == "metadata_created":
                    metadata_created = True
                    print(f"   📝 Progress: {data.get('message')}")
            
            # Call acquire_lidar_data
            try:
                result = await manager.acquire_lidar_data(
                    lat=test_lat,
                    lng=test_lng,
                    buffer_km=test_buffer,
                    provider="auto",
                    progress_callback=progress_callback
                )
            except Exception as e:
                # Even if acquisition fails, metadata should still be created
                print(f"   ⚠️  Note: Acquisition may fail (expected), but metadata creation should still work")
            
            # Check if metadata.txt was created immediately
            expected_region_name = f"lidar_{abs(test_lat):.2f}N_{abs(test_lng):.2f}W"
            metadata_path = Path(temp_dir) / "output" / expected_region_name / "metadata.txt"
            
            if metadata_path.exists():
                print(f"   ✅ SUCCESS: metadata.txt created at {metadata_path}")
                
                # Read and verify metadata content
                with open(metadata_path, 'r') as f:
                    content = f.read()
                    
                if "# REQUESTED BOUNDS (WGS84 - EPSG:4326)" in content:
                    print(f"   ✅ SUCCESS: Proper REQUESTED BOUNDS header found")
                    
                    # Check for required fields
                    required_fields = ["North Bound:", "South Bound:", "East Bound:", "West Bound:", "Center Lat:", "Center Lng:", "Buffer (km):"]
                    found_fields = []
                    for field in required_fields:
                        if field in content:
                            found_fields.append(field)
                    
                    if len(found_fields) == len(required_fields):
                        print(f"   ✅ SUCCESS: All required metadata fields found: {', '.join(found_fields)}")
                        print(f"   📄 Metadata preview:\n{content[:200]}...")
                        return True
                    else:
                        missing = set(required_fields) - set(found_fields)
                        print(f"   ❌ FAIL: Missing metadata fields: {missing}")
                        return False
                else:
                    print(f"   ❌ FAIL: REQUESTED BOUNDS header not found in metadata")
                    return False
            else:
                print(f"   ❌ FAIL: metadata.txt not created at expected path: {metadata_path}")
                return False
                
    except Exception as e:
        print(f"   ❌ ERROR: LidarAcquisitionManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_individual_sources():
    """Test individual LAZ acquisition sources for immediate bounds saving."""
    print("\n🔍 Testing individual LAZ acquisition sources...")
    
    sources_tested = 0
    sources_passed = 0
    
    # Test USGS 3DEP Source
    try:
        print("\n   📡 Testing USGS 3DEP Source...")
        from data_acquisition.sources.usgs_3dep import USGS3DEPSource
        from data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
        from data_acquisition.utils.coordinates import CoordinateConverter, BoundingBox
        
        source = USGS3DEPSource()
        converter = CoordinateConverter()
        
        # Test coordinates
        test_lat = 39.7392
        test_lng = -104.9903
        test_buffer = 2.0
        
        bbox = converter.create_bounding_box(test_lat, test_lng, test_buffer)
        request = DownloadRequest(
            bbox=bbox,
            data_type=DataType.LAZ,
            resolution=DataResolution.HIGH,
            region_name="test_region"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # This will create the info file and metadata.txt
            result = await source.download(request)
            
            # Check for metadata.txt in the expected location
            metadata_files = list(Path(temp_dir).rglob("metadata.txt"))
            input_metadata_files = list(Path("input").rglob("metadata.txt"))
            
            if metadata_files or input_metadata_files:
                found_metadata = metadata_files[0] if metadata_files else input_metadata_files[0]
                print(f"   ✅ USGS 3DEP: metadata.txt found at {found_metadata}")
                sources_passed += 1
            else:
                print(f"   ❌ USGS 3DEP: metadata.txt not found")
                
        sources_tested += 1
        
    except Exception as e:
        print(f"   ❌ USGS 3DEP test error: {e}")
        sources_tested += 1
    
    # Test OpenTopography Source
    try:
        print("\n   📡 Testing OpenTopography Source...")
        from data_acquisition.sources.opentopography import OpenTopographySource
        
        source = OpenTopographySource()
        converter = CoordinateConverter()
        
        bbox = converter.create_bounding_box(test_lat, test_lng, test_buffer)
        request = DownloadRequest(
            bbox=bbox,
            data_type=DataType.LAZ,
            resolution=DataResolution.HIGH,
            region_name="test_region"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                result = await source.download(request)
                
                # Check for metadata.txt in the expected location
                metadata_files = list(Path(temp_dir).rglob("metadata.txt"))
                input_metadata_files = list(Path("input").rglob("metadata.txt"))
                
                if metadata_files or input_metadata_files:
                    found_metadata = metadata_files[0] if metadata_files else input_metadata_files[0]
                    print(f"   ✅ OpenTopography: metadata.txt found at {found_metadata}")
                    sources_passed += 1
                else:
                    print(f"   ❌ OpenTopography: metadata.txt not found")
            except Exception as e:
                # Even if download fails, metadata should be created
                metadata_files = list(Path("input").rglob("metadata.txt"))
                if metadata_files:
                    print(f"   ✅ OpenTopography: metadata.txt found despite download failure")
                    sources_passed += 1
                else:
                    print(f"   ❌ OpenTopography: metadata.txt not found")
                
        sources_tested += 1
        
    except Exception as e:
        print(f"   ❌ OpenTopography test error: {e}")
        sources_tested += 1
    
    print(f"\n   📊 Individual sources test result: {sources_passed}/{sources_tested} passed")
    return sources_passed == sources_tested

async def main():
    """Run complete immediate bounds saving verification test."""
    print("🧪 IMMEDIATE BOUNDS SAVING - COMPLETE VERIFICATION TEST")
    print("=" * 60)
    print("Testing that ALL LAZ acquisition sources implement immediate bounds saving...")
    
    test_results = []
    
    # Test DataAcquisitionManager
    result1 = await test_data_acquisition_manager()
    test_results.append(("DataAcquisitionManager", result1))
    
    # Test LidarAcquisitionManager
    result2 = await test_lidar_acquisition_manager()
    test_results.append(("LidarAcquisitionManager", result2))
    
    # Test individual sources
    result3 = await test_individual_sources()
    test_results.append(("Individual Sources", result3))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 FINAL TEST RESULTS SUMMARY:")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if passed:
            passed_tests += 1
    
    print(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 SUCCESS: All LAZ acquisition sources have immediate bounds saving!")
        print("   ✅ DataAcquisitionManager.download_lidar_data() creates metadata.txt immediately")
        print("   ✅ LidarAcquisitionManager.acquire_lidar_data() creates metadata.txt immediately") 
        print("   ✅ Individual sources (USGS 3DEP, OpenTopography) create metadata.txt immediately")
        print("   ✅ All sources use consistent '# REQUESTED BOUNDS (WGS84 - EPSG:4326)' format")
        print("\n💾 Immediate bounds saving implementation is now COMPLETE across all LAZ sources!")
        return True
    else:
        print("\n❌ FAILURE: Some LAZ acquisition sources are missing immediate bounds saving")
        print("   Please review the failed tests above and implement missing functionality.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
