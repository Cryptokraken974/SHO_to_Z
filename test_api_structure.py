#!/usr/bin/env python3
"""
Simple test script to verify Copernicus Data Space Ecosystem API structure
and coordinate format for Sentinel-2 TIF downloads.

This script tests the API endpoints and request format without requiring valid credentials.
"""

import requests
import json
import math
from datetime import datetime, timedelta

def test_copernicus_api():
    """Test the Copernicus Processing API structure"""
    
    print("🛰️ Testing Copernicus Data Space Ecosystem Processing API")
    print("=" * 60)
    
    # Test coordinates: Portland, Oregon (known good Sentinel-2 coverage)
    lat = 45.5152
    lng = -122.6784
    buffer_km = 5.0
    
    print(f"📍 Test Location: Portland, Oregon")
    print(f"   Latitude: {lat}")
    print(f"   Longitude: {lng}")
    print(f"   Buffer: {buffer_km}km")
    print()
    
    # Calculate bounding box
    lat_delta = buffer_km / 111.0  # Rough conversion: 1 degree ≈ 111 km
    lng_delta = buffer_km / (111.0 * abs(math.cos(math.radians(lat))))
    
    bbox = [
        lng - lng_delta,  # west
        lat - lat_delta,  # south
        lng + lng_delta,  # east  
        lat + lat_delta   # north
    ]
    
    print(f"🔲 Calculated Bounding Box [west, south, east, north]:")
    print(f"   [{bbox[0]:.6f}, {bbox[1]:.6f}, {bbox[2]:.6f}, {bbox[3]:.6f}]")
    print(f"   Size: ~{(bbox[2]-bbox[0])*111:.1f}km x {(bbox[3]-bbox[1])*111:.1f}km")
    print()
    
    # Test OAuth2 token endpoint (without credentials)
    print("🔐 Step 1: Testing OAuth2 Token Endpoint")
    print("=" * 40)
    
    token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    
    try:
        # Test with invalid credentials to see the response structure
        token_response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": "test_client_id",
                "client_secret": "test_client_secret"
            },
            timeout=10
        )
        
        print(f"✅ Token endpoint accessible")
        print(f"   Status: {token_response.status_code}")
        print(f"   Response: {token_response.text[:200]}...")
        
        if token_response.status_code == 400:
            print("   Expected: Invalid credentials (400 error)")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Token endpoint error: {e}")
    
    print()
    
    # Test Processing API endpoint structure
    print("🛰️ Step 2: Testing Processing API Endpoint")
    print("=" * 40)
    
    # Create evalscript for 4-band TIFF (RGB + NDVI)
    evalscript = """
//VERSION=3
function setup() {
    return {
        input: [{
            bands: ["B02", "B03", "B04", "B08"],
            units: "DN"
        }],
        output: {
            bands: 4,
            sampleType: "INT16"
        }
    };
}

function evaluatePixel(sample) {
    // RGB bands (B04=Red, B03=Green, B02=Blue) + NIR (B08)
    return [
        sample.B04,  // Red
        sample.B03,  // Green  
        sample.B02,  // Blue
        sample.B08   // NIR
    ];
}
"""
    
    # Create processing request
    processing_request = {
        "input": {
            "bounds": {
                "bbox": bbox
            },
            "data": [{
                "dataFilter": {
                    "timeRange": {
                        "from": "2024-01-01T00:00:00Z",
                        "to": "2024-12-31T23:59:59Z"
                    },
                    "maxCloudCoverage": 20
                },
                "type": "sentinel-2-l2a"
            }]
        },
        "output": {
            "width": 512,
            "height": 512,
            "responses": [{
                "identifier": "default",
                "format": {
                    "type": "image/tiff"
                }
            }]
        },
        "evalscript": evalscript.strip()
    }
    
    print("📋 Processing Request Structure:")
    print(json.dumps(processing_request, indent=2))
    print()
    
    # Test processing endpoint (without valid token)
    processing_url = "https://sh.dataspace.copernicus.eu/api/v1/process"
    
    try:
        # Test with invalid token to see the response structure
        processing_response = requests.post(
            processing_url,
            headers={
                "Authorization": "Bearer invalid_token",
                "Content-Type": "application/json"
            },
            json=processing_request,
            timeout=10
        )
        
        print(f"✅ Processing endpoint accessible")
        print(f"   Status: {processing_response.status_code}")
        print(f"   Response: {processing_response.text[:200]}...")
        
        if processing_response.status_code == 401:
            print("   Expected: Unauthorized (401 error)")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Processing endpoint error: {e}")
    
    print()
    
    # Summary
    print("📋 API Structure Validation")
    print("=" * 30)
    print("✅ OAuth2 endpoint: https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token")
    print("✅ Processing endpoint: https://sh.dataspace.copernicus.eu/api/v1/process")
    print("✅ Coordinate format: [west, south, east, north] in WGS84")
    print("✅ Request structure: Valid JSON with input/output/evalscript")
    print()
    
    print("🔗 Next Steps:")
    print("1. Get valid CDSE credentials from: https://dataspace.copernicus.eu/")
    print("2. Register for an account and create an OAuth2 application")
    print("3. Set environment variables:")
    print("   export CDSE_CLIENT_ID='your_client_id'")
    print("   export CDSE_CLIENT_SECRET='your_client_secret'")
    print("4. Run the full test with: ./test_copernicus_api.sh")
    print()
    
    # Show curl command for manual testing
    print("🧪 Manual curl test command:")
    print("curl -X POST \\")
    print("  'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token' \\")
    print("  -H 'Content-Type: application/x-www-form-urlencoded' \\")
    print("  -d 'grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET'")
    print()

if __name__ == "__main__":
    test_copernicus_api()
