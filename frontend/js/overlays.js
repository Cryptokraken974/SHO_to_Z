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
      const response = await fetch(`/api/test-overlay/${baseName}`);
      const data = await response.json();
      
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
  }
};
