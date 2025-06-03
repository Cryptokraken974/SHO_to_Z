"""
NDVI (Normalized Difference Vegetation Index) calculation and processing module.

This module provides functionality to automatically calculate NDVI from Sentinel-2 
RED (B04) and NIR (B08) bands using GDAL and numpy.

NDVI Formula: (NIR - RED) / (NIR + RED)
"""

import os
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from osgeo import gdal
import logging

logger = logging.getLogger(__name__)

class NDVIProcessor:
    """NDVI calculation processor for Sentinel-2 data."""
    
    def __init__(self):
        """Initialize NDVI processor."""
        # Configure GDAL
        gdal.UseExceptions()
    
    def calculate_ndvi(self, red_band_path: str, nir_band_path: str, output_ndvi_path: str) -> bool:
        """
        Calculate NDVI from RED and NIR band GeoTIFF files.
        
        Args:
            red_band_path: Path to RED band (B04) GeoTIFF file
            nir_band_path: Path to NIR band (B08) GeoTIFF file
            output_ndvi_path: Path for output NDVI GeoTIFF file
            
        Returns:
            True if NDVI calculation was successful, False otherwise
        """
        try:
            print(f"\n🌱 NDVI CALCULATION STARTED")
            print(f"🔴 RED band: {red_band_path}")
            print(f"🌿 NIR band: {nir_band_path}")
            print(f"📊 Output NDVI: {output_ndvi_path}")
            
            # Check if input files exist
            if not os.path.exists(red_band_path):
                logger.error(f"RED band file not found: {red_band_path}")
                return False
            
            if not os.path.exists(nir_band_path):
                logger.error(f"NIR band file not found: {nir_band_path}")
                return False
            
            # Open the RED and NIR band images
            print("📖 Opening band files...")
            red_ds = gdal.Open(red_band_path)
            nir_ds = gdal.Open(nir_band_path)
            
            if red_ds is None:
                logger.error(f"Failed to open RED band file: {red_band_path}")
                return False
            
            if nir_ds is None:
                logger.error(f"Failed to open NIR band file: {nir_band_path}")
                return False
            
            # Verify dimensions match
            if (red_ds.RasterXSize != nir_ds.RasterXSize or 
                red_ds.RasterYSize != nir_ds.RasterYSize):
                logger.error("RED and NIR bands have different dimensions")
                return False
            
            print(f"📐 Image dimensions: {red_ds.RasterXSize} x {red_ds.RasterYSize}")
            
            # Read the band data as float arrays
            print("📊 Reading band data...")
            red_band = red_ds.GetRasterBand(1).ReadAsArray().astype(float)
            nir_band = nir_ds.GetRasterBand(1).ReadAsArray().astype(float)
            
            print(f"🔢 RED band stats: min={red_band.min():.2f}, max={red_band.max():.2f}, mean={red_band.mean():.2f}")
            print(f"🔢 NIR band stats: min={nir_band.min():.2f}, max={nir_band.max():.2f}, mean={nir_band.mean():.2f}")
            
            # Calculate NDVI using the formula: (NIR - RED) / (NIR + RED)
            print("🧮 Calculating NDVI...")
            with np.errstate(divide='ignore', invalid='ignore'):
                # Calculate NDVI
                ndvi = (nir_band - red_band) / (nir_band + red_band)
                
                # Handle division by zero and invalid values
                ndvi[ndvi == np.inf] = np.nan
                ndvi[ndvi == -np.inf] = np.nan
                
                # Replace NaN values with -999 (common no-data value)
                ndvi = np.nan_to_num(ndvi, nan=-999)
                
                # Clip NDVI values to valid range [-1, 1]
                ndvi = np.clip(ndvi, -1, 1)
            
            print(f"🌱 NDVI stats: min={ndvi.min():.3f}, max={ndvi.max():.3f}, mean={ndvi.mean():.3f}")
            
            # Count valid pixels (excluding no-data)
            valid_pixels = np.sum(ndvi != -999)
            total_pixels = ndvi.size
            print(f"✅ Valid pixels: {valid_pixels:,} / {total_pixels:,} ({100*valid_pixels/total_pixels:.1f}%)")
            
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_ndvi_path), exist_ok=True)
            
            # Create the output NDVI image
            print("💾 Creating output NDVI file...")
            driver = gdal.GetDriverByName('GTiff')
            out_ds = driver.Create(
                output_ndvi_path, 
                red_ds.RasterXSize, 
                red_ds.RasterYSize, 
                1, 
                gdal.GDT_Float32
            )
            
            # Copy geospatial information from input
            out_ds.SetGeoTransform(red_ds.GetGeoTransform())
            out_ds.SetProjection(red_ds.GetProjectionRef())
            
            # Write the NDVI data
            out_band = out_ds.GetRasterBand(1)
            out_band.WriteArray(ndvi)
            out_band.SetNoDataValue(-999)
            
            # Set band description
            out_band.SetDescription("NDVI (Normalized Difference Vegetation Index)")
            
            # Clean up
            red_ds = None
            nir_ds = None
            out_ds = None
            
            # Verify output file was created
            if os.path.exists(output_ndvi_path):
                file_size_mb = os.path.getsize(output_ndvi_path) / (1024 * 1024)
                print(f"✅ NDVI calculation completed successfully!")
                print(f"📁 Output file: {output_ndvi_path}")
                print(f"📊 File size: {file_size_mb:.2f} MB")
                return True
            else:
                logger.error("NDVI output file was not created")
                return False
                
        except Exception as e:
            logger.error(f"Error calculating NDVI: {e}")
            print(f"❌ NDVI calculation failed: {e}")
            return False
    
    def find_sentinel2_bands(self, data_dir: str, region_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Find RED and NIR band files in the Sentinel-2 data directory.
        
        Args:
            data_dir: Base data directory (e.g., "output/3.10S_57.70W")
            region_name: Region name for file matching
            
        Returns:
            Tuple of (red_band_path, nir_band_path) or (None, None) if not found
        """
        try:
            # Look for Sentinel-2 files in the sentinel2 subfolder
            sentinel2_dir = Path(data_dir) / "sentinel2"
            
            if not sentinel2_dir.exists():
                print(f"📂 Sentinel-2 directory not found: {sentinel2_dir}")
                return None, None
            
            # Pattern: {region}_{timestamp}_sentinel2_RED_B04.tif and {region}_{timestamp}_sentinel2_NIR_B08.tif
            red_files = list(sentinel2_dir.glob(f"*_sentinel2_RED_B04.tif"))
            nir_files = list(sentinel2_dir.glob(f"*_sentinel2_NIR_B08.tif"))
            
            print(f"🔍 Found RED band files: {[f.name for f in red_files]}")
            print(f"🔍 Found NIR band files: {[f.name for f in nir_files]}")
            
            if not red_files:
                print("❌ No RED band (B04) files found")
                return None, None
            
            if not nir_files:
                print("❌ No NIR band (B08) files found") 
                return None, None
            
            # Use the most recent files (sort by modification time)
            red_file = sorted(red_files, key=lambda x: x.stat().st_mtime)[-1]
            nir_file = sorted(nir_files, key=lambda x: x.stat().st_mtime)[-1]
            
            print(f"✅ Selected RED band: {red_file.name}")
            print(f"✅ Selected NIR band: {nir_file.name}")
            
            return str(red_file), str(nir_file)
            
        except Exception as e:
            logger.error(f"Error finding Sentinel-2 bands: {e}")
            print(f"❌ Error finding Sentinel-2 bands: {e}")
            return None, None
    
    def process_region_ndvi(self, region_name: str, base_output_dir: str = "output") -> Optional[Dict]:
        """
        Process NDVI for a specific region automatically.
        
        Args:
            region_name: Region name (e.g., "3.10S_57.70W")
            base_output_dir: Base output directory
            
        Returns:
            Dictionary with processing results or None if failed
        """
        try:
            print(f"\n🌱 PROCESSING NDVI FOR REGION: {region_name}")
            
            # Construct data directory path
            data_dir = os.path.join(base_output_dir, region_name)
            
            if not os.path.exists(data_dir):
                print(f"❌ Region data directory not found: {data_dir}")
                return None
            
            # Find RED and NIR band files
            red_path, nir_path = self.find_sentinel2_bands(data_dir, region_name)
            
            if not red_path or not nir_path:
                print("❌ Required Sentinel-2 bands not found for NDVI calculation")
                return None
            
            # Generate NDVI output filename
            sentinel2_dir = Path(data_dir) / "sentinel2"
            
            # Extract timestamp from one of the band files
            red_filename = Path(red_path).name
            # Pattern: {region}_{timestamp}_sentinel2_RED_B04.tif
            parts = red_filename.split('_')
            if len(parts) >= 2:
                timestamp = parts[1]  # Extract timestamp
            else:
                timestamp = "unknown"
            
            ndvi_filename = f"{region_name}_{timestamp}_sentinel2_NDVI.tif"
            ndvi_output_path = sentinel2_dir / ndvi_filename
            
            # Calculate NDVI
            success = self.calculate_ndvi(red_path, nir_path, str(ndvi_output_path))
            
            if success:
                return {
                    "success": True,
                    "region_name": region_name,
                    "red_band_path": red_path,
                    "nir_band_path": nir_path,
                    "ndvi_path": str(ndvi_output_path),
                    "timestamp": timestamp
                }
            else:
                return {
                    "success": False,
                    "error": "NDVI calculation failed"
                }
                
        except Exception as e:
            logger.error(f"Error processing NDVI for region {region_name}: {e}")
            print(f"❌ Error processing NDVI for region {region_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

def process_ndvi_for_region(region_name: str, base_output_dir: str = "output") -> Optional[Dict]:
    """
    Convenience function to process NDVI for a region.
    
    Args:
        region_name: Region name (e.g., "3.10S_57.70W")
        base_output_dir: Base output directory
        
    Returns:
        Dictionary with processing results or None if failed
    """
    processor = NDVIProcessor()
    return processor.process_region_ndvi(region_name, base_output_dir)

def find_regions_with_sentinel2_data(base_output_dir: str = "output") -> List[str]:
    """
    Find all regions that have Sentinel-2 data available for NDVI processing.
    
    Args:
        base_output_dir: Base output directory
        
    Returns:
        List of region names that have both RED and NIR bands
    """
    try:
        regions_with_data = []
        output_path = Path(base_output_dir)
        
        if not output_path.exists():
            print(f"📂 Output directory not found: {base_output_dir}")
            return []
        
        # Scan all region directories
        for region_dir in output_path.iterdir():
            if region_dir.is_dir():
                region_name = region_dir.name
                sentinel2_dir = region_dir / "sentinel2"
                
                if sentinel2_dir.exists():
                    # Check for RED and NIR bands
                    red_files = list(sentinel2_dir.glob("*_sentinel2_RED_B04.tif"))
                    nir_files = list(sentinel2_dir.glob("*_sentinel2_NIR_B08.tif"))
                    
                    if red_files and nir_files:
                        regions_with_data.append(region_name)
                        print(f"✅ Region {region_name}: Ready for NDVI processing")
                    else:
                        print(f"⚠️ Region {region_name}: Missing required bands")
        
        print(f"\n📊 Found {len(regions_with_data)} regions ready for NDVI processing")
        return regions_with_data
        
    except Exception as e:
        logger.error(f"Error scanning for Sentinel-2 data: {e}")
        return []
