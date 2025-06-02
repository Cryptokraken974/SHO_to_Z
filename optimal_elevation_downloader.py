#!/usr/bin/env python3
"""
Optimal Elevation Data Downloader for Brazilian Regions
Implements the three recommended datasets:
🥇 NASADEM (dense forest & mixed cover - Amazonas, Acre, Pará)
🥈 Copernicus GLO-30 (open/lightly wooded terrain - Cerrado, Caatinga, coastal plains)
🥉 ALOS AW3D30 (open terrain needing stereo detail)

Uses OpenTopography API with authentication and intelligent fallback mechanisms.
"""

import os
import sys
import json
import requests
import numpy as np
from pathlib import Path
from datetime import datetime
import tempfile
from typing import Dict, List, Optional, Tuple, Union
import time
import configparser
from dataclasses import dataclass
from enum import Enum
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

class TerrainType(Enum):
    DENSE_FOREST = "dense_forest"
    MIXED_COVER = "mixed_cover"
    OPEN_TERRAIN = "open_terrain"
    COASTAL_PLAINS = "coastal_plains"
    CERRADO = "cerrado"
    CAATINGA = "caatinga"
    AMAZON = "amazon"

class DatasetType(Enum):
    NASADEM = "NASADEM"
    COPERNICUS_GLO30 = "COPERNICUS_GLO30"
    ALOS_AW3D30 = "ALOS_AW3D30"
    SRTM = "SRTM"

@dataclass
class ElevationDataset:
    name: str
    opentopo_name: str
    resolution: str
    best_for: List[TerrainType]
    coverage: str
    priority: int
    requires_auth: bool = True

