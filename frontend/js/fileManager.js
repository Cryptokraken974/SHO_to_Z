/**
 * File management functionality for regions
 */

window.FileManager = {
  selectedRegion: null, // Changed from selectedLazFile
  processingRegion: null, // Region name to use for API processing calls
  regionPath: null, // Store the full path to the region file
  regionMarkers: [], // Changed from lazFileMarkers
  regionBoundRectangles: [], // To store Leaflet rectangle layers for bounds
  currentLocationPin: null,
  pendingRegionsForMarkers: null, // Store regions when map isn't ready yet

  /**
   * Load available regions from server (previously LAZ files)
   * @param {string} source - Optional filter: 'input', 'output', or null for both
   */
  async loadFiles(source = null) {
    console.log('📂 FileManager.loadFiles() called with source:', source || 'all');
    console.log('🔍 Folders being searched:');
    
    if (source === 'input') {
      console.log('  📁 input/ (LAZ files for processing)');
    } else if (source === 'output') {
      console.log('  📁 output/ (processed results)');
    } else {
      console.log('  📁 input/ (LAZ files for processing)');
      console.log('  📁 output/ (processed results)');
    }
    
    Utils.log('info', `Loading available regions from server (source: ${source || 'all'})`);
    
    try {
      $('#file-list').html('<div class="loading">Loading regions...</div>');
      
      console.log('🌐 API call via RegionAPIClient');
      
      const data = await regions().listRegions(source);
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      console.log('✅ API response received:', data);
      console.log(`📊 Found ${(data.regions || []).length} regions in ${source || 'all'} folder(s)`);
      
      // Fetch coordinates for LAZ files before displaying
      const regionsWithCoords = await this.fetchLAZCoordinates(data.regions || []);
      
      this.displayRegions(regionsWithCoords); // MODIFIED to displayRegions and data.regions
      this.createRegionMarkers(regionsWithCoords); // MODIFIED to createRegionMarkers and data.regions
      
    } catch (error) {
      console.error('❌ Error loading regions:', error);
      Utils.log('error', 'Failed to load regions', error);
      $('#file-list').html(`<div class="error">Error loading regions: ${error.message}</div>`);
      Utils.showNotification('Failed to load regions', 'error');
    }
  },

  /**
   * Display regions in the list (previously files)
   * @param {Array} regions - Array of region information
   */
  displayRegions(regions) { // MODIFIED to displayRegions
    const fileList = $('#file-list');
    fileList.empty();
    
    if (regions.length === 0) {
      fileList.html('<div class="no-files">No regions found.</div>');
      return;
    }
    
    regions.forEach((regionInfo) => {
      // regionInfo has: name (display), region_name (for processing), center_lat, center_lng, file_path
      const displayName = regionInfo.name;
      const processingRegion = regionInfo.region_name || regionInfo.name; // Fallback to name if region_name not available
      const coords = (regionInfo.center_lat && regionInfo.center_lng) ? 
                     { lat: parseFloat(regionInfo.center_lat), lng: parseFloat(regionInfo.center_lng) } : null;
      const filePath = regionInfo.file_path; // Use correct property name from backend
      
      const coordsDisplay = coords ? 
        `<small class="file-coords">Lat: ${coords.lat.toFixed(4)}, Lng: ${coords.lng.toFixed(4)}</small>` : 
        '<small class="file-coords">Coordinates not available</small>';
      
      // Store display name, processing region name, and file path
      const regionItem = $(` 
        <div class="file-item" data-region-name="${displayName}" data-processing-region="${processingRegion}" data-file-path="${filePath || ''}">
          <div class="file-name">${displayName}</div>
          <div class="file-info">
            ${coordsDisplay}
          </div>
        </div>
      `);
      
      // Store the region data immediately when creating the item
      if (coords) {
        regionItem.data('coords', coords);
      }
      if (regionInfo.bounds && typeof regionInfo.bounds === 'object') { // Check if bounds is a valid object
        regionItem.data('bounds', regionInfo.bounds);
      }
      if (filePath) {
        regionItem.data('filePath', filePath);
      }
      
      // Handle region highlighting (browsing) - don't trigger selection yet
      regionItem.on('click', () => {
        // Only highlight the region, don't select it yet
        $('.file-item').removeClass('selected');
        regionItem.addClass('selected');
        
        // Show the delete button when a region is highlighted
        $('#delete-region-btn').removeClass('hidden');
      });
      
      fileList.append(regionItem);
    });
    
    Utils.log('info', `Displayed ${regions.length} regions`);
  },

  /**
   * Select a region (previously LAZ file)
   * @param {string} displayName - Display name of the selected region
   * @param {Object} coords - Coordinates object with lat/lng
   * @param {string} processingRegion - Region name to use for processing API calls
   * @param {string} regionPath - Full file path of the region (especially for LAZ files)
   * @param {Object} bounds - Optional bounds object {north, south, east, west}
   */
  selectRegion(displayName, coords = null, processingRegion = null, regionPath = null, bounds = null) { // MODIFIED to selectRegion, added regionPath and bounds
    // Satellite gallery removed - NDVI now handled in raster gallery
    
    this.selectedRegion = displayName;
    this.processingRegion = processingRegion || displayName; // Store the processing region separately
    this.regionPath = regionPath; // Store the region path
    this.selectedRegionBounds = bounds; // Store the bounds
    
    // Update UI to show selected region
    $('.file-item').removeClass('selected');
    $(`.file-item[data-region-name="${displayName}"]`).addClass('selected');
    
    $('#selected-region-name')
      .text(displayName)
      .removeClass('text-[#666]')
      .addClass('text-[#00bfff]');
    
    // Update global region selector
    if (UIManager && UIManager.updateGlobalRegionSelector) {
      UIManager.updateGlobalRegionSelector(displayName);
    }
    
    // Center map on region location if coordinates are available
    if (coords && Utils.isValidCoordinate(coords.lat, coords.lng)) {
      MapManager.setView(coords.lat, coords.lng, 13);
      this.updateLocationPin(coords.lat, coords.lng, displayName); // Pass displayName
    }
    
    // Auto-fill the region name input field with the filename without extension
    const regionNameWithoutExt = displayName.replace(/\.[^/.]+$/, '');
    $('#region-name-input').val(regionNameWithoutExt);
    
    // This block was added to handle LAZ file specific actions
    if (displayName && displayName.toLowerCase().endsWith('.laz') && regionPath) { // Check regionPath
        UIManager.fetchAndDisplayRegionCoords(regionPath); // Pass the full path
    } else {
        // Clear lat/lon fields if not a LAZ file or if they should be specific to LAZ selection
        $('#lat-input').val('');
        $('#lng-input').val('');
    }

    // Create simple coordinate metadata when a region is selected
    if (coords && coords.lat && coords.lng && window.MetadataManager) {
      MetadataManager.createRegionMetadata(displayName, coords, this.processingRegion);
    }

    Utils.log('info', `Selected region: ${displayName} (processing region: ${this.processingRegion}, path: ${regionPath})`, { coords, bounds: this.selectedRegionBounds });
    Utils.showNotification(`Selected Region: ${displayName}`, 'success', 2000);
    
  },

  /**
   * Update the current location pin on the map
   * @param {number} lat - Latitude
   * @param {number} lng - Longitude
   * @param {string} regionName - Region name for popup
   */
  updateLocationPin(lat, lng, regionName) { // MODIFIED to accept regionName
    // Remove existing location pin
    if (this.currentLocationPin) {
      MapManager.removeMarker(this.currentLocationPin);
    }
    
    // Add new location pin
    this.currentLocationPin = MapManager.addMarker(lat, lng, {
      popup: `Selected Region: ${regionName}<br>Lat: ${lat.toFixed(4)}<br>Lng: ${lng.toFixed(4)}`, // MODIFIED popup text
      label: regionName,
      onClick: () => {
        // Re-center on click
        MapManager.setView(lat, lng, 13);
      }
    });
    
    if (this.currentLocationPin) {
      this.currentLocationPin.openPopup();
    }
  },

  /**
   * Create markers for all regions on the map (previously LAZ files)
   * @param {Array} regions - Array of region information
   */
  createRegionMarkers(regions) { // MODIFIED to createRegionMarkers
    // Check if map is available before creating markers
    if (!MapManager.map || !MapManager.getMap()) {
      Utils.log('warn', 'Map not yet initialized, storing regions for later marker creation');
      this.pendingRegionsForMarkers = regions; // Store for later
      return;
    }
    
    // Clear existing markers
    this.clearRegionMarkers(); // MODIFIED to clearRegionMarkers
    
    regions.forEach((regionInfo) => {
      const regionName = regionInfo.name;
      const filePath = regionInfo.file_path; // Use correct property name from backend
      let coords = null;
      if (regionInfo.center_lat && regionInfo.center_lng) {
        coords = { lat: parseFloat(regionInfo.center_lat), lng: parseFloat(regionInfo.center_lng) };
      }
      // Optionally, could try to parse from regionName if it contains coords and DB doesn't
      
      if (coords && Utils.isValidCoordinate(coords.lat, coords.lng)) {
        const marker = MapManager.addMarker(coords.lat, coords.lng, {
          popup: `Region: ${regionName}<br>Lat: ${coords.lat.toFixed(4)}<br>Lng: ${coords.lng.toFixed(4)}`, // MODIFIED popup text
          label: regionName,
          onClick: () => {
            this.selectRegion(regionName, coords, regionInfo.region_name || regionName, filePath, regionInfo.bounds || null); // MODIFIED to selectRegion, pass filePath and bounds
          }
        });
        
        if (marker) {
          this.regionMarkers.push(marker); // MODIFIED to regionMarkers
        }
        
        Utils.log('info', `Added marker for region ${regionName} at ${coords.lat}, ${coords.lng}`);
      }

      // Draw bounds rectangle
      if (regionInfo.bounds &&
          typeof regionInfo.bounds.min_lat === 'number' &&
          typeof regionInfo.bounds.min_lng === 'number' &&
          typeof regionInfo.bounds.max_lat === 'number' &&
          typeof regionInfo.bounds.max_lng === 'number') {

        const south = regionInfo.bounds.min_lat;
        const west = regionInfo.bounds.min_lng;
        const north = regionInfo.bounds.max_lat;
        const east = regionInfo.bounds.max_lng;

        // Ensure coordinates are valid before creating rectangle
        // Using a simple check for validity here. Utils.isValidCoordinate typically checks single points.
        if (isFinite(north) && isFinite(south) && isFinite(east) && isFinite(west) &&
            north >= -90 && north <= 90 && south >= -90 && south <= 90 &&
            east >= -180 && east <= 180 && west >= -180 && west <= 180 &&
            north > south && east > west) { // Basic sanity check for bounds

          const leafletBounds = [[south, west], [north, east]];
          const rectangle = L.rectangle(leafletBounds, {
            color: "#3388ff",
            weight: 1,        // Thinner weight for less visual clutter
            fillOpacity: 0.05,  // More transparent
            interactive: false
          }).addTo(MapManager.getMap());

          this.regionBoundRectangles.push(rectangle);
        } else {
          Utils.log('warn', `Invalid or inconsistent bounds for region ${regionInfo.name}:`, regionInfo.bounds);
        }
      }
    });
    
    Utils.log('info', `Created ${this.regionMarkers.length} region markers and ${this.regionBoundRectangles.length} bound rectangles`); // MODIFIED log
  },

  /**
   * Create markers for pending regions when map becomes available
   */
  createPendingRegionMarkers() {
    if (this.pendingRegionsForMarkers && MapManager.map && MapManager.getMap()) {
      Utils.log('info', 'Map is now ready, creating pending region markers');
      const pendingRegions = this.pendingRegionsForMarkers;
      this.pendingRegionsForMarkers = null; // Clear pending
      this.createRegionMarkers(pendingRegions); // Create markers now
    }
  },

  /**
   * Ensure region markers are visible on the map
   * Called after region selection to make sure markers don't disappear
   */
  ensureRegionMarkersVisible() {
    if (MapManager.map && MapManager.getMap() && this.regionMarkers.length === 0 && this.pendingRegionsForMarkers) {
      // If no markers are visible but we have pending regions, create them
      this.createPendingRegionMarkers();
    }
  },

  /**
   * Clear all region markers and bound rectangles from the map
   */
  clearRegionMarkers() {
    // Existing code to remove center markers:
    this.regionMarkers.forEach(marker => {
      MapManager.removeMarker(marker);
    });
    this.regionMarkers = [];

    // New code to remove bound rectangles:
    this.regionBoundRectangles.forEach(rectangle => {
      if (MapManager.getMap() && MapManager.getMap().hasLayer(rectangle)) {
        MapManager.getMap().removeLayer(rectangle);
      }
    });
    this.regionBoundRectangles = [];
  },

  /**
   * Get the currently selected region (previously file)
   * @returns {string|null} Name of selected region or null
   */
  getSelectedRegion() { // MODIFIED to getSelectedRegion
    return this.selectedRegion; // MODIFIED to selectedRegion
  },

  /**
   * Get the processing region name for API calls
   * @returns {string|null} Processing region name or null
   */
  getProcessingRegion() {
    return this.processingRegion || this.selectedRegion;
  },

  /**
   * Get the region file path
   * @returns {string|null} Region file path or null
   */
  getRegionPath() {
    return this.regionPath;
  },

  /**
   * Check if a region is selected (previously file)
   * @returns {boolean} True if a region is selected
   */
  hasSelectedRegion() { // MODIFIED to hasSelectedRegion
    return this.selectedRegion !== null; // MODIFIED to selectedRegion
  },

  /**
   * Clear current selection
   */
  clearSelection() {
    this.selectedRegion = null; // MODIFIED to selectedRegion
    this.processingRegion = null; // Clear processing region too
    this.regionPath = null; // Clear region path too
    $('#selected-region-name').text('No region selected').removeClass('text-[#00bfff]').addClass('text-[#666]'); // MODIFIED message
    
    // Update global region selector
    if (UIManager && UIManager.updateGlobalRegionSelector) {
      UIManager.updateGlobalRegionSelector(null);
    }
    
    if (this.currentLocationPin) {
      MapManager.removeMarker(this.currentLocationPin);
      this.currentLocationPin = null;
    }
    // UIManager.updateProcessingButtons(false); // This might need to be adapted based on new logic
    UIManager.hideFileInfo();
    $('.file-item').removeClass('selected');
    // Clear raster galleries when selection is cleared
    this.clearRegionSelection();
    Utils.log('info', 'Region selection cleared');
  },

  /**
   * Delete a region from the system
   * @param {string} regionName - Name of the region to delete
   * @returns {Promise<Object>} - Result of the deletion operation
   */
  async deleteRegion(regionName) {
    try {
      Utils.log('info', `Deleting region: ${regionName}`);
      
      const data = await regions().deleteRegion(regionName);
      
      if (data.success) {
        Utils.log('info', `Successfully deleted region: ${regionName}`, data);
        
        // If this was the selected region, clear the selection
        if (this.selectedRegion === regionName) {
          this.selectedRegion = null;
        }
        
        // Clear map markers if necessary
        this.clearRegionMarkers();
        
        // Reload file list with all regions (both input and output)
        const modal = $('#file-modal');
        const isForGlobal = modal.data('for-global');
        const source = isForGlobal ? null : null; // Always reload all regions for consistency
        await this.loadFiles(source);
        
        return {
          success: true,
          message: data.message
        };
      } else {
        Utils.log('error', `Failed to delete region: ${regionName}`, data);
        return {
          success: false,
          message: data.message || 'Failed to delete region'
        };
      }
    } catch (error) {
      Utils.log('error', `Error deleting region: ${regionName}`, error);
      return {
        success: false,
        message: error.message || 'An error occurred while deleting the region'
      };
    }
  },

  /**
   * Fetch coordinates for LAZ files and update region data
   * @param {Array} regions - Array of region information
   * @returns {Array} Updated regions with coordinates for LAZ files
   */
  async fetchLAZCoordinates(regions) {
    const updatedRegions = [...regions]; // Create a copy to avoid mutation
    
    Utils.log('info', 'Checking for LAZ files that need coordinate fetching...');
    
    // Find LAZ files that don't have coordinates
    const lazRegions = updatedRegions.filter(region => {
      const isLAZ = region.file_path && region.file_path.toLowerCase().endsWith('.laz');
      const hasCoords = region.center_lat && region.center_lng;
      return isLAZ && !hasCoords;
    });
    
    if (lazRegions.length === 0) {
      Utils.log('info', 'No LAZ files need coordinate fetching');
      return updatedRegions;
    }
    
    Utils.log('info', `Found ${lazRegions.length} LAZ files that need coordinates`);
    
    // Fetch coordinates for each LAZ file
    for (const region of lazRegions) {
      try {
        Utils.log('info', `Fetching coordinates for LAZ file: ${region.file_path}`);
        
        // Extract just the filename from the file path
        // region.file_path might be something like "input/LAZ/NP_T-0251.laz"
        // but the backend expects just "NP_T-0251.laz"
        const fileName = region.file_path.split('/').pop();
        
        // Use the LAZ API to get bounds
        const boundsData = await APIClient.laz.getLAZFileBounds(fileName);
        
        if (boundsData && boundsData.center) {
          // Update the region with coordinates
          const regionIndex = updatedRegions.findIndex(r => r.file_path === region.file_path);
          if (regionIndex !== -1) {
            updatedRegions[regionIndex] = {
              ...updatedRegions[regionIndex],
              center_lat: boundsData.center.lat,
              center_lng: boundsData.center.lng,
              bounds: boundsData.bounds // Store full bounds if needed
            };
            
            Utils.log('info', `Updated coordinates for ${region.name}: ${boundsData.center.lat}, ${boundsData.center.lng}`);
          }
        } else {
          Utils.log('warn', `Failed to get coordinates for LAZ file: ${region.file_path}`);
        }
      } catch (error) {
        Utils.log('error', `Error fetching coordinates for ${region.file_path}:`, error);
        // Continue with other files even if one fails
      }
    }
    
    return updatedRegions;
  },

  /**
   * Get cache statistics for administrative display
   * @returns {Object} Cache statistics
   */
  async getCacheStatistics() {
    try {
      const cacheClient = APIClient.cacheManagement;
      const stats = await cacheClient.getCacheStats();
      const health = await cacheClient.getCacheHealth();
      
      return {
        success: true,
        statistics: stats.stats,
        health: health.health
      };
    } catch (error) {
      Utils.log('error', 'Failed to get cache statistics:', error);
      return {
        success: false,
        error: error.message
      };
    }
  },

  /**
   * Display cache management UI (for administrators)
   */
  displayCacheManagement() {
    const cacheSection = `
      <div id="cache-management-section" class="admin-section">
        <h3>LAZ Metadata Cache Management</h3>
        <div id="cache-stats-container">
          <div class="loading">Loading cache statistics...</div>
        </div>
        <div class="cache-actions">
          <button id="refresh-cache-btn" class="btn btn-primary">Refresh All Cache</button>
          <button id="clear-cache-btn" class="btn btn-warning">Clear Cache</button>
          <button id="validate-cache-btn" class="btn btn-secondary">Validate Cache</button>
          <button id="cache-maintenance-btn" class="btn btn-info">Run Maintenance</button>
        </div>
        <div id="cache-operations-log" class="operations-log">
          <h4>Cache Operations Log</h4>
          <div id="cache-log-content"></div>
        </div>
      </div>
    `;

    // Add cache section to file manager or admin panel
    const targetContainer = $('#admin-panel') || $('#file-manager-container');
    if (targetContainer.length) {
      targetContainer.append(cacheSection);
      this.bindCacheManagementEvents();
      this.loadCacheStatistics();
    }
  },

  /**
   * Bind event handlers for cache management actions
   */
  bindCacheManagementEvents() {
    const cacheClient = APIClient.cacheManagement;

    $('#refresh-cache-btn').on('click', async () => {
      await this.performCacheOperation('refresh', async () => {
        return await cacheClient.refreshAllCache();
      });
    });

    $('#clear-cache-btn').on('click', async () => {
      if (confirm('Are you sure you want to clear all cached metadata? This will require re-processing coordinates for all LAZ files.')) {
        await this.performCacheOperation('clear', async () => {
          return await cacheClient.clearCache();
        });
      }
    });

    $('#validate-cache-btn').on('click', async () => {
      await this.performCacheOperation('validate', async () => {
        return await cacheClient.validateCache();
      });
    });

    $('#cache-maintenance-btn').on('click', async () => {
      await this.performCacheOperation('maintenance', async () => {
        return await cacheClient.performMaintenance({
          validateIntegrity: true,
          removeInvalid: true
        });
      });
    });
  },

  /**
   * Perform a cache operation and log the results
   * @param {string} operationType - Type of operation
   * @param {Function} operation - Async operation function
   */
  async performCacheOperation(operationType, operation) {
    const logContainer = $('#cache-log-content');
    const timestamp = new Date().toLocaleTimeString();
    
    logContainer.append(`<div class="log-entry">[${timestamp}] Starting ${operationType} operation...</div>`);
    
    try {
      const result = await operation();
      
      if (result.success) {
        logContainer.append(`<div class="log-entry success">[${timestamp}] ${operationType} completed successfully</div>`);
        if (result.message) {
          logContainer.append(`<div class="log-entry">[${timestamp}] ${result.message}</div>`);
        }
      } else {
        logContainer.append(`<div class="log-entry error">[${timestamp}] ${operationType} failed: ${result.error || 'Unknown error'}</div>`);
      }
      
      // Refresh cache statistics after operation
      setTimeout(() => this.loadCacheStatistics(), 1000);
      
    } catch (error) {
      logContainer.append(`<div class="log-entry error">[${timestamp}] ${operationType} failed: ${error.message}</div>`);
    }
    
    // Auto-scroll to latest log entry
    logContainer.scrollTop(logContainer[0].scrollHeight);
  },

  /**
   * Load and display cache statistics
   */
  async loadCacheStatistics() {
    const statsContainer = $('#cache-stats-container');
    
    try {
      const cacheStats = await this.getCacheStatistics();
      
      if (cacheStats.success) {
        const stats = cacheStats.statistics;
        const health = cacheStats.health;
        
        const statsHtml = `
          <div class="cache-stats-grid">
            <div class="stat-item">
              <div class="stat-label">Total Entries</div>
              <div class="stat-value">${stats.total_entries || 0}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Valid Entries</div>
              <div class="stat-value">${stats.valid_entries || 0}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Error Entries</div>
              <div class="stat-value">${stats.error_entries || 0}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Cache Size</div>
              <div class="stat-value">${stats.cache_file_size_mb || 0} MB</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Oldest Entry</div>
              <div class="stat-value">${stats.oldest_entry ? new Date(stats.oldest_entry).toLocaleDateString() : 'N/A'}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Newest Entry</div>
              <div class="stat-value">${stats.newest_entry ? new Date(stats.newest_entry).toLocaleDateString() : 'N/A'}</div>
            </div>
          </div>
          <div class="cache-health">
            <h4>Cache Health</h4>
            <div class="health-indicator ${stats.error_entries === 0 ? 'healthy' : 'warning'}">
              ${stats.error_entries === 0 ? '✅ Healthy' : `⚠️ ${stats.error_entries} errors found`}
            </div>
          </div>
        `;
        
        statsContainer.html(statsHtml);
      } else {
        statsContainer.html(`<div class="error">Failed to load cache statistics: ${cacheStats.error}</div>`);
      }
    } catch (error) {
      statsContainer.html(`<div class="error">Error loading cache statistics: ${error.message}</div>`);
    }
  },

  /**
   * Enhanced fetchLAZCoordinates with cache awareness and improved error handling
   * @param {Array} regions - Array of region information
   * @returns {Array} Updated regions with coordinates for LAZ files
   */
  async fetchLAZCoordinatesWithCache(regions) {
    const updatedRegions = [...regions]; // Create a copy to avoid mutation
    
    Utils.log('info', 'Checking for LAZ files that need coordinate fetching...');
    
    // Find LAZ files that don't have coordinates
    const lazRegions = updatedRegions.filter(region => {
      const isLAZ = region.file_path && region.file_path.toLowerCase().endsWith('.laz');
      const hasCoords = region.center_lat && region.center_lng;
      return isLAZ && !hasCoords;
    });
    
    if (lazRegions.length === 0) {
      Utils.log('info', 'No LAZ files need coordinate fetching');
      return updatedRegions;
    }
    
    Utils.log('info', `Found ${lazRegions.length} LAZ files that need coordinates`);
    
    // Fetch coordinates for each LAZ file with cache awareness
    for (const region of lazRegions) {
      try {
        Utils.log('info', `Fetching coordinates for LAZ file: ${region.file_path}`);
        
        // Extract just the filename from the file path
        const fileName = region.file_path.split('/').pop();
        
        // Try to get cached data first
        let boundsData = null;
        let fromCache = false;
        
        try {
          const cachedData = await APIClient.cacheManagement.getCachedMetadata(fileName);
          if (cachedData.success && cachedData.cached && cachedData.metadata && !cachedData.metadata.error) {
            boundsData = {
              center: cachedData.metadata.center,
              bounds: cachedData.metadata.bounds,
              _cached: true,
              _cache_timestamp: cachedData.metadata.cache_timestamp
            };
            fromCache = true;
            Utils.log('info', `Using cached coordinates for ${fileName}`);
          }
        } catch (cacheError) {
          Utils.log('warn', `Cache lookup failed for ${fileName}, will fetch fresh data:`, cacheError);
        }
        
        // If no cached data, fetch from LAZ API
        if (!boundsData) {
          boundsData = await APIClient.laz.getLAZFileBounds(fileName);
          Utils.log('info', `Fetched fresh coordinates for ${fileName}`);
        }
        
        if (boundsData && boundsData.center) {
          // Update the region with coordinates
          const regionIndex = updatedRegions.findIndex(r => r.file_path === region.file_path);
          if (regionIndex !== -1) {
            updatedRegions[regionIndex] = {
              ...updatedRegions[regionIndex],
              center_lat: boundsData.center.lat,
              center_lng: boundsData.center.lng,
              bounds: boundsData.bounds, // Store full bounds if needed
              _cached_data: fromCache, // Indicate if data came from cache
              _cache_timestamp: boundsData._cache_timestamp
            };
            
            const source = fromCache ? '(cached)' : '(fresh)';
            Utils.log('info', `Updated coordinates for ${region.name}: ${boundsData.center.lat}, ${boundsData.center.lng} ${source}`);
          }
        } else {
          Utils.log('warn', `Failed to get coordinates for LAZ file: ${region.file_path}`);
        }
      } catch (error) {
        Utils.log('error', `Error fetching coordinates for ${region.file_path}:`, error);
        // Continue with other files even if one fails
      }
    }
    
    return updatedRegions;
  },
};
