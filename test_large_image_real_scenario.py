#!/usr/bin/env python3
"""
Real-world test scenario for large image optimization
This script simulates the original NP_T-0251 issue with a truly large image
"""

import base64
import json
import time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

def create_large_test_image(width=12000, height=10000, filename="test_large_dsm.png"):
    """
    Create a large test image that simulates the original NP_T-0251 DSM
    This creates an image similar to what would cause browser decompression bomb warnings
    """
    print(f"🏗️  Creating large test image: {width}x{height} pixels")
    print(f"   Expected size: ~{(width * height * 3 / 1024 / 1024):.1f}MB uncompressed")
    
    # Create a realistic DSM-like image with elevation data patterns
    img = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(img)
    
    # Add realistic terrain-like patterns
    print("   🎨 Generating terrain patterns...")
    
    # Add some large-scale patterns (mountains, valleys)
    for i in range(20):
        x1 = np.random.randint(0, width//2)
        y1 = np.random.randint(0, height//2)
        x2 = x1 + np.random.randint(width//4, width//2)
        y2 = y1 + np.random.randint(height//4, height//2)
        
        # Create elevation-like colors (browns, greens, grays)
        color = (
            np.random.randint(50, 200),
            np.random.randint(40, 180), 
            np.random.randint(30, 150)
        )
        draw.ellipse([x1, y1, x2, y2], fill=color)
    
    # Add detail patterns to make it realistic
    for i in range(100):
        x1 = np.random.randint(0, width)
        y1 = np.random.randint(0, height)
        x2 = x1 + np.random.randint(10, 100)
        y2 = y1 + np.random.randint(10, 100)
        
        # Subtle terrain details
        color = (
            np.random.randint(80, 120),
            np.random.randint(70, 110),
            np.random.randint(60, 100)
        )
        draw.ellipse([x1, y1, x2, y2], fill=color, outline=color)
    
    print("   💾 Saving test image...")
    img.save(filename, 'PNG', optimize=False)
    
    file_size = Path(filename).stat().st_size
    print(f"   ✅ Created: {filename}")
    print(f"   📏 File size: {file_size / 1024 / 1024:.2f}MB")
    print(f"   🖼️  Dimensions: {width}x{height} ({width * height / 1_000_000:.1f}M pixels)")
    
    return filename, file_size

def convert_to_base64(image_path):
    """Convert image to base64 for testing"""
    print(f"🔄 Converting {image_path} to base64...")
    
    with open(image_path, 'rb') as img_file:
        img_data = img_file.read()
        base64_data = base64.b64encode(img_data).decode('utf-8')
    
    base64_size = len(base64_data)
    print(f"   📏 Base64 size: {base64_size / 1024 / 1024:.2f}MB")
    
    return base64_data, base64_size

def create_test_scenario(scenario_name, width, height):
    """Create a complete test scenario"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST SCENARIO: {scenario_name}")
    print(f"{'='*60}")
    
    # Create the large image
    filename = f"test_{scenario_name.lower().replace(' ', '_')}.png"
    image_path, file_size = create_large_test_image(width, height, filename)
    
    # Convert to base64
    base64_data, base64_size = convert_to_base64(image_path)
    
    # Analyze optimization needs
    pixels = width * height
    pixels_m = pixels / 1_000_000
    
    print(f"\n📊 OPTIMIZATION ANALYSIS:")
    print(f"   🖼️  Image: {width}x{height} ({pixels_m:.1f}M pixels)")
    print(f"   📁 File size: {file_size / 1024 / 1024:.2f}MB")
    print(f"   📋 Base64 size: {base64_size / 1024 / 1024:.2f}MB")
    
    # Check against our optimization thresholds
    compression_threshold = 25_000_000  # 25MB base64
    max_base64_size = 75_000_000       # 75MB base64
    max_pixels = 50_000_000            # 50M pixels
    pixel_compression_threshold = 25_000_000  # 25M pixels
    
    needs_optimization = False
    reasons = []
    
    if base64_size > max_base64_size:
        needs_optimization = True
        reasons.append(f"Base64 too large ({base64_size / 1024 / 1024:.1f}MB > 75MB)")
    elif base64_size > compression_threshold:
        needs_optimization = True
        reasons.append(f"Base64 exceeds compression threshold ({base64_size / 1024 / 1024:.1f}MB > 25MB)")
    
    if pixels > max_pixels:
        needs_optimization = True
        reasons.append(f"Too many pixels ({pixels_m:.1f}M > 50M)")
    elif pixels > pixel_compression_threshold:
        needs_optimization = True
        reasons.append(f"Pixels exceed compression threshold ({pixels_m:.1f}M > 25M)")
    
    print(f"\n🔧 OPTIMIZATION REQUIRED: {'YES' if needs_optimization else 'NO'}")
    if needs_optimization:
        print(f"   📝 Reasons:")
        for reason in reasons:
            print(f"      • {reason}")
        
        # Calculate target dimensions
        if pixels > max_pixels:
            scale_factor = (max_pixels / pixels) ** 0.5
            target_width = int(width * scale_factor)
            target_height = int(height * scale_factor)
            print(f"   🎯 Target dimensions: {target_width}x{target_height}")
            print(f"   📏 Scale factor: {scale_factor:.1%}")
        
    # Create test data for frontend
    test_data = {
        "scenario": scenario_name,
        "image_data": f"data:image/png;base64,{base64_data}",
        "original_size": {"width": width, "height": height},
        "file_size_mb": file_size / 1024 / 1024,
        "base64_size_mb": base64_size / 1024 / 1024,
        "pixels_m": pixels_m,
        "needs_optimization": needs_optimization,
        "optimization_reasons": reasons
    }
    
    # Save test data
    test_file = f"test_data_{scenario_name.lower().replace(' ', '_')}.json"
    with open(test_file, 'w') as f:
        # Save without the large base64 data to avoid huge files
        summary_data = test_data.copy()
        del summary_data["image_data"]
        json.dump(summary_data, f, indent=2)
    
    print(f"   💾 Test data saved: {test_file}")
    
    # Cleanup large image file
    Path(image_path).unlink()
    print(f"   🗑️  Cleaned up: {image_path}")
    
    return test_data

def main():
    """Run comprehensive large image testing scenarios"""
    print("🧪 LARGE IMAGE OPTIMIZATION - REAL WORLD TEST SCENARIOS")
    print("="*70)
    
    scenarios = [
        ("Small Image", 2048, 2048),           # 4M pixels - no optimization needed
        ("Medium Image", 4096, 4096),          # 16M pixels - no optimization needed  
        ("Large Image", 8192, 8192),           # 67M pixels - optimization needed
        ("Huge Image (NP_T-0251)", 12000, 10000),  # 120M pixels - aggressive optimization
        ("Extreme Image", 15000, 12000),       # 180M pixels - maximum compression
    ]
    
    results = []
    
    for scenario_name, width, height in scenarios:
        try:
            test_data = create_test_scenario(scenario_name, width, height)
            results.append(test_data)
        except Exception as e:
            print(f"❌ Failed to create {scenario_name}: {e}")
    
    # Summary report
    print(f"\n{'='*70}")
    print("📊 TEST SCENARIOS SUMMARY")
    print(f"{'='*70}")
    
    for result in results:
        print(f"\n🧪 {result['scenario']}:")
        print(f"   📏 Size: {result['original_size']['width']}x{result['original_size']['height']}")
        print(f"   🖼️  Pixels: {result['pixels_m']:.1f}M")
        print(f"   📁 Base64: {result['base64_size_mb']:.1f}MB")
        print(f"   🔧 Needs optimization: {'YES' if result['needs_optimization'] else 'NO'}")
        if result['needs_optimization']:
            print(f"      Reasons: {', '.join(result['optimization_reasons'])}")
    
    print(f"\n✅ All test scenarios completed!")
    print(f"🎯 Use the demo page to test frontend optimization with these scenarios")
    print(f"📋 Test data files created for integration testing")

if __name__ == "__main__":
    main()
