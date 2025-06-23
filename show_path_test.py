#!/usr/bin/env python3
"""
Quick test to show the exact path where sent_images folder is created
"""

import requests
import json
import base64
from pathlib import Path

BASE_URL = "http://localhost:8000"

def show_sent_images_path():
    """Show where the sent_images folder gets created"""
    print("📍 Testing sent_images folder path creation...")
    
    # Simple test image
    test_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jINiGwAAAABJRU5ErkJggg=="
    
    # Step 1: Save images
    save_payload = {
        "region_name": "PATH_TEST",
        "images": [
            {"name": "test_image", "data": f"data:image/png;base64,{test_png_base64}"}
        ]
    }
    
    save_response = requests.post(f"{BASE_URL}/api/openai/save_images", json=save_payload)
    save_result = save_response.json()
    temp_folder_name = save_result.get('temp_folder_name')
    
    print(f"🔹 Temp folder created: {temp_folder_name}")
    temp_path = Path("llm/logs") / temp_folder_name / "sent_images"
    print(f"🔹 Full temp path: {temp_path.absolute()}")
    
    # Step 2: Send to OpenAI (this creates the final folder)
    send_payload = {
        "prompt": "Test prompt",
        "images": [],
        "laz_name": "PATH_TEST",
        "coordinates": {"lat": 0, "lng": 0},
        "model_name": "gpt-4o-mini",
        "temp_folder_name": temp_folder_name
    }
    
    send_response = requests.post(f"{BASE_URL}/api/openai/send", json=send_payload)
    send_result = send_response.json()
    log_folder = send_result.get('log_folder')
    
    if log_folder:
        final_path = Path(log_folder) / "sent_images"
        print(f"🔹 Final log folder: {log_folder}")
        print(f"🔹 Final sent_images path: {final_path.absolute()}")
        
        # Check if images exist
        if final_path.exists():
            images = list(final_path.glob("*.png"))
            print(f"🔹 Images found: {len(images)}")
            for img in images:
                print(f"   📸 {img.name}")
        else:
            print("❌ sent_images folder doesn't exist!")
    
    return log_folder

if __name__ == "__main__":
    log_folder = show_sent_images_path()
    print(f"\n📍 SUMMARY:")
    print(f"The sent_images folder is created at:")
    print(f"   {Path(log_folder).absolute()}/sent_images")
    print(f"\nFull absolute path:")
    print(f"   {(Path(log_folder) / 'sent_images').absolute()}")
