#!/usr/bin/env python3
"""
Debug the real OpenAI workflow by adding logging to see what's happening
"""

import sys
import json
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_log_files():
    """Debug existing log files to understand what went wrong"""
    print("🔍 Debugging existing log files...")
    
    logs_dir = Path("llm/logs")
    if not logs_dir.exists():
        print("❌ Logs directory doesn't exist!")
        return
    
    print(f"📁 Found logs directory: {logs_dir}")
    
    # List all log folders
    for log_folder in logs_dir.iterdir():
        if log_folder.is_dir():
            print(f"\n📂 Analyzing folder: {log_folder.name}")
            
            # Check for request_log.json
            request_log = log_folder / "request_log.json"
            if request_log.exists():
                print(f"   ✅ Found request_log.json")
                
                try:
                    with open(request_log, 'r') as f:
                        data = json.load(f)
                    
                    print(f"   📋 Region: {data.get('laz_name', 'Unknown')}")
                    print(f"   📋 Model: {data.get('model_name', 'Unknown')}")
                    
                    images = data.get('images', [])
                    print(f"   📋 Images logged: {len(images)}")
                    
                    if images:
                        for img in images:
                            print(f"      - {img.get('filename', 'Unknown')} ({img.get('size', 0)} bytes)")
                    else:
                        print("      ⚠️ No images found in log!")
                        
                except Exception as e:
                    print(f"   ❌ Error reading request_log.json: {e}")
            else:
                print(f"   ❌ No request_log.json found")
            
            # Check for sent_images folder
            sent_images = log_folder / "sent_images"
            if sent_images.exists():
                print(f"   ✅ Found sent_images folder")
                images = list(sent_images.glob("*.png"))
                print(f"   📋 PNG files in sent_images: {len(images)}")
                for img in images:
                    print(f"      - {img.name} ({img.stat().st_size} bytes)")
            else:
                print(f"   ❌ No sent_images folder found")

def check_temp_folders():
    """Check for any remaining temp folders"""
    print("\n🔍 Checking for temp folders...")
    
    logs_dir = Path("llm/logs")
    temp_folders = list(logs_dir.glob("*temp*"))
    
    if temp_folders:
        print(f"⚠️ Found {len(temp_folders)} temp folders:")
        for temp in temp_folders:
            print(f"   - {temp.name}")
            
            sent_images = temp / "sent_images"
            if sent_images.exists():
                images = list(sent_images.glob("*.png"))
                print(f"     📋 Contains {len(images)} images")
                for img in images:
                    print(f"        - {img.name} ({img.stat().st_size} bytes)")
            else:
                print(f"     ❌ No sent_images folder")
    else:
        print("✅ No temp folders found")

def main():
    print("🔬 Starting OpenAI workflow debug...")
    print("=" * 60)
    
    debug_log_files()
    check_temp_folders()
    
    print("\n" + "=" * 60)
    print("🎯 Debug Summary:")
    print("- Check if images are being saved during the save_images step")
    print("- Check if temp_folder_name is being passed correctly to send endpoint")
    print("- Check if the move operation is actually happening")
    print("- Look for any exceptions during the process")

if __name__ == "__main__":
    main()
