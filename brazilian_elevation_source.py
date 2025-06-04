#!/usr/bin/env python3
"""
Brazilian Data Source Implementation for LAZ Terrain Processor
Demonstrates how to integrate TOPODATA and Copernicus DEM for Brazil/Amazon coverage.
"""

import asyncio
import aiohttp
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import geopandas as gpd
from shapely.geometry import Point

# Import existing base classes
import sys
sys.path.append('/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z')

from app.data_acquisition.sources.base import (
    BaseDataSource, DataSourceCapability, DataType, DataResolution,
    DownloadRequest, DownloadResult
)
from app.data_acquisition.utils.coordinates import BoundingBox

class BrazilianElevationSource(BaseDataSource):
    """Enhanced data source for Brazilian and Amazon forest elevation data."""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache"):
        super().__init__(api_key, cache_dir)
        
        # TOPODATA INPE endpoints
        self.topodata_base = "http://www.dsr.inpe.br/topodata/data/"
        self.topodata_formats = {
            "geotiff": "geotiff/",
            "ascii": "txt/", 
            "grid": "grd/"
        }
        
        # Copernicus DEM endpoints
        self.copernicus_base_30m = "https://copernicus-dem-30m.s3.amazonaws.com/"
        self.copernicus_base_90m = "https://copernicus-dem-90m.s3.amazonaws.com/"
        
        # Coverage bounds
        self.brazil_bounds = {
            "west": -74.0,   # Western Amazon
            "east": -30.0,   # Atlantic coast
            "south": -34.0,  # Southern border
            "north": 5.0     # Northern border
        }
    
    @property
    def capabilities(self) -> DataSourceCapability:
        return DataSourceCapability(
            data_types=[DataType.ELEVATION],
            resolutions=[DataResolution.HIGH, DataResolution.MEDIUM, DataResolution.LOW],
            coverage_areas=["Brazil", "Amazon", "South America", "Global"],
            max_area_km2=10000.0,  # 100km x 100km max
            requires_api_key=False
        )
    
    @property
    def name(self) -> str:
        return "brazilian_elevation"
    
    def _check_brazil_coverage(self, bbox: BoundingBox) -> str:
        """Check if coordinates are within Brazilian territory."""
        center_lat = (bbox.north + bbox.south) / 2
        center_lng = (bbox.east + bbox.west) / 2
        
        # Check if within Brazil bounds
        if (self.brazil_bounds["west"] <= center_lng <= self.brazil_bounds["east"] and
            self.brazil_bounds["south"] <= center_lat <= self.brazil_bounds["north"]):
            
            # Further classify region
            if center_lng <= -60 and center_lat >= -15:
                return "amazon"  # Amazon rainforest region
            elif center_lng <= -50:
                return "west_brazil"  # Western Brazil
            else:
                return "east_brazil"  # Eastern Brazil
        
        # Check if in broader South America
        elif -85 <= center_lng <= -30 and -60 <= center_lat <= 15:
            return "south_america"
        
        return "global"
    
    def _get_topodata_tile_name(self, bbox: BoundingBox) -> str:
        """Generate TOPODATA tile name from coordinates."""
        # TOPODATA uses 1° lat x 1.5° lon tiles
        # Format: LAHLON where LA=lat, H=hemisphere, LON=longitude
        
        center_lat = (bbox.north + bbox.south) / 2
        center_lng = (bbox.east + bbox.west) / 2
        
        # Calculate tile boundaries
        lat_int = int(abs(center_lat))
        lng_int = int(abs(center_lng))
        
        # Hemisphere
        lat_hem = "S" if center_lat < 0 else "N"
        
        # Longitude format (nn5 for .5 degrees, nn_ for integer)
        lng_frac = abs(center_lng) - lng_int
        if 0.25 <= lng_frac < 0.75:
            lng_str = f"{lng_int:02d}5"
        else:
            lng_str = f"{lng_int:02d}_"
        
        # Construct tile name
        tile_name = f"{lat_int:02d}{lat_hem}{lng_str}"
        return tile_name
    
    def _get_copernicus_tile_name(self, bbox: BoundingBox) -> str:
        """Generate Copernicus DEM tile name from coordinates."""
        # Copernicus uses 1° x 1° tiles
        # Format: Copernicus_DSM_COG_10_N00_00_E000_00_DEM.tif
        
        center_lat = (bbox.north + bbox.south) / 2
        center_lng = (bbox.east + bbox.west) / 2
        
        # Calculate tile coordinates (lower-left corner)
        lat_tile = int(center_lat) if center_lat >= 0 else int(center_lat) - 1
        lng_tile = int(center_lng) if center_lng >= 0 else int(center_lng) - 1
        
        # Format coordinates
        lat_hem = "N" if lat_tile >= 0 else "S"
        lng_hem = "E" if lng_tile >= 0 else "W"
        
        lat_str = f"{abs(lat_tile):02d}_00"
        lng_str = f"{abs(lng_tile):03d}_00"
        
        tile_name = f"Copernicus_DSM_COG_10_{lat_hem}{lat_str}_{lng_hem}{lng_str}_DEM.tif"
        return tile_name
    
    async def check_availability(self, request: DownloadRequest) -> bool:
        """Check if elevation data is available for the bounding box."""
        if not self._validate_request(request):
            return False
        
        # Only support elevation data
        if request.data_type != DataType.ELEVATION:
            return False
        
        coverage = self._check_brazil_coverage(request.bbox)
        
        # Available for Brazil, South America, and global
        return coverage in ["amazon", "west_brazil", "east_brazil", "south_america", "global"]
    
    async def estimate_size(self, request: DownloadRequest) -> float:
        """Estimate download size based on area and resolution."""
        area_deg = (request.bbox.east - request.bbox.west) * (request.bbox.north - request.bbox.south)
        area_km2 = area_deg * 111 * 111  # Rough conversion to km²
        
        # Estimate based on resolution
        if request.resolution == DataResolution.HIGH:
            size_mb = area_km2 * 2.0  # ~2MB per km² for 30m data
        elif request.resolution == DataResolution.MEDIUM:
            size_mb = area_km2 * 1.0  # ~1MB per km² for 30m data
        else:
            size_mb = area_km2 * 0.5  # ~0.5MB per km² for 90m data
        
        return min(size_mb, request.max_file_size_mb)
    
    async def download(self, request: DownloadRequest) -> DownloadResult:
        """Download elevation data using appropriate source."""
        try:
            if not await self.check_availability(request):
                return DownloadResult(
                    success=False,
                    error_message="Data not available for this region"
                )
            
            # Check cache first
            cache_path = self._get_cache_path(request)
            if cache_path.exists():
                file_size = cache_path.stat().st_size / (1024 * 1024)
                
                input_folder = self._create_input_folder(request)
                input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
                
                return DownloadResult(
                    success=True,
                    file_path=str(input_file_path),
                    file_size_mb=file_size,
                    resolution_m=self._get_resolution_meters(request.resolution)
                )
            
            # Route to appropriate data source
            coverage = self._check_brazil_coverage(request.bbox)
            
            if coverage in ["amazon", "west_brazil", "east_brazil"]:
                return await self._download_topodata(request, cache_path)
            else:
                return await self._download_copernicus(request, cache_path)
                
        except Exception as e:
            return DownloadResult(
                success=False,
                error_message=f"Brazilian elevation download failed: {str(e)}"
            )
    
    async def _download_topodata(self, request: DownloadRequest, cache_path: Path) -> DownloadResult:
        """Download elevation data from TOPODATA (INPE)."""
        try:
            tile_name = self._get_topodata_tile_name(request.bbox)
            
            # Construct download URL for GeoTIFF format
            # TOPODATA altitude files end with 'ZN' suffix
            file_name = f"{tile_name}ZN.zip"
            url = f"{self.topodata_base}{self.topodata_formats['geotiff']}{file_name}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Save to cache
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(cache_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        file_size = cache_path.stat().st_size / (1024 * 1024)
                        
                        # Copy to input folder
                        input_folder = self._create_input_folder(request)
                        input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
                        
                        return DownloadResult(
                            success=True,
                            file_path=str(input_file_path),
                            file_size_mb=file_size,
                            resolution_m=30.0,  # TOPODATA refined resolution
                            metadata={
                                'source': 'TOPODATA (INPE)',
                                'tile': tile_name,
                                'data_type': 'elevation',
                                'format': 'GeoTIFF',
                                'original_resolution': '30m (refined from SRTM)',
                                'coverage': 'Brazil/Amazon',
                                'url': url
                            }
                        )
                    else:
                        # Fallback to Copernicus if TOPODATA unavailable
                        return await self._download_copernicus(request, cache_path)
            
        except Exception as e:
            # Fallback to Copernicus on any error
            return await self._download_copernicus(request, cache_path)
    
    async def _download_copernicus(self, request: DownloadRequest, cache_path: Path) -> DownloadResult:
        """Download elevation data from Copernicus DEM."""
        try:
            tile_name = self._get_copernicus_tile_name(request.bbox)
            
            # Choose resolution based on request
            if request.resolution == DataResolution.LOW:
                base_url = self.copernicus_base_90m
                resolution = 90.0
            else:
                base_url = self.copernicus_base_30m
                resolution = 30.0
            
            url = f"{base_url}{tile_name}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Save to cache
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(cache_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        file_size = cache_path.stat().st_size / (1024 * 1024)
                        
                        # Copy to input folder
                        input_folder = self._create_input_folder(request)
                        input_file_path = self._copy_to_input_folder(cache_path, input_folder, request)
                        
                        return DownloadResult(
                            success=True,
                            file_path=str(input_file_path),
                            file_size_mb=file_size,
                            resolution_m=resolution,
                            metadata={
                                'source': 'Copernicus DEM (ESA)',
                                'tile': tile_name,
                                'data_type': 'elevation',
                                'format': 'GeoTIFF (COG)',
                                'resolution': f'{resolution}m',
                                'coverage': 'Global',
                                'url': url
                            }
                        )
                    else:
                        return DownloadResult(
                            success=False,
                            error_message=f"Copernicus DEM API error {response.status}: {await response.text()}"
                        )
            
        except Exception as e:
            return DownloadResult(
                success=False,
                error_message=f"Copernicus DEM download failed: {str(e)}"
            )
    
    def _get_resolution_meters(self, resolution: DataResolution) -> float:
        """Get resolution in meters for Brazilian sources."""
        if resolution == DataResolution.HIGH:
            return 30.0  # TOPODATA or Copernicus 30m
        elif resolution == DataResolution.MEDIUM:
            return 30.0  # Copernicus 30m
        else:
            return 90.0  # Copernicus 90m
    
    def _create_input_folder(self, request: DownloadRequest) -> Path:
        """Create descriptive folder in input directory."""
        if request.region_name:
            folder_name = request.region_name
        else:
            center_lat = (request.bbox.north + request.bbox.south) / 2
            center_lng = (request.bbox.east + request.bbox.west) / 2
            
            # Add region identifier
            coverage = self._check_brazil_coverage(request.bbox)
            region_prefix = {
                "amazon": "Amazon",
                "west_brazil": "WestBrazil", 
                "east_brazil": "EastBrazil",
                "south_america": "SouthAmerica",
                "global": "Global"
            }.get(coverage, "Brazil")
            
            lat_dir = 'S' if center_lat < 0 else 'N'
            lng_dir = 'W' if center_lng < 0 else 'E'
            folder_name = f"{region_prefix}_{abs(center_lat):.2f}{lat_dir}_{abs(center_lng):.2f}{lng_dir}"
        
        input_folder = Path("input") / folder_name
        input_folder.mkdir(parents=True, exist_ok=True)
        return input_folder
    
    def _copy_to_input_folder(self, cache_path: Path, input_folder: Path, request: DownloadRequest) -> Path:
        """Copy file from cache to input folder with descriptive name."""
        import shutil
        
        center_lat = (request.bbox.north + request.bbox.south) / 2
        center_lng = (request.bbox.east + request.bbox.west) / 2
        coverage = self._check_brazil_coverage(request.bbox)
        
        # Generate descriptive filename
        if request.region_name:
            base_file_name = f"{request.region_name}_elevation"
        else:
            lat_dir = 'S' if center_lat < 0 else 'N'
            lng_dir = 'W' if center_lng < 0 else 'E'
            region = coverage.replace("_", "").title()
            base_file_name = f"{region}_{abs(center_lat):.2f}{lat_dir}_{abs(center_lng):.2f}{lng_dir}_elevation"
        
        filename = f"{base_file_name}.tif"
        input_file_path = input_folder / filename
        shutil.copy2(cache_path, input_file_path)
        
        # Create metadata file
        metadata_filename = f"metadata_{base_file_name}.txt"
        metadata_path = input_folder / metadata_filename
        with open(metadata_path, 'w') as f:
            f.write(f"# Brazilian Elevation Data\n")
            f.write(f"# Region: {coverage.replace('_', ' ').title()}\n")
            f.write(f"# Center: {center_lat:.6f}, {center_lng:.6f}\n")
            f.write(f"# Resolution: {self._get_resolution_meters(request.resolution)}m\n")
            f.write(f"# Data Type: Elevation (DEM)\n")
            f.write(f"# Format: GeoTIFF\n")
            f.write(f"# Bounds: {request.bbox.west}, {request.bbox.south}, {request.bbox.east}, {request.bbox.north}\n")
            f.write(f"# File: {filename}\n")
        
        return input_file_path

# Example usage and testing
async def test_brazilian_coverage():
    """Test Brazilian data source with sample coordinates."""
    print("🇧🇷 TESTING BRAZILIAN ELEVATION DATA SOURCE")
    print("=" * 50)
    
    source = BrazilianElevationSource()
    
    # Test coordinates
    test_locations = [
        # Amazon rainforest
        {
            "name": "Amazon (Manaus)",
            "bbox": BoundingBox(west=-60.1, south=-3.2, east=-59.9, north=-3.0),
            "expected": "amazon"
        },
        # São Paulo area
        {
            "name": "São Paulo",
            "bbox": BoundingBox(west=-46.8, south=-23.7, east=-46.6, north=-23.5),
            "expected": "east_brazil"
        },
        # Pantanal wetlands
        {
            "name": "Pantanal",
            "bbox": BoundingBox(west=-57.1, south=-19.1, east=-56.9, north=-18.9),
            "expected": "west_brazil"
        }
    ]
    
    for location in test_locations:
        print(f"\n📍 Testing: {location['name']}")
        print(f"   Coordinates: {location['bbox']}")
        
        coverage = source._check_brazil_coverage(location['bbox'])
        print(f"   Detected coverage: {coverage}")
        print(f"   Expected: {location['expected']}")
        print(f"   ✅ Match: {coverage == location['expected']}")
        
        # Test tile naming
        topodata_tile = source._get_topodata_tile_name(location['bbox'])
        copernicus_tile = source._get_copernicus_tile_name(location['bbox'])
        print(f"   TOPODATA tile: {topodata_tile}")
        print(f"   Copernicus tile: {copernicus_tile}")
        
        # Test availability
        request = DownloadRequest(
            bbox=location['bbox'],
            data_type=DataType.ELEVATION,
            resolution=DataResolution.HIGH,
            max_file_size_mb=100.0
        )
        
        available = await source.check_availability(request)
        print(f"   Available: {available}")

if __name__ == "__main__":
    asyncio.run(test_brazilian_coverage())
