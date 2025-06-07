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
    const overlay = this.mapOverlays[processingType];
    if (overlay) {
      const map = MapManager.getMap();
      if (map) {
        map.removeLayer(overlay);
      }
      delete this.mapOverlays[processingType];
      
      // Update button state
      this.updateAddToMapButtonState(processingType, false);
      
      Utils.log('info', `Removed ${processingType} overlay from map`);
    }
  },

  /**
   * Toggle overlay visibility
   * @param {string} processingType - Type of processing to toggle
   */
  toggleOverlay(processingType) {
    const overlay = this.mapOverlays[processingType];
    if (overlay) {
      const currentOpacity = overlay.getOpacity();
      const newOpacity = currentOpacity > 0 ? 0 : 0.7;
      overlay.setOpacity(newOpacity);
      Utils.log('info', `Toggled ${processingType} overlay visibility`);
    }
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
   * @param {string} processingType - Processing type
   * @param {string} filename - Filename to process
   * @param {string} selectedRegion - Selected region
   * @returns {Promise<boolean>} Success status
   */
  async addToMap(processingType, filename, selectedRegion) {
    try {
      let overlayData;
      let displayIdentifier;

      // Get overlay data based on processing context
      if (selectedRegion) {
        overlayData = await overlays().getRasterOverlayData(selectedRegion, processingType);
        displayIdentifier = selectedRegion;
      } else {
        displayIdentifier = filename.split('/').pop().replace('.laz', '');
        overlayData = await overlays().getOverlayData(processingType, displayIdentifier);
      }

      if (!overlayData || !overlayData.image_base64) {
        throw new Error('No overlay data received');
      }

      // Create data URL for the image
      const imageUrl = `data:image/png;base64,${overlayData.image_base64}`;
      
      // Get bounds
      let bounds = overlayData.bounds;
      if (!bounds && !selectedRegion) {
        bounds = await this.getOverlayBounds(filename);
      }
      
      if (!bounds) {
        throw new Error('Could not determine overlay bounds');
      }

      // Add overlay to map
      const success = this.addImageOverlay(processingType, imageUrl, bounds);
      
      if (success) {
        Utils.log('info', `Successfully added ${processingType} overlay for ${displayIdentifier}`);
        this.showOverlayNotification(`${processingType} overlay added to map`, 'success');
      }
      
      return success;

    } catch (error) {
      Utils.log('error', `Failed to add ${processingType} overlay to map`, error);
      this.showOverlayNotification(`Failed to add ${processingType} overlay: ${error.message}`, 'error');
      return false;
    }
  },

  /**
   * Update add to map button state
   * @param {string} processingType - Processing type
   * @param {boolean} isAdded - Whether overlay is added to map
   */
  updateAddToMapButtonState(processingType, isAdded) {
    const button = document.querySelector(`[data-processing-type="${processingType}"] .add-to-map-btn`);
    if (button) {
      if (isAdded) {
        button.textContent = 'Remove from Map';
        button.classList.add('remove-mode');
      } else {
        button.textContent = 'Add to Map';
        button.classList.remove('remove-mode');
      }
    }
  },

  /**
   * Show overlay notification
   * @param {string} message - Notification message
   * @param {string} type - Notification type (success, error, info)
   */
  showOverlayNotification(message, type = 'info') {
    // Try to use existing notification system
    if (window.NotificationManager && typeof window.NotificationManager.show === 'function') {
      window.NotificationManager.show(message, type);
      return;
    }

    // Fallback notification
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Create simple toast notification if no system exists
    const toast = document.createElement('div');
    toast.className = `overlay-toast overlay-toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 4px;
      color: white;
      font-weight: 500;
      z-index: 10000;
      max-width: 300px;
      word-wrap: break-word;
      background-color: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 3000);
  },

  /**
   * Handle add to map button click
   * @param {Event} event - Click event
   */
  async handleAddToMapClick(event) {
    const button = event.target;
    const processingType = button.closest('[data-processing-type]')?.dataset.processingType;
    
    if (!processingType) {
      Utils.log('error', 'No processing type found for add to map button');
      return;
    }

    // Check if overlay is currently on map
    const isCurrentlyOnMap = this.mapOverlays[processingType];
    
    if (isCurrentlyOnMap) {
      // Remove from map
      this.removeOverlay(processingType);
      this.showOverlayNotification(`${processingType} overlay removed from map`, 'info');
    } else {
      // Add to map
      const filename = window.ProcessingManager?.getCurrentFile?.() || 'default';
      const selectedRegion = window.RegionManager?.getSelectedRegion?.() || null;
      
      button.disabled = true;
      button.textContent = 'Adding...';
      
      try {
        await this.addToMap(processingType, filename, selectedRegion);
      } finally {
        button.disabled = false;
      }
    }
  },

  /**
   * Initialize overlay controls and event listeners
   */
  initializeOverlayControls() {
    // Add event listeners for add to map buttons
    document.addEventListener('click', (event) => {
      if (event.target.classList.contains('add-to-map-btn')) {
        this.handleAddToMapClick(event);
      }
    });

    Utils.log('info', 'Overlay controls initialized');
  },

  /**
   * Get all currently active overlays
   * @returns {Object} Active overlays
   */
  getActiveOverlays() {
    return { ...this.mapOverlays };
  },

  /**
   * Clear all overlays from map
   */
  clearAllOverlays() {
    Object.keys(this.mapOverlays).forEach(processingType => {
      this.removeOverlay(processingType);
    });
    Utils.log('info', 'All overlays cleared from map');
  },

  // Enhanced overlay management features

  /**
   * List available overlays with optional region filtering
   * @param {string} regionName - Optional region name filter
   */
  async listAvailableOverlays(regionName = null) {
    try {
      const overlayList = await overlays().listAvailableOverlays(regionName);
      this.displayOverlayList(overlayList);
    } catch (error) {
      Utils.log('error', 'Failed to list available overlays', error);
      this.showOverlayNotification('Failed to load overlay list', 'error');
    }
  },

  /**
   * Display overlay list in UI
   * @param {Object} overlays - Overlays data
   */
  displayOverlayList(overlays) {
    const container = document.getElementById('overlay-list-container');
    if (!container) {
      Utils.log('warn', 'Overlay list container not found');
      return;
    }

    container.innerHTML = '';

    if (!overlays.overlays || overlays.overlays.length === 0) {
      container.innerHTML = '<p class="no-overlays">No overlays available</p>';
      return;
    }

    const listHTML = overlays.overlays.map(overlay => `
      <div class="overlay-item" data-overlay-id="${overlay.id}">
        <div class="overlay-header">
          <h4>${overlay.name || overlay.id}</h4>
          <div class="overlay-actions">
            <button class="btn-small overlay-info-btn" data-overlay-id="${overlay.id}">Info</button>
            <button class="btn-small overlay-controls-btn" data-overlay-id="${overlay.id}">Controls</button>
            <button class="btn-small overlay-delete-btn" data-overlay-id="${overlay.id}">Delete</button>
          </div>
        </div>
        <div class="overlay-meta">
          <span class="overlay-type">${overlay.processing_type || 'Unknown'}</span>
          <span class="overlay-region">${overlay.region || 'N/A'}</span>
        </div>
      </div>
    `).join('');

    container.innerHTML = listHTML;

    // Add event listeners
    container.addEventListener('click', this.handleOverlayListClick.bind(this));
  },

  /**
   * Handle clicks in overlay list
   * @param {Event} event - Click event
   */
  async handleOverlayListClick(event) {
    const target = event.target;
    const overlayId = target.dataset.overlayId;

    if (!overlayId) return;

    if (target.classList.contains('overlay-info-btn')) {
      await this.showOverlayInfo(overlayId);
    } else if (target.classList.contains('overlay-controls-btn')) {
      await this.showOverlayControls(overlayId);
    } else if (target.classList.contains('overlay-delete-btn')) {
      await this.deleteOverlayWithConfirmation(overlayId);
    }
  },

  /**
   * Show detailed overlay information
   * @param {string} overlayId - Overlay ID
   */
  async showOverlayInfo(overlayId) {
    try {
      const [metadata, statistics] = await Promise.all([
        overlays().getOverlayMetadata(overlayId),
        overlays().getOverlayStatistics(overlayId).catch(() => null)
      ]);

      const modal = this.createOverlayInfoModal(overlayId, metadata, statistics);
      document.body.appendChild(modal);
    } catch (error) {
      Utils.log('error', 'Failed to get overlay information', error);
      this.showOverlayNotification('Failed to load overlay information', 'error');
    }
  },

  /**
   * Create overlay info modal
   * @param {string} overlayId - Overlay ID
   * @param {Object} metadata - Overlay metadata
   * @param {Object} statistics - Overlay statistics
   * @returns {HTMLElement} Modal element
   */
  createOverlayInfoModal(overlayId, metadata, statistics) {
    const modal = document.createElement('div');
    modal.className = 'overlay-modal';
    modal.innerHTML = `
      <div class="overlay-modal-content">
        <div class="overlay-modal-header">
          <h3>Overlay Information</h3>
          <button class="overlay-modal-close">&times;</button>
        </div>
        <div class="overlay-modal-body">
          <div class="overlay-info-section">
            <h4>Metadata</h4>
            <div class="overlay-info-grid">
              <div class="info-item">
                <label>ID:</label>
                <span>${overlayId}</span>
              </div>
              <div class="info-item">
                <label>Name:</label>
                <span>${metadata.name || 'N/A'}</span>
              </div>
              <div class="info-item">
                <label>Type:</label>
                <span>${metadata.processing_type || 'N/A'}</span>
              </div>
              <div class="info-item">
                <label>Region:</label>
                <span>${metadata.region || 'N/A'}</span>
              </div>
              <div class="info-item">
                <label>Created:</label>
                <span>${metadata.created_at || 'N/A'}</span>
              </div>
              <div class="info-item">
                <label>Format:</label>
                <span>${metadata.format || 'N/A'}</span>
              </div>
            </div>
          </div>
          ${statistics ? `
            <div class="overlay-info-section">
              <h4>Statistics</h4>
              <div class="overlay-info-grid">
                <div class="info-item">
                  <label>Min Value:</label>
                  <span>${statistics.min_value || 'N/A'}</span>
                </div>
                <div class="info-item">
                  <label>Max Value:</label>
                  <span>${statistics.max_value || 'N/A'}</span>
                </div>
                <div class="info-item">
                  <label>Mean:</label>
                  <span>${statistics.mean || 'N/A'}</span>
                </div>
                <div class="info-item">
                  <label>Std Dev:</label>
                  <span>${statistics.std_dev || 'N/A'}</span>
                </div>
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;

    // Add close event listener
    modal.querySelector('.overlay-modal-close').addEventListener('click', () => {
      document.body.removeChild(modal);
    });

    // Close on outside click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        document.body.removeChild(modal);
      }
    });

    return modal;
  },

  /**
   * Show overlay controls
   * @param {string} overlayId - Overlay ID
   */
  async showOverlayControls(overlayId) {
    try {
      const metadata = await overlays().getOverlayMetadata(overlayId);
      const modal = this.createOverlayControlsModal(overlayId, metadata);
      document.body.appendChild(modal);
    } catch (error) {
      Utils.log('error', 'Failed to load overlay controls', error);
      this.showOverlayNotification('Failed to load overlay controls', 'error');
    }
  },

  /**
   * Create overlay controls modal
   * @param {string} overlayId - Overlay ID
   * @param {Object} metadata - Overlay metadata
   * @returns {HTMLElement} Modal element
   */
  createOverlayControlsModal(overlayId, metadata) {
    const modal = document.createElement('div');
    modal.className = 'overlay-modal';
    modal.innerHTML = `
      <div class="overlay-modal-content">
        <div class="overlay-modal-header">
          <h3>Overlay Controls</h3>
          <button class="overlay-modal-close">&times;</button>
        </div>
        <div class="overlay-modal-body">
          <div class="overlay-control-section">
            <h4>Opacity</h4>
            <div class="control-group">
              <input type="range" id="opacity-slider" min="0" max="100" value="${(metadata.opacity || 1) * 100}">
              <span id="opacity-value">${Math.round((metadata.opacity || 1) * 100)}%</span>
            </div>
          </div>
          
          <div class="overlay-control-section">
            <h4>Visibility</h4>
            <div class="control-group">
              <label class="toggle-switch">
                <input type="checkbox" id="visibility-toggle" ${metadata.visible !== false ? 'checked' : ''}>
                <span class="toggle-slider"></span>
              </label>
              <span>Visible</span>
            </div>
          </div>

          <div class="overlay-control-section">
            <h4>Color Ramp</h4>
            <div class="control-group">
              <select id="color-ramp-select">
                <option value="viridis">Viridis</option>
                <option value="plasma">Plasma</option>
                <option value="inferno">Inferno</option>
                <option value="magma">Magma</option>
                <option value="coolwarm">Cool Warm</option>
                <option value="rainbow">Rainbow</option>
              </select>
              <button class="btn-small" id="apply-color-ramp">Apply</button>
            </div>
          </div>

          <div class="overlay-control-section">
            <h4>Actions</h4>
            <div class="control-actions">
              <button class="btn" id="crop-overlay-btn">Crop Overlay</button>
              <button class="btn" id="export-overlay-btn">Export Overlay</button>
            </div>
          </div>
        </div>
      </div>
    `;

    // Add event listeners
    const closeBtn = modal.querySelector('.overlay-modal-close');
    closeBtn.addEventListener('click', () => document.body.removeChild(modal));

    const opacitySlider = modal.querySelector('#opacity-slider');
    const opacityValue = modal.querySelector('#opacity-value');
    opacitySlider.addEventListener('input', async (e) => {
      const opacity = e.target.value / 100;
      opacityValue.textContent = `${e.target.value}%`;
      await this.updateOverlayOpacity(overlayId, opacity);
    });

    const visibilityToggle = modal.querySelector('#visibility-toggle');
    visibilityToggle.addEventListener('change', async (e) => {
      await this.toggleOverlayVisibility(overlayId, e.target.checked);
    });

    const applyColorRampBtn = modal.querySelector('#apply-color-ramp');
    const colorRampSelect = modal.querySelector('#color-ramp-select');
    applyColorRampBtn.addEventListener('click', async () => {
      await this.applyColorRamp(overlayId, colorRampSelect.value);
    });

    const cropBtn = modal.querySelector('#crop-overlay-btn');
    cropBtn.addEventListener('click', () => {
      document.body.removeChild(modal);
      this.showCropOverlayDialog(overlayId);
    });

    const exportBtn = modal.querySelector('#export-overlay-btn');
    exportBtn.addEventListener('click', async () => {
      await this.exportOverlay(overlayId);
    });

    return modal;
  },

  /**
   * Update overlay opacity
   * @param {string} overlayId - Overlay ID
   * @param {number} opacity - Opacity value (0.0 to 1.0)
   */
  async updateOverlayOpacity(overlayId, opacity) {
    try {
      await overlays().updateOverlayOpacity(overlayId, opacity);
      Utils.log('info', `Updated overlay ${overlayId} opacity to ${opacity}`);
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
      Utils.log('info', `Toggled overlay ${overlayId} visibility to ${visible}`);
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
      Utils.log('info', `Applied color ramp ${colorRamp} to overlay ${overlayId}`, result);
    } catch (error) {
      Utils.log('error', 'Failed to apply color ramp', error);
      this.showOverlayNotification('Failed to apply color ramp', 'error');
    }
  },

  /**
   * Show crop overlay dialog
   * @param {string} overlayId - Overlay ID
   */
  showCropOverlayDialog(overlayId) {
    const modal = document.createElement('div');
    modal.className = 'overlay-modal';
    modal.innerHTML = `
      <div class="overlay-modal-content">
        <div class="overlay-modal-header">
          <h3>Crop Overlay</h3>
          <button class="overlay-modal-close">&times;</button>
        </div>
        <div class="overlay-modal-body">
          <div class="crop-form">
            <div class="form-row">
              <div class="form-group">
                <label>North (Max Lat):</label>
                <input type="number" id="crop-north" step="0.000001" placeholder="e.g., 45.123456">
              </div>
              <div class="form-group">
                <label>South (Min Lat):</label>
                <input type="number" id="crop-south" step="0.000001" placeholder="e.g., 45.123456">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>East (Max Lng):</label>
                <input type="number" id="crop-east" step="0.000001" placeholder="e.g., -122.123456">
              </div>
              <div class="form-group">
                <label>West (Min Lng):</label>
                <input type="number" id="crop-west" step="0.000001" placeholder="e.g., -122.123456">
              </div>
            </div>
            <div class="form-actions">
              <button class="btn" id="crop-apply-btn">Apply Crop</button>
              <button class="btn btn-secondary" id="crop-cancel-btn">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Add event listeners
    modal.querySelector('.overlay-modal-close').addEventListener('click', () => {
      document.body.removeChild(modal);
    });

    modal.querySelector('#crop-cancel-btn').addEventListener('click', () => {
      document.body.removeChild(modal);
    });

    modal.querySelector('#crop-apply-btn').addEventListener('click', async () => {
      const north = parseFloat(modal.querySelector('#crop-north').value);
      const south = parseFloat(modal.querySelector('#crop-south').value);
      const east = parseFloat(modal.querySelector('#crop-east').value);
      const west = parseFloat(modal.querySelector('#crop-west').value);

      if (isNaN(north) || isNaN(south) || isNaN(east) || isNaN(west)) {
        this.showOverlayNotification('Please enter valid coordinates', 'error');
        return;
      }

      const bounds = {
        north: north,
        south: south,
        east: east,
        west: west
      };

      try {
        const result = await overlays().cropOverlay(overlayId, bounds);
        this.showOverlayNotification('Overlay cropped successfully', 'success');
        Utils.log('info', `Cropped overlay ${overlayId}`, result);
        document.body.removeChild(modal);
      } catch (error) {
        Utils.log('error', 'Failed to crop overlay', error);
        this.showOverlayNotification('Failed to crop overlay', 'error');
      }
    });
  },

  /**
   * Export overlay
   * @param {string} overlayId - Overlay ID
   * @param {string} format - Export format
   */
  async exportOverlay(overlayId, format = 'png') {
    try {
      const result = await overlays().exportOverlay(overlayId, format);
      
      if (result.download_url) {
        // Create download link
        const link = document.createElement('a');
        link.href = result.download_url;
        link.download = result.filename || `overlay_${overlayId}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.showOverlayNotification('Overlay exported successfully', 'success');
      }
      
      Utils.log('info', `Exported overlay ${overlayId}`, result);
    } catch (error) {
      Utils.log('error', 'Failed to export overlay', error);
      this.showOverlayNotification('Failed to export overlay', 'error');
    }
  },

  /**
   * Delete overlay with confirmation
   * @param {string} overlayId - Overlay ID
   */
  async deleteOverlayWithConfirmation(overlayId) {
    if (!confirm(`Are you sure you want to delete overlay ${overlayId}?`)) {
      return;
    }

    try {
      await overlays().deleteOverlay(overlayId);
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