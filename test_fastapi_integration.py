#!/usr/bin/env python3
"""
Test the FastAPI optimal elevation integration
"""

import sys
import os
import requests
import uvicorn
import threading
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_fastapi_integration():
    """Test the FastAPI optimal elevation integration"""
    
    print("🧪 TESTING FASTAPI OPTIMAL ELEVATION INTEGRATION")
    print("=" * 60)
    
    # Start the FastAPI server in a separate thread
    def run_server():
        try:
            from app.main import app
            uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
        except Exception as e:
            print(f"❌ Server failed to start: {e}")
    
    # Start server in background
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print("⏳ Starting FastAPI server...")
    time.sleep(5)
    
    # Test the API endpoints
    base_url = "http://127.0.0.1:8000"
    
    tests = [
        {
            "name": "Health Check",
            "url": f"{base_url}/api/health",
            "method": "GET"
        },
        {
            "name": "Elevation Status",
            "url": f"{base_url}/api/elevation/status",
            "method": "GET"
        },
        {
            "name": "Elevation Datasets",
            "url": f"{base_url}/api/elevation/datasets",
            "method": "GET"
        },
        {
            "name": "Terrain Recommendations",
            "url": f"{base_url}/api/elevation/terrain-recommendations",
            "method": "GET"
        }
    ]
    
    for test in tests:
        try:
            print(f"\n🔍 Testing {test['name']}...")
            response = requests.get(test['url'], timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {test['name']}: SUCCESS (200)")
                data = response.json()
                if 'success' in data and data['success']:
                    print(f"   📊 API Response: {data.get('success', 'unknown')}")
                else:
                    print(f"   ⚠️  Response: {data}")
            else:
                print(f"❌ {test['name']}: FAILED ({response.status_code})")
                print(f"   Error: {response.text}")
        
        except requests.exceptions.ConnectionError:
            print(f"❌ {test['name']}: Connection failed (server not ready)")
        except Exception as e:
            print(f"❌ {test['name']}: {str(e)}")
    
    print(f"\n" + "=" * 60)
    print("🏁 FastAPI Integration Test Complete")
    print("💡 If tests passed, the optimal elevation integration is working!")
    
    # Keep server running for manual testing
    print("\n🌐 Server running at http://127.0.0.1:8000")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

if __name__ == "__main__":
    test_fastapi_integration()
