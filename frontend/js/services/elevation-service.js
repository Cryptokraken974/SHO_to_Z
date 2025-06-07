/**
 * Elevation Service - Frontend Service Layer
 * 
 * This service abstracts elevation data operations and provides a clean interface
 * for elevation data acquisition, following the service layer pattern used in the backend.
 * 
 * Maps to backend ElevationService and handles:
 * - Elevation data download and acquisition
 * - Optimal elevation source selection
 * - Brazilian-specific elevation operations
 * - Error handling and response processing
 */

/**
 * Main Elevation Service class
 */
class ElevationService {
  constructor() {
    this.apiClient = new ElevationAPIClient();
    this.serviceName = 'ElevationService';
  }

  /**
   * Download elevation data for coordinates with optimal source selection
   * @param {Object} request - Elevation request parameters
   * @param {number} request.lat - Latitude 
   * @param {number} request.lng - Longitude
   * @param {number} request.buffer_km - Buffer in kilometers (default: 2.0)
   * @param {string} request.region_name - Optional region name
   * @returns {Promise<Object>} Elevation data result
   */
  async downloadElevationData(request) {
    try {
      Utils.log('info', `${this.serviceName}: Downloading elevation data for coordinates ${request.lat}, ${request.lng}`);
      
      // Validate input parameters
      this._validateCoordinates(request.lat, request.lng);
      
      // Set default buffer if not provided
      const enhancedRequest = {
        buffer_km: 2.0,
        ...request
      };

      // Call the API client
      const result = await this.apiClient.downloadElevationData(enhancedRequest);
      
      // Process and enhance the response
      return this._processElevationResponse(result, enhancedRequest);
      
    } catch (error) {
      Utils.log('error', `${this.serviceName}: Error downloading elevation data:`, error);
      return this._createErrorResponse(error);
    }
  }

  /**
   * Get Brazilian-specific elevation data with optimal dataset selection
   * @param {number} latitude - Latitude
   * @param {number} longitude - Longitude  
   * @param {number} areaKm - Area in kilometers (default: 25.0 for optimal quality)
   * @param {string} regionName - Optional region name
   * @returns {Promise<Object>} Brazilian elevation data result
   */
  async getBrazilianElevationData(latitude, longitude, areaKm = 25.0, regionName = null) {
    try {
      Utils.log('info', `${this.serviceName}: Getting Brazilian elevation data for ${latitude}, ${longitude}`);
      
      // Validate coordinates are within Brazil bounds (approximate)
      this._validateBrazilianCoordinates(latitude, longitude);
      
      const result = await this.apiClient.getBrazilianElevationData(latitude, longitude, areaKm, regionName);
      
      return this._processBrazilianElevationResponse(result, { latitude, longitude, areaKm, regionName });
      
    } catch (error) {
      Utils.log('error', `${this.serviceName}: Error getting Brazilian elevation data:`, error);
      return this._createErrorResponse(error);
    }
  }

