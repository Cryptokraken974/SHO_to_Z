#!/usr/bin/env python3
"""
Test script for generating raster products from elevation TIFF files.

This script:
1. Scans the input directory for elevation TIFF files
2. Generates various raster analysis products (hillshade, slope, aspect, TPI, color relief)
3. Organizes output in structured directories 
4. Converts TIFF outputs to PNG for visualization
5. Provides detailed progress and performance reporting

Created for testing the raster generation pipeline with actual elevation data.
"""

import os
import sys
import time
import glob
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional

# Add the app directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import processing modules and utilities
try:
    # Import TIFF-native processing functions
    from app.processing.tiff_processing import (
        process_hillshade_tiff,
        process_multi_hillshade_tiff,
        create_rgb_hillshade,
        create_tint_overlay,
        create_slope_overlay,
        process_slope_tiff,
        process_slope_relief_tiff,
        process_aspect_tiff,
        process_tpi_tiff,
        process_color_relief_tiff
    )
    from app.convert import convert_geotiff_to_png
    from app.image_utils import colorize_dem
    print("✅ Successfully imported TIFF processing modules")
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)


class RasterTestGenerator:
    """Test class for generating raster products from elevation TIFFs"""
    
    def __init__(self, input_dir: str = "input", output_base_dir: str = "Tests/raster_outputs"):
        self.input_dir = Path(input_dir)
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Load hillshade definitions from JSON
        hillshade_path = Path(__file__).resolve().parent.parent / 'app/processing/pipelines_json/hillshade.json'
        try:
            with open(hillshade_path, 'r') as f:
                hillshade_defs = json.load(f)
        except Exception:
            hillshade_defs = []

        self.processors = {}
        for hs in hillshade_defs:
            if hs.get('multi'):
                self.processors[hs['name']] = process_multi_hillshade_tiff
            else:
                self.processors[hs['name']] = process_hillshade_tiff

        # Add other processors
        self.processors.update({
            'slope': process_slope_tiff,
            'slope_relief': process_slope_relief_tiff,
            'aspect': process_aspect_tiff,
            'tpi': process_tpi_tiff,
            'color_relief': process_color_relief_tiff
        })
        
        self.results = {
            'processed_files': [],
            'generated_products': [],
            'errors': [],
            'timing': {}
        }
    
    def find_elevation_tiffs(self) -> List[Path]:
        """Find all elevation TIFF files in the input directory"""
        print(f"\n🔍 Scanning for elevation TIFF files in: {self.input_dir}")
        
        tiff_patterns = [
            "**/*elevation*.tiff",
            "**/*elevation*.tif", 
            "**/*dtm*.tiff",
            "**/*dtm*.tif",
            "**/*dem*.tiff",
            "**/*dem*.tif"
        ]
        
        found_tiffs = []
        for pattern in tiff_patterns:
            matches = list(self.input_dir.glob(pattern))
            found_tiffs.extend(matches)
        
        # Remove duplicates and sort
        unique_tiffs = sorted(list(set(found_tiffs)))
        
        print(f"📁 Found {len(unique_tiffs)} elevation TIFF files:")
        for tiff in unique_tiffs:
            file_size = tiff.stat().st_size / (1024 * 1024)  # MB
            print(f"   📄 {tiff.name} ({file_size:.1f} MB)")
            print(f"      📍 Path: {tiff}")
        
        return unique_tiffs
    
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
            'png_outputs'
        ]
        
        for subdir in subdirs:
            (output_folder / subdir).mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Created output structure: {output_folder}")
        return output_folder
    
    def copy_original_tiff(self, tiff_file: Path, output_folder: Path) -> Path:
        """Copy the original TIFF to the output structure for reference"""
        import shutil
        
        original_dir = output_folder / 'Original'
        copied_tiff = original_dir / tiff_file.name
        
        if not copied_tiff.exists():
            print(f"📋 Copying original TIFF to output structure...")
            shutil.copy2(tiff_file, copied_tiff)
            print(f"✅ Original TIFF copied to: {copied_tiff}")
        
        return copied_tiff
    
    async def generate_raster_products(self, tiff_file: Path, output_folder: Path) -> Dict[str, str]:
        """Generate all raster products from the elevation TIFF"""
        print(f"\n🎯 Generating raster products for: {tiff_file.name}")
        
        # Convert Path to string for processing functions
        tiff_str = str(tiff_file)
        products = {}
        
        total_start = time.time()
        
        # Load hillshade parameters from JSON
        hillshade_path = Path(__file__).resolve().parent.parent / 'app/processing/pipelines_json/hillshade.json'
        try:
            with open(hillshade_path, 'r') as f:
                hillshade_defs = json.load(f)
        except Exception:
            hillshade_defs = []

        processing_params = {}
        for hs in hillshade_defs:
            params = {
                'azimuth': hs.get('azimuth'),
                'altitude': hs.get('altitude'),
                'azimuths': hs.get('azimuths'),
                'z_factor': hs.get('z_factor', 1.0),
                'output_filename': hs.get('output')
            }
            processing_params[hs['name']] = params

        processing_params.update({
            'slope': {},
            'slope_relief': {},
            'aspect': {},
            'tpi': {'radius': 3},
            'color_relief': {}
        })
        
        # Define output directories for different product types
        output_dirs = {name: output_folder / 'Hillshade' for name in processing_params if name not in ['slope', 'aspect', 'tpi', 'color_relief']}
        output_dirs.update({
            'slope': output_folder / 'Terrain_Analysis',
            'slope_relief': output_folder / 'Visualization',
            'aspect': output_folder / 'Terrain_Analysis',
            'tpi': output_folder / 'Terrain_Analysis',
            'color_relief': output_folder / 'Visualization'
        })
        
        for product_name, processor_func in self.processors.items():
            print(f"\n🔄 Processing: {product_name}")
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
                    
                    # Get file size
                    file_size = os.path.getsize(result['output_file']) / (1024 * 1024)  # MB
                    
                    print(f"✅ {product_name} completed in {product_time:.2f}s")
                    print(f"   📄 Output: {result['output_file']}")
                    print(f"   📊 Size: {file_size:.1f} MB")
                    
                    # Store timing info
                    self.results['timing'][f"{tiff_file.stem}_{product_name}"] = product_time
                    
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"❌ {product_name} failed: {error_msg}")
                    self.results['errors'].append(f"{tiff_file.name}: {product_name} - {error_msg}")
                    
            except Exception as e:
                product_time = time.time() - product_start
                error_msg = f"{tiff_file.name}: {product_name} - {str(e)}"
                print(f"❌ {product_name} failed after {product_time:.2f}s: {str(e)}")
                self.results['errors'].append(error_msg)

        # Create RGB composite if all channels were generated
        rgb_required = ['hs_red', 'hs_green', 'hs_blue']
        if all(name in products for name in rgb_required):
            rgb_output = output_folder / 'HillshadeRgb' / 'hillshade_rgb.tif'
            hs_paths = {
                'R': products['hs_red'],
                'G': products['hs_green'],
                'B': products['hs_blue']
            }
            rgb_result = await create_rgb_hillshade(hs_paths, str(rgb_output))
            if rgb_result['status'] == 'success':
                products['hillshade_rgb'] = rgb_result['output_file']

                # Create tint overlay using color relief
                if 'color_relief' in products:
                    tint_output = output_folder / 'HillshadeRgb' / 'tint_overlay.tif'
                    tint_res = await create_tint_overlay(products['color_relief'], rgb_result['output_file'], str(tint_output))
                    if tint_res['status'] == 'success':
                        products['tint_overlay'] = tint_res['output_file']

                        # Blend tint overlay with slope relief if available
                        if 'slope_relief' in products:
                            boosted_output = output_folder / 'HillshadeRgb' / 'boosted_hillshade.tif'
                            slope_res = await create_slope_overlay(str(tint_output), products['slope_relief'], str(boosted_output))
                            if slope_res['status'] == 'success':
                                products['boosted_hillshade'] = slope_res['output_file']

        total_time = time.time() - total_start
        print(f"\n⏱️ Total processing time for {tiff_file.name}: {total_time:.2f} seconds")
        print(f"✅ Generated {len(products)} products successfully")

        return products
    
    def convert_to_png(self, products: Dict[str, str], output_folder: Path) -> Dict[str, str]:
        """Convert all TIFF products to PNG for visualization"""
        print(f"\n🎨 Converting products to PNG for visualization...")
        
        png_outputs = {}
        png_dir = output_folder / 'png_outputs'
        
        conversion_start = time.time()
        
        for product_name, tiff_path in products.items():
            try:
                print(f"\n🔄 Converting {product_name} to PNG...")
                convert_start = time.time()
                
                # Generate PNG filename
                tiff_basename = os.path.splitext(os.path.basename(tiff_path))[0]
                png_filename = f"{tiff_basename}.png"
                png_path = png_dir / png_filename
                
                # Convert using the existing conversion function
                result_png = convert_geotiff_to_png(tiff_path, str(png_path))
                
                if result_png and os.path.exists(result_png):
                    png_outputs[product_name] = result_png
                    convert_time = time.time() - convert_start
                    
                    # Get PNG file size
                    png_size = os.path.getsize(result_png) / (1024 * 1024)  # MB
                    
                    print(f"✅ PNG conversion completed in {convert_time:.2f}s")
                    print(f"   📄 PNG: {result_png}")
                    print(f"   📊 Size: {png_size:.1f} MB")
                    
                else:
                    print(f"❌ PNG conversion failed for {product_name}")
                    self.results['errors'].append(f"PNG conversion failed: {product_name}")
                    
            except Exception as e:
                convert_time = time.time() - convert_start
                error_msg = f"PNG conversion error for {product_name}: {str(e)}"
                print(f"❌ {error_msg} (after {convert_time:.2f}s)")
                self.results['errors'].append(error_msg)
        
        conversion_time = time.time() - conversion_start
        print(f"\n🎨 PNG conversion summary:")
        print(f"   ⏱️ Total time: {conversion_time:.2f} seconds")
        print(f"   ✅ Successful: {len(png_outputs)}")
        print(f"   ❌ Failed: {len(products) - len(png_outputs)}")
        
        return png_outputs
    
    def generate_colorized_dem(self, original_tiff: Path, output_folder: Path) -> Optional[str]:
        """Generate a colorized DEM visualization"""
        try:
            print(f"\n🌈 Generating colorized DEM visualization...")
            colorize_start = time.time()
            
            viz_dir = output_folder / 'Visualization'
            colorized_path = viz_dir / f"{original_tiff.stem}_colorized_dem.png"
            
            # Use the colorize_dem function from image_utils
            result = colorize_dem(str(original_tiff), str(colorized_path), colormap='terrain')
            
            colorize_time = time.time() - colorize_start
            
            if result and os.path.exists(result):
                file_size = os.path.getsize(result) / (1024 * 1024)  # MB
                print(f"✅ Colorized DEM created in {colorize_time:.2f}s")
                print(f"   📄 Output: {result}")
                print(f"   📊 Size: {file_size:.1f} MB")
                return result
            else:
                print(f"❌ Colorized DEM generation failed")
                return None
                
        except Exception as e:
            colorize_time = time.time() - colorize_start
            print(f"❌ Colorized DEM error after {colorize_time:.2f}s: {str(e)}")
            self.results['errors'].append(f"Colorized DEM error: {str(e)}")
            return None
    
    def organize_outputs(self, products: Dict[str, str], png_outputs: Dict[str, str], 
                        output_folder: Path) -> None:
        """Organize outputs into appropriate subdirectories"""
        print(f"\n📂 Organizing outputs into structured directories...")
        
        # Mapping of product types to subdirectories
        organization_map = {
            'hs_red': 'Hillshade',
            'hs_green': 'Hillshade',
            'hs_blue': 'Hillshade',
            'hillshade_rgb': 'HillshadeRgb',
            'tint_overlay': 'HillshadeRgb',
            'boosted_hillshade': 'HillshadeRgb',
            'slope': 'Terrain_Analysis',
            'slope_relief': 'Visualization',
            'aspect': 'Terrain_Analysis',
            'tpi': 'Terrain_Analysis',
            'color_relief': 'Visualization'
        }
        
        import shutil
        
        organized_count = 0
        
        # Organize TIFF products
        for product_name, tiff_path in products.items():
            target_dir = organization_map.get(product_name, 'Terrain_Analysis')
            target_folder = output_folder / target_dir
            target_path = target_folder / os.path.basename(tiff_path)
            
            try:
                if not target_path.exists():
                    shutil.move(tiff_path, target_path)
                    print(f"📄 Moved {product_name} TIFF to {target_dir}/")
                    organized_count += 1
            except Exception as e:
                print(f"❌ Error moving {product_name}: {str(e)}")
        
        print(f"✅ Organized {organized_count} TIFF files into structured directories")
    
    def generate_summary_report(self, tiff_file: Path, output_folder: Path, 
                               products: Dict[str, str], png_outputs: Dict[str, str]) -> None:
        """Generate a comprehensive summary report"""
        print(f"\n📋 Generating summary report...")
        
        report_path = output_folder / "processing_summary.txt"
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("RASTER GENERATION TEST SUMMARY REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Source File: {tiff_file.name}\n")
            f.write(f"Source Path: {tiff_file}\n")
            f.write(f"Processing Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Output Directory: {output_folder}\n\n")
            
            # File information
            if tiff_file.exists():
                file_size = tiff_file.stat().st_size / (1024 * 1024)
                f.write(f"Source File Size: {file_size:.1f} MB\n\n")
            
            # Products generated
            f.write("PRODUCTS GENERATED:\n")
            f.write("-" * 40 + "\n")
            for i, (product_name, tiff_path) in enumerate(products.items(), 1):
                f.write(f"{i:2d}. {product_name}\n")
                f.write(f"    TIFF: {os.path.basename(tiff_path)}\n")
                if product_name in png_outputs:
                    f.write(f"    PNG:  {os.path.basename(png_outputs[product_name])}\n")
                f.write("\n")
            
            # Timing information
            f.write("PROCESSING TIMES:\n")
            f.write("-" * 40 + "\n")
            file_prefix = tiff_file.stem
            total_time = 0
            for key, timing in self.results['timing'].items():
                if key.startswith(file_prefix):
                    product_name = key.replace(f"{file_prefix}_", "")
                    f.write(f"{product_name:20s}: {timing:6.2f} seconds\n")
                    total_time += timing
            f.write(f"{'TOTAL':20s}: {total_time:6.2f} seconds\n\n")
            
            # Errors (if any)
            file_errors = [e for e in self.results['errors'] if tiff_file.name in e]
            if file_errors:
                f.write("ERRORS ENCOUNTERED:\n")
                f.write("-" * 40 + "\n")
                for error in file_errors:
                    f.write(f"• {error}\n")
                f.write("\n")
            
            # Directory structure
            f.write("OUTPUT DIRECTORY STRUCTURE:\n")
            f.write("-" * 40 + "\n")
            for root, dirs, files in os.walk(output_folder):
                level = root.replace(str(output_folder), '').count(os.sep)
                indent = ' ' * 2 * level
                f.write(f"{indent}{os.path.basename(root)}/\n")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path) / (1024 * 1024)
                        f.write(f"{subindent}{file} ({file_size:.1f} MB)\n")
                    except:
                        f.write(f"{subindent}{file}\n")
        
        print(f"✅ Summary report saved: {report_path}")
    
    async def process_single_tiff(self, tiff_file: Path) -> bool:
        """Process a single TIFF file through the complete pipeline"""
        print(f"\n{'='*80}")
        print(f"🎯 PROCESSING: {tiff_file.name}")
        print(f"{'='*80}")
        
        overall_start = time.time()
        
        try:
            # 1. Create output structure
            output_folder = self.create_output_structure(tiff_file)
            
            # 2. Copy original TIFF for reference
            copied_tiff = self.copy_original_tiff(tiff_file, output_folder)
            
            # 3. Generate raster products (async)
            products = await self.generate_raster_products(tiff_file, output_folder)
            
            if not products:
                print(f"❌ No products generated for {tiff_file.name}")
                return False
            
            # 4. Convert to PNG
            png_outputs = self.convert_to_png(products, output_folder)
            
            # 5. Generate colorized DEM
            colorized_dem = self.generate_colorized_dem(tiff_file, output_folder)
            
            # 6. Organize outputs
            self.organize_outputs(products, png_outputs, output_folder)
            
            # 7. Generate summary report
            self.generate_summary_report(tiff_file, output_folder, products, png_outputs)
            
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
            
            print(f"\n🎉 PROCESSING COMPLETE FOR: {tiff_file.name}")
            print(f"⏱️ Total time: {overall_time:.2f} seconds")
            print(f"📊 Products generated: {len(products)} TIFF + {len(png_outputs)} PNG")
            print(f"📁 Output folder: {output_folder}")
            
            return True
            
        except Exception as e:
            overall_time = time.time() - overall_start
            error_msg = f"Overall processing failed for {tiff_file.name}: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"❌ Failed after {overall_time:.2f} seconds")
            
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
            
            return False
    
    async def run_test(self) -> None:
        """Run the complete raster generation test"""
        print("🚀 STARTING RASTER GENERATION TEST")
        print("=" * 80)
        
        test_start = time.time()
        
        # Find elevation TIFFs
        tiff_files = self.find_elevation_tiffs()
        
        if not tiff_files:
            print("❌ No elevation TIFF files found in input directory!")
            return
        
        print(f"\n🎯 Processing {len(tiff_files)} elevation TIFF files...")
        
        successful_count = 0
        failed_count = 0
        
        # Process each TIFF file
        for i, tiff_file in enumerate(tiff_files, 1):
            print(f"\n📝 Progress: {i}/{len(tiff_files)}")
            
            success = await self.process_single_tiff(tiff_file)
            
            if success:
                successful_count += 1
            else:
                failed_count += 1
        
        # Generate final summary
        test_time = time.time() - test_start
        self.generate_final_summary(test_time, successful_count, failed_count)
    
    def generate_final_summary(self, test_time: float, successful_count: int, failed_count: int) -> None:
        """Generate final test summary"""
        print(f"\n{'='*80}")
        print("🏁 RASTER GENERATION TEST COMPLETE")
        print(f"{'='*80}")
        
        # Console summary
        print(f"\n📊 FINAL SUMMARY:")
        print(f"   ⏱️ Total test time: {test_time:.2f} seconds ({test_time/60:.1f} minutes)")
        print(f"   ✅ Successful files: {successful_count}")
        print(f"   ❌ Failed files: {failed_count}")
        print(f"   📄 Total files processed: {successful_count + failed_count}")
        
        if self.results['errors']:
            print(f"\n❌ ERRORS ENCOUNTERED:")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        # Generate comprehensive test report
        test_report_path = self.output_base_dir / "test_summary_report.txt"
        
        with open(test_report_path, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("RASTER GENERATION TEST - COMPREHENSIVE SUMMARY\n") 
            f.write("=" * 100 + "\n\n")
            
            f.write(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Test Duration: {test_time:.2f} seconds ({test_time/60:.1f} minutes)\n")
            f.write(f"Input Directory: {self.input_dir}\n")
            f.write(f"Output Directory: {self.output_base_dir}\n\n")
            
            f.write("PROCESSING RESULTS:\n")
            f.write("-" * 50 + "\n")
            f.write(f"Files Processed: {len(self.results['processed_files'])}\n")
            f.write(f"Successful: {successful_count}\n")
            f.write(f"Failed: {failed_count}\n")
            f.write(f"Success Rate: {(successful_count/(successful_count+failed_count)*100):.1f}%\n\n")
            
            f.write("DETAILED FILE RESULTS:\n")
            f.write("-" * 50 + "\n")
            for file_result in self.results['processed_files']:
                f.write(f"File: {file_result['name']}\n")
                f.write(f"  Status: {'✅ SUCCESS' if file_result['success'] else '❌ FAILED'}\n")
                f.write(f"  Processing Time: {file_result['processing_time']:.2f} seconds\n")
                f.write(f"  Products Generated: {file_result['products_count']} TIFF\n")
                f.write(f"  PNG Outputs: {file_result['png_count']} PNG\n")
                if file_result['output_folder']:
                    f.write(f"  Output Folder: {file_result['output_folder']}\n")
                f.write("\n")
            
            if self.results['errors']:
                f.write("ERRORS ENCOUNTERED:\n")
                f.write("-" * 50 + "\n")
                for error in self.results['errors']:
                    f.write(f"• {error}\n")
                f.write("\n")
            
            # Performance analysis
            if self.results['timing']:
                f.write("PERFORMANCE ANALYSIS:\n")
                f.write("-" * 50 + "\n")
                
                # Calculate average times per processing type
                processing_types = {}
                for key, timing in self.results['timing'].items():
                    # Extract processing type from key (format: filename_processingtype)
                    parts = key.split('_')
                    if len(parts) >= 2:
                        processing_type = '_'.join(parts[1:])  # Join back in case of multi-part names
                        if processing_type not in processing_types:
                            processing_types[processing_type] = []
                        processing_types[processing_type].append(timing)
                
                f.write("Average Processing Times by Type:\n")
                for proc_type, times in processing_types.items():
                    avg_time = sum(times) / len(times)
                    f.write(f"  {proc_type:20s}: {avg_time:6.2f}s (avg of {len(times)} runs)\n")
        
        print(f"\n📋 Comprehensive test report saved: {test_report_path}")
        print(f"📁 All outputs available in: {self.output_base_dir}")
        
        # Show structure of output directory
        print(f"\n📂 OUTPUT DIRECTORY STRUCTURE:")
        for root, dirs, files in os.walk(self.output_base_dir):
            level = root.replace(str(self.output_base_dir), '').count(os.sep)
            indent = '  ' * level
            print(f"{indent}{os.path.basename(root)}/")
            if level < 2:  # Don't show too deep
                subindent = '  ' * (level + 1)
                for d in dirs[:5]:  # Show first 5 directories
                    print(f"{subindent}{d}/")
                if len(dirs) > 5:
                    print(f"{subindent}... and {len(dirs)-5} more")


async def main():
    """Main execution function"""
    print("🧪 RASTER GENERATION TEST SCRIPT")
    print("=" * 50)
    print("This script will:")
    print("1. 🔍 Scan input directory for elevation TIFF files")
    print("2. 🎯 Generate raster products (hillshade, slope, aspect, TPI, color relief)")
    print("3. 📁 Organize outputs in structured directories")
    print("4. 🎨 Convert TIFF outputs to PNG for visualization")
    print("5. 📋 Generate comprehensive reports")
    print()
    
    try:
        # Initialize the test generator
        print("🔧 Initializing test generator...")
        generator = RasterTestGenerator()
        print("✅ Test generator initialized")
        
        # Run the test
        print("🚀 Starting test execution...")
        await generator.run_test()
        
        print("\n🎉 TEST COMPLETE! Check the Tests/raster_outputs directory for results.")
        
    except Exception as e:
        print(f"❌ Fatal error in main: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
