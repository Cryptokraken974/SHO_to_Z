/**
 * API Client for SHO to Z Application
 * 
 * JavaScript client that mirrors the Python service layer architecture.
 * Provides a clean abstraction over direct API endpoint calls.
 */

/**
 * Base API client with common functionality
 */
class BaseAPIClient {
  constructor() {
    this.baseURL = window.location.origin;
    this.timeout = 300000; // 5 minutes to accommodate large LAZ file processing
  }

  /**
   * Make an HTTP request with common error handling
   * @param {string} method - HTTP method
   * @param {string} endpoint - API endpoint (without /api prefix)
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Response data
   */
  async request(method, endpoint, options = {}) {
    const url = `${this.baseURL}/api/${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const requestOptions = {
        method,
        signal: controller.signal,
        ...options
      };

      const response = await fetch(url, requestOptions);
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new APIError(`HTTP ${response.status}: ${errorText}`, response.status);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new APIError('Request timeout', 408);
      }
      throw error;
    }
  }

  /**
   * GET request
   */
  async get(endpoint, params = {}) {
    const urlParams = new URLSearchParams(params);
    const fullEndpoint = urlParams.toString() ? `${endpoint}?${urlParams}` : endpoint;
    return this.request('GET', fullEndpoint);
  }

  /**
   * POST request with JSON body
   */
  async post(endpoint, data = {}) {
    return this.request('POST', endpoint, {
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
  }

  /**
   * POST request with FormData
   */
  async postForm(endpoint, formData) {
    return this.request('POST', endpoint, {
      body: formData
    });
  }

  /**
   * DELETE request
   */
  async delete(endpoint) {
    return this.request('DELETE', endpoint);
  }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'APIError';
    this.status = status;
  }
}

/**
 * Region Management Service
 */
class RegionAPIClient extends BaseAPIClient {
  /**
   * List all available regions
   * @param {string} source - Optional filter: 'input', 'output', or null for both
   * @returns {Promise<Object>} List of regions
   */
  async listRegions(source = null) {
    const params = source ? { source } : {};
    return this.get('list-regions', params);
  }

  /**
   * Get detailed information about a specific region
   * @param {string} regionName - Name of the region
   * @returns {Promise<Object>} Region information
   */
  async getRegionInfo(regionName) {
    return this.get(`regions/${encodeURIComponent(regionName)}`);
  }

  /**
   * Get images for a specific region
   * @param {string} regionName - Name of the region
   * @returns {Promise<Object>} Region images
   */
  async getRegionImages(regionName) {
    return this.get(`regions/${encodeURIComponent(regionName)}/images`);
  }

  /**
   * Delete a region
   * @param {string} regionName - Name of the region to delete
   * @returns {Promise<Object>} Deletion result
   */
  async deleteRegion(regionName) {
    return this.delete(`delete-region/${encodeURIComponent(regionName)}`);
  }

  /**
   * Search regions by name and source
   * @param {string} searchTerm - Search term
   * @param {string} source - Source filter
   * @returns {Promise<Object>} Search results
   */
  async searchRegions(searchTerm, source = null) {
    const params = { q: searchTerm };
    if (source) params.source = source;
    return this.get('search-regions', params);
  }
}

/**
 * Processing Service
 */
class ProcessingAPIClient extends BaseAPIClient {
  // LAZ/LAS File Operations
  
  /**
   * List all LAZ files in the input directory with metadata
   * @returns {Promise<Object>} List of LAZ files with metadata
   */
  async listLazFiles() {
    return this.get('list-laz-files');
  }

  /**
   * Load a LAZ/LAS file into the system
   * @param {File} file - The LAZ/LAS file to upload
   * @returns {Promise<Object>} Upload result
   */
  async loadLazFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.postForm('laz/load', formData);
  }

  /**
   * Get information about a LAZ file
   * @param {string} filePath - Path to the LAZ file
   * @returns {Promise<Object>} LAZ file information
   */
  async getLazInfo(filePath) {
    return this.get('laz/info', { file_path: filePath });
  }

  /**
   * Convert LAZ to DEM
   * @param {string} inputFile - Input LAZ file path
   * @returns {Promise<Object>} Conversion result
   */
  async convertLazToDem(inputFile) {
    const formData = new FormData();
    formData.append('input_file', inputFile);
    return this.postForm('laz_to_dem', formData);
  }

  /**
   * Get WGS84 bounds and center for a LAZ file.
   * @param {string} fileName - The name of the LAZ file (relative to input/LAZ).
   * @returns {Promise<Object>} Object with bounds and center coordinates.
   */
  async getLAZFileBounds(fileName) {
    if (!fileName) {
      throw new Error('File name is required for getLAZFileBounds');
    }
    // The endpoint expects the file name to be part of the path.
    // Ensure the fileName is properly encoded if it might contain special characters,
    // though for typical filenames, direct concatenation should be fine.
    return this.get(`laz/bounds-wgs84/${encodeURIComponent(fileName)}`);
  }

  // DEM Processing
  
  /**
   * Generate Digital Terrain Model (DTM) from LAZ data
   * @param {Object} options - Processing options
   * @param {string} options.inputFile - Input LAZ file path
   * @param {string} options.regionName - Region name
   * @param {string} options.processingType - Processing type
   * @param {string} options.displayRegionName - Display region name
   * @returns {Promise<Object>} DTM generation result
   */
  async generateDTM(options = {}) {
    const formData = new FormData();
    
    // Support both camelCase and snake_case parameter names for flexibility
    if (options.inputFile || options.input_file) formData.append('input_file', options.inputFile || options.input_file);
    if (options.regionName || options.region_name) formData.append('region_name', options.regionName || options.region_name);
    if (options.processingType || options.processing_type) formData.append('processing_type', options.processingType || options.processing_type);
    if (options.displayRegionName || options.display_region_name) formData.append('display_region_name', options.displayRegionName || options.display_region_name);
    
    return this.postForm('dtm', formData);
  }

  /**
   * Generate Digital Surface Model (DSM) from LAZ data
   * @param {Object} options - Processing options
   * @param {string} options.inputFile - Input LAZ file path
   * @param {string} options.regionName - Region name
   * @param {string} options.processingType - Processing type
   * @param {string} options.displayRegionName - Display region name
   * @returns {Promise<Object>} DSM generation result
   */
  async generateDSM(options = {}) {
    const formData = new FormData();
    
    // Support both camelCase and snake_case parameter names for flexibility
    if (options.inputFile || options.input_file) formData.append('input_file', options.inputFile || options.input_file);
    if (options.regionName || options.region_name) formData.append('region_name', options.regionName || options.region_name);
    if (options.processingType || options.processing_type) formData.append('processing_type', options.processingType || options.processing_type);
    if (options.displayRegionName || options.display_region_name) formData.append('display_region_name', options.displayRegionName || options.display_region_name);
    
    return this.postForm('dsm', formData);
  }

  /**
   * Generate Canopy Height Model (CHM) from LAZ data
   * @param {Object} options - Processing options
   * @param {string} options.inputFile - Input LAZ file path
   * @param {string} options.regionName - Region name
   * @param {string} options.processingType - Processing type
   * @param {string} options.displayRegionName - Display region name
   * @returns {Promise<Object>} CHM generation result
   */
  async generateCHM(options = {}) {
    const formData = new FormData();
    
    // Support both camelCase and snake_case parameter names for flexibility
    if (options.inputFile || options.input_file) formData.append('input_file', options.inputFile || options.input_file);
    if (options.regionName || options.region_name) formData.append('region_name', options.regionName || options.region_name);
    if (options.processingType || options.processing_type) formData.append('processing_type', options.processingType || options.processing_type);
    if (options.displayRegionName || options.display_region_name) formData.append('display_region_name', options.displayRegionName || options.display_region_name);
    
    return this.postForm('chm', formData);
  }

  // Terrain Analysis
  
  /**
   * Generate hillshade visualization
   * @param {Object} options - Processing options
   * @param {string} options.inputFile - Input LAZ file path
   * @param {string} options.regionName - Region name
   * @param {string} options.processingType - Processing type
   * @param {string} options.displayRegionName - Display region name
   * @returns {Promise<Object>} Hillshade generation result
   */
  async generateHillshade(options = {}) {
    const formData = new FormData();
    
    // Support both camelCase and snake_case parameter names for flexibility
    if (options.inputFile || options.input_file) formData.append('input_file', options.inputFile || options.input_file);
    if (options.regionName || options.region_name) formData.append('region_name', options.regionName || options.region_name);
    if (options.processingType || options.processing_type) formData.append('processing_type', options.processingType || options.processing_type);
    if (options.displayRegionName || options.display_region_name) formData.append('display_region_name', options.displayRegionName || options.display_region_name);
    
    return this.postForm('hillshade', formData);
  }

  /**
   * Generate slope analysis
   * @param {Object} options - Processing options
   * @param {string} options.inputFile - Input LAZ file path
   * @param {string} options.regionName - Region name
   * @param {string} options.processingType - Processing type
   * @param {string} options.displayRegionName - Display region name
   * @returns {Promise<Object>} Slope analysis result
   */
  async generateSlope(options = {}) {
    const formData = new FormData();
    
    // Support both camelCase and snake_case parameter names for flexibility
    if (options.inputFile || options.input_file) formData.append('input_file', options.inputFile || options.input_file);
    if (options.regionName || options.region_name) formData.append('region_name', options.regionName || options.region_name);
    if (options.processingType || options.processing_type) formData.append('processing_type', options.processingType || options.processing_type);
    if (options.displayRegionName || options.display_region_name) formData.append('display_region_name', options.displayRegionName || options.display_region_name);
    
    return this.postForm('slope', formData);
  }

  /**
   * Generate aspect analysis
   * @param {Object} options - Processing options
   * @param {string} options.inputFile - Input LAZ file path
   * @param {string} options.regionName - Region name
   * @param {string} options.processingType - Processing type
   * @param {string} options.displayRegionName - Display region name
   * @returns {Promise<Object>} Aspect analysis result
   */
  async generateAspect(options = {}) {
    const formData = new FormData();
    
    // Support both camelCase and snake_case parameter names for flexibility
    if (options.inputFile || options.input_file) formData.append('input_file', options.inputFile || options.input_file);
    if (options.regionName || options.region_name) formData.append('region_name', options.regionName || options.region_name);
    if (options.processingType || options.processing_type) formData.append('processing_type', options.processingType || options.processing_type);
    if (options.displayRegionName || options.display_region_name) formData.append('display_region_name', options.displayRegionName || options.display_region_name);
    
    return this.postForm('aspect', formData);
  }

  /**
   * Generate color relief visualization
   * @param {Object} options - Processing options
   * @param {string} options.inputFile - Input LAZ file path
   * @param {string} options.regionName - Region name
   * @param {string} options.processingType - Processing type
   * @param {string} options.displayRegionName - Display region name
   * @returns {Promise<Object>} Color relief generation result
   */
  async generateColorRelief(options = {}) {
    const formData = new FormData();
    
    // Support both camelCase and snake_case parameter names for flexibility
    if (options.inputFile || options.input_file) formData.append('input_file', options.inputFile || options.input_file);
    if (options.regionName || options.region_name) formData.append('region_name', options.regionName || options.region_name);
    if (options.processingType || options.processing_type) formData.append('processing_type', options.processingType || options.processing_type);
    if (options.displayRegionName || options.display_region_name) formData.append('display_region_name', options.displayRegionName || options.display_region_name);
    
    return this.postForm('color_relief', formData);
  }

  /**
   * Generate Topographic Position Index (TPI)
   * @param {Object} options - Processing options
   * @param {string} options.inputFile - Input LAZ file path
   * @param {string} options.regionName - Region name
   * @param {string} options.processingType - Processing type
   * @param {string} options.displayRegionName - Display region name
   * @returns {Promise<Object>} TPI generation result
   */
  async generateTPI(options = {}) {
    const formData = new FormData();
    
    // Support both camelCase and snake_case parameter names for flexibility
    if (options.inputFile || options.input_file) formData.append('input_file', options.inputFile || options.input_file);
    if (options.regionName || options.region_name) formData.append('region_name', options.regionName || options.region_name);
    if (options.processingType || options.processing_type) formData.append('processing_type', options.processingType || options.processing_type);
    if (options.displayRegionName || options.display_region_name) formData.append('display_region_name', options.displayRegionName || options.display_region_name);
    
    return this.postForm('tpi', formData);
  }

  /**
   * Generate terrain roughness analysis
   * @param {Object} options - Processing options
   * @param {string} options.inputFile - Input LAZ file path
   * @param {string} options.regionName - Region name
   * @param {string} options.processingType - Processing type
   * @param {string} options.displayRegionName - Display region name
   * @returns {Promise<Object>} Roughness analysis result
   */
  async generateRoughness(options = {}) {
    const formData = new FormData();
    
    // Support both camelCase and snake_case parameter names for flexibility
    if (options.inputFile || options.input_file) formData.append('input_file', options.inputFile || options.input_file);
    if (options.regionName || options.region_name) formData.append('region_name', options.regionName || options.region_name);
    if (options.processingType || options.processing_type) formData.append('processing_type', options.processingType || options.processing_type);
    if (options.displayRegionName || options.display_region_name) formData.append('display_region_name', options.displayRegionName || options.display_region_name);
    
    return this.postForm('roughness', formData);
  }

  /**
   * Generate Sky View Factor raster
   * @param {Object} options - Processing options
   * @param {string} options.inputFile - Input LAZ file path
   * @param {string} options.regionName - Region name
   * @param {string} options.processingType - Processing type
   * @param {string} options.displayRegionName - Display region name
   * @returns {Promise<Object>} Sky View Factor result
   */
  async generateSkyViewFactor(options = {}) {
    const formData = new FormData();

    if (options.inputFile || options.input_file) formData.append('input_file', options.inputFile || options.input_file);
    if (options.regionName || options.region_name) formData.append('region_name', options.regionName || options.region_name);
    if (options.processingType || options.processing_type) formData.append('processing_type', options.processingType || options.processing_type);
    if (options.displayRegionName || options.display_region_name) formData.append('display_region_name', options.displayRegionName || options.display_region_name);

    return this.postForm('sky_view_factor', formData);
  }

  // Unified Raster Generation
  
  /**
   * Generate all raster products for a region
   * @param {string} regionName - Region name
   * @param {number} batchSize - Batch size for processing (default: 4)
   * @returns {Promise<Object>} Batch generation result
   */
  async generateAllRasters(regionName, batchSize = 4) {
    return this.post('generate-rasters', {
      region_name: regionName,
      batch_size: batchSize
    });
  }

  // Processing Status and Monitoring
  
  /**
   * Get processing status for a region
   * @param {string} regionName - Region name
   * @returns {Promise<Object>} Processing status
   */
  async getProcessingStatus(regionName) {
    return this.get(`processing/status/${encodeURIComponent(regionName)}`);
  }

  /**
   * Cancel ongoing processing for a region
   * @param {string} regionName - Region name
   * @returns {Promise<Object>} Cancellation result
   */
  async cancelProcessing(regionName) {
    return this.post(`processing/cancel/${encodeURIComponent(regionName)}`);
  }

  /**
   * Get processing history
   * @returns {Promise<Object>} Processing history
   */
  async getProcessingHistory() {
    return this.get('processing/history');
  }

  // File Management
  
  /**
   * Delete processed files for a region
   * @param {string} regionName - Region name
   * @param {string[]} fileTypes - Optional array of file types to delete
   * @returns {Promise<Object>} Deletion result
   */
  async deleteProcessedFiles(regionName, fileTypes = null) {
    const data = { region_name: regionName };
    if (fileTypes) {
      data.file_types = fileTypes;
    }
    return this.delete('processing/files', data);
  }

  // Legacy Support
  
  /**
   * Get processing result overlay
   * @param {string} regionName - Region name
   * @param {string} processingType - Processing type
   * @returns {Promise<Object>} Overlay data
   */
  async getProcessingOverlay(regionName, processingType) {
    return this.get(`overlay/raster/${encodeURIComponent(regionName)}/${processingType}`);
  }

  /**
   * Process a region with specified processing type (legacy method)
   * @param {string} processingType - Type of processing (dtm, hillshade, etc.)
   * @param {Object} options - Processing options
   * @returns {Promise<Object>} Processing result
   * @deprecated Use specific service methods instead
   */
  async processRegion(processingType, options = {}) {
    // Map to service methods for backward compatibility
    const methodMap = {
      'dtm': this.generateDTM,
      'dsm': this.generateDSM,
      'chm': this.generateCHM,
      'hillshade': this.generateHillshade,
      'slope': this.generateSlope,
      'aspect': this.generateAspect,
      'color-relief': this.generateColorRelief,
      'tpi': this.generateTPI,
      'roughness': this.generateRoughness,
      'sky_view_factor': this.generateSkyViewFactor
    };

    const method = methodMap[processingType];
    if (method) {
      return method.call(this, options);
    } else {
      // Fallback to direct endpoint for unknown types
      const formData = new FormData();
      Object.keys(options).forEach(key => {
        if (options[key] !== undefined && options[key] !== null) {
          formData.append(key, options[key]);
        }
      });
      return this.postForm(processingType, formData);
    }
  }
}

/**
 * Region Analysis Service
 */
class RegionAnalysisAPIClient extends BaseAPIClient {
  /**
   * Perform comprehensive terrain analysis for a region
   * @param {string} regionName - Name of the region to analyze
   * @returns {Promise<Object>} Terrain analysis result
   */
  async analyzeRegionTerrain(regionName) {
    return this.get(`analysis/terrain/${encodeURIComponent(regionName)}`);
  }

  /**
   * Compare two regions using specified metrics
   * @param {string} region1 - First region name
   * @param {string} region2 - Second region name
   * @param {Array<string>} metrics - Optional list of metrics to compare
   * @returns {Promise<Object>} Region comparison result
   */
  async compareRegions(region1, region2, metrics = null) {
    const data = { region1, region2 };
    if (metrics) data.metrics = metrics;
    
    return this.post('analysis/compare-regions', data);
  }

  /**
   * Calculate comprehensive statistics for a region
   * @param {string} regionName - Name of the region
   * @param {Array<string>} analysisTypes - Optional list of analysis types
   * @returns {Promise<Object>} Region statistics
   */
  async calculateRegionStatistics(regionName, analysisTypes = null) {
    const params = {};
    if (analysisTypes) params.analysis_types = analysisTypes.join(',');
    
    return this.get(`analysis/statistics/${encodeURIComponent(regionName)}`, params);
  }

  /**
   * Detect land cover changes in a region over time
   * @param {string} regionName - Name of the region
   * @param {string} startDate - Start date for analysis
   * @param {string} endDate - End date for analysis
   * @returns {Promise<Object>} Land cover change analysis
   */
  async detectLandCoverChange(regionName, startDate, endDate) {
    return this.post('analysis/land-cover-change', {
      region_name: regionName,
      start_date: startDate,
      end_date: endDate
    });
  }

  /**
   * Calculate vegetation indices for a region
   * @param {string} regionName - Name of the region
   * @param {Array<string>} indices - Optional list of vegetation indices to calculate
   * @returns {Promise<Object>} Vegetation indices result
   */
  async calculateVegetationIndices(regionName, indices = null) {
    const data = { region_name: regionName };
    if (indices) data.indices = indices;
    
    return this.post('analysis/vegetation-indices', data);
  }

  /**
   * Perform hydrological analysis including flow direction and accumulation
   * @param {string} regionName - Name of the region
   * @returns {Promise<Object>} Hydrological analysis result
   */
  async performHydrologicalAnalysis(regionName) {
    return this.get(`analysis/hydrology/${encodeURIComponent(regionName)}`);
  }

  /**
   * Calculate slope stability analysis
   * @param {string} regionName - Name of the region
   * @param {number} safetyFactorThreshold - Safety factor threshold (default: 1.5)
   * @returns {Promise<Object>} Slope stability analysis
   */
  async calculateSlopeStability(regionName, safetyFactorThreshold = 1.5) {
    return this.post('analysis/slope-stability', {
      region_name: regionName,
      safety_factor_threshold: safetyFactorThreshold
    });
  }

  /**
   * Detect forest canopy gaps using CHM data
   * @param {string} regionName - Name of the region
   * @param {number} gapThreshold - Gap threshold in meters (default: 5.0)
   * @returns {Promise<Object>} Canopy gaps analysis
   */
  async detectForestCanopyGaps(regionName, gapThreshold = 5.0) {
    return this.post('analysis/canopy-gaps', {
      region_name: regionName,
      gap_threshold: gapThreshold
    });
  }

  /**
   * Calculate biodiversity and habitat metrics
   * @param {string} regionName - Name of the region
   * @returns {Promise<Object>} Biodiversity metrics
   */
  async calculateBiodiversityMetrics(regionName) {
    return this.get(`analysis/biodiversity/${encodeURIComponent(regionName)}`);
  }

  /**
   * Perform soil erosion risk assessment
   * @param {string} regionName - Name of the region
   * @param {Object} rainfallData - Optional rainfall data
   * @returns {Promise<Object>} Erosion assessment result
   */
  async performErosionAssessment(regionName, rainfallData = null) {
    const data = { region_name: regionName };
    if (rainfallData) data.rainfall_data = rainfallData;
    
    return this.post('analysis/erosion-assessment', data);
  }

  /**
   * Calculate solar energy potential
   * @param {string} regionName - Name of the region
   * @param {number} panelEfficiency - Solar panel efficiency (default: 0.2)
   * @returns {Promise<Object>} Solar potential analysis
   */
  async calculateSolarPotential(regionName, panelEfficiency = 0.2) {
    return this.post('analysis/solar-potential', {
      region_name: regionName,
      panel_efficiency: panelEfficiency
    });
  }

  /**
   * Analyze terrain accessibility from specified access points
   * @param {string} regionName - Name of the region
   * @param {Array<Object>} accessPoints - List of access point coordinates
   * @returns {Promise<Object>} Accessibility analysis
   */
  async analyzeAccessibility(regionName, accessPoints) {
    return this.post('analysis/accessibility', {
      region_name: regionName,
      access_points: accessPoints
    });
  }

  /**
   * Detect geological features in terrain data
   * @param {string} regionName - Name of the region
   * @param {Array<string>} featureTypes - Optional list of feature types to detect
   * @returns {Promise<Object>} Geological features analysis
   */
  async detectGeologicalFeatures(regionName, featureTypes = null) {
    const data = { region_name: regionName };
    if (featureTypes) data.feature_types = featureTypes;
    
    return this.post('analysis/geological-features', data);
  }

  /**
   * Calculate forest carbon storage estimates
   * @param {string} regionName - Name of the region
   * @param {string} biomassModel - Biomass model to use (default: 'default')
   * @returns {Promise<Object>} Carbon storage analysis
   */
  async calculateCarbonStorage(regionName, biomassModel = 'default') {
    return this.post('analysis/carbon-storage', {
      region_name: regionName,
      biomass_model: biomassModel
    });
  }

  /**
   * Perform flood risk analysis
   * @param {string} regionName - Name of the region
   * @param {Array<number>} returnPeriods - Optional list of return periods
   * @returns {Promise<Object>} Flood risk analysis
   */
  async performFloodRiskAnalysis(regionName, returnPeriods = null) {
    const data = { region_name: regionName };
    if (returnPeriods) data.return_periods = returnPeriods;
    
    return this.post('analysis/flood-risk', data);
  }

  /**
   * Calculate landscape ecology metrics
   * @param {string} regionName - Name of the region
   * @param {number} patchThreshold - Patch threshold (default: 0.1)
   * @returns {Promise<Object>} Landscape metrics
   */
  async calculateLandscapeMetrics(regionName, patchThreshold = 0.1) {
    return this.post('analysis/landscape-metrics', {
      region_name: regionName,
      patch_threshold: patchThreshold
    });
  }

  /**
   * Analyze microclimate variations based on terrain
   * @param {string} regionName - Name of the region
   * @param {Object} weatherData - Optional weather data
   * @returns {Promise<Object>} Microclimate analysis
   */
  async analyzeMicroclimate(regionName, weatherData = null) {
    const data = { region_name: regionName };
    if (weatherData) data.weather_data = weatherData;
    
    return this.post('analysis/microclimate', data);
  }

  /**
   * Generate comprehensive analysis report
   * @param {string} regionName - Name of the region
   * @param {Array<string>} analysisTypes - List of analysis types to include
   * @param {string} format - Report format (default: 'pdf')
   * @returns {Promise<Object>} Report generation result
   */
  async generateAnalysisReport(regionName, analysisTypes, format = 'pdf') {
    return this.post('analysis/generate-report', {
      region_name: regionName,
      analysis_types: analysisTypes,
      format: format
    });
  }

  /**
   * Export analysis results in specified format
   * @param {string} regionName - Name of the region
   * @param {string} analysisId - Analysis ID
   * @param {string} format - Export format (default: 'geojson')
   * @returns {Promise<Object>} Export result
   */
  async exportAnalysisResults(regionName, analysisId, format = 'geojson') {
    return this.get(`analysis/export/${encodeURIComponent(regionName)}/${encodeURIComponent(analysisId)}`, 
                    { format: format });
  }

  /**
   * Get history of analysis operations
   * @param {string} regionName - Optional region name to filter by
   * @returns {Promise<Object>} Analysis history
   */
  async getAnalysisHistory(regionName = null) {
    const params = {};
    if (regionName) params.region_name = regionName;
    
    return this.get('analysis/history', params);
  }

  /**
   * Schedule periodic analysis for a region
   * @param {string} regionName - Name of the region
   * @param {Array<string>} analysisTypes - List of analysis types to schedule
   * @param {string} schedule - Schedule expression (cron format)
   * @param {string} notificationEmail - Optional notification email
   * @returns {Promise<Object>} Scheduling result
   */
  async schedulePeriodicAnalysis(regionName, analysisTypes, schedule, notificationEmail = null) {
    const data = {
      region_name: regionName,
      analysis_types: analysisTypes,
      schedule: schedule
    };
    if (notificationEmail) data.notification_email = notificationEmail;
    
    return this.post('analysis/schedule', data);
  }
}

/**
 * Elevation Data Service
 */
class ElevationAPIClient extends BaseAPIClient {
  /**
   * Download elevation data for coordinates
   * @param {Object} request - Elevation request parameters
   * @returns {Promise<Object>} Download result
   */
  async downloadElevationData(request) {
    return this.post('elevation/download-coordinates', request);
  }

  /**
   * Get elevation system status
   * @returns {Promise<Object>} System status
   */
  async getElevationStatus() {
    return this.get('elevation/status');
  }

  /**
   * Get optimal elevation data for Brazilian coordinates
   * @param {number} latitude - Latitude
   * @param {number} longitude - Longitude
   * @param {number} areaKm - Area in kilometers
   * @param {string} regionName - Optional region name
   * @returns {Promise<Object>} Elevation data
   */
  async getBrazilianElevationData(latitude, longitude, areaKm, regionName = null) {
    const request = {
      lat: latitude,
      lng: longitude,
      buffer_km: areaKm / 2, // Convert area to radius
    };

    if (regionName) {
      request.region_name = regionName;
    }

    return this.downloadElevationData(request);
  }

  /**
   * Check elevation data availability
   * @param {number} latitude - Latitude
   * @param {number} longitude - Longitude
   * @returns {Promise<Object>} Availability status
   */
  async checkElevationAvailability(latitude, longitude) {
    return this.post('check-data-availability', {
      lat: latitude,
      lng: longitude
    });
  }
}

/**
 * Satellite Data Service
 */
class SatelliteAPIClient extends BaseAPIClient {
  /**
   * Download Sentinel-2 data
   * @param {Object} request - Satellite request parameters
   * @returns {Promise<Object>} Download result
   */
  async downloadSentinel2Data(request) {
    return this.post('download-sentinel2', request);
  }

  /**
   * Convert Sentinel-2 TIF files to PNG
   * @param {string} regionName - Region name
   * @returns {Promise<Object>} Conversion result
   */
  async convertSentinel2ToPNG(regionName) {
    const formData = new FormData();
    formData.append('region_name', regionName);
    return this.postForm('convert-sentinel2', formData);
  }

  /**
   * Get Sentinel-2 overlay data
   * @param {string} regionBand - Region and band identifier
   * @returns {Promise<Object>} Overlay data
   */
  async getSentinel2Overlay(regionBand) {
    return this.get(`overlay/sentinel2/${encodeURIComponent(regionBand)}`);
  }

  /**
   * Search for Sentinel-2 scenes
   * @param {number} latitude - Latitude
   * @param {number} longitude - Longitude
   * @param {string} startDate - Start date (YYYY-MM-DD)
   * @param {string} endDate - End date (YYYY-MM-DD)
   * @param {number} cloudCoverMax - Maximum cloud cover percentage
   * @param {Array} bands - Array of band identifiers
   * @param {string} regionName - Optional region name
   * @returns {Promise<Object>} Search results
   */
  async searchSentinel2Scenes(latitude, longitude, startDate, endDate, cloudCoverMax = 30, bands = ['B04', 'B08'], regionName = null) {
    const request = {
      lat: latitude,
      lng: longitude,
      start_date: startDate,
      end_date: endDate,
      cloud_cover_max: cloudCoverMax,
      bands: bands,
      buffer_km: 5.0
    };

    if (regionName) {
      request.region_name = regionName;
    }

    return this.downloadSentinel2Data(request);
  }

  /**
   * Get satellite coverage information
   * @param {number} latitude - Latitude
   * @param {number} longitude - Longitude
   * @returns {Promise<Object>} Coverage information
   */
  async getSatelliteCoverage(latitude, longitude) {
    return this.post('check-data-availability', {
      lat: latitude,
      lng: longitude
    });
  }
}

/**
 * Overlay Management Service
 * Matches the backend OverlayService methods exactly
 */
class OverlayAPIClient extends BaseAPIClient {
  /**
   * Get overlay data for a processed image including bounds and base64 encoded image
   * @param {string} processingType - Processing type
   * @param {string} filename - Filename
   * @returns {Promise<Object>} Overlay data
   */
  async getOverlayData(processingType, filename) {
    return this.get(`overlay/${processingType}/${encodeURIComponent(filename)}`);
  }

  /**
   * Get overlay data for raster-processed images from regions
   * @param {string} regionName - Region name
   * @param {string} processingType - Processing type
   * @returns {Promise<Object>} Raster overlay data
   */
  async getRasterOverlayData(regionName, processingType) {
    return this.get(`overlay/raster/${encodeURIComponent(regionName)}/${processingType}`);
  }

  /**
   * Get overlay data for a Sentinel-2 image including bounds and base64 encoded image
   * @param {string} regionBand - Region and band identifier
   * @returns {Promise<Object>} Sentinel-2 overlay data
   */
  async getSentinel2OverlayData(regionBand) {
    return this.get(`overlay/sentinel2/${encodeURIComponent(regionBand)}`);
  }

  /**
   * Get test overlay data
   * @param {string} filename - Filename
   * @returns {Promise<Object>} Test overlay data
   */
  async getTestOverlay(filename) {
    return this.get(`test-overlay/${encodeURIComponent(filename)}`);
  }

  /**
   * Create overlay from GeoTIFF file
   * @param {string} filePath - Path to GeoTIFF file
   * @param {Object} bounds - Bounding box coordinates
   * @returns {Promise<Object>} Created overlay data
   */
  async createOverlayFromGeotiff(filePath, bounds) {
    const data = {
      file_path: filePath,
      bounds: bounds
    };
    return this.post('overlay/create-from-geotiff', data);
  }

  /**
   * Get overlay bounds for a specific region and processing type
   * @param {string} regionName - Region name
   * @param {string} processingType - Processing type
   * @returns {Promise<Object>} Overlay bounds
   */
  async getOverlayBounds(regionName, processingType) {
    return this.get(`overlay/bounds/${encodeURIComponent(regionName)}/${processingType}`);
  }

  /**
   * List all available overlays, optionally filtered by region
   * @param {string} regionName - Optional region name filter
   * @returns {Promise<Object>} Available overlays
   */
  async listAvailableOverlays(regionName = null) {
    const params = regionName ? { region_name: regionName } : {};
    return this.get('overlay/list', params);
  }

  /**
   * Get metadata for a specific overlay
   * @param {string} overlayId - Overlay ID
   * @returns {Promise<Object>} Overlay metadata
   */
  async getOverlayMetadata(overlayId) {
    return this.get(`overlay/metadata/${encodeURIComponent(overlayId)}`);
  }

  /**
   * Update overlay opacity
   * @param {string} overlayId - Overlay ID
   * @param {number} opacity - Opacity value (0.0 to 1.0)
   * @returns {Promise<Object>} Update result
   */
  async updateOverlayOpacity(overlayId, opacity) {
    const data = { opacity: opacity };
    return this.request('PUT', `overlay/${encodeURIComponent(overlayId)}/opacity`, {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  /**
   * Toggle overlay visibility
   * @param {string} overlayId - Overlay ID
   * @param {boolean} visible - Visibility state
   * @returns {Promise<Object>} Update result
   */
  async toggleOverlayVisibility(overlayId, visible) {
    const data = { visible: visible };
    return this.request('PUT', `overlay/${encodeURIComponent(overlayId)}/visibility`, {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  /**
   * Delete an overlay
   * @param {string} overlayId - Overlay ID
   * @returns {Promise<Object>} Deletion result
   */
  async deleteOverlay(overlayId) {
    return this.delete(`overlay/${encodeURIComponent(overlayId)}`);
  }

  /**
   * Create a composite overlay from multiple overlays
   * @param {string[]} overlayIds - Array of overlay IDs
   * @param {string} outputName - Name for the composite overlay
   * @returns {Promise<Object>} Composite overlay data
   */
  async createCompositeOverlay(overlayIds, outputName) {
    const data = {
      overlay_ids: overlayIds,
      output_name: outputName
    };
    return this.post('overlay/composite', data);
  }

  /**
   * Export overlay to specified format
   * @param {string} overlayId - Overlay ID
   * @param {string} format - Export format (default: 'png')
   * @returns {Promise<Object>} Export result
   */
  async exportOverlay(overlayId, format = 'png') {
    const params = { format: format };
    return this.get(`overlay/${encodeURIComponent(overlayId)}/export`, params);
  }

  /**
   * Get statistical information about an overlay
   * @param {string} overlayId - Overlay ID
   * @returns {Promise<Object>} Overlay statistics
   */
  async getOverlayStatistics(overlayId) {
    return this.get(`overlay/${encodeURIComponent(overlayId)}/statistics`);
  }

  /**
   * Apply color ramp to an overlay
   * @param {string} overlayId - Overlay ID
   * @param {string} colorRamp - Color ramp name
   * @returns {Promise<Object>} Update result
   */
  async applyColorRamp(overlayId, colorRamp) {
    const data = { color_ramp: colorRamp };
    return this.request('PUT', `overlay/${encodeURIComponent(overlayId)}/color-ramp`, {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  /**
   * Crop an overlay to specified bounds
   * @param {string} overlayId - Overlay ID
   * @param {Object} bounds - Bounding box coordinates
   * @returns {Promise<Object>} Crop result
   */
  async cropOverlay(overlayId, bounds) {
    const data = { bounds: bounds };
    return this.post(`overlay/${encodeURIComponent(overlayId)}/crop`, data);
  }
}

/**
 * Saved Places Service
 */
class SavedPlacesAPIClient extends BaseAPIClient {
  /**
   * Get all saved places
   * @returns {Promise<Object>} Saved places
   */
  async getSavedPlaces() {
    return this.get('saved-places');
  }

  /**
   * Save places data
   * @param {Array} places - Array of place objects
   * @returns {Promise<Object>} Save result
   */
  async savePlaces(places) {
    return this.post('saved-places', { places });
  }

  /**
   * Delete a specific saved place
   * @param {string} placeId - Place ID
   * @returns {Promise<Object>} Delete result
   */
  async deleteSavedPlace(placeId) {
    return this.delete(`saved-places/${encodeURIComponent(placeId)}`);
  }

  /**
   * Export saved places
   * @returns {Promise<Object>} Export data
   */
  async exportSavedPlaces() {
    return this.get('saved-places/export');
  }

  /**
   * Get places near coordinates (mock implementation)
   * @param {number} latitude - Latitude
   * @param {number} longitude - Longitude
   * @param {number} radiusKm - Radius in kilometers
   * @returns {Promise<Object>} Nearby places
   */
  async getPlacesNearCoordinates(latitude, longitude, radiusKm) {
    // This would need to be implemented on the backend
    const allPlaces = await this.getSavedPlaces();
    
    // Simple distance calculation (not precise for large distances)
    const nearby = allPlaces.places?.filter(place => {
      const latDiff = Math.abs(place.lat - latitude);
      const lngDiff = Math.abs(place.lng - longitude);
      const approxDistance = Math.sqrt(latDiff * latDiff + lngDiff * lngDiff) * 111; // Rough km conversion
      return approxDistance <= radiusKm;
    }) || [];

    return { places: nearby };
  }
}

/**
 * GeoTIFF Service
 * Matches the backend GeotiffService methods exactly
 */
class GeotiffAPIClient extends BaseAPIClient {
  /**
   * List available GeoTIFF files
   * @param {string} regionName - Optional region name filter
   * @returns {Promise<Object>} List of GeoTIFF files
   */
  async listGeotiffFiles(regionName = null) {
    const params = regionName ? { region_name: regionName } : {};
    return this.get('geotiff/files', params);
  }

  /**
   * Get information about a specific GeoTIFF file
   * @param {string} filePath - Path to the GeoTIFF file
   * @returns {Promise<Object>} GeoTIFF file information
   */
  async getGeotiffInfo(filePath) {
    return this.get(`geotiff/metadata/${encodeURIComponent(filePath)}`);
  }

  /**
   * Convert GeoTIFF to PNG format
   * @param {string} filePath - Path to the GeoTIFF file
   * @param {string} outputPath - Optional output path for the PNG
   * @returns {Promise<Object>} Conversion result
   */
  async convertGeotiffToPng(filePath, outputPath = null) {
    const data = { file_path: filePath };
    if (outputPath) {
      data.output_path = outputPath;
    }
    return this.post('geotiff/convert-to-png', data);
  }

  /**
   * Get metadata for a GeoTIFF file
   * @param {string} filePath - Path to the GeoTIFF file
   * @returns {Promise<Object>} GeoTIFF metadata
   */
  async getGeotiffMetadata(filePath) {
    return this.get(`geotiff/metadata/${encodeURIComponent(filePath)}`);
  }

  /**
   * Crop a GeoTIFF file to specified bounds
   * @param {string} filePath - Path to the GeoTIFF file
   * @param {Object} bounds - Bounding box coordinates
   * @param {string} outputPath - Optional output path for cropped file
   * @returns {Promise<Object>} Crop result
   */
  async cropGeotiff(filePath, bounds, outputPath = null) {
    const data = {
      file_path: filePath,
      bounds: bounds
    };
    if (outputPath) {
      data.output_path = outputPath;
    }
    return this.post('geotiff/crop', data);
  }

  /**
   * Resample a GeoTIFF file to a different resolution
   * @param {string} filePath - Path to the GeoTIFF file
   * @param {number} resolution - Target resolution
   * @param {string} outputPath - Optional output path for resampled file
   * @returns {Promise<Object>} Resample result
   */
  async resampleGeotiff(filePath, resolution, outputPath = null) {
    const data = {
      file_path: filePath,
      resolution: resolution
    };
    if (outputPath) {
      data.output_path = outputPath;
    }
    return this.post('geotiff/resample', data);
  }

  /**
   * Get statistical information about a GeoTIFF file
   * @param {string} filePath - Path to the GeoTIFF file
   * @returns {Promise<Object>} Statistical information
   */
  async getGeotiffStatistics(filePath) {
    return this.get('geotiff/statistics', { file_path: filePath });
  }

  /**
   * Convert GeoTIFF to base64 encoded PNG
   * @param {string} filePath - Path to the GeoTIFF file
   * @returns {Promise<Object>} Base64 encoded PNG data
   */
  async convertToBase64(filePath) {
    return this.post('geotiff/to-base64', { file_path: filePath });
  }
}

/**
 * LAZ/LAS Processing Service
 */
class LAZAPIClient extends BaseAPIClient {
  /**
   * Load LAZ file
   * @param {File} file - LAZ file to load
   * @returns {Promise<Object>} Load result
   */
  async loadLAZFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.postForm('laz/load', formData);
  }

  /**
   * List available LAZ files
   * @returns {Promise<Object>} Files list
   */
  async listLAZFiles() {
    return this.get('laz/files');
  }

  /**
   * Get comprehensive LAZ file information
   * @param {string} filePath - File path
   * @returns {Promise<Object>} Comprehensive file information
   */
  async getLAZFileInfo(filePath) {
    return this.get('laz/info', { file_path: filePath });
  }

  /**
   * Get LAZ file spatial bounds in WGS84 coordinates
   * @param {string} filePath - File path
   * @returns {Promise<Object>} Spatial bounds information with WGS84 coordinates and center point
   */
  async getLAZFileBounds(filePath) {
    if (!filePath) {
      throw new Error('File path is required for getLAZFileBounds');
    }
    // The endpoint expects the file path to be part of the URL path.
    // Ensure the filePath is properly encoded if it might contain special characters.
    return this.get(`laz/bounds-wgs84/${encodeURIComponent(filePath)}`);
  }

  /**
   * Get LAZ file point count and density
   * @param {string} filePath - File path
   * @returns {Promise<Object>} Point count and density information
   */
  async getLAZPointCount(filePath) {
    return this.get('laz/point-count', { file_path: filePath });
  }

  /**
   * Get LAZ file classification statistics
   * @param {string} filePath - File path
   * @returns {Promise<Object>} Classification statistics
   */
  async getLAZClassificationStats(filePath) {
    return this.get('laz/classification-stats', { file_path: filePath });
  }

  /**
   * Get LAZ file coordinate system information
   * @param {string} filePath - File path
   * @returns {Promise<Object>} Coordinate reference system information
   */
  async getLAZCoordinateSystem(filePath) {
    return this.get('laz/coordinate-system', { file_path: filePath });
  }

  /**
   * Get LAZ file elevation statistics
   * @param {string} filePath - File path
   * @returns {Promise<Object>} Elevation statistics (min, max, mean, std)
   */
  async getLAZElevationStats(filePath) {
    return this.get('laz/elevation-stats', { file_path: filePath });
  }

  /**
   * Get LAZ file metadata
   * @param {string} filePath - File path
   * @returns {Promise<Object>} General file metadata
   */
  async getLAZMetadata(filePath) {
    return this.get('laz/metadata', { file_path: filePath });
  }

  /**
   * Validate LAZ file integrity
   * @param {string} filePath - File path
   * @returns {Promise<Object>} Validation results
   */
  async validateLAZFile(filePath) {
    return this.get('laz/validate', { file_path: filePath });
  }

  /**
   * Get LAZ file intensity statistics
   * @param {string} filePath - File path
   * @returns {Promise<Object>} Intensity value statistics
   */
  async getLAZIntensityStats(filePath) {
    return this.get('laz/intensity-stats', { file_path: filePath });
  }

  /**
   * Get LAZ file return statistics
   * @param {string} filePath - File path
   * @returns {Promise<Object>} Return number statistics
   */
  async getLAZReturnStats(filePath) {
    return this.get('laz/return-stats', { file_path: filePath });
  }

  /**
   * List all LAZ files with basic information
   * @returns {Promise<Object>} Files list with info
   */
  async listLAZFilesWithInfo() {
    return this.get('laz/files-with-info');
  }

  /**
   * Compare two LAZ files
   * @param {string} file1Path - First file path
   * @param {string} file2Path - Second file path
   * @returns {Promise<Object>} Comparison results
   */
  async compareLAZFiles(file1Path, file2Path) {
    return this.get('laz/compare', { 
      file1_path: file1Path, 
      file2_path: file2Path 
    });
  }

  /**
   * Get LAZ file quality metrics
   * @param {string} filePath - File path
   * @returns {Promise<Object>} Data quality metrics
   */
  async getLAZQualityMetrics(filePath) {
    return this.get('laz/quality-metrics', { file_path: filePath });
  }

  /**
   * Download LAZ file
   * @param {string} filePath - File path
   * @returns {Promise<Blob>} File blob
   */
  async downloadLAZFile(filePath) {
    return this.downloadFile(`laz/download/${encodeURIComponent(filePath)}`);
  }

  /**
   * Delete LAZ file
   * @param {string} filePath - File path
   * @returns {Promise<Object>} Deletion result
   */
  async deleteLAZFile(filePath) {
    return this.delete(`laz/files/${encodeURIComponent(filePath)}`);
  }

  /**
   * Get processing status for LAZ file
   * @param {string} fileName - File name
   * @returns {Promise<Object>} Processing status
   */
  async getLAZProcessingStatus(fileName) {
    return this.get(`laz/processing-status/${encodeURIComponent(fileName)}`);
  }
}

/**
 * Data Acquisition Service
 */
class DataAcquisitionAPIClient extends BaseAPIClient {
  /**
   * Acquire combined data (elevation + satellite)
   * @param {Object} request - Acquisition request
   * @returns {Promise<Object>} Acquisition result
   */
  async acquireData(request) {
    return this.post('acquire-data', request);
  }

  /**
   * Check data availability
   * @param {Object} coordinates - Coordinate object
   * @returns {Promise<Object>} Availability status
   */
  async checkDataAvailability(coordinates) {
    return this.post('check-data-availability', coordinates);
  }

  /**
   * Estimate download size
   * @param {Object} coordinates - Coordinate object
   * @returns {Promise<Object>} Size estimate
   */
  async estimateDownloadSize(coordinates) {
    return this.post('estimate-download-size', coordinates);
  }

  /**
   * Get acquisition history
   * @returns {Promise<Object>} Acquisition history
   */
  async getAcquisitionHistory() {
    return this.get('acquisition-history');
  }

  /**
   * Get configuration
   * @returns {Promise<Object>} Configuration
   */
  async getConfiguration() {
    return this.get('config');
  }

  /**
   * Cleanup cache
   * @param {number} olderThanDays - Days threshold
   * @returns {Promise<Object>} Cleanup result
   */
  async cleanupCache(olderThanDays = 30) {
    return this.post('cleanup-cache', { older_than_days: olderThanDays });
  }

  /**
   * Get storage statistics
   * @returns {Promise<Object>} Storage stats
   */
  async getStorageStats() {
    return this.get('storage-stats');
  }
}

/**
 * Cache Management Service
 */
class CacheManagementAPIClient extends BaseAPIClient {
  /**
   * Get cache statistics
   * @returns {Promise<Object>} Cache statistics including entry counts and file sizes
   */
  async getCacheStats() {
    return this.get('cache/metadata/stats');
  }

  /**
   * List all cached files
   * @returns {Promise<Object>} List of all files in the cache with their metadata
   */
  async listCachedFiles() {
    return this.get('cache/metadata/list');
  }

  /**
   * Get cached metadata for a specific file
   * @param {string} filePath - Path to the LAZ file
   * @returns {Promise<Object>} Cached metadata if available
   */
  async getCachedMetadata(filePath) {
    if (!filePath) {
      throw new Error('File path is required for getCachedMetadata');
    }
    return this.get(`cache/metadata/${encodeURIComponent(filePath)}`);
  }

  /**
   * Refresh cache for a specific file
   * @param {string} filePath - Path to the LAZ file
   * @returns {Promise<Object>} Success status of cache refresh operation
   */
  async refreshFileCache(filePath) {
    if (!filePath) {
      throw new Error('File path is required for refreshFileCache');
    }
    return this.post(`cache/metadata/refresh/${encodeURIComponent(filePath)}`);
  }

  /**
   * Refresh cache for all files
   * @returns {Promise<Object>} Success status of global cache refresh operation
   */
  async refreshAllCache() {
    return this.post('cache/metadata/refresh-all');
  }

  /**
   * Clear all cache entries
   * @returns {Promise<Object>} Success status of cache clearing operation
   */
  async clearCache() {
    return this.delete('cache/metadata/clear');
  }

  /**
   * Validate cache integrity
   * @returns {Promise<Object>} Cache validation results
   */
  async validateCache() {
    return this.get('cache/metadata/validate');
  }

  /**
   * Get cache health status
   * @returns {Promise<Object>} Cache health information
   */
  async getCacheHealth() {
    const stats = await this.getCacheStats();
    const validation = await this.validateCache();
    
    return {
      success: true,
      health: {
        ...stats.stats,
        validation: validation
      }
    };
  }

  /**
   * Perform cache maintenance
   * @param {Object} options - Maintenance options
   * @param {boolean} options.validateIntegrity - Whether to validate cache integrity
   * @param {boolean} options.removeInvalid - Whether to remove invalid entries
   * @returns {Promise<Object>} Maintenance results
   */
  async performMaintenance(options = { validateIntegrity: true, removeInvalid: false }) {
    const results = {
      validation: null,
      cleanup: null,
      stats_before: null,
      stats_after: null
    };

    try {
      // Get stats before maintenance
      const statsBefore = await this.getCacheStats();
      results.stats_before = statsBefore.stats;

      // Validate cache if requested
      if (options.validateIntegrity) {
        results.validation = await this.validateCache();
      }

      // Remove invalid entries if requested
      if (options.removeInvalid && results.validation?.invalid_entries?.length > 0) {
        // For now, we'll clear the entire cache if there are invalid entries
        // A more sophisticated approach would selectively remove invalid entries
        results.cleanup = await this.clearCache();
      }

      // Get stats after maintenance
      const statsAfter = await this.getCacheStats();
      results.stats_after = statsAfter.stats;

      return {
        success: true,
        results: results
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        results: results
      };
    }
  }
}

/**
 * Prompt Service
 */
class PromptAPIClient extends BaseAPIClient {
  /**
   * Get concatenated prompts string
   * @returns {Promise<Object>} Prompt data
   */
  async getAllPrompts() {
    return this.get('prompts/all');
  }
}

/**
 * OpenAI interaction client
 */
class OpenAIAPIClient extends BaseAPIClient {
  /**
   * Send prompt and images to OpenAI
   * @param {Object} payload Request payload
   */
  async send(payload) {
    return this.post('openai/send', payload);
  }

  /**
   * Create log entry for OpenAI request
   * @param {Object} payload Log payload
   */
  async createLog(payload) {
    return this.post('openai/log', payload);
  }
}

/**
 * API Client Factory
 */
class APIClientFactory {
  constructor() {
    this._clients = {};
  }

  /**
   * Get or create a client instance
   * @param {string} clientType - Type of client to get
   * @returns {BaseAPIClient} Client instance
   */
  getClient(clientType) {
    if (!this._clients[clientType]) {
      switch (clientType) {
        case 'region':
          this._clients[clientType] = new RegionAPIClient();
          break;
        case 'processing':
          this._clients[clientType] = new ProcessingAPIClient();
          break;
        case 'regionAnalysis':
          this._clients[clientType] = new RegionAnalysisAPIClient();
          break;
        case 'elevation':
          this._clients[clientType] = new ElevationAPIClient();
          break;
        case 'satellite':
          this._clients[clientType] = new SatelliteAPIClient();
          break;
        case 'overlay':
          this._clients[clientType] = new OverlayAPIClient();
          break;
        case 'savedPlaces':
          this._clients[clientType] = new SavedPlacesAPIClient();
          break;
        case 'geotiff':
          this._clients[clientType] = new GeotiffAPIClient();
          break;
        case 'laz':
          this._clients[clientType] = new LAZAPIClient();
          break;
        case 'dataAcquisition':
          this._clients[clientType] = new DataAcquisitionAPIClient();
          break;
        case 'cacheManagement':
          this._clients[clientType] = new CacheManagementAPIClient();
          break;
        case 'prompts':
          this._clients[clientType] = new PromptAPIClient();
          break;
        case 'openai':
          this._clients[clientType] = new OpenAIAPIClient();
          break;
        default:
          throw new Error(`Unknown client type: ${clientType}`);
      }
    }
    return this._clients[clientType];
  }

  /**
   * Get region client
   */
  get region() {
    return this.getClient('region');
  }

  /**
   * Get processing client
   */
  get processing() {
    return this.getClient('processing');
  }

  /**
   * Get region analysis client
   */
  get regionAnalysis() {
    return this.getClient('regionAnalysis');
  }

  /**
   * Get elevation client
   */
  get elevation() {
    return this.getClient('elevation');
  }

  /**
   * Get satellite client
   */
  get satellite() {
    return this.getClient('satellite');
  }

  /**
   * Get overlay client
   */
  get overlay() {
    return this.getClient('overlay');
  }

  /**
   * Get saved places client
   */
  get savedPlaces() {
    return this.getClient('savedPlaces');
  }

  /**
   * Get geotiff client
   */
  get geotiff() {
    return this.getClient('geotiff');
  }

  /**
   * Get LAZ client
   */
  get laz() {
    return this.getClient('laz');
  }

  /**
   * Get data acquisition client
   */
  get dataAcquisition() {
    return this.getClient('dataAcquisition');
  }

  /**
   * Get cache management client
   */
  get cacheManagement() {
    return this.getClient('cacheManagement');
  }

  /**
   * Get prompts client
   */
  get prompts() {
    return this.getClient('prompts');
  }

  /**
   * Get OpenAI client
   */
  get openai() {
    return this.getClient('openai');
  }
}

// Global API client factory instance
window.APIClient = new APIClientFactory();

// Export classes for module usage
window.APIError = APIError;
window.BaseAPIClient = BaseAPIClient;
window.RegionAPIClient = RegionAPIClient;
window.ProcessingAPIClient = ProcessingAPIClient;
window.RegionAnalysisAPIClient = RegionAnalysisAPIClient;
window.ElevationAPIClient = ElevationAPIClient;
window.SatelliteAPIClient = SatelliteAPIClient;
window.OverlayAPIClient = OverlayAPIClient;
window.SavedPlacesAPIClient = SavedPlacesAPIClient;
window.GeotiffAPIClient = GeotiffAPIClient;
window.LAZAPIClient = LAZAPIClient;
window.DataAcquisitionAPIClient = DataAcquisitionAPIClient;
window.CacheManagementAPIClient = CacheManagementAPIClient;
window.PromptAPIClient = PromptAPIClient;
window.OpenAIAPIClient = OpenAIAPIClient;
window.APIClientFactory = APIClientFactory;

Utils.log('info', 'API Client system initialized successfully');