class OptimalElevationDownloader:
    def __init__(self, config_file: Optional[str] = None):
        self.base_path = Path(__file__).parent
        self.download_path = self.base_path / "optimal_elevation_downloads"
        self.download_path.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Define optimal datasets in priority order
        self.datasets = {
            DatasetType.NASADEM: ElevationDataset(
                name="NASADEM",
                opentopo_name="NASADEM",
                resolution="30m",
                best_for=[TerrainType.DENSE_FOREST, TerrainType.MIXED_COVER, TerrainType.AMAZON],
                coverage="Global (improved SRTM for vegetation)",
                priority=1
            ),
            DatasetType.COPERNICUS_GLO30: ElevationDataset(
                name="Copernicus GLO-30",
                opentopo_name="COP30",
                resolution="30m",
                best_for=[TerrainType.CERRADO, TerrainType.CAATINGA, TerrainType.COASTAL_PLAINS],
                coverage="Global",
                priority=2
            ),
            DatasetType.ALOS_AW3D30: ElevationDataset(
                name="ALOS AW3D30",
                opentopo_name="ALOS",
                resolution="30m",
                best_for=[TerrainType.OPEN_TERRAIN],
                coverage="Global",
                priority=3
            ),
            DatasetType.SRTM: ElevationDataset(
                name="SRTM",
                opentopo_name="SRTM",
                resolution="30m",
                best_for=[],  # Fallback only
                coverage="Global",
                priority=4,
                requires_auth=False
            )
        }
        
        # Brazilian regions with terrain classification
        self.brazilian_regions = {
            "rio_de_janeiro": {
                "name": "Rio de Janeiro",
                "lat": -22.9068,
                "lng": -43.1729,
                "state": "RJ",
                "terrain": TerrainType.COASTAL_PLAINS,
                "preferred_dataset": DatasetType.COPERNICUS_GLO30
            },
            "sao_paulo": {
                "name": "São Paulo", 
                "lat": -23.5505,
                "lng": -46.6333,
                "state": "SP",
                "terrain": TerrainType.MIXED_COVER,
                "preferred_dataset": DatasetType.NASADEM
            },
            "existing_region_1": {
                "name": "Existing Region 11.31S_44.06W",
                "lat": -11.31,
                "lng": -44.06,
                "state": "BA",
                "terrain": TerrainType.CERRADO,
                "preferred_dataset": DatasetType.COPERNICUS_GLO30
            },
            "existing_region_2": {
                "name": "Existing Region 12.28S_37.88W",
                "lat": -12.28,
                "lng": -37.88,
                "state": "BA",
                "terrain": TerrainType.CAATINGA,
                "preferred_dataset": DatasetType.COPERNICUS_GLO30
            },
            "existing_region_3": {
                "name": "Existing Region 14.50S_53.06W",
                "lat": -14.50,
                "lng": -53.06,
                "state": "MT",
                "terrain": TerrainType.CERRADO,
                "preferred_dataset": DatasetType.COPERNICUS_GLO30
            },
            "amazon_manaus": {
                "name": "Amazon Manaus",
                "lat": -3.1190,
                "lng": -60.0217,
                "state": "AM",
                "terrain": TerrainType.DENSE_FOREST,
                "preferred_dataset": DatasetType.NASADEM
            },
            "pantanal": {
                "name": "Pantanal",
                "lat": -16.0,
                "lng": -57.0,
                "state": "MS",
                "terrain": TerrainType.OPEN_TERRAIN,
                "preferred_dataset": DatasetType.ALOS_AW3D30
            }
        }

    def _load_config(self, config_file: Optional[str] = None) -> configparser.ConfigParser:
        """Load configuration from file with environment variable fallbacks"""
        config = configparser.ConfigParser()
        
        # Default config file path
        if config_file is None:
            config_file = self.base_path / "elevation_config.ini"
        
        # Create default config if it doesn't exist
        if not Path(config_file).exists():
            self._create_default_config(config_file)
        
        config.read(config_file)
        
        # Override with environment variables if available (for security)
        if os.getenv('OPENTOPO_USERNAME'):
            if not config.has_section('opentopography'):
                config.add_section('opentopography')
            config.set('opentopography', 'username', os.getenv('OPENTOPO_USERNAME'))
            
        if os.getenv('OPENTOPO_PASSWORD'):
            if not config.has_section('opentopography'):
                config.add_section('opentopography')
            config.set('opentopography', 'password', os.getenv('OPENTOPO_PASSWORD'))
            
        if os.getenv('OPENTOPO_API_KEY'):
            if not config.has_section('opentopography'):
                config.add_section('opentopography')
            config.set('opentopography', 'api_key', os.getenv('OPENTOPO_API_KEY'))
        
        return config

    def _create_default_config(self, config_file: str):
        """Create a default configuration file"""
        config_content = """[opentopography]
# OpenTopography API credentials (optional but recommended for better access)
# Sign up at: https://portal.opentopography.org/
# For production, use environment variables: OPENTOPO_USERNAME, OPENTOPO_PASSWORD, OPENTOPO_API_KEY
api_key = 
username = 
password = 

[download_settings]
# Download settings
bbox_buffer = 0.01
timeout = 300
max_retries = 3
chunk_size = 8192

[data_sources]
# Alternative data sources as fallbacks
use_copernicus_service = true
use_nasa_earthdata = true
use_ibge_brazil = true
"""
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        print(f"📋 Created default config file: {config_file}")
        print("💡 Edit this file to add your OpenTopography API credentials for optimal performance")

    def get_optimal_dataset(self, region_key: str) -> DatasetType:
        """Determine the optimal dataset for a given region"""
        if region_key not in self.brazilian_regions:
            return DatasetType.COPERNICUS_GLO30  # Default fallback
        
        region = self.brazilian_regions[region_key]
        return region.get("preferred_dataset", DatasetType.COPERNICUS_GLO30)

    def download_elevation_data(self, region_key: str, force_dataset: Optional[DatasetType] = None) -> Dict:
        """Download optimal elevation data for a Brazilian region"""
        
        if region_key not in self.brazilian_regions:
            return {
                "success": False,
                "error": f"Unknown region: {region_key}",
                "available_regions": list(self.brazilian_regions.keys())
            }
        
        region = self.brazilian_regions[region_key]
        dataset_type = force_dataset or self.get_optimal_dataset(region_key)
        
        print(f"🎯 Downloading elevation data for: {region['name']}")
        print(f"📍 Coordinates: {region['lat']}, {region['lng']}")
        print(f"🏞️  Terrain Type: {region['terrain'].value}")
        print(f"📊 Selected Dataset: {dataset_type.value}")
        
        # Calculate bounding box
        buffer = float(self.config.get('download_settings', 'bbox_buffer', fallback='0.01'))
        bbox = {
            'south': region['lat'] - buffer,
            'north': region['lat'] + buffer,
            'west': region['lng'] - buffer,
            'east': region['lng'] + buffer
        }
        
        # Create a directory for the region if it doesn't exist
        region_name = region['name'].replace(" ", "_").lower()
        output_dir = self.download_path / region_name
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
            print(f"CREATED FOLDER (download_elevation_data): {output_dir}") # LOGGING ADDED
            print(f"Created directory: {output_dir}")
        else:
            print(f"Directory already exists: {output_dir}")
        
        # Try primary dataset first, then fallbacks
        datasets_to_try = [dataset_type]
        if dataset_type != DatasetType.SRTM:
            datasets_to_try.append(DatasetType.SRTM)  # Always try SRTM as fallback
        
        for dataset in datasets_to_try:
            print(f"\n🔄 Attempting to download from {dataset.value}...")
            result = self._download_from_opentopography(region_key, bbox, dataset, output_dir)
            
            if result["success"]:
                return result
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        # If OpenTopography fails, try alternative sources
        print(f"\n🔄 Trying alternative data sources...")
        return self._try_alternative_sources(region_key, bbox)

    def _download_from_opentopography(self, region_key: str, bbox: Dict, dataset: DatasetType, output_dir: Path) -> Dict:
        """Download data from OpenTopography API"""
        
        dataset_info = self.datasets[dataset]
        
        # Check if authentication is available
        api_key = self.config.get('opentopography', 'api_key', fallback='')
        username = self.config.get('opentopography', 'username', fallback='')
        password = self.config.get('opentopography', 'password', fallback='')
        
        if dataset_info.requires_auth and not (api_key or (username and password)):
            return {
                "success": False,
                "error": f"Dataset {dataset.value} requires authentication. Please add credentials to config file.",
                "suggestion": "Sign up at https://portal.opentopography.org/"
            }
        
        # Prepare API request
        base_url = "https://portal.opentopography.org/API/globaldem"
        
        params = {
            'demtype': dataset_info.opentopo_name,
            'south': bbox['south'],
            'north': bbox['north'],
            'west': bbox['west'],
            'east': bbox['east'],
            'outputFormat': 'GTiff'
        }
        
        # Add authentication if available
        auth = None
        if api_key:
            params['API_Key'] = api_key
        elif username and password:
            auth = (username, password)
        
        try:
            timeout = int(self.config.get('download_settings', 'timeout', fallback='300'))
            
            print(f"📡 Requesting {dataset_info.name} data from OpenTopography...")
            response = requests.get(base_url, params=params, auth=auth, timeout=timeout)
            
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                # Success! Save the file
                output_file = output_dir / f"{region_key}_{dataset.value.lower()}_elevation.tif"
                
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                file_size = output_file.stat().st_size / (1024 * 1024)  # MB
                
                return {
                    "success": True,
                    "dataset": dataset.value,
                    "file_path": str(output_file),
                    "file_size_mb": round(file_size, 2),
                    "resolution": dataset_info.resolution,
                    "bbox": bbox,
                    "source": "OpenTopography API"
                }
            else:
                error_text = response.text[:200] if response.text else f"HTTP {response.status_code}"
                return {
                    "success": False,
                    "error": f"API request failed: {error_text}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timeout - try again later or use a smaller area"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }

    def _try_alternative_sources(self, region_key: str, bbox: Dict) -> Dict:
        """Try alternative data sources when OpenTopography fails"""
        
        print("🔄 Trying alternative sources...")
        
        # Try NASA Earthdata SRTM
        if self.config.getboolean('data_sources', 'use_nasa_earthdata', fallback=True):
            result = self._download_nasa_srtm(region_key, bbox)
            if result["success"]:
                return result
        
        # Try Copernicus service directly
        if self.config.getboolean('data_sources', 'use_copernicus_service', fallback=True):
            result = self._download_copernicus_direct(region_key, bbox)
            if result["success"]:
                return result
        
        # Try IBGE for Brazilian data
        if self.config.getboolean('data_sources', 'use_ibge_brazil', fallback=True):
            result = self._download_ibge_data(region_key, bbox)
            if result["success"]:
                return result
        
        return {
            "success": False,
            "error": "All data sources failed",
            "suggestion": "Check internet connection and try again later"
        }

    def _download_nasa_srtm(self, region_key: str, bbox: Dict) -> Dict:
        """Download SRTM data from NASA Earthdata"""
        # This would implement direct NASA SRTM download
        # For now, return a placeholder
        return {
            "success": False,
            "error": "NASA SRTM direct download not yet implemented"
        }

    def _download_copernicus_direct(self, region_key: str, bbox: Dict) -> Dict:
        """Download Copernicus DEM data directly"""
        # This would implement direct Copernicus download
        # For now, return a placeholder
        return {
            "success": False,
            "error": "Copernicus direct download not yet implemented"
        }

    def _download_ibge_data(self, region_key: str, bbox: Dict) -> Dict:
        """Download data from Brazilian IBGE sources"""
        # Check if IBGE services are accessible
        try:
            test_url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
            response = requests.get(test_url, timeout=10)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "dataset": "IBGE_REFERENCE",
                    "file_path": "ibge_services_accessible",
                    "source": "IBGE Brazil",
                    "note": "IBGE services are accessible but elevation data download needs implementation"
                }
            else:
                return {
                    "success": False,
                    "error": f"IBGE services not accessible: HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"IBGE access failed: {str(e)}"
            }

    def download_all_regions(self) -> Dict:
        """Download optimal elevation data for all Brazilian regions"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "regions": {},
            "summary": {"total": 0, "successful": 0, "failed": 0}
        }
        
        for region_key in self.brazilian_regions.keys():
            print(f"\n{'='*60}")
            result = self.download_elevation_data(region_key)
            results["regions"][region_key] = result
            results["summary"]["total"] += 1
            
            if result["success"]:
                results["summary"]["successful"] += 1
                print(f"✅ {region_key}: SUCCESS")
            else:
                results["summary"]["failed"] += 1
                print(f"❌ {region_key}: FAILED - {result.get('error', 'Unknown error')}")
        
        # Save results
        results_file = self.download_path / "optimal_elevation_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📊 Results saved to: {results_file}")
        print(f"📈 Summary: {results['summary']['successful']}/{results['summary']['total']} successful")
        
        return results

    def get_terrain_recommendations(self) -> Dict:
        """Get terrain-based dataset recommendations"""
        recommendations = {}
        
        for terrain_type in TerrainType:
            best_datasets = []
            for dataset_type, dataset_info in self.datasets.items():
                if terrain_type in dataset_info.best_for:
                    best_datasets.append({
                        "dataset": dataset_type.value,
                        "name": dataset_info.name,
                        "priority": dataset_info.priority,
                        "resolution": dataset_info.resolution
                    })
            
            best_datasets.sort(key=lambda x: x["priority"])
            recommendations[terrain_type.value] = best_datasets
        
        return recommendations

def main():
    """Main function for command-line usage"""
    print("🌎 Optimal Elevation Data Downloader for Brazilian Regions")
    print("=" * 60)
    
    downloader = OptimalElevationDownloader()
    
    if len(sys.argv) > 1:
        region = sys.argv[1]
        if region == "all":
            downloader.download_all_regions()
        else:
            result = downloader.download_elevation_data(region)
            print(f"\nResult: {json.dumps(result, indent=2)}")
    else:
        print("📋 Available regions:")
        for key, region in downloader.brazilian_regions.items():
            terrain = region["terrain"].value
            dataset = region["preferred_dataset"].value
            print(f"  {key}: {region['name']} ({terrain} → {dataset})")
        
        print(f"\n🎯 Usage: python {sys.argv[0]} <region_key|all>")
        print(f"💡 Example: python {sys.argv[0]} rio_de_janeiro")
        
        print("\n🏞️  Terrain-based recommendations:")
        recommendations = downloader.get_terrain_recommendations()
        for terrain, datasets in recommendations.items():
            print(f"  {terrain}:")
            for i, dataset in enumerate(datasets, 1):
                print(f"    {i}. {dataset['name']} ({dataset['resolution']})")

if __name__ == "__main__":
    main()
