#!/usr/bin/env python3
"""
Create realistic large DSM-like images that will trigger base64 size limits
This simulates the actual data density of DSM images
"""

import base64
import json
import numpy as np
from PIL import Image
import random

def create_realistic_dsm_image(width, height, filename):
    """
    Create a realistic DSM image with high data density that won't compress well
    This simulates actual elevation data with noise and complexity
    """
    print(f"🏗️  Creating realistic DSM: {width}x{height} pixels")
    
    # Create numpy array for elevation data
    # Use random noise to simulate actual DSM complexity
    elevation_data = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    
    # Add realistic terrain features that don't compress well
    # Create high-frequency noise that simulates measurement precision
    noise = np.random.randint(-30, 30, (height, width, 3)).astype(np.int16)
    elevation_data = np.clip(elevation_data.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Add some structure but keep high entropy
    for i in range(height//100):
        for j in range(width//100):
            # Add small variations that prevent compression
            y_start = i * 100
            y_end = min((i + 1) * 100, height)
            x_start = j * 100  
            x_end = min((j + 1) * 100, width)
            
            # Random elevation shift with noise
            shift = np.random.randint(-50, 50)
            elevation_data[y_start:y_end, x_start:x_end] = np.clip(
                elevation_data[y_start:y_end, x_start:x_end].astype(np.int16) + shift, 
                0, 255
            ).astype(np.uint8)
    
    # Convert to PIL Image
    img = Image.fromarray(elevation_data, 'RGB')
    
    print("   💾 Saving realistic DSM image...")
    # Save without compression to maximize file size
    img.save(filename, 'PNG', optimize=False, compress_level=0)
    
    from pathlib import Path
    file_size = Path(filename).stat().st_size
    print(f"   ✅ Created: {filename}")
    print(f"   📏 File size: {file_size / 1024 / 1024:.2f}MB")
    print(f"   🖼️  Dimensions: {width}x{height} ({width * height / 1_000_000:.1f}M pixels)")
    
    return filename, file_size

def test_realistic_scenarios():
    """Test with more realistic DSM data sizes that trigger optimization"""
    
    print("🧪 REALISTIC DSM OPTIMIZATION TEST")
    print("="*50)
    
    # Test scenarios designed to trigger different optimization thresholds
    scenarios = [
        {
            "name": "Moderate DSM", 
            "width": 4000, 
            "height": 4000,
            "description": "16M pixels - may trigger pixel-based optimization"
        },
        {
            "name": "Large DSM", 
            "width": 6000, 
            "height": 6000,
            "description": "36M pixels - should trigger optimization"
        },
        {
            "name": "Huge DSM (NP_T-0251 style)", 
            "width": 8000, 
            "height": 8000,
            "description": "64M pixels - aggressive optimization needed"
        },
        {
            "name": "Extreme DSM", 
            "width": 10000, 
            "height": 7000,
            "description": "70M pixels - maximum optimization"
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"🧪 {scenario['name']} - {scenario['description']}")
        print(f"{'='*60}")
        
        try:
            # Create realistic DSM
            filename = f"realistic_{scenario['name'].lower().replace(' ', '_')}.png"
            image_path, file_size = create_realistic_dsm_image(
                scenario['width'], 
                scenario['height'], 
                filename
            )
            
            # Convert to base64
            print(f"🔄 Converting to base64...")
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                base64_data = base64.b64encode(img_data).decode('utf-8')
            
            base64_size = len(base64_data)
            print(f"   📏 Base64 size: {base64_size / 1024 / 1024:.2f}MB")
            
            # Check optimization requirements
            pixels = scenario['width'] * scenario['height']
            pixels_m = pixels / 1_000_000
            
            # Our thresholds
            compression_threshold = 25_000_000  # 25MB base64
            max_base64_size = 75_000_000       # 75MB base64
            max_pixels = 50_000_000            # 50M pixels
            pixel_compression_threshold = 25_000_000  # 25M pixels
            
            needs_optimization = False
            reasons = []
            optimization_type = "none"
            
            if base64_size > max_base64_size:
                needs_optimization = True
                optimization_type = "aggressive"
                reasons.append(f"Base64 too large ({base64_size / 1024 / 1024:.1f}MB > 75MB)")
            elif base64_size > compression_threshold:
                needs_optimization = True
                optimization_type = "standard"
                reasons.append(f"Base64 exceeds compression threshold ({base64_size / 1024 / 1024:.1f}MB > 25MB)")
            
            if pixels > max_pixels:
                needs_optimization = True
                if optimization_type == "none":
                    optimization_type = "pixel-based"
                reasons.append(f"Too many pixels ({pixels_m:.1f}M > 50M)")
            elif pixels > pixel_compression_threshold:
                needs_optimization = True
                if optimization_type == "none":
                    optimization_type = "compression"
                reasons.append(f"Pixels exceed compression threshold ({pixels_m:.1f}M > 25M)")
            
            print(f"\n📊 OPTIMIZATION ANALYSIS:")
            print(f"   🖼️  Pixels: {pixels_m:.1f}M")
            print(f"   📁 File size: {file_size / 1024 / 1024:.2f}MB")
            print(f"   📋 Base64 size: {base64_size / 1024 / 1024:.2f}MB")
            print(f"   🔧 Optimization needed: {'YES' if needs_optimization else 'NO'}")
            print(f"   ⚙️  Optimization type: {optimization_type}")
            
            if needs_optimization:
                print(f"   📝 Reasons:")
                for reason in reasons:
                    print(f"      • {reason}")
                
                # Calculate expected optimization
                if pixels > max_pixels:
                    scale_factor = (max_pixels / pixels) ** 0.5
                    target_width = int(scenario['width'] * scale_factor)
                    target_height = int(scenario['height'] * scale_factor)
                    expected_reduction = 1 - (target_width * target_height) / pixels
                    print(f"   🎯 Target dimensions: {target_width}x{target_height}")
                    print(f"   📏 Expected size reduction: {expected_reduction:.1%}")
            
            # Save result
            result = {
                "scenario": scenario['name'],
                "dimensions": f"{scenario['width']}x{scenario['height']}",
                "pixels_m": pixels_m,
                "file_size_mb": file_size / 1024 / 1024,
                "base64_size_mb": base64_size / 1024 / 1024,
                "needs_optimization": needs_optimization,
                "optimization_type": optimization_type,
                "reasons": reasons
            }
            results.append(result)
            
            # Cleanup
            from pathlib import Path
            Path(image_path).unlink()
            print(f"   🗑️  Cleaned up: {image_path}")
            
        except Exception as e:
            print(f"❌ Error in {scenario['name']}: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 REALISTIC DSM TEST SUMMARY")
    print(f"{'='*60}")
    
    for result in results:
        print(f"\n🧪 {result['scenario']}:")
        print(f"   📏 {result['dimensions']} ({result['pixels_m']:.1f}M pixels)")
        print(f"   📁 File: {result['file_size_mb']:.1f}MB → Base64: {result['base64_size_mb']:.1f}MB")
        print(f"   🔧 Optimization: {result['optimization_type']}")
        if result['needs_optimization']:
            print(f"      • {'; '.join(result['reasons'])}")
    
    print(f"\n✅ Realistic DSM testing completed!")
    print(f"🎯 These scenarios demonstrate when our optimization system activates")
    
    return results

if __name__ == "__main__":
    test_realistic_scenarios()
