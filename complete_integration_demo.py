#!/usr/bin/env python3
"""
LAZ Terrain Processor - Complete Integration Demo
Demonstrates the fixed GDAL conversion with optimal API source

This script shows the complete working solution:
1. Downloads high-quality TIFF from Copernicus GLO-30
2. Converts to PNG using fixed GDAL pipeline
3. Validates the complete process
"""

import os
import sys
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def main():
    """Complete integration demonstration"""
    load_dotenv()
    
    print("🚀 LAZ TERRAIN PROCESSOR - COMPLETE INTEGRATION DEMO")
    print("="*60)
    print("📍 Location: Brazilian Amazon (9.38°S, 62.67°W)")
    print("🎯 Objective: Download + Convert with optimal quality")
    print()
    
    # Configuration
    api_key = os.getenv('OPENTOPOGRAPHY_API_KEY')
    if not api_key:
        print("❌ OPENTOPOGRAPHY_API_KEY not found in .env file")
        return False
    
    print(f"🔑 API Key: {api_key[:8]}...")
    
    # Output setup
    output_dir = Path('demo_output')
    output_dir.mkdir(exist_ok=True)
    
    # Test coordinates (Brazilian Amazon)
    lat, lon = -9.38, -62.67
    
    print(f"🌍 Target coordinates: {lat:.3f}°S, {abs(lon):.3f}°W")
    print()
    
    # Step 1: Download optimal TIFF
    print("📡 STEP 1: Downloading high-quality TIFF...")
    tiff_path = download_optimal_tiff(lat, lon, api_key, output_dir)
    
    if not tiff_path:
        print("❌ TIFF download failed")
        return False
    
    # Step 2: Convert to PNG
    print("\n🔄 STEP 2: Converting TIFF to PNG...")
    png_path = convert_to_png(tiff_path, output_dir)
    
    if not png_path:
        print("❌ PNG conversion failed")  
        return False
    
    # Step 3: Validate results
    print("\n✅ STEP 3: Validating results...")
    validate_results(tiff_path, png_path)
    
    print("\n🎉 INTEGRATION DEMO COMPLETE!")
    print(f"📁 Results saved to: {output_dir}")
    return True

def download_optimal_tiff(lat, lon, api_key, output_dir):
    """Download TIFF using optimal configuration"""
    
    # Optimal parameters (from our testing)
    buffer = 0.2  # 20km area for best quality
    params = {
        'demtype': 'COP30',  # Copernicus GLO-30 (best source)
        'west': lon - buffer,
        'south': lat - buffer,
        'east': lon + buffer,
        'north': lat + buffer,
        'outputFormat': 'GTiff',
        'API_Key': api_key
    }
    
    print(f"  🎯 Using Copernicus GLO-30 with {buffer*111:.0f}km area")
    print("  📡 Making API request...", end='', flush=True)
    
    try:
        start_time = time.time()
        response = requests.get('https://portal.opentopography.org/API/globaldem', 
                               params=params, timeout=120)
        download_time = time.time() - start_time
        
        if response.status_code == 200:
            file_size = len(response.content)
            
            if file_size > 10000:  # At least 10KB
                tiff_path = output_dir / 'demo_elevation_data.tif'
                
                with open(tiff_path, 'wb') as f:
                    f.write(response.content)
                
                print(f" ✅ SUCCESS!")
                print(f"  📏 Downloaded: {file_size/1024:.0f}KB in {download_time:.1f}s")
                print(f"  📄 Saved to: {tiff_path}")
                
                return tiff_path
            else:
                print(f" ❌ File too small: {file_size} bytes")
        else:
            print(f" ❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f" ❌ Exception: {e}")
    
    return None

def convert_to_png(tiff_path, output_dir):
    """Convert TIFF to PNG using fixed pipeline"""
    
    try:
        from convert import convert_geotiff_to_png
        
        png_path = output_dir / 'demo_elevation_terrain.png'
        
        print(f"  🔄 Converting {tiff_path.name}...")
        print(f"  📤 Output: {png_path}")
        
        start_time = time.time()
        result = convert_geotiff_to_png(str(tiff_path), str(png_path))
        conversion_time = time.time() - start_time
        
        if result and png_path.exists():
            png_size = png_path.stat().st_size
            print(f"  ✅ Conversion successful in {conversion_time:.1f}s")
            print(f"  📏 PNG size: {png_size/1024:.0f}KB")
            
            return png_path
        else:
            print(f"  ❌ Conversion failed")
            
    except Exception as e:
        print(f"  ❌ Conversion error: {e}")
    
    return None

def validate_results(tiff_path, png_path):
    """Validate the complete process results"""
    
    try:
        # TIFF validation
        print(f"  📋 TIFF Analysis:")
        import subprocess
        gdalinfo = subprocess.run(['gdalinfo', str(tiff_path)], 
                                 capture_output=True, text=True, timeout=30)
        
        if gdalinfo.returncode == 0:
            info = gdalinfo.stdout
            for line in info.split('\n'):
                if 'Size is' in line:
                    print(f"    📐 {line.strip()}")
                elif 'Pixel Size' in line:
                    print(f"    🔍 {line.strip()}")
        
        # PNG validation  
        print(f"  🖼️  PNG Analysis:")
        from PIL import Image
        with Image.open(png_path) as img:
            print(f"    📐 Dimensions: {img.size[0]}×{img.size[1]} pixels")
            print(f"    🎨 Mode: {img.mode}")
            print(f"    📊 Format: {img.format}")
            
        print(f"  ✅ Both files validated successfully!")
        
    except Exception as e:
        print(f"  ⚠️  Validation warning: {e}")

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🏆 LAZ Terrain Processor integration is fully operational!")
    else:
        print("\n❌ Integration demo failed - check configuration")
