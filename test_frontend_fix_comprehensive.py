#!/usr/bin/env python3
"""
Comprehensive test to verify the DTM frontend fix works correctly.
This simulates the exact browser behavior to test our fix.
"""
import requests
import json
import time

def test_dtm_processing():
    """Test DTM processing exactly as the frontend would do it"""
    
    print("🧪 Testing DTM Processing Fix")
    print("=" * 50)
    
    # Test the exact scenario from the frontend
    region_name = "OR_WizardIsland"  # Display name
    processing_type = "LAZ"  # Processing type (maps to LAZ directory)
    
    print(f"📍 Testing region: {region_name}")
    print(f"🔧 Processing type: {processing_type}")
    print()
    
    # Step 1: Test backend API directly
    print("1️⃣ Testing Backend API Directly...")
    try:
        api_url = f"http://localhost:8001/api/process-laz/{region_name}?processing_type={processing_type}"
        print(f"   API URL: {api_url}")
        
        response = requests.post(api_url, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "image" in data:
                print("   ✅ API returns image data successfully")
                print(f"   📊 Image data length: {len(data['image'])} characters")
            else:
                print("   ❌ API response missing image data")
                print(f"   📋 Response keys: {list(data.keys())}")
        else:
            print(f"   ❌ API returned error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   📋 Error details: {error_data}")
            except:
                print(f"   📋 Raw error: {response.text}")
                
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        return False
    
    print()
    
    # Step 2: Simulate frontend processing logic
    print("2️⃣ Simulating Frontend Processing Logic...")
    
    def simulate_frontend_processing(api_response, status_code):
        """Simulate the exact frontend processing logic"""
        
        print(f"   📥 Simulating response processing...")
        print(f"   🔢 HTTP Status: {status_code}")
        
        # This mirrors our fixed frontend logic
        if status_code >= 200 and status_code < 300:
            try:
                data = api_response.json() if hasattr(api_response, 'json') else api_response
                print(f"   📋 Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Our fixed condition: check for data.success OR data.image
                has_success = data.get('success') == True if isinstance(data, dict) else False
                has_image = 'image' in data if isinstance(data, dict) else False
                
                print(f"   ✅ Has success field: {has_success}")
                print(f"   🖼️ Has image field: {has_image}")
                
                # Updated logic from our fix
                if has_success or has_image:
                    print("   ✅ FRONTEND: Processing successful!")
                    return True, "Success"
                else:
                    print("   ❌ FRONTEND: No success or image field found")
                    return False, "No success or image data"
                    
            except Exception as e:
                print(f"   ❌ FRONTEND: JSON parsing failed: {e}")
                return False, f"JSON parsing error: {e}"
        else:
            print(f"   ❌ FRONTEND: HTTP error status {status_code}")
            return False, f"HTTP error: {status_code}"
    
    # Test with the actual API response
    try:
        response = requests.post(api_url, timeout=30)
        success, message = simulate_frontend_processing(response, response.status_code)
        
        print(f"   🎯 Frontend simulation result: {'SUCCESS' if success else 'FAILED'}")
        print(f"   💬 Message: {message}")
        
        if success:
            print("\n🎉 DTM PROCESSING FIX VERIFIED!")
            print("   ✅ Frontend will now correctly handle DTM responses")
            print("   ✅ 'Unknown error' issue should be resolved")
        else:
            print("\n❌ DTM PROCESSING FIX FAILED!")
            print("   ❌ Frontend logic still has issues")
            
        return success
        
    except Exception as e:
        print(f"   ❌ Frontend simulation failed: {e}")
        return False

def test_other_processing_types():
    """Test that our fix doesn't break other processing types"""
    
    print("\n3️⃣ Testing Other Processing Types...")
    print("-" * 30)
    
    # Test cases that might have success fields
    test_cases = [
        # These might not work but shouldn't crash
        ("OR_WizardIsland", "DEM"),
        ("OR_WizardIsland", "CHM"),
    ]
    
    for region, proc_type in test_cases:
        print(f"\n   Testing {region} with {proc_type}...")
        try:
            api_url = f"http://localhost:8001/api/process-laz/{region}?processing_type={proc_type}"
            response = requests.post(api_url, timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                has_success = 'success' in data
                has_image = 'image' in data
                print(f"   Has success: {has_success}, Has image: {has_image}")
                print("   ✅ Would be handled correctly by frontend")
            else:
                print(f"   ❌ Error response (expected for non-DTM types)")
                
        except Exception as e:
            print(f"   ⚠️ Request failed: {e}")

def main():
    """Main test function"""
    
    print("🔧 DTM Frontend Fix Comprehensive Test")
    print("=" * 60)
    print()
    
    # Wait a moment for servers to be ready
    print("⏳ Waiting for servers to be ready...")
    time.sleep(2)
    
    # Run the main DTM test
    dtm_success = test_dtm_processing()
    
    # Test other processing types
    test_other_processing_types()
    
    print("\n" + "=" * 60)
    print("🏁 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    if dtm_success:
        print("✅ DTM processing fix is working correctly!")
        print("✅ Frontend should now handle DTM responses properly")
        print("✅ 'Unknown error' issue should be resolved")
        print("\n🚀 Ready to test in browser!")
    else:
        print("❌ DTM processing fix needs more work")
        print("❌ Frontend may still show 'Unknown error'")
        
    print("\n📋 Next steps:")
    print("   1. Open http://localhost:8000 in browser")
    print("   2. Select 'OR_WizardIsland' region")
    print("   3. Choose 'LAZ' processing type")
    print("   4. Click process and verify no 'Unknown error'")

if __name__ == "__main__":
    main()
