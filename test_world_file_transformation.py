#!/usr/bin/env python3
"""
Fix for world file coordinate transformation.
This function creates WGS84 world files for PNG overlays.
"""

import os
from osgeo import gdal, osr
from typing import Optional

def create_wgs84_world_file(original_world_file: str, tiff_path: str, png_path: str) -> bool:
    """
    Create a WGS84 world file for PNG overlay by transforming coordinates
    from the original TIFF projection to WGS84.
    
    Args:
        original_world_file: Path to the original world file (in projected coordinates)
        tiff_path: Path to the source TIFF file (for projection info)
        png_path: Path to the PNG file (for output world file naming)
    
    Returns:
        True if WGS84 world file was created successfully
    """
    try:
        # Read original world file
        if not os.path.exists(original_world_file):
            print(f"❌ Original world file not found: {original_world_file}")
            return False
            
        with open(original_world_file, 'r') as f:
            lines = [float(line.strip()) for line in f.readlines()]
            
        if len(lines) != 6:
            print(f"❌ Invalid world file format: {original_world_file}")
            return False
            
        pixel_size_x = lines[0]
        rotation_y = lines[1] 
        rotation_x = lines[2]
        pixel_size_y = lines[3]
        upper_left_x = lines[4]
        upper_left_y = lines[5]
        
        print(f"📄 Original world file parameters:")
        print(f"   Pixel size: {pixel_size_x}, {pixel_size_y}")
        print(f"   Upper left: {upper_left_x}, {upper_left_y}")
        
        # Get projection info from TIFF
        ds = gdal.Open(tiff_path)
        if not ds:
            print(f"❌ Could not open TIFF: {tiff_path}")
            return False
            
        projection = ds.GetProjection()
        geotransform = ds.GetGeoTransform()
        width = ds.RasterXSize
        height = ds.RasterYSize
        ds = None
        
        if not projection:
            print(f"❌ No projection information in TIFF: {tiff_path}")
            return False
            
        # Create coordinate transformation
        source_srs = osr.SpatialReference(wkt=projection)
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(4326)  # WGS84
        
        transform = osr.CoordinateTransformation(source_srs, target_srs)
        
        # Transform upper left corner
        ul_wgs84 = transform.TransformPoint(upper_left_x, upper_left_y)
        ul_lon, ul_lat = ul_wgs84[0], ul_wgs84[1]
        
        # Calculate pixel size in WGS84 degrees
        # Transform a point one pixel to the right and one pixel down
        right_point = transform.TransformPoint(upper_left_x + pixel_size_x, upper_left_y)
        down_point = transform.TransformPoint(upper_left_x, upper_left_y + pixel_size_y)
        
        # Calculate pixel sizes in degrees
        pixel_size_x_wgs84 = right_point[0] - ul_lon
        pixel_size_y_wgs84 = down_point[1] - ul_lat
        
        print(f"🌍 Transformed to WGS84:")
        print(f"   Upper left: {ul_lon:.8f}, {ul_lat:.8f}")
        print(f"   Pixel size: {pixel_size_x_wgs84:.8f}, {pixel_size_y_wgs84:.8f}")
        
        # Create WGS84 world file
        wgs84_world_file = os.path.splitext(png_path)[0] + "_wgs84.wld"
        
        with open(wgs84_world_file, 'w') as f:
            f.write(f"{pixel_size_x_wgs84:.10f}\n")
            f.write(f"0.0000000000\n")  # rotation_y
            f.write(f"0.0000000000\n")  # rotation_x 
            f.write(f"{pixel_size_y_wgs84:.10f}\n")
            f.write(f"{ul_lon:.10f}\n")
            f.write(f"{ul_lat:.10f}\n")
            
        print(f"✅ Created WGS84 world file: {wgs84_world_file}")
        
        # Calculate and display coverage info
        # Calculate lower right corner
        lr_x = upper_left_x + (width * pixel_size_x)
        lr_y = upper_left_y + (height * pixel_size_y)
        lr_wgs84 = transform.TransformPoint(lr_x, lr_y)
        lr_lon, lr_lat = lr_wgs84[0], lr_wgs84[1]
        
        width_deg = abs(lr_lon - ul_lon)
        height_deg = abs(lr_lat - ul_lat)
        width_km = width_deg * 111
        height_km = height_deg * 111
        
        print(f"📏 Coverage: {width_deg:.6f}° × {height_deg:.6f}° ({width_km:.2f}km × {height_km:.2f}km)")
        print(f"📊 Bounds: N:{max(ul_lat, lr_lat):.6f}, S:{min(ul_lat, lr_lat):.6f}, E:{max(ul_lon, lr_lon):.6f}, W:{min(ul_lon, lr_lon):.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating WGS84 world file: {e}")
        return False

def test_world_file_transformation():
    """Test the world file transformation function"""
    
    print(f"🧪 Testing World File Transformation")
    print("=" * 50)
    
    # Test with OR_WizardIsland_1 region
    test_cases = [
        {
            "region": "OR_WizardIsland_1",
            "overlay": "CHM",
            "description": "Oregon Lambert feet to WGS84"
        },
        {
            "region": "PRGL1260C9597_2014", 
            "overlay": "CHM",
            "description": "UTM Zone 18S meters to WGS84"
        }
    ]
    
    for test_case in test_cases:
        region = test_case["region"]
        overlay = test_case["overlay"]
        
        print(f"\n📊 Testing {region} - {overlay}")
        print(f"📝 {test_case['description']}")
        print("-" * 40)
        
        # File paths
        png_path = f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/{region}/lidar/png_outputs/{overlay}.png"
        world_file = f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/{region}/lidar/png_outputs/{overlay}.wld"
        
        # Find the TIFF file
        tiff_dirs = [
            f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/{region}/lidar/{overlay}",
            f"/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/{region}/lidar/CHM"
        ]
        
        tiff_path = None
        for tiff_dir in tiff_dirs:
            if os.path.exists(tiff_dir):
                for file in os.listdir(tiff_dir):
                    if file.endswith('.tif'):
                        tiff_path = os.path.join(tiff_dir, file)
                        break
                if tiff_path:
                    break
        
        if not tiff_path:
            print(f"❌ No TIFF file found for {region}/{overlay}")
            continue
            
        if not os.path.exists(world_file):
            print(f"❌ World file not found: {world_file}")
            continue
            
        print(f"📄 Input files:")
        print(f"   PNG: {os.path.basename(png_path)}")
        print(f"   World: {os.path.basename(world_file)}")  
        print(f"   TIFF: {os.path.basename(tiff_path)}")
        
        # Test transformation
        success = create_wgs84_world_file(world_file, tiff_path, png_path)
        
        if success:
            print(f"✅ Transformation successful for {region}")
        else:
            print(f"❌ Transformation failed for {region}")
    
    print(f"\n🎯 Summary:")
    print("✅ World file transformation function implemented")
    print("💡 This can be integrated into PNG conversion process")
    print("🔧 Next: Add this to convert.py after PNG generation")

if __name__ == "__main__":
    test_world_file_transformation()
