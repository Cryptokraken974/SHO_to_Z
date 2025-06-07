/**
 * Analysis Manager for Region Analysis
 * 
 * Handles region analysis operations using the RegionAnalysisService.
 * Provides UI integration for various analysis types and result visualization.
 */

window.AnalysisManager = {
  /**
   * Initialize the Analysis Manager
   */
  init() {
    this.analysisResults = {};
    this.activeAnalyses = new Set();
    this.initializeEventHandlers();
    Utils.log('info', 'Analysis Manager initialized');
  },

  /**
   * Initialize event handlers for analysis tools
   */
  initializeEventHandlers() {
    // Statistical Analysis button
    $(document).on('click', '#statistical-analysis-btn', () => {
      this.performStatisticalAnalysis();
    });

    // Terrain Analysis button
    $(document).on('click', '#terrain-analysis-btn', () => {
      this.performTerrainAnalysis();
    });

    // Comparative Analysis button
    $(document).on('click', '#comparative-analysis-btn', () => {
      this.performComparativeAnalysis();
    });

    // Vegetation Analysis button
    $(document).on('click', '#vegetation-analysis-btn', () => {
      this.performVegetationAnalysis();
    });

    // Hydrological Analysis button
    $(document).on('click', '#hydrological-analysis-btn', () => {
      this.performHydrologicalAnalysis();
    });

    // Slope Stability Analysis button
    $(document).on('click', '#slope-stability-btn', () => {
      this.performSlopeStabilityAnalysis();
    });

    // Erosion Assessment button
    $(document).on('click', '#erosion-assessment-btn', () => {
      this.performErosionAssessment();
    });

    // Solar Potential Analysis button
    $(document).on('click', '#solar-potential-btn', () => {
      this.performSolarPotentialAnalysis();
    });

    // Biodiversity Metrics button
    $(document).on('click', '#biodiversity-metrics-btn', () => {
      this.performBiodiversityAnalysis();
    });

    // Generate Report button
    $(document).on('click', '#generate-report-btn', () => {
      this.generateAnalysisReport();
    });

    // Export Results button
    $(document).on('click', '#export-results-btn', () => {
      this.exportAnalysisResults();
    });

    // Analysis History button
    $(document).on('click', '#analysis-history-btn', () => {
      this.showAnalysisHistory();
    });
  },

  /**
   * Get the currently selected region
   * @returns {string|null} Currently selected region name
   */
  getCurrentRegion() {
    return FileManager.getSelectedRegion() || UIManager.globalSelectedRegion;
  },

  /**
   * Check if a region is selected
   * @returns {boolean} True if a region is selected
   */
  isRegionSelected() {
    const region = this.getCurrentRegion();
    return region && region.trim() !== '';
  },

  /**
   * Show analysis not available message
   * @param {string} analysisType - Type of analysis
   */
  showNoRegionMessage(analysisType) {
    Utils.showNotification(`Please select a region first to perform ${analysisType}`, 'warning');
    Utils.log('warn', `${analysisType} attempted without region selection`);
  },

  /**
   * Show analysis in progress message
   * @param {string} analysisType - Type of analysis
   */
  showAnalysisInProgress(analysisType) {
    Utils.showNotification(`${analysisType} is already in progress`, 'info');
  },

  /**
   * Perform statistical analysis
   */
  async performStatisticalAnalysis() {
    const regionName = this.getCurrentRegion();
    if (!this.isRegionSelected()) {
      this.showNoRegionMessage('Statistical Analysis');
      return;
    }

    const analysisId = `stats_${regionName}`;
    if (this.activeAnalyses.has(analysisId)) {
      this.showAnalysisInProgress('Statistical Analysis');
      return;
    }

    try {
      this.activeAnalyses.add(analysisId);
      Utils.showNotification('Starting statistical analysis...', 'info');
      
      const analysisTypes = ['elevation', 'slope', 'aspect', 'terrain_metrics'];
      const result = await regionAnalysis().calculateRegionStatistics(regionName, analysisTypes);
      
      this.analysisResults[analysisId] = result;
      this.displayStatisticalResults(result, regionName);
      
      Utils.showNotification('Statistical analysis completed', 'success');
      Utils.log('info', 'Statistical analysis completed for region:', regionName);

    } catch (error) {
      Utils.log('error', 'Statistical analysis failed:', error);
      Utils.showNotification(`Statistical analysis failed: ${error.message}`, 'error');
    } finally {
      this.activeAnalyses.delete(analysisId);
    }
  },

  /**
   * Perform comprehensive terrain analysis
   */
  async performTerrainAnalysis() {
    const regionName = this.getCurrentRegion();
    if (!this.isRegionSelected()) {
      this.showNoRegionMessage('Terrain Analysis');
      return;
    }

    const analysisId = `terrain_${regionName}`;
    if (this.activeAnalyses.has(analysisId)) {
      this.showAnalysisInProgress('Terrain Analysis');
      return;
    }

    try {
      this.activeAnalyses.add(analysisId);
      Utils.showNotification('Starting terrain analysis...', 'info');
      
      const result = await regionAnalysis().analyzeRegionTerrain(regionName);
      
      this.analysisResults[analysisId] = result;
      this.displayTerrainResults(result, regionName);
      
      Utils.showNotification('Terrain analysis completed', 'success');
      Utils.log('info', 'Terrain analysis completed for region:', regionName);

    } catch (error) {
      Utils.log('error', 'Terrain analysis failed:', error);
      Utils.showNotification(`Terrain analysis failed: ${error.message}`, 'error');
    } finally {
      this.activeAnalyses.delete(analysisId);
    }
  },

  /**
   * Perform comparative analysis
   */
  async performComparativeAnalysis() {
    const regionName = this.getCurrentRegion();
    if (!this.isRegionSelected()) {
      this.showNoRegionMessage('Comparative Analysis');
      return;
    }

    // For now, we'll show a modal to select the second region
    // In a full implementation, this would be a more sophisticated UI
    const secondRegion = prompt('Enter the name of the second region to compare with:');
    if (!secondRegion || secondRegion.trim() === '') {
      Utils.showNotification('Comparative analysis cancelled', 'info');
      return;
    }

    const analysisId = `compare_${regionName}_${secondRegion}`;
    if (this.activeAnalyses.has(analysisId)) {
      this.showAnalysisInProgress('Comparative Analysis');
      return;
    }

    try {
      this.activeAnalyses.add(analysisId);
      Utils.showNotification('Starting comparative analysis...', 'info');
      
      const metrics = ['elevation', 'slope', 'aspect', 'terrain_roughness'];
      const result = await regionAnalysis().compareRegions(regionName, secondRegion, metrics);
      
      this.analysisResults[analysisId] = result;
      this.displayComparativeResults(result, regionName, secondRegion);
      
      Utils.showNotification('Comparative analysis completed', 'success');
      Utils.log('info', 'Comparative analysis completed:', regionName, 'vs', secondRegion);

    } catch (error) {
      Utils.log('error', 'Comparative analysis failed:', error);
      Utils.showNotification(`Comparative analysis failed: ${error.message}`, 'error');
    } finally {
      this.activeAnalyses.delete(analysisId);
    }
  },

  /**
   * Perform vegetation analysis
   */
  async performVegetationAnalysis() {
    const regionName = this.getCurrentRegion();
    if (!this.isRegionSelected()) {
      this.showNoRegionMessage('Vegetation Analysis');
      return;
    }

    const analysisId = `vegetation_${regionName}`;
    if (this.activeAnalyses.has(analysisId)) {
      this.showAnalysisInProgress('Vegetation Analysis');
      return;
    }

    try {
      this.activeAnalyses.add(analysisId);
      Utils.showNotification('Starting vegetation analysis...', 'info');
      
      const indices = ['NDVI', 'EVI', 'LAI', 'canopy_height'];
      const result = await regionAnalysis().calculateVegetationIndices(regionName, indices);
      
      this.analysisResults[analysisId] = result;
      this.displayVegetationResults(result, regionName);
      
      Utils.showNotification('Vegetation analysis completed', 'success');
      Utils.log('info', 'Vegetation analysis completed for region:', regionName);

    } catch (error) {
      Utils.log('error', 'Vegetation analysis failed:', error);
      Utils.showNotification(`Vegetation analysis failed: ${error.message}`, 'error');
    } finally {
      this.activeAnalyses.delete(analysisId);
    }
  },

  /**
   * Perform hydrological analysis
   */
  async performHydrologicalAnalysis() {
    const regionName = this.getCurrentRegion();
    if (!this.isRegionSelected()) {
      this.showNoRegionMessage('Hydrological Analysis');
      return;
    }

    const analysisId = `hydro_${regionName}`;
    if (this.activeAnalyses.has(analysisId)) {
      this.showAnalysisInProgress('Hydrological Analysis');
      return;
    }

    try {
      this.activeAnalyses.add(analysisId);
      Utils.showNotification('Starting hydrological analysis...', 'info');
      
      const result = await regionAnalysis().performHydrologicalAnalysis(regionName);
      
      this.analysisResults[analysisId] = result;
      this.displayHydrologicalResults(result, regionName);
      
      Utils.showNotification('Hydrological analysis completed', 'success');
      Utils.log('info', 'Hydrological analysis completed for region:', regionName);

    } catch (error) {
      Utils.log('error', 'Hydrological analysis failed:', error);
      Utils.showNotification(`Hydrological analysis failed: ${error.message}`, 'error');
    } finally {
      this.activeAnalyses.delete(analysisId);
    }
  },

  /**
   * Perform slope stability analysis
   */
  async performSlopeStabilityAnalysis() {
    const regionName = this.getCurrentRegion();
    if (!this.isRegionSelected()) {
      this.showNoRegionMessage('Slope Stability Analysis');
      return;
    }

    const analysisId = `slope_stability_${regionName}`;
    if (this.activeAnalyses.has(analysisId)) {
      this.showAnalysisInProgress('Slope Stability Analysis');
      return;
    }

    try {
      this.activeAnalyses.add(analysisId);
      Utils.showNotification('Starting slope stability analysis...', 'info');
      
      const safetyThreshold = 1.5; // Default safety factor
      const result = await regionAnalysis().calculateSlopeStability(regionName, safetyThreshold);
      
      this.analysisResults[analysisId] = result;
      this.displaySlopeStabilityResults(result, regionName);
      
      Utils.showNotification('Slope stability analysis completed', 'success');
      Utils.log('info', 'Slope stability analysis completed for region:', regionName);

    } catch (error) {
      Utils.log('error', 'Slope stability analysis failed:', error);
      Utils.showNotification(`Slope stability analysis failed: ${error.message}`, 'error');
    } finally {
      this.activeAnalyses.delete(analysisId);
    }
  },

  /**
   * Perform erosion assessment
   */
  async performErosionAssessment() {
    const regionName = this.getCurrentRegion();
    if (!this.isRegionSelected()) {
      this.showNoRegionMessage('Erosion Assessment');
      return;
    }

    const analysisId = `erosion_${regionName}`;
    if (this.activeAnalyses.has(analysisId)) {
      this.showAnalysisInProgress('Erosion Assessment');
      return;
    }

    try {
      this.activeAnalyses.add(analysisId);
      Utils.showNotification('Starting erosion assessment...', 'info');
      
      const result = await regionAnalysis().performErosionAssessment(regionName);
      
      this.analysisResults[analysisId] = result;
      this.displayErosionResults(result, regionName);
      
      Utils.showNotification('Erosion assessment completed', 'success');
      Utils.log('info', 'Erosion assessment completed for region:', regionName);

    } catch (error) {
      Utils.log('error', 'Erosion assessment failed:', error);
      Utils.showNotification(`Erosion assessment failed: ${error.message}`, 'error');
    } finally {
      this.activeAnalyses.delete(analysisId);
    }
  },

  /**
   * Perform solar potential analysis
   */
  async performSolarPotentialAnalysis() {
    const regionName = this.getCurrentRegion();
    if (!this.isRegionSelected()) {
      this.showNoRegionMessage('Solar Potential Analysis');
      return;
    }

    const analysisId = `solar_${regionName}`;
    if (this.activeAnalyses.has(analysisId)) {
      this.showAnalysisInProgress('Solar Potential Analysis');
      return;
    }

    try {
      this.activeAnalyses.add(analysisId);
      Utils.showNotification('Starting solar potential analysis...', 'info');
      
      const panelEfficiency = 0.2; // 20% efficiency
      const result = await regionAnalysis().calculateSolarPotential(regionName, panelEfficiency);
      
      this.analysisResults[analysisId] = result;
      this.displaySolarPotentialResults(result, regionName);
      
      Utils.showNotification('Solar potential analysis completed', 'success');
      Utils.log('info', 'Solar potential analysis completed for region:', regionName);

    } catch (error) {
      Utils.log('error', 'Solar potential analysis failed:', error);
      Utils.showNotification(`Solar potential analysis failed: ${error.message}`, 'error');
    } finally {
      this.activeAnalyses.delete(analysisId);
    }
  },

  /**
   * Perform biodiversity analysis
   */
  async performBiodiversityAnalysis() {
    const regionName = this.getCurrentRegion();
    if (!this.isRegionSelected()) {
      this.showNoRegionMessage('Biodiversity Analysis');
      return;
    }

    const analysisId = `biodiversity_${regionName}`;
    if (this.activeAnalyses.has(analysisId)) {
      this.showAnalysisInProgress('Biodiversity Analysis');
      return;
    }

    try {
      this.activeAnalyses.add(analysisId);
      Utils.showNotification('Starting biodiversity analysis...', 'info');
      
      const result = await regionAnalysis().calculateBiodiversityMetrics(regionName);
      
      this.analysisResults[analysisId] = result;
      this.displayBiodiversityResults(result, regionName);
      
      Utils.showNotification('Biodiversity analysis completed', 'success');
      Utils.log('info', 'Biodiversity analysis completed for region:', regionName);

    } catch (error) {
      Utils.log('error', 'Biodiversity analysis failed:', error);
      Utils.showNotification(`Biodiversity analysis failed: ${error.message}`, 'error');
    } finally {
      this.activeAnalyses.delete(analysisId);
    }
  },

  /**
   * Generate comprehensive analysis report
   */
  async generateAnalysisReport() {
    const regionName = this.getCurrentRegion();
    if (!this.isRegionSelected()) {
      this.showNoRegionMessage('Report Generation');
      return;
    }

    try {
      Utils.showNotification('Generating analysis report...', 'info');
      
      const analysisTypes = ['terrain', 'vegetation', 'hydrology', 'statistics'];
      const format = 'pdf';
      
      const result = await regionAnalysis().generateAnalysisReport(regionName, analysisTypes, format);
      
      // Handle the report result (could be a download link or file path)
      if (result.download_url) {
        const link = document.createElement('a');
        link.href = result.download_url;
        link.download = `${regionName}_analysis_report.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        Utils.showNotification('Report generated and download started', 'success');
      } else {
        Utils.showNotification('Report generated successfully', 'success');
      }
      
      Utils.log('info', 'Analysis report generated for region:', regionName);

    } catch (error) {
      Utils.log('error', 'Report generation failed:', error);
      Utils.showNotification(`Report generation failed: ${error.message}`, 'error');
    }
  },

  /**
   * Export analysis results
   */
  async exportAnalysisResults() {
    const regionName = this.getCurrentRegion();
    if (!this.isRegionSelected()) {
      this.showNoRegionMessage('Export Results');
      return;
    }

    // For now, we'll export the most recent analysis
    const analysisIds = Object.keys(this.analysisResults).filter(id => id.includes(regionName));
    if (analysisIds.length === 0) {
      Utils.showNotification('No analysis results available for export', 'warning');
      return;
    }

    try {
      Utils.showNotification('Exporting analysis results...', 'info');
      
      // Use the most recent analysis ID
      const latestAnalysisId = analysisIds[analysisIds.length - 1];
      const format = 'geojson'; // Default export format
      
      const result = await regionAnalysis().exportAnalysisResults(regionName, latestAnalysisId, format);
      
      // Handle the export result
      if (result.download_url) {
        const link = document.createElement('a');
        link.href = result.download_url;
        link.download = `${regionName}_analysis_results.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        Utils.showNotification('Results exported and download started', 'success');
      } else {
        Utils.showNotification('Results exported successfully', 'success');
      }
      
      Utils.log('info', 'Analysis results exported for region:', regionName);

    } catch (error) {
      Utils.log('error', 'Export failed:', error);
      Utils.showNotification(`Export failed: ${error.message}`, 'error');
    }
  },

  /**
   * Show analysis history
   */
  async showAnalysisHistory() {
    try {
      Utils.showNotification('Loading analysis history...', 'info');
      
      const regionName = this.getCurrentRegion();
      const result = await regionAnalysis().getAnalysisHistory(regionName);
      
      this.displayAnalysisHistory(result, regionName);
      
      Utils.log('info', 'Analysis history loaded');

    } catch (error) {
      Utils.log('error', 'Failed to load analysis history:', error);
      Utils.showNotification(`Failed to load analysis history: ${error.message}`, 'error');
    }
  },

  // Result display methods
  
  /**
   * Display statistical analysis results
   * @param {Object} result - Analysis result data
   * @param {string} regionName - Region name
   */
  displayStatisticalResults(result, regionName) {
    const mainArea = $('#analysis-main-canvas');
    
    const content = `
      <div class="h-full overflow-y-auto">
        <div class="bg-[#1a1a1a] border border-[#404040] rounded-lg p-6 mb-6">
          <h3 class="text-white text-xl font-semibold mb-4">📊 Statistical Analysis - ${regionName}</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div class="bg-[#262626] rounded-lg p-4">
              <h4 class="text-[#00bfff] font-medium mb-2">Elevation Statistics</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Min:</span>
                  <span class="text-white">${result.elevation?.min?.toFixed(2) || 'N/A'} m</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Max:</span>
                  <span class="text-white">${result.elevation?.max?.toFixed(2) || 'N/A'} m</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Mean:</span>
                  <span class="text-white">${result.elevation?.mean?.toFixed(2) || 'N/A'} m</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Std Dev:</span>
                  <span class="text-white">${result.elevation?.std?.toFixed(2) || 'N/A'} m</span>
                </div>
              </div>
            </div>
            
            <div class="bg-[#262626] rounded-lg p-4">
              <h4 class="text-[#28a745] font-medium mb-2">Slope Statistics</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Min:</span>
                  <span class="text-white">${result.slope?.min?.toFixed(2) || 'N/A'}°</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Max:</span>
                  <span class="text-white">${result.slope?.max?.toFixed(2) || 'N/A'}°</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Mean:</span>
                  <span class="text-white">${result.slope?.mean?.toFixed(2) || 'N/A'}°</span>
                </div>
              </div>
            </div>
            
            <div class="bg-[#262626] rounded-lg p-4">
              <h4 class="text-[#ffc107] font-medium mb-2">Terrain Metrics</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Area:</span>
                  <span class="text-white">${result.area?.toFixed(2) || 'N/A'} km²</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Roughness:</span>
                  <span class="text-white">${result.roughness?.toFixed(3) || 'N/A'}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Relief:</span>
                  <span class="text-white">${result.relief?.toFixed(2) || 'N/A'} m</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="mt-6 text-xs text-[#666]">
            Analysis completed at: ${new Date().toLocaleString()}
          </div>
        </div>
      </div>
    `;
    
    mainArea.html(content);
  },

  /**
   * Display terrain analysis results
   * @param {Object} result - Analysis result data
   * @param {string} regionName - Region name
   */
  displayTerrainResults(result, regionName) {
    const mainArea = $('#analysis-main-canvas');
    
    const content = `
      <div class="h-full overflow-y-auto">
        <div class="bg-[#1a1a1a] border border-[#404040] rounded-lg p-6 mb-6">
          <h3 class="text-white text-xl font-semibold mb-4">🏔️ Terrain Analysis - ${regionName}</h3>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="space-y-4">
              <div class="bg-[#262626] rounded-lg p-4">
                <h4 class="text-[#00bfff] font-medium mb-3">Topographic Characteristics</h4>
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between">
                    <span class="text-[#ababab]">Dominant Landform:</span>
                    <span class="text-white">${result.landform || 'Mixed terrain'}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-[#ababab]">Terrain Complexity:</span>
                    <span class="text-white">${result.complexity || 'Moderate'}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-[#ababab]">Drainage Density:</span>
                    <span class="text-white">${result.drainage_density?.toFixed(3) || 'N/A'} km/km²</span>
                  </div>
                </div>
              </div>
              
              <div class="bg-[#262626] rounded-lg p-4">
                <h4 class="text-[#28a745] font-medium mb-3">Surface Characteristics</h4>
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between">
                    <span class="text-[#ababab]">Surface Roughness:</span>
                    <span class="text-white">${result.surface_roughness?.toFixed(3) || 'N/A'}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-[#ababab]">Ridge Density:</span>
                    <span class="text-white">${result.ridge_density?.toFixed(2) || 'N/A'} km/km²</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-[#ababab]">Valley Density:</span>
                    <span class="text-white">${result.valley_density?.toFixed(2) || 'N/A'} km/km²</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="bg-[#262626] rounded-lg p-4">
              <h4 class="text-[#ffc107] font-medium mb-3">Analysis Summary</h4>
              <div class="text-sm text-[#ababab] leading-relaxed">
                ${result.summary || 'Comprehensive terrain analysis completed. The region shows varied topographic characteristics with diverse landform features. Detailed metrics have been calculated for elevation, slope, aspect, and surface roughness parameters.'}
              </div>
              
              ${result.recommendations ? `
                <div class="mt-4">
                  <h5 class="text-white font-medium mb-2">Recommendations:</h5>
                  <div class="text-sm text-[#ababab]">
                    ${result.recommendations}
                  </div>
                </div>
              ` : ''}
            </div>
          </div>
          
          <div class="mt-6 text-xs text-[#666]">
            Analysis completed at: ${new Date().toLocaleString()}
          </div>
        </div>
      </div>
    `;
    
    mainArea.html(content);
  },

  /**
   * Display comparative analysis results
   * @param {Object} result - Analysis result data
   * @param {string} region1 - First region name
   * @param {string} region2 - Second region name
   */
  displayComparativeResults(result, region1, region2) {
    const mainArea = $('#analysis-main-canvas');
    
    const content = `
      <div class="h-full overflow-y-auto">
        <div class="bg-[#1a1a1a] border border-[#404040] rounded-lg p-6 mb-6">
          <h3 class="text-white text-xl font-semibold mb-4">🗺️ Comparative Analysis</h3>
          <p class="text-[#ababab] mb-6">${region1} vs ${region2}</p>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-[#262626] rounded-lg p-4">
              <h4 class="text-[#00bfff] font-medium mb-3">${region1}</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Elevation Range:</span>
                  <span class="text-white">${result.region1?.elevation_range || 'N/A'} m</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Mean Slope:</span>
                  <span class="text-white">${result.region1?.mean_slope?.toFixed(2) || 'N/A'}°</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Terrain Roughness:</span>
                  <span class="text-white">${result.region1?.roughness?.toFixed(3) || 'N/A'}</span>
                </div>
              </div>
            </div>
            
            <div class="bg-[#262626] rounded-lg p-4">
              <h4 class="text-[#28a745] font-medium mb-3">${region2}</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Elevation Range:</span>
                  <span class="text-white">${result.region2?.elevation_range || 'N/A'} m</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Mean Slope:</span>
                  <span class="text-white">${result.region2?.mean_slope?.toFixed(2) || 'N/A'}°</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-[#ababab]">Terrain Roughness:</span>
                  <span class="text-white">${result.region2?.roughness?.toFixed(3) || 'N/A'}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="mt-6 bg-[#262626] rounded-lg p-4">
            <h4 class="text-[#ffc107] font-medium mb-3">Comparison Summary</h4>
            <div class="text-sm text-[#ababab] leading-relaxed">
              ${result.comparison_summary || `Comparative analysis between ${region1} and ${region2} completed. Key differences in elevation, slope, and terrain characteristics have been identified.`}
            </div>
          </div>
          
          <div class="mt-6 text-xs text-[#666]">
            Analysis completed at: ${new Date().toLocaleString()}
          </div>
        </div>
      </div>
    `;
    
    mainArea.html(content);
  },

  /**
   * Display other analysis results with generic format
   * @param {Object} result - Analysis result data
   * @param {string} regionName - Region name
   * @param {string} analysisType - Type of analysis
   * @param {string} icon - Icon for the analysis type
   */
  displayGenericResults(result, regionName, analysisType, icon = '📊') {
    const mainArea = $('#analysis-main-canvas');
    
    const content = `
      <div class="h-full overflow-y-auto">
        <div class="bg-[#1a1a1a] border border-[#404040] rounded-lg p-6 mb-6">
          <h3 class="text-white text-xl font-semibold mb-4">${icon} ${analysisType} - ${regionName}</h3>
          
          <div class="bg-[#262626] rounded-lg p-4">
            <h4 class="text-[#00bfff] font-medium mb-3">Analysis Results</h4>
            <div class="space-y-3">
              ${Object.entries(result).map(([key, value]) => {
                if (typeof value === 'object' && value !== null) {
                  return `
                    <div class="border-l-2 border-[#404040] pl-3">
                      <div class="text-[#ababab] text-sm font-medium mb-1">${key.replace(/_/g, ' ').toUpperCase()}</div>
                      ${Object.entries(value).map(([subKey, subValue]) => `
                        <div class="flex justify-between text-sm">
                          <span class="text-[#ababab]">${subKey.replace(/_/g, ' ')}:</span>
                          <span class="text-white">${typeof subValue === 'number' ? subValue.toFixed(3) : subValue}</span>
                        </div>
                      `).join('')}
                    </div>
                  `;
                } else {
                  return `
                    <div class="flex justify-between text-sm">
                      <span class="text-[#ababab]">${key.replace(/_/g, ' ')}:</span>
                      <span class="text-white">${typeof value === 'number' ? value.toFixed(3) : value}</span>
                    </div>
                  `;
                }
              }).join('')}
            </div>
          </div>
          
          <div class="mt-6 text-xs text-[#666]">
            Analysis completed at: ${new Date().toLocaleString()}
          </div>
        </div>
      </div>
    `;
    
    mainArea.html(content);
  },

  // Specific display methods for other analysis types
  displayVegetationResults(result, regionName) {
    this.displayGenericResults(result, regionName, 'Vegetation Analysis', '🌱');
  },

  displayHydrologicalResults(result, regionName) {
    this.displayGenericResults(result, regionName, 'Hydrological Analysis', '💧');
  },

  displaySlopeStabilityResults(result, regionName) {
    this.displayGenericResults(result, regionName, 'Slope Stability Analysis', '⚠️');
  },

  displayErosionResults(result, regionName) {
    this.displayGenericResults(result, regionName, 'Erosion Assessment', '🌊');
  },

  displaySolarPotentialResults(result, regionName) {
    this.displayGenericResults(result, regionName, 'Solar Potential Analysis', '☀️');
  },

  displayBiodiversityResults(result, regionName) {
    this.displayGenericResults(result, regionName, 'Biodiversity Analysis', '🦋');
  },

  /**
   * Display analysis history
   * @param {Object} result - History data
   * @param {string} regionName - Region name (optional)
   */
  displayAnalysisHistory(result, regionName = null) {
    const mainArea = $('#analysis-main-canvas');
    
    const content = `
      <div class="h-full overflow-y-auto">
        <div class="bg-[#1a1a1a] border border-[#404040] rounded-lg p-6 mb-6">
          <h3 class="text-white text-xl font-semibold mb-4">📋 Analysis History${regionName ? ` - ${regionName}` : ''}</h3>
          
          <div class="space-y-3">
            ${(result.history || []).map(item => `
              <div class="bg-[#262626] rounded-lg p-4 hover:bg-[#303030] transition-colors">
                <div class="flex justify-between items-start mb-2">
                  <div class="text-white font-medium">${item.analysis_type || 'Unknown'}</div>
                  <div class="text-xs text-[#666]">${new Date(item.timestamp || Date.now()).toLocaleString()}</div>
                </div>
                <div class="text-sm text-[#ababab] mb-2">
                  Region: ${item.region_name || 'Unknown'}
                </div>
                <div class="text-sm text-[#ababab]">
                  Status: <span class="text-${item.status === 'completed' ? 'green' : item.status === 'failed' ? 'red' : 'yellow'}-400">
                    ${item.status || 'Unknown'}
                  </span>
                </div>
                ${item.duration ? `
                  <div class="text-xs text-[#666] mt-1">
                    Duration: ${item.duration}
                  </div>
                ` : ''}
              </div>
            `).join('')}
            
            ${(result.history || []).length === 0 ? `
              <div class="text-center text-[#666] py-8">
                No analysis history available
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;
    
    mainArea.html(content);
  }
};
