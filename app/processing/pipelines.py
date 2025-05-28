"""
PDAL Pipeline Configurations for LAZ Processing

This module contains all PDAL pipeline definitions used for processing LAZ files
into various terrain analysis outputs. Each pipeline is defined as a function that
returns the pipeline configuration dictionary.
"""

import json
from typing import Dict, Any, Optional


def create_laz_to_dem_pipeline(
    input_file: str, 
    output_file: str, 
    resolution: float = 1.0,
    output_type: str = "mean",
    nodata: float = -9999
) -> Dict[str, Any]:
    """
    Create PDAL pipeline for converting LAZ to DEM (Digital Elevation Model)
    
    Args:
        input_file: Path to input LAZ file
        output_file: Path to output TIF file
        resolution: Grid resolution for DEM generation (default: 1.0)
        output_type: Output aggregation method (default: "mean")
        nodata: NoData value (default: -9999)
        
    Returns:
        PDAL pipeline configuration dictionary
    """
    return {
        "pipeline": [
            input_file,
            {
                "type": "writers.gdal",
                "filename": output_file,
                "resolution": resolution,
                "output_type": output_type,
                "nodata": nodata,
                "gdaldriver": "GTiff"
            }
        ]
    }


def create_laz_to_dtm_pipeline(
    input_file: str,
    output_file: str,
    resolution: float = 1.0,
    nodata: float = -9999,
    ground_only: bool = True
) -> Dict[str, Any]:
    """
    Create PDAL pipeline for converting LAZ to DTM (Digital Terrain Model)
    DTM filters to ground points only for terrain surface
    
    Args:
        input_file: Path to input LAZ file
        output_file: Path to output TIF file
        resolution: Grid resolution for DTM generation (default: 1.0)
        nodata: NoData value (default: -9999)
        ground_only: Filter to ground points only (default: True)
        
    Returns:
        PDAL pipeline configuration dictionary
    """
    pipeline = [input_file]
    
    if ground_only:
        # Add ground classification filter
        pipeline.append({
            "type": "filters.range",
            "limits": "Classification[2:2]"  # Ground points only
        })
    
    # Add GDAL writer
    pipeline.append({
        "type": "writers.gdal",
        "filename": output_file,
        "resolution": resolution,
        "output_type": "min",  # DTM typically uses minimum for ground surface
        "nodata": nodata,
        "gdaldriver": "GTiff"
    })
    
    return {"pipeline": pipeline}


def create_laz_to_dsm_pipeline(
    input_file: str,
    output_file: str,
    resolution: float = 1.0,
    nodata: float = -9999
) -> Dict[str, Any]:
    """
    Create PDAL pipeline for converting LAZ to DSM (Digital Surface Model)
    DSM includes all surface features (buildings, vegetation, etc.)
    
    Args:
        input_file: Path to input LAZ file
        output_file: Path to output TIF file
        resolution: Grid resolution for DSM generation (default: 1.0)
        nodata: NoData value (default: -9999)
        
    Returns:
        PDAL pipeline configuration dictionary
    """
    return {
        "pipeline": [
            input_file,
            {
                "type": "writers.gdal",
                "filename": output_file,
                "resolution": resolution,
                "output_type": "max",  # DSM typically uses maximum for surface
                "nodata": nodata,
                "gdaldriver": "GTiff"
            }
        ]
    }


def create_laz_intensity_pipeline(
    input_file: str,
    output_file: str,
    resolution: float = 1.0,
    nodata: float = -9999,
    output_type: str = "mean"
) -> Dict[str, Any]:
    """
    Create PDAL pipeline for extracting intensity data from LAZ
    
    Args:
        input_file: Path to input LAZ file
        output_file: Path to output TIF file
        resolution: Grid resolution (default: 1.0)
        nodata: NoData value (default: -9999)
        output_type: Aggregation method for intensity (default: "mean")
        
    Returns:
        PDAL pipeline configuration dictionary
    """
    return {
        "pipeline": [
            input_file,
            {
                "type": "writers.gdal",
                "filename": output_file,
                "resolution": resolution,
                "output_type": output_type,
                "dimension": "Intensity",  # Output intensity values
                "nodata": nodata,
                "gdaldriver": "GTiff"
            }
        ]
    }


