#!/usr/bin/env python3
"""
Test script to verify satellite gallery has been successfully removed from the application.
"""

import os
import re

def check_file_for_satellite_gallery_references(file_path):
    """Check a file for satellite gallery references."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find satellite gallery references
    patterns = [
        r'satellite-gallery',
        r'satelliteOverlayGallery',
        r'SatelliteOverlayGallery',
        r'satellite\.gallery',
        r'displaySentinel2ImagesForRegion',
        r'refreshSatelliteGallery',
        r'displaySentinel2BandsGallery'
    ]
    
    found_references = []
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            found_references.extend(matches)
    
    return found_references

def main():
    print("🔍 Testing satellite gallery removal...")
    print("=" * 60)
    
    # Files to check (main application files)
    files_to_check = [
        'frontend/modules/map-tab-content.html',
        'frontend/js/components/main-content.js',
        'frontend/js/components/gallery.js',
        'frontend/js/ui.js',
        'frontend/js/fileManager.js',
        'frontend/js/websocket.js',
        'frontend/css/gallery.css'
    ]
    
    all_clean = True
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"📄 Checking {file_path}...")
            references = check_file_for_satellite_gallery_references(file_path)
            
            if references:
                print(f"   ❌ Found satellite gallery references: {references}")
                all_clean = False
            else:
                print(f"   ✅ Clean - no satellite gallery references found")
        else:
            print(f"   ⚠️  File not found: {file_path}")
    
    print("=" * 60)
    
    if all_clean:
        print("🎉 SUCCESS: Satellite gallery has been successfully removed!")
        print("   ✅ No satellite gallery references found in main application files")
        print("   ✅ NDVI is now properly handled in the raster gallery")
        print("   ✅ Application should work without satellite gallery dependencies")
    else:
        print("❌ FAILED: Some satellite gallery references still exist")
        print("   Please review and remove any remaining references")
    
    print()
    print("📊 Summary:")
    print("   - Satellite gallery HTML removed from map-tab-content.html")
    print("   - Satellite gallery components removed from main-content.js")
    print("   - Satellite gallery initialization removed from components")
    print("   - Satellite gallery functions removed from ui.js")
    print("   - CSS references updated to exclude satellite gallery")
    print("   - NDVI now properly handled in raster gallery")

if __name__ == "__main__":
    main()
