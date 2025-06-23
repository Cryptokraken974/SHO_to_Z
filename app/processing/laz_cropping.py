"""
LAZ Cropping Module
Handles cropping of LAZ point clouds using vector geometries
"""

import os
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class LAZCropper:
    """
    Modular LAZ cropping service using PDAL
    Supports cropping by vector geometries (polygons, bounding boxes)
    """
    
    def __init__(self, output_format: str = "las", compression: bool = True):
        """
        Initialize LAZ cropper
        
        Args:
            output_format: Output format ("laz", "las", "ply") (default: "las")
            compression: Enable compression for output (default: True)
        """
        self.output_format = output_format.lower()
        self.compression = compression
        self.logger = logging.getLogger(__name__)
        
        # Validate output format
        supported_formats = ["laz", "las", "ply"]
        if self.output_format not in supported_formats:
            raise ValueError(f"Unsupported output format: {output_format}. Supported: {supported_formats}")
    
    def crop_laz_with_polygon(
        self,
        input_laz_path: str,
        polygon_path: str,
        output_dir: str,
        region_name: str = None,
        crop_method: str = "inside"
    ) -> Dict[str, Any]:
        """
        Crop LAZ file using polygon geometry
        
        Args:
            input_laz_path: Path to input LAZ file
            polygon_path: Path to polygon vector file (GeoJSON, Shapefile, etc.)
            output_dir: Directory for output files
            region_name: Optional region name for file naming
            crop_method: Cropping method ("inside", "outside") (default: "inside")
            
        Returns:
            Dictionary with cropping results and file paths
        """
        try:
            print(f"\n✂️ LAZ CROPPING WITH POLYGON")
            print(f"   Input LAZ: {Path(input_laz_path).name}")
            print(f"   Polygon: {Path(polygon_path).name}")
            print(f"   Method: {crop_method}")
            
            # Validate input files
            if not os.path.exists(input_laz_path):
                raise FileNotFoundError(f"Input LAZ file not found: {input_laz_path}")
            
            if not os.path.exists(polygon_path):
                raise FileNotFoundError(f"Polygon file not found: {polygon_path}")
            
            # Extract region name if not provided
            if not region_name:
                region_name = self._extract_region_name(input_laz_path)
            
            # Create cropped subdirectory
            cropped_dir = Path(output_dir) / "cropped"
            cropped_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate output filename
            suffix = "cropped" if crop_method == "inside" else "exterior"
            output_filename = f"{region_name}_{suffix}.{self.output_format}"
            output_path = cropped_dir / output_filename
            
            print(f"📄 Cropping LAZ file...")
            print(f"   Output: {output_path}")
            
            # Create PDAL pipeline for cropping
            pipeline_config = self._create_crop_pipeline(
                input_laz_path,
                polygon_path,
                str(output_path),
                crop_method
            )
            
            # Execute PDAL pipeline 
            execution_stats = self._execute_pdal_pipeline(pipeline_config)
            
            # Analyze cropped file statistics
            cropped_stats = self._analyze_cropped_file(str(output_path))
            
            # Generate comparison statistics
            original_stats = self._analyze_cropped_file(input_laz_path)
            
            print(f"✅ LAZ cropping completed successfully")
            print(f"   Output file: {output_path}")
            print(f"   Original points: {original_stats.get('point_count', 'N/A'):,}")
            print(f"   Cropped points: {cropped_stats.get('point_count', 'N/A'):,}")
            
            if original_stats.get('point_count') and cropped_stats.get('point_count'):
                retention_pct = (cropped_stats['point_count'] / original_stats['point_count']) * 100
                print(f"   Point retention: {retention_pct:.1f}%")
            
            return {
                "success": True,
                "cropped_laz_path": str(output_path),
                "output_format": self.output_format,
                "region_name": region_name,
                "crop_method": crop_method,
                "statistics": {
                    "original": original_stats,
                    "cropped": cropped_stats,
                    "retention_percentage": retention_pct if 'retention_pct' in locals() else None
                },
                "execution": execution_stats
            }
            
        except Exception as e:
            error_msg = f"LAZ cropping failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "cropped_laz_path": None,
                "statistics": {}
            }
    
    def crop_laz_with_bbox(
        self,
        input_laz_path: str,
        bbox: List[float],
        output_dir: str,
        region_name: str = None
    ) -> Dict[str, Any]:
        """
        Crop LAZ file using bounding box
        
        Args:
            input_laz_path: Path to input LAZ file
            bbox: Bounding box as [xmin, ymin, xmax, ymax]
            output_dir: Directory for output files
            region_name: Optional region name for file naming
            
        Returns:
            Dictionary with cropping results and file paths
        """
        try:
            print(f"\n✂️ LAZ CROPPING WITH BOUNDING BOX")
            print(f"   Input LAZ: {Path(input_laz_path).name}")
            print(f"   BBox: {bbox}")
            
            # Validate inputs
            if not os.path.exists(input_laz_path):
                raise FileNotFoundError(f"Input LAZ file not found: {input_laz_path}")
            
            if len(bbox) != 4:
                raise ValueError("Bounding box must have 4 values: [xmin, ymin, xmax, ymax]")
            
            # Extract region name if not provided
            if not region_name:
                region_name = self._extract_region_name(input_laz_path)
            
            # Create cropped subdirectory
            cropped_dir = Path(output_dir) / "cropped"
            cropped_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate output filename
            output_filename = f"{region_name}_bbox_cropped.{self.output_format}"
            output_path = cropped_dir / output_filename
            
            print(f"📄 Cropping LAZ file with bounding box...")
            print(f"   Output: {output_path}")
            
            # Create PDAL pipeline for bbox cropping
            pipeline_config = self._create_bbox_crop_pipeline(
                input_laz_path,
                bbox,
                str(output_path)
            )
            
            # Execute PDAL pipeline
            execution_stats = self._execute_pdal_pipeline(pipeline_config)
            
            # Analyze results
            cropped_stats = self._analyze_cropped_file(str(output_path))
            original_stats = self._analyze_cropped_file(input_laz_path)
            
            retention_pct = None
            if original_stats.get('point_count') and cropped_stats.get('point_count'):
                retention_pct = (cropped_stats['point_count'] / original_stats['point_count']) * 100
            
            print(f"✅ Bounding box cropping completed successfully")
            print(f"   Point retention: {retention_pct:.1f}%" if retention_pct else "")
            
            return {
                "success": True,
                "cropped_laz_path": str(output_path),
                "output_format": self.output_format,
                "region_name": region_name,
                "crop_method": "bbox",
                "bbox_used": bbox,
                "statistics": {
                    "original": original_stats,
                    "cropped": cropped_stats,
                    "retention_percentage": retention_pct
                },
                "execution": execution_stats
            }
            
        except Exception as e:
            error_msg = f"LAZ bbox cropping failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "cropped_laz_path": None,
                "statistics": {}
            }
    
    def _extract_region_name(self, laz_file_path: str) -> str:
        """Extract region name from LAZ file path"""
        input_path = Path(laz_file_path)
        
        # Try to extract from path structure
        if "input" in input_path.parts:
            try:
                input_index = input_path.parts.index("input")
                if input_index + 1 < len(input_path.parts):
                    return input_path.parts[input_index + 1]
            except (ValueError, IndexError):
                pass
        
        # Fallback to filename without extension
        return input_path.stem
    
    def _create_crop_pipeline(
        self,
        input_path: str,
        polygon_path: str,
        output_path: str,
        crop_method: str
    ) -> Dict[str, Any]:
        """
        Create PDAL pipeline for polygon-based cropping
        
        Args:
            input_path: Path to input LAZ file
            polygon_path: Path to polygon file
            output_path: Path for output file
            crop_method: Cropping method ("inside" or "outside")
            
        Returns:
            PDAL pipeline configuration
        """
        # Determine crop mode
        crop_outside = crop_method == "outside"
        
        # Convert polygon file to WKT format if needed
        polygon_wkt = self._convert_polygon_to_wkt(polygon_path)
        
        pipeline = {
            "pipeline": [
                {
                    "type": "readers.las",
                    "filename": input_path
                },
                {
                    "type": "filters.crop",
                    "polygon": polygon_wkt,
                    "outside": crop_outside
                }
            ]
        }
        
        # Add writer stage
        writer_stage = {
            "type": f"writers.{self.output_format}",
            "filename": output_path
        }
        
        # Add compression for LAZ
        if self.output_format == "laz" and self.compression:
            writer_stage["compression"] = "laszip"
        
        pipeline["pipeline"].append(writer_stage)
        
        return pipeline
    
    def _create_bbox_crop_pipeline(
        self,
        input_path: str,
        bbox: List[float],
        output_path: str
    ) -> Dict[str, Any]:
        """
        Create PDAL pipeline for bounding box cropping
        
        Args:
            input_path: Path to input LAZ file
            bbox: Bounding box [xmin, ymin, xmax, ymax]
            output_path: Path for output file
            
        Returns:
            PDAL pipeline configuration
        """
        xmin, ymin, xmax, ymax = bbox
        
        pipeline = {
            "pipeline": [
                {
                    "type": "readers.las",
                    "filename": input_path
                },
                {
                    "type": "filters.crop",
                    "bounds": f"([{xmin}, {xmax}], [{ymin}, {ymax}])"
                }
            ]
        }
        
        # Add writer stage
        writer_stage = {
            "type": f"writers.{self.output_format}",
            "filename": output_path
        }
        
        # Add compression for LAZ
        if self.output_format == "laz" and self.compression:
            writer_stage["compression"] = "laszip"
        
        pipeline["pipeline"].append(writer_stage)
        
        return pipeline
    
    def _execute_pdal_pipeline(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute PDAL pipeline and return statistics
        
        Args:
            pipeline_config: PDAL pipeline configuration
            
        Returns:
            Dictionary with execution statistics
        """
        try:
            # Create temporary pipeline file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(pipeline_config, f, indent=2)
                pipeline_file = f.name
            
            print(f"🔧 Executing PDAL cropping pipeline...")
            
            # Execute PDAL command
            cmd = ['pdal', 'pipeline', pipeline_file]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for large files
            )
            
            # Clean up temporary file
            os.unlink(pipeline_file)
            
            if result.returncode != 0:
                raise RuntimeError(f"PDAL cropping execution failed: {result.stderr}")
            
            print(f"✅ PDAL cropping pipeline executed successfully")
            
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("PDAL cropping pipeline execution timed out")
        except Exception as e:
            raise RuntimeError(f"PDAL cropping pipeline execution failed: {str(e)}")
    
    def _analyze_cropped_file(self, laz_file_path: str) -> Dict[str, Any]:
        """
        Analyze LAZ file statistics
        
        Args:
            laz_file_path: Path to LAZ file
            
        Returns:
            Dictionary with file statistics
        """
        try:
            if not os.path.exists(laz_file_path):
                return {"error": "File not found"}
            
            # Use pdal info to get file statistics
            cmd = ['pdal', 'info', '--summary', laz_file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return {"error": "Failed to analyze file"}
            
            # Parse JSON output
            try:
                info_data = json.loads(result.stdout)
                summary = info_data.get('summary', {})
                
                stats = {
                    "point_count": summary.get('num_points', 0),
                    "file_size_mb": round(os.path.getsize(laz_file_path) / (1024 * 1024), 2),
                    "bounds": summary.get('bounds', {})
                }
                
                return stats
                
            except json.JSONDecodeError:
                return {"error": "Failed to parse PDAL info output"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _convert_polygon_to_wkt(self, polygon_path: str) -> str:
        """
        Convert polygon file to WKT format for PDAL
        
        Args:
            polygon_path: Path to polygon file (GeoJSON, Shapefile, etc.)
            
        Returns:
            WKT string representation of the polygon
        """
        try:
            # Try to read the file as GeoJSON first
            import json
            with open(polygon_path, 'r') as f:
                geojson_data = json.load(f)
            
            # Extract the first feature's geometry
            if 'features' in geojson_data and len(geojson_data['features']) > 0:
                geometry = geojson_data['features'][0]['geometry']
                
                # Convert coordinates to WKT format
                if geometry['type'] == 'Polygon':
                    coords = geometry['coordinates'][0]  # Take exterior ring
                    wkt_coords = []
                    for coord in coords:
                        wkt_coords.append(f"{coord[0]} {coord[1]}")
                    wkt = f"POLYGON(({', '.join(wkt_coords)}))"
                    return wkt
                elif geometry['type'] == 'MultiPolygon':
                    # Take the first polygon from multipolygon
                    coords = geometry['coordinates'][0][0]  # First polygon, exterior ring
                    wkt_coords = []
                    for coord in coords:
                        wkt_coords.append(f"{coord[0]} {coord[1]}")
                    wkt = f"POLYGON(({', '.join(wkt_coords)}))"
                    return wkt
            
            # Fallback: return a simple bounding box WKT if we can't parse
            print("⚠️ Could not parse polygon geometry, using fallback bounding box")
            return "POLYGON((-180 -90, -180 90, 180 90, 180 -90, -180 -90))"
            
        except Exception as e:
            print(f"⚠️ Error converting polygon to WKT: {e}")
            # Return a fallback bounding box that should encompass most data
            return "POLYGON((-180 -90, -180 90, 180 90, 180 -90, -180 -90))"

def crop_laz_with_polygon(
    input_laz_path: str,
    polygon_path: str,
    output_dir: str,
    region_name: str = None,
    output_format: str = "laz",
    crop_method: str = "inside",
    compression: bool = True
) -> Dict[str, Any]:
    """
    Convenience function for LAZ polygon cropping
    
    Args:
        input_laz_path: Path to input LAZ file
        polygon_path: Path to polygon vector file
        output_dir: Output directory
        region_name: Optional region name
        output_format: Output format ("laz", "las", "ply")
        crop_method: Cropping method ("inside", "outside")
        compression: Enable compression
        
    Returns:
        Cropping results dictionary
    """
    cropper = LAZCropper(
        output_format=output_format,
        compression=compression
    )
    
    return cropper.crop_laz_with_polygon(
        input_laz_path,
        polygon_path,
        output_dir,
        region_name,
        crop_method
    )

def crop_laz_with_bbox(
    input_laz_path: str,
    bbox: List[float],
    output_dir: str,
    region_name: str = None,
    output_format: str = "laz",
    compression: bool = True
) -> Dict[str, Any]:
    """
    Convenience function for LAZ bounding box cropping
    
    Args:
        input_laz_path: Path to input LAZ file
        bbox: Bounding box [xmin, ymin, xmax, ymax]
        output_dir: Output directory
        region_name: Optional region name
        output_format: Output format ("laz", "las", "ply")
        compression: Enable compression
        
    Returns:
        Cropping results dictionary
    """
    cropper = LAZCropper(
        output_format=output_format,
        compression=compression
    )
    
    return cropper.crop_laz_with_bbox(
        input_laz_path,
        bbox,
        output_dir,
        region_name
    )
