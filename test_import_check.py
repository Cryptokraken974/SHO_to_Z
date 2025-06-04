#!/usr/bin/env python3
"""
Simple test to verify the FastAPI app imports correctly
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_imports():
    """Test that all imports work correctly"""
    
    print("🧪 TESTING IMPORTS FOR FASTAPI INTEGRATION")
    print("=" * 50)
    
    try:
        print("📦 Testing main app import...")
        from app.main import app
        print("✅ Main app imported successfully")
        
        print("📦 Testing optimal elevation availability...")
        from app.main import OPTIMAL_ELEVATION_AVAILABLE
        print(f"✅ Optimal elevation available: {OPTIMAL_ELEVATION_AVAILABLE}")
        
        if OPTIMAL_ELEVATION_AVAILABLE:
            from app.main import optimal_elevation_api
            print("✅ Optimal elevation API instance available")
        
        print("\n🎯 INTEGRATION STATUS:")
        print(f"   FastAPI App: ✅ Ready")
        print(f"   Optimal Elevation: {'✅ Available' if OPTIMAL_ELEVATION_AVAILABLE else '❌ Not Available'}")
        
        print(f"\n📊 AVAILABLE ENDPOINTS:")
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method != 'HEAD':  # Skip HEAD methods
                        routes.append(f"   {method} {route.path}")
        
        elevation_routes = [route for route in routes if '/elevation' in route]
        print(f"   📈 Elevation endpoints: {len(elevation_routes)}")
        for route in elevation_routes:
            print(f"     {route}")
        
        print(f"\n🏁 IMPORT TEST COMPLETE")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n✅ All imports successful! FastAPI integration is ready.")
    else:
        print("\n❌ Import test failed.")
