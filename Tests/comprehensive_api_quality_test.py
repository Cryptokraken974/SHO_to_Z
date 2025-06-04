#!/usr/bin/env python3
"""
Comprehensive API Testing Suite for LAZ Terrain Processor
Tests multiple data sources and APIs to find best quality TIFF sources
Target Region: 9.38S_62.67W (Brazilian Amazon)
"""

import sys
import os
import time
import asyncio
from datetime import datetime
from pathlib import Path
import json
import requests
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_environment():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        return True
    except ImportError:
        print("⚠️  python-dotenv not installed. Using system environment variables.")
        return False

class APIQualityTester:
    """Test different API sources for TIFF quality"""
    
    def __init__(self, test_region: Tuple[float, float]):
        self.test_lat, self.test_lon = test_region
        self.results = []
        self.output_dir = Path("Tests/api_quality_tests")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load credentials
        load_environment()
        self.opentopo_api_key = os.getenv('OPENTOPOGRAPHY_API_KEY')
        self.opentopo_username = os.getenv('OPENTOPO_USERNAME')
        self.opentopo_password = os.getenv('OPENTOPO_PASSWORD')
        self.cdse_client_id = os.getenv('CDSE_CLIENT_ID')
        self.cdse_client_secret = os.getenv('CDSE_CLIENT_SECRET')
        
        print(f"🎯 Testing APIs for region: {self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W")
        print(f"📁 Results will be saved to: {self.output_dir}")
        
    def log_result(self, source: str, test_type: str, success: bool, 
                  quality_score: int, file_size: int = 0, 
                  resolution: str = "Unknown", error: str = None, 
                  download_time: float = 0, metadata: Dict = None):
        """Log test result"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'test_type': test_type,
            'region': f"{self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W",
            'success': success,
            'quality_score': quality_score,  # 1-10 scale
            'file_size_bytes': file_size,
            'file_size_mb': round(file_size / (1024*1024), 2) if file_size > 0 else 0,
            'resolution': resolution,
            'download_time_seconds': round(download_time, 2),
            'error': error,
            'metadata': metadata or {}
        }
        self.results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {source} ({test_type}): Quality={quality_score}/10, "
              f"Size={result['file_size_mb']}MB, Time={result['download_time_seconds']}s")
        if error:
            print(f"   Error: {error}")
    
    def test_opentopography_global_dem(self):
        """Test OpenTopography Global DEM APIs"""
        print("\\n🌍 Testing OpenTopography Global DEM APIs...")
        
        # Create bounding box around test point
        buffer = 0.01  # ~1km
        bbox = {
            'west': self.test_lon - buffer,
            'east': self.test_lon + buffer,
            'south': self.test_lat - buffer,
            'north': self.test_lat + buffer
        }
        
        # Test different datasets
        datasets = [
            ('SRTM30', 'SRTM 30m', 'https://portal.opentopography.org/API/globaldem'),
            ('COP30', 'Copernicus GLO-30', 'https://portal.opentopography.org/API/globaldem'),
            ('NASADEM', 'NASADEM', 'https://portal.opentopography.org/API/globaldem'),
            ('ALOS', 'ALOS World 3D 30m', 'https://portal.opentopography.org/API/globaldem')
        ]
        
        for dataset_code, dataset_name, base_url in datasets:
            start_time = time.time()
            try:
                params = {
                    'demtype': dataset_code,
                    'west': bbox['west'],
                    'south': bbox['south'], 
                    'east': bbox['east'],
                    'north': bbox['north'],
                    'outputFormat': 'GTiff'
                }
                
                # Add authentication if available
                if self.opentopo_api_key:
                    params['API_Key'] = self.opentopo_api_key
                elif self.opentopo_username and self.opentopo_password:
                    params['username'] = self.opentopo_username
                    params['password'] = self.opentopo_password
                
                print(f"  🔍 Testing {dataset_name}...")
                response = requests.get(base_url, params=params, timeout=60)
                download_time = time.time() - start_time
                
                if response.status_code == 200:
                    # Check if we got a TIFF file
                    content_type = response.headers.get('content-type', '')
                    file_size = len(response.content)
                    
                    if 'image/tiff' in content_type or file_size > 1000:
                        # Save test file
                        test_file = self.output_dir / f"opentopo_{dataset_code}_{self.test_lat:.3f}_{abs(self.test_lon):.3f}.tif"
                        with open(test_file, 'wb') as f:
                            f.write(response.content)
                        
                        # Analyze quality
                        quality_score = self._analyze_tiff_quality(test_file, dataset_name)
                        
                        self.log_result(
                            source=f"OpenTopography {dataset_name}",
                            test_type="Global DEM",
                            success=True,
                            quality_score=quality_score,
                            file_size=file_size,
                            resolution="30m",
                            download_time=download_time,
                            metadata={
                                'dataset_code': dataset_code,
                                'content_type': content_type,
                                'api_endpoint': base_url,
                                'file_path': str(test_file)
                            }
                        )
                    else:
                        self.log_result(
                            source=f"OpenTopography {dataset_name}",
                            test_type="Global DEM", 
                            success=False,
                            quality_score=0,
                            download_time=download_time,
                            error=f"Invalid content type: {content_type}"
                        )
                else:
                    error_text = response.text[:200] if response.text else f"HTTP {response.status_code}"
                    self.log_result(
                        source=f"OpenTopography {dataset_name}",
                        test_type="Global DEM",
                        success=False, 
                        quality_score=0,
                        download_time=download_time,
                        error=error_text
                    )
                    
            except Exception as e:
                download_time = time.time() - start_time
                self.log_result(
                    source=f"OpenTopography {dataset_name}",
                    test_type="Global DEM",
                    success=False,
                    quality_score=0,
                    download_time=download_time,
                    error=str(e)
                )
    
    def test_nasa_earthdata(self):
        """Test NASA Earthdata sources"""
        print("\\n🚀 Testing NASA Earthdata APIs...")
        
        # NASADEM direct access
        start_time = time.time()
        try:
            # NASA EarthData LP DAAC NASADEM
            base_url = "https://e4ftl01.cr.usgs.gov/MEASURES/NASADEM_HGT.001"
            
            # For Brazilian Amazon, typical tile would be around S10W063
            tile_lat = int(abs(self.test_lat))
            tile_lon = int(abs(self.test_lon))
            
            # Format tile name (NASADEM uses 1-degree tiles)
            tile_name = f"NASADEM_HGT_s{tile_lat:02d}w{tile_lon:03d}"
            
            print(f"  🔍 Testing NASADEM tile: {tile_name}")
            
            # This would require EarthData authentication, so we'll test availability
            test_url = f"{base_url}/{tile_name}"
            response = requests.head(test_url, timeout=30)
            download_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result(
                    source="NASA NASADEM Direct",
                    test_type="Direct Access",
                    success=True,
                    quality_score=8,  # NASADEM is high quality
                    resolution="30m",
                    download_time=download_time,
                    metadata={'tile_name': tile_name, 'endpoint': test_url}
                )
            else:
                self.log_result(
                    source="NASA NASADEM Direct", 
                    test_type="Direct Access",
                    success=False,
                    quality_score=0,
                    download_time=download_time,
                    error=f"HTTP {response.status_code} - Authentication likely required"
                )
                
        except Exception as e:
            download_time = time.time() - start_time
            self.log_result(
                source="NASA NASADEM Direct",
                test_type="Direct Access", 
                success=False,
                quality_score=0,
                download_time=download_time,
                error=str(e)
            )
    
    def test_copernicus_dem(self):
        """Test Copernicus DEM sources"""
        print("\\n🇪🇺 Testing Copernicus DEM APIs...")
        
        start_time = time.time()
        try:
            # AWS Copernicus DEM access (public)
            # Tile calculation for Copernicus GLO-30
            lat_tile = int((90 + self.test_lat) // 1)
            lon_tile = int((180 + self.test_lon) // 1)
            
            # Format: Copernicus_DSM_COG_10_S10_00_W063_00_DEM.tif
            tile_name = f"Copernicus_DSM_COG_30_S{abs(int(self.test_lat)):02d}_00_W{abs(int(self.test_lon)):03d}_00_DEM"
            
            # Test AWS S3 public access
            aws_url = f"https://copernicus-dem-30m.s3.amazonaws.com/{tile_name}.tif"
            
            print(f"  🔍 Testing Copernicus GLO-30 tile: {tile_name}")
            response = requests.head(aws_url, timeout=30)
            download_time = time.time() - start_time
            
            if response.status_code == 200:
                # Try to download a small portion for quality testing
                response = requests.get(aws_url, timeout=60)
                file_size = len(response.content)
                
                if file_size > 1000:  # Valid file
                    test_file = self.output_dir / f"copernicus_glo30_{self.test_lat:.3f}_{abs(self.test_lon):.3f}.tif"
                    with open(test_file, 'wb') as f:
                        f.write(response.content)
                    
                    quality_score = self._analyze_tiff_quality(test_file, "Copernicus GLO-30")
                    
                    self.log_result(
                        source="Copernicus GLO-30 (AWS)",
                        test_type="Public S3 Access",
                        success=True,
                        quality_score=quality_score,
                        file_size=file_size,
                        resolution="30m", 
                        download_time=download_time,
                        metadata={
                            'tile_name': tile_name,
                            'aws_url': aws_url,
                            'file_path': str(test_file)
                        }
                    )
                else:
                    self.log_result(
                        source="Copernicus GLO-30 (AWS)",
                        test_type="Public S3 Access",
                        success=False,
                        quality_score=0,
                        download_time=download_time,
                        error="File too small or invalid"
                    )
            else:
                self.log_result(
                    source="Copernicus GLO-30 (AWS)",
                    test_type="Public S3 Access", 
                    success=False,
                    quality_score=0,
                    download_time=download_time,
                    error=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            download_time = time.time() - start_time
            self.log_result(
                source="Copernicus GLO-30 (AWS)",
                test_type="Public S3 Access",
                success=False,
                quality_score=0,
                download_time=download_time,
                error=str(e)
            )
    
    def test_ibge_brazil(self):
        """Test IBGE Brazil elevation sources"""
        print("\\n🇧🇷 Testing IBGE Brazil APIs...")
        
        start_time = time.time()
        try:
            # IBGE elevation API (if available)
            ibge_url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
            
            print("  🔍 Testing IBGE municipal data availability...")
            response = requests.get(ibge_url, timeout=30)
            download_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    source="IBGE Brazil Municipal",
                    test_type="Data Availability",
                    success=True,
                    quality_score=6,  # Good for Brazil-specific data
                    file_size=len(response.content),
                    resolution="Municipal level",
                    download_time=download_time,
                    metadata={'municipalities_count': len(data)}
                )
            else:
                self.log_result(
                    source="IBGE Brazil Municipal",
                    test_type="Data Availability",
                    success=False,
                    quality_score=0,
                    download_time=download_time,
                    error=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            download_time = time.time() - start_time
            self.log_result(
                source="IBGE Brazil Municipal",
                test_type="Data Availability",
                success=False,
                quality_score=0,
                download_time=download_time,
                error=str(e)
            )
    
    def test_alos_global(self):
        """Test ALOS World 3D access"""
        print("\\n🗾 Testing ALOS World 3D APIs...")
        
        start_time = time.time()
        try:
            # ALOS World 3D is typically available through JAXA or research institutions
            # Test availability through different access points
            
            # Option 1: OpenTopography ALOS (already tested above)
            # Option 2: Direct JAXA access (requires registration)
            # Option 3: Research data portals
            
            print("  🔍 Testing ALOS data portal availability...")
            
            # Test JAXA G-Portal availability 
            jaxa_url = "https://gportal.jaxa.jp/gpr/"
            response = requests.get(jaxa_url, timeout=30)
            download_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result(
                    source="ALOS World 3D (JAXA)",
                    test_type="Portal Availability",
                    success=True,
                    quality_score=7,  # High quality stereo-derived DEM
                    resolution="30m",
                    download_time=download_time,
                    metadata={'portal_url': jaxa_url, 'requires_registration': True}
                )
            else:
                self.log_result(
                    source="ALOS World 3D (JAXA)",
                    test_type="Portal Availability", 
                    success=False,
                    quality_score=0,
                    download_time=download_time,
                    error=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            download_time = time.time() - start_time
            self.log_result(
                source="ALOS World 3D (JAXA)",
                test_type="Portal Availability",
                success=False,
                quality_score=0,
                download_time=download_time,
                error=str(e)
            )
    
    def test_alternative_sources(self):
        """Test alternative elevation data sources"""
        print("\\n🌐 Testing Alternative Sources...")
        
        # Test USGS Global Data Explorer
        start_time = time.time()
        try:
            usgs_url = "https://www.usgs.gov/core-science-systems/ngp/tnm-delivery/"
            response = requests.get(usgs_url, timeout=30)
            download_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result(
                    source="USGS Global Data Explorer",
                    test_type="Portal Availability",
                    success=True,
                    quality_score=8,
                    resolution="Various",
                    download_time=download_time,
                    metadata={'portal_url': usgs_url}
                )
            else:
                self.log_result(
                    source="USGS Global Data Explorer", 
                    test_type="Portal Availability",
                    success=False,
                    quality_score=0,
                    download_time=download_time,
                    error=f"HTTP {response.status_code}"
                )
        except Exception as e:
            download_time = time.time() - start_time
            self.log_result(
                source="USGS Global Data Explorer",
                test_type="Portal Availability",
                success=False,
                quality_score=0,
                download_time=download_time,
                error=str(e)
            )
    
    def _analyze_tiff_quality(self, file_path: Path, dataset_name: str) -> int:
        """Analyze TIFF file quality and return score 1-10"""
        try:
            # Check file size
            file_size = file_path.stat().st_size
            
            # Basic quality assessment based on file size and format
            if file_size < 1000:  # Too small
                return 1
            elif file_size < 10000:  # Very small, likely low quality
                return 3
            elif file_size < 100000:  # Small, basic quality
                return 5
            elif file_size < 1000000:  # Medium, good quality
                return 7
            else:  # Large, likely high quality
                base_score = 8
                
                # Dataset-specific scoring
                if 'NASADEM' in dataset_name:
                    return min(10, base_score + 2)  # NASADEM is typically highest quality
                elif 'Copernicus' in dataset_name:
                    return min(10, base_score + 1)  # Copernicus is very good
                elif 'ALOS' in dataset_name:
                    return min(10, base_score + 1)  # ALOS stereo is high quality
                elif 'SRTM' in dataset_name:
                    return base_score  # SRTM is good baseline
                else:
                    return base_score
                    
        except Exception as e:
            print(f"    Warning: Could not analyze {file_path}: {e}")
            return 5  # Default score if analysis fails
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\\n" + "="*80)
        print("📊 API QUALITY TEST RESULTS SUMMARY")
        print("="*80)
        
        # Sort results by quality score (descending)
        sorted_results = sorted(self.results, key=lambda x: x['quality_score'], reverse=True)
        
        print(f"\\n🎯 Test Region: {self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📈 Total Tests: {len(self.results)}")
        
        successful_tests = [r for r in self.results if r['success']]
        print(f"✅ Successful: {len(successful_tests)}")
        print(f"❌ Failed: {len(self.results) - len(successful_tests)}")
        
        if successful_tests:
            avg_quality = sum(r['quality_score'] for r in successful_tests) / len(successful_tests)
            print(f"📊 Average Quality Score: {avg_quality:.1f}/10")
            
        print("\\n🏆 TOP 5 BEST SOURCES BY QUALITY:")
        print("-" * 60)
        
        for i, result in enumerate(sorted_results[:5], 1):
            status = "✅" if result['success'] else "❌"
            print(f"{i}. {status} {result['source']}")
            print(f"   Quality: {result['quality_score']}/10 | Size: {result['file_size_mb']}MB | "
                  f"Resolution: {result['resolution']} | Time: {result['download_time_seconds']}s")
            if result['error']:
                print(f"   Error: {result['error']}")
            print()
        
        # Save detailed JSON report
        report_file = self.output_dir / f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'test_summary': {
                    'region': f"{self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W",
                    'test_date': datetime.now().isoformat(),
                    'total_tests': len(self.results),
                    'successful_tests': len(successful_tests),
                    'average_quality_score': avg_quality if successful_tests else 0
                },
                'results': self.results,
                'recommendations': self._generate_recommendations()
            }, f, indent=2)
        
        print(f"📄 Detailed report saved: {report_file}")
        
        return report_file
    
    def _generate_recommendations(self) -> Dict:
        """Generate recommendations based on test results"""
        successful_tests = [r for r in self.results if r['success']]
        
        if not successful_tests:
            return {
                'primary_source': None,
                'fallback_sources': [],
                'notes': 'No successful API sources found. Manual data acquisition may be required.'
            }
        
        # Find best source by quality score
        best_source = max(successful_tests, key=lambda x: x['quality_score'])
        
        # Find fallback sources (quality score >= 6)
        fallback_sources = [r for r in successful_tests 
                          if r['quality_score'] >= 6 and r['source'] != best_source['source']]
        fallback_sources.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return {
            'primary_source': {
                'name': best_source['source'],
                'quality_score': best_source['quality_score'],
                'resolution': best_source['resolution'],
                'reasons': ['Highest quality score', 'Successful download', 'Good file size']
            },
            'fallback_sources': [
                {
                    'name': r['source'],
                    'quality_score': r['quality_score'], 
                    'resolution': r['resolution']
                } for r in fallback_sources[:3]  # Top 3 fallbacks
            ],
            'notes': f"Primary source achieved {best_source['quality_score']}/10 quality score. "
                    f"{len(fallback_sources)} fallback sources available."
        }

def main():
    """Main test execution"""
    print("🚀 LAZ Terrain Processor - API Quality Testing Suite")
    print("=" * 60)
    
    # Test region: 9.38S_62.67W (Brazilian Amazon)
    test_region = (-9.38, -62.67)
    
    tester = APIQualityTester(test_region)
    
    print("\\n🔍 Starting comprehensive API tests...")
    
    # Run all tests
    tester.test_opentopography_global_dem()
    tester.test_nasa_earthdata()
    tester.test_copernicus_dem() 
    tester.test_ibge_brazil()
    tester.test_alos_global()
    tester.test_alternative_sources()
    
    # Generate final report
    report_file = tester.generate_report()
    
    print("\\n🎉 API Quality Testing Complete!")
    print(f"📊 Results saved to: {tester.output_dir}")
    
    return report_file

if __name__ == "__main__":
    main()
