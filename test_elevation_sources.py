#!/usr/bin/env python3
"""
Test script to diagnose elevation data source issues
"""
import asyncio
import sys
import os
sys.path.append('.')

from app.data_acquisition.sources.brazilian_elevation import BrazilianElevationSource
from app.data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
from app.data_acquisition.utils.coordinates import BoundingBox

async def test_brazilian_elevation():
    """Test the Brazilian elevation source directly"""
    print("🧪 Testing Brazilian Elevation Source")
    print("=" * 50)
    
    # Test coordinates from the region that failed
    test_lat = -2.3134
    test_lng = -56.6221
    
    # Create a small test bounding box (12.5km buffer ≈ 0.1125° at equator)
    buffer_deg = 12.5 / 111.0
    bbox = BoundingBox(
        west=test_lng - buffer_deg,
        south=test_lat - buffer_deg,
        east=test_lng + buffer_deg,
        north=test_lat + buffer_deg
    )
    
    print(f"Test coordinates: {test_lat:.4f}, {test_lng:.4f}")
    print(f"BBox: {bbox.west:.4f}, {bbox.south:.4f}, {bbox.east:.4f}, {bbox.north:.4f}")
    print(f"Area: {bbox.area_km2():.2f} km²")
    
    # Initialize Brazilian elevation source
    source = BrazilianElevationSource()
    
    # Create download request
    request = DownloadRequest(
        bbox=bbox,
        data_type=DataType.ELEVATION,
        resolution=DataResolution.HIGH,
        max_file_size_mb=100.0,
        region_name="TEST_ELEVATION_DEBUG"
    )
    
    # Test availability
    print("\n🔍 Checking availability...")
    
    # Debug the availability check
    center_lat = (bbox.north + bbox.south) / 2
    center_lng = (bbox.east + bbox.west) / 2
    print(f"Center coordinates: {center_lat:.4f}, {center_lng:.4f}")
    
    # Test is_in_brazil directly
    in_brazil = source.is_in_brazil(center_lat, center_lng)
    print(f"is_in_brazil result: {in_brazil}")
    print(f"Brazil bounds check: lat {center_lat:.4f} in (-35, 5)? {-35 <= center_lat <= 5}")
    print(f"Brazil bounds check: lng {center_lng:.4f} in (-75, -30)? {-75 <= center_lng <= -30}")
    
    # Test the full availability check
    available = await source.check_availability(request)
    print(f"Available: {available}")
    
    if not available:
        print("❌ Source not available for this area")
        # Let's check what's failing in check_availability
        print("\nDebugging check_availability:")
        print(f"Request data type: {request.data_type}")
        print(f"Expected data type: {DataType.ELEVATION}")
        print(f"Data type match: {request.data_type == DataType.ELEVATION}")
        
        # Check _validate_request components
        capabilities = source.capabilities
        print(f"\nSource capabilities:")
        print(f"Data types: {capabilities.data_types}")
        print(f"Resolutions: {capabilities.resolutions}")
        print(f"Max area: {capabilities.max_area_km2} km²")
        print(f"Requires API key: {capabilities.requires_api_key}")
        
        # Check each validation step
        data_type_ok = request.data_type in capabilities.data_types
        resolution_ok = request.resolution in capabilities.resolutions
        bbox_area = request.bbox.area_km2()
        area_ok = bbox_area <= capabilities.max_area_km2
        
        print(f"\nValidation breakdown:")
        print(f"Data type OK: {data_type_ok}")
        print(f"Resolution OK: {resolution_ok}")
        print(f"Area OK: {area_ok} (bbox area: {bbox_area:.2f} km² <= max: {capabilities.max_area_km2} km²)")
        
        return
    
    # Test download with progress callback
    progress_logs = []
    
    async def test_progress_callback(update):
        message = update.get('message', '')
        progress = update.get('progress', 0)
        update_type = update.get('type', 'unknown')
        error = update.get('error', '')
        
        log_msg = f"[{update_type}] {message}"
        if progress:
            log_msg += f" ({progress}%)"
        if error:
            log_msg += f" - ERROR: {error}"
        
        progress_logs.append(log_msg)
        print(f"📊 {log_msg}")
    
    print("\n⬇️ Starting download test...")
    try:
        result = await source.download(request, test_progress_callback)
        
        print(f"\n📋 DOWNLOAD RESULT:")
        print(f"Success: {result.success}")
        if result.success:
            print(f"File path: {result.file_path}")
            print(f"File size: {result.file_size_mb:.3f} MB")
            print(f"Resolution: {result.resolution_m}m")
            if result.metadata:
                print(f"Metadata: {result.metadata}")
        else:
            print(f"Error: {result.error_message}")
            
        print(f"\n📝 Progress Log Summary:")
        for i, log in enumerate(progress_logs, 1):
            print(f"{i:2}. {log}")
            
    except Exception as e:
        print(f"❌ Exception during download: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_brazilian_elevation())
