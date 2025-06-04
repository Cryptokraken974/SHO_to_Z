#!/usr/bin/env python3
"""
Test the enhanced resolution by downloading and processing a small sample
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.data_acquisition.sources.opentopography import OpenTopographySource
from app.data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
from app.data_acquisition.utils.coordinates import BoundingBox

async def test_enhanced_resolution():
    """Test enhanced resolution with actual data download"""
    print("="*70)
    print("🎯 ENHANCED RESOLUTION - REAL DATA TEST")
    print("="*70)
    
    # Create a small test area - Portland, Oregon (known to have 3DEP data)
    bbox = BoundingBox(
        north=45.525,   # Portland, Oregon area
        south=45.515,
        east=-122.675,
        west=-122.685
    )
    
    # Create download request with HIGH resolution
    request = DownloadRequest(
        bbox=bbox,
        data_type=DataType.ELEVATION,  # Test elevation (DEM) generation
        resolution=DataResolution.HIGH,  # Use the enhanced HIGH resolution
        max_file_size_mb=100
    )
    
    print(f"📍 Test Coordinates: {bbox.north:.3f}N to {bbox.south:.3f}N, {abs(bbox.west):.3f}W to {abs(bbox.east):.3f}W")
    print(f"📏 Resolution Level: HIGH (Enhanced)")
    print(f"🎯 Expected DEM Resolution: 0.05m (was 0.5m)")
    print(f"🖼️  Expected Image Quality: ~715×725 pixels (vs previous 130×130)")
    
    # Initialize OpenTopography source
    source = OpenTopographySource()
    
    try:
        print(f"\n🔍 Checking data availability...")
        available = await source.check_availability(request)
        
        if not available:
            print("❌ No data available for this area")
            return
            
        print("✅ Data available!")
        
        # Get estimated size
        estimated_size = await source.estimate_size(request)
        print(f"📊 Estimated download size: {estimated_size:.1f} MB")
        
        # Download with progress tracking
        print(f"\n🚀 Starting enhanced resolution download...")
        
        async def progress_callback(update):
            print(f"   📡 {update.get('message', 'Processing...')}")
        
        result = await source.download(request, progress_callback)
        
        if result.success:
            print(f"\n✅ DOWNLOAD SUCCESSFUL!")
            print(f"📁 File: {result.file_path}")
            print(f"📊 Size: {result.file_size_mb:.1f} MB") 
            print(f"📏 Resolution: {result.resolution_m}m")
            
            # Check if we have PNG outputs to compare
            file_path = Path(result.file_path)
            if file_path.exists():
                # Look for PNG outputs in the same directory structure
                base_dir = file_path.parent
                png_dir = base_dir / "png_outputs"
                
                print(f"\n🔍 Checking for PNG outputs in: {png_dir}")
                
                if png_dir.exists():
                    png_files = list(png_dir.glob("*.png"))
                    if png_files:
                        print(f"🖼️  Found {len(png_files)} PNG files:")
                        for png_file in png_files:
                            print(f"   📄 {png_file.name}")
                        
                        # Check dimensions of the first PNG
                        try:
                            from PIL import Image
                            first_png = png_files[0]
                            with Image.open(first_png) as img:
                                width, height = img.size
                                print(f"\n📐 PNG Dimensions: {width}×{height} pixels")
                                print(f"🎯 Target was: 715×725 pixels")
                                if width >= 600 and height >= 600:
                                    print("✅ SUCCESS: Achieved high resolution comparable to OpenTopography!")
                                else:
                                    print("⚠️  Resolution lower than expected")
                        except ImportError:
                            print("📝 Install Pillow to check PNG dimensions: pip install Pillow")
                        except Exception as e:
                            print(f"⚠️  Could not check PNG dimensions: {e}")
                    else:
                        print("📝 No PNG files found yet (processing may still be running)")
                else:
                    print("📝 PNG output directory not found yet")
        else:
            print(f"❌ Download failed: {result.error_message}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await source.close()
        
    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(test_enhanced_resolution())
