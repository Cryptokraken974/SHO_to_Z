#!/usr/bin/env python3
"""
Large Image Overlay Optimization Module

This module provides functionality to automatically detect large images during raster
generation and create browser-friendly overlay versions with "_overlays" suffix.
Integrates with the frontend optimization system that uses 25M pixel thresholds.
"""

import os
import time
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from PIL import Image, ImageOps
import numpy as np
from osgeo import gdal

class OverlayOptimizer:
    """Handles automatic generation of browser-friendly overlay versions"""
    
    # Frontend compatibility thresholds (matching overlays_fixed.js)
    COMPRESSION_THRESHOLD = 25_000_000  # 25M pixels - triggers optimization
    AGGRESSIVE_THRESHOLD = 75_000_000   # 75M pixels - more aggressive optimization  
    EXTREME_THRESHOLD = 100_000_000     # 100M pixels - super aggressive optimization
    
    # Target dimensions for different optimization levels
    STANDARD_MAX_DIM = 4096     # Standard optimization
    AGGRESSIVE_MAX_DIM = 2048   # Aggressive optimization  
    EXTREME_MAX_DIM = 1024      # Extreme optimization
    
    def __init__(self):
        self.results = {
            'optimized_files': [],
            'skipped_files': [],
            'errors': []
        }
    
    def should_optimize_image(self, tiff_path: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if image requires optimization based on pixel count
        
        Args:
            tiff_path: Path to TIFF file
            
        Returns:
            Tuple of (should_optimize, analysis_info)
        """
        try:
            # Open TIFF with GDAL to get dimensions
            ds = gdal.Open(tiff_path)
            if ds is None:
                return False, {'error': f'Cannot open TIFF: {tiff_path}'}
            
            width = ds.RasterXSize
            height = ds.RasterYSize
            pixel_count = width * height
            
            # Calculate file size for reference
            file_size_mb = os.path.getsize(tiff_path) / (1024 * 1024)
            
            analysis = {
                'width': width,
                'height': height,
                'pixel_count': pixel_count,
                'file_size_mb': file_size_mb,
                'pixel_count_millions': pixel_count / 1_000_000
            }
            
            # Determine optimization level needed
            if pixel_count >= self.EXTREME_THRESHOLD:
                analysis['optimization_level'] = 'extreme'
                analysis['target_max_dim'] = self.EXTREME_MAX_DIM
                should_optimize = True
            elif pixel_count >= self.AGGRESSIVE_THRESHOLD:
                analysis['optimization_level'] = 'aggressive' 
                analysis['target_max_dim'] = self.AGGRESSIVE_MAX_DIM
                should_optimize = True
            elif pixel_count >= self.COMPRESSION_THRESHOLD:
                analysis['optimization_level'] = 'standard'
                analysis['target_max_dim'] = self.STANDARD_MAX_DIM
                should_optimize = True
            else:
                analysis['optimization_level'] = 'none'
                analysis['target_max_dim'] = max(width, height)
                should_optimize = False
            
            analysis['should_optimize'] = should_optimize
            
            print(f"📊 Image analysis for {os.path.basename(tiff_path)}:")
            print(f"   Dimensions: {width}x{height} ({pixel_count:,} pixels = {analysis['pixel_count_millions']:.1f}M)")
            print(f"   File size: {file_size_mb:.2f}MB")
            print(f"   Optimization: {'✅ ' + analysis['optimization_level'] if should_optimize else '❌ not needed'}")
            
            ds = None  # Close dataset
            return should_optimize, analysis
            
        except Exception as e:
            error_msg = f"Error analyzing {tiff_path}: {str(e)}"
            print(f"❌ {error_msg}")
            return False, {'error': error_msg}
    
    def calculate_optimal_dimensions(self, width: int, height: int, optimization_level: str) -> Tuple[int, int]:
        """
        Calculate optimal dimensions based on optimization level
        
        Args:
            width: Original width
            height: Original height  
            optimization_level: 'standard', 'aggressive', or 'extreme'
            
        Returns:
            Tuple of (target_width, target_height)
        """
        # Get target maximum dimension
        if optimization_level == 'extreme':
            max_dim = self.EXTREME_MAX_DIM
        elif optimization_level == 'aggressive':
            max_dim = self.AGGRESSIVE_MAX_DIM
        else:
            max_dim = self.STANDARD_MAX_DIM
        
        # If already within limits, no resize needed
        if max(width, height) <= max_dim:
            return width, height
        
        # Calculate scale factor to fit within max dimension
        scale_factor = max_dim / max(width, height)
        
        # Calculate new dimensions maintaining aspect ratio
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        # Ensure minimum dimensions
        new_width = max(new_width, 256)
        new_height = max(new_height, 256)
        
        print(f"   Scaling: {width}x{height} → {new_width}x{new_height} (factor: {scale_factor:.3f})")
        
        return new_width, new_height
    
    def generate_overlay_png(self, tiff_path: str, target_width: int, target_height: int) -> Optional[str]:
        """
        Generate optimized PNG overlay from TIFF
        
        Args:
            tiff_path: Source TIFF path
            target_width: Target width for optimization
            target_height: Target height for optimization
            
        Returns:
            Path to generated overlay PNG or None if failed
        """
        try:
            # Generate overlay filename with "_overlays" suffix
            tiff_dir = os.path.dirname(tiff_path)
            tiff_basename = os.path.splitext(os.path.basename(tiff_path))[0]
            overlay_filename = f"{tiff_basename}_overlays.png"
            overlay_path = os.path.join(tiff_dir, overlay_filename)
            
            print(f"🔄 Generating overlay: {overlay_filename}")
            start_time = time.time()
            
            # Open TIFF with GDAL
            ds = gdal.Open(tiff_path)
            if ds is None:
                raise Exception(f"Cannot open TIFF: {tiff_path}")
            
            # Get band statistics for proper scaling
            band = ds.GetRasterBand(1)
            band.ComputeStatistics(False)
            min_val, max_val, mean_val, std_val = band.GetStatistics(True, True)
            
            print(f"   Data range: {min_val:.0f} to {max_val:.0f}")
            
            # Use GDAL to create optimized PNG with scaling and resizing
            translate_options = [
                "-of", "PNG",
                "-ot", "Byte",
                "-scale", str(min_val), str(max_val), "0", "255",
                "-outsize", str(target_width), str(target_height),
                "-r", "cubic",  # High-quality resampling
                "-co", "WORLDFILE=YES"
            ]
            
            # Perform translation
            result = gdal.Translate(overlay_path, ds, format="PNG", options=translate_options)
            
            if result is not None and os.path.exists(overlay_path):
                # Get file sizes for comparison
                original_size_mb = os.path.getsize(tiff_path) / (1024 * 1024)
                overlay_size_mb = os.path.getsize(overlay_path) / (1024 * 1024)
                compression_ratio = (1 - overlay_size_mb / original_size_mb) * 100
                processing_time = time.time() - start_time
                
                print(f"   ✅ Overlay generated in {processing_time:.2f}s")
                print(f"   Size: {original_size_mb:.2f}MB → {overlay_size_mb:.2f}MB ({compression_ratio:.1f}% reduction)")
                
                # Copy worldfile with proper naming
                original_worldfile = os.path.splitext(tiff_path)[0] + ".wld"
                overlay_worldfile = os.path.splitext(overlay_path)[0] + ".pgw"
                
                if os.path.exists(original_worldfile):
                    import shutil
                    shutil.copy2(original_worldfile, overlay_worldfile)
                    print(f"   🌍 Worldfile copied: {os.path.basename(overlay_worldfile)}")
                
                ds = None  # Close dataset
                return overlay_path
            else:
                ds = None
                raise Exception("GDAL translation failed")
                
        except Exception as e:
            error_msg = f"Failed to generate overlay for {os.path.basename(tiff_path)}: {str(e)}"
            print(f"❌ {error_msg}")
            self.results['errors'].append(error_msg)
            return None
    
    def process_png_for_overlay_optimization(self, png_path: str) -> Optional[str]:
        """
        Process an existing PNG file to create an optimized overlay version
        
        Args:
            png_path: Path to existing PNG file
            
        Returns:
            Path to optimized overlay PNG or None if not needed/failed
        """
        try:
            # Check if PNG needs optimization
            with Image.open(png_path) as img:
                width, height = img.size
                pixel_count = width * height
                
                if pixel_count < self.COMPRESSION_THRESHOLD:
                    print(f"📊 PNG {os.path.basename(png_path)}: {width}x{height} ({pixel_count:,} pixels) - no optimization needed")
                    return None
                
                # Determine optimization level
                if pixel_count >= self.EXTREME_THRESHOLD:
                    optimization_level = 'extreme'
                    max_dim = self.EXTREME_MAX_DIM
                elif pixel_count >= self.AGGRESSIVE_THRESHOLD:
                    optimization_level = 'aggressive'
                    max_dim = self.AGGRESSIVE_MAX_DIM
                else:
                    optimization_level = 'standard'
                    max_dim = self.STANDARD_MAX_DIM
                
                print(f"📊 PNG {os.path.basename(png_path)}: {width}x{height} ({pixel_count / 1_000_000:.1f}M pixels) - {optimization_level} optimization needed")
                
                # Calculate target dimensions
                target_width, target_height = self.calculate_optimal_dimensions(width, height, optimization_level)
                
                # If no resize needed, skip
                if target_width == width and target_height == height:
                    return None
                
                # Generate overlay filename
                png_dir = os.path.dirname(png_path)
                png_basename = os.path.splitext(os.path.basename(png_path))[0]
                overlay_filename = f"{png_basename}_overlays.png"
                overlay_path = os.path.join(png_dir, overlay_filename)
                
                print(f"🔄 Optimizing PNG: {overlay_filename}")
                start_time = time.time()
                
                # Resize image with high-quality resampling
                resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Save optimized version
                resized_img.save(overlay_path, 'PNG', optimize=True)
                
                # Get file sizes for comparison
                original_size_mb = os.path.getsize(png_path) / (1024 * 1024)
                overlay_size_mb = os.path.getsize(overlay_path) / (1024 * 1024)
                compression_ratio = (1 - overlay_size_mb / original_size_mb) * 100
                processing_time = time.time() - start_time
                
                print(f"   ✅ PNG overlay generated in {processing_time:.2f}s")
                print(f"   Size: {original_size_mb:.2f}MB → {overlay_size_mb:.2f}MB ({compression_ratio:.1f}% reduction)")
                
                # Copy worldfile if it exists
                original_worldfile = os.path.splitext(png_path)[0] + ".pgw"
                overlay_worldfile = os.path.splitext(overlay_path)[0] + ".pgw"
                
                if os.path.exists(original_worldfile):
                    import shutil
                    shutil.copy2(original_worldfile, overlay_worldfile)
                    print(f"   🌍 Worldfile copied: {os.path.basename(overlay_worldfile)}")
                
                self.results['optimized_files'].append({
                    'original': png_path,
                    'overlay': overlay_path,
                    'original_size_mb': original_size_mb,
                    'overlay_size_mb': overlay_size_mb,
                    'compression_ratio': compression_ratio,
                    'processing_time': processing_time
                })
                
                return overlay_path
                
        except Exception as e:
            error_msg = f"Failed to optimize PNG {os.path.basename(png_path)}: {str(e)}"
            print(f"❌ {error_msg}")
            self.results['errors'].append(error_msg)
            return None
    
    def optimize_tiff_to_overlay(self, tiff_path: str) -> Optional[str]:
        """
        Main function to check and optimize a TIFF file to overlay PNG
        
        Args:
            tiff_path: Path to TIFF file
            
        Returns:
            Path to generated overlay PNG or None if not needed/failed
        """
        should_optimize, analysis = self.should_optimize_image(tiff_path)
        
        if not should_optimize:
            self.results['skipped_files'].append({
                'file': tiff_path,
                'reason': f"Below threshold ({analysis.get('pixel_count_millions', 0):.1f}M < 25M pixels)"
            })
            return None
        
        # Generate optimized overlay
        target_width, target_height = self.calculate_optimal_dimensions(
            analysis['width'], 
            analysis['height'], 
            analysis['optimization_level']
        )
        
        overlay_path = self.generate_overlay_png(tiff_path, target_width, target_height)
        
        if overlay_path:
            self.results['optimized_files'].append({
                'original': tiff_path,
                'overlay': overlay_path,
                'analysis': analysis
            })
        
        return overlay_path
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization results"""
        return {
            'optimized_count': len(self.results['optimized_files']),
            'skipped_count': len(self.results['skipped_files']),
            'error_count': len(self.results['errors']),
            'optimized_files': self.results['optimized_files'],
            'skipped_files': self.results['skipped_files'],
            'errors': self.results['errors']
        }
