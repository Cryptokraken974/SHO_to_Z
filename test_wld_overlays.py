#!/usr/bin/env python3
"""
Test script to check if the "wld" region needs world file fixes like areweok
"""

import os
import sys

# Add the app directory to the Python path
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

try:
    from app.geo_utils import get_laz_overlay_data
    
    def test_wld_overlays():
        """Test that wld overlays work properly"""
        
        print("🧪 Testing wld region PNG overlay functionality...")
        print("=" * 60)
        
        # Test different overlay types
        overlay_types = [
            "CHM",
            "LRM", 
            "SVF",
            "Slope",
            "HillshadeRGB",
            "TintOverlay"
        ]
        
        base_filename = "wld"
        
        results = {
            'working': [],
            'failed': [],
            'has_bounds': [],
            'no_bounds': []
        }
        
        for overlay_type in overlay_types:
            print(f"\n📊 Testing {overlay_type} overlay...")
            
            try:
                overlay_data = get_laz_overlay_data(base_filename, overlay_type)
                
                if overlay_data:
                    results['working'].append(overlay_type)
                    
                    # Check if bounds are available and reasonable
                    bounds = overlay_data.get('bounds', {})
                    
                    if bounds:
                        north = bounds.get('north')
                        south = bounds.get('south')  
                        east = bounds.get('east')
                        west = bounds.get('west')
                        
                        if all(coord is not None for coord in [north, south, east, west]):
                            # Calculate extent
                            lat_extent = abs(north - south)
                            lng_extent = abs(east - west)
                            
                            print(f"   ✅ Bounds found:")
                            print(f"      North: {north:.6f}, South: {south:.6f}")
                            print(f"      East: {east:.6f}, West: {west:.6f}")
                            print(f"      Extent: {lat_extent:.6f}° x {lng_extent:.6f}°")
                            print(f"      Source: {bounds.get('source', 'unknown')}")
                            
                            results['has_bounds'].append(overlay_type)
                            
                            # Check if bounds are realistic (not tiny like areweok had)
                            if lat_extent > 0.1 and lng_extent > 0.1:
                                print(f"   🎯 PASS: Bounds are realistic")
                            else:
                                print(f"   ⚠️  WARNING: Bounds might be too small")
                        else:
                            print(f"   ❌ Incomplete bounds data")
                            results['no_bounds'].append(overlay_type)
                    else:
                        print(f"   ❌ No bounds found")
                        results['no_bounds'].append(overlay_type)
                        
                else:
                    print(f"   ❌ No overlay data returned")
                    results['failed'].append(overlay_type)
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                results['failed'].append(overlay_type)
        
        print("\n" + "=" * 60)
        print("📝 WLD Region Test Summary:")
        print(f"✅ Working overlays: {len(results['working'])}/{len(overlay_types)}")
        print(f"   {results['working']}")
        print(f"📍 Have bounds: {len(results['has_bounds'])}/{len(overlay_types)}")
        print(f"   {results['has_bounds']}")
        print(f"❌ Failed/No bounds: {len(results['failed']) + len(results['no_bounds'])}/{len(overlay_types)}")
        if results['failed']:
            print(f"   Failed: {results['failed']}")
        if results['no_bounds']:
            print(f"   No bounds: {results['no_bounds']}")
        
        # Analysis and recommendations
        print("\n🔍 Analysis:")
        if len(results['working']) == len(overlay_types) and len(results['has_bounds']) == len(overlay_types):
            print("✅ All overlays working properly with bounds - NO ACTION NEEDED")
        elif len(results['working']) > 0 and len(results['has_bounds']) == 0:
            print("⚠️  Overlays exist but missing bounds - NEEDS METADATA UPDATE")
        elif len(results['working']) > 0 and len(results['has_bounds']) < len(results['working']):
            print("⚠️  Some overlays missing bounds - MAY NEED SELECTIVE FIXES")
        else:
            print("❌ Major issues detected - NEEDS INVESTIGATION")
            
        return results
        
    if __name__ == "__main__":
        test_wld_overlays()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure you're running this from the correct directory")
