"""
Vector Operations Module
Handles conversion from raster masks to vector polygons for spatial analysis
"""

import os
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

try:
    import rasterio
    import rasterio.features
    import shapely.geometry
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)

class VectorProcessor:
    """
    Modular vector operations for raster-to-vector conversion
    Supports multiple output formats and processing methods
    """
    
    def __init__(self, simplify_tolerance: float = 0.5, min_area: float = 100.0):
        """
        Initialize vector processor
        
        Args:
            simplify_tolerance: Tolerance for polygon simplification in meters (default: 0.5)
            min_area: Minimum polygon area to keep in square meters (default: 100.0)
        """
        self.simplify_tolerance = simplify_tolerance
        self.min_area = min_area
        self.logger = logging.getLogger(__name__)
    
    def mask_to_polygon(
        self,
        mask_raster_path: str,
        output_dir: str,
        region_name: str,
        output_format: str = "GeoJSON",
        method: str = "auto"
    ) -> Dict[str, Any]:
        """
        Convert binary mask raster to polygon vector file
        
        Args:
            mask_raster_path: Path to binary mask TIFF file
            output_dir: Directory for output vector file
            region_name: Region name for file naming
            output_format: Output format ("GeoJSON", "Shapefile", "GPKG")
            method: Processing method ("gdal", "python", "auto")
            
        Returns:
            Dictionary with conversion results and file paths
        """
        try:
            print(f"\n🔄 MASK TO POLYGON CONVERSION")
            print(f"   Input mask: {Path(mask_raster_path).name}")
            print(f"   Output format: {output_format}")
            print(f"   Method: {method}")
            
            # Validate input file
            if not os.path.exists(mask_raster_path):
                raise FileNotFoundError(f"Mask raster not found: {mask_raster_path}")
            
            # Create vectors subdirectory
            vectors_dir = Path(output_dir) / "vectors"
            vectors_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine output file path and extension
            file_extensions = {
                "GeoJSON": ".geojson",
                "Shapefile": ".shp", 
                "GPKG": ".gpkg"
            }
            
            if output_format not in file_extensions:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            output_filename = f"{region_name}_valid_footprint{file_extensions[output_format]}"
            output_path = vectors_dir / output_filename
            
            # Choose processing method
            if method == "auto":
                if RASTERIO_AVAILABLE:
                    method = "python"
                else:
                    method = "gdal"
            
            # Perform conversion
            if method == "python" and RASTERIO_AVAILABLE:
                result = self._mask_to_polygon_python(
                    mask_raster_path, str(output_path), output_format
                )
            else:
                result = self._mask_to_polygon_gdal(
                    mask_raster_path, str(output_path), output_format
                )
            
            # Analyze polygon statistics
            polygon_stats = self._analyze_polygon_statistics(str(output_path), output_format)
            
            print(f"✅ Polygon conversion completed")
            print(f"   Output file: {output_path}")
            print(f"   Polygons: {polygon_stats.get('polygon_count', 'N/A')}")
            print(f"   Total area: {polygon_stats.get('total_area_sqm', 'N/A'):.1f} m²")
            
            return {
                "success": True,
                "vector_path": str(output_path),
                "output_format": output_format,
                "method_used": method,
                "statistics": polygon_stats,
                "region_name": region_name
            }
            
        except Exception as e:
            error_msg = f"Mask to polygon conversion failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "vector_path": None,
                "statistics": {}
            }
    
    def _mask_to_polygon_python(
        self,
        mask_path: str, 
        output_path: str,
        output_format: str
    ) -> Dict[str, Any]:
        """
        Convert mask to polygon using Python/rasterio approach
        
        Args:
            mask_path: Path to input mask raster
            output_path: Path for output vector file
            output_format: Output vector format
            
        Returns:
            Processing results
        """
        print(f"🐍 Using Python/rasterio for polygon conversion...")
        
        import rasterio
        from rasterio import features
        from shapely.geometry import shape, Polygon
        
        # Read mask raster
        with rasterio.open(mask_path) as src:
            mask_data = src.read(1)
            transform = src.transform
            crs = src.crs
            
            print(f"   Mask shape: {mask_data.shape}")
            print(f"   Valid pixels: {(mask_data > 0).sum():,}")
            
            # Convert raster to polygons
            polygons = []
            for geom, value in features.shapes(
                mask_data.astype(rasterio.uint8), 
                mask=(mask_data > 0), 
                transform=transform
            ):
                if value == 1:  # Valid data pixels
                    poly = shape(geom)
                    
                    # Filter by minimum area
                    if poly.area >= self.min_area:
                        # Simplify polygon
                        if self.simplify_tolerance > 0:
                            poly = poly.simplify(self.simplify_tolerance, preserve_topology=True)
                        polygons.append(poly)
        
        print(f"   Generated {len(polygons)} polygons")
        
        # Create GeoDataFrame if geopandas available
        if GEOPANDAS_AVAILABLE:
            gdf = gpd.GeoDataFrame(
                {'geometry': polygons, 'value': [1] * len(polygons)},
                crs=crs
            )
            
            # Save to file
            if output_format == "GeoJSON":
                gdf.to_file(output_path, driver="GeoJSON")
            elif output_format == "Shapefile":
                gdf.to_file(output_path, driver="ESRI Shapefile")
            elif output_format == "GPKG":
                gdf.to_file(output_path, driver="GPKG")
        else:
            # Fallback to GeoJSON using basic approach
            features_list = []
            for poly in polygons:
                features_list.append({
                    "type": "Feature",
                    "geometry": poly.__geo_interface__,
                    "properties": {"value": 1}
                })
            
            geojson_data = {
                "type": "FeatureCollection",
                "features": features_list
            }
            
            with open(output_path, 'w') as f:
                json.dump(geojson_data, f, indent=2)
        
        return {
            "success": True,
            "method": "python",
            "polygons_generated": len(polygons)
        }
    
    def _mask_to_polygon_gdal(
        self,
        mask_path: str,
        output_path: str, 
        output_format: str
    ) -> Dict[str, Any]:
        """
        Convert mask to polygon using GDAL approach
        
        Args:
            mask_path: Path to input mask raster
            output_path: Path for output vector file
            output_format: Output vector format
            
        Returns:
            Processing results
        """
        print(f"🔧 Using GDAL for polygon conversion...")
        
        # GDAL format mapping
        gdal_drivers = {
            "GeoJSON": "GeoJSON",
            "Shapefile": "ESRI Shapefile", 
            "GPKG": "GPKG"
        }
        
        # Build gdal_polygonize command
        cmd = [
            'gdal_polygonize.py',
            mask_path,
            '-f', gdal_drivers[output_format],
            output_path
        ]
        
        # Add field name for polygon values
        if output_format in ["Shapefile", "GPKG"]:
            cmd.extend(['-b', '1', 'DN'])  # Band 1, field name 'DN'
        
        print(f"   Running: {' '.join(cmd)}")
        
        # Execute GDAL command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"GDAL polygonize failed: {result.stderr}")
        
        print(f"✅ GDAL polygonize completed successfully")
        
        # Optionally simplify polygons using ogr2ogr
        if self.simplify_tolerance > 0:
            self._simplify_polygons_gdal(output_path, output_format)
        
        return {
            "success": True,
            "method": "gdal",
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def _simplify_polygons_gdal(self, vector_path: str, output_format: str):
        """
        Simplify polygons using GDAL/OGR
        
        Args:
            vector_path: Path to vector file to simplify
            output_format: Vector format
        """
        try:
            print(f"🔄 Simplifying polygons (tolerance: {self.simplify_tolerance}m)...")
            
            # Create temporary simplified file
            temp_path = str(Path(vector_path).with_suffix('.simplified' + Path(vector_path).suffix))
            
            # GDAL format mapping
            gdal_drivers = {
                "GeoJSON": "GeoJSON",
                "Shapefile": "ESRI Shapefile",
                "GPKG": "GPKG"
            }
            
            cmd = [
                'ogr2ogr',
                '-f', gdal_drivers[output_format],
                temp_path,
                vector_path,
                '-simplify', str(self.simplify_tolerance)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Replace original with simplified version
                os.replace(temp_path, vector_path)
                print(f"✅ Polygon simplification completed")
            else:
                print(f"⚠️ Polygon simplification failed: {result.stderr}")
                # Clean up temp file if it exists
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            print(f"⚠️ Polygon simplification error: {e}")
    
    def _analyze_polygon_statistics(
        self,
        vector_path: str,
        output_format: str
    ) -> Dict[str, Any]:
        """
        Analyze polygon statistics
        
        Args:
            vector_path: Path to vector file
            output_format: Vector format
            
        Returns:
            Dictionary with polygon statistics
        """
        try:
            print(f"📊 Analyzing polygon statistics...")
            
            # Use ogrinfo to get basic statistics
            cmd = ['ogrinfo', '-al', '-so', vector_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {"error": "Failed to analyze polygon statistics"}
            
            # Parse ogrinfo output
            stats = {}
            lines = result.stdout.split('\n')
            
            for line in lines:
                line = line.strip()
                if 'Feature Count:' in line:
                    try:
                        stats['polygon_count'] = int(line.split(':')[1].strip())
                    except (ValueError, IndexError):
                        pass
                elif 'Extent:' in line:
                    # Parse extent information
                    try:
                        extent_part = line.split('Extent:')[1].strip()
                        # Basic extent parsing - could be enhanced
                        stats['extent_info'] = extent_part
                    except (ValueError, IndexError):
                        pass
            
            # Calculate approximate total area if geopandas is available
            if GEOPANDAS_AVAILABLE and os.path.exists(vector_path):
                try:
                    gdf = gpd.read_file(vector_path)
                    if not gdf.empty:
                        # Convert to appropriate CRS for area calculation if needed
                        if gdf.crs and gdf.crs.is_geographic:
                            # Use a metric CRS for area calculation
                            gdf_metric = gdf.to_crs('EPSG:3857')  # Web Mercator
                            total_area = gdf_metric.geometry.area.sum()
                        else:
                            total_area = gdf.geometry.area.sum()
                        
                        stats['total_area_sqm'] = float(total_area)
                        stats['avg_area_sqm'] = float(total_area / len(gdf)) if len(gdf) > 0 else 0
                        stats['geometry_types'] = gdf.geometry.type.value_counts().to_dict()
                except Exception as e:
                    print(f"⚠️ Advanced statistics calculation failed: {e}")
            
            return stats
            
        except Exception as e:
            print(f"⚠️ Statistics analysis failed: {e}")
            return {"error": str(e)}

def convert_mask_to_polygon(
    mask_raster_path: str,
    output_dir: str,
    region_name: str = None,
    output_format: str = "GeoJSON",
    simplify_tolerance: float = 0.5,
    min_area: float = 100.0,
    method: str = "auto"
) -> Dict[str, Any]:
    """
    Convenience function for mask to polygon conversion
    
    Args:
        mask_raster_path: Path to binary mask raster
        output_dir: Output directory
        region_name: Optional region name
        output_format: Output vector format ("GeoJSON", "Shapefile", "GPKG")
        simplify_tolerance: Polygon simplification tolerance in meters
        min_area: Minimum polygon area to keep in square meters
        method: Processing method ("gdal", "python", "auto")
        
    Returns:
        Conversion results dictionary
    """
    # Extract region name if not provided
    if not region_name:
        mask_path = Path(mask_raster_path)
        region_name = mask_path.stem.replace('_valid_mask', '').replace('_mask', '')
    
    processor = VectorProcessor(
        simplify_tolerance=simplify_tolerance,
        min_area=min_area
    )
    
    return processor.mask_to_polygon(
        mask_raster_path,
        output_dir,
        region_name,
        output_format,
        method
    )
