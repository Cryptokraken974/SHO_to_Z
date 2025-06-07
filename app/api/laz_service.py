"""
LAZ Information Service
Provides comprehensive information about LAZ/LAS point cloud files including:
- Coordinate systems and bounds
- Point count and density
- Classification statistics
- Spatial information
- Quality metrics
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json
import logging
import subprocess
import tempfile
from datetime import datetime

from .base_service import BaseService

logger = logging.getLogger(__name__)


class LAZService(BaseService):
    """Service for LAZ/LAS file information and analysis"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        self.base_dir = Path(__file__).parent.parent.parent
        self.laz_input_dir = self.base_dir / "input" / "LAZ"
        self.laz_output_dir = self.base_dir / "output" / "LAZ"
        
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive information about a LAZ/LAS file"""
        return await self._get('/api/laz/info', params={'file_path': file_path})
    
    async def get_file_bounds(self, file_path: str) -> Dict[str, Any]:
        """Get spatial bounds of a LAZ/LAS file"""
        return await self._get('/api/laz/bounds', params={'file_path': file_path})
    
    async def get_file_bounds_wgs84(self, file_path: str, src_epsg: int = 31978) -> Dict[str, Any]:
        """Get spatial bounds of a LAZ/LAS file transformed to WGS84 coordinates"""
        return await self._get('/api/laz/bounds-wgs84', params={'file_path': file_path, 'src_epsg': src_epsg})
    
    async def get_point_count(self, file_path: str) -> Dict[str, Any]:
        """Get point count and density information"""
        return await self._get('/api/laz/point-count', params={'file_path': file_path})
    
    async def get_classification_stats(self, file_path: str) -> Dict[str, Any]:
        """Get point classification statistics"""
        return await self._get('/api/laz/classification-stats', params={'file_path': file_path})
    
    async def get_coordinate_system(self, file_path: str) -> Dict[str, Any]:
        """Get coordinate reference system information"""
        return await self._get('/api/laz/coordinate-system', params={'file_path': file_path})
    
    async def get_elevation_stats(self, file_path: str) -> Dict[str, Any]:
        """Get elevation statistics (min, max, mean, std)"""
        return await self._get('/api/laz/elevation-stats', params={'file_path': file_path})
    
    async def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get general file metadata"""
        return await self._get('/api/laz/metadata', params={'file_path': file_path})
    
    async def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate LAZ/LAS file integrity"""
        return await self._get('/api/laz/validate', params={'file_path': file_path})
    
    async def get_intensity_stats(self, file_path: str) -> Dict[str, Any]:
        """Get intensity value statistics"""
        return await self._get('/api/laz/intensity-stats', params={'file_path': file_path})
    
    async def get_return_stats(self, file_path: str) -> Dict[str, Any]:
        """Get return number statistics"""
        return await self._get('/api/laz/return-stats', params={'file_path': file_path})
    
    async def list_files_with_info(self) -> Dict[str, Any]:
        """List all LAZ files with basic info"""
        return await self._get('/api/laz/files-with-info')
    
    async def compare_files(self, file1_path: str, file2_path: str) -> Dict[str, Any]:
        """Compare two LAZ files"""
        return await self._get('/api/laz/compare', params={
            'file1_path': file1_path,
            'file2_path': file2_path
        })
    
    async def get_spatial_index_info(self, file_path: str) -> Dict[str, Any]:
        """Get spatial indexing information"""
        return await self._get('/api/laz/spatial-index', params={'file_path': file_path})
    
    async def get_quality_metrics(self, file_path: str) -> Dict[str, Any]:
        """Get data quality metrics"""
        return await self._get('/api/laz/quality-metrics', params={'file_path': file_path})
    
    # Local utility methods for complex analysis
    def _analyze_with_pdal(self, file_path: Path) -> Dict[str, Any]:
        """Analyze LAZ file using PDAL for detailed information"""
        try:
            # Create PDAL pipeline for info extraction
            pipeline = {
                "pipeline": [
                    str(file_path),
                    {
                        "type": "filters.info",
                        "summary": True,
                        "stats": True
                    }
                ]
            }
            
            # Write pipeline to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(pipeline, f)
                pipeline_file = f.name
            
            try:
                # Run PDAL info command
                result = subprocess.run([
                    'pdal', 'pipeline', pipeline_file
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    # Parse PDAL output (usually goes to stderr for info)
                    return self._parse_pdal_info_output(result.stderr)
                else:
                    logger.error(f"PDAL failed: {result.stderr}")
                    return {"error": f"PDAL analysis failed: {result.stderr}"}
                    
            finally:
                # Clean up temporary file
                Path(pipeline_file).unlink(missing_ok=True)
                
        except subprocess.TimeoutExpired:
            logger.error("PDAL analysis timed out")
            return {"error": "Analysis timed out"}
        except Exception as e:
            logger.error(f"PDAL analysis error: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _parse_pdal_info_output(self, pdal_output: str) -> Dict[str, Any]:
        """Parse PDAL info command output"""
        try:
            # PDAL info output is typically JSON-like
            # This is a simplified parser - PDAL output format may vary
            info = {}
            lines = pdal_output.split('\n')
            
            for line in lines:
                line = line.strip()
                if 'point count:' in line.lower():
                    info['point_count'] = int(line.split(':')[1].strip())
                elif 'bounds:' in line.lower():
                    # Extract bounds information
                    pass  # Implementation depends on PDAL output format
                    
            return info
            
        except Exception as e:
            logger.error(f"Error parsing PDAL output: {str(e)}")
            return {"error": "Failed to parse PDAL output"}
    
    def _get_file_stats(self, file_path: Path) -> Dict[str, Any]:
        """Get basic file system statistics"""
        try:
            stat = file_path.stat()
            return {
                "file_size_bytes": stat.st_size,
                "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting file stats: {str(e)}")
            return {"error": f"Failed to get file stats: {str(e)}"}
    
    def _validate_laz_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate LAZ file using basic checks"""
        try:
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Basic file checks
            if not file_path.exists():
                validation_results["valid"] = False
                validation_results["errors"].append("File does not exist")
                return validation_results
            
            if file_path.stat().st_size == 0:
                validation_results["valid"] = False
                validation_results["errors"].append("File is empty")
                return validation_results
            
            # Check file extension
            if file_path.suffix.lower() not in ['.laz', '.las']:
                validation_results["warnings"].append("Unexpected file extension")
            
            # More detailed validation would require PDAL or laspy
            # For now, we'll use basic checks
            
            return validation_results
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": []
            }
