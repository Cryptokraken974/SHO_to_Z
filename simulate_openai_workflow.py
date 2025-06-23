#!/usr/bin/env python3
"""
Simulate sending OR_WizardIsland to OpenAI without actually calling the API.
This tests if the sent_images folder is created and images are copied correctly.
"""

import requests
import json
import base64
from pathlib import Path
import time

BASE_URL = "http://localhost:8000"

def create_realistic_images():
    """Create realistic test images with proper names"""
    # Simple 1x1 pixel PNG in base64
    test_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jINiGwAAAABJRU5ErkJggg=="
    
    return [
        {"name": "HillshadeRGB", "data": f"data:image/png;base64,{test_png_base64}"},
        {"name": "Slope", "data": f"data:image/png;base64,{test_png_base64}"},
        {"name": "CHM", "data": f"data:image/png;base64,{test_png_base64}"},
        {"name": "LRM", "data": f"data:image/png;base64,{test_png_base64}"},
        {"name": "SVF", "data": f"data:image/png;base64,{test_png_base64}"},
        {"name": "TintOverlay", "data": f"data:image/png;base64,{test_png_base64}"}
    ]

def simulate_openai_workflow():
    """Simulate the complete OpenAI workflow for OR_WizardIsland"""
    print("🎭 Simulating OpenAI workflow for OR_WizardIsland...")
    print("=" * 60)
    
    region_name = "OR_WizardIsland"
    
    # Step 1: Save images to temp folder (simulate image selection and saving)
    print(f"📸 Step 1: Saving images for {region_name}...")
    
    save_payload = {
        "region_name": region_name,
        "images": create_realistic_images()
    }
    
    try:
        save_response = requests.post(f"{BASE_URL}/api/openai/save_images", json=save_payload)
        if save_response.status_code != 200:
            print(f"❌ Save images failed: {save_response.status_code}")
            print(f"Response: {save_response.text}")
            return False
        
        save_result = save_response.json()
        temp_folder_name = save_result.get('temp_folder_name')
        saved_images_count = len(save_result.get('saved_images', []))
        
        print(f"✅ Saved {saved_images_count} images to temp folder: {temp_folder_name}")
        
    except Exception as e:
        print(f"❌ Error saving images: {e}")
        return False
    
    # Step 2: Simulate sending to OpenAI (but with empty response)
    print(f"\n🤖 Step 2: Simulating OpenAI send (no actual API call)...")
    
    # Create a mock send payload
    send_payload = {
        "prompt": "Analyze these terrain analysis images for archaeological features and anomalies.",
        "images": [],  # Using saved images from temp folder
        "laz_name": region_name,
        "coordinates": {"lat": 42.939, "lng": -122.144},
        "model_name": "gpt-4o-mini",
        "temp_folder_name": temp_folder_name
    }
    
    try:
        # This will try to call OpenAI but should handle the failure gracefully
        send_response = requests.post(f"{BASE_URL}/api/openai/send", json=send_payload)
        send_result = send_response.json()
        
        # Even if OpenAI call fails, the image copying should still work
        log_folder = send_result.get('log_folder')
        error_msg = send_result.get('error', '')
        
        print(f"📝 OpenAI call result: {send_result.get('response', 'No response')[:100]}...")
        if error_msg:
            print(f"⚠️ Expected error (no OpenAI API key): {error_msg[:100]}...")
        
        if log_folder:
            print(f"📁 Log folder created: {log_folder}")
            return check_sent_images_folder(log_folder)
        else:
            print("❌ No log folder was created!")
            return False
            
    except Exception as e:
        print(f"❌ Error during send simulation: {e}")
        return False

def check_sent_images_folder(log_folder):
    """Check if the sent_images folder was created and contains images"""
    print(f"\n🔍 Step 3: Checking sent_images folder...")
    
    log_path = Path(log_folder)
    sent_images_path = log_path / "sent_images"
    
    print(f"📂 Checking: {sent_images_path}")
    print(f"   - Log folder exists: {log_path.exists()}")
    print(f"   - sent_images folder exists: {sent_images_path.exists()}")
    
    if sent_images_path.exists():
        images = list(sent_images_path.glob("*.png"))
        print(f"   - Found {len(images)} images:")
        
        for img in images:
            size_kb = img.stat().st_size / 1024
            print(f"     * {img.name} ({size_kb:.1f} KB)")
        
        # Check the request_log.json for image entries
        log_file = log_path / "request_log.json"
        if log_file.exists():
            with open(log_file, 'r') as f:
                log_data = json.load(f)
            
            image_entries = log_data.get('images', [])
            print(f"   - Log file has {len(image_entries)} image entries")
            
            for entry in image_entries:
                print(f"     * {entry.get('filename', 'unknown')} ({entry.get('size', 0)} bytes)")
        
        return len(images) > 0
    else:
        print("❌ sent_images folder was not created!")
        return False

def cleanup_test_folders():
    """Clean up any test folders created during simulation"""
    print(f"\n🧹 Cleaning up test folders...")
    
    logs_dir = Path("llm/logs")
    if logs_dir.exists():
        # Look for OR_WizardIsland folders created during this test
        test_folders = []
        for folder in logs_dir.iterdir():
            if folder.is_dir() and "OR_WizardIsland" in folder.name:
                # Check if it's a recent folder (created in last 5 minutes)
                folder_age = time.time() - folder.stat().st_mtime
                if folder_age < 300:  # 5 minutes
                    test_folders.append(folder)
        
        if test_folders:
            print(f"Found {len(test_folders)} recent test folders:")
            for folder in test_folders:
                print(f"   - {folder.name}")
            
            response = input("Delete these test folders? (y/N): ")
            if response.lower() == 'y':
                import shutil
                for folder in test_folders:
                    try:
                        shutil.rmtree(folder)
                        print(f"🗑️  Removed: {folder.name}")
                    except Exception as e:
                        print(f"⚠️ Could not remove {folder.name}: {e}")
            else:
                print("Test folders kept for inspection.")
        else:
            print("No recent test folders found.")

def main():
    print("🎭 OpenAI Workflow Simulation for OR_WizardIsland")
    print("=" * 60)
    print("This test simulates clicking 'Send to OpenAI' without actually")
    print("sending the prompt, just to verify sent_images folder creation.")
    print("=" * 60)
    
    success = simulate_openai_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SIMULATION SUCCESS!")
        print("✅ sent_images folder was created and populated correctly")
        print("✅ Image copying workflow is working properly")
    else:
        print("❌ SIMULATION FAILED!")
        print("❌ sent_images folder was not created or is empty")
        print("❌ Image copying workflow needs debugging")
    
    print("\n" + "=" * 60)
    cleanup_test_folders()

if __name__ == "__main__":
    main()
