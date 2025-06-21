"""
Configuration management for the LAZ Terrain Processor with Data Acquisition
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Base directories
    cache_dir: str = "data/cache"
    output_dir: str = "output"
    processed_dir: str = "data/processed"
    
    # API Keys (optional)
    opentopography_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # OpenTopography credentials for elevation data
    opentopo_username: Optional[str] = None
    opentopo_password: Optional[str] = None
    opentopo_api_key: Optional[str] = None
    opentopo_key: Optional[str] = None  # Alternative field name for API key
    
    # Elevation download settings
    elevation_bbox_buffer: float = 0.01
    elevation_timeout: int = 300
    elevation_max_retries: int = 3
    
    copernicus_username: Optional[str] = None
    copernicus_password: Optional[str] = None
    cdse_token: Optional[str] = None  # Copernicus Data Space Ecosystem access token (legacy)
    cdse_client_id: Optional[str] = None  # Copernicus Data Space Ecosystem OAuth2 client ID
    cdse_client_secret: Optional[str] = None  # Copernicus Data Space Ecosystem OAuth2 client secret
    earthdata_username: Optional[str] = None
    earthdata_password: Optional[str] = None
    
    # Development settings
    debug: bool = False
    use_mock_sources: bool = False
    
    # Default acquisition settings
    default_buffer_km: float = 1.0
    max_file_size_mb: float = 500.0
    cache_expiry_days: int = 30
    max_concurrent_downloads: int = 3
    
    # Data source priorities (higher number = higher priority)
    source_priorities: dict = {
        "opentopography": 3,
        "sentinel2": 2,
        "ornl_daac": 1
    }
    
    # Regional settings for Brazil
    brazil_bounds: dict = {
        "north": 5.27,
        "south": -33.75,
        "east": -28.65,
        "west": -73.99
    }
    
    # UTM zones for Brazil (simplified)
    brazil_utm_zones: dict = {
        "west_boundary": -73.99,
        "east_boundary": -28.65,
        "zones": [18, 19, 20, 21, 22, 23, 24, 25]  # Common Brazilian UTM zones
    }
    
    # File size limits by data type
    max_file_sizes: dict = {
        "srtm_dem": 100,      # MB
        "sentinel2": 300,     # MB
        "lidar": 200,         # MB
        "environmental": 50   # MB
    }
    
    # Supported file formats
    supported_formats: dict = {
        "elevation": [".tif", ".tiff", ".dem", ".asc"],
        "imagery": [".tif", ".tiff", ".jp2", ".png"],
        "lidar": [".laz", ".las", ".ply"],
        "vector": [".shp", ".geojson", ".kml"]
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_prefix = ""

class DataSourceConfig:
    """Configuration for individual data sources"""
    
    OPENTOPOGRAPHY = {
        "name": "OpenTopography",
        "base_url": "https://cloud.sdsc.edu/v1/opentopodata",
        "datasets": {
            "srtm30m": {
                "name": "SRTM 30m",
                "resolution_m": 30,
                "coverage": "global",
                "max_area_km2": 100
            },
            "srtm90m": {
                "name": "SRTM 90m", 
                "resolution_m": 90,
                "coverage": "global",
                "max_area_km2": 500
            }
        },
        "requires_api_key": False,
        "rate_limit": 300  # requests per hour
    }
    
    SENTINEL2 = {
        "name": "Sentinel-2",
        "base_url": "https://scihub.copernicus.eu/dhus",
        "datasets": {
            "l1c": {
                "name": "Level-1C",
                "resolution_m": 10,
                "coverage": "global", 
                "max_area_km2": 50,
                "cloud_cover_max": 20
            },
            "l2a": {
                "name": "Level-2A",
                "resolution_m": 10,
                "coverage": "global",
                "max_area_km2": 50,
                "cloud_cover_max": 20
            }
        },
        "requires_api_key": True,
        "rate_limit": 200  # requests per hour
    }
    
    ORNL_DAAC = {
        "name": "ORNL DAAC",
        "base_url": "https://daac.ornl.gov/daacdata",
        "datasets": {
            "biomass": {
                "name": "Biomass",
                "resolution_m": 100,
                "coverage": "global",
                "max_area_km2": 200
            },
            "vegetation": {
                "name": "Vegetation Indices",
                "resolution_m": 250,
                "coverage": "global", 
                "max_area_km2": 300
            }
        },
        "requires_api_key": False,
        "rate_limit": 500  # requests per hour
    }

def get_settings() -> Settings:
    """Get application settings with caching"""
    if not hasattr(get_settings, '_settings'):
        get_settings._settings = Settings()
        
        # Ensure directories exist
        for dir_path in [
            get_settings._settings.cache_dir,
            get_settings._settings.output_dir, 
            get_settings._settings.processed_dir
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    return get_settings._settings

def get_data_source_config(source_name: str) -> dict:
    """Get configuration for a specific data source"""
    source_configs = {
        "opentopography": DataSourceConfig.OPENTOPOGRAPHY,
        "sentinel2": DataSourceConfig.SENTINEL2,
        "ornl_daac": DataSourceConfig.ORNL_DAAC
    }
    
    return source_configs.get(source_name.lower(), {})

def validate_api_keys() -> dict:
    """Check which API keys are available"""
    settings = get_settings() # This call might be part of the problem if get_settings() is not fully initialized
    
    return {
        "opentopography": settings.opentopography_api_key is not None,
        "copernicus": all([
            settings.copernicus_username,
            settings.copernicus_password
        ]),
        "earthdata": all([
            settings.earthdata_username,
            settings.earthdata_password
        ])
    }

def get_utm_zone_for_longitude(longitude: float) -> int:
    """Get UTM zone for a given longitude in Brazil"""
    settings = get_settings() # This call might be part of the problem
    
    # Simplified UTM zone calculation for Brazil
    if longitude < -66:
        return 18
    elif longitude < -60:
        return 19
    elif longitude < -54:
        return 20
    elif longitude < -48:
        return 21
    elif longitude < -42:
        return 22
    elif longitude < -36:
        return 23
    elif longitude < -30:
        return 24
    else:
        return 25

def is_coordinate_in_brazil(lat: float, lng: float) -> bool:
    """Check if coordinates are within Brazil boundaries"""
    settings = get_settings() # This call might be part of the problem
    bounds = settings.brazil_bounds
    
    return (
        bounds["south"] <= lat <= bounds["north"] and
        bounds["west"] <= lng <= bounds["east"]
    )
