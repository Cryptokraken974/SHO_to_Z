"""
True DSM Service using SRTM data for proper CHM calculation

SRTM provides actual surface elevation (including vegetation in forested areas)
while Copernicus DEM provides terrain elevation (bare earth).
"""

import os
import requests
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import logging
import rasterio
import numpy as np

logger = logging.getLogger(__name__)

class TrueDSMService:
    """Service for downloading actual Digital Surface Model data for CHM calculation"""
    
    def __init__(self):
        # OpenTopography API for SRTM data (true DSM in forested areas)
        self.opentopo_base_url = "https://portal.opentopography.org/API/globaldem"
        
        # Get authentication from environment
        self.opentopo_username = os.getenv('OPENTOPO_USERNAME')
        self.opentopo_password = os.getenv('OPENTOPO_PASSWORD')
        self.opentopo_api_key = (os.getenv('OPENTOPOGRAPHY_API_KEY') or 
                               os.getenv('OPENTOPO_KEY') or 
                               os.getenv('OPENTOPO_API_KEY'))
    
    async def get_srtm_dsm_for_region(self, 
                                    lat: float, 
                                    lng: float, 
                                    region_name: str,
                                    buffer_km: float = 12.5) -> Dict:
        """
        Download SRTM data as DSM for CHM calculation
        
        SRTM is a C-band radar dataset that provides:
        - Surface elevation in forested areas (includes vegetation)
        - Terrain elevation in open areas (penetrates to ground)
        - This makes it suitable as DSM for forest CHM calculation
        
        Args:
            lat: Latitude of center point
            lng: Longitude of center point  
            region_name: Name of the region
            buffer_km: Buffer distance in kilometers
            
        Returns:
            Dictionary with download results
        """
        try:
            logger.info(f"Starting SRTM DSM download for region {region_name} at ({lat}, {lng})")
            
            # Calculate bounding box
            bbox = self._calculate_bbox_from_center(lat, lng, buffer_km)
            logger.info(f"Calculated bounding box: {bbox}")
            
            # Create output directory
            output_dir = Path("output") / region_name / "lidar" / "DSM"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Download SRTM data via OpenTopography
            result = await self._download_srtm_via_opentopo(bbox, output_dir, region_name)
            
            if result.get("success"):
                logger.info("Successfully downloaded SRTM DSM data")
                return result
            else:
                logger.error(f"Failed to download SRTM DSM: {result.get('error')}")
                return result
                
        except Exception as e:
            logger.error(f"Error in get_srtm_dsm_for_region: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "region_name": region_name
            }
    
    def _calculate_bbox_from_center(self, lat: float, lng: float, buffer_km: float) -> List[float]:
        """Calculate bounding box from center coordinates and buffer distance"""
        # Approximate conversion: 1 degree ≈ 111 km
        lat_buffer = buffer_km / 111.0
        lng_buffer = buffer_km / (111.0 * abs(np.cos(np.radians(lat))))
        
        west = lng - lng_buffer
        east = lng + lng_buffer
        south = lat - lat_buffer
        north = lat + lat_buffer
        
        return [west, south, east, north]
    
    async def _download_srtm_via_opentopo(self, bbox: List[float], 
                                        output_dir: Path, 
                                        region_name: str) -> Dict:
        """Download SRTM data via OpenTopography API"""
        try:
            # OpenTopography API parameters for SRTM GL1 (30m)
            params = {
                'demtype': 'SRTMGL1',  # SRTM GL1 30m (surface elevation in forests)
                'south': bbox[1],
                'north': bbox[3], 
                'west': bbox[0],
                'east': bbox[2],
                'outputFormat': 'GTiff'
            }
            
            # Add authentication
            auth = None
            if self.opentopo_api_key:
                params['API_Key'] = self.opentopo_api_key
                logger.info("Using OpenTopography API key authentication")
            elif self.opentopo_username and self.opentopo_password:
                auth = (self.opentopo_username, self.opentopo_password)
                logger.info("Using OpenTopography username/password authentication")
            else:
                logger.warning("No OpenTopography authentication - may fail for large requests")
            
            logger.info(f"Requesting SRTM DSM data from OpenTopography...")
            response = requests.get(self.opentopo_base_url, params=params, auth=auth, timeout=300)
            
            # Check if response is valid
            is_valid_response = (
                response.status_code == 200 and (
                    response.headers.get('content-type', '').startswith('image/') or
                    response.headers.get('content-type', '').startswith('application/') or
                    (len(response.content) > 4 and response.content[:4] in [b'II*\x00', b'MM\x00*'])
                )
            )
            
            if is_valid_response:
                # Save SRTM DSM file
                output_file = output_dir / f"{region_name}_srtm_dsm_30m.tif"
                
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                file_size = output_file.stat().st_size / (1024 * 1024)
                logger.info(f"SRTM DSM saved: {output_file} ({file_size:.1f} MB)")
                
                # Generate metadata
                metadata = await self._generate_srtm_metadata(output_file, bbox)
                
                return {
                    "success": True,
                    "method": "opentopography_srtm",
                    "file_path": str(output_file),
                    "metadata": metadata,
                    "region_name": region_name,
                    "data_type": "DSM",
                    "source": "SRTM GL1 (C-band radar - surface elevation in forests)",
                    "file_size_mb": file_size
                }
            else:
                error_text = response.text[:500] if response.text else "Unknown error"
                return {
                    "success": False,
                    "error": f"OpenTopography API error {response.status_code}: {error_text}"
                }
                
        except Exception as e:
            logger.error(f"SRTM download failed: {str(e)}")
            return {
                "success": False,
                "error": f"SRTM download error: {str(e)}"
            }
    
    async def _generate_srtm_metadata(self, srtm_file: Path, bbox: List[float]) -> Dict:
        """Generate metadata for the downloaded SRTM DSM"""
        try:
            with rasterio.open(srtm_file) as src:
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
                    "source": "SRTM GL1 (Digital Surface Model)",
                    "resolution": "30m",
                    "data_type": "DSM",
                    "note": "C-band radar data - includes vegetation in forested areas",
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
            logger.error(f"Error generating SRTM metadata: {str(e)}")
            return {}


# Global service instance
true_dsm_service = TrueDSMService()
