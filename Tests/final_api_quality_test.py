#!/usr/bin/env python3
"""
Final API Quality Test - Focus on Best Sources
Tests and downloads high-quality TIFF files for region 9.38S_62.67W
"""

import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_environment():
    """Load environment variables"""
    from dotenv import load_dotenv
    load_dotenv()

class FinalAPITest:
    """Final comprehensive API test for best TIFF quality"""
    
    def __init__(self):
        self.test_lat = -9.38
        self.test_lon = -62.67
        self.output_dir = Path("Tests/final_api_quality")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        
        load_environment()
        self.api_key = os.getenv('OPENTOPOGRAPHY_API_KEY')
        
        print("🎯 Final API Quality Test for LAZ Terrain Processor")
        print(f"📍 Region: {self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W (Brazilian Amazon)")
        print(f"🔑 API Key available: {bool(self.api_key)}")
        print(f"📁 Output directory: {self.output_dir}")
    
    def test_optimal_configurations(self):
        """Test different API configurations for optimal TIFF quality"""
        
        # Test configurations optimized for different use cases
        test_configs = [
            {
                'name': 'High Detail - Small Area',
                'buffer': 0.05,  # ~5km
                'description': 'Best for detailed terrain analysis'
            },
            {
                'name': 'Balanced - Medium Area', 
                'buffer': 0.1,   # ~10km
                'description': 'Good balance of detail and coverage'
            },
            {
                'name': 'Regional - Large Area',
                'buffer': 0.2,   # ~20km  
                'description': 'Best for regional analysis'
            }
        ]
        
        # Test best datasets
        datasets = [
            ('COP30', 'Copernicus GLO-30', 'Best global coverage'),
            ('NASADEM', 'NASADEM', 'Void-filled SRTM enhancement'),
            ('SRTMGL1', 'SRTM GL1', 'Classic SRTM 30m')
        ]
        
        for config in test_configs:
            print(f"\\n🔍 Testing {config['name']} ({config['description']})")
            
            for dataset_code, dataset_name, description in datasets:
                self._test_dataset_config(dataset_code, dataset_name, description, config)
    
    def _test_dataset_config(self, dataset_code, dataset_name, description, config):
        """Test specific dataset with configuration"""
        start_time = time.time()
        
        try:
            # Create bounding box
            buffer = config['buffer']
            bbox = {
                'west': self.test_lon - buffer,
                'east': self.test_lon + buffer,
                'south': self.test_lat - buffer,
                'north': self.test_lat + buffer
            }
            
            # API parameters
            params = {
                'demtype': dataset_code,
                'west': bbox['west'],
                'south': bbox['south'],
                'east': bbox['east'],
                'north': bbox['north'],
                'outputFormat': 'GTiff'
            }
            
            if self.api_key:
                params['API_Key'] = self.api_key
            
            print(f"  📡 {dataset_name} ({buffer*111:.0f}km area)...", end='')
            
            # Make request
            url = 'https://portal.opentopography.org/API/globaldem'
            response = requests.get(url, params=params, timeout=120)
            
            download_time = time.time() - start_time
            
            if response.status_code == 200:
                file_size = len(response.content)
                
                if file_size > 10000:  # Minimum 10KB for valid data
                    # Save file
                    filename = f"{dataset_code}_{config['name'].replace(' ', '_').replace('-', '')}_{buffer*111:.0f}km.tif"
                    filepath = self.output_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    # Analyze file
                    analysis = self._analyze_tiff_file(filepath)
                    
                    result = {
                        'dataset': dataset_name,
                        'dataset_code': dataset_code,
                        'config_name': config['name'],
                        'area_description': config['description'],
                        'area_km': f"{buffer*111:.0f}km",
                        'file_size_bytes': file_size,
                        'file_size_mb': round(file_size / (1024*1024), 2),
                        'download_time_seconds': round(download_time, 1),
                        'filename': filename,
                        'filepath': str(filepath),
                        'analysis': analysis,
                        'success': True,
                        'error': None
                    }
                    
                    self.results.append(result)
                    
                    print(f" ✅ {file_size/1024:.0f}KB")
                    if analysis.get('dimensions'):
                        dims = analysis['dimensions']
                        print(f"    📐 {dims['width']}×{dims['height']} pixels")
                        
                else:
                    print(f" ❌ File too small ({file_size} bytes)")
                    self._log_failed_result(dataset_name, config, download_time, f"File too small: {file_size} bytes")
                    
            else:
                error_msg = response.text[:100] if response.text else f"HTTP {response.status_code}"
                print(f" ❌ {response.status_code}")
                self._log_failed_result(dataset_name, config, download_time, error_msg)
                
        except Exception as e:
            download_time = time.time() - start_time
            print(f" ❌ Error: {str(e)[:50]}")
            self._log_failed_result(dataset_name, config, download_time, str(e))
    
    def _log_failed_result(self, dataset_name, config, download_time, error):
        """Log failed test result"""
        result = {
            'dataset': dataset_name,
            'config_name': config['name'],
            'area_description': config['description'],
            'download_time_seconds': round(download_time, 1),
            'success': False,
            'error': error
        }
        self.results.append(result)
    
    def _analyze_tiff_file(self, filepath):
        """Analyze TIFF file quality"""
        analysis = {
            'gdal_available': False,
            'dimensions': None,
            'pixel_size': None,
            'data_stats': None,
            'quality_score': 0
        }
        
        try:
            from osgeo import gdal
            gdal.UseExceptions()
            analysis['gdal_available'] = True
            
            dataset = gdal.Open(str(filepath))
            if dataset:
                # Basic info
                width = dataset.RasterXSize
                height = dataset.RasterYSize
                bands = dataset.RasterCount
                
                analysis['dimensions'] = {
                    'width': width,
                    'height': height,
                    'bands': bands,
                    'total_pixels': width * height
                }
                
                # Geospatial info
                geotransform = dataset.GetGeoTransform()
                pixel_size_x = abs(geotransform[1])
                pixel_size_y = abs(geotransform[5])
                
                analysis['pixel_size'] = {
                    'degrees_x': pixel_size_x,
                    'degrees_y': pixel_size_y,
                    'meters_approx': pixel_size_x * 111320 * 0.8  # Rough estimate for this latitude
                }
                
                # Data statistics (if numpy available)
                try:
                    import numpy as np
                    band = dataset.GetRasterBand(1)
                    data = band.ReadAsArray()
                    
                    if data is not None:
                        # Remove nodata values
                        nodata = band.GetNoDataValue()
                        if nodata is not None:
                            valid_data = data[data != nodata]
                        else:
                            valid_data = data.flatten()
                        
                        if len(valid_data) > 0:
                            analysis['data_stats'] = {
                                'min': float(np.min(valid_data)),
                                'max': float(np.max(valid_data)),
                                'mean': float(np.mean(valid_data)),
                                'std': float(np.std(valid_data)),
                                'valid_pixels': len(valid_data),
                                'coverage_percent': round(len(valid_data) / data.size * 100, 1)
                            }
                            
                except ImportError:
                    pass
                
                # Calculate quality score
                analysis['quality_score'] = self._calculate_quality_score(analysis)
                
                dataset = None
                
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _calculate_quality_score(self, analysis):
        """Calculate quality score (0-100)"""
        score = 0
        
        # Dimensions score (40 points max)
        if analysis.get('dimensions'):
            total_pixels = analysis['dimensions']['total_pixels']
            if total_pixels > 1000000:    # > 1M pixels
                score += 40
            elif total_pixels > 500000:   # > 500K pixels  
                score += 35
            elif total_pixels > 100000:   # > 100K pixels
                score += 30
            elif total_pixels > 50000:    # > 50K pixels
                score += 25
            elif total_pixels > 10000:    # > 10K pixels
                score += 20
            else:
                score += 10
        
        # Resolution score (30 points max)
        if analysis.get('pixel_size'):
            meters = analysis['pixel_size']['meters_approx']
            if meters < 10:       # < 10m
                score += 30
            elif meters < 20:     # < 20m
                score += 25
            elif meters < 30:     # < 30m
                score += 20
            elif meters < 50:     # < 50m
                score += 15
            else:
                score += 10
        
        # Data coverage score (20 points max)
        if analysis.get('data_stats'):
            coverage = analysis['data_stats']['coverage_percent']
            if coverage > 95:
                score += 20
            elif coverage > 90:
                score += 18
            elif coverage > 80:
                score += 15
            elif coverage > 70:
                score += 12
            else:
                score += 8
        
        # Elevation range score (10 points max)
        if analysis.get('data_stats'):
            elev_range = analysis['data_stats']['max'] - analysis['data_stats']['min']
            if elev_range > 500:
                score += 10
            elif elev_range > 200:
                score += 8
            elif elev_range > 100:
                score += 6
            else:
                score += 4
        
        return min(score, 100)
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        print("\\n" + "="*80)
        print("📊 FINAL API QUALITY TEST RESULTS")
        print("="*80)
        
        successful_results = [r for r in self.results if r['success']]
        failed_results = [r for r in self.results if not r['success']]
        
        print(f"\\n📍 Test Region: {self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📈 Total Tests: {len(self.results)}")
        print(f"✅ Successful: {len(successful_results)}")
        print(f"❌ Failed: {len(failed_results)}")
        
        if successful_results:
            # Sort by quality score
            successful_results.sort(key=lambda x: x['analysis'].get('quality_score', 0), reverse=True)
            
            print("\\n🏆 TOP 5 BEST QUALITY SOURCES:")
            print("-" * 60)
            
            for i, result in enumerate(successful_results[:5], 1):
                analysis = result['analysis']
                quality_score = analysis.get('quality_score', 0)
                
                print(f"{i}. 🥇 {result['dataset']} ({result['config_name']})")
                print(f"   📊 Quality Score: {quality_score}/100")
                print(f"   💾 File Size: {result['file_size_mb']} MB")
                print(f"   📐 Area: {result['area_km']} ({result['area_description']})")
                
                if analysis.get('dimensions'):
                    dims = analysis['dimensions']
                    print(f"   🖼️  Dimensions: {dims['width']}×{dims['height']} pixels ({dims['total_pixels']:,} total)")
                
                if analysis.get('pixel_size'):
                    ps = analysis['pixel_size']
                    print(f"   🎯 Resolution: ~{ps['meters_approx']:.0f}m per pixel")
                
                if analysis.get('data_stats'):
                    ds = analysis['data_stats']
                    print(f"   🏔️  Elevation: {ds['min']:.0f}m to {ds['max']:.0f}m (range: {ds['max']-ds['min']:.0f}m)")
                    print(f"   📈 Data Coverage: {ds['coverage_percent']}%")
                
                print(f"   📄 File: {result['filename']}")
                print()
            
            # Recommendations
            best_result = successful_results[0]
            print("🎯 RECOMMENDATION:")
            print("-" * 40)
            print(f"🥇 Best Source: {best_result['dataset']} ({best_result['config_name']})")
            print(f"📊 Quality Score: {best_result['analysis']['quality_score']}/100")
            print(f"💡 Use Case: {best_result['area_description']}")
            print(f"📄 File: {best_result['filename']}")
            print()
            
            # Save detailed report
            report_data = {
                'test_summary': {
                    'region': f"{self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W",
                    'test_date': datetime.now().isoformat(),
                    'total_tests': len(self.results),
                    'successful_tests': len(successful_results),
                    'failed_tests': len(failed_results)
                },
                'best_source': {
                    'dataset': best_result['dataset'],
                    'config': best_result['config_name'],
                    'quality_score': best_result['analysis']['quality_score'],
                    'file_size_mb': best_result['file_size_mb'],
                    'filename': best_result['filename']
                },
                'all_results': self.results
            }
            
            report_file = self.output_dir / f"final_api_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            print(f"📄 Detailed report saved: {report_file}")
            
        else:
            print("\\n❌ No successful downloads found.")
            print("Check API credentials and network connectivity.")
        
        # List downloaded files
        tiff_files = list(self.output_dir.glob("*.tif"))
        if tiff_files:
            print(f"\\n📁 Downloaded Files ({len(tiff_files)} total):")
            for tiff_file in tiff_files:
                size_mb = tiff_file.stat().st_size / (1024*1024)
                print(f"   📄 {tiff_file.name} ({size_mb:.2f} MB)")
        
        print("\\n" + "="*80)
        print("🎉 FINAL API QUALITY TEST COMPLETE!")
        print(f"📊 Results saved to: {self.output_dir}")
        print("="*80)

def main():
    """Run final API quality test"""
    tester = FinalAPITest()
    tester.test_optimal_configurations()
    tester.generate_final_report()

if __name__ == "__main__":
    main()
