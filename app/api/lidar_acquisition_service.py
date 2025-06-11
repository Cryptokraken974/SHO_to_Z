"""
LIDAR Acquisition Service

Provides LIDAR data acquisition functionality including:
- LIDAR data acquisition from various providers
- Provider management and discovery
- LIDAR data processing workflows
- Quality assessment and validation
"""

from typing import Dict, Any, List, Optional, Union
import logging
from pathlib import Path

from .base_service import BaseService, ServiceError

logger = logging.getLogger(__name__)


class LidarAcquisitionService(BaseService):
    """Service for LIDAR data acquisition operations"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        
    async def acquire_lidar(
        self,
        location: Dict[str, Any],
        provider: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Acquire LIDAR data for a specific location
        
        Args:
            location: Geographic location (lat, lon, bounds, region)
            provider: Preferred LIDAR data provider
            parameters: Additional acquisition parameters
            
        Returns:
            Dict containing acquisition results
        """
        try:
            payload = {
                "location": location
            }
            if provider:
                payload["provider"] = provider
            if parameters:
                payload["parameters"] = parameters
                
            return await self._make_request('POST', '/api/acquire-lidar', json_data=payload)
        except Exception as e:
            logger.error(f"Failed to acquire LIDAR data: {e}")
            raise ServiceError(f"LIDAR acquisition failed: {str(e)}")
    
    async def get_providers(self) -> Dict[str, Any]:
        """
        Get list of available LIDAR data providers
        
        Returns:
            Dict containing provider information
        """
        try:
            return await self._make_request('GET', '/api/lidar/providers')
        except Exception as e:
            logger.error(f"Failed to get LIDAR providers: {e}")
            raise ServiceError(f"Provider listing failed: {str(e)}")
    
    async def process_lidar(
        self,
        file_path: str,
        processing_type: str = "basic",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process LIDAR data with specified parameters
        
        Args:
            file_path: Path to LIDAR file to process
            processing_type: Type of processing (basic, advanced, custom)
            parameters: Processing parameters
            
        Returns:
            Dict containing processing results
        """
        try:
            payload = {
                "file_path": file_path,
                "processing_type": processing_type
            }
            if parameters:
                payload["parameters"] = parameters
                
            return await self._make_request('POST', '/api/process-lidar', json_data=payload)
        except Exception as e:
            logger.error(f"Failed to process LIDAR data: {e}")
            raise ServiceError(f"LIDAR processing failed: {str(e)}")
    
    # Convenience methods for common workflows
    async def get_provider_details(self, provider_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific provider
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Dict containing provider details
        """
        try:
            providers = await self.get_providers()
            
            for provider in providers.get("providers", []):
                if provider.get("name") == provider_name:
                    return provider
                    
            raise ServiceError(f"Provider '{provider_name}' not found")
        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to get provider details for {provider_name}: {e}")
            raise ServiceError(f"Provider details retrieval failed: {str(e)}")
    
    async def find_best_provider(
        self, 
        location: Dict[str, Any],
        criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Find the best LIDAR provider for a given location and criteria
        
        Args:
            location: Geographic location
            criteria: Selection criteria (resolution, coverage, cost, etc.)
            
        Returns:
            Dict containing best provider recommendation
        """
        try:
            providers = await self.get_providers()
            
            # Default criteria if none provided
            if not criteria:
                criteria = {
                    "prefer_high_resolution": True,
                    "prefer_recent_data": True,
                    "prefer_full_coverage": True
                }
            
            # Simple scoring algorithm (could be enhanced)
            best_provider = None
            best_score = -1
            
            for provider in providers.get("providers", []):
                score = self._score_provider(provider, location, criteria)
                if score > best_score:
                    best_score = score
                    best_provider = provider
            
            return {
                "recommended_provider": best_provider,
                "score": best_score,
                "criteria": criteria,
                "all_providers": providers.get("providers", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to find best provider: {e}")
            raise ServiceError(f"Provider selection failed: {str(e)}")
    
    async def acquire_and_process(
        self,
        location: Dict[str, Any],
        processing_type: str = "basic",
        provider: Optional[str] = None,
        acquisition_params: Optional[Dict[str, Any]] = None,
        processing_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete workflow: acquire LIDAR data and process it
        
        Args:
            location: Geographic location
            processing_type: Type of processing to apply
            provider: Preferred provider (auto-select if None)
            acquisition_params: Parameters for acquisition
            processing_params: Parameters for processing
            
        Returns:
            Dict containing complete workflow results
        """
        try:
            # Auto-select provider if not specified
            if not provider:
                provider_selection = await self.find_best_provider(location)
                recommended_provider = provider_selection.get("recommended_provider")
                if recommended_provider:
                    provider = recommended_provider.get("name")
                    logger.info(f"Auto-selected provider: {provider}")
            
            # Acquire the data
            logger.info(f"Starting LIDAR acquisition for location: {location}")
            acquisition_result = await self.acquire_lidar(
                location=location,
                provider=provider,
                parameters=acquisition_params
            )
            
            if not acquisition_result.get("success", False):
                return {
                    "success": False,
                    "stage": "acquisition",
                    "acquisition_result": acquisition_result,
                    "processing_result": None,
                    "message": "LIDAR acquisition failed"
                }
            
            # Extract file path from acquisition result
            acquired_files = acquisition_result.get("files", [])
            if not acquired_files:
                return {
                    "success": False,
                    "stage": "acquisition",
                    "acquisition_result": acquisition_result,
                    "processing_result": None,
                    "message": "No files acquired"
                }
            
            # Process each acquired file
            processing_results = []
            for file_info in acquired_files:
                file_path = file_info.get("path") or file_info.get("file_path")
                if file_path:
                    logger.info(f"Processing LIDAR file: {file_path}")
                    processing_result = await self.process_lidar(
                        file_path=file_path,
                        processing_type=processing_type,
                        parameters=processing_params
                    )
                    processing_results.append(processing_result)
            
            return {
                "success": True,
                "acquisition_result": acquisition_result,
                "processing_results": processing_results,
                "provider_used": provider,
                "files_processed": len(processing_results),
                "message": f"Successfully acquired and processed {len(processing_results)} LIDAR files"
            }
            
        except Exception as e:
            logger.error(f"Failed to acquire and process LIDAR: {e}")
            raise ServiceError(f"LIDAR acquisition and processing workflow failed: {str(e)}")
    
    async def validate_lidar_data(
        self,
        file_path: str,
        validation_level: str = "basic"
    ) -> Dict[str, Any]:
        """
        Validate LIDAR data quality and integrity
        
        Args:
            file_path: Path to LIDAR file
            validation_level: Level of validation (basic, standard, comprehensive)
            
        Returns:
            Dict containing validation results
        """
        try:
            # Use the processing endpoint with validation parameters
            validation_params = {
                "validation_only": True,
                "validation_level": validation_level
            }
            
            return await self.process_lidar(
                file_path=file_path,
                processing_type="validation",
                parameters=validation_params
            )
            
        except Exception as e:
            logger.error(f"Failed to validate LIDAR data: {e}")
            raise ServiceError(f"LIDAR validation failed: {str(e)}")
    
    async def get_acquisition_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of an ongoing acquisition job
        
        Args:
            job_id: ID of the acquisition job
            
        Returns:
            Dict containing job status
        """
        try:
            return await self._make_request('GET', f'/api/lidar/status/{job_id}')
        except Exception as e:
            logger.error(f"Failed to get acquisition status: {e}")
            raise ServiceError(f"Status retrieval failed: {str(e)}")
    
    def _score_provider(
        self,
        provider: Dict[str, Any],
        location: Dict[str, Any],
        criteria: Dict[str, Any]
    ) -> float:
        """
        Score a provider based on location and criteria
        
        Args:
            provider: Provider information
            location: Target location
            criteria: Scoring criteria
            
        Returns:
            Provider score (higher is better)
        """
        score = 0.0
        
        # Base score
        score += 1.0
        
        # Resolution preference
        if criteria.get("prefer_high_resolution", False):
            resolution = provider.get("max_resolution", 1.0)
            if resolution <= 0.5:  # High resolution (0.5m or better)
                score += 2.0
            elif resolution <= 1.0:  # Medium resolution
                score += 1.0
        
        # Coverage preference
        if criteria.get("prefer_full_coverage", False):
            coverage = provider.get("coverage_percentage", 0)
            score += coverage / 100.0  # 0-1 points based on coverage
        
        # Data recency preference
        if criteria.get("prefer_recent_data", False):
            max_age_years = provider.get("max_data_age_years", 10)
            if max_age_years <= 2:  # Very recent
                score += 1.5
            elif max_age_years <= 5:  # Recent
                score += 1.0
            elif max_age_years <= 10:  # Acceptable
                score += 0.5
        
        # Cost consideration (if provided)
        cost_factor = provider.get("cost_factor", 1.0)
        if criteria.get("prefer_low_cost", False):
            score += (2.0 - cost_factor)  # Lower cost = higher score
        
        # Reliability factor
        reliability = provider.get("reliability_score", 0.8)
        score *= reliability  # Multiply by reliability
        
        return max(0.0, score)  # Ensure non-negative score
