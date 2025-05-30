"""
JSON-based PDAL Pipeline Loader

This module provides functionality to load PDAL pipeline configurations from JSON files
and adapt them for use with specific input files and output paths. This allows for
more flexible pipeline management compared to hardcoded configurations.
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PipelineLoader:
    """Class for loading and adapting JSON-based PDAL pipelines"""
    
    def __init__(self, pipelines_dir: Optional[str] = None):
        """
        Initialize the pipeline loader
        
        Args:
            pipelines_dir: Directory containing JSON pipeline files. 
                          If None, uses default 'pipelines_json' directory
        """
        if pipelines_dir is None:
            # Default to pipelines_json directory relative to this file
            current_dir = Path(__file__).parent
            self.pipelines_dir = current_dir / "pipelines_json"
        else:
            self.pipelines_dir = Path(pipelines_dir)
        
        if not self.pipelines_dir.exists():
            raise FileNotFoundError(f"Pipelines directory not found: {self.pipelines_dir}")
    
    def list_available_pipelines(self) -> List[str]:
        """
        List all available pipeline JSON files
        
        Returns:
            List of pipeline names (without .json extension)
        """
        pipeline_files = []
        for file_path in self.pipelines_dir.glob("*.json"):
            pipeline_files.append(file_path.stem)
        return sorted(pipeline_files)
    
    def load_pipeline_json(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Load a pipeline configuration from JSON file
        
        Args:
            pipeline_name: Name of the pipeline (without .json extension)
            
        Returns:
            Pipeline configuration dictionary
            
        Raises:
            FileNotFoundError: If pipeline file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        pipeline_file = self.pipelines_dir / f"{pipeline_name}.json"
        
        if not pipeline_file.exists():
            available = self.list_available_pipelines()
            raise FileNotFoundError(
                f"Pipeline '{pipeline_name}' not found. Available pipelines: {available}"
            )
        
        try:
            with open(pipeline_file, 'r') as f:
                pipeline_config = json.load(f)
            
            logger.info(f"Loaded pipeline '{pipeline_name}' from {pipeline_file}")
            return pipeline_config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in pipeline file {pipeline_file}: {e}")
            raise
    
    def adapt_pipeline(
        self, 
        pipeline_config: Dict[str, Any], 
        input_file: str, 
        output_file: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Adapt a pipeline configuration with specific input/output files and parameters
        
        Args:
            pipeline_config: Original pipeline configuration
            input_file: Path to input LAZ file
            output_file: Path to output file
            **kwargs: Additional parameters to override in the pipeline
            
        Returns:
            Adapted pipeline configuration
        """
        # Create a deep copy to avoid modifying the original
        adapted_config = json.loads(json.dumps(pipeline_config))
        
        # Adapt the pipeline stages
        if "pipeline" in adapted_config and isinstance(adapted_config["pipeline"], list):
            stages = adapted_config["pipeline"]
            
            # Replace input file (usually the first stage)
            for i, stage in enumerate(stages):
                if isinstance(stage, str):
                    # This is likely the input file
                    if any(ext in stage.lower() for ext in ['.laz', '.las', '.copc']):
                        stages[i] = input_file
                        logger.debug(f"Replaced input file: {stage} -> {input_file}")
                        break
            
            # Replace output file and apply kwargs to writer stages
            for stage in stages:
                if isinstance(stage, dict):
                    # Check if this is a writer stage
                    if stage.get("type", "").startswith("writers."):
                        # Update filename if present
                        if "filename" in stage:
                            old_filename = stage["filename"]
                            stage["filename"] = output_file
                            logger.debug(f"Replaced output file: {old_filename} -> {output_file}")
                        
                        # Apply any additional parameters from kwargs
                        for key, value in kwargs.items():
                            if key in stage:
                                old_value = stage[key]
                                stage[key] = value
                                logger.debug(f"Updated parameter {key}: {old_value} -> {value}")
                            elif key not in ["input_file", "output_file"]:
                                # Add new parameter if it's not already there
                                stage[key] = value
                                logger.debug(f"Added parameter {key}: {value}")
        
        return adapted_config
    
    def get_pipeline(
        self, 
        pipeline_name: str, 
        input_file: str, 
        output_file: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Load and adapt a pipeline in one step
        
        Args:
            pipeline_name: Name of the pipeline to load
            input_file: Path to input LAZ file
            output_file: Path to output file
            **kwargs: Additional parameters to override in the pipeline
            
        Returns:
            Adapted pipeline configuration ready for use
        """
        # Load the base pipeline
        pipeline_config = self.load_pipeline_json(pipeline_name)
        
        # Adapt it for the specific files and parameters
        adapted_config = self.adapt_pipeline(
            pipeline_config, 
            input_file, 
            output_file, 
            **kwargs
        )
        
        return adapted_config
    
    def get_pipeline_json_string(
        self, 
        pipeline_name: str, 
        input_file: str, 
        output_file: str, 
        **kwargs
    ) -> str:
        """
        Get a pipeline as a JSON string ready for PDAL execution
        
        Args:
            pipeline_name: Name of the pipeline to load
            input_file: Path to input LAZ file
            output_file: Path to output file
            **kwargs: Additional parameters to override in the pipeline
            
        Returns:
            JSON string representation of the adapted pipeline
        """
        pipeline_config = self.get_pipeline(pipeline_name, input_file, output_file, **kwargs)
        return json.dumps(pipeline_config, indent=2)
    
    def validate_pipeline(self, pipeline_config: Dict[str, Any]) -> bool:
        """
        Basic validation of pipeline configuration
        
        Args:
            pipeline_config: Pipeline configuration to validate
            
        Returns:
            True if pipeline appears valid, False otherwise
        """
        if not isinstance(pipeline_config, dict):
            logger.error("Pipeline config must be a dictionary")
            return False
        
        if "pipeline" not in pipeline_config:
            logger.error("Pipeline config must have a 'pipeline' key")
            return False
        
        pipeline_stages = pipeline_config["pipeline"]
        if not isinstance(pipeline_stages, list):
            logger.error("Pipeline stages must be a list")
            return False
        
        if len(pipeline_stages) == 0:
            logger.error("Pipeline must have at least one stage")
            return False
        
        # Check for at least one input (string) and one output (writer)
        has_input = any(isinstance(stage, str) for stage in pipeline_stages)
        has_writer = any(
            isinstance(stage, dict) and stage.get("type", "").startswith("writers.")
            for stage in pipeline_stages
        )
        
        if not has_input:
            logger.error("Pipeline must have an input file (string stage)")
            return False
        
        if not has_writer:
            logger.error("Pipeline must have at least one writer stage")
            return False
        
        logger.info("Pipeline validation passed")
        return True


# Global instance for easy access
_default_loader = None


def get_default_loader() -> PipelineLoader:
    """Get the default pipeline loader instance"""
    global _default_loader
    if _default_loader is None:
        _default_loader = PipelineLoader()
    return _default_loader


def load_pipeline(pipeline_name: str, input_file: str, output_file: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to load and adapt a pipeline using the default loader
    
    Args:
        pipeline_name: Name of the pipeline to load
        input_file: Path to input LAZ file
        output_file: Path to output file
        **kwargs: Additional parameters to override in the pipeline
        
    Returns:
        Adapted pipeline configuration
    """
    loader = get_default_loader()
    return loader.get_pipeline(pipeline_name, input_file, output_file, **kwargs)


def get_pipeline_json(pipeline_name: str, input_file: str, output_file: str, **kwargs) -> str:
    """
    Convenience function to get a pipeline as JSON string using the default loader
    
    Args:
        pipeline_name: Name of the pipeline to load
        input_file: Path to input LAZ file
        output_file: Path to output file
        **kwargs: Additional parameters to override in the pipeline
        
    Returns:
        JSON string representation of the adapted pipeline
    """
    loader = get_default_loader()
    return loader.get_pipeline_json_string(pipeline_name, input_file, output_file, **kwargs)


def list_pipelines() -> List[str]:
    """
    Convenience function to list available pipelines using the default loader
    
    Returns:
        List of available pipeline names
    """
    loader = get_default_loader()
    return loader.list_available_pipelines()


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        loader = PipelineLoader()
        
        print("Available pipelines:")
        for pipeline in loader.list_available_pipelines():
            print(f"  - {pipeline}")
        
        # Test loading and adapting a pipeline
        if "laz_to_dem" in loader.list_available_pipelines():
            print("\nTesting laz_to_dem pipeline:")
            
            pipeline_config = loader.get_pipeline(
                "laz_to_dem",
                "input/test.laz",
                "output/test_dem.tif",
                resolution=2.0,
                nodata=-999
            )
            
            print("Adapted pipeline:")
            print(json.dumps(pipeline_config, indent=2))
            
            # Validate the pipeline
            is_valid = loader.validate_pipeline(pipeline_config)
            print(f"Pipeline valid: {is_valid}")
    
    except Exception as e:
        print(f"Error: {e}")
