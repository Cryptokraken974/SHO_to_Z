"""Sentinel-2 data source for satellite imagery using pystac_client."""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple, Callable, Callable
from pathlib import Path
import json
from datetime import datetime, timedelta
import requests

try:
    from pystac_client import Client
    import pystac
    import planetary_computer as pc
    from osgeo import gdal
except ImportError as e:
    if "gdal" in str(e).lower():
        raise ImportError("GDAL is required for data cropping. Install with: pip install gdal")
    else:
        raise ImportError("pystac_client and planetary_computer are required. Install with: pip install pystac-client planetary-computer")

from .base import (
    BaseDataSource, DataSourceCapability, DataType, DataResolution,
    DownloadRequest, DownloadResult
)
from ..utils.coordinates import BoundingBox

logger = logging.getLogger(__name__)

class Sentinel2Source(BaseDataSource):
    """Sentinel-2 satellite imagery data source using STAC APIs."""
    
    # Microsoft Planetary Computer STAC API (free, no auth required for Sentinel-2)
    STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
    # Alternative: AWS Earth Search
    # STAC_URL = "https://earth-search.aws.element84.com/v1"
    
    COLLECTION_ID = "sentinel-2-l2a"  # Sentinel-2 Level 2A (surface reflectance)
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        """Initialize Sentinel-2 data source."""
        # Use a dummy cache dir since we save directly to data/acquired/
        super().__init__(None, "data/cache/sentinel2_temp")
        self._client = None
        self.progress_callback = progress_callback
    
    @property
    def capabilities(self) -> DataSourceCapability:
        return DataSourceCapability(
            data_types=[DataType.IMAGERY],
            resolutions=[DataResolution.HIGH, DataResolution.MEDIUM],
            coverage_areas=["Global"],
            max_area_km2=5000.0,
            requires_api_key=False
        )
    
    @property
    def name(self) -> str:
        return "sentinel2"
    
    def _get_client(self) -> Client:
        """Get or create STAC client with planetary computer modifier for automatic URL signing."""
        if self._client is None:
            self._client = Client.open(
                self.STAC_URL,
                modifier=pc.sign_inplace  # Automatically sign all URLs
            )
        return self._client
    
    async def check_availability(self, request: DownloadRequest) -> bool:
        """Check if Sentinel-2 imagery is available for the bounding box."""
        if not self._validate_request(request):
            return False
            
        if request.data_type != DataType.IMAGERY:
            return False
            
        try:
            client = self._get_client()
            
            # Search for available items
            search = client.search(
                collections=[self.COLLECTION_ID],
                bbox=[request.bbox.west, request.bbox.south, request.bbox.east, request.bbox.north],
                datetime="2024-01-01T00:00:00Z/2025-05-30T23:59:59Z",  # Last year and a half with proper RFC 3339 format
                limit=1
            )
            
            items = list(search.items())
            return len(items) > 0
            
        except Exception as e:
            logger.warning(f"Error checking Sentinel-2 availability: {e}")
            return True  # Assume available if we can't check
    
    async def estimate_size(self, request: DownloadRequest) -> float:
        """Estimate download size for Sentinel-2 red and NIR bands."""
        if not await self.check_availability(request):
            return 0.0
        
        # Sentinel-2 red (B04) and NIR (B08) bands are typically 10-20 MB each for a small area
        # Estimate based on the area requested
        bbox_area = request.bbox.area_km2()
        
        # Base size per km² for both bands
        size_per_km2 = 0.5  # MB per km²
        estimated_size = bbox_area * size_per_km2
        
        # Minimum reasonable size
        estimated_size = max(estimated_size, 5.0)
        
        return min(estimated_size, request.max_file_size_mb)
    
    async def download(self, request: DownloadRequest) -> DownloadResult:
        """Download Sentinel-2 red and NIR bands."""
        try:
            print(f"\n🛰️ {'='*60}")
            print(f"🛰️ SENTINEL-2 DATA ACQUISITION STARTED")
            print(f"🛰️ {'='*60}")
            
            print(f"📍 Target coordinates: {request.bbox.west:.6f}°W, {request.bbox.south:.6f}°S, {request.bbox.east:.6f}°E, {request.bbox.north:.6f}°N")
            print(f"📐 Search area: {request.bbox.area_km2():.2f} km²")
            print(f"📊 Max file size: {request.max_file_size_mb} MB")
            
            if not await self.check_availability(request):
                print(f"❌ No Sentinel-2 data available for the requested area")
                return DownloadResult(
                    success=False,
                    error_message="No Sentinel-2 data available for the requested area"
                )
            
            print(f"✅ Sentinel-2 data is available for this region")
            
            # Search for the best available item
            print(f"\n🔍 Searching for optimal Sentinel-2 scenes...")
            item = await self._find_best_item(request)
            
            if not item:
                print(f"❌ No suitable Sentinel-2 items found")
                return DownloadResult(
                    success=False,
                    error_message="No suitable Sentinel-2 items found"
                )
            
            # Display scene information
            acquisition_date = item.datetime.strftime("%Y-%m-%d") if item.datetime else "unknown_date"
            cloud_cover = item.properties.get('eo:cloud_cover', 'unknown')
            
            print(f"✅ Selected optimal Sentinel-2 scene:")
            print(f"   📅 Acquisition date: {acquisition_date}")
            print(f"   🆔 Scene ID: {item.id}")
            print(f"   ☁️ Cloud cover: {cloud_cover}%")
            print(f"   🛰️ Platform: {item.properties.get('platform', 'Sentinel-2')}")
            
            # Create output directory using item ID and date for unique identification
            acquisition_date_folder = item.datetime.strftime("%Y%m%d") if item.datetime else "unknown_date"
            region_name = f"{item.id}_{acquisition_date_folder}"
            output_dir = Path("data/acquired") / region_name / "sentinel-2"
            
            print(f"\n📁 Creating output directory: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Output directory ready")
            
            logger.info(f"📁 Saving Sentinel-2 data to: {output_dir}")
            
            # Download red and NIR bands with cropping to reduce file size
            print(f"\n📥 Starting band downloads with cropping...")
            print(f"🔴 Downloading and cropping Red band (B04)...")
            red_path = await self._download_band(item, "B04", "Red", output_dir, request.bbox, self.progress_callback)
            
            print(f"🌿 Downloading and cropping NIR band (B08)...")
            nir_path = await self._download_band(item, "B08", "NIR", output_dir, request.bbox, self.progress_callback)
            
            if not red_path or not nir_path:
                print(f"❌ Failed to download required bands")
                return DownloadResult(
                    success=False,
                    error_message="Failed to download required bands"
                )
            
            # Calculate total file size
            total_size = 0
            if red_path.exists():
                red_size = red_path.stat().st_size
                total_size += red_size
                print(f"✅ Red band downloaded: {red_size / (1024*1024):.2f} MB")
            if nir_path.exists():
                nir_size = nir_path.stat().st_size
                total_size += nir_size
                print(f"✅ NIR band downloaded: {nir_size / (1024*1024):.2f} MB")
            
            total_size_mb = total_size / (1024 * 1024)
            
            print(f"\n🎉 SENTINEL-2 DOWNLOAD COMPLETED SUCCESSFULLY!")
            print(f"📊 Total download size: {total_size_mb:.2f} MB")
            print(f"📁 Files saved to: {output_dir}")
            print(f"🛰️ {'='*60}\n")
            
            return DownloadResult(
                success=True,
                file_path=str(output_dir),  # Return directory containing both bands
                file_size_mb=total_size_mb,
                resolution_m=10.0,  # Sentinel-2 red and NIR are 10m resolution
                metadata={
                    'item_id': item.id,
                    'acquisition_date': item.datetime.isoformat() if item.datetime else None,
                    'cloud_cover': item.properties.get('eo:cloud_cover', 'unknown'),
                    'source': 'Sentinel-2',
                    'collection': self.COLLECTION_ID,
                    'bands': ['Red', 'NIR'],  # Human-readable band names
                    'red_band_path': str(red_path),
                    'nir_band_path': str(nir_path),
                    'region_name': region_name,
                    'bbox': {
                        'west': request.bbox.west,
                        'south': request.bbox.south,
                        'east': request.bbox.east,
                        'north': request.bbox.north
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Sentinel-2 download failed: {e}")
            return DownloadResult(
                success=False,
                error_message=f"Sentinel-2 download failed: {str(e)}"
            )
    
    async def _find_best_item(self, request: DownloadRequest):
        """Find the best Sentinel-2 item for the request."""
        try:
            client = self._get_client()
            
            print(f"🔍 Searching Sentinel-2 catalog...")
            print(f"   📅 Date range: Last 6 months (Nov 2024 - May 2025)")
            print(f"   📍 Bounding box: [{request.bbox.west:.6f}, {request.bbox.south:.6f}, {request.bbox.east:.6f}, {request.bbox.north:.6f}]")
            
            # Search for items from the last 6 months
            search = client.search(
                collections=[self.COLLECTION_ID],
                bbox=[request.bbox.west, request.bbox.south, request.bbox.east, request.bbox.north],
                datetime="2024-11-01T00:00:00Z/2025-05-30T23:59:59Z",  # Last 6 months with proper RFC 3339 format
                limit=20
            )
            
            items = list(search.items())
            
            print(f"📊 Found {len(items)} Sentinel-2 scenes in search area")
            
            if not items:
                print(f"❌ No Sentinel-2 scenes found for the specified area and time range")
                return None
            
            # Display information about available scenes
            print(f"\n📋 Analyzing available scenes:")
            for i, item in enumerate(items[:5]):  # Show first 5 scenes
                cloud_cover = item.properties.get('eo:cloud_cover', 'unknown')
                date_str = item.datetime.strftime("%Y-%m-%d") if item.datetime else "unknown"
                print(f"   {i+1}. {date_str} - {cloud_cover}% cloud cover - {item.id[:20]}...")
            
            if len(items) > 5:
                print(f"   ... and {len(items) - 5} more scenes")
            
            # Sort by cloud cover (ascending) and then by date (descending)
            def sort_key(item):
                cloud_cover = item.properties.get('eo:cloud_cover', 100)
                date_score = 0
                if item.datetime:
                    # More recent items get higher score
                    days_ago = (datetime.now() - item.datetime.replace(tzinfo=None)).days
                    date_score = -days_ago  # Negative so more recent = higher score
                return (cloud_cover, date_score)
            
            print(f"\n🎯 Selecting optimal scene (lowest cloud cover, most recent)...")
            items.sort(key=sort_key)
            
            best_item = items[0]
            best_cloud_cover = best_item.properties.get('eo:cloud_cover', 'unknown')
            best_date = best_item.datetime.strftime("%Y-%m-%d") if best_item.datetime else "unknown"
            
            print(f"✅ Selected scene: {best_date} with {best_cloud_cover}% cloud cover")
            
            return best_item
            
        except Exception as e:
            logger.error(f"Error finding Sentinel-2 item: {e}")
            print(f"❌ Error during scene search: {e}")
            return None
    
    async def _download_band(self, item, band_name: str, human_name: str, output_dir: Path, bbox: BoundingBox, progress_callback=None) -> Optional[Path]:
        """Download a specific band and crop it to the requested bounding box."""
        try:
            # Get the asset for the requested band
            if band_name not in item.assets:
                logger.error(f"Band {band_name} not found in item assets")
                return None

            asset = item.assets[band_name]
            download_url = asset.href

            # Sign the URL for authenticated access to Microsoft Planetary Computer
            logger.info(f"Signing URL for authentication")
            signed_url = pc.sign(download_url)

            # Create temporary filename for full download, then final cropped filename
            temp_filename = f"{human_name}_full.tif"
            final_filename = f"{human_name}.tif"
            temp_path = output_dir / temp_filename
            output_path = output_dir / final_filename

            # Download the full tile first
            logger.info(f"🛰️ Downloading full Sentinel-2 {human_name} tile")
            await self._download_band_direct(signed_url, temp_path, progress_callback)

            if not temp_path.exists():
                logger.error(f"❌ Failed to download {human_name} band")
                return None

            # Crop the downloaded file to the requested bounding box
            print(f"\n✂️ Cropping {human_name} band to requested area...")
            crop_success = await self._crop_geotiff_to_bbox(temp_path, output_path, bbox, progress_callback)

            if crop_success and output_path.exists():
                file_size = output_path.stat().st_size / (1024*1024)
                logger.info(f"✅ Successfully processed {human_name} band ({file_size:.2f} MB)")
                return output_path
            else:
                logger.error(f"❌ Failed to crop {human_name} band")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading band {band_name} ({human_name}): {e}")
            return None
    
    async def _download_band_direct(self, url: str, output_path: Path, progress_callback=None):
        """Download a band directly with progress tracking."""
        try:
            print(f"\n🛰️ SENTINEL-2 DOWNLOAD: Starting {output_path.name}")
            print(f"📡 URL: {url[:100]}...")
            print(f"💾 Output: {output_path}")
            
            # Send initial progress update
            if progress_callback:
                await progress_callback({
                    "type": "download_start",
                    "band": output_path.stem,
                    "message": f"Starting download of {output_path.name}"
                })
            
            # Get file size first for progress tracking
            head_response = requests.head(url, allow_redirects=True)
            total_size = int(head_response.headers.get('content-length', 0))
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size > 0:
                print(f"📊 File size: {total_size_mb:.2f} MB ({total_size:,} bytes)")
                if progress_callback:
                    await progress_callback({
                        "type": "download_info",
                        "band": output_path.stem,
                        "total_size_mb": total_size_mb,
                        "message": f"File size: {total_size_mb:.2f} MB"
                    })
            else:
                print(f"📊 File size: Unknown (streaming)")
            
            # Download the file with progress tracking
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            downloaded = 0
            chunk_size = 8192
            last_progress = 0
            
            print(f"⬇️ Downloading...")
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress every 5% or every 5MB (whichever is smaller)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if progress - last_progress >= 5:
                                downloaded_mb = downloaded / (1024 * 1024)
                                print(f"📊 Progress: {progress:.1f}% ({downloaded_mb:.2f}/{total_size_mb:.2f} MB)")
                                if progress_callback:
                                    await progress_callback({
                                        "type": "download_progress",
                                        "band": output_path.stem,
                                        "progress": progress,
                                        "downloaded_mb": downloaded_mb,
                                        "total_mb": total_size_mb,
                                        "message": f"Progress: {progress:.1f}%"
                                    })
                                last_progress = progress
                        else:
                            # Unknown size - show downloaded amount every 5MB
                            downloaded_mb = downloaded / (1024 * 1024)
                            if downloaded_mb - last_progress >= 5:
                                print(f"📊 Downloaded: {downloaded_mb:.2f} MB")
                                if progress_callback:
                                    await progress_callback({
                                        "type": "download_progress",
                                        "band": output_path.stem,
                                        "downloaded_mb": downloaded_mb,
                                        "message": f"Downloaded: {downloaded_mb:.2f} MB"
                                    })
                                last_progress = downloaded_mb
            
            final_size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"✅ Download complete! Final size: {final_size_mb:.2f} MB")
            print(f"📄 Saved to: {output_path}")
            
            if progress_callback:
                await progress_callback({
                    "type": "download_complete",
                    "band": output_path.stem,
                    "final_size_mb": final_size_mb,
                    "message": f"Download complete: {final_size_mb:.2f} MB"
                })
                        
        except Exception as e:
            print(f"❌ Download failed: {str(e)}")
            logger.error(f"Error downloading band: {e}")
            if progress_callback:
                await progress_callback({
                    "type": "download_error",
                    "band": output_path.stem,
                    "error": str(e),
                    "message": f"Download failed: {str(e)}"
                })
            raise

    async def _crop_geotiff_to_bbox(self, input_path: Path, output_path: Path, bbox: BoundingBox, progress_callback=None) -> bool:
        """Crop a GeoTIFF file to the specified bounding box to reduce file size."""
        try:
            print(f"\n✂️ CROPPING: {input_path.name}")
            print(f"📐 Target area: {bbox.west:.6f}°W, {bbox.south:.6f}°S, {bbox.east:.6f}°E, {bbox.north:.6f}°N")
            
            # Send cropping start update
            if progress_callback:
                await progress_callback({
                    "type": "crop_start",
                    "band": output_path.stem,
                    "message": f"Starting cropping of {input_path.name}"
                })
            
            # Get original file size
            original_size_mb = input_path.stat().st_size / (1024 * 1024)
            print(f"📊 Original size: {original_size_mb:.2f} MB")
            
            # Use GDAL translate to crop the image
            translate_options = gdal.TranslateOptions(
                projWin=[bbox.west, bbox.north, bbox.east, bbox.south],  # [ulx, uly, lrx, lry]
                projWinSRS='EPSG:4326',  # WGS84 coordinates
                format='GTiff',
                creationOptions=['COMPRESS=LZW', 'TILED=YES']  # Compression to reduce file size
            )
            
            print(f"🔄 Cropping in progress...")
            if progress_callback:
                await progress_callback({
                    "type": "crop_progress",
                    "band": output_path.stem,
                    "message": "Cropping in progress..."
                })
            
            result = gdal.Translate(str(output_path), str(input_path), options=translate_options)
            
            if result is None:
                print(f"❌ GDAL cropping failed")
                if progress_callback:
                    await progress_callback({
                        "type": "crop_error",
                        "band": output_path.stem,
                        "message": "GDAL cropping failed"
                    })
                return False
            
            # Clean up GDAL dataset
            result = None
            
            if output_path.exists():
                cropped_size_mb = output_path.stat().st_size / (1024 * 1024)
                size_reduction = ((original_size_mb - cropped_size_mb) / original_size_mb) * 100
                print(f"✅ Cropping complete!")
                print(f"📊 Cropped size: {cropped_size_mb:.2f} MB")
                print(f"📉 Size reduction: {size_reduction:.1f}%")
                
                if progress_callback:
                    await progress_callback({
                        "type": "crop_complete",
                        "band": output_path.stem,
                        "original_size_mb": original_size_mb,
                        "cropped_size_mb": cropped_size_mb,
                        "size_reduction": size_reduction,
                        "message": f"Cropping complete: {size_reduction:.1f}% size reduction"
                    })
                
                # Remove original file to save space
                input_path.unlink()
                print(f"🗑️ Removed original uncropped file")
                
                return True
            else:
                print(f"❌ Cropped file not created")
                if progress_callback:
                    await progress_callback({
                        "type": "crop_error",
                        "band": output_path.stem,
                        "message": "Cropped file not created"
                    })
                return False
                
        except Exception as e:
            print(f"❌ Cropping failed: {str(e)}")
            logger.error(f"Error cropping GeoTIFF: {e}")
            if progress_callback:
                await progress_callback({
                    "type": "crop_error",
                    "band": output_path.stem,
                    "error": str(e),
                    "message": f"Cropping failed: {str(e)}"
                })
            return False
    
    async def close(self):
        """Clean up resources."""
        # pystac_client doesn't require explicit cleanup
        pass
