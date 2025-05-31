#!/bin/bash

# Test script for Copernicus Data Space Ecosystem Processing API
# This script tests the API directly with curl to isolate any authentication or request issues

echo "🛰️ Testing Copernicus Data Space Ecosystem Processing API"
echo "========================================================="

# Test coordinates: Portland, Oregon (known good Sentinel-2 coverage)
LAT=45.5152
LNG=-122.6784
BUFFER_KM=5.0

# Calculate bounding box (5km buffer = ~0.045 degrees)
LAT_DELTA=$(echo "scale=6; $BUFFER_KM / 111.0" | bc -l)
LNG_DELTA=$(echo "scale=6; $BUFFER_KM / 111.0" | bc -l)

WEST=$(echo "scale=6; $LNG - $LNG_DELTA" | bc -l)
SOUTH=$(echo "scale=6; $LAT - $LAT_DELTA" | bc -l) 
EAST=$(echo "scale=6; $LNG + $LNG_DELTA" | bc -l)
NORTH=$(echo "scale=6; $LAT + $LAT_DELTA" | bc -l)

echo "📍 Test Location: Portland, Oregon"
echo "   Latitude: $LAT"
echo "   Longitude: $LNG"
echo "   Buffer: ${BUFFER_KM}km"
echo ""
echo "🔲 Calculated Bounding Box:"
echo "   West: $WEST"
echo "   South: $SOUTH" 
echo "   East: $EAST"
echo "   North: $NORTH"
echo ""

# Check if CDSE credentials are available
if [ -z "$CDSE_CLIENT_ID" ] || [ -z "$CDSE_CLIENT_SECRET" ]; then
    echo "❌ CDSE credentials not found in environment variables"
    echo "   Please set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET"
    echo ""
    echo "🔗 To get credentials:"
    echo "   1. Register at: https://dataspace.copernicus.eu/"
    echo "   2. Create an application to get OAuth2 client credentials"
    echo "   3. Export credentials:"
    echo "      export CDSE_CLIENT_ID='your_client_id'"
    echo "      export CDSE_CLIENT_SECRET='your_client_secret'"
    echo ""
    echo "🧪 Testing without credentials (will fail but show API structure)..."
    CDSE_CLIENT_ID="test_client_id"
    CDSE_CLIENT_SECRET="test_client_secret"
fi

echo "🔐 Step 1: Getting OAuth2 Access Token"
echo "======================================"

# Get OAuth2 token
TOKEN_RESPONSE=$(curl -s -X POST \
  "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$CDSE_CLIENT_ID&client_secret=$CDSE_CLIENT_SECRET")

echo "Token Response:"
echo "$TOKEN_RESPONSE" | jq . 2>/dev/null || echo "$TOKEN_RESPONSE"
echo ""

# Extract access token
ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token' 2>/dev/null)

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to get access token"
    echo "   This is expected if using test credentials"
    echo "   Response: $TOKEN_RESPONSE"
    exit 1
else
    echo "✅ Access token obtained successfully"
    echo "   Token: ${ACCESS_TOKEN:0:20}..."
fi

echo ""
echo "🛰️ Step 2: Testing Sentinel Hub Processing API"
echo "=============================================="

# Create evalscript for 4-band TIF (RGB + NDVI) - properly escaped for JSON
EVALSCRIPT='//VERSION=3
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
    return [
        sample.B04,
        sample.B03,
        sample.B02,
        sample.B08
    ];
}'

# Create processing request with properly escaped evalscript
PROCESSING_REQUEST=$(cat << EOF
{
    "input": {
        "bounds": {
            "bbox": [$WEST, $SOUTH, $EAST, $NORTH]
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
    "evalscript": $(echo "$EVALSCRIPT" | jq -Rs .)
}
EOF
)

echo "Processing Request:"
echo "$PROCESSING_REQUEST" | jq . 2>/dev/null || echo "$PROCESSING_REQUEST"
echo ""

# Make processing API request
echo "🚀 Sending Processing API Request..."
RESPONSE=$(curl -s -X POST \
  "https://sh.dataspace.copernicus.eu/api/v1/process" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PROCESSING_REQUEST" \
  --max-time 30)

echo "API Response Headers and Status:"
curl -s -I -X POST \
  "https://sh.dataspace.copernicus.eu/api/v1/process" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PROCESSING_REQUEST" \
  --max-time 10

echo ""
echo "API Response Body:"
# Check if response is binary (TIFF) or text (error)
if file -b --mime-type - <<< "$RESPONSE" | grep -q "image\|application/octet-stream"; then
    echo "✅ Received binary data (likely a TIFF file!)"
    echo "   Response size: $(echo -n "$RESPONSE" | wc -c) bytes"
    
    # Save to file
    OUTPUT_FILE="test_sentinel2_$(date +%Y%m%d_%H%M%S).tif"
    echo -n "$RESPONSE" > "$OUTPUT_FILE"
    echo "   Saved to: $OUTPUT_FILE"
    
    # Check file info
    echo "   File info:"
    file "$OUTPUT_FILE" || echo "   Could not determine file type"
    ls -lh "$OUTPUT_FILE" || echo "   Could not list file"
    
else
    echo "📄 Received text response:"
    echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
    
    # Check for common error patterns
    if echo "$RESPONSE" | grep -q "authentication\|unauthorized"; then
        echo ""
        echo "❌ Authentication Error"
        echo "   Check your CDSE credentials"
    elif echo "$RESPONSE" | grep -q "quota\|limit"; then
        echo ""
        echo "⚠️  Quota/Rate Limit Error"
        echo "   Your account may have usage limits"
    elif echo "$RESPONSE" | grep -q "coverage\|no.*data"; then
        echo ""
        echo "ℹ️  No Data Available"
        echo "   Try different coordinates or time range"
    fi
fi

echo ""
echo "🧪 Test Summary"
echo "==============="
echo "Location: Portland, Oregon ($LAT, $LNG)"
echo "BBox: [$WEST, $SOUTH, $EAST, $NORTH]"
echo "Buffer: ${BUFFER_KM}km"

if [ -f "$OUTPUT_FILE" ]; then
    echo "Result: ✅ SUCCESS - TIF file downloaded"
    echo "File: $OUTPUT_FILE"
else
    echo "Result: ❌ FAILED - No TIF file generated"
fi

echo ""
echo "🔗 Next Steps:"
echo "   1. Check Copernicus Data Space credentials at: https://dataspace.copernicus.eu/"
echo "   2. Verify account has Processing API access"
echo "   3. Check quota/usage limits in your account dashboard"
echo "   4. Try different coordinates if no data available for this location"
