#!/usr/bin/env python3
"""
Simple Sentinel-2 availability test
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

print("🚀 Simple Sentinel-2 Test")
print("=" * 30)

try:
    print("📦 Importing dependencies...")
    from pystac_client import Client
    import planetary_computer as pc
    print("✅ Imports successful")
    
    print("🔗 Connecting to STAC API...")
    client = Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=pc.sign_inplace
    )
    print("✅ Client connection successful")
    
    print("🔍 Searching for Sentinel-2 data...")
    # Amazon Basin coordinates
    bbox = [62.557711, -9.492289, 62.782289, -9.267711]
    
    search = client.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime="2023-01-01T00:00:00Z/2025-06-04T23:59:59Z",
        limit=5
    )
    
    print("📊 Getting items...")
    items = list(search.items())
    
    print(f"✅ Found {len(items)} items")
    
    if items:
        print("📋 First item details:")
        item = items[0]
        print(f"   ID: {item.id}")
        print(f"   Date: {item.datetime}")
        print(f"   Collection: {item.collection_id}")
    else:
        print("❌ No items found")
        
        # Try different location
        print("\n🔄 Trying São Paulo...")
        sao_paulo_bbox = [-46.7, -23.6, -46.5, -23.5]
        
        sp_search = client.search(
            collections=["sentinel-2-l2a"],
            bbox=sao_paulo_bbox,
            datetime="2024-01-01T00:00:00Z/2025-06-04T23:59:59Z",
            limit=5
        )
        
        sp_items = list(sp_search.items())
        print(f"São Paulo results: {len(sp_items)} items")
        
except Exception as e:
    print(f"💥 Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Test completed")
