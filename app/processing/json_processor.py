"""
JSON Pipeline Processor

This module provides a processing interface that can use either hardcoded pipelines
or JSON-based pipelines. It serves as a bridge between the existing processing
functions and the new JSON pipeline system.
"""

import os
import time
import pdal
import logging
from typing import Dict, Any, Optional

from .pipelines_json import PipelineLoader
from .pipelines import (
    create_laz_to_dem_pipeline, 
    create_laz_to_dtm_pipeline,
    get_pipeline_json,
    print_pipeline_info
)

logger = logging.getLogger(__name__)


class JSONProcessor:
    """
    Processor that can use both hardcoded and JSON-based PDAL pipelines
    """
    
    def __init__(self, use_json_pipelines: bool = True):
        """
        Initialize the processor
        
        Args:
            use_json_pipelines: Whether to use JSON pipelines by default
        """
        self.use_json_pipelines = use_json_pipelines
        self.pipeline_loader = PipelineLoader() if use_json_pipelines else None
        
    def process_with_pipeline(
        self,
        input_file: str,
        output_file: str,
        pipeline_name: Optional[str] = None,
        fallback_pipeline_func: Optional[callable] = None,
        **kwargs
    ) -> tuple[bool, str]:
        """
        Process a file using either JSON pipeline or hardcoded pipeline
        
        Args:
            input_file: Path to input file
            output_file: Path to output file
            pipeline_name: Name of JSON pipeline to use (e.g. 'dtm', 'laz_to_dem')
            fallback_pipeline_func: Hardcoded pipeline function to use as fallback
            **kwargs: Additional parameters for pipeline adaptation
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        print(f"\n{'='*60}")
        print(f"🔧 STARTING PIPELINE PROCESSING")
        print(f"{'='*60}")
        print(f"📁 Input file: {input_file}")
        print(f"📁 Output file: {output_file}")
        print(f"🎯 Pipeline name: {pipeline_name}")
        print(f"🔄 Use JSON pipelines: {self.use_json_pipelines}")
        
        # Validate input file
        if not os.path.exists(input_file):
            error_msg = f"Input file not found: {input_file}"
            print(f"❌ {error_msg}")
            return False, error_msg
            
        file_size = os.path.getsize(input_file)
        print(f"✅ Input file validated ({file_size:,} bytes)")
        
        # Create output directory if needed
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            print(f"📂 Output directory ready: {output_dir}")
        
        try:
            # Try JSON pipeline first if enabled and pipeline name provided
            if self.use_json_pipelines and pipeline_name and self.pipeline_loader:
                print(f"\n🎯 Attempting to use JSON pipeline: {pipeline_name}")
                
                try:
                    # Load and adapt JSON pipeline
                    pipeline_dict = self.pipeline_loader.get_pipeline(
                        pipeline_name,
                        input_file=input_file,
                        output_file=output_file,
                        **kwargs
                    )
                    
                    if pipeline_dict:
                        print(f"✅ JSON pipeline loaded successfully")
                        print_pipeline_info(pipeline_dict, f"JSON Pipeline: {pipeline_name}")
                        
                        # Execute JSON pipeline
                        success, message = self._execute_pipeline(pipeline_dict, input_file)
                        if success:
                            return success, message
                        else:
                            print(f"⚠️ JSON pipeline failed: {message}")
                            print(f"🔄 Falling back to hardcoded pipeline...")
                    else:
                        print(f"⚠️ JSON pipeline '{pipeline_name}' not found")
                        print(f"🔄 Falling back to hardcoded pipeline...")
                        
                except Exception as e:
                    print(f"⚠️ Error loading JSON pipeline: {str(e)}")
                    print(f"🔄 Falling back to hardcoded pipeline...")
            
            # Use hardcoded pipeline as fallback or primary method
            if fallback_pipeline_func:
                print(f"\n🔧 Using hardcoded pipeline")
                pipeline_dict = fallback_pipeline_func(
                    input_file=input_file,
                    output_file=output_file,
                    **kwargs
                )
                
                print(f"✅ Hardcoded pipeline created")
                print_pipeline_info(pipeline_dict, "Hardcoded Pipeline")
                
                return self._execute_pipeline(pipeline_dict, input_file)
            else:
                error_msg = "No pipeline available (neither JSON nor hardcoded)"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Pipeline processing error: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(f"Pipeline processing error: {error_msg}", exc_info=True)
            return False, error_msg
    
    def _execute_pipeline(self, pipeline_dict: Dict[str, Any], input_file: str) -> tuple[bool, str]:
        """
        Execute a PDAL pipeline
        
        Args:
            pipeline_dict: PDAL pipeline configuration
            input_file: Input file path for logging
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        print(f"\n🚀 Executing PDAL pipeline...")
        
        try:
            # Convert pipeline dict to JSON string
            pipeline_json = get_pipeline_json(pipeline_dict)
            
            # Create and execute PDAL pipeline
            execution_start = time.time()
            pdal_pipeline = pdal.Pipeline(pipeline_json)
            
            print(f"   🔄 Running PDAL execution...")
            count = pdal_pipeline.execute()
            
            execution_time = time.time() - execution_start
            print(f"✅ PDAL execution completed in {execution_time:.2f}s")
            print(f"📊 Points processed: {count:,}")
            
            # Check if output was created
            pipeline_stages = pipeline_dict.get("pipeline", [])
            output_file = None
            
            # Find the output file from writer stages
            for stage in pipeline_stages:
                if isinstance(stage, dict) and stage.get("type", "").startswith("writers."):
                    output_file = stage.get("filename")
                    break
            
            if output_file and os.path.exists(output_file):
                output_size = os.path.getsize(output_file)
                print(f"✅ Output file created: {output_file}")
                print(f"📊 Output size: {output_size:,} bytes ({output_size / (1024**2):.2f} MB)")
                
                success_msg = f"Pipeline executed successfully. Output: {output_file}"
                print(f"✅ {success_msg}")
                return True, success_msg
            else:
                error_msg = "Pipeline executed but output file was not created"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except RuntimeError as e:
            error_msg = f"PDAL execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error during pipeline execution: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def list_available_json_pipelines(self) -> list[str]:
        """
        List available JSON pipelines
        
        Returns:
            List of available pipeline names
        """
        if self.pipeline_loader:
            return self.pipeline_loader.list_available_pipelines()
        return []
    
    def get_pipeline_info(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a JSON pipeline
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Pipeline configuration dict or None if not found
        """
        if self.pipeline_loader:
            return self.pipeline_loader.load_pipeline_json(pipeline_name)
        return None


# Global processor instance
_processor = JSONProcessor(use_json_pipelines=True)


def get_processor() -> JSONProcessor:
    """Get the global processor instance"""
    return _processor


def set_use_json_pipelines(use_json: bool):
    """
    Configure whether to use JSON pipelines by default
    
    Args:
        use_json: Whether to use JSON pipelines
    """
    global _processor
    _processor.use_json_pipelines = use_json
    if use_json and not _processor.pipeline_loader:
        _processor.pipeline_loader = PipelineLoader()
    print(f"🔧 JSON pipeline usage set to: {use_json}")


def process_with_json_pipeline(
    input_file: str,
    output_file: str,
    pipeline_name: str,
    fallback_pipeline_func: Optional[callable] = None,
    **kwargs
) -> tuple[bool, str]:
    """
    Convenience function to process with JSON pipeline
    
    Args:
        input_file: Path to input file
        output_file: Path to output file
        pipeline_name: Name of JSON pipeline to use
        fallback_pipeline_func: Hardcoded pipeline function to use as fallback
        **kwargs: Additional parameters for pipeline adaptation
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    return _processor.process_with_pipeline(
        input_file=input_file,
        output_file=output_file,
        pipeline_name=pipeline_name,
        fallback_pipeline_func=fallback_pipeline_func,
        **kwargs
    )
