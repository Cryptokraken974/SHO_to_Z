#!/usr/bin/env python3
"""
Simple test script to verify DSM overlay backend functionality
"""

import requests
import json
import os

def test_dsm_file_existence():
    """Check if DSM files exist in the expected locations"""
    print("🔍 Checking DSM file existence...")
    
    regions_with_dsm = []
    output_dir = "output"
    
    if not os.path.exists(output_dir):
        print(f"❌ Output directory not found: {output_dir}")
        return []
    
    for region in os.listdir(output_dir):
        region_path = os.path.join(output_dir, region)
        if os.path.isdir(region_path):
            png_outputs = os.path.join(region_path, "lidar", "png_outputs")
            if os.path.exists(png_outputs):
                dsm_files = [f for f in os.listdir(png_outputs) if "dsm" in f.lower()]
                if dsm_files:
                    print(f"✅ Found DSM files for region {region}: {dsm_files}")
                    regions_with_dsm.append(region)
                else:
                    print(f"⚪ No DSM files found for region {region}")
            else:
                print(f"⚪ No png_outputs directory for region {region}")
    
    return regions_with_dsm

def test_dsm_api_endpoints(regions):
    """Test DSM overlay API endpoints for given regions"""
    print(f"\n🧪 Testing DSM API endpoints for {len(regions)} regions...")
    
    results = {}
    
    for region in regions:
        print(f"\n📍 Testing region: {region}")
        try:
            url = f"http://localhost:8000/api/overlay/raster/{region}/dsm"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                has_image = 'image_data' in data and len(data.get('image_data', '')) > 0
                has_bounds = 'bounds' in data
                
                results[region] = {
                    'status': 'success',
                    'api_success': success,
                    'has_image_data': has_image,
                    'has_bounds': has_bounds
                }
                
                if success and has_image and has_bounds:
                    bounds = data['bounds']
                    print(f"✅ API successful for {region}")
                    print(f"   Bounds: N:{bounds.get('north'):.6f}, S:{bounds.get('south'):.6f}")
                    print(f"           E:{bounds.get('east'):.6f}, W:{bounds.get('west'):.6f}")
                    print(f"   Image data: {len(data['image_data'])} characters")
                else:
                    print(f"⚠️  API returned incomplete data for {region}")
                    print(f"   Success: {success}, Has image: {has_image}, Has bounds: {has_bounds}")
            
            else:
                results[region] = {
                    'status': 'error',
                    'status_code': response.status_code,
                    'error': response.text[:200]
                }
                print(f"❌ API error for {region}: {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                
        except Exception as e:
            results[region] = {
                'status': 'exception',
                'error': str(e)
            }
            print(f"❌ Exception for {region}: {e}")
    
    return results

def test_dtm_comparison():
    """Compare DTM vs DSM API responses to identify differences"""
    print(f"\n🔍 Comparing DTM vs DSM API responses...")
    
    test_region = "OR_WizardIsland"  # Known working region
    
    for processing_type in ['dtm', 'dsm']:
        print(f"\n📊 Testing {processing_type.upper()}...")
        try:
            url = f"http://localhost:8000/api/overlay/raster/{test_region}/{processing_type}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {processing_type.upper()} API successful")
                print(f"   Success: {data.get('success', False)}")
                print(f"   Has image_data: {'image_data' in data and len(data.get('image_data', '')) > 0}")
                print(f"   Has bounds: {'bounds' in data}")
                
                if 'image_data' in data:
                    print(f"   Image data length: {len(data['image_data'])}")
                    
                if 'bounds' in data:
                    bounds = data['bounds']
                    print(f"   Bounds: N:{bounds.get('north'):.6f}, S:{bounds.get('south'):.6f}")
            else:
                print(f"❌ {processing_type.upper()} API failed: {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ {processing_type.upper()} Exception: {e}")

def analyze_dsm_files():
    """Analyze DSM files to understand their structure"""
    print(f"\n🔍 Analyzing DSM file structure...")
    
    dsm_files = []
    for root, dirs, files in os.walk("output"):
        for file in files:
            if "dsm" in file.lower() and file.endswith('.png'):
                dsm_files.append(os.path.join(root, file))
    
    print(f"Found {len(dsm_files)} DSM PNG files")
    
    for dsm_file in dsm_files[:3]:  # Analyze first 3 files
        print(f"\n📄 Analyzing: {dsm_file}")
        
        # Check file size
        size = os.path.getsize(dsm_file)
        print(f"   File size: {size} bytes ({size/1024:.1f} KB)")
        
        # Check for companion files
        base_path = dsm_file.replace('.png', '')
        tiff_file = f"{base_path}.tif"
        world_file = f"{base_path}.wld"
        
        print(f"   TIFF exists: {os.path.exists(tiff_file)}")
        print(f"   World file exists: {os.path.exists(world_file)}")
        
        if os.path.exists(tiff_file):
            tiff_size = os.path.getsize(tiff_file)
            print(f"   TIFF size: {tiff_size} bytes ({tiff_size/1024:.1f} KB)")

def main():
    """Main test function"""
    print("🔍 DSM Overlay Investigation\n" + "="*40)
    
    # Test 1: Check file existence
    regions_with_dsm = test_dsm_file_existence()
    
    if not regions_with_dsm:
        print("\n❌ No regions with DSM files found. Cannot proceed with API tests.")
        return
    
    # Test 2: Test API endpoints
    api_results = test_dsm_api_endpoints(regions_with_dsm)
    
    # Test 3: Compare DTM vs DSM
    test_dtm_comparison()
    
    # Test 4: Analyze file structure
    analyze_dsm_files()
    
    # Summary
    print(f"\n📊 SUMMARY")
    print(f"="*40)
    print(f"Regions with DSM files: {len(regions_with_dsm)}")
    
    successful_apis = sum(1 for result in api_results.values() if result.get('status') == 'success')
    print(f"Successful API calls: {successful_apis}/{len(regions_with_dsm)}")
    
    if successful_apis == len(regions_with_dsm):
        print("\n✅ DSM backend functionality appears to be working correctly")
        print("💡 The issue is likely in the frontend overlay display or user interaction")
    else:
        print(f"\n⚠️  Some DSM API calls failed - this may be the root cause")

if __name__ == "__main__":
    main()
