#!/usr/bin/env python3
"""
Final test to verify the OpenAI image copying fix works with real data.
"""

import requests
import json
import base64

BASE_URL = "http://localhost:8000"

def create_realistic_test_images():
    """Create test images with more realistic names"""
    # Simple 1x1 pixel PNG
    test_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jINiGwAAAABJRU5ErkJggg=="
    
    return [
        {"name": "HillshadeRGB", "data": f"data:image/png;base64,{test_png_base64}"},
        {"name": "Slope", "data": f"data:image/png;base64,{test_png_base64}"},
        {"name": "CHM", "data": f"data:image/png;base64,{test_png_base64}"},
        {"name": "LRM", "data": f"data:image/png;base64,{test_png_base64}"},
        {"name": "SVF", "data": f"data:image/png;base64,{test_png_base64}"}
    ]

def test_realistic_workflow():
    """Test with realistic region and image names"""
    print("🔬 Testing realistic OpenAI workflow...")
    
    # Step 1: Save images
    save_payload = {
        "region_name": "OR_WizardIsland",
        "images": create_realistic_test_images()
    }
    
    save_response = requests.post(f"{BASE_URL}/api/openai/save_images", json=save_payload)
    if save_response.status_code != 200:
        print(f"❌ Save images failed: {save_response.status_code}")
        return False
    
    save_result = save_response.json()
    temp_folder_name = save_result.get('temp_folder_name')
    print(f"✅ Saved images to temp folder: {temp_folder_name}")
    
    # Step 2: Send to OpenAI (will fail API call but should copy images)
    send_payload = {
        "prompt": "Analyze these terrain features for geological insights.",
        "images": [],  # Using saved images, not data URLs
        "laz_name": "OR_WizardIsland",
        "coordinates": {"lat": 42.939, "lng": -122.144},
        "model_name": "gpt-4o-mini", 
        "temp_folder_name": temp_folder_name
    }
    
    send_response = requests.post(f"{BASE_URL}/api/openai/send", json=send_payload)
    send_result = send_response.json()
    
    log_folder = send_result.get('log_folder')
    if log_folder:
        print(f"✅ OpenAI process completed, log folder: {log_folder}")
        
        # Check if images were copied
        from pathlib import Path
        sent_images_path = Path(log_folder) / "sent_images"
        if sent_images_path.exists():
            images = list(sent_images_path.glob("*.png"))
            print(f"📸 Found {len(images)} images in sent_images folder:")
            for img in images:
                print(f"   - {img.name}")
            
            # Check log file
            log_file = Path(log_folder) / "request_log.json"
            if log_file.exists():
                with open(log_file, 'r') as f:
                    log_data = json.load(f)
                print(f"📝 Log file has {len(log_data.get('images', []))} image entries")
                
            return len(images) > 0
        else:
            print("❌ sent_images folder not found!")
            return False
    else:
        print("❌ No log folder created!")
        return False

if __name__ == "__main__":
    success = test_realistic_workflow()
    print("\n" + "=" * 60)
    if success:
        print("🎉 REALISTIC TEST PASSED: Image copying works correctly!")
    else:
        print("❌ REALISTIC TEST FAILED: Image copying still has issues!")
