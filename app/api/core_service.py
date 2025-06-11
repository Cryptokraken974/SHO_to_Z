"""
Core Service

Provides core application functionality including:
- Application status and health checks
- File listing and management
- System information and diagnostics
- General utility operations
"""

from typing import Dict, Any, List, Optional, Union
import logging
from pathlib import Path

from .base_service import BaseService, ServiceError

logger = logging.getLogger(__name__)


class CoreService(BaseService):
    """Service for core application operations"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        
    async def get_app_status(self) -> Dict[str, Any]:
        """
        Get application status and health information
        
        Returns:
            Dict containing application status
        """
        try:
            # Use the root endpoint which should provide status
            return await self._make_request('GET', '/')
        except Exception as e:
            logger.error(f"Failed to get app status: {e}")
            raise ServiceError(f"Application status retrieval failed: {str(e)}")
    
    async def list_laz_files(self) -> Dict[str, Any]:
        """
        List available LAZ files in the system
        
        Returns:
            Dict containing LAZ file listing
        """
        try:
            return await self._make_request('GET', '/api/list-laz-files')
        except Exception as e:
            logger.error(f"Failed to list LAZ files: {e}")
            raise ServiceError(f"LAZ file listing failed: {str(e)}")
    
    # Extended core functionality methods
    async def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information
        
        Returns:
            Dict containing system information
        """
        try:
            # Get both app status and file listings
            app_status = await self.get_app_status()
            laz_files = await self.list_laz_files()
            
            return {
                "app_status": app_status,
                "laz_files": laz_files,
                "system_healthy": app_status.get("healthy", True),
                "file_count": len(laz_files.get("files", [])),
                "timestamp": app_status.get("timestamp")
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            raise ServiceError(f"System information retrieval failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check
        
        Returns:
            Dict containing health check results
        """
        try:
            health_status = {
                "healthy": True,
                "checks": {},
                "issues": [],
                "warnings": []
            }
            
            # Check app status
            try:
                app_status = await self.get_app_status()
                health_status["checks"]["app_status"] = {
                    "status": "healthy",
                    "details": app_status
                }
            except Exception as e:
                health_status["healthy"] = False
                health_status["checks"]["app_status"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["issues"].append(f"App status check failed: {e}")
            
            # Check file system access
            try:
                laz_files = await self.list_laz_files()
                health_status["checks"]["file_system"] = {
                    "status": "healthy",
                    "file_count": len(laz_files.get("files", []))
                }
            except Exception as e:
                health_status["healthy"] = False
                health_status["checks"]["file_system"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["issues"].append(f"File system check failed: {e}")
            
            # Check API connectivity
            try:
                session = await self._get_session()
                health_status["checks"]["api_connectivity"] = {
                    "status": "healthy",
                    "session_open": not session.closed
                }
            except Exception as e:
                health_status["warnings"].append(f"API connectivity check inconclusive: {e}")
                health_status["checks"]["api_connectivity"] = {
                    "status": "warning",
                    "error": str(e)
                }
            
            # Overall health determination
            if health_status["issues"]:
                health_status["overall_status"] = "unhealthy"
            elif health_status["warnings"]:
                health_status["overall_status"] = "degraded"
            else:
                health_status["overall_status"] = "healthy"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "overall_status": "unhealthy",
                "error": str(e),
                "checks": {},
                "issues": [f"Health check system failure: {e}"],
                "warnings": []
            }
    
    async def get_file_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about files in the system
        
        Returns:
            Dict containing file statistics
        """
        try:
            laz_files = await self.list_laz_files()
            files = laz_files.get("files", [])
            
            stats = {
                "total_files": len(files),
                "total_size_mb": 0,
                "file_types": {},
                "average_size_mb": 0,
                "largest_file": None,
                "smallest_file": None
            }
            
            if files:
                sizes = []
                for file_info in files:
                    # Extract file info
                    file_path = file_info.get("path", file_info.get("name", ""))
                    file_size = file_info.get("size_mb", 0)
                    
                    sizes.append(file_size)
                    stats["total_size_mb"] += file_size
                    
                    # Track file types
                    file_ext = Path(file_path).suffix.lower()
                    stats["file_types"][file_ext] = stats["file_types"].get(file_ext, 0) + 1
                    
                    # Track largest and smallest
                    if stats["largest_file"] is None or file_size > stats["largest_file"]["size_mb"]:
                        stats["largest_file"] = {
                            "path": file_path,
                            "size_mb": file_size
                        }
                    
                    if stats["smallest_file"] is None or file_size < stats["smallest_file"]["size_mb"]:
                        stats["smallest_file"] = {
                            "path": file_path,
                            "size_mb": file_size
                        }
                
                stats["average_size_mb"] = round(stats["total_size_mb"] / len(files), 2)
                stats["total_size_mb"] = round(stats["total_size_mb"], 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get file statistics: {e}")
            raise ServiceError(f"File statistics retrieval failed: {str(e)}")
    
    async def validate_system_configuration(self) -> Dict[str, Any]:
        """
        Validate system configuration and dependencies
        
        Returns:
            Dict containing validation results
        """
        try:
            validation = {
                "valid": True,
                "validations": {},
                "issues": [],
                "recommendations": []
            }
            
            # Validate app is responding
            try:
                app_status = await self.get_app_status()
                validation["validations"]["app_response"] = {
                    "valid": True,
                    "message": "Application responding normally"
                }
            except Exception as e:
                validation["valid"] = False
                validation["validations"]["app_response"] = {
                    "valid": False,
                    "error": str(e)
                }
                validation["issues"].append("Application not responding properly")
            
            # Validate file access
            try:
                laz_files = await self.list_laz_files()
                file_count = len(laz_files.get("files", []))
                validation["validations"]["file_access"] = {
                    "valid": True,
                    "file_count": file_count,
                    "message": f"File system accessible, {file_count} LAZ files found"
                }
                
                if file_count == 0:
                    validation["recommendations"].append("No LAZ files found - consider adding sample data")
                
            except Exception as e:
                validation["valid"] = False
                validation["validations"]["file_access"] = {
                    "valid": False,
                    "error": str(e)
                }
                validation["issues"].append("File system access issues")
            
            # Validate API connectivity
            try:
                session = await self._get_session()
                validation["validations"]["api_connectivity"] = {
                    "valid": True,
                    "message": "API client connectivity working"
                }
            except Exception as e:
                validation["validations"]["api_connectivity"] = {
                    "valid": False,
                    "error": str(e)
                }
                validation["issues"].append("API connectivity issues")
            
            return validation
            
        except Exception as e:
            logger.error(f"System validation failed: {e}")
            return {
                "valid": False,
                "error": str(e),
                "validations": {},
                "issues": [f"System validation failure: {e}"],
                "recommendations": ["Check system logs for detailed error information"]
            }
    
    async def get_diagnostic_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive diagnostic report
        
        Returns:
            Dict containing diagnostic information
        """
        try:
            # Gather all diagnostic information
            health_check = await self.health_check()
            system_info = await self.get_system_info()
            file_stats = await self.get_file_statistics()
            validation = await self.validate_system_configuration()
            
            report = {
                "timestamp": system_info.get("timestamp"),
                "overall_health": health_check.get("overall_status", "unknown"),
                "summary": {
                    "healthy": health_check.get("healthy", False),
                    "total_files": file_stats.get("total_files", 0),
                    "total_size_mb": file_stats.get("total_size_mb", 0),
                    "configuration_valid": validation.get("valid", False)
                },
                "detailed_results": {
                    "health_check": health_check,
                    "system_info": system_info,
                    "file_statistics": file_stats,
                    "configuration_validation": validation
                },
                "recommendations": []
            }
            
            # Collect recommendations from all sources
            if health_check.get("warnings"):
                report["recommendations"].extend(
                    [f"Health: {w}" for w in health_check["warnings"]]
                )
            
            if validation.get("recommendations"):
                report["recommendations"].extend(
                    [f"Config: {r}" for r in validation["recommendations"]]
                )
            
            # Add general recommendations based on findings
            if file_stats.get("total_files", 0) == 0:
                report["recommendations"].append("Consider adding sample LAZ files for testing")
            
            if file_stats.get("total_size_mb", 0) > 1000:  # > 1GB
                report["recommendations"].append("Large file storage detected - consider cleanup strategies")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate diagnostic report: {e}")
            raise ServiceError(f"Diagnostic report generation failed: {str(e)}")
    
    async def ping(self) -> Dict[str, Any]:
        """
        Simple ping to check if service is responsive
        
        Returns:
            Dict containing ping response
        """
        try:
            start_time = await self._get_current_time()
            app_status = await self.get_app_status()
            end_time = await self._get_current_time()
            
            return {
                "status": "ok",
                "response_time_ms": (end_time - start_time) * 1000,
                "server_responsive": True,
                "timestamp": end_time
            }
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "server_responsive": False,
                "timestamp": await self._get_current_time()
            }
    
    async def _get_current_time(self) -> float:
        """Get current time as timestamp"""
        import time
        return time.time()
