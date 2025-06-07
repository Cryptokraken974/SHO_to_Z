/**
 * Map overlay management functionality
 */

window.OverlayManager = {
  mapOverlays: {},

  /**
   * Add image overlay to map
   * @param {string} processingType - Type of processing (DTM, Hillshade, etc.)
   * @param {string} imagePath - Path to the overlay image
   * @param {Array} bounds - Image bounds [[south, west], [north, east]]
   * @param {Object} options - Additional overlay options
   */
  addImageOverlay(processingType, imagePath, bounds, options = {}) {
    const map = MapManager.getMap();
    if (!map) {
      Utils.log('error', 'Map not available for overlay');
      return false;
    }

    try {
      // Remove existing overlay if present
      this.removeOverlay(processingType);

      // Create new overlay
      const overlay = L.imageOverlay(imagePath, bounds, {
        opacity: options.opacity || 0.7,
        ...options
      }).addTo(map);

      // Store overlay reference
      this.mapOverlays[processingType] = overlay;

      // Update button state
      this.updateAddToMapButtonState(processingType, true);

      // Show notification
      this.showOverlayNotification(`${processingType} overlay added to map`, 'success');

      Utils.log('info', `Added ${processingType} overlay to map`);
      return true;

    } catch (error) {
      Utils.log('error', `Failed to add ${processingType} overlay`, error);
      this.showOverlayNotification(`Failed to add ${processingType} overlay`, 'error');
      return false;
    }
  },

  /**
   * Remove overlay from map
   * @param {string} processingType - Type of processing to remove
   */
  removeOverlay(processingType) {
    const map = MapManager.getMap();
    if (!map) return;

    const overlay = this.mapOverlays[processingType];
    if (overlay) {
      map.removeLayer(overlay);
      delete this.mapOverlays[processingType];
      
      // Update button state
      this.updateAddToMapButtonState(processingType, false);
      
      // Show notification
      this.showOverlayNotification(`${processingType} overlay removed from map`, 'info');
      
      Utils.log('info', `Removed ${processingType} overlay from map`);
    }
  },

  /**
   * Toggle overlay visibility
   * @param {string} processingType - Type of processing to toggle
   */
  toggleOverlay(processingType) {
    const overlay = this.mapOverlays[processingType];
    if (!overlay) return;

    const currentOpacity = overlay.options.opacity;
    const newOpacity = currentOpacity > 0 ? 0 : 0.7;
    
    overlay.setOpacity(newOpacity);
    
    const status = newOpacity > 0 ? 'shown' : 'hidden';
    this.showOverlayNotification(`${processingType} overlay ${status}`, 'info');
    
    Utils.log('info', `Toggled ${processingType} overlay visibility: ${status}`);
  },

  /**
   * Set overlay opacity
   * @param {string} processingType - Type of processing
   * @param {number} opacity - Opacity value (0-1)
   */
  setOverlayOpacity(processingType, opacity) {
    const overlay = this.mapOverlays[processingType];
    if (overlay && opacity >= 0 && opacity <= 1) {
      overlay.setOpacity(opacity);
      Utils.log('info', `Set ${processingType} overlay opacity to ${opacity}`);
    }
  },

  /**
   * Get overlay bounds from processed file information
   * @param {string} selectedFile - Path to the selected LAZ file
   * @returns {Promise<Array>} Promise resolving to bounds array
   */
  async getOverlayBounds(selectedFile) {
    try {
      // Get the base filename without extension
      const baseName = selectedFile.split('/').pop().replace('.laz', '');
      
      // Try to get bounds from test-overlay endpoint
      const data = await overlays().getTestOverlay(baseName);
      
      if (data.bounds) {
        return data.bounds;
      }
      
      // Fallback: extract coordinates from filename and create approximate bounds
      const fileName = selectedFile.split('/').pop();
      const coords = Utils.extractCoordinatesFromFilename(fileName);
      
      if (coords) {
        // Create approximate bounds (±0.01 degrees around center point)
        const margin = 0.01;
        return [
          [coords.lat - margin, coords.lng - margin], // Southwest
          [coords.lat + margin, coords.lng + margin]  // Northeast
        ];
      }
      
      Utils.log('warn', 'Could not determine overlay bounds');
      return null;
      
    } catch (error) {
      Utils.log('error', 'Failed to get overlay bounds', error);
      return null;
    }
  },

  /**
   * Add overlay to map for a specific processing type
   * @param {string} processingType - Type of processing
   */
  async addProcessingOverlay(processingType) {
    const selectedFile = FileManager.getSelectedFile();
    if (!selectedFile) {
      Utils.showNotification('Please select a LAZ file first', 'warning');
      return;
    }

    try {
      // Get the base filename for constructing the overlay path
      const baseName = selectedFile.split('/').pop().replace('.laz', '');
      const overlayPath = `/api/overlay/${processingType}/${baseName}`;
      
      // Get overlay bounds
      const bounds = await this.getOverlayBounds(selectedFile);
      if (!bounds) {
        throw new Error('Could not determine overlay bounds');
      }

      // Add the overlay
      const success = this.addImageOverlay(processingType, overlayPath, bounds);
      
      if (success) {
        // Show the "Add to Map" button if not already visible
        this.showAddToMapButton(processingType);
      }

    } catch (error) {
      Utils.log('error', `Failed to add ${processingType} overlay`, error);
      Utils.showNotification(`Failed to add ${processingType} overlay: ${error.message}`, 'error');
    }
  },

  /**
   * Show overlay notification
   * @param {string} message - Notification message
   * @param {string} type - Notification type
   */
  showOverlayNotification(message, type = 'info') {
    // Create overlay-specific notification
    const notification = $(`
      <div class="overlay-notification overlay-notification-${type}">
        <i class="overlay-icon"></i>
        <span>${message}</span>
        <button class="overlay-close">&times;</button>
      </div>
    `);
    
    $('#map').append(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
      notification.fadeOut(() => notification.remove());
    }, 3000);
    
    // Remove on close click
    notification.find('.overlay-close').on('click', function() {
      notification.fadeOut(() => notification.remove());
    });
  },

  /**
   * Update Add to Map button state
   * @param {string} processingType - Type of processing
   * @param {boolean} isActive - Whether overlay is active
   */
  updateAddToMapButtonState(processingType, isActive) {
    const button = $(`#add-to-map-${processingType.toLowerCase()}`);
    if (button.length) {
      if (isActive) {
        button.text('Remove from Map')
               .removeClass('btn-primary')
               .addClass('btn-secondary')
               .data('active', true);
      } else {
        button.text('Add to Map')
               .removeClass('btn-secondary')
               .addClass('btn-primary')
               .data('active', false);
      }
    }
  },

  /**
   * Show Add to Map button after successful processing
   * @param {string} processingType - Type of processing
   */
  showAddToMapButton(processingType) {
    const buttonContainer = $(`#${processingType.toLowerCase()}-map-controls`);
    if (buttonContainer.length && buttonContainer.is(':hidden')) {
      buttonContainer.fadeIn();
    }
  },

  /**
   * Handle Add to Map button click
   * @param {string} processingType - Type of processing
   */
  handleAddToMapClick(processingType) {
    if (!processingType) {
      Utils.log('warn', 'handleAddToMapClick: processingType is undefined');
      return;
    }
    
    const button = $(`#add-to-map-${processingType.toLowerCase()}`);
    const isActive = button.data('active') || false;
    
    if (isActive) {
      this.removeOverlay(processingType);
    } else {
      this.addProcessingOverlay(processingType);
    }
  },

  /**
   * Add test overlay to map
   * @param {string} imageData - Base64 encoded image data
   * @param {Array} bounds - Image bounds [[south, west], [north, east]]
   */
  addTestOverlay(imageData, bounds) {
    const map = MapManager.getMap();
    if (!map) {
      Utils.log('error', 'Map not available for test overlay');
      return false;
    }

    try {
      // Remove existing test overlay if present
      this.removeOverlay('TEST');

      // Create new test overlay
      const overlay = L.imageOverlay(
        `data:image/png;base64,${imageData}`,
        bounds,
        {
          opacity: 0.7,
          interactive: false
        }
      ).addTo(map);

      // Store overlay reference
      this.mapOverlays['TEST'] = overlay;

      Utils.log('info', 'Added test overlay to map with bounds:', bounds);
      return true;

    } catch (error) {
      Utils.log('error', 'Failed to add test overlay', error);
      return false;
    }
  },

  /**
   * Add satellite image overlay to map
   * @param {string} imageFile - Image file path
   * @param {string} bandType - Band type (RED, NIR, etc.)
   */
  addSatelliteImageOverlay(imageFile, bandType, regionName) {
    const map = MapManager.getMap();
    if (!map) {
      Utils.log('error', 'Map not available for satellite overlay');
      return false;
    }

    try {
      // Remove existing satellite overlay of same type if present
      const overlayKey = `SATELLITE_${bandType}`;
      this.removeOverlay(overlayKey);

      // For now, we'll need to get bounds from the backend
      // This is a simplified implementation - in practice, you'd want to fetch the bounds
      const defaultBounds = [
        [45.51, -122.68],  // Portland area default bounds
        [45.52, -122.67]
      ];

      // Construct the correct image path using regionName
      const imagePath = regionName ? 
        `/output/${regionName}/sentinel-2/${imageFile}` : 
        `/api/image/${imageFile}`;

      // Create new satellite overlay
      const overlay = L.imageOverlay(
        imagePath,
        defaultBounds,
        {
          opacity: 0.8,
          interactive: false
        }
      ).addTo(map);

      // Store overlay reference
      this.mapOverlays[overlayKey] = overlay;

      Utils.log('info', `Added ${bandType} satellite overlay for region ${regionName} to map`);
      Utils.showNotification(`Added ${bandType} band overlay to map`, 'success');
      return true;

    } catch (error) {
      Utils.log('error', 'Failed to add satellite overlay', error);
      Utils.showNotification(`Failed to add ${bandType} overlay`, 'error');
      return false;
    }
  },

  /**
   * Clear all overlays
   */
  clearAllOverlays() {
    Object.keys(this.mapOverlays).forEach(processingType => {
      this.removeOverlay(processingType);
    });
    Utils.log('info', 'Cleared all overlays');
  },

  /**
   * Get active overlays
   * @returns {Array} Array of active overlay types
   */
  getActiveOverlays() {
    return Object.keys(this.mapOverlays);
  },

  /**
   * Enhanced overlay management using new service methods
   */
  
  /**
   * List and display available overlays
   * @param {string} regionName - Optional region filter
   */
  async listAvailableOverlays(regionName = null) {
    try {
      const overlayList = await overlays().listAvailableOverlays(regionName);
      this.displayOverlayList(overlayList);
      return overlayList;
    } catch (error) {
      Utils.log('error', 'Failed to list overlays', error);
      this.showOverlayNotification('Failed to load overlay list', 'error');
      return null;
    }
  },

  /**
   * Display overlay list in UI
   * @param {Object} overlaysData - Overlay data from service
   */
  displayOverlayList(overlaysData) {
    const container = document.getElementById('overlay-list-container');
    if (!container) return;

    const overlays = overlaysData.overlays || [];
    container.innerHTML = `
      <div class="overlay-list bg-[#2a2a2a] rounded-lg p-4">
        <h3 class="text-white text-lg font-semibold mb-3">Available Overlays (${overlays.length})</h3>
        <div class="space-y-2 max-h-64 overflow-y-auto">
          ${overlays.map(overlay => `
            <div class="overlay-item bg-[#1e1e1e] rounded p-3 flex items-center justify-between">
              <div class="flex-1">
                <div class="text-white font-medium">${overlay.name || overlay.id}</div>
                <div class="text-[#ababab] text-sm">${overlay.type} • ${overlay.region || 'Global'}</div>
              </div>
              <div class="flex gap-2">
                <button onclick="OverlayManager.showOverlayDetails('${overlay.id}')" 
                        class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                  Details
                </button>
                <button onclick="OverlayManager.loadOverlayToMap('${overlay.id}')" 
                        class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                  Load
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  },

  /**
   * Show detailed overlay information
   * @param {string} overlayId - Overlay ID
   */
  async showOverlayDetails(overlayId) {
    try {
      const [metadata, statistics] = await Promise.all([
        overlays().getOverlayMetadata(overlayId),
        overlays().getOverlayStatistics(overlayId).catch(() => null)
      ]);

      this.displayOverlayDetailsModal(overlayId, metadata, statistics);
    } catch (error) {
      Utils.log('error', 'Failed to load overlay details', error);
      this.showOverlayNotification('Failed to load overlay details', 'error');
    }
  },

  /**
   * Display overlay details in a modal
   * @param {string} overlayId - Overlay ID
   * @param {Object} metadata - Overlay metadata
   * @param {Object} statistics - Overlay statistics
   */
  displayOverlayDetailsModal(overlayId, metadata, statistics) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
      <div class="bg-[#2a2a2a] rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-white text-xl font-semibold">Overlay Details</h2>
          <button onclick="this.closest('.fixed').remove()" 
                  class="text-[#ababab] hover:text-white text-2xl">&times;</button>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-[#1e1e1e] rounded p-4">
            <h3 class="text-white font-semibold mb-3">Metadata</h3>
            <div class="space-y-2 text-sm">
              ${Object.entries(metadata).map(([key, value]) => `
                <div class="flex justify-between">
                  <span class="text-[#ababab]">${key}:</span>
                  <span class="text-white">${typeof value === 'object' ? JSON.stringify(value) : value}</span>
                </div>
              `).join('')}
            </div>
          </div>
          
          ${statistics ? `
            <div class="bg-[#1e1e1e] rounded p-4">
              <h3 class="text-white font-semibold mb-3">Statistics</h3>
              <div class="space-y-2 text-sm">
                ${Object.entries(statistics).map(([key, value]) => `
                  <div class="flex justify-between">
                    <span class="text-[#ababab]">${key}:</span>
                    <span class="text-white">${typeof value === 'number' ? value.toFixed(4) : value}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}
        </div>
        
        <div class="flex gap-3 mt-6">
          <button onclick="OverlayManager.loadOverlayToMap('${overlayId}')" 
                  class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
            Load to Map
          </button>
          <button onclick="OverlayManager.showOverlayControls('${overlayId}')" 
                  class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Controls
          </button>
          <button onclick="OverlayManager.exportOverlay('${overlayId}')" 
                  class="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">
            Export
          </button>
          <button onclick="this.closest('.fixed').remove()" 
                  class="bg-[#3a3a3a] text-white px-4 py-2 rounded hover:bg-[#4a4a4a]">
            Close
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
  },

  /**
   * Load overlay to map
   * @param {string} overlayId - Overlay ID
   */
  async loadOverlayToMap(overlayId) {
    try {
      const metadata = await overlays().getOverlayMetadata(overlayId);
      if (metadata.bounds && metadata.image_url) {
        this.addImageOverlay(overlayId, metadata.image_url, metadata.bounds);
        this.showOverlayNotification('Overlay loaded to map', 'success');
      } else {
        throw new Error('Invalid overlay metadata');
      }
    } catch (error) {
      Utils.log('error', 'Failed to load overlay to map', error);
      this.showOverlayNotification('Failed to load overlay to map', 'error');
    }
  },

  /**
   * Show overlay controls panel
   * @param {string} overlayId - Overlay ID
   */
  async showOverlayControls(overlayId) {
    const controlsPanel = document.createElement('div');
    controlsPanel.className = 'fixed top-4 right-4 bg-[#2a2a2a] rounded-lg p-4 z-40 w-80';
    controlsPanel.innerHTML = `
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-white font-semibold">Overlay Controls</h3>
        <button onclick="this.closest('.fixed').remove()" 
                class="text-[#ababab] hover:text-white">&times;</button>
      </div>
      
      <div class="space-y-4">
        <div>
          <label class="block text-[#ababab] text-sm mb-2">Opacity</label>
          <input type="range" id="opacity-slider-${overlayId}" min="0" max="100" value="70" 
                 class="w-full" onchange="OverlayManager.updateOverlayOpacity('${overlayId}', this.value / 100)">
          <span id="opacity-value-${overlayId}" class="text-white text-sm">70%</span>
        </div>
        
        <div class="flex items-center gap-2">
          <input type="checkbox" id="visibility-${overlayId}" checked 
                 onchange="OverlayManager.toggleOverlayVisibility('${overlayId}', this.checked)"
                 class="rounded">
          <label for="visibility-${overlayId}" class="text-white text-sm">Visible</label>
        </div>
        
        <div>
          <label class="block text-[#ababab] text-sm mb-2">Color Ramp</label>
          <select id="color-ramp-${overlayId}" onchange="OverlayManager.applyColorRamp('${overlayId}', this.value)"
                  class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]">
            <option value="viridis">Viridis</option>
            <option value="plasma">Plasma</option>
            <option value="inferno">Inferno</option>
            <option value="magma">Magma</option>
            <option value="terrain">Terrain</option>
            <option value="gray">Grayscale</option>
          </select>
        </div>
        
        <div class="flex gap-2">
          <button onclick="OverlayManager.cropOverlayDialog('${overlayId}')" 
                  class="flex-1 bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700">
            Crop
          </button>
          <button onclick="OverlayManager.deleteOverlay('${overlayId}')" 
                  class="flex-1 bg-red-600 text-white px-3 py-2 rounded text-sm hover:bg-red-700">
            Delete
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(controlsPanel);
  },

  /**
   * Update overlay opacity
   * @param {string} overlayId - Overlay ID
   * @param {number} opacity - Opacity value (0.0 to 1.0)
   */
  async updateOverlayOpacity(overlayId, opacity) {
    try {
      await overlays().updateOverlayOpacity(overlayId, opacity);
      
      // Update local overlay if loaded
      if (this.mapOverlays[overlayId]) {
        this.mapOverlays[overlayId].setOpacity(opacity);
      }
      
      // Update UI
      const valueSpan = document.getElementById(`opacity-value-${overlayId}`);
      if (valueSpan) {
        valueSpan.textContent = `${Math.round(opacity * 100)}%`;
      }
      
      Utils.log('info', `Updated ${overlayId} opacity to ${opacity}`);
    } catch (error) {
      Utils.log('error', 'Failed to update overlay opacity', error);
      this.showOverlayNotification('Failed to update opacity', 'error');
    }
  },

  /**
   * Toggle overlay visibility
   * @param {string} overlayId - Overlay ID
   * @param {boolean} visible - Visibility state
   */
  async toggleOverlayVisibility(overlayId, visible) {
    try {
      await overlays().toggleOverlayVisibility(overlayId, visible);
      
      // Update local overlay if loaded
      if (this.mapOverlays[overlayId]) {
        if (visible) {
          this.mapOverlays[overlayId].addTo(MapManager.getMap());
        } else {
          MapManager.getMap().removeLayer(this.mapOverlays[overlayId]);
        }
      }
      
      Utils.log('info', `${visible ? 'Showed' : 'Hidden'} overlay ${overlayId}`);
    } catch (error) {
      Utils.log('error', 'Failed to toggle overlay visibility', error);
      this.showOverlayNotification('Failed to toggle visibility', 'error');
    }
  },

  /**
   * Apply color ramp to overlay
   * @param {string} overlayId - Overlay ID
   * @param {string} colorRamp - Color ramp name
   */
  async applyColorRamp(overlayId, colorRamp) {
    try {
      const result = await overlays().applyColorRamp(overlayId, colorRamp);
      this.showOverlayNotification(`Applied ${colorRamp} color ramp`, 'success');
      
      // Reload overlay if it's currently displayed
      if (this.mapOverlays[overlayId]) {
        await this.loadOverlayToMap(overlayId);
      }
      
      Utils.log('info', `Applied ${colorRamp} color ramp to ${overlayId}`);
    } catch (error) {
      Utils.log('error', 'Failed to apply color ramp', error);
      this.showOverlayNotification('Failed to apply color ramp', 'error');
    }
  },

  /**
   * Show crop overlay dialog
   * @param {string} overlayId - Overlay ID
   */
  async cropOverlayDialog(overlayId) {
    const dialog = document.createElement('div');
    dialog.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    dialog.innerHTML = `
      <div class="bg-[#2a2a2a] rounded-lg p-6 max-w-md w-full mx-4">
        <h3 class="text-white text-lg font-semibold mb-4">Crop Overlay</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-[#ababab] text-sm mb-1">Min X (West)</label>
            <input type="number" id="crop-min-x" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" step="any">
          </div>
          <div>
            <label class="block text-[#ababab] text-sm mb-1">Min Y (South)</label>
            <input type="number" id="crop-min-y" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" step="any">
          </div>
          <div>
            <label class="block text-[#ababab] text-sm mb-1">Max X (East)</label>
            <input type="number" id="crop-max-x" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" step="any">
          </div>
          <div>
            <label class="block text-[#ababab] text-sm mb-1">Max Y (North)</label>
            <input type="number" id="crop-max-y" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" step="any">
          </div>
        </div>
        <div class="flex gap-3 mt-6">
          <button onclick="this.closest('.fixed').remove()" 
                  class="flex-1 bg-[#3a3a3a] text-white px-4 py-2 rounded hover:bg-[#4a4a4a]">
            Cancel
          </button>
          <button onclick="OverlayManager.cropOverlay('${overlayId}'); this.closest('.fixed').remove()" 
                  class="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Crop
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(dialog);
  },

  /**
   * Crop overlay with specified bounds
   * @param {string} overlayId - Overlay ID
   */
  async cropOverlay(overlayId) {
    try {
      const bounds = {
        min_x: parseFloat(document.getElementById('crop-min-x').value),
        min_y: parseFloat(document.getElementById('crop-min-y').value),
        max_x: parseFloat(document.getElementById('crop-max-x').value),
        max_y: parseFloat(document.getElementById('crop-max-y').value)
      };

      const result = await overlays().cropOverlay(overlayId, bounds);
      this.showOverlayNotification('Overlay cropped successfully', 'success');
      Utils.log('info', `Cropped overlay ${overlayId}`, result);
    } catch (error) {
      Utils.log('error', 'Failed to crop overlay', error);
      this.showOverlayNotification('Failed to crop overlay', 'error');
    }
  },

  /**
   * Export overlay
   * @param {string} overlayId - Overlay ID
   * @param {string} format - Export format
   */
  async exportOverlay(overlayId, format = 'png') {
    try {
      const result = await overlays().exportOverlay(overlayId, format);
      this.showOverlayNotification('Overlay exported successfully', 'success');
      
      // If the result contains a download URL, trigger download
      if (result.download_url) {
        const link = document.createElement('a');
        link.href = result.download_url;
        link.download = `overlay_${overlayId}.${format}`;
        link.click();
      }
      
      Utils.log('info', `Exported overlay ${overlayId} as ${format}`);
    } catch (error) {
      Utils.log('error', 'Failed to export overlay', error);
      this.showOverlayNotification('Failed to export overlay', 'error');
    }
  },

  /**
   * Delete overlay
   * @param {string} overlayId - Overlay ID
   */
  async deleteOverlay(overlayId) {
    if (!confirm(`Are you sure you want to delete overlay ${overlayId}?`)) {
      return;
    }

    try {
      await overlays().deleteOverlay(overlayId);
      
      // Remove from map if loaded
      if (this.mapOverlays[overlayId]) {
        this.removeOverlay(overlayId);
      }
      
      this.showOverlayNotification('Overlay deleted successfully', 'success');
      Utils.log('info', `Deleted overlay ${overlayId}`);
      
      // Refresh overlay list if displayed
      this.listAvailableOverlays();
    } catch (error) {
      Utils.log('error', 'Failed to delete overlay', error);
      this.showOverlayNotification('Failed to delete overlay', 'error');
    }
  },

  /**
   * Create composite overlay from multiple overlays
   * @param {string[]} overlayIds - Array of overlay IDs
   * @param {string} outputName - Name for composite overlay
   */
  async createCompositeOverlay(overlayIds, outputName) {
    try {
      const result = await overlays().createCompositeOverlay(overlayIds, outputName);
      this.showOverlayNotification('Composite overlay created successfully', 'success');
      Utils.log('info', `Created composite overlay: ${outputName}`, result);
      
      // Refresh overlay list
      this.listAvailableOverlays();
    } catch (error) {
      Utils.log('error', 'Failed to create composite overlay', error);
      this.showOverlayNotification('Failed to create composite overlay', 'error');
    }
  }
};
