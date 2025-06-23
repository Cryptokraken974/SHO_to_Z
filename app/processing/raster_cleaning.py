"""
Raster Cleaning Service
Applies binary masks to clean up raster outputs by removing artifacts and edge bands
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import subprocess
import tempfile

try:
    import rasterio
    import numpy as np
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

logger = logging.getLogger(__name__)

class RasterCleaner:
    """
    Modular service for cleaning raster outputs using binary masks
    Removes interpolated artifacts and edge bands from LAZ-derived rasters
    """
    
    def __init__(self, method: str = "auto", nodata_value: float = 0):
        """
        Initialize raster cleaner
        
        Args:
            method: Cleaning method - "gdal", "python", or "auto" (default: "auto")
            nodata_value: NoData value for cleaned rasters (default: 0)
        """
        self.method = method
        self.nodata_value = nodata_value
        self.logger = logging.getLogger(__name__)
        
        # Auto-select method based on availability
        if self.method == "auto":
            self.method = "python" if RASTERIO_AVAILABLE else "gdal"
    
    def clean_raster_with_mask(
        self, 
        raster_path: str, 
        mask_path: str, 
        output_path: str,
        method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clean a single raster using binary mask
        
        Args:
            raster_path: Path to input raster file
            mask_path: Path to binary mask file
            output_path: Path for cleaned output raster
            method: Override cleaning method for this operation
            
        Returns:
            Dictionary with cleaning results
        """
        try:
            print(f"\n🧹 RASTER CLEANING: {Path(raster_path).name}")
            print(f"   Input raster: {raster_path}")
            print(f"   Mask: {Path(mask_path).name}")
            print(f"   Output: {output_path}")
            
            # Validate inputs
            if not os.path.exists(raster_path):
                raise FileNotFoundError(f"Raster file not found: {raster_path}")
            if not os.path.exists(mask_path):
                raise FileNotFoundError(f"Mask file not found: {mask_path}")
            
            # Create output directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Choose cleaning method
            clean_method = method or self.method
            
            if clean_method == "python" and RASTERIO_AVAILABLE:
                result = self._clean_with_python(raster_path, mask_path, output_path)
            else:
                result = self._clean_with_gdal(raster_path, mask_path, output_path)
            
            if result["success"]:
                # Calculate file sizes
                input_size = os.path.getsize(raster_path) / (1024 * 1024)
                output_size = os.path.getsize(output_path) / (1024 * 1024)
                
                print(f"✅ Raster cleaning completed")
                print(f"   Input size: {input_size:.2f} MB")
                print(f"   Output size: {output_size:.2f} MB")
                print(f"   Method used: {clean_method}")
                
                result.update({
                    "input_size_mb": round(input_size, 2),
                    "output_size_mb": round(output_size, 2),
                    "method_used": clean_method
                })
            
            return result
            
        except Exception as e:
            error_msg = f"Raster cleaning failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "input_raster": raster_path,
                "output_raster": output_path
            }
    
    def clean_region_rasters(
        self, 
        region_dir: str, 
        mask_path: str,
        raster_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Clean all rasters in a region using the provided mask
        
        Args:
            region_dir: Path to region directory (e.g., output/PRGL1260C9597_2014/lidar)
            mask_path: Path to binary mask file
            raster_types: List of raster types to clean (None = all supported types)
            
        Returns:
            Dictionary with batch cleaning results
        """
        try:
            print(f"\n🏢 REGION RASTER CLEANING: {Path(region_dir).name}")
            print(f"   Region directory: {region_dir}")
            print(f"   Mask: {Path(mask_path).name}")
            
            # Default raster types to clean
            if raster_types is None:
                raster_types = [
                    "DTM", "DSM", "CHM", "Hillshade", "HillshadeRGB", 
                    "Slope", "Aspect", "TRI", "TPI", "Roughness", 
                    "LRM", "SVF", "TintOverlay"
                ]
            
            print(f"   Target raster types: {', '.join(raster_types)}")
            
            # Find rasters to clean
            rasters_to_clean = self._find_rasters_in_region(region_dir, raster_types)
            
            if not rasters_to_clean:
                return {
                    "success": True,
                    "message": "No rasters found to clean",
                    "files_processed": 0,
                    "results": []
                }
            
            print(f"   Found {len(rasters_to_clean)} rasters to clean")
            
            # Create cleaned output directory
            cleaned_dir = Path(region_dir) / "cleaned"
            cleaned_dir.mkdir(parents=True, exist_ok=True)
            
            # Clean each raster
            results = []
            successful_count = 0
            
            for raster_info in rasters_to_clean:
                raster_path = raster_info["path"]
                raster_name = raster_info["name"]
                raster_type = raster_info["type"]
                
                # Generate output path
                cleaned_filename = f"{raster_name}_cleaned.tif"
                output_path = cleaned_dir / cleaned_filename
                
                print(f"\n   Processing: {raster_name} ({raster_type})")
                
                # Clean the raster
                result = self.clean_raster_with_mask(
                    raster_path=raster_path,
                    mask_path=mask_path,
                    output_path=str(output_path)
                )
                
                result.update({
                    "raster_name": raster_name,
                    "raster_type": raster_type,
                    "original_path": raster_path
                })
                
                results.append(result)
                
                if result["success"]:
                    successful_count += 1
                    
                    # Copy cleaned raster to png_outputs if it's a visualization type
                    if raster_type in ["HillshadeRGB", "TintOverlay", "DTM", "DSM"]:
                        self._update_png_gallery(result, region_dir)
            
            summary = {
                "success": True,
                "files_processed": len(rasters_to_clean),
                "successful_count": successful_count,
                "failed_count": len(rasters_to_clean) - successful_count,
                "cleaned_directory": str(cleaned_dir),
                "results": results
            }
            
            print(f"\n📊 REGION CLEANING SUMMARY:")
            print(f"   Files processed: {summary['files_processed']}")
            print(f"   Successfully cleaned: {summary['successful_count']}")
            print(f"   Failed: {summary['failed_count']}")
            print(f"   Cleaned files directory: {cleaned_dir}")
            
            return summary
            
        except Exception as e:
            error_msg = f"Region raster cleaning failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "files_processed": 0,
                "results": []
            }
    
    def _clean_with_python(
        self, 
        raster_path: str, 
        mask_path: str, 
        output_path: str
    ) -> Dict[str, Any]:
        """
        Clean raster using Python/rasterio (preferred method)
        
        Args:
            raster_path: Path to input raster
            mask_path: Path to binary mask
            output_path: Path for output raster
            
        Returns:
            Cleaning result dictionary
        """
        try:
            print(f"   🐍 Using Python/rasterio for cleaning...")
            
            # Open mask and raster
            with rasterio.open(mask_path) as mask_src, rasterio.open(raster_path) as raster_src:
                # Read data
                mask_data = mask_src.read(1)
                raster_data = raster_src.read()
                
                print(f"   📊 Raster shape: {raster_data.shape}")
                print(f"   📊 Mask shape: {mask_data.shape}")
                
                # Ensure mask and raster have compatible dimensions
                if raster_data.shape[1:] != mask_data.shape:
                    raise ValueError(f"Dimension mismatch: raster {raster_data.shape[1:]} vs mask {mask_data.shape}")
                
                # Apply mask to each band
                cleaned_data = np.zeros_like(raster_data, dtype=raster_data.dtype)
                valid_pixels_total = 0
                
                for band_idx in range(raster_data.shape[0]):
                    band_data = raster_data[band_idx]
                    
                    # Apply mask: multiply by mask (0 or 1)
                    cleaned_band = band_data * mask_data
                    
                    # Set invalid areas to nodata value
                    cleaned_band = np.where(mask_data > 0, cleaned_band, self.nodata_value)
                    
                    cleaned_data[band_idx] = cleaned_band
                    
                    # Count valid pixels in this band
                    valid_pixels_total += np.sum(mask_data > 0)
                
                # Update profile for output
                profile = raster_src.profile.copy()
                profile.update({
                    'nodata': self.nodata_value,
                    'compress': 'lzw'
                })
                
                # Write cleaned raster
                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(cleaned_data)
                
                # Calculate statistics
                total_pixels = mask_data.size * raster_data.shape[0]
                coverage_percentage = (valid_pixels_total / total_pixels) * 100 if total_pixels > 0 else 0
                
                print(f"   📈 Coverage after cleaning: {coverage_percentage:.1f}%")
                
                return {
                    "success": True,
                    "method": "python",
                    "input_raster": raster_path,
                    "output_raster": output_path,
                    "bands_processed": raster_data.shape[0],
                    "coverage_percentage": round(coverage_percentage, 2)
                }
                
        except Exception as e:
            raise RuntimeError(f"Python cleaning failed: {str(e)}")
    
    def _clean_with_gdal(
        self, 
        raster_path: str, 
        mask_path: str, 
        output_path: str
    ) -> Dict[str, Any]:
        """
        Clean raster using GDAL (fallback method)
        
        Args:
            raster_path: Path to input raster
            mask_path: Path to binary mask
            output_path: Path for output raster
            
        Returns:
            Cleaning result dictionary
        """
        try:
            print(f"   🔧 Using GDAL for cleaning...")
            
            # Use gdal_calc.py to apply mask
            cmd = [
                'gdal_calc.py',
                '-A', raster_path,
                '-B', mask_path,
                '--outfile', output_path,
                '--calc', 'A*(B>0)',
                '--NoDataValue', str(self.nodata_value),
                '--type', 'Float32',
                '--co', 'COMPRESS=LZW'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise RuntimeError(f"gdal_calc.py failed: {result.stderr}")
            
            print(f"   ✅ GDAL cleaning completed")
            
            return {
                "success": True,
                "method": "gdal",
                "input_raster": raster_path,
                "output_raster": output_path,
                "gdal_stdout": result.stdout,
                "gdal_stderr": result.stderr
            }
            
        except Exception as e:
            raise RuntimeError(f"GDAL cleaning failed: {str(e)}")
    
    def _find_rasters_in_region(
        self, 
        region_dir: str, 
        raster_types: List[str]
    ) -> List[Dict[str, str]]:
        """
        Find rasters in region directory that match the specified types
        
        Args:
            region_dir: Path to region directory
            raster_types: List of raster types to find
            
        Returns:
            List of raster info dictionaries
        """
        rasters_found = []
        region_path = Path(region_dir)
        
        # Search patterns for different raster organizations
        search_patterns = [
            # Pattern 1: Individual folders (DTM/file.tif, DSM/file.tif)
            {
                "pattern": lambda rtype: list(region_path.glob(f"{rtype}/*.tif")),
                "extract_info": lambda path, rtype: {
                    "path": str(path),
                    "name": path.stem,
                    "type": rtype,
                    "source": "individual_folder"
                }
            },
            # Pattern 2: Consolidated png_outputs (look for TIFF equivalents)
            {
                "pattern": lambda rtype: list(region_path.glob(f"*/{rtype}.tif")) + list(region_path.glob(f"**/{rtype}.tif")),
                "extract_info": lambda path, rtype: {
                    "path": str(path),
                    "name": path.stem,
                    "type": rtype,
                    "source": "consolidated"
                }
            },
            # Pattern 3: Search by filename patterns
            {
                "pattern": lambda rtype: list(region_path.glob(f"**/*{rtype}*.tif")),
                "extract_info": lambda path, rtype: {
                    "path": str(path),
                    "name": path.stem,
                    "type": rtype,
                    "source": "pattern_match"
                }
            }
        ]
        
        for raster_type in raster_types:
            found_for_type = False
            
            for pattern_config in search_patterns:
                matching_files = pattern_config["pattern"](raster_type)
                
                for file_path in matching_files:
                    # Skip already processed cleaned files
                    if "cleaned" in str(file_path):
                        continue
                    
                    raster_info = pattern_config["extract_info"](file_path, raster_type)
                    
                    # Avoid duplicates
                    if not any(r["path"] == raster_info["path"] for r in rasters_found):
                        rasters_found.append(raster_info)
                        found_for_type = True
                
                # If we found files for this type, don't try other patterns
                if found_for_type:
                    break
        
        return rasters_found
    
    def _update_png_gallery(self, clean_result: Dict[str, Any], region_dir: str):
        """
        Update PNG gallery with cleaned raster if applicable
        
        Args:
            clean_result: Result from cleaning operation
            region_dir: Region directory path
        """
        try:
            if not clean_result.get("success"):
                return
            
            # Generate PNG from cleaned TIFF for gallery
            cleaned_tiff = clean_result["output_raster"]
            raster_type = clean_result["raster_type"]
            
            # PNG output directory
            png_outputs_dir = Path(region_dir) / "png_outputs"
            png_outputs_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate PNG filename
            png_filename = f"{raster_type}_Cleaned.png"
            png_output_path = png_outputs_dir / png_filename
            
            # Convert TIFF to PNG using GDAL
            cmd = [
                'gdal_translate',
                '-of', 'PNG',
                '-scale',
                cleaned_tiff,
                str(png_output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"   📁 Updated gallery: {png_filename}")
            else:
                print(f"   ⚠️ PNG gallery update failed: {result.stderr}")
                
        except Exception as e:
            print(f"   ⚠️ Gallery update failed: {e}")

def clean_rasters_with_mask(
    region_dir: str,
    mask_path: str,
    raster_types: Optional[List[str]] = None,
    method: str = "auto"
) -> Dict[str, Any]:
    """
    Convenience function for cleaning region rasters with mask
    
    Args:
        region_dir: Path to region directory
        mask_path: Path to binary mask file
        raster_types: List of raster types to clean (None = all)
        method: Cleaning method ("auto", "python", "gdal")
        
    Returns:
        Cleaning results dictionary
    """
    cleaner = RasterCleaner(method=method)
    return cleaner.clean_region_rasters(region_dir, mask_path, raster_types)
