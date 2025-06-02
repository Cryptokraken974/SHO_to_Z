/**
 * Processing operations for LAZ files
 */

window.ProcessingManager = {
  activeProcesses: new Set(),

  /**
   * Send processing request to server
   * @param {string} processingType - Type of processing (dtm, hillshade, etc.)
   * @param {Object} options - Additional processing options
   */
  async sendProcess(processingType, options = {}) {
    // Check for region-based processing first, then fall back to LAZ file processing
    const selectedRegion = FileManager.getSelectedRegion();
    const selectedFile = typeof FileManager.getSelectedFile === 'function' ? FileManager.getSelectedFile() : null;
    
    if (!selectedRegion && !selectedFile) {
      Utils.showNotification('Please select a region or LAZ file first', 'warning');
      return false;
    }

    if (this.activeProcesses.has(processingType)) {
      Utils.showNotification(`${processingType} processing is already in progress`, 'info');
      return false;
    }

    try {
      // Mark process as active
      this.activeProcesses.add(processingType);
      this.updateProcessingUI(processingType, 'processing');

      // Prepare request data based on whether we have a region or individual file
      let requestData;
      
      if (selectedRegion) {
        // Region-based processing: find the LAZ file(s) within the region
        // The backend will automatically find LAZ files in input/{region}/lidar/ directory
        requestData = {
          region_name: selectedRegion,
          processing_type: processingType,
          ...options
        };
        Utils.log('info', `Starting ${processingType} processing for region: ${selectedRegion}`, requestData);
      } else {
        // Individual LAZ file processing (legacy support)
        requestData = {
          input_file: selectedFile,
          ...options
        };
        Utils.log('info', `Starting ${processingType} processing for file: ${selectedFile}`, requestData);
      }

      // Send processing request
      const response = await fetch(`/api/${processingType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (data.success) {
        this.handleProcessingSuccess(processingType, data);
      } else {
        this.handleProcessingError(processingType, data.error || 'Unknown error');
      }

      return data.success;

    } catch (error) {
      Utils.log('error', `${processingType} processing failed`, error);
      this.handleProcessingError(processingType, error.message);
      return false;
    } finally {
      // Remove from active processes
      this.activeProcesses.delete(processingType);
    }
  },

  /**
   * Handle successful processing completion
   * @param {string} processingType - Type of processing
   * @param {Object} data - Response data from server
   */
  handleProcessingSuccess(processingType, data) {
    Utils.log('info', `${processingType} processing completed successfully`);
    
    // Update UI
    this.updateProcessingUI(processingType, 'success');
    
    // Show success notification
    Utils.showNotification(`${processingType} processing completed successfully`, 'success');
    
    // Display PNG image in gallery cell automatically
    this.displayProcessingResultImage(processingType);
    
    // Also refresh Sentinel-2 images for the region if we're doing region-based processing
    const selectedRegion = FileManager.getSelectedRegion();
    if (selectedRegion) {
      Utils.log('info', `Refreshing Sentinel-2 images for region: ${selectedRegion}`);
      // Use setTimeout to allow the raster image to display first
      setTimeout(() => {
        UIManager.displaySentinel2ImagesForRegion(selectedRegion);
      }, 100);
    }
    
    // Show Add to Map button
    OverlayManager.showAddToMapButton(processingType);
    
    // If auto-add is enabled, add overlay to map
    if (data.auto_add_to_map) {
      setTimeout(() => {
        OverlayManager.addProcessingOverlay(processingType);
      }, 500);
    }
  },

  /**
   * Display generated PNG image in the corresponding gallery cell
   * @param {string} processingType - Type of processing (dtm, hillshade, slope, etc.)
   */
  async displayProcessingResultImage(processingType) {
    // Check if we're processing a region or a LAZ file
    const selectedRegion = FileManager.getSelectedRegion();
    const selectedFile = typeof FileManager.getSelectedFile === 'function' ? FileManager.getSelectedFile() : null;
    
    if (!selectedRegion && !selectedFile) {
      Utils.log('warn', 'No selected region or file for image display');
      return;
    }

    try {
      let response;
      let displayIdentifier;

      if (selectedRegion) {
        // Region-based processing: use the new raster API endpoint
        displayIdentifier = selectedRegion;
        response = await fetch(`/api/overlay/raster/${selectedRegion}/${processingType}`);
      } else {
        // LAZ file-based processing: use the original overlay API
        displayIdentifier = selectedFile.replace(/\.[^/.]+$/, "");
        response = await fetch(`/api/overlay/${processingType}/${displayIdentifier}`);
      }

      
      if (!response.ok) {
        Utils.log('warn', `No PNG data available for ${processingType}: ${response.status}`);
        return;
      }

      const overlayData = await response.json();
      
      if (!overlayData || !overlayData.image_data) {
        Utils.log('warn', `No image data in overlay response for ${processingType}`);
        return;
      }

      // Find the corresponding gallery cell
      const cellId = `cell-${processingType}`;
      const cell = $(`#${cellId}`);
      
      if (!cell.length) {
        Utils.log('warn', `Gallery cell not found: ${cellId}`);
        return;
      }

      // Create base64 data URL for the image
      const imageDataUrl = `data:image/png;base64,${overlayData.image_data}`;
      
      // Get the processing type display name
      const displayName = this.getProcessingDisplayName(processingType);
      
      // Update the cell content to show the image
      const cellContent = cell.find('.flex-1');
      cellContent.html(`
        <div class="relative w-full h-full">
          <img src="${imageDataUrl}" 
               alt="${displayName}" 
               class="processing-result-image cursor-pointer"
               title="Click to view larger image">
          <div class="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
            ${displayName}
          </div>
          <div class="absolute top-2 right-2 bg-green-600 bg-opacity-75 text-white text-xs px-2 py-1 rounded">
            ✓ Ready
          </div>
        </div>
      `);

      // Add click handler to show larger image
      cellContent.find('img').on('click', () => {
        UIManager.showImageModal(imageDataUrl, `${displayName} - ${displayIdentifier}`);
      });

      // Show the "Add to Map" button for this processing type
      const addToMapBtn = cell.find('.add-to-map-btn');
      if (addToMapBtn.length) {
        addToMapBtn.removeClass('hidden').show();
        Utils.log('info', `Showing Add to Map button for ${processingType}`);
      }

      Utils.log('info', `Successfully displayed ${processingType} image in gallery cell for ${selectedRegion ? 'region' : 'file'}: ${displayIdentifier}`);

    } catch (error) {
      Utils.log('error', `Error displaying ${processingType} image:`, error);
      // Don't show error notification as this is a nice-to-have feature
    }
  },

  /**
   * Get display name for processing type
   * @param {string} processingType - Processing type
   * @returns {string} Display name
   */
  getProcessingDisplayName(processingType) {
    const displayNames = {
      'laz_to_dem': 'DEM',
      'dtm': 'DTM',
      'dsm': 'DSM',
      'chm': 'CHM',
      'hillshade': 'Hillshade',
      'hillshade_315_45_08': 'Hillshade 315°',
      'hillshade_225_45_08': 'Hillshade 225°',
      'slope': 'Slope',
      'aspect': 'Aspect',
      'color_relief': 'Color Relief',
      'tri': 'TRI',
      'tpi': 'TPI',
      'roughness': 'Roughness'
    };
    
    return displayNames[processingType] || processingType.charAt(0).toUpperCase() + processingType.slice(1);
  },

  /**
   * Handle processing error
   * @param {string} processingType - Type of processing
   * @param {string} error - Error message
   */
  handleProcessingError(processingType, error) {
    Utils.log('error', `${processingType} processing failed: ${error}`);
    
    // Update UI
    this.updateProcessingUI(processingType, 'error');
    
    // Show error notification
    Utils.showNotification(`${processingType} processing failed: ${error}`, 'error');
  },

  /**
   * Update processing UI state
   * @param {string} processingType - Type of processing
   * @param {string} state - UI state (processing, success, error, idle)
   */
  updateProcessingUI(processingType, state) {
    const button = $(`#process-${processingType.toLowerCase()}`);
    const progressIndicator = $(`#progress-${processingType.toLowerCase()}`);
    const statusIcon = $(`#status-${processingType.toLowerCase()}`);

    // Reset classes
    button.removeClass('processing success error');
    
    switch (state) {
      case 'processing':
        button.addClass('processing')
              .prop('disabled', true)
              .text('Processing...');
        
        if (progressIndicator.length) {
          progressIndicator.show().addClass('spinning');
        }
        
        if (statusIcon.length) {
          statusIcon.removeClass('success error').addClass('processing');
        }
        break;

      case 'success':
        button.addClass('success')
              .prop('disabled', false)
              .text(`Process ${processingType}`);
        
        if (progressIndicator.length) {
          progressIndicator.hide().removeClass('spinning');
        }
        
        if (statusIcon.length) {
          statusIcon.removeClass('processing error').addClass('success');
        }
        break;

      case 'error':
        button.addClass('error')
              .prop('disabled', false)
              .text(`Retry ${processingType}`);
        
        if (progressIndicator.length) {
          progressIndicator.hide().removeClass('spinning');
        }
        
        if (statusIcon.length) {
          statusIcon.removeClass('processing success').addClass('error');
        }
        break;

      case 'idle':
      default:
        button.prop('disabled', false)
              .text(`Process ${processingType}`);
        
        if (progressIndicator.length) {
          progressIndicator.hide().removeClass('spinning');
        }
        
        if (statusIcon.length) {
          statusIcon.removeClass('processing success error');
        }
        break;
    }
  },

  /**
   * Process DTM (Digital Terrain Model)
   * @param {Object} options - DTM processing options
   */
  async processDTM(options = {}) {
    const defaultOptions = {
      resolution: 1.0,
      output_type: 'min'
    };
    
    return await this.sendProcess('dtm', { ...defaultOptions, ...options });
  },

  /**
   * Process Hillshade
   * @param {Object} options - Hillshade processing options
   */
  async processHillshade(options = {}) {
    const defaultOptions = {
      azimuth: 315.0,
      altitude: 45.0,
      z_factor: 1.0
    };
    
    return await this.sendProcess('hillshade', { ...defaultOptions, ...options });
  },

  /**
   * Process DSM (Digital Surface Model)
   * @param {Object} options - DSM processing options
   */
  async processDSM(options = {}) {
    const defaultOptions = {
      resolution: 1.0,
      output_type: 'max'
    };
    
    return await this.sendProcess('dsm', { ...defaultOptions, ...options });
  },

  /**
   * Process CHM (Canopy Height Model)
   * @param {Object} options - CHM processing options
   */
  async processCHM(options = {}) {
    const defaultOptions = {
      resolution: 1.0
    };
    
    return await this.sendProcess('chm', { ...defaultOptions, ...options });
  },

  /**
   * Process Slope
   * @param {Object} options - Slope processing options
   */
  async processSlope(options = {}) {
    const defaultOptions = {
      units: 'degrees'
    };
    
    return await this.sendProcess('slope', { ...defaultOptions, ...options });
  },

  /**
   * Process Aspect
   * @param {Object} options - Aspect processing options
   */
  async processAspect(options = {}) {
    return await this.sendProcess('aspect', options);
  },

  /**
   * Process Roughness
   * @param {Object} options - Roughness processing options
   */
  async processRoughness(options = {}) {
    return await this.sendProcess('roughness', options);
  },

  /**
   * Process TRI (Terrain Ruggedness Index)
   * @param {Object} options - TRI processing options
   */
  async processTRI(options = {}) {
    return await this.sendProcess('tri', options);
  },

  /**
   * Process TPI (Topographic Position Index)
   * @param {Object} options - TPI processing options
   */
  async processTPI(options = {}) {
    return await this.sendProcess('tpi', options);
  },

  /**
   * Process Color Relief
   * @param {Object} options - Color Relief processing options
   */
  async processColorRelief(options = {}) {
    const defaultOptions = {
      color_scheme: 'elevation'
    };
    
    return await this.sendProcess('color_relief', { ...defaultOptions, ...options });
  },

  /**
   * Cancel processing operation
   * @param {string} processingType - Type of processing to cancel
   */
  async cancelProcessing(processingType) {
    if (!this.activeProcesses.has(processingType)) {
      return false;
    }

    try {
      // Note: No backend cancel endpoint available, so we just update the UI
      this.activeProcesses.delete(processingType);
      this.updateProcessingUI(processingType, 'idle');
      Utils.showNotification(`${processingType} processing cancelled locally`, 'info');
      return true;
      
    } catch (error) {
      Utils.log('error', `Failed to cancel ${processingType} processing`, error);
    }
    
    return false;
  },

  /**
   * Get processing status
   * @param {string} processingType - Type of processing
   * @returns {string} Current processing status
   */
  getProcessingStatus(processingType) {
    return this.activeProcesses.has(processingType) ? 'processing' : 'idle';
  },

  /**
   * Check if any processing is active
   * @returns {boolean} True if any processing is active
   */
  hasActiveProcesses() {
    return this.activeProcesses.size > 0;
  },

  /**
   * Get list of active processes
   * @returns {Array} Array of active processing types
   */
  getActiveProcesses() {
    return Array.from(this.activeProcesses);
  }
};
