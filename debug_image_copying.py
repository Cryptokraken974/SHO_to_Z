#!/usr/bin/env python3
"""
Debug script to test the image copying issue in OpenAI analysis workflow.
This script simulates the process to identify where images are getting lost.
"""

import sys
import os
import base64
from pathlib import Path
import shutil
import uuid
import datetime
import json

# Add the project root to sys.path so we can import from app
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_test_images():
    """Create some test base64 images"""
    # Create a simple 1x1 pixel PNG in base64
    # This is a minimal valid PNG image
    test_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jINiGwAAAABJRU5ErkJggg=="
    
    return [
        {"name": "test_image_1", "data": f"data:image/png;base64,{test_png_base64}"},
        {"name": "test_image_2", "data": f"data:image/png;base64,{test_png_base64}"},
        {"name": "hillshade", "data": f"data:image/png;base64,{test_png_base64}"},
    ]

def simulate_save_images():
    """Simulate the save_images endpoint"""
    print("🧪 Testing image saving process...")
    
    LOG_DIR = Path("llm/logs")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    region_name = "TEST_REGION"
    images_data = create_test_images()
    
    # Generate folder structure similar to actual code
    clean_region = "".join(c for c in region_name if c.isalnum() or c in "_-")
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    
    # Create temporary folder
    temp_folder_name = f"{clean_region}_temp_{date_str}_{unique_id}"
    images_folder = LOG_DIR / temp_folder_name / "sent_images"
    images_folder.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Created temp folder: {images_folder}")
    
    saved_images = []
    for img_data in images_data:
        img_name = img_data.get("name", "unknown")
        img_base64 = img_data.get("data", "")
        
        # Handle data URL format
        if img_base64.startswith("data:image/"):
            img_base64 = img_base64.split(",", 1)[1]
        
        try:
            # Decode base64 image
            img_bytes = base64.b64decode(img_base64)
            
            # Save image file
            img_filename = f"{img_name}.png"
            img_path = images_folder / img_filename
            
            with open(img_path, "wb") as f:
                f.write(img_bytes)
            
            saved_images.append({
                "name": img_name,
                "path": str(img_path.relative_to(Path.cwd())),
                "filename": img_filename,
                "size": len(img_bytes)
            })
            
            print(f"💾 Saved image: {img_path}")
            
        except Exception as e:
            print(f"❌ Error saving image {img_name}: {e}")
            continue
    
    return {
        "saved_images": saved_images,
        "temp_folder_name": temp_folder_name,
        "images_folder": images_folder
    }

def simulate_send_to_openai(temp_folder_name, images_folder):
    """Simulate the send_to_openai function's image moving logic"""
    print("🚀 Testing OpenAI send process...")
    
    LOG_DIR = Path("llm/logs")
    
    # Simulate OpenAI response creation
    region_name = "TEST_REGION"
    model_name = "gpt-4o-mini"
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    
    # Create final log folder
    clean_region = "".join(c for c in region_name if c.isalnum() or c in "_-")
    clean_model = "".join(c for c in model_name.replace("-", "").replace(".", "") if c.isalnum())
    
    folder_name = f"{clean_region}_{clean_model}_{date_str}_{unique_id}"
    log_folder = LOG_DIR / folder_name
    log_folder.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Created final log folder: {log_folder}")
    
    # Check if temp folder exists
    temp_folder = LOG_DIR / temp_folder_name
    sent_images_folder = temp_folder / "sent_images"
    
    print(f"🔍 Looking for temp folder: {temp_folder}")
    print(f"🔍 Looking for sent_images folder: {sent_images_folder}")
    print(f"📂 Temp folder exists: {temp_folder.exists()}")
    print(f"📂 Sent images folder exists: {sent_images_folder.exists()}")
    
    if sent_images_folder.exists():
        print(f"📋 Contents of sent_images folder:")
        for item in sent_images_folder.iterdir():
            print(f"   - {item.name} ({'directory' if item.is_dir() else 'file'})")
        
        # Move the sent_images folder to the final log folder
        final_images_folder = log_folder / "sent_images"
        print(f"🚚 Moving {sent_images_folder} to {final_images_folder}")
        
        try:
            shutil.move(str(sent_images_folder), str(final_images_folder))
            print(f"✅ Successfully moved images folder")
            
            # Verify the move worked
            if final_images_folder.exists():
                print(f"📋 Contents of final sent_images folder:")
                for item in final_images_folder.iterdir():
                    print(f"   - {item.name} ({'directory' if item.is_dir() else 'file'})")
            else:
                print(f"❌ Final images folder doesn't exist after move!")
                
        except Exception as e:
            print(f"❌ Error moving images folder: {e}")
            return False
            
        # Clean up temp folder
        try:
            if temp_folder.exists():
                print(f"🧹 Cleaning up temp folder: {temp_folder}")
                temp_folder.rmdir()
                print(f"✅ Temp folder cleaned up successfully")
        except OSError as e:
            print(f"⚠️ Could not clean up temp folder: {e}")
    else:
        print(f"❌ Sent images folder not found: {sent_images_folder}")
        return False
    
    return True

def main():
    print("🔬 Starting image copying debug test...")
    print("=" * 50)
    
    # Step 1: Test image saving
    save_result = simulate_save_images()
    temp_folder_name = save_result["temp_folder_name"]
    images_folder = save_result["images_folder"]
    
    print("\n" + "=" * 50)
    
    # Step 2: Test image moving
    success = simulate_send_to_openai(temp_folder_name, images_folder)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Image copying test PASSED")
    else:
        print("❌ Image copying test FAILED")
    
    # Clean up test folders
    print("\n🧹 Cleaning up test folders...")
    LOG_DIR = Path("llm/logs")
    for folder in LOG_DIR.glob("TEST_REGION*"):
        try:
            if folder.is_dir():
                shutil.rmtree(folder)
                print(f"🗑️  Removed: {folder}")
        except Exception as e:
            print(f"⚠️ Could not remove {folder}: {e}")

if __name__ == "__main__":
    main()