  /**
   * Get elevation system status and configuration
   * @returns {Promise<Object>} System status
   */
  async getElevationStatus() {
    try {
      Utils.log('info', `${this.serviceName}: Getting elevation system status`);
      
      const result = await this.apiClient.getElevationStatus();
      
      return {
        success: true,
        status: result,
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      Utils.log('error', `${this.serviceName}: Error getting elevation status:`, error);
      return this._createErrorResponse(error);
    }
  }

  /**
   * Check elevation data availability for coordinates
   * @param {number} latitude - Latitude
   * @param {number} longitude - Longitude
   * @returns {Promise<Object>} Availability information
   */
  async checkElevationAvailability(latitude, longitude) {
    try {
      Utils.log('info', `${this.serviceName}: Checking elevation availability for ${latitude}, ${longitude}`);
      
      this._validateCoordinates(latitude, longitude);
      
      const result = await this.apiClient.checkElevationAvailability(latitude, longitude);
      
      return {
        success: true,
        availability: result,
        coordinates: { latitude, longitude },
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      Utils.log('error', `${this.serviceName}: Error checking elevation availability:`, error);
      return this._createErrorResponse(error);
    }
  }

  /**
   * Download elevation data with enhanced progress tracking
   * @param {Object} request - Elevation request 
   * @param {Function} progressCallback - Optional progress callback
   * @returns {Promise<Object>} Enhanced elevation result with progress tracking
   */
  async downloadWithProgress(request, progressCallback = null) {
    try {
      Utils.log('info', `${this.serviceName}: Starting elevation download with progress tracking`);
      
      // Setup progress monitoring if WebSocket is available
      if (progressCallback && window.WebSocketManager) {
        this._setupProgressMonitoring(progressCallback);
      }
      
      const result = await this.downloadElevationData(request);
      
      if (progressCallback && result.success) {
        progressCallback({
          type: 'elevation_complete',
          message: 'Elevation data download completed',
          progress: 100,
          data: result
        });
      }
      
      return result;
      
    } catch (error) {
      if (progressCallback) {
        progressCallback({
          type: 'elevation_error',
          message: `Elevation download failed: ${error.message}`,
          progress: 0,
          error: error.message
        });
      }
      throw error;
    }
  }

  /**
   * Get recommended elevation settings for a region
   * @param {number} latitude - Latitude
   * @param {number} longitude - Longitude
   * @returns {Promise<Object>} Recommended settings
   */
  async getRecommendedSettings(latitude, longitude) {
    try {
      // Determine region type for optimal settings
      const regionType = this._determineRegionType(latitude, longitude);
      
      return {
        success: true,
        recommendations: {
          buffer_km: this._getOptimalBufferSize(regionType),
          dataset: this._getOptimalDataset(regionType),
          resolution: this._getOptimalResolution(regionType),
          region_type: regionType
        }
      };
      
    } catch (error) {
      return this._createErrorResponse(error);
    }
  }

  // =================== PRIVATE HELPER METHODS ===================

  /**
   * Validate coordinate ranges
   * @private
   */
  _validateCoordinates(latitude, longitude) {
    if (typeof latitude !== 'number' || typeof longitude !== 'number') {
      throw new Error('Latitude and longitude must be numbers');
    }
    
    if (latitude < -90 || latitude > 90) {
      throw new Error(`Invalid latitude: ${latitude}. Must be between -90 and 90`);
    }
    
    if (longitude < -180 || longitude > 180) {
      throw new Error(`Invalid longitude: ${longitude}. Must be between -180 and 180`);
    }
  }

  /**
   * Validate coordinates are within Brazil bounds
   * @private
   */
  _validateBrazilianCoordinates(latitude, longitude) {
    this._validateCoordinates(latitude, longitude);
    
    // Approximate Brazil bounds
    const brazilBounds = {
      north: 5.3,
      south: -33.8,
      east: -28.6,
      west: -73.9
    };
    
    if (latitude < brazilBounds.south || latitude > brazilBounds.north ||
        longitude < brazilBounds.west || longitude > brazilBounds.east) {
      Utils.log('warn', `${this.serviceName}: Coordinates ${latitude}, ${longitude} may be outside Brazil bounds`);
    }
  }

  /**
   * Process elevation response and enhance with metadata
   * @private
   */
  _processElevationResponse(result, originalRequest) {
    if (!result.success) {
      return {
        success: false,
        error: result.error || 'Elevation download failed',
        request: originalRequest,
        timestamp: new Date().toISOString()
      };
    }

    return {
      success: true,
      data: {
        file_path: result.file_path,
        file_size_mb: result.file_size_mb,
        resolution_m: result.resolution_m,
        coordinates: result.coordinates,
        region_name: result.region_name,
        source_metadata: result.source_metadata
      },
      metadata: {
        data_type: 'elevation',
        format: 'GeoTIFF',
        download_id: result.download_id,
        routing_info: result.routing_info,
        processing_info: result.processing_info
      },
      request: originalRequest,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Process Brazilian elevation response
   * @private
   */
  _processBrazilianElevationResponse(result, originalRequest) {
    const processedResult = this._processElevationResponse(result, originalRequest);
    
    if (processedResult.success) {
      // Add Brazilian-specific metadata
      processedResult.metadata.region_optimization = 'brazilian_amazon';
      processedResult.metadata.optimal_for_terrain = ['forest', 'amazon', 'tropical'];
    }
    
    return processedResult;
  }

  /**
   * Create standardized error response
   * @private
   */
  _createErrorResponse(error) {
    return {
      success: false,
      error: error.message || 'Unknown error occurred',
      error_type: error.name || 'ElevationError',
      timestamp: new Date().toISOString(),
      service: this.serviceName
    };
  }

  /**
   * Setup progress monitoring via WebSocket
   * @private
   */
  _setupProgressMonitoring(progressCallback) {
    if (window.WebSocketManager && window.WebSocketManager.isConnected()) {
      // Listen for elevation-specific progress updates
      const originalOnMessage = window.WebSocketManager.onMessage;
      
      window.WebSocketManager.onMessage = (data) => {
        if (data.source === 'elevation_data') {
          progressCallback({
            type: data.type,
            message: data.message,
            progress: data.progress,
            stage: data.stage,
            metadata: data
          });
        }
        
        // Call original handler if it exists
        if (originalOnMessage) {
          originalOnMessage(data);
        }
      };
    }
  }

  /**
   * Determine region type for optimization
   * @private
   */
  _determineRegionType(latitude, longitude) {
    // Brazilian Amazon region
    if (latitude >= -12 && latitude <= 5 && longitude >= -74 && longitude <= -44) {
      return 'amazon';
    }
    
    // Brazilian Atlantic Forest
    if (latitude >= -30 && latitude <= -5 && longitude >= -50 && longitude <= -34) {
      return 'atlantic_forest';
    }
    
    // Brazilian Cerrado
    if (latitude >= -24 && latitude <= -2 && longitude >= -60 && longitude <= -41) {
      return 'cerrado';
    }
    
    // Other Brazilian regions
    if (latitude >= -34 && latitude <= 6 && longitude >= -74 && longitude <= -28) {
      return 'brazil_other';
    }
    
    // International
    return 'international';
  }

  /**
   * Get optimal buffer size for region type
   * @private
   */
  _getOptimalBufferSize(regionType) {
    const bufferMap = {
      amazon: 2.5,
      atlantic_forest: 2.0,
      cerrado: 2.0,
      brazil_other: 2.0,
      international: 1.5
    };
    
    return bufferMap[regionType] || 2.0;
  }

  /**
   * Get optimal dataset for region type
   * @private
   */
  _getOptimalDataset(regionType) {
    const datasetMap = {
      amazon: 'NASADEM',
      atlantic_forest: 'COP30',
      cerrado: 'COP30',
      brazil_other: 'COP30',
      international: 'SRTM'
    };
    
    return datasetMap[regionType] || 'COP30';
  }

  /**
   * Get optimal resolution for region type
   * @private
   */
  _getOptimalResolution(regionType) {
    const resolutionMap = {
      amazon: 'high',
      atlantic_forest: 'high',
      cerrado: 'medium',
      brazil_other: 'medium',
      international: 'medium'
    };
    
    return resolutionMap[regionType] || 'medium';
  }
}

// Export for global usage
window.ElevationService = ElevationService;

Utils.log('info', 'ElevationService initialized successfully');
