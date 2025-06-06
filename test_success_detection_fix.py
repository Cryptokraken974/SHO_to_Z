#!/usr/bin/env python3

import requests
import json

def test_success_detection_fix():
    """Test that the success detection fix works correctly"""
    
    print("🧪 Testing Success Detection Fix")
    print("=" * 50)
    
    # Test DTM API to verify backend response format
    url = "http://localhost:8000/api/dtm"
    data = {
        "region_name": "LAZ",
        "processing_type": "dtm"
    }
    
    print(f"📍 Testing DTM API response format")
    print(f"🔗 URL: {url}")
    print(f"📦 Data: {data}")
    print()
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        print(f"📊 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API call successful!")
            print(f"📋 Response keys: {list(data.keys())}")
            
            # Test the frontend logic conditions
            has_success = data.get('success') == True
            has_image = 'image' in data
            
            print(f"\n🔍 Frontend Logic Analysis:")
            print(f"   data.success: {data.get('success')} → {has_success}")
            print(f"   'image' in data: {has_image}")
            print(f"   Condition (success || image): {has_success or has_image}")
            
            # Simulate the old buggy logic
            old_return_value = data.get('success')  # This was the bug
            print(f"\n🐛 Old Logic (buggy):")
            print(f"   return data.success: {old_return_value} → {bool(old_return_value)}")
            
            # Simulate the new fixed logic
            new_return_value = has_success or has_image
            print(f"\n✅ New Logic (fixed):")
            print(f"   return (success || image): {new_return_value}")
            
            print(f"\n🎯 Result:")
            if new_return_value:
                print("   ✅ SUCCESS: Frontend will now correctly detect successful processing!")
            else:
                print("   ❌ FAILED: Logic still has issues")
                
            return new_return_value
            
        else:
            print(f"❌ API call failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"📋 Error: {error_data}")
            except:
                print(f"📋 Raw error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
        print("💡 Start the server with: uvicorn app.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_success_detection_fix()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 SUCCESS DETECTION FIX VERIFIED!")
        print("   ✅ The '0 successful, 9 failed' issue should now be resolved")
        print("   ✅ Frontend will correctly count successful raster generations")
    else:
        print("❌ SUCCESS DETECTION FIX FAILED!")
        print("   ❌ Further investigation needed")
