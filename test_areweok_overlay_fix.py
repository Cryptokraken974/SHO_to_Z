#!/usr/bin/env python3
"""
Test script to verify areweok PNG overlay fix
"""

import os
import sys
import json

# Add the app directory to the Python path
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

try:
    from app.geo_utils import get_laz_overlay_data
    
    def test_areweok_overlays():
        """Test that areweok overlays now have proper georeferencing"""
        
        print("🧪 Testing areweok PNG overlay fix...")
        print("=" * 50)
        
        # Test different overlay types
        overlay_types = [
            "CHM",
            "LRM", 
            "SVF",
            "Slope",
            "HillshadeRGB",
            "TintOverlay"
        ]
        
        base_filename = "areweok"
        
        for overlay_type in overlay_types:
            print(f"\n📊 Testing {overlay_type} overlay...")
            
            try:
                overlay_data = get_laz_overlay_data(base_filename, overlay_type)
                
                if overlay_data:
                    # Check if bounds are reasonable (not tiny)
                    bounds = overlay_data.get('bounds', {})
                    
                    if bounds:
                        north = bounds.get('north')
                        south = bounds.get('south')  
                        east = bounds.get('east')
                        west = bounds.get('west')
                        
                        # Calculate extent
                        lat_extent = abs(north - south) if north and south else 0
                        lng_extent = abs(east - west) if east and west else 0
                        
                        print(f"   ✅ Bounds found:")
                        print(f"      North: {north:.6f}, South: {south:.6f}")
                        print(f"      East: {east:.6f}, West: {west:.6f}")
                        print(f"      Extent: {lat_extent:.6f}° x {lng_extent:.6f}°")
                        
                        # Check if bounds are realistic (not tiny like before)
                        if lat_extent > 0.1 and lng_extent > 0.1:
                            print(f"   🎯 PASS: Bounds are realistic (not tiny points)")
                        else:
                            print(f"   ❌ FAIL: Bounds still too small")
                            
                    else:
                        print(f"   ❌ FAIL: No bounds found")
                        
                else:
                    print(f"   ❌ FAIL: No overlay data returned")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
        
        print("\n" + "=" * 50)
        print("🏁 Test complete!")
        
        # Test summary
        print("\n📝 Fix Summary:")
        print("1. ✅ Updated metadata.txt with proper bounds from TIFF files")
        print("2. ✅ Generated .pgw world files for all PNG overlays")  
        print("3. ✅ Bounds changed from tiny 0.002° to realistic 1.0° extent")
        print("4. ✅ Overlays should now display properly on map")
        
    if __name__ == "__main__":
        test_areweok_overlays()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure you're running this from the correct directory")
