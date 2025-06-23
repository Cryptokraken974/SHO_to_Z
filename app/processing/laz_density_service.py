"""
LAZ Density Processing Service
Integrates density analysis into existing LAZ processing workflows
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .density_analysis import DensityAnalyzer
from .laz_classifier import LAZClassifier

logger = logging.getLogger(__name__)

class LAZDensityService:
    """
    Service for processing density analysis on loaded LAZ files
    """
    
    def __init__(self, resolution: float = 1.0, mask_threshold: float = 2.0):
        """
        Initialize density processing service
        
        Args:
            resolution: Grid resolution for density analysis (default: 1.0m)
            mask_threshold: Threshold for binary mask generation (default: 2.0 points/cell)
        """
        self.resolution = resolution
        self.mask_threshold = mask_threshold
        self.analyzer = DensityAnalyzer(
            resolution=resolution, 
            mask_threshold=mask_threshold
        )
        self.logger = logging.getLogger(__name__)
    
    def process_loaded_laz_files(
        self, 
        search_directory: str = "input",
        output_base_dir: str = "output"
    ) -> Dict[str, Any]:
        """
        Process density analysis for all loaded LAZ files
        
        Args:
            search_directory: Directory to search for LAZ files
            output_base_dir: Base output directory
            
        Returns:
            Processing results summary
        """
        print(f"\n🔍 LAZ DENSITY SERVICE: Scanning for loaded LAZ files...")
        print(f"   Search directory: {search_directory}")
        print(f"   Output base: {output_base_dir}")
        
        try:
            # Find loaded LAZ files
            loaded_files = LAZClassifier.get_loaded_laz_files(search_directory)
            
            if not loaded_files:
                print(f"📭 No loaded LAZ files found in {search_directory}")
                return {
                    "success": True,
                    "files_processed": 0,
                    "files_found": 0,
                    "results": [],
                    "message": "No loaded LAZ files found"
                }
            
            print(f"📁 Found {len(loaded_files)} loaded LAZ files to process")
            
            # Process each loaded file
            results = []
            successful_count = 0
            
            for file_info in loaded_files:
                print(f"\n🔄 Processing: {file_info['file_name']}")
                
                result = self.process_single_laz(
                    file_info['file_path'],
                    output_base_dir,
                    file_info['region_name']
                )
                
                result['file_info'] = file_info
                results.append(result)
                
                if result['success']:
                    successful_count += 1
                    print(f"✅ Completed: {file_info['file_name']}")
                else:
                    print(f"❌ Failed: {file_info['file_name']} - {result.get('error', 'Unknown error')}")
            
            summary = {
                "success": True,
                "files_processed": len(loaded_files),
                "files_found": len(loaded_files),
                "successful_count": successful_count,
                "failed_count": len(loaded_files) - successful_count,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\n📊 DENSITY PROCESSING SUMMARY:")
            print(f"   Files found: {summary['files_found']}")
            print(f"   Successfully processed: {summary['successful_count']}")
            print(f"   Failed: {summary['failed_count']}")
            
            return summary
            
        except Exception as e:
            error_msg = f"Density service processing failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "files_processed": 0,
                "files_found": 0,
                "results": []
            }
    
    def process_single_laz(
        self, 
        laz_file_path: str, 
        output_base_dir: str, 
        region_name: str
    ) -> Dict[str, Any]:
        """
        Process density analysis for a single LAZ file
        
        Args:
            laz_file_path: Path to LAZ file
            output_base_dir: Base output directory
            region_name: Region name for organization
            
        Returns:
            Processing result
        """
        try:
            # Verify this is a loaded LAZ file
            is_loaded, reason = LAZClassifier.is_loaded_laz(laz_file_path)
            
            if not is_loaded:
                return {
                    "success": False,
                    "error": f"File not classified as loaded LAZ: {reason}",
                    "file_path": laz_file_path,
                    "region_name": region_name
                }
            
            # Create output directory for this region
            region_output_dir = Path(output_base_dir) / region_name / "lidar"
            region_output_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"   📊 Running density analysis...")
            print(f"      Resolution: {self.resolution}m")
            print(f"      Output directory: {region_output_dir}")
            
            # Run density analysis
            result = self.analyzer.generate_density_raster(
                laz_file_path=laz_file_path,
                output_dir=str(region_output_dir),
                region_name=region_name
            )
            
            if result['success']:
                print(f"   ✅ Density analysis completed")
                print(f"      TIFF: {Path(result['tiff_path']).name}")
                print(f"      PNG: {Path(result['png_path']).name}")
                
                # Add density files to region's png_outputs for gallery display
                self._copy_to_png_outputs(result, region_output_dir)
                
                # Copy mask files if generated
                if result.get('mask_results'):
                    self._copy_mask_to_gallery(result['mask_results'], region_output_dir)
            
            return result
            
        except Exception as e:
            error_msg = f"Single LAZ processing failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            self.logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "file_path": laz_file_path,
                "region_name": region_name
            }
    
    def _copy_to_png_outputs(self, density_result: Dict[str, Any], region_output_dir: Path):
        """
        Copy density PNG to png_outputs directory for gallery display
        
        Args:
            density_result: Density analysis result
            region_output_dir: Region output directory
        """
        try:
            if not density_result.get('png_path'):
                return
            
            png_outputs_dir = region_output_dir / "png_outputs"
            png_outputs_dir.mkdir(parents=True, exist_ok=True)
            
            source_png = Path(density_result['png_path'])
            if source_png.exists():
                dest_png = png_outputs_dir / f"Density.png"
                
                import shutil
                shutil.copy2(source_png, dest_png)
                print(f"   📁 Copied density PNG to gallery: {dest_png.name}")
            
        except Exception as e:
            print(f"   ⚠️ Could not copy to png_outputs: {e}")
    
    def _copy_mask_to_gallery(self, mask_results: Dict[str, Any], region_output_dir: Path):
        """
        Copy mask PNG to png_outputs directory for gallery display
        
        Args:
            mask_results: Mask generation results
            region_output_dir: Region output directory
        """
        try:
            if not mask_results.get('png_path'):
                print(f"   ⚠️ No mask PNG to copy to gallery")
                return
            
            png_outputs_dir = region_output_dir / "png_outputs"
            png_outputs_dir.mkdir(parents=True, exist_ok=True)
            
            source_png = Path(mask_results['png_path'])
            if source_png.exists():
                dest_png = png_outputs_dir / f"ValidMask.png"
                
                import shutil
                shutil.copy2(source_png, dest_png)
                print(f"   📁 Copied mask PNG to gallery: {dest_png.name}")
                
                # Also show mask statistics
                if 'statistics' in mask_results:
                    stats = mask_results['statistics']
                    coverage = stats.get('coverage_percentage', 0)
                    print(f"   📊 Mask coverage: {coverage:.1f}% valid pixels")
            else:
                print(f"   ⚠️ Mask PNG not found: {source_png}")
            
        except Exception as e:
            print(f"   ⚠️ Could not copy mask to png_outputs: {e}")
    
    def check_density_requirements(self) -> Dict[str, Any]:
        """
        Check if system requirements are met for density processing
        
        Returns:
            Requirements check results
        """
        print(f"🔧 Checking density processing requirements...")
        
        requirements = {
            "pdal_available": False,
            "gdal_available": False,
            "system_ready": False,
            "missing_tools": []
        }
        
        # Check PDAL
        try:
            import subprocess
            result = subprocess.run(['pdal', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                requirements["pdal_available"] = True
                print(f"   ✅ PDAL available: {result.stdout.strip()}")
            else:
                requirements["missing_tools"].append("pdal")
                print(f"   ❌ PDAL not available")
        except Exception as e:
            requirements["missing_tools"].append("pdal")
            print(f"   ❌ PDAL check failed: {e}")
        
        # Check GDAL
        try:
            result = subprocess.run(['gdalinfo', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                requirements["gdal_available"] = True
                print(f"   ✅ GDAL available: {result.stdout.strip()}")
            else:
                requirements["missing_tools"].append("gdal")
                print(f"   ❌ GDAL not available")
        except Exception as e:
            requirements["missing_tools"].append("gdal")
            print(f"   ❌ GDAL check failed: {e}")
        
        requirements["system_ready"] = requirements["pdal_available"] and requirements["gdal_available"]
        
        if requirements["system_ready"]:
            print(f"   🎉 System ready for density processing!")
        else:
            print(f"   ⚠️ Missing tools: {', '.join(requirements['missing_tools'])}")
        
        return requirements

    def process_loaded_laz_file(self, laz_file_path: str) -> Dict[str, Any]:
        """
        Process a single loaded LAZ file for density analysis
        
        Args:
            laz_file_path: Path to the LAZ file to process
            
        Returns:
            Dictionary with processing results
        """
        try:
            print(f"🔄 Processing single LAZ file: {laz_file_path}")
            
            # Validate file exists
            if not os.path.exists(laz_file_path):
                return {
                    "success": False,
                    "error": f"LAZ file not found: {laz_file_path}",
                    "file_path": laz_file_path
                }
            
            # Extract region name
            file_path = Path(laz_file_path)
            region_name = file_path.stem
            
            # Determine output directory
            output_dir = f"output/{region_name}/lidar"
            
            # Process the file
            result = self.process_single_laz(laz_file_path, "output", region_name)
            
            print(f"✅ Single file processing completed: {result.get('success', False)}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to process loaded LAZ file: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "file_path": laz_file_path
            }

def process_all_loaded_laz_density(resolution: float = 1.0) -> Dict[str, Any]:
    """
    Convenience function to process density for all loaded LAZ files
    
    Args:
        resolution: Grid resolution for density analysis
        
    Returns:
        Processing results
    """
    service = LAZDensityService(resolution=resolution)
    
    # Check requirements first
    requirements = service.check_density_requirements()
    if not requirements["system_ready"]:
        return {
            "success": False,
            "error": f"Missing required tools: {', '.join(requirements['missing_tools'])}",
            "requirements": requirements
        }
    
    # Process loaded LAZ files
    return service.process_loaded_laz_files()
