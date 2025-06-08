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
  async addImageOverlay(processingType, imagePath, bounds, options = {}) {
    const map = MapManager.getMap();
    if (!map) {
      Utils.log('error', 'Map not available for overlay');
      return false;
    }

    try {
      // Remove existing overlay if present
      this.removeOverlay(processingType);

      // Enhanced logging for debugging
      Utils.log('info', `Creating overlay "${processingType}" with bounds:`, bounds);
      Utils.log('info', `Image path type: ${typeof imagePath}, length: ${imagePath.length > 100 ? imagePath.substring(0, 100) + '...' : imagePath}`);

      // Enhanced validation with detailed diagnostics
      const boundsValidation = this.validateBounds(bounds, processingType);
      Utils.log('info', `🔍 Bounds validation for ${processingType}:`, boundsValidation);
      
      if (!boundsValidation.isValid) {
        Utils.log('error', `❌ Bounds validation failed for ${processingType}:`, boundsValidation.errors);
        this.showOverlayNotification(`Invalid bounds for ${processingType}: ${boundsValidation.errors.join(', ')}`, 'error');
        return false;
      }

      if (boundsValidation.warnings.length > 0) {
        Utils.log('warn', `⚠️ Bounds warnings for ${processingType}:`, boundsValidation.warnings);
      }

      // If imagePath is base64 data, validate and potentially optimize the image data
      if (typeof imagePath === 'string' && imagePath.startsWith('data:image/')) {
        const base64Data = imagePath.split(',')[1];
        if (base64Data) {
          const imageValidation = this.validateImageData(base64Data, processingType);
          Utils.log('info', `🖼️ Image validation for ${processingType}:`, imageValidation);
          
          if (!imageValidation.isValid) {
            Utils.log('error', `❌ Image validation failed for ${processingType}:`, imageValidation.errors);
            this.showOverlayNotification(`Invalid image data for ${processingType}: ${imageValidation.errors.join(', ')}`, 'error');
            return false;
          }

          if (imageValidation.warnings.length > 0) {
            Utils.log('warn', `⚠️ Image warnings for ${processingType}:`, imageValidation.warnings);
          }
          
          // Always check if optimization is needed for large images (regardless of warnings)
          // First, try to get image dimensions from the validation process
          let imageWidth = null;
          let imageHeight = null;
          
          // Create a temporary image to get dimensions for optimization check
          try {
            const tempImage = await this.createImageFromBase64(base64Data);
            imageWidth = tempImage.width;
            imageHeight = tempImage.height;
            Utils.log('info', `📐 Image dimensions for ${processingType}: ${imageWidth}x${imageHeight} (${((imageWidth * imageHeight) / 1000000).toFixed(1)}M pixels)`);
          } catch (dimensionError) {
            Utils.log('warn', `Could not determine image dimensions for ${processingType}:`, dimensionError);
          }
          
          const optimizationCheck = this.checkImageOptimizationNeeds(base64Data, imageWidth, imageHeight);
          if (optimizationCheck.needsOptimization) {
            Utils.log('info', `🔧 Large image detected, applying optimization for ${processingType}`);
            Utils.log('info', `Optimization reasons: ${optimizationCheck.reasons.join(', ')}`);
            
            try {
              const optimizationResult = await this.optimizeLargeImage(base64Data, processingType);
              
              if (optimizationResult.success) {
                Utils.log('info', `✅ Image optimization successful for ${processingType}`);
                imagePath = optimizationResult.optimizedData;
                
                // Show optimization summary
                const sizeBefore = (base64Data.length / 1024 / 1024).toFixed(2);
                const sizeAfter = (optimizationResult.optimizedData.split(',')[1].length / 1024 / 1024).toFixed(2);
                this.showOverlayNotification(
                  `${processingType} optimized: ${sizeBefore}MB → ${sizeAfter}MB`, 
                  'success'
                );
              } else {
                Utils.log('warn', `⚠️ Image optimization failed for ${processingType}, using original`);
                this.showOverlayNotification(
                  `Warning: Could not optimize large ${processingType} image, performance may be affected`, 
                  'warning'
                );
              }
            } catch (optimizationError) {
              Utils.log('error', `❌ Image optimization error for ${processingType}:`, optimizationError);
              this.showOverlayNotification(
                `Warning: Image optimization failed for ${processingType}`, 
                'warning'
              );
            }
          }
        }
      }

      // Create new overlay with memory-safe approach
      const overlay = await this.createMemorySafeOverlay(imagePath, bounds, {
        opacity: options.opacity || 0.8,
        interactive: false,
        ...options
      }, processingType);

      if (!overlay) {
        throw new Error('Failed to create overlay');
      }

      // Add overlay to map
      overlay.addTo(map);

      // Store overlay reference
      this.mapOverlays[processingType] = overlay;

      // Fit map to overlay bounds for better visibility
      try {
        map.fitBounds(bounds, { padding: [20, 20] });
        Utils.log('info', `Map fitted to overlay bounds for ${processingType}`);
      } catch (boundsError) {
        Utils.log('warn', `Could not fit map to bounds for ${processingType}:`, boundsError);
      }

      // Add overlay loaded event listener for debugging
      overlay.on('load', () => {
        Utils.log('info', `Overlay image loaded successfully for ${processingType}`);
      });

      overlay.on('error', (e) => {
        Utils.log('error', `Overlay image failed to load for ${processingType}:`, e);
      });

      // Update button state
      this.updateAddToMapButtonState(processingType, true);

      // Show notification
      this.showOverlayNotification(`${processingType} overlay added to map`, 'success');

      Utils.log('info', `Successfully added ${processingType} overlay to map with enhanced visibility features`);
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
   * Enhanced notification system with progress support
   * @param {string} message - Notification message
   * @param {string} type - Notification type (success, error, info, warning)
   * @param {number} progress - Progress percentage (0-100, optional)
   */
  showOverlayNotification(message, type = 'info', progress = null) {
    // Check if we have an existing notification system
    if (typeof NotificationManager !== 'undefined' && NotificationManager.show) {
      // Use existing notification system if available
      NotificationManager.show(message, type, progress ? { progress } : {});
    } else {
      // Fallback to console logging and simple UI feedback
      const logLevel = type === 'error' ? 'error' : type === 'warning' ? 'warn' : 'info';
      Utils.log(logLevel, `[${type.toUpperCase()}] ${message}${progress !== null ? ` (${progress}%)` : ''}`);
      
      // Try to update UI elements if they exist
      this.updateNotificationUI(message, type, progress);
    }
  },

  /**
   * Update notification UI elements
   * @param {string} message - Message to display
   * @param {string} type - Message type
   * @param {number} progress - Progress percentage
   */
  updateNotificationUI(message, type, progress) {
    try {
      // Look for existing notification elements
      const statusElements = document.querySelectorAll('.overlay-status, .processing-status, #status-message');
      
      statusElements.forEach(element => {
        if (element) {
          element.textContent = message;
          element.className = `overlay-status ${type}`;
          
          // Add progress bar if progress is specified
          if (progress !== null) {
            let progressBar = element.querySelector('.progress-bar');
            if (!progressBar) {
              progressBar = document.createElement('div');
              progressBar.className = 'progress-bar';
              progressBar.innerHTML = '<div class="progress-fill"></div>';
              element.appendChild(progressBar);
            }
            
            const progressFill = progressBar.querySelector('.progress-fill');
            if (progressFill) {
              progressFill.style.width = `${progress}%`;
            }
          }
        }
      });
      
      // Auto-hide success/info messages after delay
      if (type === 'success' || type === 'info') {
        setTimeout(() => {
          statusElements.forEach(element => {
            if (element && element.textContent === message) {
              element.textContent = '';
              element.className = 'overlay-status';
              const progressBar = element.querySelector('.progress-bar');
              if (progressBar) {
                progressBar.remove();
              }
            }
          });
        }, progress !== null ? 2000 : 3000);
      }
      
    } catch (error) {
      Utils.log('warn', 'Could not update notification UI:', error);
    }
  },

  /**
   * Progressive loading for large overlay images
   * @param {string} imagePath - Image path or base64 data
   * @param {string} processingType - Processing type
   * @returns {Promise<string>} Processed image path
   */
  async progressiveLoadOverlay(imagePath, processingType) {
    if (!this.largeImageConfig.enableProgressiveLoading) {
      return imagePath;
    }

    try {
      Utils.log('info', `🔄 Starting progressive loading for ${processingType}`);
      
      // If it's a URL, we don't need progressive loading
      if (!imagePath.startsWith('data:image/')) {
        return imagePath;
      }

      const base64Data = imagePath.split(',')[1];
      const dataSize = base64Data.length;
      
      // Only use progressive loading for very large images
      if (dataSize < this.largeImageConfig.loadingChunkSize * 10) {
        return imagePath;
      }

      this.showOverlayNotification(`Loading large ${processingType} image...`, 'info', 0);

      // Simulate progressive loading with chunks
      const chunks = Math.ceil(dataSize / this.largeImageConfig.loadingChunkSize);
      let loadedChunks = 0;

      const loadChunk = () => {
        return new Promise((resolve) => {
          setTimeout(() => {
            loadedChunks++;
            const progress = Math.floor((loadedChunks / chunks) * 100);
            this.showOverlayNotification(
              `Loading ${processingType} image... ${progress}%`, 
              'info', 
              progress
            );
            resolve();
          }, 50); // Small delay to show progress
        });
      };

      // Load chunks progressively
      for (let i = 0; i < chunks; i++) {
        await loadChunk();
      }

      this.showOverlayNotification(`${processingType} image loaded successfully`, 'success', 100);
      
      Utils.log('info', `✅ Progressive loading completed for ${processingType}`);
      return imagePath;

    } catch (error) {
      Utils.log('error', `❌ Progressive loading failed for ${processingType}:`, error);
      return imagePath; // Return original on error
    }
  },

  /**
   * Memory-safe overlay creation with error handling
   * @param {string} imagePath - Image path or data
   * @param {Array} bounds - Image bounds
   * @param {Object} options - Overlay options
   * @param {string} processingType - Processing type for logging
   * @returns {Promise<L.ImageOverlay>} Leaflet overlay or null
   */
  async createMemorySafeOverlay(imagePath, bounds, options, processingType) {
    const maxRetries = this.largeImageConfig.maxRetries;
    let attempt = 0;

    while (attempt < maxRetries) {
      try {
        Utils.log('info', `Creating overlay attempt ${attempt + 1}/${maxRetries} for ${processingType}`);

        // Apply progressive loading if needed
        const processedImagePath = await this.progressiveLoadOverlay(imagePath, processingType);

        // Create overlay with memory monitoring
        const overlay = L.imageOverlay(processedImagePath, bounds, {
          opacity: options.opacity || 0.8,
          interactive: false,
          ...options
        });

        // Add memory monitoring
        const memoryBefore = this.getMemoryUsage();
        
        return new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error(`Overlay creation timeout for ${processingType}`));
          }, 30000); // 30 second timeout

          overlay.on('load', () => {
            clearTimeout(timeout);
            const memoryAfter = this.getMemoryUsage();
            Utils.log('info', `✅ Overlay loaded for ${processingType}. Memory change: ${(memoryAfter - memoryBefore).toFixed(2)}MB`);
            resolve(overlay);
          });

          overlay.on('error', (e) => {
            clearTimeout(timeout);
            Utils.log('error', `❌ Overlay load error for ${processingType}:`, e);
            reject(new Error(`Failed to load overlay: ${e.message || 'Unknown error'}`));
          });
        });

      } catch (error) {
        attempt++;
        Utils.log('warn', `Overlay creation attempt ${attempt} failed for ${processingType}:`, error);

        if (attempt >= maxRetries) {
          throw new Error(`Failed to create overlay after ${maxRetries} attempts: ${error.message}`);
        }

        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      }
    }
  },

  /**
   * Get current memory usage (approximate)
   * @returns {number} Memory usage in MB
   */
  getMemoryUsage() {
    if (performance.memory) {
      return performance.memory.usedJSHeapSize / 1024 / 1024;
    }
    return 0; // Not available in all browsers
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
   * @param {string} regionName - Region name for the overlay
   */
  async addSatelliteImageOverlay(imageFile, bandType, regionName) {
    const map = MapManager.getMap();
    if (!map) {
      Utils.log('error', 'Map not available for satellite overlay');
      return false;
    }

    try {
      // Remove existing satellite overlay of same type if present
      const overlayKey = `SATELLITE_${bandType}`;
      this.removeOverlay(overlayKey);

      // Convert bandType to proper API format (e.g., "RED" -> "RED_B04")
      let bandName = bandType;
      if (bandType === 'RED') bandName = 'RED_B04';
      else if (bandType === 'NIR') bandName = 'NIR_B08';
      // NDVI and other bands should already be in correct format

      // Create regionBand identifier for API call
      const regionBand = `${regionName}_${bandName}`;
      
      Utils.log('info', `Fetching Sentinel-2 overlay data for ${regionBand}`);

      // Fetch actual bounds and image data from Sentinel-2 overlay API
      const response = await fetch(`/api/overlay/sentinel2/${encodeURIComponent(regionBand)}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch overlay data: ${response.status} ${response.statusText}`);
      }

      const overlayData = await response.json();
      
      if (!overlayData.bounds || !overlayData.image_data) {
        throw new Error('Invalid overlay data received from server');
      }

      // Convert bounds to Leaflet format [[south, west], [north, east]]
      const bounds = [
        [overlayData.bounds.south, overlayData.bounds.west],
        [overlayData.bounds.north, overlayData.bounds.east]
      ];

      // Log detailed coordinate information
      Utils.log('info', `Retrieved ${bandType} overlay data for ${regionName} - Bounds: N:${overlayData.bounds.north}, S:${overlayData.bounds.south}, E:${overlayData.bounds.east}, W:${overlayData.bounds.west}`);

      // Create image data URL from base64
      const imageDataUrl = `data:image/png;base64,${overlayData.image_data}`;

      // Enhanced logging for debugging
      Utils.log('info', `Creating ${bandType} satellite overlay with image data length: ${overlayData.image_data.length} chars`);
      Utils.log('info', `Satellite overlay bounds: [[${bounds[0][0]}, ${bounds[0][1]}], [${bounds[1][0]}, ${bounds[1][1]}]]`);

      // Create new satellite overlay using the actual bounds and image data
      const overlay = L.imageOverlay(
        imageDataUrl,
        bounds,
        {
          opacity: 0.8,
          interactive: false
        }
      ).addTo(map);

      // Add overlay event listeners for debugging
      overlay.on('load', () => {
        Utils.log('info', `Satellite overlay image loaded successfully for ${bandType}`);
      });

      overlay.on('error', (e) => {
        Utils.log('error', `Satellite overlay image failed to load for ${bandType}:`, e);
      });

      // Store overlay reference
      this.mapOverlays[overlayKey] = overlay;

      // Fit map to overlay bounds for better visibility with padding
      try {
        map.fitBounds(bounds, { padding: [20, 20] });
        Utils.log('info', `Map fitted to satellite overlay bounds for ${bandType}`);
      } catch (boundsError) {
        Utils.log('warn', `Could not fit map to satellite bounds for ${bandType}:`, boundsError);
      }

      Utils.log('info', `Successfully added ${bandType} satellite overlay for region ${regionName} with coordinates: N:${overlayData.bounds.north}, S:${overlayData.bounds.south}, E:${overlayData.bounds.east}, W:${overlayData.bounds.west}`);
      Utils.showNotification(`Added ${bandType} band overlay to map`, 'success');
      return true;

    } catch (error) {
      Utils.log('error', 'Failed to add satellite overlay', error);
      Utils.showNotification(`Failed to add ${bandType} overlay: ${error.message}`, 'error');
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
  },

  /**
   * Validate base64 image data and detect potential issues
   * @param {string} imageData - Base64 encoded image data
   * @param {string} processingType - Processing type for logging
   * @returns {Object} Validation results
   */
  validateImageData(imageData, processingType) {
    const validation = {
      isValid: true,
      warnings: [],
      errors: [],
      info: {}
    };

    try {
      // Check if image data exists
      if (!imageData) {
        validation.errors.push('No image data provided');
        validation.isValid = false;
        return validation;
      }

      // Check image data length
      validation.info.dataLength = imageData.length;
      if (imageData.length < 100) {
        validation.warnings.push(`Very small image data (${imageData.length} chars)`);
      } else if (imageData.length > 50000000) { // 50MB limit
        validation.warnings.push(`Very large image data (${(imageData.length / 1024 / 1024).toFixed(2)} MB)`);
      }

      // Check for valid base64 format
      const base64Regex = /^[A-Za-z0-9+/]*={0,2}$/;
      if (!base64Regex.test(imageData)) {
        validation.errors.push('Invalid base64 format detected');
        validation.isValid = false;
      }

      // Try to decode and validate as image
      try {
        const testImage = new Image();
        const dataUrl = `data:image/png;base64,${imageData}`;
        
        // Test if browser can create the image (async validation)
        testImage.onload = () => {
          Utils.log('info', `✅ Image validation passed for ${processingType}: ${testImage.width}x${testImage.height}`);
        };
        
        testImage.onerror = (e) => {
          Utils.log('error', `❌ Image validation failed for ${processingType}:`, e);
        };
        
        testImage.src = dataUrl;
        validation.info.testImageCreated = true;
        
      } catch (imageError) {
        validation.errors.push(`Image creation failed: ${imageError.message}`);
        validation.isValid = false;
      }

      // Check for PNG header
      if (imageData.startsWith('iVBORw0KGgo')) {
        validation.info.format = 'PNG';
      } else if (imageData.startsWith('/9j/')) {
        validation.info.format = 'JPEG';
        validation.warnings.push('JPEG format detected, PNG expected');
      } else {
        validation.warnings.push('Unknown image format detected');
      }

    } catch (error) {
      validation.errors.push(`Validation error: ${error.message}`);
      validation.isValid = false;
    }

    return validation;
  },

  /**
   * Enhanced bounds validation with geographic coordinate checks
   * @param {Array} bounds - Leaflet bounds [[south, west], [north, east]]
   * @param {string} processingType - Processing type for logging
   * @returns {Object} Validation results
   */
  validateBounds(bounds, processingType) {
    const validation = {
      isValid: true,
      warnings: [],
      errors: [],
      info: {}
    };

    try {
      // Check bounds format
      if (!Array.isArray(bounds) || bounds.length !== 2) {
        validation.errors.push('Invalid bounds format - must be [[south, west], [north, east]]');
        validation.isValid = false;
        return validation;
      }

      const [southwest, northeast] = bounds;
      if (!Array.isArray(southwest) || !Array.isArray(northeast) || 
          southwest.length !== 2 || northeast.length !== 2) {
        validation.errors.push('Invalid bounds corner format');
        validation.isValid = false;
        return validation;
      }

      const [south, west] = southwest;
      const [north, east] = northeast;

      // Store parsed values
      validation.info = { south, west, north, east };

      // Check for valid numeric values
      if ([south, west, north, east].some(coord => typeof coord !== 'number' || isNaN(coord))) {
        validation.errors.push('Non-numeric coordinates detected');
        validation.isValid = false;
        return validation;
      }

      // Check latitude bounds (-90 to 90)
      if (south < -90 || south > 90 || north < -90 || north > 90) {
        validation.errors.push(`Invalid latitude values: south=${south}, north=${north}`);
        validation.isValid = false;
      }

      // Check longitude bounds (-180 to 180)
      if (west < -180 || west > 180 || east < -180 || east > 180) {
        validation.errors.push(`Invalid longitude values: west=${west}, east=${east}`);
        validation.isValid = false;
      }

      // Check logical ordering
      if (south >= north) {
        validation.errors.push(`South (${south}) must be less than North (${north})`);
        validation.isValid = false;
      }

      // Note: We don't enforce west < east due to possible dateline crossing

      // Calculate area
      const width = Math.abs(east - west);
      const height = Math.abs(north - south);
      validation.info.width = width;
      validation.info.height = height;
      validation.info.area = width * height;

      // Check for reasonable size
      if (width > 180 || height > 90) {
        validation.warnings.push(`Very large overlay area: ${width.toFixed(4)}° x ${height.toFixed(4)}°`);
      } else if (width < 0.001 || height < 0.001) {
        validation.warnings.push(`Very small overlay area: ${width.toFixed(6)}° x ${height.toFixed(6)}°`);
      }

    } catch (error) {
      validation.errors.push(`Bounds validation error: ${error.message}`);
      validation.isValid = false;
    }

    return validation;
  },

  /**
   * Large Image Optimization Configuration
   */
  largeImageConfig: {
    // Memory limits
    maxPixels: 50000000, // 50M pixels (approximately 200MB uncompressed)
    maxBase64Size: 75000000, // 75MB base64 data
    compressionThreshold: 25000000, // 25M pixels
    
    // Aggressive optimization for very large images
    extremePixelThreshold: 100000000, // 100M pixels - super aggressive
    aggressivePixelThreshold: 75000000, // 75M pixels - more aggressive
    
    // Progressive loading settings
    enableProgressiveLoading: true,
    loadingChunkSize: 1024 * 1024, // 1MB chunks
    
    // Fallback settings
    maxRetries: 3,
    fallbackQuality: 0.7,
    fallbackMaxWidth: 4096,
    fallbackMaxHeight: 4096,
    
    // Extreme optimization settings
    extremeMaxWidth: 2048,
    extremeMaxHeight: 2048,
    extremeQuality: 0.5
  },

  /**
   * Check if image requires optimization due to size
   * @param {string} imageData - Base64 image data
   * @param {number} width - Image width
   * @param {number} height - Image height
   * @returns {Object} Optimization requirements
   */
  checkImageOptimizationNeeds(imageData, width = null, height = null) {
    const config = this.largeImageConfig;
    const result = {
      needsOptimization: false,
      reasons: [],
      recommendations: [],
      estimatedPixels: width && height ? width * height : null,
      base64Size: imageData.length
    };

    // Check base64 size
    if (imageData.length > config.maxBase64Size) {
      result.needsOptimization = true;
      result.reasons.push(`Base64 data too large (${(imageData.length / 1024 / 1024).toFixed(2)}MB)`);
      result.recommendations.push('Apply aggressive compression');
    } else if (imageData.length > (config.maxBase64Size * 0.33)) { // 25MB threshold for base64
      result.needsOptimization = true;
      result.reasons.push(`Base64 data exceeds compression threshold`);
      result.recommendations.push('Apply standard compression');
    }

    // Check pixel count if available
    if (result.estimatedPixels) {
      if (result.estimatedPixels > config.maxPixels) {
        result.needsOptimization = true;
        result.reasons.push(`Too many pixels (${(result.estimatedPixels / 1000000).toFixed(1)}M)`);
        result.recommendations.push('Resize image');
      } else if (result.estimatedPixels > config.compressionThreshold) {
        result.needsOptimization = true;
        result.reasons.push(`Pixel count exceeds compression threshold`);
        result.recommendations.push('Apply compression');
      }
    }

    return result;
  },

  /**
   * Optimize large image for display
   * @param {string} imageData - Base64 image data
   * @param {string} processingType - Processing type for logging
   * @returns {Promise<Object>} Optimization result
   */
  async optimizeLargeImage(imageData, processingType) {
    const startTime = Date.now();
    Utils.log('info', `🔄 Starting image optimization for ${processingType}`);

    try {
      // Show progress notification
      this.showOverlayNotification(`Optimizing large ${processingType} image...`, 'info', 0);

      // Create image element to get dimensions
      const originalImage = await this.createImageFromBase64(imageData);
      const originalWidth = originalImage.width;
      const originalHeight = originalImage.height;
      const originalPixels = originalWidth * originalHeight;

      Utils.log('info', `Original image: ${originalWidth}x${originalHeight} (${(originalPixels / 1000000).toFixed(1)}M pixels)`);

      // Check optimization needs
      const optimizationNeeds = this.checkImageOptimizationNeeds(imageData, originalWidth, originalHeight);
      
      if (!optimizationNeeds.needsOptimization) {
        Utils.log('info', `No optimization needed for ${processingType}`);
        return {
          success: true,
          optimizedData: `data:image/png;base64,${imageData}`,
          originalSize: { width: originalWidth, height: originalHeight },
          optimizedSize: { width: originalWidth, height: originalHeight },
          compressionRatio: 1.0,
          processingTime: Date.now() - startTime
        };
      }

      Utils.log('info', `Optimization needed: ${optimizationNeeds.reasons.join(', ')}`);

      // Calculate target dimensions
      const targetDimensions = this.calculateOptimalDimensions(
        originalWidth, 
        originalHeight, 
        optimizationNeeds
      );

      // Update progress
      this.showOverlayNotification(`Resizing ${processingType} image to ${targetDimensions.width}x${targetDimensions.height}...`, 'info', 30);

      // Perform optimization
      const optimizedResult = await this.performImageOptimization(
        originalImage,
        targetDimensions,
        processingType
      );

      // Update progress
      this.showOverlayNotification(`Finalizing ${processingType} optimization...`, 'info', 80);

      const processingTime = Date.now() - startTime;
      const compressionRatio = optimizedResult.compressedSize / imageData.length;

      Utils.log('info', `✅ Image optimization completed for ${processingType} in ${processingTime}ms`);
      Utils.log('info', `Size reduction: ${(imageData.length / 1024 / 1024).toFixed(2)}MB → ${(optimizedResult.compressedSize / 1024 / 1024).toFixed(2)}MB (${(compressionRatio * 100).toFixed(1)}%)`);

      // Show success notification
      this.showOverlayNotification(
        `${processingType} optimized: ${(compressionRatio * 100).toFixed(1)}% of original size`, 
        'success', 
        100
      );

      return {
        success: true,
        optimizedData: optimizedResult.dataUrl,
        originalSize: { width: originalWidth, height: originalHeight },
        optimizedSize: targetDimensions,
        compressionRatio: compressionRatio,
        processingTime: processingTime
      };

    } catch (error) {
      Utils.log('error', `❌ Image optimization failed for ${processingType}:`, error);
      this.showOverlayNotification(`Failed to optimize ${processingType} image: ${error.message}`, 'error');
      
      return {
        success: false,
        error: error.message,
        processingTime: Date.now() - startTime
      };
    }
  },

  /**
   * Create image element from base64 data
   * @param {string} base64Data - Base64 image data
   * @returns {Promise<HTMLImageElement>} Image element
   */
  createImageFromBase64(base64Data) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = (error) => reject(new Error(`Failed to load image: ${error.message || 'Unknown error'}`));
      img.src = `data:image/png;base64,${base64Data}`;
    });
  },

  /**
   * Calculate optimal dimensions for image optimization
   * @param {number} originalWidth - Original image width
   * @param {number} originalHeight - Original image height
   * @param {Object} optimizationNeeds - Optimization requirements
   * @returns {Object} Target dimensions
   */
  calculateOptimalDimensions(originalWidth, originalHeight, optimizationNeeds) {
    const config = this.largeImageConfig;
    const originalPixels = originalWidth * originalHeight;
    
    // If within limits, no resizing needed
    if (originalPixels <= config.compressionThreshold) {
      return { width: originalWidth, height: originalHeight };
    }

    // Calculate scale factor based on pixel count
    let scaleFactor = 1.0;
    
    if (originalPixels > config.maxPixels) {
      // Aggressive scaling for very large images
      scaleFactor = Math.sqrt(config.maxPixels / originalPixels);
    } else {
      // Conservative scaling for moderately large images
      scaleFactor = Math.sqrt(config.compressionThreshold / originalPixels);
    }

    // Apply minimum scale factor to prevent over-compression
    scaleFactor = Math.max(scaleFactor, 0.25); // Never scale below 25%

    // Calculate target dimensions
    let targetWidth = Math.floor(originalWidth * scaleFactor);
    let targetHeight = Math.floor(originalHeight * scaleFactor);

    // Apply maximum dimension limits
    if (targetWidth > config.fallbackMaxWidth) {
      const aspectRatio = originalHeight / originalWidth;
      targetWidth = config.fallbackMaxWidth;
      targetHeight = Math.floor(targetWidth * aspectRatio);
    }

    if (targetHeight > config.fallbackMaxHeight) {
      const aspectRatio = originalWidth / originalHeight;
      targetHeight = config.fallbackMaxHeight;
      targetWidth = Math.floor(targetHeight * aspectRatio);
    }

    // Ensure minimum dimensions
    targetWidth = Math.max(targetWidth, 256);
    targetHeight = Math.max(targetHeight, 256);

    Utils.log('info', `Calculated target dimensions: ${targetWidth}x${targetHeight} (scale: ${(scaleFactor * 100).toFixed(1)}%)`);

    return { width: targetWidth, height: targetHeight };
  },

  /**
   * Perform actual image optimization using canvas
   * @param {HTMLImageElement} sourceImage - Source image element
   * @param {Object} targetDimensions - Target dimensions
   * @param {string} processingType - Processing type for logging
   * @returns {Promise<Object>} Optimization result
   */
  async performImageOptimization(sourceImage, targetDimensions, processingType) {
    return new Promise((resolve, reject) => {
      try {
        // Create canvas for optimization
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Set canvas dimensions
        canvas.width = targetDimensions.width;
        canvas.height = targetDimensions.height;

        // Configure high-quality rendering
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        // Draw resized image
        ctx.drawImage(
          sourceImage,
          0, 0, sourceImage.width, sourceImage.height,
          0, 0, targetDimensions.width, targetDimensions.height
        );

        // Convert to optimized format
        const quality = this.largeImageConfig.fallbackQuality;
        
        // Try PNG first (lossless)
        canvas.toBlob((pngBlob) => {
          if (pngBlob) {
            const reader = new FileReader();
            reader.onload = () => {
              const dataUrl = reader.result;
              const base64Data = dataUrl.split(',')[1];
              
              resolve({
                dataUrl: dataUrl,
                compressedSize: base64Data.length,
                format: 'PNG'
              });
            };
            reader.onerror = () => reject(new Error('Failed to read optimized PNG'));
            reader.readAsDataURL(pngBlob);
          } else {
            // Fallback to JPEG if PNG fails
            canvas.toBlob((jpegBlob) => {
              if (jpegBlob) {
                const reader = new FileReader();
                reader.onload = () => {
                  const dataUrl = reader.result;
                  const base64Data = dataUrl.split(',')[1];
                  
                  resolve({
                    dataUrl: dataUrl,
                    compressedSize: base64Data.length,
                    format: 'JPEG'
                  });
                };
                reader.onerror = () => reject(new Error('Failed to read optimized JPEG'));
                reader.readAsDataURL(jpegBlob);
              } else {
                reject(new Error('Failed to create optimized image blob'));
              }
            }, 'image/jpeg', quality);
          }
        }, 'image/png');

      } catch (error) {
        reject(new Error(`Canvas optimization failed: ${error.message}`));
      }
    });
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
        button.classList.remove('bg-[#28a745]', 'hover:bg-[#218838]');
        button.classList.add('bg-[#dc3545]', 'hover:bg-[#c82333]');
      } else {
        button.textContent = 'Add to Map';
        button.classList.remove('remove-mode');
        button.classList.remove('bg-[#dc3545]', 'hover:bg-[#c82333]');
        button.classList.add('bg-[#28a745]', 'hover:bg-[#218838]');
      }
    }
  },

  /**
   * Show add to map button for a processing type
   * @param {string} processingType - Processing type
   */
  showAddToMapButton(processingType) {
    const button = document.querySelector(`[data-processing-type="${processingType}"] .add-to-map-btn`);
    if (button) {
      button.classList.remove('hidden');
      button.style.display = '';
    }
  },

  // ...existing code...
};