def create_laz_density_pipeline(
    input_file: str,
    output_file: str,
    resolution: float = 1.0,
    nodata: float = -9999
) -> Dict[str, Any]:
    """
    Create PDAL pipeline for creating point density raster from LAZ
    
    Args:
        input_file: Path to input LAZ file
        output_file: Path to output TIF file
        resolution: Grid resolution (default: 1.0)
        nodata: NoData value (default: -9999)
        
    Returns:
        PDAL pipeline configuration dictionary
    """
    return {
        "pipeline": [
            input_file,
            {
                "type": "writers.gdal",
                "filename": output_file,
                "resolution": resolution,
                "output_type": "count",  # Count points per cell
                "nodata": nodata,
                "gdaldriver": "GTiff"
            }
        ]
    }


def create_laz_classification_pipeline(
    input_file: str,
    output_file: str,
    resolution: float = 1.0,
    nodata: float = -9999,
    classification_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create PDAL pipeline for extracting specific classification from LAZ
    
    Args:
        input_file: Path to input LAZ file
        output_file: Path to output TIF file
        resolution: Grid resolution (default: 1.0)
        nodata: NoData value (default: -9999)
        classification_filter: Classification range filter (e.g., "2:2" for ground)
        
    Returns:
        PDAL pipeline configuration dictionary
    """
    pipeline = [input_file]
    
    if classification_filter:
        pipeline.append({
            "type": "filters.range",
            "limits": f"Classification[{classification_filter}]"
        })
    
    pipeline.append({
        "type": "writers.gdal",
        "filename": output_file,
        "resolution": resolution,
        "output_type": "mean",
        "nodata": nodata,
        "gdaldriver": "GTiff"
    })
    
    return {"pipeline": pipeline}


def get_pipeline_json(pipeline_config: Dict[str, Any]) -> str:
    """
    Convert pipeline configuration to JSON string for PDAL execution
    
    Args:
        pipeline_config: Pipeline configuration dictionary
        
    Returns:
        JSON string representation of the pipeline
    """
    return json.dumps(pipeline_config)


def print_pipeline_info(pipeline_config: Dict[str, Any], pipeline_name: str = "Pipeline") -> None:
    """
    Print formatted pipeline information for debugging
    
    Args:
        pipeline_config: Pipeline configuration dictionary
        pipeline_name: Name of the pipeline for display
    """
    print(f"\n⚙️ {pipeline_name} Configuration:")
    pipeline_formatted = json.dumps(pipeline_config, indent=4)
    print(f"{pipeline_formatted}")


# Pipeline registry for easy access
PIPELINE_REGISTRY = {
    "laz_to_dem": create_laz_to_dem_pipeline,
    "laz_to_dtm": create_laz_to_dtm_pipeline,
    "laz_to_dsm": create_laz_to_dsm_pipeline,
    "laz_intensity": create_laz_intensity_pipeline,
    "laz_density": create_laz_density_pipeline,
    "laz_classification": create_laz_classification_pipeline,
}


def get_pipeline(pipeline_type: str, **kwargs) -> Dict[str, Any]:
    """
    Get a pipeline configuration by type name
    
    Args:
        pipeline_type: Type of pipeline from PIPELINE_REGISTRY
        **kwargs: Arguments to pass to the pipeline creation function
        
    Returns:
        Pipeline configuration dictionary
        
    Raises:
        ValueError: If pipeline_type is not found in registry
    """
    if pipeline_type not in PIPELINE_REGISTRY:
        available_types = ", ".join(PIPELINE_REGISTRY.keys())
        raise ValueError(f"Unknown pipeline type '{pipeline_type}'. Available types: {available_types}")
    
    return PIPELINE_REGISTRY[pipeline_type](**kwargs)
