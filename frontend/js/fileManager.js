/**
 * File management functionality for regions
 */

window.FileManager = {
  selectedRegion: null, // Changed from selectedLazFile
  processingRegion: null, // Region name to use for API processing calls
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
      fileList.html('<div class="no-files">No regions found in input folder.</div>');
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
      
      // Handle region highlighting (browsing) - don't trigger selection yet
      regionItem.on('click', () => {
        // Only highlight the region, don't select it yet
        $('.file-item').removeClass('selected');
        regionItem.addClass('selected');
        
        // Show the delete button when a region is highlighted
        $('#delete-region-btn').removeClass('hidden');
        
        // Store the region data for later selection
        regionItem.data('coords', coords);
        regionItem.data('filePath', filePath); // Store filePath
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
   */
  selectRegion(displayName, coords = null, processingRegion = null, regionPath = null) { // MODIFIED to selectRegion, added regionPath
    this.selectedRegion = displayName;
    this.processingRegion = processingRegion || displayName; // Store the processing region separately
    
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

    Utils.log('info', `Selected region: ${displayName} (processing region: ${this.processingRegion}, path: ${regionPath})`, { coords });
    Utils.showNotification(`Selected Region: ${displayName}`, 'success', 2000);

    // Potentially trigger display of Sentinel-2 images for this region if available
    // Check if Sentinel-2 data exists for this region and display it
    // This requires a new function or modification to an existing one
    UIManager.displaySentinel2ImagesForRegion(displayName);

    //Potentially trigger display of LIDAR raster images for this region if available
    UIManager.displayLidarRasterForRegion(displayName);
    
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
      const filePath = regionInfo.file_path; // Use correct property name from backend
      let coords = null;
      if (regionInfo.center_lat && regionInfo.center_lng) {
        coords = { lat: parseFloat(regionInfo.center_lat), lng: parseFloat(regionInfo.center_lng) };
      }
      // Optionally, could try to parse from regionName if it contains coords and DB doesn't
      
      if (coords && Utils.isValidCoordinate(coords.lat, coords.lng)) {
        const marker = MapManager.addMarker(coords.lat, coords.lng, {
          popup: `Region: ${regionName}<br>Lat: ${coords.lat.toFixed(4)}<br>Lng: ${coords.lng.toFixed(4)}`, // MODIFIED popup text
          onClick: () => {
            this.selectRegion(regionName, coords, regionInfo.region_name || regionName, filePath); // MODIFIED to selectRegion, pass filePath
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
   * Get the processing region name for API calls
   * @returns {string|null} Processing region name or null
   */
  getProcessingRegion() {
    return this.processingRegion || this.selectedRegion;
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
      
      const data = await regions().deleteRegion(regionName);
      
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
};
