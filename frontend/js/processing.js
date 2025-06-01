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
    const selectedFile = FileManager.getSelectedFile();
    if (!selectedFile) {
      Utils.showNotification('Please select a LAZ file first', 'warning');
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

      // Prepare request data
      const requestData = {
        input_file: selectedFile,
        ...options
      };

      Utils.log('info', `Starting ${processingType} processing`, requestData);

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
