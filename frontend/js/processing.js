/**
 * Processing operations for LAZ files
 */

window.ProcessingManager = {
  activeProcesses: new Set(),
  // Global flag for cancellation
  isRasterProcessingCancelled: false,

  /**
   * Send processing request to server
   * @param {string} processingType - Type of processing (dtm, hillshade, etc.)
   * @param {Object} options - Additional processing options
   */
  async sendProcess(processingType, options = {}) {
    // Check for region-based processing first, then fall back to LAZ file processing
    const selectedRegion = FileManager.getSelectedRegion();
    const processingRegion = FileManager.getProcessingRegion(); // Get the actual region for API calls
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

      // Prepare form data based on whether we have a region or individual file
      const formData = new FormData();
      
      if (selectedRegion && processingRegion) {
        // Region-based processing: find the LAZ file(s) within the region
        // The backend will automatically find LAZ files in input/{processingRegion}/lidar/ directory
        formData.append('region_name', processingRegion); // Use processing region for LAZ file lookup
        formData.append('display_region_name', selectedRegion); // Pass the actual selected region for output folders
        formData.append('processing_type', processingType);
        
        // Add any additional options as form fields
        for (const [key, value] of Object.entries(options)) {
          formData.append(key, value);
        }
        
        Utils.log('info', `Starting ${processingType} processing for region: ${selectedRegion} (processing region: ${processingRegion})`, {region_name: processingRegion, display_region_name: selectedRegion, processing_type: processingType, ...options});
      } else {
        // Individual LAZ file processing (legacy support)
        formData.append('input_file', selectedFile);
        
        // Add any additional options as form fields
        for (const [key, value] of Object.entries(options)) {
          formData.append(key, value);
        }
        
        Utils.log('info', `Starting ${processingType} processing for file: ${selectedFile}`, {input_file: selectedFile, ...options});
      }

      // Send processing request with form data
      const response = await fetch(`/api/${processingType}`, {
        method: 'POST',
        body: formData  // No need for Content-Type header with FormData
      });

      if (!response.ok) {
        const errorData = await response.json();
        this.handleProcessingError(processingType, errorData.detail || `HTTP ${response.status}`);
        return false;
      }

      const data = await response.json();

      // Check for successful response - either has success=true OR has image data
      if (data.success || data.image) {
        this.handleProcessingSuccess(processingType, data);
        return true;  // Return true when the condition is met
      } else {
        this.handleProcessingError(processingType, data.error || 'Unknown error');
        return false;
      }

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
      'aspect': 'Aspect'
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
   * Cancel all raster processing
   */
  async cancelAllRasterProcessing() {
    this.isRasterProcessingCancelled = true;
    
    // Cancel any active individual processes
    this.activeProcesses.forEach(processType => {
      this.cancelProcessing(processType);
    });

    // Update UI
    this.hideRasterProcessingUI();
    Utils.showNotification('Raster processing cancelled', 'info');
    
    Utils.log('info', 'All raster processing cancelled by user');
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
  },

  /**
   * Process all rasters sequentially (DTM first, then all terrain analysis products)
   * This replaces the individual button approach with a single workflow
   */
  async processAllRasters() {
    // Check prerequisites
    const selectedRegion = FileManager.getSelectedRegion();
    const processingRegion = FileManager.getProcessingRegion();
    const selectedFile = typeof FileManager.getSelectedFile === 'function' ? FileManager.getSelectedFile() : null;
    
    if (!selectedRegion && !selectedFile) {
      Utils.showNotification('Please select a region or LAZ file first', 'warning');
      return false;
    }

    // Check if any processing is already active
    if (this.hasActiveProcesses()) {
      Utils.showNotification('Processing is already in progress. Please wait for completion.', 'info');
      return false;
    }

    // Reset cancellation flag
    this.isRasterProcessingCancelled = false;

    // Define processing queue (DTM first, then all others)
    const processingQueue = [
      { type: 'dtm', name: 'DTM', icon: '🏔️' },
      { type: 'hillshade', name: 'Hillshade', icon: '🌄' },
      { type: 'slope', name: 'Slope', icon: '📐' },
      { type: 'aspect', name: 'Aspect', icon: '🧭' },
      { type: 'tri', name: 'TRI', icon: '📊' },
      { type: 'tpi', name: 'TPI', icon: '📈' },
      { type: 'roughness', name: 'Roughness', icon: '🪨' }
    ];

    try {
      // Show progress UI
      this.showRasterProcessingUI(true);
      this.updateRasterProcessingQueue(processingQueue, -1); // Initialize queue display
      
      Utils.showNotification('Starting sequential raster generation...', 'info');
      
      let successCount = 0;
      let failedProcesses = [];

      // Process each item in the queue sequentially
      for (let i = 0; i < processingQueue.length; i++) {
        // Check for cancellation
        if (this.isRasterProcessingCancelled) {
          Utils.log('info', 'Processing cancelled by user');
          this.hideRasterProcessingUI();
          return false;
        }

        const process = processingQueue[i];
        
        try {
          // Update UI to show current processing step
          this.updateCurrentProcessingStep(process.name, i, processingQueue.length);
          this.updateRasterProcessingQueue(processingQueue, i);
          
          Utils.log('info', `Processing ${process.name} (${i + 1}/${processingQueue.length})`);
          
          // Execute the processing
          const success = await this.sendProcess(process.type);
          
          if (success) {
            successCount++;
            this.markQueueItemComplete(process.type, 'success');
            Utils.log('info', `${process.name} completed successfully`);
          } else {
            failedProcesses.push(process.name);
            this.markQueueItemComplete(process.type, 'error');
            Utils.log('warn', `${process.name} failed`);
          }
          
          // Small delay between processes to prevent overwhelming the backend
          if (i < processingQueue.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 500));
          }
          
          // Check for cancellation
          if (this.isRasterProcessingCancelled) {
            Utils.log('info', 'Raster processing cancelled by user');
            break;
          }
        } catch (error) {
          failedProcesses.push(process.name);
          this.markQueueItemComplete(process.type, 'error');
          Utils.log('error', `${process.name} processing failed:`, error);
        }
      }

      // Show completion summary
      this.showRasterProcessingComplete(successCount, failedProcesses);
      
      // Final notification
      if (failedProcesses.length === 0) {
        Utils.showNotification(`All ${successCount} raster products generated successfully!`, 'success');
      } else if (successCount > 0) {
        Utils.showNotification(`${successCount} raster products completed, ${failedProcesses.length} failed`, 'warning');
      } else {
        Utils.showNotification('Raster generation failed. Please check your input data.', 'error');
      }

      return successCount > 0;

    } catch (error) {
      Utils.log('error', 'Sequential raster processing failed:', error);
      Utils.showNotification('Sequential raster processing failed', 'error');
      this.hideRasterProcessingUI();
      return false;
    }
  },

  /**
   * Show/hide raster processing UI elements
   */
  showRasterProcessingUI(show) {
    const progressEl = document.getElementById('raster-generation-progress');
    const queueEl = document.getElementById('processing-queue');
    const statusEl = document.getElementById('raster-generation-status');
    const buttonEl = document.getElementById('generate-all-rasters-btn');
    const cancelButtonEl = document.getElementById('cancel-all-rasters-btn');

    if (show) {
      progressEl?.classList.remove('hidden');
      queueEl?.classList.remove('hidden');
      statusEl?.classList.remove('hidden');
      
      // Hide main button and show cancel button
      if (buttonEl) {
        buttonEl.classList.add('hidden');
      }
      if (cancelButtonEl) {
        cancelButtonEl.classList.remove('hidden');
      }
    } else {
      progressEl?.classList.add('hidden');
      queueEl?.classList.add('hidden');
      
      // Show main button and hide cancel button
      if (buttonEl) {
        buttonEl.classList.remove('hidden');
        buttonEl.disabled = false;
        buttonEl.textContent = '🏔️ Generate Rasters (DTM + All Terrain Analysis)';
        buttonEl.classList.remove('opacity-50', 'cursor-not-allowed');
      }
      if (cancelButtonEl) {
        cancelButtonEl.classList.add('hidden');
      }
    }
  },

  /**
   * Hide raster processing UI
   */
  hideRasterProcessingUI() {
    this.showRasterProcessingUI(false);
  },

  /**
   * Update current processing step display
   */
  updateCurrentProcessingStep(stepName, currentIndex, totalSteps) {
    const stepEl = document.getElementById('current-processing-step');
    const progressTextEl = document.getElementById('processing-progress-text');
    const progressBarEl = document.getElementById('processing-progress-bar');

    if (stepEl) {
      stepEl.textContent = `Processing ${stepName}...`;
    }

    const progressPercent = Math.round(((currentIndex + 1) / totalSteps) * 100);
    
    if (progressTextEl) {
      progressTextEl.textContent = `${progressPercent}%`;
    }

    if (progressBarEl) {
      progressBarEl.style.width = `${progressPercent}%`;
    }
  },

  /**
   * Update processing queue visual display
   */
  updateRasterProcessingQueue(queue, currentIndex) {
    queue.forEach((process, index) => {
      const queueItem = document.getElementById(`queue-${process.type.replace('_', '-')}`);
      if (queueItem) {
        // Reset classes
        queueItem.className = 'p-2 rounded bg-[#1a1a1a] text-center border-l-2';
        
        if (index < currentIndex) {
          // Completed
          queueItem.classList.add('border-green-500', 'bg-green-900', 'bg-opacity-20');
        } else if (index === currentIndex) {
          // Currently processing
          queueItem.classList.add('border-yellow-500', 'bg-yellow-900', 'bg-opacity-20', 'animate-pulse');
        } else {
          // Pending
          queueItem.classList.add('border-[#666]');
        }
      }
    });
  },

  /**
   * Mark a queue item as complete with status
   */
  markQueueItemComplete(processType, status) {
    const queueItem = document.getElementById(`queue-${processType.replace('_', '-')}`);
    if (queueItem) {
      queueItem.classList.remove('animate-pulse', 'border-yellow-500', 'bg-yellow-900');
      
      if (status === 'success') {
        queueItem.classList.add('border-green-500', 'bg-green-900', 'bg-opacity-20');
      } else if (status === 'error') {
        queueItem.classList.add('border-red-500', 'bg-red-900', 'bg-opacity-20');
      }
    }
  },

  /**
   * Show processing completion summary
   */
  showRasterProcessingComplete(successCount, failedProcesses) {
    const statusEl = document.getElementById('raster-status-text');
    if (statusEl) {
      if (failedProcesses.length === 0) {
        statusEl.textContent = `All ${successCount} raster products generated successfully`;
        statusEl.className = 'text-green-400';
      } else {
        statusEl.textContent = `${successCount} successful, ${failedProcesses.length} failed: ${failedProcesses.join(', ')}`;
        statusEl.className = 'text-yellow-400';
      }
    }

    // Hide progress UI after a delay
    setTimeout(() => {
      this.hideRasterProcessingUI();
    }, 5000);
  },
};
