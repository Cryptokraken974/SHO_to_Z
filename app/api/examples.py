"""
API Service Layer Usage Examples

This file demonstrates how to use the service layer for various operations.
The service layer provides both async and sync methods for all operations.
"""

import asyncio
from app.api import (
    RegionService, 
    ProcessingService, 
    ElevationService, 
    SatelliteService,
    OverlayService,
    SavedPlacesService,
    GeotiffService,
    RegionAnalysisService
)

async def example_region_operations():
    """Example of region management operations"""
    region_service = RegionService()
    
    try:
        # List all regions
        regions = await region_service.list_regions()
        print(f"Found {len(regions.get('regions', []))} regions")
        
        # Search for specific regions
        search_results = await region_service.search_regions("amazon", source="input")
        print(f"Amazon search found {len(search_results.get('regions', []))} results")
        
        # Get detailed info for a specific region
        if regions.get('regions'):
            region_name = regions['regions'][0]['name']
            region_info = await region_service.get_region_info(region_name)
            print(f"Region {region_name}: {region_info}")
        
    finally:
        await region_service.close()

async def example_processing_operations():
    """Example of LIDAR processing operations"""
    processing_service = ProcessingService()
    
    try:
        # List available LAZ files
        laz_files = await processing_service.list_laz_files()
        print(f"Available LAZ files: {len(laz_files.get('files', []))}")
        
        # Generate DTM for a region
        if laz_files.get('files'):
            file_path = laz_files['files'][0]['path']
            dtm_result = await processing_service.generate_dtm(input_file=file_path)
            print(f"DTM generation result: {dtm_result}")
        
        # Generate multiple terrain products
        # processing_result = await processing_service.generate_all_rasters(
        #     region_name="test_region",
        #     batch_size=4
        # )
        # print(f"Raster generation: {processing_result}")
        
    finally:
        await processing_service.close()

async def example_elevation_operations():
    """Example of elevation data operations"""
    elevation_service = ElevationService()
    
    try:
        # Check elevation system status
        status = await elevation_service.get_elevation_status()
        print(f"Elevation system status: {status}")
        
        # Get optimal elevation data for Brazilian coordinates
        brazilian_data = await elevation_service.get_brazilian_elevation_data(
            latitude=-9.38,
            longitude=-62.67,
            area_km=25.0
        )
        print(f"Brazilian elevation data: {brazilian_data}")
        
        # Check data availability
        availability = await elevation_service.check_elevation_availability(
            latitude=-9.38,
            longitude=-62.67
        )
        print(f"Data availability: {availability}")
        
    finally:
        await elevation_service.close()

async def example_satellite_operations():
    """Example of satellite data operations"""
    satellite_service = SatelliteService()
    
    try:
        # Search for Sentinel-2 scenes
        scenes = await satellite_service.search_sentinel2_scenes(
            latitude=-9.38,
            longitude=-62.67,
            start_date="2023-01-01",
            end_date="2023-12-31",
            cloud_cover_max=30.0
        )
        print(f"Found Sentinel-2 scenes: {scenes}")
        
        # Get satellite coverage information
        coverage = await satellite_service.get_satellite_coverage(
            latitude=-9.38,
            longitude=-62.67
        )
        print(f"Satellite coverage: {coverage}")
        
    finally:
        await satellite_service.close()

async def example_overlay_operations():
    """Example of overlay operations"""
    overlay_service = OverlayService()
    
    try:
        # List available overlays
        overlays = await overlay_service.list_available_overlays()
        print(f"Available overlays: {overlays}")
        
        # Get overlay data for a specific processing type
        # overlay_data = await overlay_service.get_raster_overlay_data(
        #     region_name="test_region",
        #     processing_type="hillshade"
        # )
        # print(f"Overlay data: {overlay_data}")
        
    finally:
        await overlay_service.close()

async def example_saved_places_operations():
    """Example of saved places operations"""
    saved_places_service = SavedPlacesService()
    
    try:
        # Get all saved places
        places = await saved_places_service.get_saved_places()
        print(f"Saved places: {places}")
        
        # Search places near coordinates
        nearby_places = await saved_places_service.get_places_near_coordinates(
            latitude=-9.38,
            longitude=-62.67,
            radius_km=50.0
        )
        print(f"Nearby places: {nearby_places}")
        
    finally:
        await saved_places_service.close()

async def example_analysis_operations():
    """Example of region analysis operations"""
    analysis_service = RegionAnalysisService()
    
    try:
        # Get analysis history
        history = await analysis_service.get_analysis_history()
        print(f"Analysis history: {history}")
        
        # Calculate region statistics (if region exists)
        # stats = await analysis_service.calculate_region_statistics(
        #     region_name="test_region",
        #     analysis_types=["terrain", "vegetation", "hydrology"]
        # )
        # print(f"Region statistics: {stats}")
        
    finally:
        await analysis_service.close()

def example_sync_operations():
    """Example of using synchronous methods"""
    # All services provide sync versions of their methods
    region_service = RegionService()
    
    # Use sync methods
    regions = region_service.list_regions_sync()
    print(f"Sync regions: {len(regions.get('regions', []))}")
    
    # Close the service (this is also async, but can be called sync)
    region_service.close_sync()

async def main():
    """Run all examples"""
    print("=== API Service Layer Examples ===\n")
    
    print("1. Region Operations:")
    await example_region_operations()
    print()
    
    print("2. Processing Operations:")
    await example_processing_operations()
    print()
    
    print("3. Elevation Operations:")
    await example_elevation_operations()
    print()
    
    print("4. Satellite Operations:")
    await example_satellite_operations()
    print()
    
    print("5. Overlay Operations:")
    await example_overlay_operations()
    print()
    
    print("6. Saved Places Operations:")
    await example_saved_places_operations()
    print()
    
    print("7. Analysis Operations:")
    await example_analysis_operations()
    print()
    
    print("8. Synchronous Operations:")
    example_sync_operations()
    print()
    
    print("=== Examples Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
