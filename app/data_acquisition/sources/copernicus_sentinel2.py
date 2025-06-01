"""
Copernicus Data Space Ecosystem Sentinel-2 Source

More efficient Sentinel-2 data acquisition using the Copernicus Data Space Ecosystem
with OAuth2 client credentials authentication.
"""

import os
import json
import math
import asyncio
import aiohttp
import aiofiles
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path

# OAuth2 imports for CDSE authentication
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from .base import BaseDataSource, DownloadRequest, DownloadResult, DataType, DataSourceCapability, DataResolution
from ..utils.coordinates import BoundingBox

logger = logging.getLogger(__name__)

class CopernicusSentinel2Source(BaseDataSource):
    """
    Sentinel-2 data source using Copernicus Data Space Ecosystem
    """
    
    def __init__(self, 
                 token: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 cache_dir: str = "./data_cache",
                 progress_callback: Optional[Callable] = None):
        """
        Initialize Copernicus Sentinel-2 source
        
        Args:
            token: Legacy Copernicus Data Space Ecosystem access token (deprecated)
            client_id: OAuth2 client ID for CDSE authentication
            client_secret: OAuth2 client secret for CDSE authentication
            cache_dir: Directory for caching data
            progress_callback: Optional callback for progress updates
        """
        super().__init__(api_key=token or client_id, cache_dir=cache_dir)
        
        # Support both legacy token and OAuth2 client credentials
        self.legacy_token = token or os.getenv("CDSE_TOKEN")
        self.client_id = client_id or os.getenv("CDSE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("CDSE_CLIENT_SECRET")
        
        self.progress_callback = progress_callback
        
        # OAuth2 authentication setup
        self.oauth_session = None
        self.token_expires_at = None
        
        # Session for HTTP requests (for async operations)
        self.session = None
        
        # Cancellation support
        self.is_cancelled = False
        self.current_task = None
        
        # Initialize OAuth2 session if credentials are available
        if self.client_id and self.client_secret:
            self._initialize_oauth_session()
        elif not self.legacy_token:
            logger.warning("No CDSE credentials found. Set CDSE_CLIENT_ID/CDSE_CLIENT_SECRET or CDSE_TOKEN environment variables.")
    
    @property
    def capabilities(self) -> DataSourceCapability:
        """Return the capabilities of this data source."""
        return DataSourceCapability(
            data_types=[DataType.IMAGERY],
            resolutions=[DataResolution.HIGH, DataResolution.MEDIUM],
            coverage_areas=["Global"],
            max_area_km2=10000.0,  # 100km x 100km max area
            requires_api_key=True
        )
    
    @property
    def name(self) -> str:
        """Return the name of this data source."""
        return "copernicus_sentinel2"
    
    async def estimate_size(self, request: DownloadRequest) -> float:
        """Estimate download size in MB."""
        # Estimate based on area and bands (2 bands: B04, B08)
        # Typical Sentinel-2 10m resolution: ~0.1 MB per km² per band
        area_km2 = request.bbox.area_km2()
        estimated_mb = area_km2 * 0.2  # 2 bands × 0.1 MB/km²/band
        return min(estimated_mb, 100.0)  # Cap at 100MB due to processing limitations
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._get_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def close(self):
        """Close the HTTP session and clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("CopernicusSentinel2Source closed")
    
    def _initialize_oauth_session(self):
        """Initialize OAuth2 session for client credentials flow"""
        try:
            client = BackendApplicationClient(client_id=self.client_id)
            self.oauth_session = OAuth2Session(client=client)
            logger.info("OAuth2 session initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OAuth2 session: {e}")
            self.oauth_session = None
    
    async def _authenticate_oauth2_async(self) -> Optional[str]:
        """Authenticate using OAuth2 client credentials (async version)"""
        if not self.oauth_session:
            logger.error("OAuth2 session not initialized")
            return None
        
        try:
            # Use requests-oauthlib in a thread since it's synchronous
            import concurrent.futures
            
            def fetch_token():
                return self.oauth_session.fetch_token(
                    token_url="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
            
            # Run the synchronous OAuth2 call in a thread
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                token = await loop.run_in_executor(executor, fetch_token)
            
            access_token = token.get('access_token')
            expires_in = token.get('expires_in', 3600)
            
            # Calculate expiration time
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 60s buffer
            
            logger.info(f"OAuth2 authentication successful, token expires in {expires_in}s")
            return access_token
            
        except Exception as e:
            logger.error(f"OAuth2 authentication failed: {e}")
            return None
    
    async def _get_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if necessary"""
        # Try OAuth2 first
        if self.client_id and self.client_secret:
            # Check if token needs refresh
            if not self.token_expires_at or datetime.now() >= self.token_expires_at:
                logger.info("Refreshing OAuth2 access token")
                return await self._authenticate_oauth2_async()
            else:
                # Get current token from oauth session
                if self.oauth_session and hasattr(self.oauth_session, 'token') and self.oauth_session.token:
                    # Handle both dict and string token formats
                    token = self.oauth_session.token
                    if isinstance(token, dict):
                        return token.get('access_token')
                    elif isinstance(token, str):
                        # If token is a string, it might be the access token itself
                        return token
                    else:
                        logger.warning(f"Unexpected token type: {type(token)}")
                        return await self._authenticate_oauth2_async()
                else:
                    return await self._authenticate_oauth2_async()
        
        # Fallback to legacy token
        return self.legacy_token
    
    def _check_cancelled(self):
        """Check if operation was cancelled"""
        if self.is_cancelled:
            raise asyncio.CancelledError("Operation was cancelled")
    
    def cancel(self):
        """Cancel the current operation"""
        self.is_cancelled = True
        if self.current_task:
            self.current_task.cancel()
    
    def _calculate_bbox_degrees(self, bbox: BoundingBox, buffer_factor: float = 0.1) -> List[float]:
        """
        Calculate bounding box in degrees with optional buffer
        
        Args:
            bbox: Input bounding box
            buffer_factor: Buffer factor (0.1 = 10% buffer)
            
        Returns:
            List of [west, south, east, north] in degrees
        """
        if buffer_factor > 0:
            # Calculate buffer in degrees (approximate)
            width = bbox.east - bbox.west
            height = bbox.north - bbox.south
            lon_buffer = width * buffer_factor
            lat_buffer = height * buffer_factor
            
            return [
                bbox.west - lon_buffer,
                bbox.south - lat_buffer,
                bbox.east + lon_buffer,
                bbox.north + lat_buffer
            ]
        else:
            return [bbox.west, bbox.south, bbox.east, bbox.north]
    
    async def check_availability(self, request: DownloadRequest) -> bool:
        """
        Check if Sentinel-2 data is available for the requested area and time
        
        Args:
            request: Download request
            
        Returns:
            True if data is available
        """
        try:
            self._check_cancelled()
            session = await self._get_session()
            
            # Calculate search window - use historical dates for availability check
            date_to = datetime.now().replace(day=1) - timedelta(days=1)  # End of last month
            date_from = date_to - timedelta(days=365)  # Search past year
            
            bbox = self._calculate_bbox_degrees(request.bbox)
            
            # Use main STAC search endpoint (works without authentication)
            # This endpoint has better performance and reliability
            catalog_url = "https://catalogue.dataspace.copernicus.eu/stac/search"
            
            # Build query parameters
            params = {
                "collections": "SENTINEL-2",
                "bbox": ",".join(map(str, bbox)),
                "datetime": f"{date_from.strftime('%Y-%m-%dT%H:%M:%SZ')}/{date_to.strftime('%Y-%m-%dT%H:%M:%SZ')}",
                "limit": "1"
            }
            
            headers = {
                "Accept": "application/json"
            }
            
            logger.info(f"Checking availability for bbox: {bbox}")
            logger.info(f"Using catalog URL: {catalog_url}")
            logger.info(f"Search period: {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}")
            
            async with session.get(
                catalog_url,
                headers=headers,
                params=params
            ) as response:
                self._check_cancelled()
                logger.info(f"Catalog search response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    feature_count = len(data.get("features", []))
                    logger.info(f"Found {feature_count} Sentinel-2 scenes")
                    return feature_count > 0
                else:
                    error_text = await response.text()
                    logger.error(f"Catalog search failed: {response.status} - {error_text}")
                    return False
                    
        except asyncio.CancelledError:
            logger.info("Availability check cancelled")
            return False
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return False

    async def download(self, request: DownloadRequest) -> DownloadResult:
        """
        Download Sentinel-2 data using Copernicus Processing API
        
        Args:
            request: Download request
            
        Returns:
            DownloadResult with success status and file information
        """
        access_token = await self._get_access_token()
        if not access_token:
            return DownloadResult(
                success=False,
                error_message="No CDSE access token available. Set CDSE_CLIENT_ID/CDSE_CLIENT_SECRET or CDSE_TOKEN environment variables."
            )
        
        try:
            self._check_cancelled()
            
            # Send progress update
            if self.progress_callback:
                await self.progress_callback({"message": "Searching for Sentinel-2 scenes...", "type": "download_start", "band": "Sentinel-2"})
            
            session = await self._get_session()
            
            # Find the best scene
            product_id, metadata = await self._find_best_scene(request, session)
            if not product_id:
                return DownloadResult(
                    success=False,
                    error_message="No suitable Sentinel-2 scenes found for the specified area and time range"
                )
            
            if self.progress_callback:
                await self.progress_callback({"message": f"Found scene: {product_id}", "type": "download_info", "band": "Sentinel-2"})
                await self.progress_callback({"message": "Starting download...", "type": "download_start", "band": "Sentinel-2"})
            
            # Download the data
            file_path = await self._download_processed_data(request, product_id, metadata, session)
            
            if file_path and os.path.exists(file_path):
                return DownloadResult(
                    success=True,
                    file_path=file_path,
                    metadata=metadata
                )
            else:
                return DownloadResult(
                    success=False,
                    error_message="Download completed but file was not created"
                )
                
        except asyncio.CancelledError:
            logger.info("Download cancelled")
            return DownloadResult(
                success=False,
                error_message="Download was cancelled"
            )
        except Exception as e:
            logger.error(f"Download error: {e}")
            return DownloadResult(
                success=False,
                error_message=f"Download error: {str(e)}"
            )
    
    async def _find_best_scene(self, request: DownloadRequest, session) -> tuple[Optional[str], Dict[str, Any]]:
        """
        Find the best available Sentinel-2 scene for the request
        
        Args:
            request: Download request
            session: aiohttp session
            
        Returns:
            Tuple of (product_id, metadata) or (None, {})
        """
        # Calculate search window - use historical dates for better results
        date_to = datetime.now().replace(day=1) - timedelta(days=1)  # End of last month
        bbox = self._calculate_bbox_degrees(request.bbox)
        
        # Try different time windows if needed
        for days_back in [90, 180, 365]:
            self._check_cancelled()
            
            date_from = date_to - timedelta(days=days_back)
                
            # Use main STAC search endpoint (works without authentication)
            catalog_url = "https://catalogue.dataspace.copernicus.eu/stac/search"
            
            params = {
                "collections": "SENTINEL-2",
                "bbox": ",".join(map(str, bbox)),
                "datetime": f"{date_from.strftime('%Y-%m-%dT%H:%M:%SZ')}/{date_to.strftime('%Y-%m-%dT%H:%M:%SZ')}",
                "limit": "10",
                "sortby": "-datetime"  # Sort by date descending
            }
            
            headers = {
                "Accept": "application/json"
            }
            
            logger.info(f"Searching for scenes with {days_back} days lookback period")
            logger.info(f"Search bbox: {bbox}")
            logger.info(f"Search period: {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}")
            
            try:
                async with session.get(
                    catalog_url,
                    headers=headers,
                    params=params
                ) as response:
                    self._check_cancelled()
                    logger.info(f"Scene search response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        features = data.get("features", [])
                        logger.info(f"Found {len(features)} scenes in {days_back} day search window")
                        
                        # Filter by cloud cover and find best scene
                        good_scenes = []
                        for feature in features:
                            properties = feature.get("properties", {})
                            cloud_cover = properties.get("eo:cloud_cover", properties.get("cloudCover", 100))
                            
                            # Prefer scenes with low cloud cover
                            if cloud_cover <= 30:
                                good_scenes.append((feature, cloud_cover))
                        
                        # If no low-cloud scenes, accept higher cloud cover
                        if not good_scenes:
                            for feature in features:
                                properties = feature.get("properties", {})
                                cloud_cover = properties.get("eo:cloud_cover", properties.get("cloudCover", 100))
                                if cloud_cover <= 80:
                                    good_scenes.append((feature, cloud_cover))
                        
                        if good_scenes:
                            # Sort by cloud cover
                            good_scenes.sort(key=lambda x: x[1])
                            best_scene, _ = good_scenes[0]
                            
                            product_id = best_scene["id"]
                            properties = best_scene["properties"]
                            geometry = best_scene.get("geometry", {})
                            
                            metadata = {
                                "acquisition_date": properties.get("datetime", ""),
                                "cloud_cover": properties.get("eo:cloud_cover", properties.get("cloudCover", 0)),
                                "region_name": self._generate_region_name(bbox, properties.get("datetime", "")),
                                "platform": properties.get("platform", "Sentinel-2"),
                                "processing_level": "L2A",  # We're requesting L2A data with DN units
                                "bbox": bbox,
                                "geometry": geometry
                            }
                            
                            logger.info(f"Found Sentinel-2 scene: {product_id}, cloud cover: {metadata['cloud_cover']}%")
                            return product_id, metadata
                        
                    else:
                        logger.warning(f"Catalog search failed: {response.status}")
                        
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error searching catalog: {e}")
                continue
        
        return None, {}
    
    async def _download_processed_data(self, request: DownloadRequest, product_id: str, 
                                     metadata: Dict[str, Any], session) -> Optional[str]:
        """
        Download processed Sentinel-2 data using Copernicus Processing API
        
        Args:
            request: Download request
            product_id: Sentinel-2 product ID
            metadata: Scene metadata
            session: aiohttp session
            
        Returns:
            Path to downloaded file or None
        """
        access_token = await self._get_access_token()
        if not access_token:
            logger.error("No CDSE access token available for download")
            return None

        try:
            self._check_cancelled()
            
            # Determine region name: use provided, then metadata, then generate
            region_name = request.region_name
            if not region_name:
                region_name = metadata.get('region_name')
            if not region_name:
                # Use the original _generate_region_name if no name is available
                # This part of the logic for _generate_region_name might need adjustment
                # if the `bbox` in `metadata` is not always what `_generate_region_name` expects.
                # For now, we assume metadata['bbox'] is appropriate.
                region_name = self._generate_region_name(metadata['bbox'], metadata.get('acquisition_date', ''))
            
            # Ensure metadata is updated with the final region_name
            metadata['region_name'] = region_name

            # Create input folder following the standard structure: input/<region_name>/
            input_folder_path = Path("input") / region_name
            input_folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created input folder: {input_folder_path}")

            # Use acquisition date from metadata for filename, or current date as fallback
            date_str = metadata.get('acquisition_date')
            if date_str:
                try:
                    date_str = datetime.fromisoformat(date_str.replace("Z", "")).strftime("%Y%m%d")
                except ValueError:
                    # Fallback if parsing fails
                    date_str = datetime.now().strftime("%Y%m%d")
            else:
                date_str = datetime.now().strftime("%Y%m%d")
            
            filename = f"{region_name}_{date_str}_sentinel2.tif"
            
            # Save to input/<region_name>/ following the standard folder structure
            # The raw downloaded TIF will be saved in input, then conversion will process to output
            output_dir = input_folder_path
            output_path = output_dir / filename

            # Check if file already exists (cache hit)
            if os.path.exists(output_path):
                logger.info(f"Found cached Sentinel-2 data: {output_path}")
                if self.progress_callback:
                    await self.progress_callback({"message": "Using cached data", "type": "cache_hit", "band": "Sentinel-2"})
                return str(output_path)

            # Processing API request body
            bbox = metadata["bbox"]
            process_body = {
                "input": {
                    "bounds": {
                        "bbox": bbox,
                        "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                    },
                    "data": [{
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": "2024-01-01T00:00:00Z",
                                "to": "2024-12-31T23:59:59Z"
                            },
                            "maxCloudCoverage": 20
                        }
                    }]
                },
                "output": {
                    "width": 512,
                    "height": 512,
                    "responses": [{
                        "identifier": "default",
                        "format": {"type": "image/tiff"}
                    }]
                },
                "evalscript": "//VERSION=3\nfunction setup() {\n    return {\n        input: [{\n            bands: [\"B02\", \"B03\", \"B04\", \"B08\"],\n            units: \"DN\"\n        }],\n        output: {\n            bands: 4,\n            sampleType: \"INT16\"\n        }\n    };\n}\n\nfunction evaluatePixel(sample) {\n    return [\n        sample.B04,\n        sample.B03,\n        sample.B02,\n        sample.B08\n    ];\n}\n"
            }
            
            # Submit processing request
            processing_url = "https://sh.dataspace.copernicus.eu/api/v1/process"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "image/tiff"
            }
            
            logger.info("Submitting Sentinel-2 processing request...")
            if self.progress_callback:
                await self.progress_callback({"message": "Processing satellite data...", "type": "download_start", "band": "Sentinel-2"})
            
            async with session.post(
                processing_url,
                json=process_body,
                headers=headers
            ) as response:
                self._check_cancelled()
                logger.info(f"Processing response status: {response.status}")
                
                if response.status == 200:
                    # Stream download with progress
                    file_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    async with aiofiles.open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            self._check_cancelled()
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            if self.progress_callback and file_size > 0:
                                progress = (downloaded / file_size) * 100
                                await self.progress_callback({
                                    "message": f"Downloading: {progress:.1f}%",
                                    "type": "download_progress",
                                    "progress": progress,
                                    "downloaded_mb": downloaded / (1024 * 1024),
                                    "total_mb": file_size / (1024 * 1024),
                                    "band": "Sentinel-2"
                                })
                    
                    logger.info(f"Downloaded Sentinel-2 data to: {output_path}")
                    if self.progress_callback:
                        await self.progress_callback({"message": "Download completed!", "type": "download_complete", "band": "Sentinel-2"})
                    
                    return str(output_path)
                else:
                    error_text = await response.text()
                    logger.error(f"Processing API error: {response.status} - {error_text}")
                    if self.progress_callback:
                        await self.progress_callback({"message": f"Processing failed: {response.status}", "type": "download_error", "band": "Sentinel-2"})
                    return None
                    
        except asyncio.CancelledError:
            logger.info("Download cancelled")
            if self.progress_callback:
                await self.progress_callback({"message": "Download cancelled", "type": "download_error", "band": "Sentinel-2"})
            raise
        except Exception as e:
            logger.error(f"Download error: {e}")
            if self.progress_callback:
                await self.progress_callback({"message": f"Download error: {str(e)}", "type": "download_error", "band": "Sentinel-2"})
            return None
    
    def _generate_region_name(self, bbox: List[float], datetime_str: str) -> str:
        """Generate a region name from bbox and datetime"""
        # Simple region naming based on coordinates
        center_lat = (bbox[1] + bbox[3]) / 2
        center_lon = (bbox[0] + bbox[2]) / 2
        
        # Determine hemisphere and general region
        lat_suffix = "N" if center_lat >= 0 else "S"
        lon_suffix = "E" if center_lon >= 0 else "W"
        
        region = f"region_{abs(center_lat):.2f}{lat_suffix}_{abs(center_lon):.2f}{lon_suffix}"
        return region.replace(".", "_")
