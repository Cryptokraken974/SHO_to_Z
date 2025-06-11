"""
Pipeline Service

Provides pipeline management functionality including:
- JSON pipeline listing and retrieval
- Pipeline execution and monitoring
- Pipeline configuration management
- Pipeline status tracking
"""

from typing import Dict, Any, List, Optional, Union
import logging
from pathlib import Path

from .base_service import BaseService, ServiceError

logger = logging.getLogger(__name__)


class PipelineService(BaseService):
    """Service for pipeline management operations"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        
    async def list_json_pipelines(self) -> Dict[str, Any]:
        """
        List all available JSON pipelines
        
        Returns:
            Dict containing list of available pipelines
        """
        try:
            return await self._make_request('GET', '/api/pipelines/json')
        except Exception as e:
            logger.error(f"Failed to list JSON pipelines: {e}")
            raise ServiceError(f"Pipeline listing failed: {str(e)}")
    
    async def get_json_pipeline(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Get specific JSON pipeline configuration
        
        Args:
            pipeline_name: Name of the pipeline to retrieve
            
        Returns:
            Dict containing pipeline configuration
        """
        try:
            return await self._make_request('GET', f'/api/pipelines/json/{pipeline_name}')
        except Exception as e:
            logger.error(f"Failed to get JSON pipeline {pipeline_name}: {e}")
            raise ServiceError(f"Pipeline retrieval failed for {pipeline_name}: {str(e)}")
    
    async def toggle_json_pipeline(
        self,
        pipeline_name: str,
        enabled: bool
    ) -> Dict[str, Any]:
        """
        Toggle JSON pipeline enabled/disabled state
        
        Args:
            pipeline_name: Name of the pipeline to toggle
            enabled: Whether to enable or disable the pipeline
            
        Returns:
            Dict containing toggle operation result
        """
        try:
            payload = {
                "pipeline_name": pipeline_name,
                "enabled": enabled
            }
            return await self._make_request('POST', '/api/pipelines/toggle-json', json_data=payload)
        except Exception as e:
            logger.error(f"Failed to toggle JSON pipeline {pipeline_name}: {e}")
            raise ServiceError(f"Pipeline toggle failed for {pipeline_name}: {str(e)}")
    
    # Convenience methods for common operations
    async def enable_pipeline(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Enable a specific pipeline
        
        Args:
            pipeline_name: Name of the pipeline to enable
            
        Returns:
            Dict containing enable operation result
        """
        return await self.toggle_json_pipeline(pipeline_name, enabled=True)
    
    async def disable_pipeline(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Disable a specific pipeline
        
        Args:
            pipeline_name: Name of the pipeline to disable
            
        Returns:
            Dict containing disable operation result
        """
        return await self.toggle_json_pipeline(pipeline_name, enabled=False)
    
    async def get_pipeline_status(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Get comprehensive status of a pipeline
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Dict containing pipeline status information
        """
        try:
            # Get pipeline configuration
            pipeline_config = await self.get_json_pipeline(pipeline_name)
            
            # Get list of all pipelines to check status
            all_pipelines = await self.list_json_pipelines()
            
            # Find the specific pipeline in the list
            pipeline_status = None
            for pipeline in all_pipelines.get("pipelines", []):
                if pipeline.get("name") == pipeline_name:
                    pipeline_status = pipeline
                    break
            
            return {
                "pipeline_name": pipeline_name,
                "config": pipeline_config,
                "status": pipeline_status,
                "exists": pipeline_status is not None,
                "enabled": pipeline_status.get("enabled", False) if pipeline_status else False
            }
            
        except Exception as e:
            logger.error(f"Failed to get pipeline status for {pipeline_name}: {e}")
            raise ServiceError(f"Pipeline status retrieval failed: {str(e)}")
    
    async def get_all_pipeline_statuses(self) -> Dict[str, Any]:
        """
        Get status of all available pipelines
        
        Returns:
            Dict containing all pipeline statuses
        """
        try:
            all_pipelines = await self.list_json_pipelines()
            
            pipeline_statuses = []
            for pipeline in all_pipelines.get("pipelines", []):
                pipeline_name = pipeline.get("name")
                if pipeline_name:
                    try:
                        status = await self.get_pipeline_status(pipeline_name)
                        pipeline_statuses.append(status)
                    except Exception as e:
                        logger.warning(f"Failed to get status for pipeline {pipeline_name}: {e}")
                        pipeline_statuses.append({
                            "pipeline_name": pipeline_name,
                            "error": str(e),
                            "exists": False,
                            "enabled": False
                        })
            
            return {
                "total_pipelines": len(pipeline_statuses),
                "enabled_count": sum(1 for p in pipeline_statuses if p.get("enabled", False)),
                "disabled_count": sum(1 for p in pipeline_statuses if not p.get("enabled", False)),
                "pipelines": pipeline_statuses
            }
            
        except Exception as e:
            logger.error(f"Failed to get all pipeline statuses: {e}")
            raise ServiceError(f"All pipelines status retrieval failed: {str(e)}")
    
    async def validate_pipeline(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Validate a pipeline configuration
        
        Args:
            pipeline_name: Name of the pipeline to validate
            
        Returns:
            Dict containing validation results
        """
        try:
            pipeline_config = await self.get_json_pipeline(pipeline_name)
            
            # Basic validation checks
            validation_results = {
                "pipeline_name": pipeline_name,
                "valid": True,
                "issues": [],
                "warnings": []
            }
            
            # Check if config is valid JSON
            if not isinstance(pipeline_config, dict):
                validation_results["valid"] = False
                validation_results["issues"].append("Pipeline configuration is not valid JSON")
                return validation_results
            
            # Check for required fields (adjust based on your pipeline structure)
            if "pipeline" not in pipeline_config:
                validation_results["issues"].append("Missing 'pipeline' section")
                validation_results["valid"] = False
            
            # Check pipeline array
            pipeline_array = pipeline_config.get("pipeline", [])
            if not isinstance(pipeline_array, list):
                validation_results["issues"].append("Pipeline should be an array")
                validation_results["valid"] = False
            elif len(pipeline_array) == 0:
                validation_results["warnings"].append("Pipeline is empty")
            
            # Validate each stage
            for i, stage in enumerate(pipeline_array):
                if not isinstance(stage, dict):
                    validation_results["issues"].append(f"Stage {i} is not a valid object")
                    validation_results["valid"] = False
                    continue
                
                if "type" not in stage:
                    validation_results["issues"].append(f"Stage {i} missing 'type' field")
                    validation_results["valid"] = False
                
                # Check for common issues
                stage_type = stage.get("type", "")
                if stage_type.startswith("readers.") and "filename" not in stage:
                    validation_results["warnings"].append(f"Reader stage {i} missing 'filename'")
                elif stage_type.startswith("writers.") and "filename" not in stage:
                    validation_results["warnings"].append(f"Writer stage {i} missing 'filename'")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Failed to validate pipeline {pipeline_name}: {e}")
            return {
                "pipeline_name": pipeline_name,
                "valid": False,
                "issues": [f"Validation failed: {str(e)}"],
                "warnings": []
            }
    
    async def bulk_pipeline_operation(
        self,
        operation: str,
        pipeline_names: List[str]
    ) -> Dict[str, Any]:
        """
        Perform bulk operations on multiple pipelines
        
        Args:
            operation: Operation to perform ('enable', 'disable', 'validate')
            pipeline_names: List of pipeline names
            
        Returns:
            Dict containing bulk operation results
        """
        try:
            results = []
            success_count = 0
            
            for pipeline_name in pipeline_names:
                try:
                    if operation == 'enable':
                        result = await self.enable_pipeline(pipeline_name)
                    elif operation == 'disable':
                        result = await self.disable_pipeline(pipeline_name)
                    elif operation == 'validate':
                        result = await self.validate_pipeline(pipeline_name)
                    else:
                        result = {
                            "pipeline_name": pipeline_name,
                            "success": False,
                            "error": f"Unknown operation: {operation}"
                        }
                    
                    if result.get("success", result.get("valid", False)):
                        success_count += 1
                    
                    results.append({
                        "pipeline_name": pipeline_name,
                        "operation": operation,
                        "result": result
                    })
                    
                except Exception as e:
                    logger.error(f"Failed {operation} for pipeline {pipeline_name}: {e}")
                    results.append({
                        "pipeline_name": pipeline_name,
                        "operation": operation,
                        "result": {
                            "success": False,
                            "error": str(e)
                        }
                    })
            
            return {
                "operation": operation,
                "total_pipelines": len(pipeline_names),
                "success_count": success_count,
                "failure_count": len(pipeline_names) - success_count,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Failed bulk operation {operation}: {e}")
            raise ServiceError(f"Bulk {operation} operation failed: {str(e)}")
    
    async def get_pipeline_health(self) -> Dict[str, Any]:
        """
        Get overall pipeline system health
        
        Returns:
            Dict containing system health information
        """
        try:
            all_statuses = await self.get_all_pipeline_statuses()
            
            # Count different states
            total = all_statuses["total_pipelines"]
            enabled = all_statuses["enabled_count"]
            disabled = all_statuses["disabled_count"]
            
            # Validate all pipelines
            validation_results = []
            valid_count = 0
            
            for pipeline_status in all_statuses["pipelines"]:
                pipeline_name = pipeline_status["pipeline_name"]
                try:
                    validation = await self.validate_pipeline(pipeline_name)
                    validation_results.append(validation)
                    if validation.get("valid", False):
                        valid_count += 1
                except:
                    validation_results.append({
                        "pipeline_name": pipeline_name,
                        "valid": False,
                        "issues": ["Validation failed"]
                    })
            
            health_score = (valid_count / total * 100) if total > 0 else 100
            
            return {
                "total_pipelines": total,
                "enabled_pipelines": enabled,
                "disabled_pipelines": disabled,
                "valid_pipelines": valid_count,
                "invalid_pipelines": total - valid_count,
                "health_score": round(health_score, 1),
                "healthy": health_score >= 90,
                "validation_results": validation_results,
                "summary": {
                    "status": "healthy" if health_score >= 90 else "degraded" if health_score >= 70 else "unhealthy",
                    "message": f"{valid_count}/{total} pipelines are valid ({health_score:.1f}% health score)"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get pipeline health: {e}")
            raise ServiceError(f"Pipeline health check failed: {str(e)}")
