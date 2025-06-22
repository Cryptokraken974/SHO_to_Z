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
    
    def create_output_structure(self, tiff_file: Path, region_name: str = None) -> Path:
        """Create organized output directory structure for a TIFF file"""
        # Use region name if provided, otherwise use TIFF filename (without extension)
        if region_name:
            base_name = region_name
        else:
            base_name = tiff_file.stem
        
        # Always create output in the proper output directory structure: output/{region}/lidar/
        # This ensures coordinate-based regions don't create directories in input/
        if region_name:
            output_folder = Path("output") / region_name / "lidar"
        else:
            # Fallback to the configured output base directory
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
                                      progress_callback: Optional[Callable] = None, 
                                      region_name: str = None) -> Dict[str, str]:
        """
        DEPRECATED: Generate all raster products from the elevation TIFF
        This method is deprecated in favor of generate_all_raster_products which uses
        the unified processor to ensure proper output directory structure.
        """
        # Redirect to the new unified processor
        return await self.generate_all_raster_products(tiff_file, output_folder, progress_callback, region_name)
    
    def convert_to_png(self, products: Dict[str, str], output_folder: Path,
                       progress_callback: Optional[Callable] = None) -> Dict[str, str]:
        """Convert all TIFF products to PNG for visualization with enhanced resolution and automatic overlay generation"""
        
        # DISABLED: PNG conversion is now handled by the main tiff_processing.py pipeline
        # to avoid duplicate PNG creation. This function now returns empty dict.
        print("ℹ️ PNG conversion disabled in RasterGenerator - handled by main pipeline")
        
        if progress_callback:
            asyncio.create_task(progress_callback({
                "type": "png_conversion_skipped",
                "message": "PNG conversion skipped - handled by main pipeline to avoid duplicates"
            }))
        
        return {}
    
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
    
    async def process_single_tiff(self, tiff_file: Path, progress_callback: Optional[Callable] = None, region_name: str = None) -> Dict:
        """Process a single TIFF file through the complete pipeline"""
        overall_start = time.time()
        
        if progress_callback:
            await progress_callback({
                "type": "raster_processing_started",
                "message": f"Starting raster processing for: {tiff_file.name}",
                "file": str(tiff_file)
            })
        
        try:
            # 1. Create output structure with region name if provided
            output_folder = self.create_output_structure(tiff_file, region_name)
            
            # 2. Copy original TIFF for reference
            copied_tiff = self.copy_original_tiff(tiff_file, output_folder)
            
            # 3. Generate raster products (async)
            # Use the new unified processor instead of the original method
            products = await self.generate_all_raster_products(tiff_file, output_folder, progress_callback, region_name)
            
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
            
            # 4. Convert to PNG - DISABLED to prevent duplicates (handled by main pipeline)
            # png_outputs = self.convert_to_png(products, output_folder, progress_callback)
            png_outputs = {}  # Empty dict since PNG conversion is handled elsewhere
            
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
            result = await self.process_single_tiff(tiff_file, progress_callback, region_name)
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
                                  progress_callback: Optional[Callable] = None, 
                                  region_name: str = None) -> Dict[str, Any]:
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
        
        # Create a simple request object with region name if provided
        class SimpleRequest:
            def __init__(self, region_name):
                self.region_name = region_name
        
        request = SimpleRequest(region_name) if region_name else None
        
        # Process all raster products with region name context
        result = await process_all_raster_products(tiff_str, progress_callback, request)
        
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
