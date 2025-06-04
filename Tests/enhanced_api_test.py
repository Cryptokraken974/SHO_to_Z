#!/usr/bin/env python3
"""
Enhanced API Testing Suite for High-Quality TIFF Sources
Focuses on obtaining larger, higher quality elevation data files
Target Region: 9.38S_62.67W (Brazilian Amazon)
"""

import sys
import os
import time
import requests
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_environment():
    """Load environment variables"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        return True
    except ImportError:
        print("⚠️  python-dotenv not installed. Using system environment variables.")
        return False

class EnhancedAPITester:
    """Enhanced API testing for better quality sources"""
    
    def __init__(self, test_region: Tuple[float, float]):
        self.test_lat, self.test_lon = test_region
        self.results = []
        self.output_dir = Path("Tests/enhanced_api_tests")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load credentials
        load_environment()
        self.opentopo_api_key = os.getenv('OPENTOPOGRAPHY_API_KEY')
        self.opentopo_username = os.getenv('OPENTOPO_USERNAME')
        self.opentopo_password = os.getenv('OPENTOPO_PASSWORD')
        
        print(f"🎯 Enhanced API testing for region: {self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W")
        print(f"📁 Results will be saved to: {self.output_dir}")
    
    def log_result(self, source: str, test_type: str, success: bool, 
                  file_size: int = 0, resolution: str = "Unknown", 
                  error: str = None, download_time: float = 0, 
                  dimensions: Dict = None, metadata: Dict = None):
        """Log test result with enhanced metrics"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'test_type': test_type,
            'region': f"{self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W",
            'success': success,
            'file_size_bytes': file_size,
            'file_size_mb': round(file_size / (1024*1024), 3) if file_size > 0 else 0,
            'resolution': resolution,
            'download_time_seconds': round(download_time, 2),
            'dimensions': dimensions or {},
            'error': error,
            'metadata': metadata or {}
        }
        self.results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {source}: Size={result['file_size_mb']}MB, Time={result['download_time_seconds']}s")
        if dimensions:
            print(f"   📐 Dimensions: {dimensions.get('width', '?')}×{dimensions.get('height', '?')} pixels")
        if error:
            print(f"   Error: {error}")
    
    def test_larger_areas_opentopo(self):
        """Test OpenTopography with larger bounding boxes for better quality"""
        print("\\n🌍 Testing OpenTopography with Enhanced Parameters...")
        
        # Test different buffer sizes for better quality
        buffer_tests = [
            (0.05, "5km area"),   # ~5km x 5km
            (0.1, "10km area"),   # ~10km x 10km
            (0.2, "20km area"),   # ~20km x 20km
        ]
        
        datasets = [
            ('COP30', 'Copernicus GLO-30'),
            ('NASADEM', 'NASADEM'),
            ('SRTMGL1', 'SRTM GL1 30m')
        ]
        
        for buffer, area_desc in buffer_tests:
            for dataset_code, dataset_name in datasets:
                self._test_opentopo_with_buffer(dataset_code, dataset_name, buffer, area_desc)
    
    def _test_opentopo_with_buffer(self, dataset_code: str, dataset_name: str, 
                                   buffer: float, area_desc: str):
        """Test OpenTopography with specific buffer size"""
        start_time = time.time()
        
        try:
            bbox = {
                'west': self.test_lon - buffer,
                'east': self.test_lon + buffer,
                'south': self.test_lat - buffer,
                'north': self.test_lat + buffer
            }
            
            params = {
                'demtype': dataset_code,
                'west': bbox['west'],
                'south': bbox['south'],
                'east': bbox['east'],
                'north': bbox['north'],
                'outputFormat': 'GTiff'
            }
            
            # Add authentication
            if self.opentopo_api_key:
                params['API_Key'] = self.opentopo_api_key
            elif self.opentopo_username and self.opentopo_password:
                params['username'] = self.opentopo_username
                params['password'] = self.opentopo_password
            
            print(f"  🔍 Testing {dataset_name} ({area_desc})...")
            
            url = "https://portal.opentopography.org/API/globaldem"
            response = requests.get(url, params=params, timeout=120)
            download_time = time.time() - start_time
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                file_size = len(response.content)
                
                if 'image/tiff' in content_type or file_size > 5000:
                    # Save file
                    filename = f"opentopo_{dataset_code}_{area_desc.replace(' ', '_')}_{self.test_lat:.3f}_{abs(self.test_lon):.3f}.tif"
                    test_file = self.output_dir / filename
                    
                    with open(test_file, 'wb') as f:
                        f.write(response.content)
                    
                    # Analyze dimensions if GDAL available
                    dimensions = self._get_tiff_dimensions(test_file)
                    
                    self.log_result(
                        source=f"OpenTopography {dataset_name}",
                        test_type=f"Enhanced {area_desc}",
                        success=True,
                        file_size=file_size,
                        resolution="30m",
                        download_time=download_time,
                        dimensions=dimensions,
                        metadata={
                            'dataset_code': dataset_code,
                            'area_description': area_desc,
                            'bbox': bbox,
                            'file_path': str(test_file)
                        }
                    )
                else:
                    self.log_result(
                        source=f"OpenTopography {dataset_name}",
                        test_type=f"Enhanced {area_desc}",
                        success=False,
                        download_time=download_time,
                        error=f"Invalid content: {content_type}, size: {file_size}"
                    )
            else:
                error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
                self.log_result(
                    source=f"OpenTopography {dataset_name}",
                    test_type=f"Enhanced {area_desc}",
                    success=False,
                    download_time=download_time,
                    error=error_msg
                )
                
        except Exception as e:
            download_time = time.time() - start_time
            self.log_result(
                source=f"OpenTopography {dataset_name}",
                test_type=f"Enhanced {area_desc}",
                success=False,
                download_time=download_time,
                error=str(e)
            )
    
    def test_high_resolution_sources(self):
        """Test sources specifically for high-resolution data"""
        print("\\n🎯 Testing High-Resolution Specific Sources...")
        
        # Test ALOS PALSAR World 3D (higher resolution in some areas)
        self._test_alos_palsar()
        
        # Test Copernicus DEM with different resolutions
        self._test_copernicus_variations()
        
        # Test USGS 3DEP (if available for region)
        self._test_usgs_3dep()
    
    def _test_alos_palsar(self):
        """Test ALOS PALSAR for higher resolution"""
        start_time = time.time()
        
        try:
            # ALOS World 3D is available through multiple portals
            # Test availability through Alaska Satellite Facility
            asf_url = "https://search.asf.alaska.edu/api/search"
            
            params = {
                'platform': 'ALOS',
                'bbox': f"{self.test_lon-0.1},{self.test_lat-0.1},{self.test_lon+0.1},{self.test_lat+0.1}",
                'output': 'json'
            }
            
            print("  🔍 Testing ALOS PALSAR availability...")
            response = requests.get(asf_url, params=params, timeout=30)
            download_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results_count = len(data.get('results', []))
                
                self.log_result(
                    source="ALOS PALSAR (ASF)",
                    test_type="Data Availability Search",
                    success=True,
                    file_size=len(response.content),
                    resolution="12.5m SAR",
                    download_time=download_time,
                    metadata={
                        'results_found': results_count,
                        'search_url': asf_url,
                        'note': 'SAR data - may require processing for elevation'
                    }
                )
            else:
                self.log_result(
                    source="ALOS PALSAR (ASF)",
                    test_type="Data Availability Search",
                    success=False,
                    download_time=download_time,
                    error=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            download_time = time.time() - start_time
            self.log_result(
                source="ALOS PALSAR (ASF)",
                test_type="Data Availability Search",
                success=False,
                download_time=download_time,
                error=str(e)
            )
    
    def _test_copernicus_variations(self):
        """Test different Copernicus DEM variations"""
        start_time = time.time()
        
        try:
            # Test Copernicus DEM GLO-90 (lower resolution but better coverage)
            print("  🔍 Testing Copernicus DEM variations...")
            
            # Try different tile naming conventions
            tile_variations = [
                f"Copernicus_DSM_COG_10_S{abs(int(self.test_lat)):02d}_00_W{abs(int(self.test_lon)):03d}_00_DEM",
                f"Copernicus_DSM_COG_30_S{abs(int(self.test_lat)):02d}_00_W{abs(int(self.test_lon)):03d}_00_DEM",
                f"Copernicus_DSM_COG_90_S{abs(int(self.test_lat)):02d}_00_W{abs(int(self.test_lon)):03d}_00_DEM"
            ]
            
            for tile_name in tile_variations:
                # Test AWS S3 access
                aws_url = f"https://copernicus-dem-30m.s3.amazonaws.com/{tile_name}.tif"
                
                try:
                    response = requests.head(aws_url, timeout=15)
                    if response.status_code == 200:
                        # Try to download
                        response = requests.get(aws_url, timeout=60)
                        file_size = len(response.content)
                        
                        if file_size > 1000:
                            filename = f"copernicus_{tile_name}.tif"
                            test_file = self.output_dir / filename
                            
                            with open(test_file, 'wb') as f:
                                f.write(response.content)
                            
                            dimensions = self._get_tiff_dimensions(test_file)
                            
                            resolution = "10m" if "COG_10" in tile_name else "30m" if "COG_30" in tile_name else "90m"
                            
                            self.log_result(
                                source=f"Copernicus DEM {resolution}",
                                test_type="AWS S3 Direct",
                                success=True,
                                file_size=file_size,
                                resolution=resolution,
                                download_time=time.time() - start_time,
                                dimensions=dimensions,
                                metadata={
                                    'tile_name': tile_name,
                                    'aws_url': aws_url,
                                    'file_path': str(test_file)
                                }
                            )
                            break  # Found one that works
                except:
                    continue
            
        except Exception as e:
            download_time = time.time() - start_time
            self.log_result(
                source="Copernicus DEM Variations",
                test_type="AWS S3 Direct",
                success=False,
                download_time=download_time,
                error=str(e)
            )
    
    def _test_usgs_3dep(self):
        """Test USGS 3DEP for high-resolution data"""
        start_time = time.time()
        
        try:
            # USGS 3DEP API for lidar-derived DEMs
            print("  🔍 Testing USGS 3DEP availability...")
            
            # Check if 3DEP data is available for the region
            usgs_api = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer"
            
            params = {
                'f': 'json',
                'geometry': f"{self.test_lon},{self.test_lat}",
                'geometryType': 'esriGeometryPoint',
                'returnGeometry': 'false'
            }
            
            response = requests.get(f"{usgs_api}/identify", params=params, timeout=30)
            download_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                self.log_result(
                    source="USGS 3DEP",
                    test_type="Availability Check",
                    success=True,
                    file_size=len(response.content),
                    resolution="1m-3m (lidar-derived)",
                    download_time=download_time,
                    metadata={
                        'api_response': data,
                        'note': 'May require additional processing for data extraction'
                    }
                )
            else:
                self.log_result(
                    source="USGS 3DEP",
                    test_type="Availability Check",
                    success=False,
                    download_time=download_time,
                    error=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            download_time = time.time() - start_time
            self.log_result(
                source="USGS 3DEP",
                test_type="Availability Check",
                success=False,
                download_time=download_time,
                error=str(e)
            )
    
    def _get_tiff_dimensions(self, file_path: Path) -> Dict:
        """Get TIFF file dimensions using GDAL"""
        try:
            from osgeo import gdal
            gdal.UseExceptions()
            
            dataset = gdal.Open(str(file_path))
            if dataset:
                dimensions = {
                    'width': dataset.RasterXSize,
                    'height': dataset.RasterYSize,
                    'bands': dataset.RasterCount
                }
                dataset = None
                return dimensions
        except:
            pass
        
        return {}
    
    def generate_enhanced_report(self):
        """Generate enhanced test report"""
        print("\\n" + "="*80)
        print("📊 ENHANCED API TESTING RESULTS")
        print("="*80)
        
        successful_tests = [r for r in self.results if r['success']]
        
        print(f"\\n🎯 Test Region: {self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📈 Total Tests: {len(self.results)}")
        print(f"✅ Successful: {len(successful_tests)}")
        print(f"❌ Failed: {len(self.results) - len(successful_tests)}")
        
        if successful_tests:
            # Sort by file size (larger is generally better for elevation data)
            successful_tests.sort(key=lambda x: x['file_size_bytes'], reverse=True)
            
            print("\\n🏆 TOP SOURCES BY FILE SIZE (Quality Indicator):")
            print("-" * 60)
            
            for i, result in enumerate(successful_tests[:5], 1):
                print(f"{i}. ✅ {result['source']}")
                print(f"   📊 Size: {result['file_size_mb']} MB")
                print(f"   🎯 Resolution: {result['resolution']}")
                print(f"   ⏱️  Download time: {result['download_time_seconds']}s")
                
                if result['dimensions']:
                    dims = result['dimensions']
                    print(f"   📐 Dimensions: {dims.get('width', '?')}×{dims.get('height', '?')} pixels")
                
                print()
        
        # Save enhanced report
        report_file = self.output_dir / f"enhanced_api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'test_summary': {
                    'region': f"{self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W",
                    'test_date': datetime.now().isoformat(),
                    'total_tests': len(self.results),
                    'successful_tests': len(successful_tests)
                },
                'results': self.results,
                'best_sources': self._rank_sources()
            }, f, indent=2)
        
        print(f"📄 Enhanced report saved: {report_file}")
        return report_file
    
    def _rank_sources(self) -> List[Dict]:
        """Rank sources by quality metrics"""
        successful_tests = [r for r in self.results if r['success']]
        
        # Score each source
        for result in successful_tests:
            score = 0
            
            # File size score (larger is generally better)
            if result['file_size_mb'] > 10:
                score += 40
            elif result['file_size_mb'] > 1:
                score += 30
            elif result['file_size_mb'] > 0.1:
                score += 20
            else:
                score += 10
            
            # Resolution score
            resolution = result['resolution'].lower()
            if '1m' in resolution or '3m' in resolution:
                score += 30
            elif '10m' in resolution:
                score += 25
            elif '30m' in resolution:
                score += 20
            elif '90m' in resolution:
                score += 15
            else:
                score += 10
            
            # Dimensions score
            if result['dimensions']:
                width = result['dimensions'].get('width', 0)
                height = result['dimensions'].get('height', 0)
                pixels = width * height
                
                if pixels > 1000000:  # > 1M pixels
                    score += 20
                elif pixels > 100000:  # > 100K pixels
                    score += 15
                elif pixels > 10000:   # > 10K pixels
                    score += 10
                else:
                    score += 5
            
            # Download time penalty (faster is better)
            if result['download_time_seconds'] < 10:
                score += 10
            elif result['download_time_seconds'] < 30:
                score += 5
            
            result['quality_score'] = score
        
        # Sort by score
        successful_tests.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return [{
            'source': r['source'],
            'quality_score': r['quality_score'],
            'file_size_mb': r['file_size_mb'],
            'resolution': r['resolution'],
            'dimensions': r['dimensions']
        } for r in successful_tests[:5]]

def main():
    """Main enhanced testing execution"""
    print("🚀 LAZ Terrain Processor - Enhanced API Quality Testing")
    print("=" * 60)
    
    # Test region: 9.38S_62.67W (Brazilian Amazon)
    test_region = (-9.38, -62.67)
    
    tester = EnhancedAPITester(test_region)
    
    print("\\n🔍 Starting enhanced API tests for high-quality TIFF sources...")
    
    # Run enhanced tests
    tester.test_larger_areas_opentopo()
    tester.test_high_resolution_sources()
    
    # Generate final report
    report_file = tester.generate_enhanced_report()
    
    print("\\n🎉 Enhanced API Testing Complete!")
    print(f"📊 Results saved to: {tester.output_dir}")
    
    return report_file

if __name__ == "__main__":
    main()
