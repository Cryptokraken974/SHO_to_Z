"""
Utility functions for coordinate handling and validation
"""

import math
from typing import Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class BoundingBox:
    """Represents a geographic bounding box"""
    north: float
    south: float
    east: float
    west: float
    
    def contains_point(self, lat: float, lng: float) -> bool:
        """Check if a point is within this bounding box"""
        return (self.south <= lat <= self.north and 
                self.west <= lng <= self.east)
    
    def get_center(self) -> Tuple[float, float]:
        """Get the center point of the bounding box"""
        center_lat = (self.north + self.south) / 2
        center_lng = (self.east + self.west) / 2
        return center_lat, center_lng
    
    def get_area_sq_km(self) -> float:
        """Calculate approximate area in square kilometers"""
        # Rough approximation using spherical Earth
        lat_diff = self.north - self.south
        lng_diff = self.east - self.west
        
        # Convert degrees to km (rough approximation)
        lat_km = lat_diff * 111  # 1 degree lat ≈ 111 km
        
        # Longitude varies with latitude
        avg_lat = (self.north + self.south) / 2
        lng_km = lng_diff * 111 * math.cos(math.radians(avg_lat))
        
        return lat_km * lng_km
    
    def area_km2(self) -> float:
        """Calculate approximate area in square kilometers (alias for get_area_sq_km)"""
        return self.get_area_sq_km()

class CoordinateValidator:
    """Validates geographic coordinates and regions"""
    
    # Country boundaries (rough approximations)
    BRAZIL_BOUNDS = BoundingBox(
        north=5.27,    # Northern border
        south=-33.75,  # Southern border  
        east=-28.65,   # Eastern border
        west=-73.99    # Western border
    )
    
    def validate_coordinates(self, lat: float, lng: float) -> bool:
        """
        Validate that coordinates are within valid geographic bounds
        
        Args:
            lat: Latitude in decimal degrees
            lng: Longitude in decimal degrees
            
        Returns:
            True if coordinates are valid
        """
        return (-90 <= lat <= 90) and (-180 <= lng <= 180)
    
    def is_in_brazil(self, lat: float, lng: float) -> bool:
        """
        Check if coordinates are within Brazil's boundaries
        
        Args:
            lat: Latitude in decimal degrees
            lng: Longitude in decimal degrees
            
        Returns:
            True if coordinates are in Brazil
        """
        return self.BRAZIL_BOUNDS.contains_point(lat, lng)
    
    def validate_bounding_box(self, bbox: BoundingBox) -> bool:
        """
        Validate that a bounding box is reasonable
        
        Args:
            bbox: BoundingBox to validate
            
        Returns:
            True if bounding box is valid
        """
        # Check coordinate validity
        coords_valid = (
            self.validate_coordinates(bbox.north, bbox.east) and
            self.validate_coordinates(bbox.south, bbox.west)
        )
        
        # Check logical order
        order_valid = (bbox.north > bbox.south and bbox.east > bbox.west)
        
        # Check reasonable size (not larger than a continent)
        area = bbox.get_area_sq_km()
        size_reasonable = area < 10_000_000  # 10 million sq km
        
        return coords_valid and order_valid and size_reasonable

class CoordinateConverter:
    """Converts between different coordinate systems and projections"""
    
    def create_bounding_box(self, lat: float, lng: float, buffer_km: float) -> BoundingBox:
        """
        Create a bounding box around a point with a buffer distance
        
        Args:
            lat: Center latitude in decimal degrees
            lng: Center longitude in decimal degrees
            buffer_km: Buffer distance in kilometers
            
        Returns:
            BoundingBox representing the buffered area
        """
        return self.point_to_bounding_box(lat, lng, buffer_km)
    
    def point_to_bounding_box(self, lat: float, lng: float, buffer_km: float) -> BoundingBox:
        """
        Convert a point and buffer distance to a bounding box
        
        Args:
            lat: Center latitude in decimal degrees
            lng: Center longitude in decimal degrees
            buffer_km: Buffer distance in kilometers
            
        Returns:
            BoundingBox representing the buffered area
        """
        # Convert km to degrees (rough approximation)
        lat_buffer = buffer_km / 111.0  # 1 degree lat ≈ 111 km
        
        # Longitude buffer varies with latitude
        lng_buffer = buffer_km / (111.0 * math.cos(math.radians(lat)))
        
        return BoundingBox(
            north=lat + lat_buffer,
            south=lat - lat_buffer,
            east=lng + lng_buffer,
            west=lng - lng_buffer
        )
    
    def bounding_box_to_wkt(self, bbox: BoundingBox) -> str:
        """
        Convert bounding box to WKT polygon format
        
        Args:
            bbox: BoundingBox to convert
            
        Returns:
            WKT polygon string
        """
        return f"POLYGON(({bbox.west} {bbox.south}, {bbox.east} {bbox.south}, " \
               f"{bbox.east} {bbox.north}, {bbox.west} {bbox.north}, {bbox.west} {bbox.south}))"
    
    def degrees_to_meters(self, lat_degrees: float, lng_degrees: float, 
                         reference_lat: float) -> Tuple[float, float]:
        """
        Convert degree differences to approximate meters
        
        Args:
            lat_degrees: Latitude difference in degrees
            lng_degrees: Longitude difference in degrees
            reference_lat: Reference latitude for longitude calculation
            
        Returns:
            Tuple of (lat_meters, lng_meters)
        """
        lat_meters = lat_degrees * 111_000  # 1 degree lat ≈ 111 km
        lng_meters = lng_degrees * 111_000 * math.cos(math.radians(reference_lat))
        
        return lat_meters, lng_meters
    
    def calculate_distance_km(self, lat1: float, lng1: float, 
                            lat2: float, lng2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Args:
            lat1, lng1: First point coordinates
            lat2, lng2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1_rad, lng1_rad = math.radians(lat1), math.radians(lng1)
        lat2_rad, lng2_rad = math.radians(lat2), math.radians(lng2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in km
        r = 6371
        
        return c * r
    
    def get_utm_zone(self, lng: float) -> int:
        """
        Get UTM zone number for a given longitude
        
        Args:
            lng: Longitude in decimal degrees
            
        Returns:
            UTM zone number (1-60)
        """
        return int((lng + 180) / 6) + 1

class UTMConverter:
    """Handles UTM coordinate system conversions (simplified)"""
    
    def get_utm_zone(self, lng: float) -> int:
        """
        Get UTM zone number for a given longitude
        
        Args:
            lng: Longitude in decimal degrees
            
        Returns:
            UTM zone number (1-60)
        """
        return int((lng + 180) / 6) + 1
    
    def get_brazilian_utm_zone(self, lng: float) -> str:
        """
        Get the appropriate Brazilian UTM zone EPSG code
        
        Args:
            lng: Longitude in decimal degrees
            
        Returns:
            EPSG code string for Brazilian UTM zones
        """
        utm_zone = self.get_utm_zone(lng)
        
        # Brazilian SIRGAS 2000 UTM zones
        brazil_utm_zones = {
            18: 'EPSG:31978',  # UTM Zone 18S
            19: 'EPSG:31979',  # UTM Zone 19S
            20: 'EPSG:31980',  # UTM Zone 20S
            21: 'EPSG:31981',  # UTM Zone 21S
            22: 'EPSG:31982',  # UTM Zone 22S
            23: 'EPSG:31983',  # UTM Zone 23S
            24: 'EPSG:31984',  # UTM Zone 24S
            25: 'EPSG:31985',  # UTM Zone 25S
        }
        
        return brazil_utm_zones.get(utm_zone, 'EPSG:4674')  # Default to SIRGAS 2000
