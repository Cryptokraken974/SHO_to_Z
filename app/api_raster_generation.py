#!/usr/bin/env python3
"""
Raster Generation API Service

This module provides the core functionality for automatically generating
raster products from elevation TIFF files. It extracts the working code
from the test_raster_generation.py and makes it available as an API service.

This service generates:
- Hillshade (multiple configurations)
- Slope analysis
- Aspect analysis  
- TPI (Topographic Position Index)
- Color relief maps
- PNG visualizations of all products
"""

import os
import sys
import time
import glob
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add the app directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import processing modules and utilities
try:
    # Import TIFF-native processing functions
    from app.processing.tiff_processing import (
        process_hillshade_tiff,
        process_slope_tiff,
        process_aspect_tiff,
        process_tpi_tiff,
        process_color_relief_tiff
    )
    from app.convert import convert_geotiff_to_png
    from app.image_utils import colorize_dem
    print("✅ Successfully imported TIFF processing modules")
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    # Don't exit here since this is a service module


class RasterGenerationService:
    """Service class for generating raster products from elevation TIFFs"""
    
    def __init__(self, input_dir: str = "input", output_base_dir: str = "output"):
        self.input_dir = Path(input_dir)
        self.output_base_dir = Path(output_base_dir)
        
        # Processing functions mapping (TIFF-native functions)
        self.processors = {
            'hillshade_standard': process_hillshade_tiff,
            'hillshade_315_45_08': process_hillshade_tiff,
            'hillshade_225_45_08': process_hillshade_tiff,
            'slope': process_slope_tiff,
            'aspect': process_aspect_tiff,
            'tpi': process_tpi_tiff,
            'color_relief': process_color_relief_tiff
        }
        
        # Processing parameters for different products
        self.processing_params = {
            'hillshade_standard': {'azimuth': 315, 'altitude': 45, 'z_factor': 1.0},
            'hillshade_315_45_08': {'azimuth': 315, 'altitude': 45, 'z_factor': 0.8},
            'hillshade_225_45_08': {'azimuth': 225, 'altitude': 45, 'z_factor': 0.8},
            'slope': {},
            'aspect': {},
            'tpi': {'radius': 3},
            'color_relief': {}
        }
    
    def find_elevation_tiffs_for_region(self, region_name: str) -> List[Path]:
        """Find elevation TIFF files for a specific region"""
        print(f"🔍 Scanning for elevation TIFF files for region: {region_name}")
        
        region_dir = self.input_dir / region_name
        if not region_dir.exists():
            print(f"❌ Region directory not found: {region_dir}")
            return []
        
        tiff_patterns = [
            f"*elevation*.tiff",
            f"*elevation*.tif", 
            f"*dtm*.tiff",
            f"*dtm*.tif",
            f"*dem*.tiff",
            f"*dem*.tif"
        ]
        
        found_tiffs = []
        # Search recursively in the region directory and all subdirectories
        for pattern in tiff_patterns:
            # Use ** for recursive search
            matches = list(region_dir.rglob(pattern))
            found_tiffs.extend(matches)
        
        # Remove duplicates and sort
        unique_tiffs = sorted(list(set(found_tiffs)))
        
        print(f"📁 Found {len(unique_tiffs)} elevation TIFF files:")
        for tiff in unique_tiffs:
            file_size = tiff.stat().st_size / (1024 * 1024)  # MB
            relative_path = tiff.relative_to(region_dir)
            print(f"   📄 {relative_path} ({file_size:.1f} MB)")
        
        return unique_tiffs
    
    def create_raster_output_structure(self, region_name: str) -> Path:
        """Create organized output directory structure for raster products"""
        # Create main lidar folder for this region
        raster_folder = self.output_base_dir / region_name / "lidar"
        
        # Create subdirectories for different product types
        subdirs = [
            'hillshade',
            'terrain_analysis', 
            'visualization',
            'png_outputs'
        ]
        
        for subdir in subdirs:
            (raster_folder / subdir).mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Created raster output structure: {raster_folder}")
        return raster_folder
    
    async def generate_raster_products_for_region(self, region_name: str) -> Dict[str, any]:
        """Generate all raster products for a specific region"""
        print(f"🎯 Starting raster generation for region: {region_name}")
        
        start_time = time.time()
        results = {
            'success': False,
            'region_name': region_name,
            'products_generated': [],
            'png_outputs': [],
            'errors': [],
            'processing_time': 0,
            'total_products': 0
        }
        
        try:
            # 1. Find elevation TIFF files for this region
            tiff_files = self.find_elevation_tiffs_for_region(region_name)
            
            if not tiff_files:
                results['errors'].append(f"No elevation TIFF files found for region: {region_name}")
                return results
            
            # 2. Create output structure
            raster_output_dir = self.create_raster_output_structure(region_name)
            
            # 3. Process each TIFF file
            all_products = {}
            all_png_outputs = {}
            
            for tiff_file in tiff_files:
                print(f"\n🔄 Processing: {tiff_file.name}")
                
                # Generate raster products for this TIFF
                products = await self.generate_single_tiff_products(tiff_file, raster_output_dir)
                all_products.update(products)
                
                # Convert to PNG
                png_outputs = await self.convert_products_to_png(products, raster_output_dir)
                all_png_outputs.update(png_outputs)
                
                # Generate colorized DEM
                colorized_dem = await self.generate_colorized_dem(tiff_file, raster_output_dir)
                if colorized_dem:
                    all_png_outputs[f"{tiff_file.stem}_colorized_dem"] = colorized_dem
            
            # 4. Update results
            results['success'] = True
            results['products_generated'] = list(all_products.keys())
            results['png_outputs'] = list(all_png_outputs.keys()) 
            results['total_products'] = len(all_products) + len(all_png_outputs)
            results['processing_time'] = time.time() - start_time
            
            print(f"✅ Raster generation completed for region: {region_name}")
            print(f"📊 Generated {len(all_products)} TIFF products and {len(all_png_outputs)} PNG visualizations")
            print(f"⏱️ Total processing time: {results['processing_time']:.2f} seconds")
            
        except Exception as e:
            results['errors'].append(f"Raster generation failed: {str(e)}")
            results['processing_time'] = time.time() - start_time
            print(f"❌ Raster generation failed for region {region_name}: {str(e)}")
        
        return results
    
    async def generate_single_tiff_products(self, tiff_file: Path, output_dir: Path) -> Dict[str, str]:
        """Generate all raster products from a single elevation TIFF"""
        print(f"🎯 Generating raster products for: {tiff_file.name}")
        
        tiff_str = str(tiff_file)
        products = {}
        
        # Define output directories for different product types
        output_dirs = {
            'hillshade_standard': output_dir / 'hillshade',
            'hillshade_315_45_08': output_dir / 'hillshade',
            'hillshade_225_45_08': output_dir / 'hillshade',
            'slope': output_dir / 'terrain_analysis',
            'aspect': output_dir / 'terrain_analysis', 
            'tpi': output_dir / 'terrain_analysis',
            'color_relief': output_dir / 'visualization'
        }
        
        for product_name, processor_func in self.processors.items():
            try:
                print(f"🔄 Processing: {product_name}")
                
                # Get output directory and parameters for this product
                product_output_dir = output_dirs[product_name]
                params = self.processing_params[product_name]
                
                # Call the async processing function
                result = await processor_func(tiff_str, str(product_output_dir), params)
                
                if result['status'] == 'success' and os.path.exists(result['output_file']):
                    products[product_name] = result['output_file']
                    
                    # Get file size
                    file_size = os.path.getsize(result['output_file']) / (1024 * 1024)  # MB
                    print(f"✅ {product_name} completed ({file_size:.1f} MB)")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"❌ {product_name} failed: {error_msg}")
                    
            except Exception as e:
                print(f"❌ {product_name} failed: {str(e)}")
        
        return products
    
    async def convert_products_to_png(self, products: Dict[str, str], output_dir: Path) -> Dict[str, str]:
        """Convert TIFF products to PNG for visualization"""
        print(f"🎨 Converting {len(products)} products to PNG...")
        
        png_outputs = {}
        png_dir = output_dir / 'png_outputs'
        
        for product_name, tiff_path in products.items():
            try:
                # Generate PNG filename
                tiff_basename = os.path.splitext(os.path.basename(tiff_path))[0]
                png_filename = f"{tiff_basename}.png"
                png_path = png_dir / png_filename
                
                # Convert using the existing conversion function
                result_png = convert_geotiff_to_png(tiff_path, str(png_path))
                
                if result_png and os.path.exists(result_png):
                    png_outputs[product_name] = result_png
                    
                    # Get PNG file size
                    png_size = os.path.getsize(result_png) / (1024 * 1024)  # MB
                    print(f"✅ {product_name} PNG created ({png_size:.1f} MB)")
                else:
                    print(f"❌ PNG conversion failed for {product_name}")
                    
            except Exception as e:
                print(f"❌ PNG conversion error for {product_name}: {str(e)}")
        
        return png_outputs
    
    async def generate_colorized_dem(self, tiff_file: Path, output_dir: Path) -> Optional[str]:
        """Generate a colorized DEM visualization"""
        try:
            print(f"🌈 Generating colorized DEM for: {tiff_file.name}")
            
            viz_dir = output_dir / 'visualization'
            colorized_path = viz_dir / f"{tiff_file.stem}_colorized_dem.png"
            
            # Use the colorize_dem function from image_utils
            result = colorize_dem(str(tiff_file), str(colorized_path), colormap='terrain')
            
            if result and os.path.exists(result):
                file_size = os.path.getsize(result) / (1024 * 1024)  # MB
                print(f"✅ Colorized DEM created ({file_size:.1f} MB)")
                return result
            else:
                print(f"❌ Colorized DEM generation failed")
                return None
                
        except Exception as e:
            print(f"❌ Colorized DEM error: {str(e)}")
            return None


# API endpoint function for Flask integration
async def generate_rasters_for_region(region_name: str, input_dir: str = "input", 
                                     output_dir: str = "output") -> Dict[str, any]:
    """
    Main API function to generate raster products for a region.
    
    Args:
        region_name: Name of the region to process
        input_dir: Base input directory (default: "input")
        output_dir: Base output directory (default: "output")
    
    Returns:
        Dictionary with processing results
    """
    service = RasterGenerationService(input_dir, output_dir)
    return await service.generate_raster_products_for_region(region_name)


# Test function
async def test_raster_generation(region_name: str = None):
    """Test function for the raster generation service"""
    if not region_name:
        # Find any region in the input directory
        input_dir = Path("input")
        if input_dir.exists():
            regions = [d.name for d in input_dir.iterdir() if d.is_dir()]
            if regions:
                region_name = regions[0]
                print(f"🧪 Testing with region: {region_name}")
            else:
                print("❌ No regions found in input directory")
                return
        else:
            print("❌ Input directory not found")
            return
    
    result = await generate_rasters_for_region(region_name)
    print(f"\n📋 Test Result: {result}")


if __name__ == "__main__":
    import sys
    region = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(test_raster_generation(region))
