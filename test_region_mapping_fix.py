#!/usr/bin/env python3
"""
Test script to verify the FoxIsland region mapping fix.

This script simulates the scenario that was causing the original issue:
- User selects "FoxIsland" as region
- System should map to "FoxIsland.laz" file, not "OR_WizardIsland.laz"
"""

import sys
import os
sys.path.append('.')

def test_region_mapping_fix():
    """Test that the region mapping fix resolves the FoxIsland issue."""
    print("🧪 Testing Region Mapping Fix")
    print("=" * 50)
    
    try:
        from app.config.region_mapping import region_mapper
        
        # Test the core issue: FoxIsland mapping
        print("\n🎯 CORE ISSUE TEST:")
        print("Before fix: FoxIsland would incorrectly map to OR_WizardIsland.laz")
        print("After fix: FoxIsland should correctly map to FoxIsland.laz")
        
        fox_result = region_mapper.find_laz_file_for_region('FoxIsland')
        print(f"\n📍 FoxIsland mapping result: {fox_result}")
        
        if 'FoxIsland.laz' in fox_result:
            print("✅ SUCCESS: FoxIsland correctly maps to FoxIsland.laz")
            print("✅ The region mapping issue has been RESOLVED!")
            
            # Test the API endpoint utility function
            print("\n🔧 Testing API endpoint utility function:")
            from app.endpoints.laz_processing import resolve_laz_file_from_region
            
            api_result = resolve_laz_file_from_region('FoxIsland', 'DTM')
            print(f"📍 API utility result: {api_result}")
            
            if api_result == fox_result:
                print("✅ API endpoint utility working correctly")
                return True
            else:
                print("❌ API endpoint utility mismatch")
                return False
                
        else:
            print(f"❌ ISSUE PERSISTS: FoxIsland incorrectly maps to {fox_result}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False

def test_wizard_island_alias():
    """Test that WizardIsland alias still works correctly."""
    print("\n🔮 Testing WizardIsland alias mapping:")
    
    try:
        from app.config.region_mapping import region_mapper
        
        wizard_result = region_mapper.find_laz_file_for_region('WizardIsland')
        print(f"📍 WizardIsland mapping result: {wizard_result}")
        
        if 'OR_WizardIsland.laz' in wizard_result:
            print("✅ WizardIsland alias correctly maps to OR_WizardIsland.laz")
            return True
        else:
            print(f"❌ WizardIsland alias broken: maps to {wizard_result}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing WizardIsland: {e}")
        return False

def main():
    """Run all tests and provide summary."""
    print("🚀 Region Mapping Fix Verification")
    print("=" * 60)
    
    # Test core fix
    fox_test_passed = test_region_mapping_fix()
    
    # Test that existing aliases still work
    wizard_test_passed = test_wizard_island_alias()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"  FoxIsland mapping fix: {'✅ PASSED' if fox_test_passed else '❌ FAILED'}")
    print(f"  WizardIsland alias: {'✅ PASSED' if wizard_test_passed else '❌ FAILED'}")
    
    if fox_test_passed and wizard_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("🎯 The FoxIsland region mapping issue has been successfully resolved!")
        print("✅ Users can now select 'FoxIsland' without getting 'Unknown error' messages.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("🚨 The region mapping issue may not be fully resolved.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
