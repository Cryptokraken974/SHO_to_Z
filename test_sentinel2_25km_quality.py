#!/usr/bin/env python3
"""
🛰️ SENTINEL-2 25KM QUALITY TEST
===============================

Test Sentinel-2 data acquisition with 25x25km areas to achieve the highest 
resolution GeoTIFF, just like our elevation data optimization.

This script will:
1. Test the same region coordinates used for elevation testing
2. Use 25km buffer for maximum quality (matching elevation optimization)
3. Download highest resolution Sentinel-2 data available
4. Compare with smaller area downloads to validate quality improvement
5. Measure file sizes, resolution, and processing performance

Goal: Achieve the best possible Sentinel-2 resolution and quality using 25x25km areas.
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from data_acquisition.sources.copernicus_sentinel2 import CopernicusSentinel2Source
from data_acquisition.sources.base import DownloadRequest, DataType, DataResolution
from data_acquisition.utils.coordinates import BoundingBox

class Sentinel2QualityTest:
    """Test Sentinel-2 quality vs region size (matching elevation test methodology)"""
    
    def __init__(self):
        """Initialize the test suite"""
        self.test_coordinates = {
            # Use same coordinates as elevation testing for direct comparison
            "amazon_brazil": {"lat": -9.38, "lng": 62.67, "name": "Amazon Basin, Brazil"},
            "mountains_alps": {"lat": 46.52, "lng": 7.98, "name": "Swiss Alps, Switzerland"},
            "coastal_california": {"lat": 34.05, "lng": -118.25, "name": "Los Angeles, California"},
        }
        
        # Test different buffer sizes (same methodology as elevation testing)
        self.test_configurations = [
            {"buffer_km": 2.5, "area_km": "5km", "description": "Small area test"},
            {"buffer_km": 5.5, "area_km": "11km", "description": "Medium area test"},  
            {"buffer_km": 12.5, "area_km": "25km", "description": "OPTIMAL 25km area test"}
        ]
        
        self.results = []
        self.source = None
        
    async def setup_source(self):
        """Set up Sentinel-2 data source with authentication"""
        print("🔧 Setting up Copernicus Sentinel-2 data source...")
        
        # Check for environment variables
        client_id = os.getenv("CDSE_CLIENT_ID")
        client_secret = os.getenv("CDSE_CLIENT_SECRET")
        token = os.getenv("CDSE_TOKEN")
        
        if not (client_id and client_secret) and not token:
            print("⚠️ WARNING: No Copernicus credentials found!")
            print("   Please set CDSE_CLIENT_ID/CDSE_CLIENT_SECRET or CDSE_TOKEN environment variables")
            print("   Continuing with limited functionality...")
        
        self.source = CopernicusSentinel2Source(
            client_id=client_id,
            client_secret=client_secret,
            token=token,
            progress_callback=self.progress_callback
        )
        
        print("✅ Copernicus Sentinel-2 source initialized")
        
    async def progress_callback(self, update):
        """Handle progress updates from the download"""
        message = update.get("message", "")
        progress = update.get("progress", 0)
        if progress > 0:
            print(f"   📊 {message} ({progress:.1f}%)")
        else:
            print(f"   ℹ️ {message}")
    
    def calculate_buffer_degrees(self, buffer_km: float, lat: float) -> tuple:
        """Calculate buffer in degrees (same as elevation testing)"""
        # 1 degree ≈ 111 km at equator
        lat_buffer = buffer_km / 111.0
        # Longitude adjustment for latitude
        lng_buffer = buffer_km / (111.0 * abs(math.cos(math.radians(lat))))
        return lat_buffer, lng_buffer
    
    async def test_single_configuration(self, coord_name: str, coord_data: dict, config: dict) -> dict:
        """Test a single coordinate/buffer configuration"""
        print(f"\n{'='*80}")
        print(f"🛰️ TESTING: {coord_data['name']} - {config['description']}")
        print(f"{'='*80}")
        
        lat, lng = coord_data["lat"], coord_data["lng"]
        buffer_km = config["buffer_km"]
        
        print(f"📍 Center coordinates: {lat}, {lng}")
        print(f"📏 Buffer radius: {buffer_km}km ({config['area_km']} area)")
        
        # Calculate bounding box (same method as elevation testing)
        import math
        lat_delta = buffer_km / 111.0
        lng_delta = buffer_km / (111.0 * abs(math.cos(math.radians(lat))))
        
        bbox = BoundingBox(
            west=lng - lng_delta,
            south=lat - lat_delta, 
            east=lng + lng_delta,
            north=lat + lat_delta
        )
        
        area_km2 = bbox.area_km2()
        print(f"🔲 BBox: W={bbox.west:.4f}, S={bbox.south:.4f}, E={bbox.east:.4f}, N={bbox.north:.4f}")
        print(f"📐 Calculated area: {area_km2:.2f} km²")
        
        # Create download request
        request = DownloadRequest(
            bbox=bbox,
            data_type=DataType.IMAGERY,
            resolution=DataResolution.HIGH,  # Request highest resolution
            max_file_size_mb=200.0,  # Allow larger files for 25km areas
            output_format="GeoTIFF",
            region_name=f"{coord_name}_{config['area_km']}_test"
        )
        
        # Test availability first
        print(f"\n🔍 Checking Sentinel-2 data availability...")
        start_time = time.time()
        
        try:
            available = await self.source.check_availability(request)
            check_time = time.time() - start_time
            
            if not available:
                print(f"❌ No Sentinel-2 data available for this area")
                return {
                    "location": coord_data["name"],
                    "coordinates": f"{lat}, {lng}",
                    "buffer_km": buffer_km,
                    "area_km": config["area_km"],
                    "area_km2": area_km2,
                    "status": "No data available",
                    "availability_check_time": f"{check_time:.2f}s"
                }
            
            print(f"✅ Sentinel-2 data available! (checked in {check_time:.2f}s)")
            
            # Download the data
            print(f"\n📥 Starting Sentinel-2 download...")
            download_start = time.time()
            
            result = await self.source.download(request)
            download_time = time.time() - download_start
            
            if result.success:
                print(f"\n🎉 SUCCESS! Downloaded in {download_time:.2f}s")
                print(f"📁 File path: {result.file_path}")
                print(f"📊 File size: {result.file_size_mb:.2f} MB")
                print(f"📏 Resolution: {result.resolution_m}m per pixel")
                
                # Get additional file information
                file_info = await self.analyze_downloaded_file(result.file_path)
                
                return {
                    "location": coord_data["name"],
                    "coordinates": f"{lat}, {lng}",
                    "buffer_km": buffer_km,
                    "area_km": config["area_km"],
                    "area_km2": area_km2,
                    "status": "Success",
                    "file_path": result.file_path,
                    "file_size_mb": result.file_size_mb,
                    "resolution_m": result.resolution_m,
                    "download_time_s": download_time,
                    "availability_check_time_s": check_time,
                    "metadata": result.metadata,
                    **file_info
                }
            else:
                print(f"❌ Download failed: {result.error_message}")
                return {
                    "location": coord_data["name"],
                    "coordinates": f"{lat}, {lng}",
                    "buffer_km": buffer_km,
                    "area_km": config["area_km"],
                    "area_km2": area_km2,
                    "status": "Download failed",
                    "error": result.error_message,
                    "download_time_s": download_time
                }
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return {
                "location": coord_data["name"],
                "coordinates": f"{lat}, {lng}",
                "buffer_km": buffer_km,
                "area_km": config["area_km"],
                "area_km2": area_km2,
                "status": "Error",
                "error": str(e)
            }
    
    async def analyze_downloaded_file(self, file_path: str) -> dict:
        """Analyze the downloaded Sentinel-2 file for detailed information"""
        try:
            if not os.path.exists(file_path):
                return {"analysis_error": "File not found"}
            
            file_size_bytes = os.path.getsize(file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            # Check if it's a directory (multiple band files) or single file
            if os.path.isdir(file_path):
                # Count band files
                band_files = [f for f in os.listdir(file_path) if f.endswith('.tif')]
                total_size = sum(os.path.getsize(os.path.join(file_path, f)) for f in band_files)
                total_size_mb = total_size / (1024 * 1024)
                
                return {
                    "file_type": "Multi-band directory",
                    "band_count": len(band_files),
                    "band_files": band_files,
                    "total_directory_size_mb": total_size_mb
                }
            else:
                # Single GeoTIFF file - try to get dimensions using GDAL if available
                try:
                    from osgeo import gdal
                    dataset = gdal.Open(file_path)
                    if dataset:
                        width = dataset.RasterXSize
                        height = dataset.RasterYSize
                        bands = dataset.RasterCount
                        projection = dataset.GetProjection()
                        dataset = None  # Close file
                        
                        return {
                            "file_type": "Single GeoTIFF",
                            "dimensions": f"{width}x{height}",
                            "total_pixels": width * height,
                            "band_count": bands,
                            "has_projection": bool(projection)
                        }
                except ImportError:
                    pass
                
                return {
                    "file_type": "Single file",
                    "analyzed": "Limited (GDAL not available)"
                }
                
        except Exception as e:
            return {"analysis_error": str(e)}
    
    async def run_comprehensive_test(self):
        """Run comprehensive Sentinel-2 quality test across all configurations"""
        print(f"🛰️ SENTINEL-2 25KM QUALITY TEST")
        print(f"{'='*80}")
        print(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Objective: Find optimal Sentinel-2 area size for maximum quality")
        print(f"📊 Testing {len(self.test_configurations)} area configurations")
        print(f"🌍 Testing {len(self.test_coordinates)} geographic locations")
        
        await self.setup_source()
        
        # Test each configuration for each location
        total_tests = len(self.test_coordinates) * len(self.test_configurations)
        test_count = 0
        
        for coord_name, coord_data in self.test_coordinates.items():
            for config in self.test_configurations:
                test_count += 1
                print(f"\n🧪 TEST {test_count}/{total_tests}")
                
                result = await self.test_single_configuration(coord_name, coord_data, config)
                self.results.append(result)
                
                # Brief pause between tests
                await asyncio.sleep(2)
        
        # Generate summary report
        await self.generate_summary_report()
        
        # Save detailed results
        await self.save_detailed_results()
        
        # Cleanup
        if self.source:
            await self.source.close()
    
    async def generate_summary_report(self):
        """Generate summary report of test results"""
        print(f"\n{'='*80}")
        print(f"📊 SENTINEL-2 QUALITY TEST SUMMARY REPORT")
        print(f"{'='*80}")
        
        successful_tests = [r for r in self.results if r.get("status") == "Success"]
        failed_tests = [r for r in self.results if r.get("status") != "Success"]
        
        print(f"✅ Successful downloads: {len(successful_tests)}")
        print(f"❌ Failed downloads: {len(failed_tests)}")
        
        if successful_tests:
            print(f"\n📈 QUALITY ANALYSIS BY AREA SIZE:")
            print(f"{'='*60}")
            
            # Group by area size
            by_area = {}
            for result in successful_tests:
                area = result["area_km"]
                if area not in by_area:
                    by_area[area] = []
                by_area[area].append(result)
            
            # Analyze each area size
            for area, results in by_area.items():
                if not results:
                    continue
                    
                avg_size = sum(r.get("file_size_mb", 0) for r in results) / len(results)
                avg_download_time = sum(r.get("download_time_s", 0) for r in results) / len(results)
                
                print(f"\n🔍 {area} Area Analysis:")
                print(f"   📊 Average file size: {avg_size:.2f} MB")
                print(f"   ⏱️ Average download time: {avg_download_time:.1f}s")
                print(f"   📍 Successful locations: {len(results)}")
                
                for result in results:
                    dims = result.get("dimensions", "unknown")
                    pixels = result.get("total_pixels", 0)
                    print(f"      • {result['location']}: {result.get('file_size_mb', 0):.2f}MB, {dims} ({pixels:,} pixels)")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"{'='*60}")
        
        if successful_tests:
            # Find the configuration with best quality/size ratio
            best_quality = max(successful_tests, key=lambda x: x.get("file_size_mb", 0))
            
            print(f"🏆 HIGHEST QUALITY CONFIGURATION:")
            print(f"   📏 Area: {best_quality['area_km']}")
            print(f"   📊 File size: {best_quality.get('file_size_mb', 0):.2f} MB")
            print(f"   📍 Location: {best_quality['location']}")
            
            # Compare 25km vs smaller areas
            area_25km = [r for r in successful_tests if r["area_km"] == "25km"]
            area_smaller = [r for r in successful_tests if r["area_km"] != "25km"]
            
            if area_25km and area_smaller:
                avg_25km = sum(r.get("file_size_mb", 0) for r in area_25km) / len(area_25km)
                avg_smaller = sum(r.get("file_size_mb", 0) for r in area_smaller) / len(area_smaller)
                
                improvement = (avg_25km / avg_smaller) if avg_smaller > 0 else 0
                
                print(f"\n📊 25KM VS SMALLER AREAS:")
                print(f"   🔵 25km average: {avg_25km:.2f} MB")
                print(f"   🔴 Smaller areas average: {avg_smaller:.2f} MB")
                print(f"   ⚡ Quality improvement: {improvement:.1f}x better with 25km areas")
        else:
            print(f"❌ No successful downloads to analyze")
            print(f"🔧 Check Copernicus credentials and network connectivity")
    
    async def save_detailed_results(self):
        """Save detailed test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sentinel2_25km_quality_test_{timestamp}.json"
        
        output_data = {
            "test_metadata": {
                "test_name": "Sentinel-2 25km Quality Test",
                "timestamp": timestamp,
                "objective": "Test Sentinel-2 quality vs area size (25km optimal)",
                "total_tests": len(self.results),
                "successful_tests": len([r for r in self.results if r.get("status") == "Success"])
            },
            "test_configurations": self.test_configurations,
            "test_coordinates": self.test_coordinates,
            "detailed_results": self.results
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"\n💾 Detailed results saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Failed to save results: {e}")

async def main():
    """Main test execution"""
    print("🛰️ Starting Sentinel-2 25km Quality Test...")
    
    # Import math here since we need it in the class
    import math
    globals()['math'] = math
    
    test_suite = Sentinel2QualityTest()
    await test_suite.run_comprehensive_test()
    
    print(f"\n🎉 Sentinel-2 25km Quality Test completed!")
    print(f"📄 Check the generated JSON file for detailed results")

if __name__ == "__main__":
    asyncio.run(main())
