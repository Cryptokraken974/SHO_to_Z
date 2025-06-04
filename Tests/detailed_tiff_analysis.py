#!/usr/bin/env python3
"""
Detailed TIFF Quality Analysis for Best API Sources
Analyzes the downloaded TIFF files from the comprehensive API test
Region: 9.38S_62.67W (Brazilian Amazon)
"""

import sys
import os
import time
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from osgeo import gdal, gdalinfo
    gdal.UseExceptions()
    GDAL_AVAILABLE = True
except ImportError:
    print("⚠️  GDAL not available. Limited analysis will be performed.")
    GDAL_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    print("⚠️  NumPy not available. Statistical analysis will be limited.")
    NUMPY_AVAILABLE = False

class TIFFQualityAnalyzer:
    """Detailed analysis of TIFF file quality"""
    
    def __init__(self, test_region: Tuple[float, float]):
        self.test_lat, self.test_lon = test_region
        self.input_dir = Path("Tests/api_quality_tests")
        self.results = []
        
        print(f"🔍 Analyzing TIFF quality for region: {self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W")
        print(f"📁 Looking for files in: {self.input_dir}")
    
    def analyze_all_tiffs(self):
        """Analyze all TIFF files in the test directory"""
        tiff_files = list(self.input_dir.glob("*.tif"))
        
        if not tiff_files:
            print("❌ No TIFF files found for analysis")
            return
        
        print(f"📊 Found {len(tiff_files)} TIFF files to analyze")
        
        for tiff_file in tiff_files:
            print(f"\\n🎯 Analyzing: {tiff_file.name}")
            self.analyze_single_tiff(tiff_file)
    
    def analyze_single_tiff(self, file_path: Path):
        """Perform detailed analysis of a single TIFF file"""
        start_time = time.time()
        
        try:
            # Basic file info
            file_size = file_path.stat().st_size
            
            analysis = {
                'filename': file_path.name,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024*1024), 3),
                'analysis_time': 0,
                'success': False,
                'error': None,
                'basic_info': {},
                'spatial_info': {},
                'data_quality': {},
                'recommendations': []
            }
            
            print(f"  📊 File size: {analysis['file_size_mb']} MB")
            
            if GDAL_AVAILABLE:
                analysis.update(self._analyze_with_gdal(file_path))
            else:
                analysis['error'] = "GDAL not available for detailed analysis"
            
            analysis['analysis_time'] = round(time.time() - start_time, 2)
            self.results.append(analysis)
            
            # Print summary
            if analysis['success']:
                print(f"  ✅ Analysis complete ({analysis['analysis_time']}s)")
                if 'dimensions' in analysis['spatial_info']:
                    dims = analysis['spatial_info']['dimensions']
                    print(f"  📐 Dimensions: {dims['width']}×{dims['height']} pixels")
                if 'pixel_size' in analysis['spatial_info']:
                    ps = analysis['spatial_info']['pixel_size']
                    print(f"  🎯 Pixel size: {ps['x']:.6f}° × {ps['y']:.6f}°")
                if 'elevation_range' in analysis['data_quality']:
                    er = analysis['data_quality']['elevation_range']
                    print(f"  🏔️  Elevation: {er['min']:.1f}m to {er['max']:.1f}m")
            else:
                print(f"  ❌ Analysis failed: {analysis['error']}")
                
        except Exception as e:
            analysis['error'] = str(e)
            analysis['analysis_time'] = round(time.time() - start_time, 2)
            self.results.append(analysis)
            print(f"  ❌ Analysis failed: {e}")
    
    def _analyze_with_gdal(self, file_path: Path) -> Dict:
        """Perform GDAL-based analysis"""
        try:
            # Open dataset
            dataset = gdal.Open(str(file_path))
            if not dataset:
                return {'error': 'Failed to open with GDAL', 'success': False}
            
            # Basic information
            width = dataset.RasterXSize
            height = dataset.RasterYSize
            bands = dataset.RasterCount
            driver = dataset.GetDriver().LongName
            
            # Geospatial information
            geotransform = dataset.GetGeoTransform()
            projection = dataset.GetProjection()
            
            # Calculate pixel size and coverage
            pixel_size_x = abs(geotransform[1])
            pixel_size_y = abs(geotransform[5])
            
            # Coverage area
            min_x = geotransform[0]
            max_x = min_x + width * geotransform[1]
            max_y = geotransform[3]
            min_y = max_y + height * geotransform[5]
            
            analysis = {
                'success': True,
                'basic_info': {
                    'driver': driver,
                    'bands': bands,
                    'data_type': gdal.GetDataTypeName(dataset.GetRasterBand(1).DataType)
                },
                'spatial_info': {
                    'dimensions': {'width': width, 'height': height},
                    'pixel_size': {'x': pixel_size_x, 'y': pixel_size_y},
                    'pixel_size_meters': self._degrees_to_meters(pixel_size_x, self.test_lat),
                    'coverage': {
                        'min_x': min_x, 'max_x': max_x,
                        'min_y': min_y, 'max_y': max_y
                    },
                    'projection': projection[:100] if projection else 'Unknown'
                },
                'data_quality': {}
            }
            
            # Analyze first band for elevation data
            band = dataset.GetRasterBand(1)
            nodata_value = band.GetNoDataValue()
            
            if NUMPY_AVAILABLE:
                # Read data for statistical analysis
                data = band.ReadAsArray()
                
                if data is not None:
                    # Remove nodata values for statistics
                    if nodata_value is not None:
                        valid_data = data[data != nodata_value]
                    else:
                        valid_data = data.flatten()
                    
                    if len(valid_data) > 0:
                        analysis['data_quality'] = {
                            'elevation_range': {
                                'min': float(np.min(valid_data)),
                                'max': float(np.max(valid_data)),
                                'mean': float(np.mean(valid_data)),
                                'std': float(np.std(valid_data))
                            },
                            'data_coverage': {
                                'total_pixels': int(data.size),
                                'valid_pixels': int(len(valid_data)),
                                'coverage_percent': round(len(valid_data) / data.size * 100, 1)
                            },
                            'nodata_value': nodata_value
                        }
                        
                        # Quality assessment
                        analysis['recommendations'] = self._generate_quality_recommendations(analysis)
            
            dataset = None  # Close dataset
            return analysis
            
        except Exception as e:
            return {'error': f'GDAL analysis failed: {str(e)}', 'success': False}
    
    def _degrees_to_meters(self, degrees: float, latitude: float) -> float:
        """Convert degrees to approximate meters at given latitude"""
        # Approximate conversion (varies by latitude)
        meters_per_degree_lat = 111320  # Roughly constant
        meters_per_degree_lon = meters_per_degree_lat * abs(np.cos(np.radians(latitude))) if NUMPY_AVAILABLE else meters_per_degree_lat * 0.5
        
        # Use the smaller value (longitude) as it's usually more restrictive
        return degrees * meters_per_degree_lon
    
    def _generate_quality_recommendations(self, analysis: Dict) -> List[str]:
        """Generate quality recommendations based on analysis"""
        recommendations = []
        
        # Check spatial resolution
        if 'pixel_size_meters' in analysis['spatial_info']:
            pixel_size_m = analysis['spatial_info']['pixel_size_meters']
            
            if pixel_size_m < 10:
                recommendations.append("🎯 Excellent resolution (<10m) - suitable for detailed terrain analysis")
            elif pixel_size_m < 30:
                recommendations.append("✅ Good resolution (<30m) - suitable for most applications")
            elif pixel_size_m < 100:
                recommendations.append("⚠️  Moderate resolution (<100m) - adequate for regional analysis")
            else:
                recommendations.append("❌ Low resolution (>100m) - limited detail available")
        
        # Check data coverage
        if 'data_coverage' in analysis['data_quality']:
            coverage = analysis['data_quality']['data_coverage']['coverage_percent']
            
            if coverage > 95:
                recommendations.append("✅ Excellent data coverage (>95%)")
            elif coverage > 80:
                recommendations.append("✅ Good data coverage (>80%)")
            elif coverage > 50:
                recommendations.append("⚠️  Moderate data coverage (>50%) - some gaps expected")
            else:
                recommendations.append("❌ Poor data coverage (<50%) - significant data gaps")
        
        # Check elevation range
        if 'elevation_range' in analysis['data_quality']:
            elev_range = analysis['data_quality']['elevation_range']
            range_span = elev_range['max'] - elev_range['min']
            
            if range_span > 500:
                recommendations.append("🏔️  High elevation variation - good for terrain analysis")
            elif range_span > 100:
                recommendations.append("⛰️  Moderate elevation variation - suitable for basic terrain")
            else:
                recommendations.append("🌊 Low elevation variation - may be suitable for flood modeling")
        
        return recommendations
    
    def generate_detailed_report(self):
        """Generate comprehensive analysis report"""
        print("\\n" + "="*80)
        print("📊 DETAILED TIFF QUALITY ANALYSIS REPORT")
        print("="*80)
        
        print(f"\\n🎯 Test Region: {self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W")
        print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📈 Files Analyzed: {len(self.results)}")
        
        successful_analyses = [r for r in self.results if r['success']]
        print(f"✅ Successful Analyses: {len(successful_analyses)}")
        
        if not successful_analyses:
            print("❌ No successful analyses to report")
            return
        
        print("\\n📋 DETAILED ANALYSIS RESULTS:")
        print("-" * 60)
        
        for i, result in enumerate(successful_analyses, 1):
            print(f"\\n{i}. {result['filename']}")
            print(f"   📊 Size: {result['file_size_mb']} MB")
            
            if 'dimensions' in result['spatial_info']:
                dims = result['spatial_info']['dimensions']
                print(f"   📐 Dimensions: {dims['width']}×{dims['height']} pixels")
            
            if 'pixel_size_meters' in result['spatial_info']:
                pixel_m = result['spatial_info']['pixel_size_meters']
                print(f"   🎯 Resolution: ~{pixel_m:.0f}m per pixel")
            
            if 'elevation_range' in result['data_quality']:
                elev = result['data_quality']['elevation_range']
                print(f"   🏔️  Elevation: {elev['min']:.1f}m to {elev['max']:.1f}m (range: {elev['max']-elev['min']:.1f}m)")
                print(f"   📊 Mean elevation: {elev['mean']:.1f}m ± {elev['std']:.1f}m")
            
            if 'data_coverage' in result['data_quality']:
                cov = result['data_quality']['data_coverage']
                print(f"   📈 Data coverage: {cov['coverage_percent']}% ({cov['valid_pixels']:,} valid pixels)")
            
            if result['recommendations']:
                print("   💡 Recommendations:")
                for rec in result['recommendations']:
                    print(f"      {rec}")
        
        # Find best file
        if len(successful_analyses) > 1:
            print("\\n🏆 BEST FILE RECOMMENDATION:")
            print("-" * 40)
            
            # Score files based on multiple criteria
            for result in successful_analyses:
                score = 0
                
                # Resolution score (lower meters = higher score)
                if 'pixel_size_meters' in result['spatial_info']:
                    pixel_m = result['spatial_info']['pixel_size_meters']
                    if pixel_m < 10:
                        score += 40
                    elif pixel_m < 30:
                        score += 30
                    elif pixel_m < 100:
                        score += 20
                    else:
                        score += 10
                
                # Coverage score
                if 'data_coverage' in result['data_quality']:
                    coverage = result['data_quality']['data_coverage']['coverage_percent']
                    score += coverage * 0.3  # Max 30 points
                
                # File size score (larger generally better for elevation data)
                score += min(result['file_size_mb'] * 5, 20)  # Max 20 points
                
                # Elevation range score
                if 'elevation_range' in result['data_quality']:
                    elev_range = result['data_quality']['elevation_range']
                    range_span = elev_range['max'] - elev_range['min']
                    score += min(range_span / 20, 10)  # Max 10 points
                
                result['quality_score'] = round(score, 1)
            
            # Sort by score
            successful_analyses.sort(key=lambda x: x['quality_score'], reverse=True)
            best_file = successful_analyses[0]
            
            print(f"🥇 Best file: {best_file['filename']}")
            print(f"   📊 Quality score: {best_file['quality_score']}/100")
            print(f"   💾 File size: {best_file['file_size_mb']} MB")
            
            if 'pixel_size_meters' in best_file['spatial_info']:
                print(f"   🎯 Resolution: ~{best_file['spatial_info']['pixel_size_meters']:.0f}m")
            
            print("\\n   🎯 Use this file for:")
            for rec in best_file['recommendations']:
                print(f"      {rec}")
        
        # Save detailed report
        report_file = self.input_dir / f"detailed_tiff_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'analysis_summary': {
                    'region': f"{self.test_lat:.3f}°S, {abs(self.test_lon):.3f}°W",
                    'analysis_date': datetime.now().isoformat(),
                    'files_analyzed': len(self.results),
                    'successful_analyses': len(successful_analyses)
                },
                'detailed_results': self.results
            }, f, indent=2)
        
        print(f"\\n📄 Detailed analysis saved: {report_file}")
        print("="*80)

def main():
    """Main analysis execution"""
    print("🔍 LAZ Terrain Processor - Detailed TIFF Quality Analysis")
    print("=" * 60)
    
    # Test region: 9.38S_62.67W (Brazilian Amazon)
    test_region = (-9.38, -62.67)
    
    analyzer = TIFFQualityAnalyzer(test_region)
    analyzer.analyze_all_tiffs()
    analyzer.generate_detailed_report()
    
    print("\\n🎉 Detailed TIFF Analysis Complete!")

if __name__ == "__main__":
    main()
