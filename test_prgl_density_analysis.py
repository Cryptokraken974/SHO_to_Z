#!/usr/bin/env python3
"""
Test script for PRGL LAZ Density Analysis
Tests the density analysis functionality with the PRGL1260C9597_2014.laz file
"""

import sys
import os
from pathlib import Path
import tempfile
import time

# Add the project root to Python path
sys.path.insert(0, '/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

def test_prgl_density_analysis():
    """Test density analysis on the PRGL LAZ file"""
    
    print("🧪 Testing Density Analysis with PRGL LAZ File...")
    
    # Test with PRGL LAZ file (loaded LAZ, not coordinate-generated)
    laz_file = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ/PRGL1260C9597_2014.laz"
    region_name = "PRGL1260C9597_2014"
    
    # Check if LAZ file exists
    if not os.path.exists(laz_file):
        print(f"❌ LAZ file not found: {laz_file}")
        return False
    
    print(f"✅ Found LAZ file: {laz_file}")
    file_size_mb = round(os.path.getsize(laz_file) / (1024 * 1024), 2)
    print(f"   File size: {file_size_mb} MB")
    
    # Test LAZ classification first
    try:
        from app.processing.laz_classifier import LAZClassifier
        
        is_loaded, reason = LAZClassifier.is_loaded_laz(laz_file)
        print(f"📋 LAZ Classification:")
        print(f"   Is loaded LAZ: {is_loaded}")
        print(f"   Reason: {reason}")
        
        if not is_loaded:
            print(f"⚠️ Warning: LAZ file is not classified as 'loaded' - continuing anyway for test")
        
    except Exception as e:
        print(f"⚠️ LAZ classification failed: {e}")
    
    # Test density analysis
    try:
        from app.processing.density_analysis import DensityAnalyzer
        
        print(f"\n🔍 Starting Density Analysis...")
        
        # Create output directory
        output_dir = f"output/{region_name}/lidar"
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize density analyzer
        analyzer = DensityAnalyzer(resolution=1.0, nodata_value=0)
        print(f"   Resolution: {analyzer.resolution}m")
        print(f"   NoData value: {analyzer.nodata_value}")
        
        # Check system requirements first
        print(f"\n🔧 Checking system requirements...")
        
        # Check if PDAL is available
        import subprocess
        try:
            result = subprocess.run(['pdal', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"   ✅ PDAL available: {result.stdout.strip()}")
                pdal_available = True
            else:
                print(f"   ❌ PDAL not available or failed")
                pdal_available = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"   ❌ PDAL not found in system PATH")
            pdal_available = False
        
        # Check if GDAL is available
        try:
            result = subprocess.run(['gdalinfo', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"   ✅ GDAL available: {result.stdout.strip()}")
                gdal_available = True
            else:
                print(f"   ❌ GDAL not available or failed")
                gdal_available = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"   ❌ GDAL not found in system PATH")
            gdal_available = False
        
        if not pdal_available:
            print(f"\n⚠️ PDAL not available - cannot perform full density analysis")
            print(f"   To install PDAL: brew install pdal")
            return False
        
        if not gdal_available:
            print(f"\n⚠️ GDAL not available - visualization may not work")
            print(f"   To install GDAL: brew install gdal")
        
        # Perform density analysis
        print(f"\n🚀 Running density analysis...")
        start_time = time.time()
        
        result = analyzer.generate_density_raster(
            laz_file_path=laz_file,
            output_dir=output_dir,
            region_name=region_name
        )
        
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        
        print(f"\n📊 Analysis Results:")
        print(f"   Processing time: {processing_time} seconds")
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"   ✅ Density analysis completed successfully!")
            
            # Check output files
            if 'tiff_path' in result:
                tiff_path = Path(result['tiff_path'])
                if tiff_path.exists():
                    tiff_size_mb = round(tiff_path.stat().st_size / (1024 * 1024), 2)
                    print(f"   📁 TIFF output: {tiff_path}")
                    print(f"      Size: {tiff_size_mb} MB")
                
            if 'png_path' in result:
                png_path = Path(result['png_path'])
                if png_path.exists():
                    png_size_mb = round(png_path.stat().st_size / (1024 * 1024), 2)
                    print(f"   🎨 PNG output: {png_path}")
                    print(f"      Size: {png_size_mb} MB")
            
            if 'metadata_path' in result:
                metadata_path = Path(result['metadata_path'])
                if metadata_path.exists():
                    print(f"   📋 Metadata: {metadata_path}")
            
            # Display metadata if available
            if 'metadata' in result:
                metadata = result['metadata']
                if 'statistics' in metadata:
                    stats = metadata['statistics']
                    print(f"\n📈 Density Statistics:")
                    if 'min' in stats:
                        print(f"      Min density: {stats['min']} points/cell")
                    if 'max' in stats:
                        print(f"      Max density: {stats['max']} points/cell")
                    if 'mean' in stats:
                        print(f"      Mean density: {stats['mean']:.2f} points/cell")
                    if 'stddev' in stats:
                        print(f"      Std deviation: {stats['stddev']:.2f}")
            
            return True
            
        else:
            print(f"   ❌ Density analysis failed!")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Density analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_density_service():
    """Test the density service with PRGL LAZ file"""
    
    print(f"\n🧪 Testing Density Service with PRGL LAZ...")
    
    try:
        from app.processing.laz_density_service import LAZDensityService
        
        # Initialize service
        service = LAZDensityService(resolution=1.0)
        
        # Check requirements
        requirements = service.check_density_requirements()
        print(f"📋 System Requirements:")
        print(f"   PDAL available: {requirements['pdal_available']}")
        print(f"   GDAL available: {requirements['gdal_available']}")
        print(f"   System ready: {requirements['system_ready']}")
        
        if not requirements['system_ready']:
            print(f"   Missing tools: {', '.join(requirements['missing_tools'])}")
            return False
        
        # Process PRGL LAZ file
        laz_file = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/input/LAZ/PRGL1260C9597_2014.laz"
        
        if not os.path.exists(laz_file):
            print(f"❌ LAZ file not found: {laz_file}")
            return False
        
        print(f"\n🚀 Processing LAZ file with service...")
        result = service.process_loaded_laz_file(laz_file)
        
        print(f"📊 Service Results:")
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"   ✅ Service processing completed!")
            if 'density_result' in result:
                density_result = result['density_result']
                if 'tiff_path' in density_result:
                    print(f"   📁 Output: {density_result['tiff_path']}")
            return True
        else:
            print(f"   ❌ Service processing failed!")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Density service test failed: {e}")
        return False

def main():
    """Run the PRGL density analysis tests"""
    
    print(f"🚀 PRGL LAZ Density Analysis Test")
    print(f"=" * 50)
    
    tests = [
        ("PRGL Density Analysis", test_prgl_density_analysis),
        ("Density Service", test_density_service)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print(f"=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print(f"🎉 All tests passed! PRGL density analysis works correctly.")
    else:
        print(f"⚠️ Some tests failed. Check the implementation or system requirements.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
