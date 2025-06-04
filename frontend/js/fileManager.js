/**
 * File management functionality for regions
 */

window.FileManager = {
  selectedRegion: null, // Changed from selectedLazFile
  regionMarkers: [], // Changed from lazFileMarkers
  currentLocationPin: null,

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
      
      // Build API endpoint with optional source filter
      let url = '/api/list-regions';
      if (source) {
        url += `?source=${source}`;
      }
      
      console.log('🌐 API call to:', url);
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      console.log('✅ API response received:', data);
      console.log(`📊 Found ${(data.regions || []).length} regions in ${source || 'all'} folder(s)`);
      
      this.displayRegions(data.regions || []); // MODIFIED to displayRegions and data.regions
      this.createRegionMarkers(data.regions || []); // MODIFIED to createRegionMarkers and data.regions
      
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
      fileList.html('<div class="no-files">No regions found in input folder.</div>');
      return;
    }
    
    regions.forEach((regionInfo) => {
      // Assuming regionInfo has: name, center_lat, center_lng
      const regionName = regionInfo.name;
      const coords = (regionInfo.center_lat && regionInfo.center_lng) ? 
                     { lat: parseFloat(regionInfo.center_lat), lng: parseFloat(regionInfo.center_lng) } : null;
      
      const coordsDisplay = coords ? 
        `<small class="file-coords">Lat: ${coords.lat.toFixed(4)}, Lng: ${coords.lng.toFixed(4)}</small>` : 
        '<small class="file-coords">Coordinates not available</small>';
      
      // Using regionName for data-file-path for now, can be changed to a unique ID if available
      const regionItem = $(` 
        <div class="file-item" data-region-name="${regionName}">
          <div class="file-name">${regionName}</div>
          <div class="file-info">
            ${coordsDisplay}
          </div>
        </div>
      `);
      
      // Handle region selection
      regionItem.on('click', () => {
        this.selectRegion(regionName, coords); // MODIFIED to selectRegion
      });
      
      fileList.append(regionItem);
    });
    
    Utils.log('info', `Displayed ${regions.length} regions`);
  },

  /**
   * Select a region (previously LAZ file)
   * @param {string} regionName - Name of the selected region
   * @param {Object} coords - Coordinates object with lat/lng
   */
  selectRegion(regionName, coords = null) { // MODIFIED to selectRegion
    this.selectedRegion = regionName;
    
    // Update UI to show selected region
    $('.file-item').removeClass('selected');
    $(`.file-item[data-region-name="${regionName}"]`).addClass('selected');
    
    $('#selected-region-name')
      .text(regionName)
      .removeClass('text-[#666]')
      .addClass('text-[#00bfff]');
    
    // Update global region selector
    if (UIManager && UIManager.updateGlobalRegionSelector) {
      UIManager.updateGlobalRegionSelector(regionName);
    }
    
    // Center map on region location if coordinates are available
    if (coords && Utils.isValidCoordinate(coords.lat, coords.lng)) {
      MapManager.setView(coords.lat, coords.lng, 13);
      this.updateLocationPin(coords.lat, coords.lng, regionName); // Pass regionName
    }
    
    Utils.log('info', `Selected region: ${regionName}`, { coords });
    Utils.showNotification(`Selected Region: ${regionName}`, 'success', 2000);

    // Potentially trigger display of Sentinel-2 images for this region if available
    // Check if Sentinel-2 data exists for this region and display it
    // This requires a new function or modification to an existing one
    UIManager.displaySentinel2ImagesForRegion(regionName);

    //Potentially trigger display of LIDAR raster images for this region if available
    UIManager.displayLidarRasterForRegion(regionName);
    
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
    // Clear existing markers
    this.clearRegionMarkers(); // MODIFIED to clearRegionMarkers
    
    regions.forEach((regionInfo) => {
      const regionName = regionInfo.name;
      let coords = null;
      if (regionInfo.center_lat && regionInfo.center_lng) {
        coords = { lat: parseFloat(regionInfo.center_lat), lng: parseFloat(regionInfo.center_lng) };
      }
      // Optionally, could try to parse from regionName if it contains coords and DB doesn't
      
      if (coords && Utils.isValidCoordinate(coords.lat, coords.lng)) {
        const marker = MapManager.addMarker(coords.lat, coords.lng, {
          popup: `Region: ${regionName}<br>Lat: ${coords.lat.toFixed(4)}<br>Lng: ${coords.lng.toFixed(4)}`, // MODIFIED popup text
          onClick: () => {
            this.selectRegion(regionName, coords); // MODIFIED to selectRegion
          }
        });
        
        if (marker) {
          this.regionMarkers.push(marker); // MODIFIED to regionMarkers
        }
        
        Utils.log('info', `Added marker for region ${regionName} at ${coords.lat}, ${coords.lng}`);
      }
    });
    
    Utils.log('info', `Created ${this.regionMarkers.length} region markers`); // MODIFIED log
  },

  /**
   * Clear all region markers from the map (previously LAZ file markers)
   */
  clearRegionMarkers() { // MODIFIED to clearRegionMarkers
    this.regionMarkers.forEach(marker => { // MODIFIED to regionMarkers
      MapManager.removeMarker(marker);
    });
    this.regionMarkers = []; // MODIFIED to regionMarkers
  },

  /**
   * Get the currently selected region (previously file)
   * @returns {string|null} Name of selected region or null
   */
  getSelectedRegion() { // MODIFIED to getSelectedRegion
    return this.selectedRegion; // MODIFIED to selectedRegion
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
    $('#selected-region-name').text('No region selected').removeClass('text-[#00bfff]').addClass('text-[#666]'); // MODIFIED message
    $('#analysis-selected-region-name').text('No region selected'); // Clear Analysis tab too
    
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
    // Clear satellite image gallery when selection is cleared
    $('#satellite-gallery').empty().html('<div class="no-files">Select a region to see satellite images.</div>');
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
      
      const response = await fetch(`/api/delete-region/${regionName}`, {
        method: 'DELETE',
      });
      
      const data = await response.json();
      
      if (data.success) {
        Utils.log('info', `Successfully deleted region: ${regionName}`, data);
        
        // If this was the selected region, clear the selection
        if (this.selectedRegion === regionName) {
          this.selectedRegion = null;
        }
        
        // Clear map markers if necessary
        this.clearRegionMarkers();
        
        // Reload file list with the same source filter as currently displayed
        const modal = $('#file-modal');
        const isForGlobal = modal.data('for-global');
        const source = isForGlobal ? 'input' : null; // Only reload input regions for global modal
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
};
