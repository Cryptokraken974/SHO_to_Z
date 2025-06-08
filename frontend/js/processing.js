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
    
    // DEBUG: Log current state
    Utils.log('debug', `sendProcess DEBUG - processingType: ${processingType}`, {
      selectedRegion,
      processingRegion,
      selectedFile,
      options
    });
    
    if (!selectedRegion && !selectedFile) {
      Utils.showNotification('Please select a region or LAZ file first', 'warning');
      Utils.log('error', 'sendProcess failed: No region or file selected');
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

      // Send processing request with API client using service-oriented methods
      const processingOptions = {};
      
      // Convert FormData to options object
      for (const [key, value] of formData.entries()) {
        processingOptions[key] = value;
      }

      // DEBUG: Log final processing options that will be sent to API
      Utils.log('debug', `sendProcess API call parameters:`, {
        processingType,
        processingOptions,
        formDataEntries: Array.from(formData.entries())
      });

      // Use specific service methods based on processing type
      let data;
      switch (processingType) {
        case 'dtm':
          data = await processing().generateDTM(processingOptions);
          break;
        case 'dsm':
          data = await processing().generateDSM(processingOptions);
          break;
        case 'chm':
          data = await processing().generateCHM(processingOptions);
          break;
        case 'hillshade':
          data = await processing().generateHillshade(processingOptions);
          break;
        case 'slope':
          data = await processing().generateSlope(processingOptions);
          break;
        case 'aspect':
          data = await processing().generateAspect(processingOptions);
          break;
        case 'color-relief':
          data = await processing().generateColorRelief(processingOptions);
          break;
        case 'tpi':
          data = await processing().generateTPI(processingOptions);
          break;
        case 'roughness':
          data = await processing().generateRoughness(processingOptions);
          break;
        default:
          // Fallback to generic method for unknown processing types
          data = await processing().processRegion(processingType, processingOptions);
          break;
      }

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
        overlayData = await overlays().getRasterOverlayData(selectedRegion, processingType);
      } else {
        // LAZ file-based processing: use the file-based overlay API
        displayIdentifier = selectedFile.replace(/\.[^/.]+$/, "");
        overlayData = await overlays().getOverlayData(processingType, displayIdentifier);
      }
      
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

      // Add or show the "Add to Map" button for this processing type
      let addToMapBtn = cell.find('.add-to-map-btn');
      if (!addToMapBtn.length) {
        // Create the button if it doesn't exist
        const regionName = selectedRegion || displayIdentifier;
        cell.append(`
          <button class="add-to-map-btn bg-[#28a745] hover:bg-[#218838] text-white px-3 py-1 rounded-b-lg text-sm font-medium transition-colors mt-1" 
                  data-target="${processingType}"
                  data-region-name="${regionName}">
            Add to Map
          </button>
        `);
        addToMapBtn = cell.find('.add-to-map-btn');
        Utils.log('info', `Created Add to Map button for ${processingType}`);
      } else {
        addToMapBtn.removeClass('hidden').show();
        Utils.log('info', `Showing existing Add to Map button for ${processingType}`);
      }

      // Add click handler for the button if it doesn't already have one
      if (addToMapBtn.length && !addToMapBtn.data('events')) {
        addToMapBtn.on('click', function(e) {
          e.preventDefault();
          const $button = $(this);
          const processingType = $button.data('target');
          
          if (!processingType) {
            Utils.log('warn', 'No processing type found in data-target attribute');
            return;
          }
          
          Utils.log('info', `Processing result: Add to Map clicked for ${processingType}`);
          
          // Handle the add to map functionality
          UIManager.handleProcessingResultsAddToMap(processingType, $button);
        });
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
    // Check if a region is selected before proceeding
    const selectedRegion = FileManager.getSelectedRegion();
    const selectedFile = typeof FileManager.getSelectedFile === 'function' ? FileManager.getSelectedFile() : null;
    
    if (!selectedRegion && !selectedFile) {
      Utils.showNotification('Please select a region or LAZ file before processing DTM', 'warning');
      console.log('❌ DTM processing attempted without region selection');
      return false;
    }
    
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
    // Check if a region is selected before proceeding
    const selectedRegion = FileManager.getSelectedRegion();
    const selectedFile = typeof FileManager.getSelectedFile === 'function' ? FileManager.getSelectedFile() : null;
    
    if (!selectedRegion && !selectedFile) {
      Utils.showNotification('Please select a region or LAZ file before processing Hillshade', 'warning');
      console.log('❌ Hillshade processing attempted without region selection');
      return false;
    }
    
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
    // Check if a region is selected before proceeding
    const selectedRegion = FileManager.getSelectedRegion();
    const selectedFile = typeof FileManager.getSelectedFile === 'function' ? FileManager.getSelectedFile() : null;
    
    if (!selectedRegion && !selectedFile) {
      Utils.showNotification('Please select a region or LAZ file before processing DSM', 'warning');
      console.log('❌ DSM processing attempted without region selection');
      return false;
    }
    
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
      // Try to cancel processing on the backend using the new service method
      const selectedRegion = FileManager.getSelectedRegion();
      if (selectedRegion) {
        try {
          await processing().cancelProcessing(selectedRegion);
          Utils.log('info', `Backend processing cancelled for region: ${selectedRegion}`);
        } catch (error) {
          Utils.log('warn', `Backend cancellation failed, proceeding with local cancellation: ${error.message}`);
        }
      }
      
      // Always update local state
      this.activeProcesses.delete(processingType);
      this.updateProcessingUI(processingType, 'idle');
      Utils.showNotification(`${processingType} processing cancelled`, 'info');
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

    // Define processing queue (DTM first, then DSM, then other terrain analysis, then CHM last)
    const processingQueue = [
      { type: 'dtm', name: 'DTM', icon: '🏔️' },
      { type: 'dsm', name: 'DSM', icon: '🏗️' },
      { type: 'hillshade', name: 'Hillshade', icon: '🌄' },
      { type: 'slope', name: 'Slope', icon: '📐' },
      { type: 'aspect', name: 'Aspect', icon: '🧭' },
      { type: 'tpi', name: 'TPI', icon: '📈' },
      { type: 'roughness', name: 'Roughness', icon: '🪨' },
      { type: 'chm', name: 'CHM', icon: '🌳' }
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
        
        // 🎯 NOW refresh overlay display after successful raster generation
        setTimeout(() => {
          const selectedRegion = FileManager.getSelectedRegion();
          const processingRegion = FileManager.getProcessingRegion();
          
          if (processingRegion || selectedRegion) {
            Utils.log('info', '🔄 Refreshing LIDAR raster display after successful generation...');
            UIManager.displayLidarRasterForRegion(processingRegion || selectedRegion);
          }
        }, 2000); // 2 second delay to ensure files are ready
        
      } else if (successCount > 0) {
        Utils.showNotification(`${successCount} raster products completed, ${failedProcesses.length} failed`, 'warning');
        
        // Still refresh display for successful ones
        setTimeout(() => {
          const selectedRegion = FileManager.getSelectedRegion();
          const processingRegion = FileManager.getProcessingRegion();
          
          if (processingRegion || selectedRegion) {
            Utils.log('info', '🔄 Refreshing LIDAR raster display for successful generations...');
            UIManager.displayLidarRasterForRegion(processingRegion || selectedRegion);
          }
        }, 2000);
        
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

  // Service-Oriented Processing Methods
  
  /**
   * List available LAZ files using the service
   * @returns {Promise<Object>} List of LAZ files with metadata
   */
  async listLazFiles() {
    try {
      return await processing().listLazFiles();
    } catch (error) {
      Utils.log('error', 'Failed to list LAZ files', error);
      Utils.showNotification('Failed to retrieve LAZ files list', 'error');
      return { success: false, error: error.message };
    }
  },

  /**
   * Load a LAZ file using the service
   * @param {File} file - LAZ file to upload
   * @returns {Promise<Object>} Upload result
   */
  async loadLazFile(file) {
    try {
      Utils.showNotification('Uploading LAZ file...', 'info');
      const result = await processing().loadLazFile(file);
      
      if (result.success) {
        Utils.showNotification('LAZ file uploaded successfully', 'success');
      } else {
        Utils.showNotification('LAZ file upload failed', 'error');
      }
      
      return result;
    } catch (error) {
      Utils.log('error', 'Failed to load LAZ file', error);
      Utils.showNotification('Failed to upload LAZ file', 'error');
      return { success: false, error: error.message };
    }
  },

  /**
   * Get LAZ file information using the service
   * @param {string} filePath - Path to LAZ file
   * @returns {Promise<Object>} LAZ file information
   */
  async getLazInfo(filePath) {
    try {
      return await processing().getLazInfo(filePath);
    } catch (error) {
      Utils.log('error', 'Failed to get LAZ info', error);
      Utils.showNotification('Failed to retrieve LAZ file information', 'error');
      return { success: false, error: error.message };
    }
  },

  /**
   * Generate all raster products for a region using the service
   * @param {string} regionName - Region name
   * @param {number} batchSize - Batch size for processing
   * @returns {Promise<Object>} Batch generation result
   */
  async generateAllRastersForRegion(regionName, batchSize = 4) {
    try {
      Utils.showNotification(`Starting batch generation of all rasters for ${regionName}...`, 'info');
      const result = await processing().generateAllRasters(regionName, batchSize);
      
      if (result.success) {
        Utils.showNotification('Batch raster generation completed successfully', 'success');
        
        // Refresh the region display to show new rasters
        setTimeout(() => {
          UIManager.displayLidarRasterForRegion(regionName);
        }, 1000);
      } else {
        Utils.showNotification('Batch raster generation failed', 'error');
      }
      
      return result;
    } catch (error) {
      Utils.log('error', 'Failed to generate all rasters', error);
      Utils.showNotification('Batch raster generation failed', 'error');
      return { success: false, error: error.message };
    }
  },

  /**
   * Get processing status for a region using the service
   * @param {string} regionName - Region name
   * @returns {Promise<Object>} Processing status
   */
  async getProcessingStatusForRegion(regionName) {
    try {
      return await processing().getProcessingStatus(regionName);
    } catch (error) {
      Utils.log('error', 'Failed to get processing status', error);
      return { success: false, error: error.message };
    }
  },

  /**
   * Get processing history using the service
   * @returns {Promise<Object>} Processing history
   */
  async getProcessingHistory() {
    try {
      return await processing().getProcessingHistory();
    } catch (error) {
      Utils.log('error', 'Failed to get processing history', error);
      Utils.showNotification('Failed to retrieve processing history', 'error');
      return { success: false, error: error.message };
    }
  },

  /**
   * Delete processed files for a region using the service
   * @param {string} regionName - Region name
   * @param {string[]} fileTypes - Optional array of file types to delete
   * @returns {Promise<Object>} Deletion result
   */
  async deleteProcessedFiles(regionName, fileTypes = null) {
    try {
      const result = await processing().deleteProcessedFiles(regionName, fileTypes);
      
      if (result.success) {
        Utils.showNotification(`Processed files deleted for ${regionName}`, 'success');
      } else {
        Utils.showNotification('Failed to delete processed files', 'error');
      }
      
      return result;
    } catch (error) {
      Utils.log('error', 'Failed to delete processed files', error);
      Utils.showNotification('Failed to delete processed files', 'error');
      return { success: false, error: error.message };
    }
  },
};
