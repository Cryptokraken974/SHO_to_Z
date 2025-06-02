"""USGS 3DEP data source for LiDAR point cloud data."""

import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
from datetime import datetime

from .base import (
    BaseDataSource, DataSourceCapability, DataType, DataResolution,
    DownloadRequest, DownloadResult
)
from ..utils.coordinates import BoundingBox

class USGS3DEPSource(BaseDataSource):
    """USGS 3D Elevation Program (3DEP) data source for LiDAR point clouds."""
    
    # Note: USGS 3DEP data is available through various endpoints
    # This is a simplified implementation for demonstration
    BASE_URL = "https://cloud.sdsc.edu/v1/usgs"
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache"):
        super().__init__(api_key, cache_dir)
        self._session = None
    
    @property
    def capabilities(self) -> DataSourceCapability:
        return DataSourceCapability(
            data_types=[DataType.ELEVATION, DataType.LAZ],  # Added LAZ type
            resolutions=[DataResolution.HIGH, DataResolution.MEDIUM],
            coverage_areas=["United States", "Puerto Rico", "US Territories"],
            max_area_km2=100.0,  # Smaller areas for LiDAR data
            requires_api_key=False
        )
    
    @property
    def name(self) -> str:
        return "usgs_3dep"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def check_availability(self, request: DownloadRequest) -> bool:
        """Check if USGS 3DEP data is available for the bounding box."""
        if not self._validate_request(request):
            return False
        
        # Check if coordinates are within US boundaries (simplified check)
        center_lat = (request.bbox.north + request.bbox.south) / 2
        center_lng = (request.bbox.east + request.bbox.west) / 2
        
        # US mainland bounds (simplified)
        if (24.0 <= center_lat <= 49.0 and -125.0 <= center_lng <= -66.0):
            return True
        
        # Alaska
        if (55.0 <= center_lat <= 72.0 and -180.0 <= center_lng <= -129.0):
            return True
            
        # Hawaii and territories (simplified)
        if (18.0 <= center_lat <= 22.0 and -162.0 <= center_lng <= -154.0):
            return True
            
        return False
    
    async def estimate_size(self, request: DownloadRequest) -> float:
        """Estimate download size for LiDAR data."""
        if not await self.check_availability(request):
            return 0.0
            
        bbox_area = request.bbox.area_km2()
        
        if request.data_type == DataType.LAZ:
            # LiDAR point clouds are much larger
            # Estimate ~50-200 MB per km² depending on point density
            if request.resolution == DataResolution.HIGH:
                size_per_km2 = 200.0  # High density LiDAR
            else:
                size_per_km2 = 100.0  # Medium density LiDAR
        else:
            # DEM data is smaller
            size_per_km2 = 5.0
        
        total_size = bbox_area * size_per_km2
        return min(total_size, request.max_file_size_mb)
    
    async def download(self, request: DownloadRequest, progress_callback=None) -> DownloadResult:
        """Download USGS 3DEP data."""
        try:
            if not await self.check_availability(request):
                return DownloadResult(
                    success=False,
                    error_message="USGS 3DEP data not available for this location (US only)"
                )
            
            # Send initial progress update
            if progress_callback:
                await progress_callback({
                    "type": "download_started",
                    "provider": "USGS 3DEP",
                    "message": "Starting USGS 3DEP data preparation..."
                })
            
            # For now, return a note about manual download
            # In a real implementation, this would query USGS APIs
            
            # Create input folder with descriptive name
            input_folder = self._create_input_folder(request)
            
            # Progress update for file generation
            if progress_callback:
                await progress_callback({
                    "type": "download_progress",
                    "message": "Generating download instructions...",
                    "progress": 50
                })
            
            # Create information file about where to get the real data
            info_file = self._create_info_file(input_folder, request)
            
            # Brief pause to simulate processing
            await asyncio.sleep(0.5)
            
            # Final progress update
            if progress_callback:
                await progress_callback({
                    "type": "download_completed",
                    "message": "Download instructions file created",
                    "progress": 100
                })
            
            return DownloadResult(
                success=True,
                file_path=str(info_file),
                file_size_mb=0.001,  # Just the info file
                resolution_m=1.0 if request.resolution == DataResolution.HIGH else 2.0,
                metadata={
                    'source': 'USGS 3DEP',
                    'note': 'Manual download required - see info file for instructions',
                    'bbox': {
                        'west': request.bbox.west,
                        'south': request.bbox.south,
                        'east': request.bbox.east,
                        'north': request.bbox.north
                    }
                }
            )
                    
        except Exception as e:
            if progress_callback:
                await progress_callback({
                    "type": "download_error",
                    "message": f"USGS 3DEP error: {str(e)}"
                })
            return DownloadResult(
                success=False,
                error_message=f"USGS 3DEP download failed: {str(e)}"
            )
    
    def _create_input_folder(self, request: DownloadRequest) -> Path:
        """Create descriptive folder in input directory."""
        if request.region_name:
            folder_name = request.region_name
        else:
            center_lat = (request.bbox.north + request.bbox.south) / 2
            center_lng = (request.bbox.east + request.bbox.west) / 2
            lat_dir = 'S' if center_lat < 0 else 'N'
            lng_dir = 'W' if center_lng < 0 else 'E'
            region_name = f"{abs(center_lat):.2f}{lat_dir}_{abs(center_lng):.2f}{lng_dir}"
            folder_name = region_name
        
        # Create main region folder
        input_folder = Path("input") / folder_name
        input_folder.mkdir(parents=True, exist_ok=True)
        
        # Create lidar subfolder and return it
        lidar_folder = input_folder / "lidar"
        lidar_folder.mkdir(parents=True, exist_ok=True)
        print(f"CREATED FOLDER (usgs_3dep): {lidar_folder}")
        
        return lidar_folder
    
    def _create_info_file(self, input_folder: Path, request: DownloadRequest) -> Path:
        """Create information file with download instructions."""
        info_file_name = "USGS_3DEP_download_instructions.txt"
        if request.region_name:
            info_file_name = f"{request.region_name}_USGS_3DEP_download_instructions.txt"
            
        # input_folder is already the lidar subfolder
        info_file = input_folder / info_file_name
        
        with open(info_file, 'w') as f:
            f.write("# USGS 3D Elevation Program (3DEP) Data Download Instructions\n")
            f.write("#" + "="*60 + "\n\n")
            f.write("LOCATION INFORMATION:\n")
            if request.region_name:
                f.write(f"  Region Name: {request.region_name}\n")
            center_lat = (request.bbox.north + request.bbox.south) / 2
            center_lng = (request.bbox.east + request.bbox.west) / 2
            f.write(f"  Center Coordinates: {center_lat:.6f}, {center_lng:.6f}\n")
            f.write(f"  Bounding Box: {request.bbox.west:.6f}, {request.bbox.south:.6f}, {request.bbox.east:.6f}, {request.bbox.north:.6f}\n")
            f.write(f"  Data Type: {request.data_type.value}\n")
            f.write(f"  Resolution: {request.resolution.value if request.resolution else 'medium'}\n\n")
            
            f.write("MANUAL DOWNLOAD OPTIONS:\n\n")
            
            f.write("1. USGS National Map Downloader:\n")
            f.write("   https://apps.nationalmap.gov/downloader/\n")
            f.write("   - Select 'Elevation Products (3DEP)'\n")
            f.write("   - Choose 'Lidar Point Cloud (LPC)' for LAZ files\n")
            f.write("   - Or choose '1/3 arc-second DEM' for elevation rasters\n")
            f.write("   - Enter your coordinates in the search box\n")
            f.write("   - Download available tiles\n\n")
            
            f.write("2. USGS Earth Explorer:\n")
            f.write("   https://earthexplorer.usgs.gov/\n")
            f.write("   - Register for free account\n")
            f.write("   - Search by coordinates or address\n")
            f.write("   - Filter by 'Digital Elevation' category\n")
            f.write("   - Look for 'USGS 3DEP' datasets\n\n")
            
            f.write("3. OpenTopography (for processed DEMs):\n")
            f.write("   https://portal.opentopography.org/raster\n")
            f.write("   - Select 'USGS NED' or 'SRTM' datasets\n")
            f.write("   - Enter bounding box coordinates\n")
            f.write("   - Download GeoTIFF format\n\n")
            
            f.write("4. State/Local LiDAR Portals:\n")
            f.write("   Many states have their own LiDAR data portals:\n")
            f.write("   - Oregon: https://www.oregongeology.org/lidar/\n")
            f.write("   - Washington: https://lidarportal.dnr.wa.gov/\n")
            f.write("   - California: https://cloud.sdsc.edu/v1/opentopoapi/\n\n")
            
            f.write("COORDINATE REFERENCE:\n")
            f.write(f"  Decimal Degrees: {center_lat:.6f}, {center_lng:.6f}\n")
            f.write(f"  Google Maps Link: https://www.google.com/maps/@{center_lat},{center_lng},15z\n\n")
            
            f.write("NOTES:\n")
            f.write("- LAZ files are compressed LiDAR point clouds\n")
            f.write("- Coverage varies by location and acquisition date\n")
            f.write("- Most urban and forested areas have good coverage\n")
            f.write("- Check multiple sources if data is not available from one\n")
            f.write(f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Also create a metadata file in the lidar subfolder
        lat_dir = 'S' if center_lat < 0 else 'N'
        lng_dir = 'W' if center_lng < 0 else 'E'
        region_name = f"{abs(center_lat):.2f}{lat_dir}_{abs(center_lng):.2f}{lng_dir}"
        metadata_path = input_folder / f"metadata_{region_name}.txt"
        
        with open(metadata_path, 'w') as f:
            f.write(f"# USGS 3DEP Elevation Data\n")
            f.write(f"# Region: {region_name}\n")
            f.write(f"# Data Type: Instructions for {request.data_type.value}\n")
            f.write(f"# Instructions File: {info_file_name}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Center: {center_lat:.6f}, {center_lng:.6f}\n")
        
        return info_file
    
    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
