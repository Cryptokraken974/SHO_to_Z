#!/usr/bin/env python3
"""
Test script for large image optimization functionality
"""

import sys
import json
import base64
import requests
from pathlib import Path

def test_large_image_overlay():
    """Test the large image overlay optimization with a problematic DSM image"""
    
    print("🧪 Testing Large Image Overlay Optimization")
    print("=" * 50)
    
    # Test configuration
    base_url = "http://localhost:8000"
    test_cases = [
        {
            "name": "NP_T-0251 (Large DSM)",
            "endpoint": f"{base_url}/api/overlay/dsm/NP_T-0251",
            "description": "115M pixel DSM that previously triggered browser memory issues"
        },
        {
            "name": "Medium Size Test",
            "endpoint": f"{base_url}/api/overlay/dsm/test_medium",
            "description": "Medium-sized image for compression threshold testing"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        print(f"   Endpoint: {test_case['endpoint']}")
        
        try:
            # Make request to overlay endpoint
            response = requests.get(test_case['endpoint'], timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Analyze response
                if 'image_data' in data:
                    image_size = len(data['image_data'])
                    size_mb = image_size / (1024 * 1024)
                    
                    print(f"   ✅ Response received")
                    print(f"   📏 Image data size: {size_mb:.2f} MB")
                    print(f"   🗺️ Bounds: {data.get('bounds', 'Not specified')}")
                    
                    # Check if optimization would be triggered
                    if size_mb > 75:  # Large image threshold
                        print(f"   🔧 LARGE IMAGE: Will trigger aggressive optimization")
                    elif size_mb > 25:  # Compression threshold
                        print(f"   ⚙️ MEDIUM IMAGE: Will trigger standard compression")
                    else:
                        print(f"   ✨ SMALL IMAGE: No optimization needed")
                        
                    # Estimate pixel count (rough calculation)
                    estimated_pixels = (image_size * 3) // 4  # Base64 encoding overhead
                    estimated_pixels_m = estimated_pixels / 1_000_000
                    print(f"   🖼️ Estimated pixels: {estimated_pixels_m:.1f}M")
                    
                else:
                    print(f"   ❌ No image data in response")
                    
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timeout (30s) - Image may be very large")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Connection error - Server may not be running")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n🔍 Frontend Optimization Features:")
    print(f"   • Progressive loading for images > 10MB")
    print(f"   • Client-side resizing for images > 50M pixels")
    print(f"   • Canvas-based compression with quality fallback")
    print(f"   • Memory monitoring and retry logic")
    print(f"   • User feedback with progress indicators")
    
    print(f"\n📊 Optimization Thresholds:")
    print(f"   • Compression threshold: 25MB / 25M pixels")
    print(f"   • Maximum size: 75MB / 50M pixels")
    print(f"   • Fallback dimensions: 4096x4096")
    print(f"   • Minimum scale factor: 25%")
    
    print(f"\n✅ Test completed. Check frontend console for detailed logs when using the overlay.")

if __name__ == "__main__":
    test_large_image_overlay()
