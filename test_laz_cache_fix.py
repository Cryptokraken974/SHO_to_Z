#!/usr/bin/env python3
"""
Test script to verify LAZ coordinate caching integration
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from services.laz_metadata_cache import get_metadata_cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_laz_cache_integration():
    """Test LAZ coordinate caching functionality"""
    print("🧪 Testing LAZ Cache Integration Fix")
    print("=" * 50)
    
    # Test 1: Check if cache system is working
    print("\n📦 Test 1: Cache System Initialization")
    try:
        cache = get_metadata_cache()
        print("  ✅ LAZ metadata cache initialized successfully")
        
        # Check cache database exists
        cache_db_path = cache.db_path
        if cache_db_path.exists():
            print(f"  ✅ Cache database exists: {cache_db_path}")
        else:
            print(f"  ⚠️  Cache database will be created: {cache_db_path}")
    except Exception as e:
        print(f"  ❌ Cache initialization failed: {e}")
        return False
    
    # Test 2: Check if we can store and retrieve metadata
    print("\n💾 Test 2: Cache Store/Retrieve")
    try:
        test_file = "test_file.laz"
        test_metadata = {
            "center": {"lat": 45.5, "lng": -122.5},
            "bounds": {"north": 45.6, "south": 45.4, "east": -122.4, "west": -122.6},
            "source_epsg": "EPSG:4326"
        }
        
        # Try to cache metadata
        cache_success = cache.cache_metadata(test_file, test_metadata)
        if cache_success:
            print("  ✅ Successfully cached test metadata")
            
            # Try to retrieve cached metadata
            retrieved = cache.get_cached_metadata(test_file)
            if retrieved:
                print("  ✅ Successfully retrieved cached metadata")
                print(f"    Center: {retrieved.get('center', {})}")
                print(f"    Bounds: {retrieved.get('bounds', {})}")
            else:
                print("  ⚠️  Could not retrieve cached metadata (file not found)")
        else:
            print("  ❌ Failed to cache test metadata")
    except Exception as e:
        print(f"  ❌ Cache test failed: {e}")
    
    # Test 3: Check LAZ input directory
    print("\n📁 Test 3: LAZ Directory Structure")
    try:
        laz_input_dir = Path("input/LAZ")
        if laz_input_dir.exists():
            laz_files = list(laz_input_dir.glob("*.laz")) + list(laz_input_dir.glob("*.las"))
            print(f"  ✅ LAZ input directory exists: {laz_input_dir}")
            print(f"  📊 Found {len(laz_files)} LAZ/LAS files")
            for laz_file in laz_files[:3]:  # Show first 3 files
                print(f"    - {laz_file.name}")
            if len(laz_files) > 3:
                print(f"    ... and {len(laz_files) - 3} more files")
                
            # Test if we have any cached data for existing files
            print("\n🔍 Checking for existing cached data:")
            for laz_file in laz_files[:2]:  # Check first 2 files
                cached = cache.get_cached_metadata(laz_file.name)
                if cached:
                    print(f"    ✅ {laz_file.name}: Has cached metadata")
                else:
                    print(f"    ⚪ {laz_file.name}: No cached metadata")
        else:
            print(f"  ⚠️  LAZ input directory not found: {laz_input_dir}")
            print("  💡 Create the directory and add LAZ files to test coordinate extraction")
    except Exception as e:
        print(f"  ❌ Directory check failed: {e}")
    
    # Test 4: Check output directory structure
    print("\n🗂️  Test 4: Output Directory Structure")
    try:
        output_dir = Path("output")
        if output_dir.exists():
            subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
            print(f"  ✅ Output directory exists with {len(subdirs)} subdirectories")
            
            # Check for metadata.txt files
            metadata_files = list(output_dir.glob("*/metadata.txt"))
            print(f"  📄 Found {len(metadata_files)} metadata.txt files")
            
            for meta_file in metadata_files[:3]:  # Show first 3
                region_name = meta_file.parent.name
                print(f"    - {region_name}/metadata.txt")
            if len(metadata_files) > 3:
                print(f"    ... and {len(metadata_files) - 3} more files")
        else:
            print(f"  ⚠️  Output directory not found: {output_dir}")
    except Exception as e:
        print(f"  ❌ Output directory check failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 LAZ Cache Integration Test Complete")
    print("\n💡 Next Steps:")
    print("   1. Add LAZ files to input/LAZ/ directory")
    print("   2. Start the FastAPI server")
    print("   3. Call /api/laz/bounds-wgs84/{file_name} endpoint")
    print("   4. Check that coordinates are cached and metadata.txt files are created")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_laz_cache_integration())
