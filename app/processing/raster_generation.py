#!/usr/bin/env python3
"""
Module for generating raster products from elevation TIFF files.

This module provides functionality to:
1. Generate various raster analysis products (hillshade, slope, aspect, TPI, color relief)
2. Organize output in structured directories 
3. Convert TIFF outputs to PNG for visualization
4. Provide detailed progress and performance reporting
"""

import os
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

# Import processing modules and utilities
from app.processing.tiff_processing import (
    process_hillshade_tiff,
    process_slope_tiff,
    process_aspect_tiff,
    process_color_relief_tiff,
    process_all_raster_products
)
from app.convert import convert_geotiff_to_png
from app.image_utils import colorize_dem
from app.overlay_optimization import OverlayOptimizer


class RasterGenerator:
    """Class for generating raster products from elevation TIFFs"""
    
    def __init__(self, output_base_dir: str = "output"):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Processing functions mapping (TIFF-native functions)
        self.processors = {
            'hillshade_standard': process_hillshade_tiff,
            'hillshade_315_45_08': process_hillshade_tiff,
            'hillshade_225_45_08': process_hillshade_tiff,
            'slope': process_slope_tiff,
            'aspect': process_aspect_tiff,
            'color_relief': process_color_relief_tiff
        }
        
        self.results = {
            'processed_files': [],
            'generated_products': [],
            'errors': [],
            'timing': {}
        }
    
    def create_output_structure(self, tiff_file: Path) -> Path:
        """Create organized output directory structure for a TIFF file"""
        # Use the TIFF filename (without extension) as the base folder name
        base_name = tiff_file.stem
        
        # Create main output folder for this TIFF
        output_folder = self.output_base_dir / base_name
        
        # Create subdirectories for different product types
        subdirs = [
            'Original',
            'Hillshade',
            'Terrain_Analysis', 
            'Visualization',
            'png_outputs'  # Changed to lowercase to match what the API is looking for
        ]
        
        for subdir in subdirs:
            (output_folder / subdir).mkdir(parents=True, exist_ok=True)
        
        return output_folder
    
    def copy_original_tiff(self, tiff_file: Path, output_folder: Path) -> Path:
        """Copy the original TIFF to the output structure for reference"""
        import shutil
        
        original_dir = output_folder / 'Original'
        copied_tiff = original_dir / tiff_file.name
        
        if not copied_tiff.exists():
            shutil.copy2(tiff_file, copied_tiff)
        
        return copied_tiff
    
    async def generate_raster_products(self, tiff_file: Path, output_folder: Path, 
                                      progress_callback: Optional[Callable] = None) -> Dict[str, str]:
        """Generate all raster products from the elevation TIFF"""
        if progress_callback:
            await progress_callback({
                "type": "raster_generation_started",
                "message": f"Generating raster products for: {tiff_file.name}"
            })
        
        # Convert Path to string for processing functions
        tiff_str = str(tiff_file)
        products = {}
        
        total_start = time.time()
        
        # Define processing parameters for different products
        processing_params = {
            'hillshade_standard': {'azimuth': 315, 'altitude': 45, 'z_factor': 1.0},
            'hillshade_315_45_08': {'azimuth': 315, 'altitude': 45, 'z_factor': 0.8},
            'hillshade_225_45_08': {'azimuth': 225, 'altitude': 45, 'z_factor': 0.8},
            'slope': {},
            'aspect': {},
            'color_relief': {}
        }
        
        # Define output directories for different product types
        output_dirs = {
            'hillshade_standard': output_folder / 'Hillshade',
            'hillshade_315_45_08': output_folder / 'Hillshade',
            'hillshade_225_45_08': output_folder / 'Hillshade',
            'slope': output_folder / 'Terrain_Analysis',
            'aspect': output_folder / 'Terrain_Analysis', 
            'color_relief': output_folder / 'Visualization'
        }
        
        for product_name, processor_func in self.processors.items():
            if progress_callback:
                await progress_callback({
                    "type": "processing_product",
                    "message": f"Processing: {product_name}"
                })
            
            product_start = time.time()
            
            try:
                # Get output directory and parameters for this product
                output_dir = output_dirs[product_name]
                params = processing_params[product_name]
                
                # Call the async processing function
                result = await processor_func(tiff_str, str(output_dir), params)
                
                if result['status'] == 'success' and os.path.exists(result['output_file']):
                    products[product_name] = result['output_file']
                    product_time = result['processing_time']
                    
                    # Store timing info
                    self.results['timing'][f"{tiff_file.stem}_{product_name}"] = product_time
                    
                    if progress_callback:
                        await progress_callback({
                            "type": "product_completed",
                            "message": f"{product_name} completed",
                            "product": product_name,
                            "output_file": result['output_file'],
                            "time": product_time
                        })
                else:
                    error_msg = result.get('error', 'Unknown error')
                    self.results['errors'].append(f"{tiff_file.name}: {product_name} - {error_msg}")
                    
                    if progress_callback:
                        await progress_callback({
                            "type": "product_error",
                            "message": f"{product_name} failed: {error_msg}",
                            "product": product_name,
                            "error": error_msg
                        })
                    
            except Exception as e:
                product_time = time.time() - product_start
                error_msg = f"{tiff_file.name}: {product_name} - {str(e)}"
                self.results['errors'].append(error_msg)
                
                if progress_callback:
                    await progress_callback({
                        "type": "product_error",
                        "message": f"{product_name} failed: {str(e)}",
                        "product": product_name,
                        "error": str(e)
                    })
        
        total_time = time.time() - total_start
        
        if progress_callback:
            await progress_callback({
                "type": "raster_generation_progress",
                "message": f"Generated {len(products)} products in {total_time:.2f}s",
                "products_count": len(products),
                "total_time": total_time
            })
        
        return products
    
    def convert_to_png(self, products: Dict[str, str], output_folder: Path,
                       progress_callback: Optional[Callable] = None) -> Dict[str, str]:
        """Convert all TIFF products to PNG for visualization with enhanced resolution and automatic overlay generation"""
        if progress_callback:
            asyncio.create_task(progress_callback({
                "type": "png_conversion_started",
                "message": "Converting products to PNG with ENHANCED RESOLUTION and automatic overlay generation"
            }))
        
        png_outputs = {}
        png_dir = output_folder / 'png_outputs'
        
        # Initialize overlay optimizer
        overlay_optimizer = OverlayOptimizer()
        
        conversion_start = time.time()
        
        for product_name, tiff_path in products.items():
            try:
                # Generate PNG filename
                tiff_basename = os.path.splitext(os.path.basename(tiff_path))[0]
                png_filename = f"{tiff_basename}.png"
                png_path = png_dir / png_filename
                
                # Convert using the ENHANCED resolution conversion function
                result_png = convert_geotiff_to_png(tiff_path, str(png_path), enhanced_resolution=True)
                
                if result_png and os.path.exists(result_png):
                    png_outputs[product_name] = result_png
                    
                    # Check if we need to generate an optimized overlay version
                    if progress_callback:
                        asyncio.create_task(progress_callback({
                            "type": "overlay_optimization_check",
                            "message": f"Checking {product_name} for overlay optimization..."
                        }))
                    
                    # Generate overlay from TIFF (more efficient than PNG optimization)
                    overlay_path = overlay_optimizer.optimize_tiff_to_overlay(tiff_path)
                    
                    if overlay_path:
                        if progress_callback:
                            asyncio.create_task(progress_callback({
                                "type": "overlay_generated",
                                "message": f"Generated optimized overlay for {product_name}",
                                "product": product_name,
                                "overlay_file": overlay_path
                            }))
                    
                    if progress_callback:
                        asyncio.create_task(progress_callback({
                            "type": "png_conversion_progress",
                            "message": f"Converted {product_name} to ENHANCED PNG",
                            "product": product_name,
                            "png_file": result_png
                        }))
                else:
                    self.results['errors'].append(f"PNG conversion failed: {product_name}")
                    
                    if progress_callback:
                        asyncio.create_task(progress_callback({
                            "type": "png_conversion_error",
                            "message": f"PNG conversion failed for {product_name}",
                            "product": product_name
                        }))
                    
            except Exception as e:
                error_msg = f"PNG conversion error for {product_name}: {str(e)}"
                self.results['errors'].append(error_msg)
                
                if progress_callback:
                    asyncio.create_task(progress_callback({
                        "type": "png_conversion_error",
                        "message": error_msg,
                        "product": product_name,
                        "error": str(e)
                    }))
        
        conversion_time = time.time() - conversion_start
        
        # Get optimization summary
        optimization_summary = overlay_optimizer.get_optimization_summary()
        
        if progress_callback:
            asyncio.create_task(progress_callback({
                "type": "png_conversion_completed",
                "message": f"ENHANCED PNG conversion completed in {conversion_time:.2f}s. Overlays: {optimization_summary['optimized_count']} generated, {optimization_summary['skipped_count']} skipped",
                "successful": len(png_outputs),
                "failed": len(products) - len(png_outputs),
                "total_time": conversion_time,
                "overlay_summary": optimization_summary
            }))
        
        # Log overlay optimization summary
        if optimization_summary['optimized_count'] > 0:
            print(f"\n🎯 Overlay Optimization Summary:")
            print(f"   ✅ Generated: {optimization_summary['optimized_count']} overlay files")
            print(f"   ⏭️ Skipped: {optimization_summary['skipped_count']} (below threshold)")
            if optimization_summary['error_count'] > 0:
                print(f"   ❌ Errors: {optimization_summary['error_count']}")
        
        return png_outputs
    
    def generate_colorized_dem(self, original_tiff: Path, output_folder: Path,
                              progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Generate a colorized DEM visualization with enhanced quality"""
        try:
            if progress_callback:
                asyncio.create_task(progress_callback({
                    "type": "colorized_dem_started",
                    "message": "Generating ENHANCED colorized DEM visualization"
                }))
            
            colorize_start = time.time()
            
            viz_dir = output_folder / 'Visualization'
            colorized_path = viz_dir / f"{original_tiff.stem}_colorized_dem.png"
            
            # Use the enhanced colorize_dem function from image_utils
            result = colorize_dem(str(original_tiff), str(colorized_path), colormap='terrain', enhanced_resolution=True)
            
            colorize_time = time.time() - colorize_start
            
            if result and os.path.exists(result):
                if progress_callback:
                    asyncio.create_task(progress_callback({
                        "type": "colorized_dem_completed",
                        "message": f"ENHANCED colorized DEM created in {colorize_time:.2f}s",
                        "output_file": result,
                        "time": colorize_time
                    }))
                return result
            else:
                if progress_callback:
                    asyncio.create_task(progress_callback({
                        "type": "colorized_dem_error",
                        "message": "Enhanced colorized DEM generation failed"
                    }))
                return None
                
        except Exception as e:
            colorize_time = time.time() - colorize_start
            
            if progress_callback:
                asyncio.create_task(progress_callback({
                    "type": "colorized_dem_error",
                    "message": f"Colorized DEM error: {str(e)}",
                    "error": str(e)
                }))
            
            self.results['errors'].append(f"Colorized DEM error: {str(e)}")
            return None
    
    def organize_outputs(self, products: Dict[str, str], png_outputs: Dict[str, str], 
                        output_folder: Path) -> None:
        """Organize outputs into appropriate subdirectories"""
        # Mapping of product types to subdirectories
        organization_map = {
            'hillshade_standard': 'Hillshade',
            'hillshade_315_45_08': 'Hillshade', 
            'hillshade_225_45_08': 'Hillshade',
            'slope': 'Terrain_Analysis',
            'aspect': 'Terrain_Analysis',
            'color_relief': 'Visualization'
        }
        
        import shutil
        
        # Organize TIFF products
        for product_name, tiff_path in products.items():
            target_dir = organization_map.get(product_name, 'Terrain_Analysis')
            target_folder = output_folder / target_dir
            target_path = target_folder / os.path.basename(tiff_path)
            
            try:
                if not target_path.exists() and os.path.exists(tiff_path):
                    shutil.move(tiff_path, target_path)
            except Exception:
                # If move fails, don't raise an error - the file might already be in the right place
                pass
    
    async def process_single_tiff(self, tiff_file: Path, progress_callback: Optional[Callable] = None) -> Dict:
        """Process a single TIFF file through the complete pipeline"""
        overall_start = time.time()
        
        if progress_callback:
            await progress_callback({
                "type": "raster_processing_started",
                "message": f"Starting raster processing for: {tiff_file.name}",
                "file": str(tiff_file)
            })
        
        try:
            # 1. Create output structure
            output_folder = self.create_output_structure(tiff_file)
            
            # 2. Copy original TIFF for reference
            copied_tiff = self.copy_original_tiff(tiff_file, output_folder)
            
            # 3. Generate raster products (async)
            # Use the new unified processor instead of the original method
            products = await self.generate_all_raster_products(tiff_file, output_folder, progress_callback)
            
            if not products:
                if progress_callback:
                    await progress_callback({
                        "type": "raster_processing_error",
                        "message": f"No products generated for {tiff_file.name}",
                        "file": str(tiff_file)
                    })
                return {
                    "success": False,
                    "message": f"No products generated for {tiff_file.name}",
                    "file": str(tiff_file)
                }
            
            # 4. Convert to PNG
            png_outputs = self.convert_to_png(products, output_folder, progress_callback)
            
            # 5. Generate colorized DEM
            colorized_dem = self.generate_colorized_dem(tiff_file, output_folder, progress_callback)
            
            # 6. Organize outputs
            self.organize_outputs(products, png_outputs, output_folder)
            
            overall_time = time.time() - overall_start
            
            # Update results
            self.results['processed_files'].append({
                'name': tiff_file.name,
                'path': str(tiff_file),
                'output_folder': str(output_folder),
                'products_count': len(products),
                'png_count': len(png_outputs),
                'processing_time': overall_time,
                'success': True
            })
            
            if progress_callback:
                await progress_callback({
                    "type": "raster_processing_completed",
                    "message": f"Raster processing completed for: {tiff_file.name}",
                    "file": str(tiff_file),
                    "output_folder": str(output_folder),
                    "products_count": len(products),
                    "png_count": len(png_outputs),
                    "processing_time": overall_time
                })
            
            return {
                "success": True,
                "message": f"Raster processing completed for: {tiff_file.name}",
                "file": str(tiff_file),
                "output_folder": str(output_folder),
                "products": list(products.keys()),
                "png_outputs": list(png_outputs.keys()),
                "processing_time": overall_time
            }
            
        except Exception as e:
            overall_time = time.time() - overall_start
            error_msg = f"Overall processing failed for {tiff_file.name}: {str(e)}"
            
            self.results['errors'].append(error_msg)
            self.results['processed_files'].append({
                'name': tiff_file.name,
                'path': str(tiff_file),
                'output_folder': None,
                'products_count': 0,
                'png_count': 0,
                'processing_time': overall_time,
                'success': False
            })
            
            if progress_callback:
                await progress_callback({
                    "type": "raster_processing_error",
                    "message": error_msg,
                    "file": str(tiff_file),
                    "error": str(e)
                })
            
            return {
                "success": False,
                "message": error_msg,
                "file": str(tiff_file),
                "error": str(e)
            }

    async def find_and_process_elevation_tiffs(self, 
                                              input_path: str, 
                                              progress_callback: Optional[Callable] = None,
                                              region_name: Optional[str] = None) -> Dict:
        """Find and process all elevation TIFF files in the input path"""
        
        if progress_callback:
            await progress_callback({
                "type": "elevation_tiff_search_started",
                "message": f"Searching for elevation TIFF files in: {input_path}"
            })
        
        input_dir = Path(input_path)
        
        # Define patterns for elevation TIFF files
        tiff_patterns = [
            "**/*elevation*.tiff",
            "**/*elevation*.tif", 
            "**/*dtm*.tiff",
            "**/*dtm*.tif",
            "**/*dem*.tiff",
            "**/*dem*.tif"
        ]
        
        # If region_name is provided, refine the search
        if region_name:
            region_patterns = []
            for pattern in tiff_patterns:
                region_patterns.append(f"**/{region_name}/{pattern}")
                region_patterns.append(f"**/{region_name}*/{pattern}")
            tiff_patterns.extend(region_patterns)
        
        found_tiffs = []
        for pattern in tiff_patterns:
            matches = list(input_dir.glob(pattern))
            found_tiffs.extend(matches)
        
        # Remove duplicates and sort
        unique_tiffs = sorted(list(set(found_tiffs)))
        
        if progress_callback:
            await progress_callback({
                "type": "elevation_tiff_search_completed",
                "message": f"Found {len(unique_tiffs)} elevation TIFF files",
                "files": [str(tiff) for tiff in unique_tiffs]
            })
        
        if not unique_tiffs:
            return {
                "success": False,
                "message": "No elevation TIFF files found",
                "files_processed": 0
            }
        
        results = []
        for tiff_file in unique_tiffs:
            result = await self.process_single_tiff(tiff_file, progress_callback)
            results.append(result)
        
        successful = [r for r in results if r["success"]]
        
        return {
            "success": len(successful) > 0,
            "message": f"Processed {len(successful)}/{len(unique_tiffs)} elevation TIFF files successfully",
            "files_processed": len(unique_tiffs),
            "successful_count": len(successful),
            "failed_count": len(unique_tiffs) - len(successful),
            "results": results
        }

    async def generate_all_raster_products(self, tiff_file: Path, output_folder: Path, 
                                  progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process all raster products using the unified process_all_raster_products function.
        This method is an alternative to the manual processing and uses the updated function
        that excludes TRI processing but includes TPI processing.
        """
        if progress_callback:
            await progress_callback({
                "type": "raster_generation_started",
                "message": f"Generating raster products for: {tiff_file.name} using unified processor"
            })
        
        from app.processing.tiff_processing import process_all_raster_products
        
        # Convert Path to string
        tiff_str = str(tiff_file)
        
        # Process all raster products
        result = await process_all_raster_products(tiff_str, progress_callback)
        
        if progress_callback:
            await progress_callback({
                "type": "raster_generation_progress",
                "message": f"Generated {result.get('successful', 0)}/{result.get('total_tasks', 0)} products",
                "success_count": result.get('successful', 0),
                "total_count": result.get('total_tasks', 0)
            })
        
        # Convert the result format to match the expected output of generate_raster_products
        products = {}
        for product_name, product_result in result.get('results', {}).items():
            if product_result.get('status') == 'success':
                products[product_name] = product_result.get('output_file', '')
        
        return products
