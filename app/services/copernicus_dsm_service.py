"""
Copernicus DSM (Digital Surface Model) Service

This service provides functionality to download DSM data from Copernicus DEM 
for coordinate-based regions using multiple access methods.
"""

import os
import json
import requests
import rasterio
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, List
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.merge import merge
import tempfile
import logging

logger = logging.getLogger(__name__)

class CopernicusDSMService:
    """Service for downloading and processing Copernicus DSM data"""
    
    def __init__(self):
        self.stac_endpoints = {
            "glo30": "https://copernicus-dem-30m-stac.s3.amazonaws.com/",
            "glo90": "https://copernicus-dem-90m-stac.s3.amazonaws.com/"
        }
        
        # AWS S3 buckets (no authentication required)
        self.s3_buckets = {
            "glo30": "copernicus-dem-30m",
            "glo90": "copernicus-dem-90m"
        }
        
        # Planetary Computer STAC API
        self.planetary_computer_endpoint = "https://planetarycomputer.microsoft.com/api/stac/v1"
    
    async def get_dsm_for_region(self, 
                                lat: float, 
                                lng: float, 
                                region_name: str,
                                buffer_km: float = 5.0,
                                resolution: str = "30m") -> Dict:
        """
        Download DSM data for a region defined by coordinates
        
        Args:
            lat: Latitude of the center point
            lng: Longitude of the center point
            region_name: Name of the region for file naming
            buffer_km: Buffer distance in kilometers around the center point
            resolution: Resolution ("30m" or "90m")
            
        Returns:
            Dictionary with download results and file paths
        """
        try:
            logger.info(f"Starting DSM download for region {region_name} at ({lat}, {lng})")
            
            # Calculate bounding box
            bbox = self._calculate_bbox_from_center(lat, lng, buffer_km)
            logger.info(f"Calculated bounding box: {bbox}")
            
            # Create output directory to match existing LAZ processing structure
            output_dir = Path("output") / region_name / "lidar" / "DSM"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Try different download methods in order of preference
            result = None
            
            # Method 1: Try Planetary Computer STAC API (recommended)
            try:
                result = await self._download_via_planetary_computer(bbox, output_dir, region_name, resolution)
                if result and result.get("success"):
                    logger.info("Successfully downloaded DSM via Planetary Computer")
                    return result
            except Exception as e:
                logger.warning(f"Planetary Computer method failed: {e}")
            
            # Method 2: Try direct STAC API access
            try:
                result = await self._download_via_stac_api(bbox, output_dir, region_name, resolution)
                if result and result.get("success"):
                    logger.info("Successfully downloaded DSM via STAC API")
                    return result
            except Exception as e:
                logger.warning(f"STAC API method failed: {e}")
            
            # Method 3: Try direct AWS S3 access (fallback)
            try:
                result = await self._download_via_s3_direct(bbox, output_dir, region_name, resolution)
                if result and result.get("success"):
                    logger.info("Successfully downloaded DSM via direct S3 access")
                    return result
            except Exception as e:
                logger.warning(f"Direct S3 method failed: {e}")
            
            # If all methods failed
            return {
                "success": False,
                "error": "All download methods failed",
                "region_name": region_name,
                "bbox": bbox
            }
            
        except Exception as e:
            logger.error(f"Error in get_dsm_for_region: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "region_name": region_name
            }
    
    def _calculate_bbox_from_center(self, lat: float, lng: float, buffer_km: float) -> List[float]:
        """
        Calculate bounding box from center coordinates and buffer distance
        
        Returns [west, south, east, north]
        """
        # Approximate conversion: 1 degree ≈ 111 km
        # Adjust for latitude (longitude degrees get smaller towards poles)
        lat_buffer = buffer_km / 111.0
        lng_buffer = buffer_km / (111.0 * abs(np.cos(np.radians(lat))))
        
        west = lng - lng_buffer
        east = lng + lng_buffer
        south = lat - lat_buffer
        north = lat + lat_buffer
        
        return [west, south, east, north]
    
    async def _download_via_planetary_computer(self, bbox: List[float], 
                                             output_dir: Path, 
                                             region_name: str,
                                             resolution: str) -> Dict:
        """Download DSM via Microsoft Planetary Computer STAC API"""
        try:
            import pystac_client
            import planetary_computer
            
            # Collection names for Copernicus DEM
            collection_id = "cop-dem-glo-30" if resolution == "30m" else "cop-dem-glo-90"
            
            # Open the STAC client
            catalog = pystac_client.Client.open(
                self.planetary_computer_endpoint,
                modifier=planetary_computer.sign_inplace
            )
            
            # Search for items
            search = catalog.search(
                collections=[collection_id],
                bbox=bbox
            )
            
            items = list(search.items())
            logger.info(f"Found {len(items)} DSM tiles for region")
            
            if not items:
                return {"success": False, "error": "No DSM tiles found for the specified region"}
            
            # Download and merge tiles
            downloaded_files = []
            temp_files = []
            
            for i, item in enumerate(items):
                # Get the data asset (usually 'data' or 'elevation')
                asset_key = 'data'
                if asset_key not in item.assets:
                    # Try other common asset keys
                    for key in ['elevation', 'dem', 'cog']:
                        if key in item.assets:
                            asset_key = key
                            break
                
                if asset_key not in item.assets:
                    logger.warning(f"No suitable asset found in item {item.id}")
                    continue
                
                asset = item.assets[asset_key]
                
                # Download tile to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tif')
                temp_files.append(temp_file.name)
                
                response = requests.get(asset.href, stream=True)
                response.raise_for_status()
                
                with open(temp_file.name, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                downloaded_files.append(temp_file.name)
                logger.info(f"Downloaded tile {i+1}/{len(items)}")
            
            if not downloaded_files:
                return {"success": False, "error": "Failed to download any DSM tiles"}
            
            # Merge tiles and crop to exact bbox
            output_file = output_dir / f"{region_name}_copernicus_dsm_{resolution}.tif"
            merged_file = await self._merge_and_crop_tiles(downloaded_files, bbox, output_file)
            
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            # Generate metadata
            metadata = await self._generate_dsm_metadata(merged_file, bbox, resolution)
            
            return {
                "success": True,
                "method": "planetary_computer",
                "file_path": str(merged_file),
                "metadata": metadata,
                "tiles_downloaded": len(downloaded_files),
                "region_name": region_name
            }
            
        except ImportError:
            logger.error("pystac-client and planetary-computer packages required for this method")
            raise Exception("Missing required packages: pystac-client, planetary-computer")
        except Exception as e:
            logger.error(f"Planetary Computer download failed: {str(e)}")
            raise
    
    async def _download_via_stac_api(self, bbox: List[float], 
                                   output_dir: Path, 
                                   region_name: str,
                                   resolution: str) -> Dict:
        """Download DSM via direct STAC API access"""
        try:
            import pystac_client
            
            # Choose endpoint based on resolution
            stac_endpoint = self.stac_endpoints["glo30" if resolution == "30m" else "glo90"]
            
            # Open the STAC catalog
            catalog = pystac_client.Client.open(stac_endpoint)
            
            # Search for items
            search = catalog.search(bbox=bbox)
            items = list(search.items())
            
            if not items:
                return {"success": False, "error": "No DSM tiles found for the specified region"}
            
            logger.info(f"Found {len(items)} DSM tiles via STAC API")
            
            # Download and process tiles (similar to planetary computer method)
            downloaded_files = []
            temp_files = []
            
            for i, item in enumerate(items):
                # Find the elevation data asset
                asset_key = None
                for key in ['data', 'elevation', 'dem']:
                    if key in item.assets:
                        asset_key = key
                        break
                
                if not asset_key:
                    continue
                
                asset = item.assets[asset_key]
                
                # Download tile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tif')
                temp_files.append(temp_file.name)
                
                response = requests.get(asset.href, stream=True)
                response.raise_for_status()
                
                with open(temp_file.name, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                downloaded_files.append(temp_file.name)
                logger.info(f"Downloaded tile {i+1}/{len(items)} via STAC API")
            
            if not downloaded_files:
                return {"success": False, "error": "Failed to download any DSM tiles"}
            
            # Merge and process
            output_file = output_dir / f"{region_name}_copernicus_dsm_{resolution}.tif"
            merged_file = await self._merge_and_crop_tiles(downloaded_files, bbox, output_file)
            
            # Clean up
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            metadata = await self._generate_dsm_metadata(merged_file, bbox, resolution)
            
            return {
                "success": True,
                "method": "stac_api",
                "file_path": str(merged_file),
                "metadata": metadata,
                "tiles_downloaded": len(downloaded_files),
                "region_name": region_name
            }
            
        except ImportError:
            logger.error("pystac-client package required for this method")
            raise Exception("Missing required package: pystac-client")
        except Exception as e:
            logger.error(f"STAC API download failed: {str(e)}")
            raise
    
    async def _download_via_s3_direct(self, bbox: List[float], 
                                    output_dir: Path, 
                                    region_name: str,
                                    resolution: str) -> Dict:
        """Download DSM via direct S3 access (fallback method)"""
        try:
            # This is a simplified implementation
            # In practice, you'd need to determine which tiles cover the bbox
            # and construct the S3 URLs accordingly
            
            bucket = self.s3_buckets["glo30" if resolution == "30m" else "glo90"]
            
            # For now, return not implemented
            # This would require implementing tile indexing logic
            return {
                "success": False, 
                "error": "Direct S3 method not fully implemented - requires tile indexing"
            }
            
        except Exception as e:
            logger.error(f"Direct S3 download failed: {str(e)}")
            raise
    
    async def _merge_and_crop_tiles(self, tile_files: List[str], 
                                  bbox: List[float], 
                                  output_file: Path) -> Path:
        """Merge multiple raster tiles and crop to bounding box"""
        try:
            # Open all tiles
            src_files_to_mosaic = []
            for tile_file in tile_files:
                src = rasterio.open(tile_file)
                src_files_to_mosaic.append(src)
            
            # Merge tiles
            mosaic, out_trans = merge(src_files_to_mosaic)
            
            # Get the metadata from the first file
            out_meta = src_files_to_mosaic[0].meta.copy()
            
            # Update metadata
            out_meta.update({
                "driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_trans,
                "compress": "lzw"
            })
            
            # Write merged raster
            with rasterio.open(output_file, "w", **out_meta) as dest:
                dest.write(mosaic)
            
            # Close source files
            for src in src_files_to_mosaic:
                src.close()
            
            # Crop to exact bounding box if needed
            # (This step can be added if precise cropping is required)
            
            logger.info(f"Successfully merged {len(tile_files)} tiles to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error merging tiles: {str(e)}")
            raise
    
    async def _generate_dsm_metadata(self, dsm_file: Path, 
                                   bbox: List[float], 
                                   resolution: str) -> Dict:
        """Generate metadata for the downloaded DSM"""
        try:
            with rasterio.open(dsm_file) as src:
                stats = []
                for i in range(src.count):
                    band_data = src.read(i + 1)
                    # Mask no-data values
                    if src.nodata is not None:
                        band_data = band_data[band_data != src.nodata]
                    
                    if len(band_data) > 0:
                        stats.append({
                            "band": i + 1,
                            "min": float(np.min(band_data)),
                            "max": float(np.max(band_data)),
                            "mean": float(np.mean(band_data)),
                            "std": float(np.std(band_data))
                        })
                
                metadata = {
                    "source": "Copernicus DEM",
                    "resolution": resolution,
                    "bbox": bbox,
                    "crs": src.crs.to_string(),
                    "transform": list(src.transform),
                    "shape": [src.height, src.width],
                    "bands": src.count,
                    "dtype": str(src.dtypes[0]),
                    "nodata": src.nodata,
                    "statistics": stats
                }
                
                return metadata
                
        except Exception as e:
            logger.error(f"Error generating metadata: {str(e)}")
            return {}

# Global service instance
copernicus_dsm_service = CopernicusDSMService()
