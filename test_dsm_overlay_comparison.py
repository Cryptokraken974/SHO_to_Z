#!/usr/bin/env python3
"""
Test DSM overlay functionality for different region types to compare behavior.
This will help identify the specific difference causing overlay visibility issues.
"""

import requests
import json
import base64
from PIL import Image
import io

def test_dsm_overlay_api(region_name):
    """Test DSM overlay API for a specific region"""
    print(f"\n🧪 Testing DSM overlay API for: {region_name}")
    
    try:
        url = f"http://localhost:8000/api/overlay/raster/{region_name}/dsm"
        response = requests.get(url, timeout=15)
        
        print(f"📡 Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            success = data.get('success', False)
            has_image = 'image_data' in data and len(data.get('image_data', '')) > 0
            has_bounds = 'bounds' in data and data['bounds'] is not None
            
            print(f"✅ API Success: {success}")
            print(f"🖼️  Has image data: {has_image}")
            print(f"🗺️  Has bounds: {has_bounds}")
            
            if has_image:
                image_data_len = len(data['image_data'])
                print(f"📊 Image data length: {image_data_len} characters")
                
                # Try to decode the image to verify it's valid
                try:
                    image_data = base64.b64decode(data['image_data'])
                    img = Image.open(io.BytesIO(image_data))
                    print(f"🖼️  Image dimensions: {img.size}")
                    print(f"🎨 Image mode: {img.mode}")
                    
                    # Check if image has actual content (not all black/white)
                    extrema = img.getextrema()
                    print(f"📈 Image value range: {extrema}")
                    
                except Exception as e:
                    print(f"❌ Error decoding image: {e}")
            
            if has_bounds:
                bounds = data['bounds']
                print(f"🌍 Bounds:")
                print(f"   North: {bounds.get('north', 'N/A'):.6f}")
                print(f"   South: {bounds.get('south', 'N/A'):.6f}")
                print(f"   East:  {bounds.get('east', 'N/A'):.6f}")
                print(f"   West:  {bounds.get('west', 'N/A'):.6f}")
                
                # Calculate bounds size
                if all(k in bounds for k in ['north', 'south', 'east', 'west']):
                    lat_range = abs(bounds['north'] - bounds['south'])
                    lng_range = abs(bounds['east'] - bounds['west'])
                    print(f"📏 Latitude range: {lat_range:.6f}°")
                    print(f"📏 Longitude range: {lng_range:.6f}°")
            
            return {
                'status': 'success',
                'api_success': success,
                'has_image_data': has_image,
                'has_bounds': has_bounds,
                'data': data
            }
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"📝 Response: {response.text[:200]}")
            return {
                'status': 'error',
                'status_code': response.status_code,
                'error': response.text
            }
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        return {
            'status': 'exception',
            'error': str(e)
        }

def compare_image_files(region1, region2):
    """Compare the actual DSM PNG files on disk"""
    print(f"\n📁 Comparing DSM files on disk...")
    
    import os
    
    path1 = f"output/{region1}/lidar/png_outputs/{region1}_elevation_dsm.png"
    path2 = f"output/{region2}/lidar/png_outputs/{region2}_elevation_dsm.png"
    
    for region, path in [(region1, path1), (region2, path2)]:
        print(f"\n📂 {region}:")
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            print(f"   ✅ File exists: {path}")
            print(f"   📊 File size: {file_size:,} bytes")
            
            try:
                with Image.open(path) as img:
                    print(f"   🖼️  Dimensions: {img.size}")
                    print(f"   🎨 Mode: {img.mode}")
                    extrema = img.getextrema()
                    print(f"   📈 Value range: {extrema}")
            except Exception as e:
                print(f"   ❌ Error reading image: {e}")
        else:
            print(f"   ❌ File not found: {path}")

def main():
    """Main test function"""
    print("🔍 DSM Overlay Comparison Test")
    print("=" * 50)
    
    # Test regions
    working_region = "OR_WizardIsland"  # Known to work
    problematic_region = "NP_T-0251"   # Reported not working
    
    # Test API responses
    result1 = test_dsm_overlay_api(working_region)
    result2 = test_dsm_overlay_api(problematic_region)
    
    # Compare files
    compare_image_files(working_region, problematic_region)
    
    # Summary
    print(f"\n📋 SUMMARY")
    print("=" * 30)
    
    print(f"🟢 {working_region}:")
    print(f"   API Success: {result1.get('api_success', False)}")
    print(f"   Has Image: {result1.get('has_image_data', False)}")
    print(f"   Has Bounds: {result1.get('has_bounds', False)}")
    
    print(f"🔴 {problematic_region}:")
    print(f"   API Success: {result2.get('api_success', False)}")
    print(f"   Has Image: {result2.get('has_image_data', False)}")
    print(f"   Has Bounds: {result2.get('has_bounds', False)}")
    
    # Identify differences
    if result1.get('status') == 'success' and result2.get('status') == 'success':
        if (result1.get('api_success') == result2.get('api_success') and 
            result1.get('has_image_data') == result2.get('has_image_data') and 
            result1.get('has_bounds') == result2.get('has_bounds')):
            print("\n✅ Both regions return identical API responses!")
            print("   The issue is likely in the frontend overlay display logic.")
        else:
            print("\n⚠️  API responses differ between regions:")
            for key in ['api_success', 'has_image_data', 'has_bounds']:
                if result1.get(key) != result2.get(key):
                    print(f"   {key}: {working_region}={result1.get(key)} vs {problematic_region}={result2.get(key)}")
    else:
        print(f"\n❌ One or both API calls failed")

if __name__ == "__main__":
    main()
