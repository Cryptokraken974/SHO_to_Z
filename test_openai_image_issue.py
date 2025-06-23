#!/usr/bin/env python3
"""
Test script to reproduce the OpenAI image copying issue.
This will simulate the frontend workflow to identify where images are getting lost.
"""

import requests
import json
import base64
from pathlib import Path

# Server configuration
BASE_URL = "http://localhost:8000"

def create_test_image_base64():
    """Create a simple test image in base64 format"""
    # Simple 1x1 pixel PNG
    test_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jINiGwAAAABJRU5ErkJggg=="
    return f"data:image/png;base64,{test_png_base64}"

def test_save_images():
    """Test the save_images endpoint"""
    print("🧪 Testing save_images endpoint...")
    
    payload = {
        "region_name": "TEST_REGION_ISSUE", 
        "images": [
            {"name": "test_hillshade", "data": create_test_image_base64()},
            {"name": "test_slope", "data": create_test_image_base64()},
            {"name": "test_chm", "data": create_test_image_base64()}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/openai/save_images", json=payload)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ save_images successful:")
        print(f"   - Saved {len(result.get('saved_images', []))} images")
        print(f"   - Temp folder: {result.get('temp_folder_name')}")
        
        return result.get('temp_folder_name')
        
    except Exception as e:
        print(f"❌ save_images failed: {e}")
        return None

def test_send_to_openai(temp_folder_name):
    """Test the send_to_openai endpoint"""
    print("🚀 Testing send_to_openai endpoint...")
    
    payload = {
        "prompt": "Analyze these geospatial images for testing purposes.",
        "images": [],  # Using saved images, not data URLs
        "laz_name": "TEST_REGION_ISSUE", 
        "coordinates": {"lat": 42.0, "lng": -122.0},
        "model_name": "gpt-4o-mini",
        "temp_folder_name": temp_folder_name
    }
    
    try:
        # Note: This will fail with OpenAI API call but should still process the images
        response = requests.post(f"{BASE_URL}/api/openai/send", json=payload)
        result = response.json()
        
        if "error" in result:
            print(f"⚠️ OpenAI call failed (expected): {result.get('error')}")
        else:
            print(f"✅ send_to_openai successful")
            
        print(f"   - Log folder: {result.get('log_folder')}")
        return result.get('log_folder')
        
    except Exception as e:
        print(f"❌ send_to_openai failed: {e}")
        return None

def check_final_images(log_folder):
    """Check if images were copied to the final log folder"""
    if not log_folder:
        print("❌ No log folder to check")
        return
        
    print("🔍 Checking final image location...")
    
    log_path = Path(log_folder)
    sent_images_path = log_path / "sent_images"
    
    print(f"   - Log folder exists: {log_path.exists()}")
    print(f"   - sent_images folder exists: {sent_images_path.exists()}")
    
    if sent_images_path.exists():
        images = list(sent_images_path.glob("*.png"))
        print(f"   - Found {len(images)} images:")
        for img in images:
            print(f"     * {img.name}")
        
        if images:
            print("✅ Images successfully copied to final location!")
            return True
        else:
            print("❌ sent_images folder exists but contains no images!")
            return False
    else:
        print("❌ sent_images folder was not created!")
        return False

def main():
    print("🔬 Testing OpenAI image copying workflow...")
    print("=" * 60)
    
    # Step 1: Save images
    temp_folder_name = test_save_images()
    if not temp_folder_name:
        print("❌ Failed to save images, aborting test")
        return
    
    print("\n" + "=" * 60)
    
    # Step 2: Send to OpenAI (will copy images)
    log_folder = test_send_to_openai(temp_folder_name) 
    
    print("\n" + "=" * 60)
    
    # Step 3: Check final result
    success = check_final_images(log_folder)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: Images were successfully copied!")
    else:
        print("❌ TEST FAILED: Images were not copied correctly!")
    
    # Clean up test folders
    print("\n🧹 Cleaning up test folders...")
    logs_dir = Path("llm/logs")
    for folder in logs_dir.glob("TEST_REGION_ISSUE*"):
        try:
            if folder.is_dir():
                import shutil
                shutil.rmtree(folder)
                print(f"🗑️  Removed: {folder}")
        except Exception as e:
            print(f"⚠️ Could not remove {folder}: {e}")

if __name__ == "__main__":
    main()
