"""
Region Analysis Service

Handles region analysis operations including spatial analysis,
region comparison, and geographic data processing.
"""

from typing import Dict, Any, Optional, List
from .base_service import BaseService, SyncServiceMixin


class RegionAnalysisService(BaseService, SyncServiceMixin):
    """Service for region analysis operations"""
    
    async def analyze_region_terrain(self, region_name: str) -> Dict[str, Any]:
        """Perform comprehensive terrain analysis for a region"""
        return await self._get(f'/api/analysis/terrain/{region_name}')
    
    async def compare_regions(self, region1: str, region2: str, metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """Compare two regions using specified metrics"""
        data = {
            'region1': region1,
            'region2': region2
        }
        if metrics:
            data['metrics'] = metrics
        
        return await self._post('/api/analysis/compare-regions', json_data=data)
    
    async def calculate_region_statistics(self, region_name: str, analysis_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calculate comprehensive statistics for a region"""
        params = {}
        if analysis_types:
            params['analysis_types'] = ','.join(analysis_types)
        
        return await self._get(f'/api/analysis/statistics/{region_name}', params=params)
    
    async def detect_land_cover_change(self, region_name: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Detect land cover changes in a region over time"""
        data = {
            'region_name': region_name,
            'start_date': start_date,
            'end_date': end_date
        }
        return await self._post('/api/analysis/land-cover-change', json_data=data)
    
    async def calculate_vegetation_indices(self, region_name: str, indices: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calculate vegetation indices for a region"""
        data = {'region_name': region_name}
        if indices:
            data['indices'] = indices
        
        return await self._post('/api/analysis/vegetation-indices', json_data=data)
    
    async def perform_hydrological_analysis(self, region_name: str) -> Dict[str, Any]:
        """Perform hydrological analysis including flow direction and accumulation"""
        return await self._get(f'/api/analysis/hydrology/{region_name}')
    
    async def calculate_slope_stability(self, region_name: str, safety_factor_threshold: float = 1.5) -> Dict[str, Any]:
        """Calculate slope stability analysis"""
        data = {
            'region_name': region_name,
            'safety_factor_threshold': safety_factor_threshold
        }
        return await self._post('/api/analysis/slope-stability', json_data=data)
    
    async def detect_forest_canopy_gaps(self, region_name: str, gap_threshold: float = 5.0) -> Dict[str, Any]:
        """Detect forest canopy gaps using CHM data"""
        data = {
            'region_name': region_name,
            'gap_threshold': gap_threshold
        }
        return await self._post('/api/analysis/canopy-gaps', json_data=data)
    
    async def calculate_biodiversity_metrics(self, region_name: str) -> Dict[str, Any]:
        """Calculate biodiversity and habitat metrics"""
        return await self._get(f'/api/analysis/biodiversity/{region_name}')
    
    async def perform_erosion_assessment(self, region_name: str, rainfall_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform soil erosion risk assessment"""
        data = {'region_name': region_name}
        if rainfall_data:
            data['rainfall_data'] = rainfall_data
        
        return await self._post('/api/analysis/erosion-assessment', json_data=data)
    
    async def calculate_solar_potential(self, region_name: str, panel_efficiency: float = 0.2) -> Dict[str, Any]:
        """Calculate solar energy potential"""
        data = {
            'region_name': region_name,
            'panel_efficiency': panel_efficiency
        }
        return await self._post('/api/analysis/solar-potential', json_data=data)
    
    async def analyze_accessibility(self, region_name: str, access_points: List[Dict[str, float]]) -> Dict[str, Any]:
        """Analyze terrain accessibility from specified access points"""
        data = {
            'region_name': region_name,
            'access_points': access_points
        }
        return await self._post('/api/analysis/accessibility', json_data=data)
    
    async def detect_geological_features(self, region_name: str, feature_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Detect geological features in terrain data"""
        data = {'region_name': region_name}
        if feature_types:
            data['feature_types'] = feature_types
        
        return await self._post('/api/analysis/geological-features', json_data=data)
    
    async def calculate_carbon_storage(self, region_name: str, biomass_model: str = 'default') -> Dict[str, Any]:
        """Calculate forest carbon storage estimates"""
        data = {
            'region_name': region_name,
            'biomass_model': biomass_model
        }
        return await self._post('/api/analysis/carbon-storage', json_data=data)
    
    async def perform_flood_risk_analysis(self, region_name: str, return_periods: Optional[List[int]] = None) -> Dict[str, Any]:
        """Perform flood risk analysis"""
        data = {'region_name': region_name}
        if return_periods:
            data['return_periods'] = return_periods
        
        return await self._post('/api/analysis/flood-risk', json_data=data)
    
    async def calculate_landscape_metrics(self, region_name: str, patch_threshold: float = 0.1) -> Dict[str, Any]:
        """Calculate landscape ecology metrics"""
        data = {
            'region_name': region_name,
            'patch_threshold': patch_threshold
        }
        return await self._post('/api/analysis/landscape-metrics', json_data=data)
    
    async def analyze_microclimate(self, region_name: str, weather_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze microclimate variations based on terrain"""
        data = {'region_name': region_name}
        if weather_data:
            data['weather_data'] = weather_data
        
        return await self._post('/api/analysis/microclimate', json_data=data)
    
    async def generate_analysis_report(self, region_name: str, analysis_types: List[str], format: str = 'pdf') -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        data = {
            'region_name': region_name,
            'analysis_types': analysis_types,
            'format': format
        }
        return await self._post('/api/analysis/generate-report', json_data=data)
    
    async def export_analysis_results(self, region_name: str, analysis_id: str, format: str = 'geojson') -> Dict[str, Any]:
        """Export analysis results in specified format"""
        params = {'format': format}
        return await self._get(f'/api/analysis/export/{region_name}/{analysis_id}', params=params)
    
    async def get_analysis_history(self, region_name: Optional[str] = None) -> Dict[str, Any]:
        """Get history of analysis operations"""
        params = {}
        if region_name:
            params['region_name'] = region_name
        
        return await self._get('/api/analysis/history', params=params)
    
    async def schedule_periodic_analysis(self, region_name: str, analysis_types: List[str], 
                                       schedule: str, notification_email: Optional[str] = None) -> Dict[str, Any]:
        """Schedule periodic analysis for a region"""
        data = {
            'region_name': region_name,
            'analysis_types': analysis_types,
            'schedule': schedule
        }
        if notification_email:
            data['notification_email'] = notification_email
        
        return await self._post('/api/analysis/schedule', json_data=data)
