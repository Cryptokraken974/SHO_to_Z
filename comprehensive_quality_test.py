#!/usr/bin/env python3
"""
Final Comprehensive API Quality Test
Tests multiple datasets and configurations for optimal TIFF quality
"""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path
import time
import json

load_dotenv()

def comprehensive_api_test():
    """Run comprehensive API tests"""
    api_key = os.getenv('OPENTOPOGRAPHY_API_KEY')
    output_dir = Path('Tests/final_api_quality')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🎯 COMPREHENSIVE API QUALITY TEST")
    print(f"📍 Region: 9.38°S, 62.67°W (Brazilian Amazon)")
    print(f"🔑 API Key: {api_key[:8]}...")
    print("="*60)
    
    # Test configurations
    test_configs = [
        {'name': 'Small_High_Detail', 'buffer': 0.05, 'desc': '5km area, high detail'},
        {'name': 'Medium_Balanced', 'buffer': 0.1, 'desc': '10km area, balanced'},
        {'name': 'Large_Regional', 'buffer': 0.2, 'desc': '20km area, regional'},
    ]
    
    # Datasets to test
    datasets = [
        ('COP30', 'Copernicus GLO-30'),
        ('NASADEM', 'NASADEM'),
        ('SRTMGL1', 'SRTM GL1'),
    ]
    
    results = []
    base_lat, base_lon = -9.38, -62.67
    
    for config in test_configs:
        print(f"\n🔍 {config['name']} - {config['desc']}")
        
        for dataset_code, dataset_name in datasets:
            print(f"  📡 {dataset_name}...", end='', flush=True)
            
            try:
                # Create bounding box
                buffer = config['buffer']
                params = {
                    'demtype': dataset_code,
                    'west': base_lon - buffer,
                    'south': base_lat - buffer,
                    'east': base_lon + buffer,
                    'north': base_lat + buffer,
                    'outputFormat': 'GTiff',
                    'API_Key': api_key
                }
                
                start_time = time.time()
                response = requests.get('https://portal.opentopography.org/API/globaldem', 
                                      params=params, timeout=120)
                download_time = time.time() - start_time
                
                if response.status_code == 200:
                    file_size = len(response.content)
                    
                    if file_size > 5000:  # At least 5KB
                        # Save file
                        filename = f"{dataset_code}_{config['name']}_{buffer*111:.0f}km.tif"
                        filepath = output_dir / filename
                        
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        # Quick analysis using gdalinfo
                        analysis = analyze_tiff_quick(filepath)
                        
                        result = {
                            'dataset': dataset_name,
                            'config': config['name'],
                            'area_km': f"{buffer*111:.0f}km",
                            'file_size_kb': round(file_size/1024, 1),
                            'download_time': round(download_time, 1),
                            'filename': filename,
                            'analysis': analysis,
                            'success': True
                        }
                        results.append(result)
                        
                        print(f" ✅ {file_size/1024:.0f}KB")
                        if analysis.get('dimensions'):
                            print(f"    📐 {analysis['dimensions']}")
                            
                    else:
                        print(f" ❌ Too small ({file_size}B)")
                        
                else:
                    print(f" ❌ Error {response.status_code}")
                    
            except Exception as e:
                print(f" ❌ Exception: {str(e)[:50]}")
                
    # Generate summary report
    print("\n" + "="*60)
    print("📊 FINAL RESULTS SUMMARY")
    print("="*60)
    
    if results:
        # Best by file size
        best_size = max(results, key=lambda x: x['file_size_kb'])
        print(f"🏆 Largest file: {best_size['dataset']} - {best_size['config']}")
        print(f"   📏 {best_size['file_size_kb']}KB - {best_size['filename']}")
        
        # Results by dataset
        print("\n📈 Results by Dataset:")
        for dataset_code, dataset_name in datasets:
            dataset_results = [r for r in results if r['dataset'] == dataset_name]
            if dataset_results:
                sizes = [r['file_size_kb'] for r in dataset_results]
                avg_size = sum(sizes) / len(sizes)
                max_size = max(sizes)
                print(f"  🔹 {dataset_name}: Avg {avg_size:.0f}KB, Max {max_size:.0f}KB")
        
        # Save detailed results
        with open(output_dir / 'results_summary.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📁 Files saved to: {output_dir}")
        print(f"📋 Detailed results: {output_dir}/results_summary.json")
        
    else:
        print("❌ No successful downloads")
    
    return results

def analyze_tiff_quick(filepath):
    """Quick TIFF analysis using gdalinfo"""
    try:
        import subprocess
        result = subprocess.run(['gdalinfo', str(filepath)], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            info = result.stdout
            
            # Extract key information
            analysis = {}
            for line in info.split('\n'):
                if 'Size is' in line:
                    parts = line.split('Size is')[1].strip().split(',')
                    if len(parts) >= 2:
                        width = int(parts[0].strip())
                        height = int(parts[1].strip())
                        analysis['dimensions'] = f"{width}×{height}"
                        
                elif 'Pixel Size' in line:
                    analysis['pixel_size'] = line.split('=')[1].strip() if '=' in line else 'unknown'
                    
            return analysis
            
    except Exception as e:
        return {'error': str(e)}
    
    return {}

if __name__ == "__main__":
    comprehensive_api_test()
