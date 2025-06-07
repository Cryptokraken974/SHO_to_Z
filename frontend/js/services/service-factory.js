/**
 * Service Factory for Frontend
 * 
 * JavaScript implementation of the backend ServiceFactory pattern.
 * Provides convenient factory methods for creating and managing API services.
 */

class ServiceFactory {
  /**
   * Factory class for creating and managing API services
   * @param {string} baseURL - Base URL for API calls
   */
  constructor(baseURL = window.location.origin) {
    this.baseURL = baseURL;
    this._services = {};
  }

  /**
   * Get or create ElevationService instance
   * @returns {ElevationService} ElevationService instance
   */
  getElevationService() {
    if (!this._services.elevation) {
      this._services.elevation = new ElevationService();
    }
    return this._services.elevation;
  }

  /**
   * Get or create SatelliteService instance
   * @returns {SatelliteAPIClient} SatelliteService instance
   */
  getSatelliteService() {
    if (!this._services.satellite) {
      this._services.satellite = new SatelliteAPIClient();
    }
    return this._services.satellite;
  }

  /**
   * Get or create ProcessingService instance
   * @returns {ProcessingAPIClient} ProcessingService instance
   */
  getProcessingService() {
    if (!this._services.processing) {
      this._services.processing = new ProcessingAPIClient();
    }
    return this._services.processing;
  }

  /**
   * Get or create RegionAnalysisService instance
   * @returns {RegionAnalysisAPIClient} RegionAnalysisService instance
   */
  getRegionAnalysisService() {
    if (!this._services.regionAnalysis) {
      this._services.regionAnalysis = new RegionAnalysisAPIClient();
    }
    return this._services.regionAnalysis;
  }

  /**
   * Get or create OverlayService instance
   * @returns {OverlayAPIClient} OverlayService instance
   */
  getOverlayService() {
    if (!this._services.overlay) {
      this._services.overlay = new OverlayAPIClient();
    }
    return this._services.overlay;
  }

  /**
   * Get or create RegionService instance
   * @returns {RegionAPIClient} RegionService instance
   */
  getRegionService() {
    if (!this._services.region) {
      this._services.region = new RegionAPIClient();
    }
    return this._services.region;
  }

  /**
   * Get or create GeotiffService instance
   * @returns {GeotiffAPIClient} GeotiffService instance
   */
  getGeotiffService() {
    if (!this._services.geotiff) {
      this._services.geotiff = new GeotiffAPIClient();
    }
    return this._services.geotiff;
  }

  /**
   * Get or create SavedPlacesService instance
   * @returns {SavedPlacesAPIClient} SavedPlacesService instance
   */
  getSavedPlacesService() {
    if (!this._services.savedPlaces) {
      this._services.savedPlaces = new SavedPlacesAPIClient();
    }
    return this._services.savedPlaces;
  }

  /**
   * Get or create LAZService instance
   * @returns {LAZAPIClient} LAZService instance
   */
  getLAZService() {
    if (!this._services.laz) {
      this._services.laz = new LAZAPIClient();
    }
    return this._services.laz;
  }

  /**
   * Clear all service instances
   */
  clearAll() {
    this._services = {};
  }

  /**
   * Get all service instances
   * @returns {Object} Object containing all service instances
   */
  getAllServices() {
    return { ...this._services };
  }
}

/**
 * Convenience functions for quick service access
 */

function createElevationService() {
  return new ElevationService();
}

function createSatelliteService() {
  return new SatelliteAPIClient();
}

function createProcessingService() {
  return new ProcessingAPIClient();
}

function createOverlayService() {
  return new OverlayAPIClient();
}

function createRegionAnalysisService() {
  return new RegionAnalysisAPIClient();
}

function createRegionService() {
  return new RegionAPIClient();
}

function createGeotiffService() {
  return new GeotiffAPIClient();
}

function createSavedPlacesService() {
  return new SavedPlacesAPIClient();
}

function createLAZService() {
  return new LAZAPIClient();
}

// Global service factory instance
const defaultFactory = new ServiceFactory();

// Convenience aliases matching the backend pattern
const regions = () => defaultFactory.getRegionService();
const processing = () => defaultFactory.getProcessingService();
const elevation = () => defaultFactory.getElevationService();
const satellite = () => defaultFactory.getSatelliteService();
const overlays = () => defaultFactory.getOverlayService();
const savedPlaces = () => defaultFactory.getSavedPlacesService();
const geotiff = () => defaultFactory.getGeotiffService();
const regionAnalysis = () => defaultFactory.getRegionAnalysisService();
const laz = () => defaultFactory.getLAZService();

// Export for use in modules or global access
window.ServiceFactory = ServiceFactory;
window.defaultFactory = defaultFactory;

// Export convenience functions
window.createElevationService = createElevationService;
window.createSatelliteService = createSatelliteService;
window.createProcessingService = createProcessingService;
window.createOverlayService = createOverlayService;
window.createRegionService = createRegionService;
window.createGeotiffService = createGeotiffService;
window.createSavedPlacesService = createSavedPlacesService;
window.createRegionAnalysisService = createRegionAnalysisService;
window.createLAZService = createLAZService;

// Export convenience aliases
window.regions = regions;
window.processing = processing;
window.elevation = elevation;
window.satellite = satellite;
window.overlays = overlays;
window.savedPlaces = savedPlaces;
window.geotiff = geotiff;
window.regionAnalysis = regionAnalysis;
window.laz = laz;
