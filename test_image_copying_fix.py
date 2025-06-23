#!/usr/bin/env python3
"""
Test script to verify that images are properly copied to sent_images folder
"""

import requests
import json
from pathlib import Path
import time

def test_openai_image_copying():
    """Test that region images are copied to sent_images folder"""
    
    print("🧪 Testing OpenAI image copying functionality...")
    
    # Test parameters
    region_name = "OR_WizardIsland"
    test_prompt = "Analyze these LIDAR images and describe the terrain features."
    
    # Check if region has images
    region_png_outputs = Path("output") / region_name / "lidar" / "png_outputs"
    if not region_png_outputs.exists():
        print(f"❌ Region png_outputs folder not found: {region_png_outputs}")
        return False
    
    # List available images
    png_files = list(region_png_outputs.glob("*.png"))
    print(f"📁 Found {len(png_files)} PNG files in region folder:")
    for png_file in png_files:
        print(f"   - {png_file.name}")
    
    if not png_files:
        print(f"❌ No PNG files found in region folder")
        return False
    
    # Prepare request payload
    payload = {
        "prompt": test_prompt,
        "images": [],  # No images in the request itself
        "laz_name": region_name,
        "coordinates": {"lat": 43.1, "lng": -122.1},
        "model_name": "gpt-4o-mini",
        "temp_folder_name": None  # No temp folder - should use region images
    }
    
    # Make the request
    print(f"\n🚀 Sending OpenAI request...")
    print(f"   Region: {region_name}")
    print(f"   Expected to copy: {len(png_files)} images")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/openai/send",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        print(f"✅ Request successful")
        
        # Check the log folder and sent_images
        if "log_folder" in result:
            log_folder = Path(result["log_folder"])
            sent_images_folder = log_folder / "sent_images"
            
            print(f"\n📁 Checking sent_images folder: {sent_images_folder}")
            
            if sent_images_folder.exists():
                copied_files = list(sent_images_folder.glob("*.png"))
                print(f"✅ sent_images folder exists")
                print(f"📊 Found {len(copied_files)} copied images:")
                
                for copied_file in copied_files:
                    print(f"   - {copied_file.name} ({copied_file.stat().st_size} bytes)")
                
                # Check if all original images were copied
                original_names = {f.name for f in png_files}
                copied_names = {f.name for f in copied_files}
                
                if original_names == copied_names:
                    print(f"✅ All original images were copied successfully!")
                    return True
                else:
                    missing = original_names - copied_names
                    extra = copied_names - original_names
                    if missing:
                        print(f"❌ Missing images: {missing}")
                    if extra:
                        print(f"⚠️ Extra images: {extra}")
                    return False
            else:
                print(f"❌ sent_images folder was not created")
                return False
        else:
            print(f"❌ No log_folder in response")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_openai_image_copying()
    if success:
        print(f"\n🎉 Test PASSED: Images are properly copied to sent_images folder!")
    else:
        print(f"\n💥 Test FAILED: Images were not copied correctly")
