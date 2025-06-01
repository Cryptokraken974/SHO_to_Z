/**
 * UI interactions and interface management
 */

window.UIManager = {
  /**
   * Initialize UI components
   */
  init() {
    this.initializeAccordions();
    this.initializeEventHandlers();
    this.initializeTooltips();
    this.initializeModals();
    
    Utils.log('info', 'UI Manager initialized');
  },

  /**
   * Initialize accordion functionality
   */
  initializeAccordions() {
    // Region selection accordion
    $('#region-accordion').on('click', () => {
      this.toggleAccordion('region');
    });

    // Test accordion
    $('#test-accordion').on('click', () => {
      this.toggleAccordion('test');
    });

    // Processing accordion
    $('#processing-accordion').on('click', () => {
      this.toggleAccordion('processing');
    });

    Utils.log('info', 'Accordions initialized');
  },

  /**
   * Toggle accordion state
   * @param {string} accordionType - Type of accordion (laz, test, processing)
   */
  toggleAccordion(accordionType) {
    const content = $(`#${accordionType}-content`);
    const arrow = $(`#${accordionType}-accordion .accordion-arrow`);

    if (content.hasClass('collapsed')) {
      content.removeClass('collapsed');
      arrow.css('transform', 'rotate(0deg)');
    } else {
      content.addClass('collapsed');
      arrow.css('transform', 'rotate(-90deg)');
    }

    Utils.log('info', `Toggled ${accordionType} accordion`);
  },

  /**
   * Initialize event handlers
   */
  initializeEventHandlers() {
    // Browse regions button
    $('#browse-regions-btn').on('click', () => {
      FileManager.loadFiles();
      $('#file-modal').fadeIn();
    });

    // Processing buttons
    $('#process-dtm').on('click', () => {
      ProcessingManager.processDTM();
    });

    $('#process-hillshade').on('click', () => {
      ProcessingManager.processHillshade();
    });

    $('#process-dsm').on('click', () => {
      ProcessingManager.processDSM();
    });

    $('#process-chm').on('click', () => {
      ProcessingManager.processCHM();
    });

    $('#process-slope').on('click', () => {
      ProcessingManager.processSlope();
    });

    $('#process-aspect').on('click', () => {
      ProcessingManager.processAspect();
    });

    $('#process-roughness').on('click', () => {
      ProcessingManager.processRoughness();
    });

    $('#process-tri').on('click', () => {
      ProcessingManager.processTRI();
    });

    $('#process-tpi').on('click', () => {
      ProcessingManager.processTPI();
    });

    $('#process-color-relief').on('click', () => {
      ProcessingManager.processColorRelief();
    });

    // Add to Map buttons
    $('.add-to-map-btn').on('click', function() {
      const processingType = $(this).data('processing-type');
      OverlayManager.handleAddToMapClick(processingType);
    });

    // Test coordinate acquisition button
    $('#test-coordinate-acquisition').on('click', () => {
      this.testCoordinateAcquisition();
    });

    // Test overlay button
    $('#test-overlay-btn').on('click', () => {
      this.testOverlay();
    });

    // Test Sentinel-2 button
    $('#test-sentinel2-btn').on('click', () => {
      this.testSentinel2();
    });

    // Clear selection button
    $('#clear-selection').on('click', () => {
      FileManager.clearSelection();
    });

    // Clear all overlays button
    $('#clear-overlays').on('click', () => {
      OverlayManager.clearAllOverlays();
    });

    // Settings button
    $('#settings-btn').on('click', () => {
      this.showSettingsModal();
    });

    // Help button
    $('#help-btn').on('click', () => {
      this.showHelpModal();
    });

    // File modal close buttons
    $('.close, #cancel-select').on('click', function() {
      $('#file-modal').fadeOut();
    });

    // File item selection in modal
    $(document).on('click', '.file-item', function() {
      $('.file-item').removeClass('selected');
      $(this).addClass('selected');
    });

    // Select region button in modal
    $('#confirm-region-selection').on('click', function() {
      const selectedItem = $('.file-item.selected'); // Changed from selectedFileItem
      if (selectedItem.length === 0) {
        Utils.showNotification('Please select a region first', 'warning'); // Changed message
        return;
      }

      const regionName = selectedItem.data('region-name'); // Changed from data('file-path')
      // const fileName = filePath.split('/').pop(); // No longer relevant for regions directly
      
      // Get coordinates from the region item if available
      // Assuming coordinates are stored on the item if parsed during displayRegions
      let coords = null;
      const latText = selectedItem.find('.file-coords').text().match(/Lat: ([-\d\.]+)/);
      const lngText = selectedItem.find('.file-coords').text().match(/Lng: ([-\d\.]+)/);
      if (latText && lngText) {
        coords = { lat: parseFloat(latText[1]), lng: parseFloat(lngText[1]) };
      }

      // Select the region using FileManager
      FileManager.selectRegion(regionName, coords); // Changed from selectFile
      
      // Close the modal
      $('#file-modal').fadeOut();
    });

    // Progress modal close buttons
    $('#progress-close, #cancel-progress').on('click', () => {
      this.hideProgress();
    });

    // Coordinate input field event handlers for region name generation
    $('#lat-input, #lng-input').on('input change', Utils.debounce(() => {
      this.updateRegionNameFromCoordinates();
    }, 500));

    // Manual region name editing
    $('#region-name-input').on('input', () => {
      // Allow manual editing of region name
      Utils.log('info', 'Region name manually edited');
    });

    Utils.log('info', 'Event handlers initialized');
  },

  /**
   * Initialize tooltips
   */
  initializeTooltips() {
    // Initialize tooltips for elements with data-tooltip attribute
    $('[data-tooltip]').each(function() {
      const tooltip = $(this).attr('data-tooltip');
      $(this).attr('title', tooltip);
    });

    // Custom tooltip implementation
    $('[data-tooltip]').hover(
      function() {
        const tooltip = $(this).attr('data-tooltip');
        const tooltipElement = $(`<div class="custom-tooltip">${tooltip}</div>`);
        $('body').append(tooltipElement);
        
        const offset = $(this).offset();
        tooltipElement.css({
          top: offset.top - tooltipElement.outerHeight() - 5,
          left: offset.left + ($(this).outerWidth() / 2) - (tooltipElement.outerWidth() / 2)
        }).fadeIn(200);
      },
      function() {
        $('.custom-tooltip').remove();
      }
    );

    Utils.log('info', 'Tooltips initialized');
  },

  /**
   * Initialize modals
   */
  initializeModals() {
    // Close modal on background click
    $('.modal').on('click', function(e) {
      if (e.target === this) {
        $(this).fadeOut();
      }
    });

    // Close modal on X button click
    $('.modal-close').on('click', function() {
      $(this).closest('.modal').fadeOut();
    });

    // Close modal on Escape key
    $(document).on('keydown', function(e) {
      if (e.key === 'Escape') {
        $('.modal:visible').fadeOut();
      }
    });

    Utils.log('info', 'Modals initialized');
  },

  /**
   * Test coordinate acquisition functionality
   */
  async testCoordinateAcquisition() {
    const lat = parseFloat($('#test-lat').val());
    const lng = parseFloat($('#test-lng').val());
    const regionName = $('#region-name-input').val(); // Get region name

    if (!Utils.isValidCoordinate(lat, lng)) {
      Utils.showNotification('Please enter valid coordinates', 'warning');
      return;
    }

    // If the user is testing coordinate acquisition, it implies they might want to acquire data.
    // We should include the region name if they've provided one.
    // This example doesn't directly call /api/acquire-data, but if it did, region_name would be included.
    // For now, we'll just log it and set the map view.

    try {
      this.showProgress('Setting map coordinates...');
      
      let message = 'Coordinates set successfully';
      if (regionName && regionName.trim() !== '') {
        message += ` for region: ${regionName.trim()}`;
        Utils.log('info', `Region name for coordinate test: ${regionName.trim()}`);
      }
      
      Utils.showNotification(message, 'success');
      MapManager.setView(lat, lng, 13);

    } catch (error) {
      Utils.log('error', 'Coordinate setting failed', error);
      Utils.showNotification('Failed to set coordinates', 'error');
    } finally {
      this.hideProgress();
    }
  },

  /**
   * Test overlay functionality
   */
  async testOverlay() {
    Utils.log('info', 'Test Overlay button clicked');

    const selectedRegion = FileManager.getSelectedRegion(); // Changed from getSelectedFile
    if (!selectedRegion) {
      Utils.showNotification('Please select a Region first before testing overlay', 'warning'); // Changed message
      return;
    }

    try {
      this.showProgress('Creating test overlay...');

      // Use selectedRegion directly as it's the identifier (e.g., folder name)
      Utils.log('info', `Testing overlay for region: ${selectedRegion}`);

      // Call the test overlay API endpoint, assuming it now takes regionName
      const response = await fetch(`/api/test-overlay/${selectedRegion}`); // Pass region name
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        Utils.log('info', 'Test overlay successful:', data);

        // Add the test overlay to the map using OverlayManager
        const bounds = [
          [data.bounds.south, data.bounds.west],
          [data.bounds.north, data.bounds.east]
        ];

        OverlayManager.addTestOverlay(data.image_data, bounds);

        Utils.showNotification('Test overlay added to map! Look for a black rectangle with red border.', 'success');
        Utils.log('info', 'Test overlay added to map with bounds:', bounds);

      } else {
        throw new Error(data.error || 'Unknown error');
      }

    } catch (error) {
      Utils.log('error', 'Error calling test overlay API:', error);
      Utils.showNotification(`Error testing overlay: ${error.message}`, 'error');
    } finally {
      this.hideProgress();
    }
  },

  /**
   * Test Sentinel-2 Images functionality
   */
  async testSentinel2() {
    Utils.log('info', 'Test Sentinel-2 button clicked');

    // Get coordinates from input fields
    let lat = $('#lat-input').val();
    let lng = $('#lng-input').val();
    const regionName = $('#region-name-input').val(); // Get region name

    // If no coordinates are set, use Portland, Oregon as default (good Sentinel-2 coverage)
    if (!lat || !lng || lat === '' || lng === '') {
      lat = 45.5152;  // Portland, Oregon
      lng = -122.6784;

      // Update the input fields
      $('#lat-input').val(lat);
      $('#lng-input').val(lng);

      // Center map on the location
      MapManager.setView(lat, lng, 12);

      // Add a marker
      MapManager.addSentinel2TestMarker(lat, lng);

      Utils.showNotification('Using Portland, Oregon coordinates for Sentinel-2 test (good satellite coverage area)', 'info');
    }

    // Validate coordinates
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);

    if (!Utils.isValidCoordinate(latNum, lngNum)) {
      Utils.showNotification('Invalid coordinates. Please enter valid latitude and longitude values.', 'error');
      return;
    }

    try {
      this.showProgress('🛰️ Downloading Sentinel-2 images...');

      // Start WebSocket connection for progress updates if available
      if (window.WebSocketManager) {
        WebSocketManager.connect();
      }

      const requestBody = {
        lat: latNum,
        lng: lngNum,
        buffer_km: 5.0,  // 5km radius for 10km x 10km area
        bands: ['B04', 'B08']  // Sentinel-2 red and NIR band identifiers
      };

      if (regionName && regionName.trim() !== '') {
        requestBody.region_name = regionName.trim();
      }

      const response = await fetch('/api/download-sentinel2', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result = await response.json();

      if (result.success) {
        Utils.log('info', 'Sentinel-2 download successful:', result);

        Utils.showNotification(
          `Successfully downloaded Sentinel-2 images! File size: ${result.file_size_mb?.toFixed(2) || 'Unknown'} MB`,
          'success'
        );

        // Automatically convert TIF files to PNG and display them
        // Use the region name from the result if available, otherwise from input
        const effectiveRegionName = result.metadata?.region_name || (regionName && regionName.trim() !== '' ? regionName.trim() : null);
        if (effectiveRegionName) {
          Utils.log('info', `Converting Sentinel-2 TIFs to PNG for region: ${effectiveRegionName}`);
          await this.convertAndDisplaySentinel2(effectiveRegionName);
        } else {
          Utils.log('error', 'No region name found in Sentinel-2 result or input for conversion.');
        }

      } else {
        throw new Error(result.error_message || 'Unknown error');
      }

    } catch (error) {
      Utils.log('error', 'Error downloading Sentinel-2 images:', error);
      Utils.showNotification(`Error downloading Sentinel-2 images: ${error.message}`, 'error');
    } finally {
      this.hideProgress();
    }
  },

  /**
   * Convert and display Sentinel-2 images
   * @param {string} regionName - Region name for the conversion
   */
  async convertAndDisplaySentinel2(regionName) {
    Utils.log('info', `Converting Sentinel-2 images for region: ${regionName}`);

    try {
      this.showProgress('Converting images to PNG...');

      const formData = new FormData();
      formData.append('region_name', regionName);

      const response = await fetch('/api/convert-sentinel2', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result = await response.json();

      if (result.success && result.files && result.files.length > 0) {
        Utils.log('info', `Successfully converted ${result.files.length} Sentinel-2 images for ${regionName}`);

        // Display each converted image in the satellite images gallery
        this.displaySentinel2Images(result.files, regionName); // Pass regionName here

        Utils.showNotification(`Converted ${result.files.length} Sentinel-2 images to PNG for ${regionName}`, 'success');
      } else {
        throw new Error(result.error || 'No images converted');
      }

    } catch (error) {
      Utils.log('error', 'Error converting Sentinel-2 images:', error);
      Utils.showNotification(`Error converting images: ${error.message}`, 'error');
    } finally {
      this.hideProgress();
    }
  },

  /**
   * Display Sentinel-2 images in the gallery
   * @param {Array} files - Array of converted image file objects
   */
  displaySentinel2Images(files, regionName) {
    const gallery = $('#satellite-gallery');
    if (!gallery.length) {
      Utils.log('error', 'Satellite gallery not found');
      return;
    }
    gallery.empty(); // Clear previous images

    // Expecting files to be objects with band, png_path, image, size_mb properties
    files.forEach(fileObj => {
      Utils.log('info', `Processing satellite image file: ${JSON.stringify(fileObj)} for region: ${regionName}`);
      
      const band = fileObj.band; // e.g., 'RED_B04', 'NIR_B08'
      const pngPath = fileObj.png_path;
      const imageB64 = fileObj.image;
      const sizeMb = fileObj.size_mb;
      
      let bandType = 'Unknown';
      let bandColor = '#666';
      if (band.includes('NIR_B08')) {
        bandType = 'NIR (B08)';
        bandColor = '#8B4513'; // Brown for NIR
      } else if (band.includes('RED_B04')) {
        bandType = 'Red (B04)';
        bandColor = '#DC143C'; // Crimson for Red
      }
      
      // Extract filename from png_path for display
      const fileName = pngPath.split('/').pop();
      Utils.log('info', `Image file: ${fileName}, Band: ${bandType}`);

      const imageItem = $(`
        <div class="gallery-item flex-shrink-0 w-64 h-48 bg-[#1a1a1a] border border-[#303030] rounded-lg overflow-hidden hover:border-[#404040] transition-colors">
          <div class="flex-1 relative">
            <img src="data:image/png;base64,${imageB64}" alt="${bandType} - ${regionName}" class="w-full h-full object-cover">
            <div class="absolute bottom-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ${bandType} - ${regionName}
            </div>
          </div>
          <button class="add-to-map-btn w-full bg-[#28a745] hover:bg-[#218838] text-white px-3 py-1 text-sm font-medium transition-colors" 
                  data-image-file="${fileName}" data-region-name="${regionName}" data-band-type="${bandType}">Add to Map</button>
        </div>
      `);

      // Handle add to map click for satellite images
      imageItem.find('.add-to-map-btn').on('click', function() {
        const $button = $(this);
        const imgFile = $button.data('image-file');
        const rName = $button.data('region-name');
        const bType = $button.data('band-type');
        
        // Create overlay key to check if it's already active
        const regionBand = `${rName}_${band}`;
        const overlayKey = `SENTINEL2_${regionBand}`;
        
        // Check if overlay is already active
        const isActive = OverlayManager.mapOverlays[overlayKey] !== undefined;
        
        if (isActive) {
          // Remove overlay
          Utils.log('info', `Removing ${bType} overlay from map for region ${rName}`);
          OverlayManager.removeOverlay(overlayKey);
          
          // Update button state to "Add to Map"
          $button.text('Add to Map')
                 .removeClass('bg-[#dc3545] hover:bg-[#c82333]')
                 .addClass('bg-[#28a745] hover:bg-[#218838]');
          
          Utils.showNotification(`Removed ${bType} overlay from map`, 'success');
        } else {
          // Add overlay
          Utils.log('info', `Adding ${bType} overlay to map for region ${rName}`);
          
          // Use the Sentinel-2 overlay API to get the image with proper bounds
          UIManager.addSentinel2OverlayToMap(regionBand, bType).then((success) => {
            if (success) {
              // Update button state to "Remove from Map"
              $button.text('Remove from Map')
                     .removeClass('bg-[#28a745] hover:bg-[#218838]')
                     .addClass('bg-[#dc3545] hover:bg-[#c82333]');
            }
          });
        }
      });

      gallery.append(imageItem);
    });

    Utils.log('info', `Displayed ${files.length} Sentinel-2 images in gallery for region ${regionName}`);
  },

  /**
   * Show settings modal
   */
  showSettingsModal() {
    $('#settings-modal').fadeIn();
  },

  /**
   * Show help modal
   */
  showHelpModal() {
    $('#help-modal').fadeIn();
  },

  /**
   * Show progress indicator
   * @param {string} message - Progress message
   */
  showProgress(message = 'Processing...') {
    $('#progress-title').text('Processing');
    $('#progress-status').text(message);
    $('#progress-bar').css('width', '0%');
    $('#progress-details').text('');
    $('#progress-modal').fadeIn();
    
    Utils.log('info', `Progress shown: ${message}`);
  },

  /**
   * Update progress
   * @param {number} percentage - Progress percentage (0-100)
   * @param {string} status - Status message
   * @param {string} details - Additional details
   */
  updateProgress(percentage, status = '', details = '') {
    if (status) $('#progress-status').text(status);
    if (details) $('#progress-details').text(details);
    $('#progress-bar').css('width', `${percentage}%`);
    
    Utils.log('info', `Progress updated: ${percentage}% - ${status}`);
  },

  /**
   * Hide progress indicator
   */
  hideProgress() {
    $('#progress-modal').fadeOut();
    Utils.log('info', 'Progress hidden');
  },

  /**
   * Update processing button states
   * @param {boolean} hasSelectedRegion - Whether a region is selected
   */
  updateProcessingButtons(hasSelectedRegion) { // Changed parameter name
    const processingButtons = $('.processing-btn');
    
    if (hasSelectedRegion) { // Changed variable name
      processingButtons.prop('disabled', false)
                     .removeClass('disabled')
                     .attr('title', 'Click to process selected region'); // Changed message
    } else {
      processingButtons.prop('disabled', true)
                     .addClass('disabled')
                     .attr('title', 'Please select a region first'); // Changed message
    }
  },

  /**
   * Show file info panel - This might need to be re-evaluated for regions
   * For now, it will show region name and coordinates if available.
   * @param {Object} regionInfo - Information about the selected region {name, coords}
   */
  showFileInfo(regionInfo) { // Parameter changed to regionInfo
    const panel = $('#file-info-panel');
    if (panel.length) {
      panel.find('.file-name').text(regionInfo.name || 'Unknown Region');
      // These might not be applicable or need different sources for regions
      panel.find('.file-size').text('N/A'); // Size isn't directly applicable to a region folder in this context
      panel.find('.file-path').text(`output/${regionInfo.name}`); // Example path
      panel.find('.file-coords').text(
        regionInfo.coords ? 
        `${regionInfo.coords.lat.toFixed(6)}, ${regionInfo.coords.lng.toFixed(6)}` : 
        'No coordinates for region'
      );
      panel.fadeIn();
    }
  },

  /**
   * Hide file info panel
   */
  hideFileInfo() {
    $('#file-info-panel').fadeOut();
  },

  /**
   * Update connection status indicator
   * @param {string} status - Connection status (connected, disconnected, error)
   */
  updateConnectionStatus(status) {
    const indicator = $('#connection-status');
    if (indicator.length) {
      indicator.removeClass('connected disconnected error')
               .addClass(status);
      
      const statusText = {
        connected: 'Connected',
        disconnected: 'Disconnected',
        error: 'Connection Error'
      };
      
      indicator.attr('title', statusText[status] || 'Unknown Status');
    }
  },

  /**
   * Show confirmation dialog
   * @param {string} message - Confirmation message
   * @param {Function} onConfirm - Callback for confirmation
   * @param {Function} onCancel - Callback for cancellation
   */
  showConfirmation(message, onConfirm, onCancel) {
    const modal = $(`
      <div class="modal confirmation-modal">
        <div class="modal-content">
          <h3>Confirmation</h3>
          <p>${message}</p>
          <div class="modal-buttons">
            <button class="btn btn-primary confirm-btn">Confirm</button>
            <button class="btn btn-secondary cancel-btn">Cancel</button>
          </div>
        </div>
      </div>
    `);

    $('body').append(modal);

    modal.find('.confirm-btn').on('click', () => {
      modal.remove();
      if (onConfirm) onConfirm();
    });

    modal.find('.cancel-btn').on('click', () => {
      modal.remove();
      if (onCancel) onCancel();
    });

    modal.fadeIn();
  },

  /**
   * Update UI theme
   * @param {string} theme - Theme name (light, dark)
   */
  updateTheme(theme) {
    $('body').removeClass('light-theme dark-theme')
             .addClass(`${theme}-theme`);
    
    localStorage.setItem('ui-theme', theme);
    Utils.log('info', `Theme updated to: ${theme}`);
  },

  /**
   * Load saved UI preferences
   */
  loadPreferences() {
    // Load theme preference
    const savedTheme = localStorage.getItem('ui-theme') || 'light';
    this.updateTheme(savedTheme);

    // Load accordion states
    const accordionStates = JSON.parse(localStorage.getItem('accordion-states') || '{}');
    Object.keys(accordionStates).forEach(accordion => {
      if (accordionStates[accordion]) {
        this.toggleAccordion(accordion);
      }
    });

    Utils.log('info', 'UI preferences loaded');
  },

  /**
   * Callback for when Sentinel-2 download completes via WebSocket
   * @param {Object} data - Download completion data, expected to include region_name
   */
  onSentinel2DownloadComplete(data) {
    Utils.log('info', 'Sentinel-2 download completed via WebSocket', data);
    
    const regionName = data.region_name; // Expect region_name directly from WebSocket
    
    if (regionName) {
      Utils.showNotification(`Sentinel-2 data ready for region: ${regionName}`, 'success');
      // If this region is currently selected, or to auto-select and display:
      // FileManager.selectRegion(regionName, data.coords); // Assuming coords might also come via WebSocket
      // Then call displaySentinel2ImagesForRegion or convertAndDisplaySentinel2
      setTimeout(async () => {
        try {
          await this.convertAndDisplaySentinel2(regionName);
          // If the downloaded region is the currently selected one, refresh its view
          if (FileManager.getSelectedRegion() === regionName) {
            this.displaySentinel2ImagesForRegion(regionName);
          }
        } catch (error) {
          Utils.log('error', 'Error in automatic Sentinel-2 conversion after download:', error);
          Utils.showNotification('Download completed but conversion/display failed: ' + error.message, 'error');
        }
      }, 1000); 
    } else {
      Utils.log('warn', 'Could not determine region name from WebSocket download completion data');
      Utils.showNotification('Sentinel-2 download completed! Please select the region to see images.', 'info');
    }
  },

  /**
   * Save UI preferences
   */
  savePreferences() {
    // Save accordion states
    const accordionStates = {
      region: !$('#region-content').hasClass('collapsed'),
      test: !$('#test-content').hasClass('collapsed'),
      processing: !$('#processing-content').hasClass('collapsed')
    };
    
    localStorage.setItem('accordion-states', JSON.stringify(accordionStates));
    Utils.log('info', 'UI preferences saved');
  },

  /**
   * Update region name based on current coordinate input values
   */
  updateRegionNameFromCoordinates() {
    const latInput = document.getElementById('lat-input');
    const lngInput = document.getElementById('lng-input');
    const regionNameInput = document.getElementById('region-name-input');

    if (!latInput || !lngInput || !regionNameInput) {
      return;
    }

    const lat = parseFloat(latInput.value);
    const lng = parseFloat(lngInput.value);

    if (Utils.isValidCoordinate(lat, lng)) {
      const regionName = Utils.generateRegionName(lat, lng);
      regionNameInput.value = regionName;
      Utils.log('info', `Region name updated to: ${regionName}`);
    } else {
      regionNameInput.value = '';
    }
  },

  /**
   * Fetches and displays Sentinel-2 images for a given region.
   * Checks for available Sentinel-2 images and displays them with proper metadata.
   * @param {string} regionName - The name of the region.
   */
  async displaySentinel2ImagesForRegion(regionName) {
    if (!regionName) {
      $('#satellite-gallery').empty().html('<div class="no-files">No region selected.</div>');
      return;
    }

    const gallery = $('#satellite-gallery');
    gallery.empty().html('<div class="loading text-center py-8 text-[#ababab]">Loading satellite images...</div>');

    Utils.log('info', `Fetching Sentinel-2 images for selected region: ${regionName}`);
    
    try {
      // Try to get available Sentinel-2 images for the region
      // We'll check for the most common bands: RED (B04) and NIR (B08)
      const bands = ['RED_B04', 'NIR_B08'];
      const availableImages = [];

      for (const band of bands) {
        try {
          // Use the Sentinel-2 overlay API to check if the band is available
          const response = await fetch(`/api/overlay/sentinel2/${regionName}_${band}`);
          
          if (response.ok) {
            const overlayData = await response.json();
            if (overlayData && overlayData.image_data) {
              availableImages.push({
                band: band,
                bandDisplay: band === 'RED_B04' ? 'Red (B04)' : 'NIR (B08)',
                overlayData: overlayData,
                timestamp: this.extractTimestampFromFilename(overlayData.filename || ''),
                regionName: regionName
              });
              Utils.log('info', `Found ${band} band data for region ${regionName}`);
            }
          } else {
            Utils.log('info', `No ${band} band data available for region ${regionName}`);
          }
        } catch (error) {
          Utils.log('warn', `Error checking ${band} band for region ${regionName}:`, error);
        }
      }

      if (availableImages.length === 0) {
        gallery.html(`
          <div class="no-files text-center py-8">
            <div class="text-[#ababab] mb-4">No Sentinel-2 satellite images found for region: ${regionName}</div>
            <div class="text-sm text-[#666]">
              Images may need to be downloaded and processed first.<br>
              Use the region coordinates to download Sentinel-2 data.
            </div>
          </div>
        `);
        return;
      }

      // Display available images
      this.displaySentinel2ImageGallery(availableImages);
      Utils.log('info', `Displayed ${availableImages.length} Sentinel-2 images for region ${regionName}`);

    } catch (error) {
      Utils.log('error', `Error fetching Sentinel-2 images for ${regionName}:`, error);
      gallery.html(`
        <div class="error text-center py-8">
          <div class="text-red-400 mb-2">Error loading satellite images</div>
          <div class="text-sm text-[#666]">${error.message}</div>
        </div>
      `);
      Utils.showNotification(`Could not load satellite images for ${regionName}`, 'error');
    }
  },

  /**
   * Extract timestamp from filename for sorting/display
   * @param {string} filename - The filename to parse
   * @returns {string} Extracted timestamp or empty string
   */
  extractTimestampFromFilename(filename) {
    const match = filename.match(/(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})/);
    return match ? match[1] : '';
  },

  /**
   * Display Sentinel-2 images in a gallery format
   * @param {Array} images - Array of image data objects
   */
  displaySentinel2ImageGallery(images) {
    const gallery = $('#satellite-gallery');
    gallery.empty();

    // Sort images by timestamp (newest first) and then by band type
    images.sort((a, b) => {
      if (a.timestamp !== b.timestamp) {
        return b.timestamp.localeCompare(a.timestamp);
      }
      return a.band.localeCompare(b.band);
    });

    images.forEach(imageData => {
      const { band, bandDisplay, overlayData, timestamp, regionName } = imageData;
      
      // Create base64 data URL for the image
      const imageDataUrl = `data:image/png;base64,${overlayData.image_data}`;
      
      // Format timestamp for display
      const displayTimestamp = timestamp ? 
        new Date(timestamp.replace(/T/, ' ').replace(/-/g, ':')).toLocaleDateString() : 
        'Unknown date';

      const imageItem = $(`
        <div class="gallery-item flex-shrink-0 w-64 bg-[#1a1a1a] border border-[#303030] rounded-lg overflow-hidden hover:border-[#404040] transition-colors">
          <div class="relative h-48">
            <img src="${imageDataUrl}" 
                 alt="${bandDisplay} - ${regionName}" 
                 class="w-full h-full object-cover cursor-pointer"
                 title="Click to view larger image">
            <div class="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ${bandDisplay}
            </div>
            <div class="absolute bottom-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ${displayTimestamp}
            </div>
            <div class="absolute top-2 right-2 bg-blue-600 bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              Sentinel-2
            </div>
          </div>
          <div class="p-3">
            <div class="text-white text-sm font-medium mb-2">${regionName}</div>
            <button class="add-to-map-btn w-full bg-[#28a745] hover:bg-[#218838] text-white px-3 py-2 text-sm font-medium rounded transition-colors" 
                    data-band="${band}" 
                    data-region-name="${regionName}" 
                    data-band-display="${bandDisplay}">
              Add ${bandDisplay} to Map
            </button>
          </div>
        </div>
      `);

      // Handle image click to show larger view
      imageItem.find('img').on('click', function() {
        UIManager.showImageModal(imageDataUrl, `${bandDisplay} - ${regionName} (${displayTimestamp})`);
      });

      // Handle add to map click
      imageItem.find('.add-to-map-btn').on('click', function() {
        const $button = $(this);
        const selectedBand = $button.data('band');
        const selectedRegion = $button.data('region-name');
        const selectedBandDisplay = $button.data('band-display');
        
        // Create overlay key to check if it's already active
        const regionBand = `${selectedRegion}_${selectedBand}`;
        const overlayKey = `SENTINEL2_${regionBand}`;
        
        // Check if overlay is already active
        const isActive = OverlayManager.mapOverlays[overlayKey] !== undefined;
        
        if (isActive) {
          // Remove overlay
          Utils.log('info', `Removing ${selectedBandDisplay} overlay from map for region ${selectedRegion}`);
          OverlayManager.removeOverlay(overlayKey);
          
          // Update button state to "Add to Map"
          $button.text(`Add ${selectedBandDisplay} to Map`)
                 .removeClass('bg-[#dc3545] hover:bg-[#c82333]')
                 .addClass('bg-[#28a745] hover:bg-[#218838]');
          
          Utils.showNotification(`Removed ${selectedBandDisplay} overlay from map`, 'success');
        } else {
          // Add overlay
          Utils.log('info', `Adding ${selectedBandDisplay} overlay to map for region ${selectedRegion}`);
          
          // Use the Sentinel-2 overlay API to get the image with proper bounds
          UIManager.addSentinel2OverlayToMap(regionBand, selectedBandDisplay).then((success) => {
            if (success) {
              // Update button state to "Remove from Map"
              $button.text(`Remove ${selectedBandDisplay} from Map`)
                     .removeClass('bg-[#28a745] hover:bg-[#218838]')
                     .addClass('bg-[#dc3545] hover:bg-[#c82333]');
            }
          });
        }
      });

      gallery.append(imageItem);
    });
  },

  /**
   * Show image in a modal for larger viewing
   * @param {string} imageDataUrl - Base64 data URL of the image
   * @param {string} title - Title for the modal
   */
  showImageModal(imageDataUrl, title) {
    // Remove existing modal if present
    $('#image-modal').remove();
    
    const modal = $(`
      <div id="image-modal" class="modal fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
        <div class="modal-content bg-[#1a1a1a] border border-[#303030] rounded-lg max-w-4xl max-h-[90vh] overflow-hidden">
          <div class="modal-header flex justify-between items-center p-4 border-b border-[#303030]">
            <h3 class="text-white text-lg font-semibold">${title}</h3>
            <button class="modal-close text-[#ababab] hover:text-white text-2xl">&times;</button>
          </div>
          <div class="modal-body p-4">
            <img src="${imageDataUrl}" alt="${title}" class="max-w-full max-h-[70vh] object-contain mx-auto">
          </div>
        </div>
      </div>
    `);
    
    // Handle modal close
    modal.find('.modal-close').on('click', () => modal.remove());
    modal.on('click', function(e) {
      if (e.target === this) modal.remove();
    });
    
    $('body').append(modal);
  },

  /**
   * Add Sentinel-2 overlay to map using the overlay API
   * @param {string} regionBand - Region and band identifier (e.g., "region_18_83S_45_00W_RED_B04")
   * @param {string} bandType - Display name for the band (e.g., "Red (B04)")
   */
  async addSentinel2OverlayToMap(regionBand, bandType) {
    Utils.log('info', `Adding Sentinel-2 overlay to map: ${regionBand}`);
    
    try {
      this.showProgress(`Adding ${bandType} overlay to map...`);
      
      // Call the Sentinel-2 overlay API
      const response = await fetch(`/api/overlay/sentinel2/${regionBand}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }
      
      const overlayData = await response.json();
      
      if (!overlayData.bounds || !overlayData.image_data) {
        throw new Error('Invalid overlay data received');
      }
      
      // Create image bounds for Leaflet
      const bounds = [
        [overlayData.bounds.south, overlayData.bounds.west],
        [overlayData.bounds.north, overlayData.bounds.east]
      ];
      
      const imageUrl = `data:image/png;base64,${overlayData.image_data}`;
      const overlayKey = `SENTINEL2_${regionBand}`;
      
      // Use OverlayManager to add the overlay
      const success = OverlayManager.addImageOverlay(
        overlayKey,
        imageUrl,
        bounds,
        {
          opacity: 0.8,
          attribution: 'Sentinel-2 © Copernicus'
        }
      );
      
      if (success) {
        Utils.showNotification(`Added ${bandType} overlay to map`, 'success');
        return true;
      } else {
        throw new Error('Failed to add overlay to map');
      }
      
    } catch (error) {
      Utils.log('error', `Error adding Sentinel-2 overlay:`, error);
      Utils.showNotification(`Error adding ${bandType} overlay: ${error.message}`, 'error');
      return false;
    } finally {
      this.hideProgress();
    }
  },
};
