/**
 * UI interactions and interface management
 */

window.UIManager = {
  /**
   * Initialize UI components
   */
  init() {
    this.initializeTabs();
    this.initializeAccordions();
    this.initializeEventHandlers();
    this.initializeTooltips();
    this.initializeModals();
    this.initializeGlobalRegionSelector();
    this.initializeResizablePanels();
    
    Utils.log('info', 'UI Manager initialized');
  },

  /**
   * Initialize tab functionality
   */
  initializeTabs() {
    // Tab switching event handlers
    $('.tab-btn').on('click', (e) => {
      const targetTab = $(e.target).data('tab');
      this.switchTab(targetTab);
    });

    Utils.log('info', 'Tabs initialized');
  },

  /**
   * Switch to a specific tab
   * @param {string} tabName - Name of the tab to switch to ('map' or 'analysis')
   */
  switchTab(tabName) {
    // Update tab buttons
    $('.tab-btn').removeClass('active').addClass('text-[#ababab]').removeClass('text-white').removeClass('border-[#00bfff]').addClass('border-transparent');
    $(`.tab-btn[data-tab="${tabName}"]`).addClass('active').removeClass('text-[#ababab]').addClass('text-white').removeClass('border-transparent').addClass('border-[#00bfff]');

    // Update tab content
    $('.tab-content').addClass('hidden');
    $(`#${tabName}-tab`).removeClass('hidden');

    // Initialize Analysis tab if switching to it for the first time
    if (tabName === 'analysis') {
      this.initializeAnalysisTab();
      
      // Sync region selection if one is selected globally
      const currentRegion = this.globalSelectedRegion || FileManager.getSelectedRegion();
      if (currentRegion) {
        // Load analysis images for the current region
        this.loadAnalysisImages(currentRegion);
      }
    }

    Utils.log('info', `Switched to ${tabName} tab`);
  },

  /**
   * Initialize global region selector
   */
  initializeGlobalRegionSelector() {
    // Store reference to the currently selected region
    this.globalSelectedRegion = null;
    
    Utils.log('info', 'Global region selector initialized');
  },

  /**
   * Update global region selector display
   * @param {string} regionName - Name of the selected region
   */
  updateGlobalRegionSelector(regionName) {
    this.globalSelectedRegion = regionName;
    
    if (regionName) {
      $('#global-selected-region-name')
        .text(regionName)
        .removeClass('text-[#666]')
        .addClass('text-[#00bfff]');
    } else {
      $('#global-selected-region-name')
        .text('No region selected')
        .removeClass('text-[#00bfff]')
        .addClass('text-[#666]');
    }
    
    Utils.log('info', `Global region selector updated: ${regionName}`);
  },

  /**
   * Handle global region selection
   * @param {string} regionName - Name of the selected region
   * @param {Object} coords - Coordinates object with lat/lng
   */
  handleGlobalRegionSelection(regionName, coords = null) {
    // Update global selector
    this.updateGlobalRegionSelector(regionName);
    
    // Update FileManager's selected region
    FileManager.selectedRegion = regionName;
    
    // Switch to Map tab
    this.switchTab('map');
    
    // Set map view and pin if coordinates are available
    if (coords && Utils.isValidCoordinate(coords.lat, coords.lng)) {
      MapManager.setView(coords.lat, coords.lng, 13);
      FileManager.updateLocationPin(coords.lat, coords.lng, regionName);
    }
    
    // Load satellite images and LIDAR data for the region
    this.displaySentinel2ImagesForRegion(regionName);
    this.displayLidarRasterForRegion(regionName);
    
    // Show success notification
    Utils.showNotification(`Selected Region: ${regionName}`, 'success', 2000);
    
    Utils.log('info', `Global region selection completed: ${regionName}`, { coords });
  },

  /**
   * Initialize accordion functionality
   */
  initializeAccordions() {
    // Get Data accordion (renamed from Test)
    $('#get-data-accordion').on('click', () => {
      this.toggleAccordion('get-data');
    });

    // Go to accordion
    $('#go-to-accordion').on('click', () => {
      this.toggleAccordion('go-to');
    });

    // Analysis tab accordions
    $('#analysis-images-accordion').on('click', () => {
      this.toggleAccordion('analysis-images');
    });

    $('#analysis-tools-accordion').on('click', () => {
      this.toggleAccordion('analysis-tools');
    });

    $('#data-sources-accordion').on('click', () => {
      this.toggleAccordion('data-sources');
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
    // Global region selector button
    $('#global-browse-regions-btn').on('click', () => {
      FileManager.loadFiles();
      $('#file-modal').fadeIn();
      // Set a flag to indicate this is for global region selection
      $('#file-modal').data('for-global', true);
      // Hide the delete button when modal is first opened
      $('#delete-region-btn').addClass('hidden').prop('disabled', false).text('Delete Region');
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

    $('#process-color-relief').on('click', () => {
      ProcessingManager.processColorRelief();
    });

    // Add to Map buttons (excluding gallery buttons which have their own handler)
    $('.add-to-map-btn:not(#gallery .add-to-map-btn)').on('click', function() {
      const processingType = $(this).data('processing-type');
      OverlayManager.handleAddToMapClick(processingType);
    });

    // Processing Results gallery "Add to Map" buttons (using data-target)
    $('#gallery .add-to-map-btn').on('click', function(e) {
      e.preventDefault();
      const $button = $(this);
      const processingType = $button.data('target');
      
      if (!processingType) {
        Utils.log('warn', 'No processing type found in data-target attribute');
        return;
      }

      Utils.log('info', `Processing Results gallery: Add to Map clicked for ${processingType}`);
      
      // Handle the add to map functionality for Processing Results gallery
      UIManager.handleProcessingResultsAddToMap(processingType, $button);
    });

    // Test coordinate acquisition button
    $('#test-coordinate-acquisition').on('click', () => {
      this.testCoordinateAcquisition();
    });

    // Test Sentinel-2 button
    $('#test-sentinel2-btn').on('click', () => {
      this.testSentinel2();
    });

    // Get Elevation Data button
    $('#get-lidar-btn').on('click', () => {
      this.acquireElevationData();
    });

    // Get Data button (Combined: Elevation + Satellite)
    $('#get-data-btn').on('click', () => {
      this.getCombinedData();
    });

    // Go to coordinates button
    $('#go-to-coordinates-btn').on('click', () => {
      this.goToCoordinates();
    });

    // Coordinate input parser
    $('#goto-coordinates-input').on('input', Utils.debounce(() => {
      this.parseAndDisplayCoordinates();
    }, 300));

    // Preset location buttons
    $(document).on('click', '.preset-location', function() {
      const lat = parseFloat($(this).data('lat'));
      const lng = parseFloat($(this).data('lng'));
      UIManager.goToPresetLocation(lat, lng, $(this).text().replace('📍 ', ''));
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
      // Hide the delete button when modal is closed
      $('#delete-region-btn').addClass('hidden').prop('disabled', false).text('Delete Region');
    });

    // File item selection in modal
    $(document).on('click', '.file-item', function() {
      $('.file-item').removeClass('selected');
      $(this).addClass('selected');
      
      // Show the delete button when a region is selected
      $('#delete-region-btn').removeClass('hidden');
    });
    
    // Delete region button in modal
    $('#delete-region-btn').on('click', function() {
      const selectedItem = $('.file-item.selected');
      if (selectedItem.length === 0) {
        Utils.showNotification('Please select a region first', 'warning');
        return;
      }
      
      const regionName = selectedItem.data('region-name');
      
      // Confirm deletion
      if (confirm(`Are you sure you want to delete the region "${regionName}"? This will permanently delete all files in input/${regionName} and output/${regionName}.`)) {
        // Show loading state
        $(this).prop('disabled', true).text('Deleting...');
        
        // Use FileManager's deleteRegion method
        FileManager.deleteRegion(regionName)
          .then(result => {
            if (result.success) {
              Utils.showNotification(`Region "${regionName}" deleted successfully`, 'success');
              
              // Remove from UI
              selectedItem.remove();
              
              // Reset button
              $('#delete-region-btn').addClass('hidden').prop('disabled', false).text('Delete Region');
              
              // If this was the currently selected region, reset the selection UI
              if (FileManager.getSelectedRegion() === regionName) {
                $('#selected-region-name').text('No region selected').removeClass('text-[#00bfff]').addClass('text-[#666]');
              }
            } else {
              Utils.showNotification(`Failed to delete region: ${result.message}`, 'error');
              $('#delete-region-btn').prop('disabled', false).text('Delete Region');
            }
          })
          .catch(error => {
            console.error('Error deleting region:', error);
            Utils.showNotification(`Error deleting region: ${error.message}`, 'error');
            $('#delete-region-btn').prop('disabled', false).text('Delete Region');
          });
      }
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

      // Check which type of selection this is
      const isForGlobal = $('#file-modal').data('for-global');
      const isForAnalysis = $('#file-modal').data('for-analysis');
      
      if (isForGlobal) {
        // Handle global region selection
        UIManager.handleGlobalRegionSelection(regionName, coords);
        // Clear the flag
        $('#file-modal').removeData('for-global');
      } else if (isForAnalysis) {
        // Update Analysis tab
        UIManager.updateAnalysisSelectedRegion(regionName);
        // Clear the flag
        $('#file-modal').removeData('for-analysis');
      } else {
        // Select the region using FileManager for Map tab
        FileManager.selectRegion(regionName, coords); // Changed from selectFile
      }
      
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
   * Initialize resizable panels
   */
  initializeResizablePanels() {
    let isResizing = false;
    let currentPanel = null;
    let startX = 0;
    let startWidth = 0;

    // Handle mousedown on resize handles
    $('.resize-handle').on('mousedown', function(e) {
      e.preventDefault();
      isResizing = true;
      currentPanel = $(this).parent();
      startX = e.pageX;
      startWidth = currentPanel.outerWidth();
      
      $(this).addClass('dragging');
      $('body').addClass('resize-active');
      
      Utils.log('debug', 'Started resizing panel');
    });

    // Handle mousemove for resizing
    $(document).on('mousemove', function(e) {
      if (!isResizing || !currentPanel) return;
      
      e.preventDefault();
      const deltaX = e.pageX - startX;
      const newWidth = Math.max(200, Math.min(600, startWidth + deltaX));
      
      currentPanel.css('width', newWidth + 'px');
    });

    // Handle mouseup to stop resizing
    $(document).on('mouseup', function(e) {
      if (!isResizing) return;
      
      isResizing = false;
      $('.resize-handle').removeClass('dragging');
      $('body').removeClass('resize-active');
      
      if (currentPanel) {
        const finalWidth = currentPanel.outerWidth();
        Utils.log('info', `Panel resized to ${finalWidth}px`);
        
        // Save panel width preference
        const panelId = currentPanel.attr('id');
        localStorage.setItem(`panel-width-${panelId}`, finalWidth);
      }
      
      currentPanel = null;
      startX = 0;
      startWidth = 0;
    });

    // Load saved panel widths
    $('.resizable-panel').each(function() {
      const panelId = $(this).attr('id');
      const savedWidth = localStorage.getItem(`panel-width-${panelId}`);
      if (savedWidth) {
        $(this).css('width', savedWidth + 'px');
      }
    });

    Utils.log('info', 'Resizable panels initialized');
  },

  /**
   * Test coordinate acquisition functionality
   */
  async testCoordinateAcquisition() {
    const lat = parseFloat($('#lat-input').val());
    const lng = parseFloat($('#lng-input').val());
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

    // Create image items with the same styling as Analysis tab
    const imageItems = files.map(fileObj => {
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
      } else if (band === 'NDVI') {
        bandType = 'NDVI';
        bandColor = '#228B22'; // Forest green for NDVI (vegetation index)
      }
      
      // Extract filename from png_path for display
      const fileName = pngPath.split('/').pop();
      Utils.log('info', `Image file: ${fileName}, Band: ${bandType}`);

      return `
        <div class="gallery-item w-64 bg-[#1a1a1a] border border-[#303030] rounded-lg overflow-hidden hover:border-[#404040] transition-colors">
          <div class="relative h-48">
            <img src="data:image/png;base64,${imageB64}" 
                 alt="${bandType} - ${regionName}" 
                 class="w-full h-full object-cover cursor-pointer"
                 title="Click to view larger image">
            <div class="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ${bandType}
            </div>
            <div class="absolute bottom-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ${(sizeMb || 0).toFixed(1)} MB
            </div>
            <div class="absolute top-2 right-2 bg-blue-600 bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              Sentinel-2
            </div>
          </div>
          <div class="p-3">
            <div class="text-white text-sm font-medium mb-2">${regionName}</div>
            <button class="add-to-map-btn w-full bg-[#28a745] hover:bg-[#218838] text-white px-3 py-2 text-sm font-medium rounded transition-colors" 
                    data-image-file="${fileName}" 
                    data-region-name="${regionName}" 
                    data-band-type="${band}"
                    data-band="${band}">
              Add ${bandType} to Map
            </button>
          </div>
        </div>
      `;
    }).join('');

    // Display in a responsive grid layout like Analysis tab
    gallery.html(`
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        ${imageItems}
      </div>
    `);

    // Add event handlers after rendering
    gallery.find('.gallery-item img').on('click', function() {
      const imageSrc = $(this).attr('src');
      const imageAlt = $(this).attr('alt');
      UIManager.showImageModal(imageSrc, imageAlt);
    });

    // Handle add to map click for satellite images
    gallery.find('.add-to-map-btn').on('click', function() {
      const $button = $(this);
      const imgFile = $button.data('image-file');
      const rName = $button.data('region-name');
      const bType = $button.data('band-type');
      const band = $button.data('band');
      
      // Ensure proper API region name format for overlay calls
      let apiRegionName = rName;
      if (!rName.startsWith('region_')) {
        apiRegionName = `region_${rName.replace(/\./g, '_')}`;
      }
      
      // Create overlay key to check if it's already active
      const regionBand = `${apiRegionName}_${band}`;
      const overlayKey = `SENTINEL2_${regionBand}`;
      
      // Check if overlay is already active
      const isActive = OverlayManager.mapOverlays[overlayKey] !== undefined;
      
      if (isActive) {
        // Remove overlay
        Utils.log('info', `Removing ${bType} overlay from map for region ${rName}`);
        OverlayManager.removeOverlay(overlayKey);
        
        // Update button state to "Add to Map"
        $button.text(`Add ${bType} to Map`)
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
            $button.text(`Remove ${bType} from Map`)
                   .removeClass('bg-[#28a745] hover:bg-[#218838]')
                   .addClass('bg-[#dc3545] hover:bg-[#c82333]');
          }
        });
      }
    });

    Utils.log('info', `Displayed ${files.length} Sentinel-2 images in gallery for region ${regionName}`);
  },

  /**
   * Fetches and displays Sentinel-2 images for a given region.
   * Checks for available Sentinel-2 processing results and displays them in the satellite gallery.
   * @param {string} regionName - The name of the region.
   */
  async displaySentinel2ImagesForRegion(regionName) {
    Utils.log('info', `Checking for Sentinel-2 images for region: ${regionName}`);

    try {
      // Check for available Sentinel-2 bands (RED, NIR, NDVI)
      const availableBands = [];
      const sentinel2Bands = ['RED_B04', 'NIR_B08', 'NDVI'];

      for (const band of sentinel2Bands) {
        try {
          // Use the overlay API to check if the band data exists
          let apiRegionName = regionName;
          if (!regionName.startsWith('region_')) {
            apiRegionName = `region_${regionName.replace(/\./g, '_')}`;
          }

          const regionBand = `${apiRegionName}_${band}`;
          const response = await fetch(`/api/overlay/sentinel2/${regionBand}`);

          if (response.ok) {
            const overlayData = await response.json();
            if (overlayData && overlayData.image_data) {
              availableBands.push({
                band: band,
                bandType: this.getSentinel2BandDisplayName(band),
                overlayData: overlayData,
                regionName: regionName,
                filename: overlayData.filename || `${regionName}_${band}`
              });
              Utils.log('info', `Found ${band} data for region ${regionName}`);
            }
          } else {
            // This is expected - not all bands may be available
            Utils.log('debug', `No ${band} data available for region ${regionName}`);
          }
        } catch (error) {
          Utils.log('debug', `Error checking ${band} for region ${regionName}:`, error);
        }
      }

      if (availableBands.length === 0) {
        Utils.log('info', `No Sentinel-2 images found for region ${regionName}`);
        // Don't show anything in the satellite gallery if no data exists
        return;
      }

      // Display available Sentinel-2 images in the satellite gallery
      this.displaySentinel2BandsGallery(availableBands);
      Utils.log('info', `Displayed ${availableBands.length} Sentinel-2 images for region ${regionName}`);

    } catch (error) {
      Utils.log('error', `Error fetching Sentinel-2 images for region ${regionName}:`, error);
    }
  },

  /**
   * Display Sentinel-2 band images in the satellite gallery
   * @param {Array} availableBands - Array of available band data
   */
  displaySentinel2BandsGallery(availableBands) {
    const gallery = $('#satellite-gallery');
    if (!gallery.length) {
      Utils.log('error', 'Satellite gallery not found');
      return;
    }
    gallery.empty(); // Clear previous images

    // Create image items with the same styling as the converted images
    const imageItems = availableBands.map(bandData => {
      const { band, bandType, overlayData, regionName } = bandData;
      const imageB64 = overlayData.image_data;
      
      // Get band color for styling
      let bandColor = '#666';
      if (band.includes('NIR')) {
        bandColor = '#8B4513'; // Brown for NIR
      } else if (band.includes('RED')) {
        bandColor = '#DC143C'; // Crimson for Red
      } else if (band === 'NDVI') {
        bandColor = '#228B22'; // Forest green for NDVI
      }

      return `
        <div class="gallery-item w-64 bg-[#1a1a1a] border border-[#303030] rounded-lg overflow-hidden hover:border-[#404040] transition-colors">
          <div class="relative h-48">
            <img src="data:image/png;base64,${imageB64}" 
                 alt="${bandType} - ${regionName}" 
                 class="w-full h-full object-cover cursor-pointer"
                 title="Click to view larger image">
            <div class="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ${bandType}
            </div>
            <div class="absolute top-2 right-2 bg-blue-600 bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              Sentinel-2
            </div>
          </div>
          <div class="p-3">
            <div class="text-white text-sm font-medium mb-2">${regionName}</div>
            <button class="add-to-map-btn w-full bg-[#28a745] hover:bg-[#218838] text-white px-3 py-2 text-sm font-medium rounded transition-colors" 
                    data-region-name="${regionName}" 
                    data-band-type="${bandType}"
                    data-band="${band}">
              Add ${bandType} to Map
            </button>
          </div>
        </div>
      `;
    }).join('');

    // Display in a responsive grid layout
    gallery.html(`
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        ${imageItems}
      </div>
    `);

    // Add event handlers after rendering
    gallery.find('.gallery-item img').on('click', function() {
      const imageSrc = $(this).attr('src');
      const imageAlt = $(this).attr('alt');
      UIManager.showImageModal(imageSrc, imageAlt);
    });

    // Handle add to map click for satellite images
    gallery.find('.add-to-map-btn').on('click', function() {
      const $button = $(this);
      const rName = $button.data('region-name');
      const bType = $button.data('band-type');
      const band = $button.data('band');
      
      // Ensure proper API region name format for overlay calls
      let apiRegionName = rName;
      if (!rName.startsWith('region_')) {
        apiRegionName = `region_${rName.replace(/\./g, '_')}`;
      }
      
      // Create overlay key to check if it's already active
      const regionBand = `${apiRegionName}_${band}`;
      const overlayKey = `SENTINEL2_${regionBand}`;
      
      // Check if overlay is already active
      const isActive = OverlayManager.mapOverlays[overlayKey] !== undefined;
      
      if (isActive) {
        // Remove overlay
        Utils.log('info', `Removing ${bType} overlay from map for region ${rName}`);
        OverlayManager.removeOverlay(overlayKey);
        
        // Update button state to "Add to Map"
        $button.text(`Add ${bType} to Map`)
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
            $button.text(`Remove ${bType} from Map`)
                   .removeClass('bg-[#28a745] hover:bg-[#218838]')
                   .addClass('bg-[#dc3545] hover:bg-[#c82333]');
          }
        });
      }
    });

    Utils.log('info', `Displayed ${availableBands.length} Sentinel-2 bands in gallery`);
  },

  /**
   * Get display name for Sentinel-2 bands
   * @param {string} band - Band identifier (e.g., 'RED_B04', 'NIR_B08', 'NDVI')
   * @returns {string} Display-friendly name
   */
  getSentinel2BandDisplayName(band) {
    if (band.includes('NIR_B08')) {
      return 'NIR (B08)';
    } else if (band.includes('RED_B04')) {
      return 'Red (B04)';
    } else if (band === 'NDVI') {
      return 'NDVI';
    }
    return band;
  },

  /**
   * Fetches and displays LIDAR raster images for a given region.
   * Checks for available LIDAR processing results and displays them in the processing gallery.
   * @param {string} regionName - The name of the region.
   */
  async displayLidarRasterForRegion(regionName) {
    if (!regionName) {
      Utils.log('info', 'No region selected for LIDAR raster display');
      return;
    }

    Utils.log('info', `Checking for LIDAR raster images for region: ${regionName}`);
    
    try {
      // Processing types that might have LIDAR raster results
      const processingTypes = ['hillshade', 'slope', 'aspect', 'color_relief'];
      const availableRasters = [];

      // Check each processing type for available raster data
      for (const processingType of processingTypes) {
        try {
          const response = await fetch(`/api/overlay/raster/${regionName}/${processingType}`);
          
          if (response.ok) {
            const overlayData = await response.json();
            if (overlayData && overlayData.image_data) {
              availableRasters.push({
                processingType: processingType,
                display: this.getProcessingDisplayName(processingType),
                color: this.getProcessingColor(processingType),
                overlayData: overlayData,
                regionName: regionName,
                filename: overlayData.filename || `${regionName}_${processingType}`
              });
              Utils.log('info', `Found ${processingType} raster data for region ${regionName}`);
            }
          } else {
            // This is expected - not all processing types may be available
            Utils.log('debug', `No ${processingType} raster data available for region ${regionName}`);
          }
        } catch (error) {
          Utils.log('debug', `Error checking ${processingType} raster for region ${regionName}:`, error);
        }
      }

      if (availableRasters.length === 0) {
        Utils.log('info', `No LIDAR raster images found for region ${regionName}`);
        // Reset gallery to show processing buttons instead
        this.resetProcessingGalleryToLabels();
        return;
      }

      // Display available LIDAR raster images in the processing gallery
      this.displayLidarRasterGallery(availableRasters);
      Utils.log('info', `Displayed ${availableRasters.length} LIDAR raster images for region ${regionName}`);

    } catch (error) {
      Utils.log('error', `Error fetching LIDAR raster images for ${regionName}:`, error);
      // Reset to labels on error
      this.resetProcessingGalleryToLabels();
    }
  },

  /**
   * Display LIDAR raster images in the Processing Results gallery
   * @param {Array} availableRasters - Array of available raster data
   */
  displayLidarRasterGallery(availableRasters) {
    const gallery = $('#gallery');
    
    if (!availableRasters || availableRasters.length === 0) {
      this.resetProcessingGalleryToLabels();
      return;
    }

    // Create image items for each available raster
    const imageItems = availableRasters.map(raster => {
      const { processingType, display, overlayData, regionName } = raster;
      const imageDataUrl = `data:image/png;base64,${overlayData.image_data}`;
      
      return `
        <div class="gallery-item flex-shrink-0 w-64 h-48 bg-[#1a1a1a] border border-[#303030] rounded-lg flex flex-col hover:border-[#404040] transition-colors" id="cell-${processingType}">
          <div class="flex-1 flex items-center justify-center relative">
            <img src="${imageDataUrl}" 
                 alt="${display}" 
                 class="processing-result-image cursor-pointer"
                 title="Click to view larger image">
            <div class="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ${display}
            </div>
            <div class="absolute top-2 right-2 bg-green-600 bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ✓ Ready
            </div>
          </div>
          <button class="add-to-map-btn bg-[#28a745] hover:bg-[#218838] text-white px-3 py-1 rounded-b-lg text-sm font-medium transition-colors" 
                  data-target="${processingType}"
                  data-region-name="${regionName}">
            Add to Map
          </button>
        </div>
      `;
    }).join('');

    // Update the gallery with the image items
    gallery.html(`
      <div class="flex gap-4 overflow-x-auto pb-4">
        ${imageItems}
      </div>
    `);

    // Add click handlers for image modal view
    gallery.find('.processing-result-image').on('click', function() {
      const imageSrc = $(this).attr('src');
      const imageAlt = $(this).attr('alt');
      UIManager.showImageModal(imageSrc, imageAlt);
    });

    // Add click handlers for Add to Map buttons
    gallery.find('.add-to-map-btn').on('click', function(e) {
      e.preventDefault();
      const $button = $(this);
      const processingType = $button.data('target');
      
      if (!processingType) {
        Utils.log('warn', 'No processing type found in data-target attribute');
        return;
      }
      
      Utils.log('info', `LIDAR Raster gallery: Add to Map clicked for ${processingType}`);
      
      // Handle the add to map functionality for LIDAR raster images
      UIManager.handleProcessingResultsAddToMap(processingType, $button);
    });

    Utils.log('info', `Displayed ${availableRasters.length} LIDAR raster images in Processing Results gallery`);
  },

  /**
   * Reset the Processing Results gallery to show processing labels (text only)
   */
  resetProcessingGalleryToLabels() {
    const gallery = $('#gallery');
    
    // Reset to the original text-based gallery structure (no buttons)
    const labelItems = [
      { id: 'hillshade', label: 'Hillshade' },
      { id: 'slope', label: 'Slope' },
      { id: 'aspect', label: 'Aspect' },
      { id: 'color_relief', label: 'Color Relief' }
    ];

    const galleryHTML = labelItems.map(item => `
      <div class="gallery-item flex-shrink-0 w-64 h-48 bg-[#1a1a1a] border border-[#303030] rounded-lg flex flex-col hover:border-[#404040] transition-colors" id="cell-${item.id}">
        <div class="flex-1 flex items-center justify-center">
          <div class="text-white text-lg font-medium">${item.label}</div>
        </div>
      </div>
    `).join('');

    gallery.html(`
      <div class="flex gap-4 overflow-x-auto pb-4">
        ${galleryHTML}
      </div>
    `);

    Utils.log('info', 'Reset Processing Results gallery to text labels');
  },

  /**
   * Handle Add to Map button clicks in the Processing Results gallery
   * @param {string} processingType - Processing type (hillshade, slope, etc.)
   * @param {jQuery} $button - The clicked button element
   */
  handleProcessingResultsAddToMap(processingType, $button) {
    const regionName = $button.data('region-name');
    
    if (!regionName) {
      Utils.showNotification('No region selected for overlay', 'warning');
      return;
    }

    const displayName = this.getProcessingDisplayName(processingType);
    
    // Check if the overlay is already active
    const overlayKey = `LIDAR_RASTER_${regionName}_${processingType}`;
    const isActive = OverlayManager.mapOverlays[overlayKey] !== undefined;
    
    if (isActive) {
      // Remove overlay
      OverlayManager.removeOverlay(overlayKey);
      $button.text('Add to Map')
             .removeClass('bg-[#dc3545] hover:bg-[#c82333]')
             .addClass('bg-[#28a745] hover:bg-[#218838]');
      Utils.showNotification(`Removed ${displayName} overlay from map`, 'success');
    } else {
      // Add overlay
      $button.text('Remove from Map')
             .removeClass('bg-[#28a745] hover:bg-[#218838]')
             .addClass('bg-[#dc3545] hover:bg-[#c82333]');
      
      this.addLidarRasterOverlayToMap(regionName, processingType, displayName).then((success) => {
        if (!success) {
          // Revert button state if overlay failed
          $button.text('Add to Map')
                 .removeClass('bg-[#dc3545] hover:bg-[#c82333]')
                 .addClass('bg-[#28a745] hover:bg-[#218838]');
        }
      });
    }
  },

  /**
   * Initialize the Analysis tab when first activated
   */
  initializeAnalysisTab() {
    // Initialize analysis images array if not exists
    if (!this.analysisImages) {
      this.analysisImages = [];
    }
    
    // Update the main area to show initial state
    this.updateAnalysisMainArea();
    
    Utils.log('info', 'Analysis tab initialized');
  },

  /**
   * Update the selected region display for Analysis tab
   * @param {string} regionName - Name of the selected region
   */
  updateAnalysisSelectedRegion(regionName) {
    $('#analysis-selected-region-name').text(regionName);
    
    // Update global region selector if not already updated
    if (this.globalSelectedRegion !== regionName) {
      this.updateGlobalRegionSelector(regionName);
    }
    
    // Load images for the selected region
    this.loadAnalysisImages(regionName);
    
    Utils.log('info', `Analysis tab region updated: ${regionName}`);
  },

  /**
   * Load available images for a region in the Analysis tab
   * @param {string} regionName - Name of the region
   */
  async loadAnalysisImages(regionName) {
    try {
      const response = await fetch(`/api/regions/${encodeURIComponent(regionName)}/images`);
      
      if (!response.ok) {
        throw new Error(`Failed to load images: ${response.status}`);
      }
      
      const data = await response.json();
      // The API returns {images: [...], region_name: "...", total_images: 3}
      // so we need to access the images array
      const images = data.images || [];
      this.displayAnalysisImages(images);
      
    } catch (error) {
      Utils.log('error', 'Error loading analysis images:', error);
      $('#analysis-images-list').html(`
        <div class="text-[#dc3545] text-sm text-center py-4">
          Error loading images: ${error.message}
        </div>
      `);
    }
  },

  /**
   * Display images in the Analysis tab
   * @param {Array} images - Array of image objects
   */
  displayAnalysisImages(images) {
    const imagesList = $('#analysis-images-list');
    
    if (!images || images.length === 0) {
      imagesList.html(`
        <div class="text-[#666] text-sm text-center py-8">
          <div class="mb-2">No images available for this region</div>
          <div class="text-xs">Select a region with processed data to view available images</div>
        </div>
      `);
      return;
    }

    // Create image gallery using similar style to satellite images
    const imageItems = images.map(image => {
      // Determine image type and color
      let imageType = 'Unknown';
      let typeColor = '#666';
      let typeIcon = '📄';
      
      if (image.type === 'lidar') {
        imageType = 'LiDAR';
        typeColor = '#28a745';
        typeIcon = '🏔️';
      } else if (image.type === 'sentinel2') {
        imageType = 'Sentinel-2';
        typeColor = '#007bff';
        typeIcon = '🛰️';
      }
      
      // Get processing type display
      const processingType = image.processing_type || 'Unknown';
      
      return `
        <div class="gallery-item bg-[#1a1a1a] border border-[#303030] rounded-lg overflow-hidden hover:border-[#404040] transition-colors">
          <div class="relative w-full h-48">
            <img src="/${image.path}" 
                 alt="${this.getImageDisplayName(image.name)}" 
                 class="w-full h-full object-cover cursor-pointer"
                 title="Click to view larger image">
            <div class="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ${typeIcon} ${imageType}
            </div>
            <div class="absolute top-2 right-2 bg-opacity-75 text-white text-xs px-2 py-1 rounded"
                 style="background-color: ${typeColor};">
              ${processingType}
            </div>
            <div class="absolute bottom-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ${image.size || 'Unknown size'}
            </div>
          </div>
          <div class="p-3">
            <button class="add-to-analysis-btn w-full bg-[#28a745] hover:bg-[#218838] text-white px-3 py-2 text-sm font-medium rounded transition-colors" 
                    data-image-path="${image.path}" 
                    data-image-name="${image.name}"
                    data-image-type="${imageType}"
                    data-processing-type="${processingType}">
              Add to Analysis
            </button>
          </div>
        </div>
      `;
    }).join('');

    // Display in a responsive grid layout like the Map tab gallery
    imagesList.html(`
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        ${imageItems}
      </div>
    `);

    // Add event handlers for "Add to Analysis" buttons
    $('.add-to-analysis-btn').on('click', (e) => {
      const $button = $(e.target);
      const imagePath = $button.data('image-path');
      const imageName = $button.data('image-name');
      const imageType = $button.data('image-type');
      const processingType = $button.data('processing-type');
      
      this.addImageToAnalysis(imagePath, imageName, imageType, processingType);
    });

    // Add event handlers for image click to show larger view
    $('.gallery-item img').on('click', function() {
      const imageSrc = $(this).attr('src');
      const imageAlt = $(this).attr('alt');
      UIManager.showImageModal(imageSrc, imageAlt);
    });
  },

  /**
   * Get display name for an image
   * @param {string} imageName - Original image name
   * @returns {string} Display-friendly name
   */
  getImageDisplayName(imageName) {
    // Remove file extension and format the name
    const nameWithoutExt = imageName.replace(/\.(png|jpg|jpeg|tif|tiff)$/i, '');
    
    // Convert underscores to spaces and capitalize
    return nameWithoutExt
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  },

  /**
   * Add an image to the analysis
   * @param {string} imagePath - Path to the image
   * @param {string} imageName - Name of the image
   * @param {string} imageType - Type of image (LiDAR, Sentinel-2, etc.)
   * @param {string} processingType - Processing type (Hillshade, NDVI, etc.)
   */
  addImageToAnalysis(imagePath, imageName, imageType = 'Unknown', processingType = 'Unknown') {
    Utils.log('info', `Adding image to analysis: ${imageName} (${imageType} - ${processingType})`);
    
    try {
      // Initialize analysis images array if not exists
      if (!this.analysisImages) {
        this.analysisImages = [];
      }
      
      // Check if image is already in analysis
      const existingIndex = this.analysisImages.findIndex(img => img.path === imagePath);
      if (existingIndex !== -1) {
        Utils.showNotification(`${this.getImageDisplayName(imageName)} is already in analysis`, 'warning');
        return;
      }
      
      // Add image to analysis
      const imageData = {
        name: imageName,
        path: imagePath,
        displayName: this.getImageDisplayName(imageName),
        imageType: imageType,
        processingType: processingType,
        addedAt: new Date().toISOString()
      };
      
      this.analysisImages.push(imageData);
      
      // Update the analysis main area
      this.updateAnalysisMainArea();
      
      // Update the button state
      const button = $(`.add-to-analysis-btn[data-image-path="${imagePath}"]`);
      button.text('Added ✓')
            .removeClass('bg-[#28a745] hover:bg-[#218838]')
            .addClass('bg-[#6c757d] hover:bg-[#5a6268]')
            .prop('disabled', true);
      
      Utils.showNotification(`Added ${this.getImageDisplayName(imageName)} to analysis`, 'success');
      
    } catch (error) {
      Utils.log('error', 'Error adding image to analysis:', error);
      Utils.showNotification('Failed to add image to analysis', 'error');
    }
  },

  /**
   * Update the analysis main area with selected images
   */
  updateAnalysisMainArea() {
    const mainArea = $('#analysis-main-canvas');
    
    if (!this.analysisImages || this.analysisImages.length === 0) {
      mainArea.html(`
        <div class="flex items-center justify-center h-full text-[#666]">
          <div class="text-center">
            <div class="text-xl mb-2">No images selected for analysis</div>
            <div class="text-sm">Select images from the left panel to begin analysis</div>
          </div>
        </div>
      `);
      return;
    }
    
    // Create image gallery for analysis
    const imageItems = this.analysisImages.map((image, index) => {
      // Determine type icon and color
      let typeIcon = '📄';
      let typeColor = '#666';
      
      if (image.imageType === 'LiDAR') {
        typeIcon = '🏔️';
        typeColor = '#28a745';
      } else if (image.imageType === 'Sentinel-2') {
        typeIcon = '🛰️';
        typeColor = '#007bff';
      }
      
      return `
        <div class="analysis-image-card bg-[#1a1a1a] border border-[#404040] rounded-lg overflow-hidden hover:border-[#00bfff] transition-colors">
          <div class="flex">
            <div class="relative w-64 h-40 flex-shrink-0">
              <img src="/${image.path}" 
                   alt="${image.displayName}" 
                   class="w-full h-full object-cover cursor-pointer"
                   title="Click to view larger image">
              <div class="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                ${typeIcon} ${image.imageType || 'Unknown'}
              </div>
              <div class="absolute top-2 right-8 bg-opacity-75 text-white text-xs px-2 py-1 rounded"
                   style="background-color: ${typeColor};">
                ${image.processingType || 'Unknown'}
              </div>
              <button class="remove-from-analysis absolute top-2 right-2 bg-[#dc3545] hover:bg-[#c82333] text-white rounded-full w-6 h-6 flex items-center justify-center text-xs" 
                      data-index="${index}" title="Remove from analysis">
                ×
              </button>
            </div>
            <div class="flex-1 p-4 flex flex-col justify-center">
              <div class="text-white text-lg font-medium mb-2">${image.displayName}</div>
              <div class="text-[#ababab] text-sm mb-2">${image.imageType || 'Unknown'} • ${image.processingType || 'Unknown'}</div>
              <div class="text-[#ababab] text-sm">Added: ${new Date(image.addedAt).toLocaleString()}</div>
            </div>
          </div>
        </div>
      `;
    }).join('');
    
    const analysisContent = `
      <div class="h-full flex flex-col">
        <div class="flex items-center justify-between mb-4 p-4 bg-[#1a1a1a] border border-[#404040] rounded-lg">
          <h3 class="text-white text-lg font-medium">Analysis Images (${this.analysisImages.length})</h3>
          <button id="clear-analysis" class="bg-[#dc3545] hover:bg-[#c82333] text-white px-3 py-1 rounded text-sm font-medium transition-colors">
            Clear All
          </button>
        </div>
        <div class="flex-1 overflow-auto">
          <div class="space-y-4 p-4">
            ${imageItems}
          </div>
        </div>
      </div>
    `;
    
    mainArea.html(analysisContent);
    
    // Add event handlers
    $('.remove-from-analysis').on('click', (e) => {
      const index = parseInt($(e.target).data('index'));
      this.removeImageFromAnalysis(index);
    });
    
    $('#clear-analysis').on('click', () => {
      this.clearAnalysis();
    });
  },

  /**
   * Remove an image from analysis
   * @param {number} index - Index of the image to remove
   */
  removeImageFromAnalysis(index) {
    if (!this.analysisImages || index < 0 || index >= this.analysisImages.length) {
      return;
    }
    
    const removedImage = this.analysisImages.splice(index, 1)[0];
    
    // Re-enable the "Add to Analysis" button
    const button = $(`.add-to-analysis-btn[data-image-path="${removedImage.path}"]`);
    button.text('Add to Analysis')
          .removeClass('bg-[#6c757d] hover:bg-[#5a6268]')
          .addClass('bg-[#28a745] hover:bg-[#218838]')
          .prop('disabled', false);
    
    // Update the main area
    this.updateAnalysisMainArea();
    
    Utils.showNotification(`Removed ${removedImage.displayName} from analysis`, 'info');
  },

  /**
   * Clear all images from analysis
   */
  clearAnalysis() {
    if (!this.analysisImages || this.analysisImages.length === 0) {
      return;
    }
    
    // Re-enable all "Add to Analysis" buttons
    this.analysisImages.forEach(image => {
      const button = $(`.add-to-analysis-btn[data-image-path="${image.path}"]`);
      button.text('Add to Analysis')
            .removeClass('bg-[#6c757d] hover:bg-[#5a6268]')
            .addClass('bg-[#28a745] hover:bg-[#218838]')
            .prop('disabled', false);
    });
    
    // Clear the analysis images array
    this.analysisImages = [];
    
    // Update the main area
    this.updateAnalysisMainArea();
    
    Utils.showNotification('Analysis cleared', 'info');
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
      'color_relief': 'Color Relief'
    };
    
    return displayNames[processingType] || processingType.charAt(0).toUpperCase() + processingType.slice(1);
  },

  /**
   * Get color scheme for processing type
   * @param {string} processingType - Processing type
   * @returns {string} Color code for the processing type
   */
  getProcessingColor(processingType) {
    const colorSchemes = {
      'laz_to_dem': '#8B4513',        // Brown for DEM
      'dtm': '#8B4513',               // Brown for DTM
      'dsm': '#228B22',               // Forest Green for DSM
      'chm': '#32CD32',               // Lime Green for CHM
      'hillshade': '#696969',         // Dim Gray for Hillshade
      'hillshade_315_45_08': '#808080', // Gray for Hillshade 315°
      'hillshade_225_45_08': '#A9A9A9', // Dark Gray for Hillshade 225°
      'slope': '#FF6347',             // Tomato for Slope
      'aspect': '#4169E1',            // Royal Blue for Aspect
      'color_relief': '#FF8C00'       // Dark Orange for Color Relief
    };
    
    return colorSchemes[processingType] || '#6c757d'; // Default gray
  },

  /**
   * Add LIDAR raster overlay to map
   * @param {string} regionName - Name of the region
   * @param {string} processingType - Processing type (hillshade, slope, etc.)
   * @param {string} displayName - Display name for notifications
   * @returns {Promise<boolean>} Promise resolving to success status
   */
  async addLidarRasterOverlayToMap(regionName, processingType, displayName) {
    try {
      Utils.log('info', `Adding ${displayName} overlay for region ${regionName}`);

      // Fetch overlay data from the raster API
      const response = await fetch(`/api/overlay/raster/${regionName}/${processingType}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch overlay data: ${response.status}`);
      }

      const overlayData = await response.json();
      
      if (!overlayData.success || !overlayData.image_data || !overlayData.bounds) {
        throw new Error('Invalid overlay data received from server');
      }

      // Convert bounds to Leaflet format [[south, west], [north, east]]
      const bounds = [
        [overlayData.bounds.south, overlayData.bounds.west],
        [overlayData.bounds.north, overlayData.bounds.east]
      ];

      // Create the overlay key
      const overlayKey = `LIDAR_RASTER_${regionName}_${processingType}`;
      
      // Create image data URL
      const imageDataUrl = `data:image/png;base64,${overlayData.image_data}`;
      
      // Add the overlay using OverlayManager
      const success = OverlayManager.addImageOverlay(overlayKey, imageDataUrl, bounds, {
        opacity: 0.7,
        interactive: false
      });

      if (success) {
        Utils.showNotification(`Added ${displayName} overlay to map`, 'success');
        Utils.log('info', `Successfully added ${displayName} overlay for region ${regionName}`);
        return true;
      } else {
        throw new Error('Failed to add overlay to map');
      }

    } catch (error) {
      Utils.log('error', `Failed to add ${displayName} overlay for region ${regionName}:`, error);
      Utils.showNotification(`Failed to add ${displayName} overlay: ${error.message}`, 'error');
      return false;
    }
  },

  /**
   * Add Sentinel-2 overlay to map
   * @param {string} regionBand - Region and band identifier (e.g., "region_xxx_RED_B04")
   * @param {string} bType - Band type for display (e.g., "Red", "NIR", "NDVI")
   * @returns {Promise<boolean>} Promise resolving to success status
   */
  async addSentinel2OverlayToMap(regionBand, bType) {
    try {
      Utils.log('info', `Adding ${bType} Sentinel-2 overlay for ${regionBand}`);

      // Fetch overlay data from the Sentinel-2 API
      const response = await fetch(`/api/overlay/sentinel2/${regionBand}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch Sentinel-2 overlay data: ${response.status}`);
      }

      const overlayData = await response.json();
      
      if (!overlayData.bounds || !overlayData.image_data) {
        throw new Error('Invalid Sentinel-2 overlay data received from server');
      }

      // Convert bounds to Leaflet format [[south, west], [north, east]]
      const bounds = [
        [overlayData.bounds.south, overlayData.bounds.west],
        [overlayData.bounds.north, overlayData.bounds.east]
      ];

      // Create the overlay key
      const overlayKey = `SENTINEL2_${regionBand}`;
      
      // Create image data URL
      const imageDataUrl = `data:image/png;base64,${overlayData.image_data}`;
      
      // Add the overlay using OverlayManager
      const success = OverlayManager.addImageOverlay(overlayKey, imageDataUrl, bounds, {
        opacity: 0.7,
        interactive: false
      });

      if (success) {
        Utils.showNotification(`Added ${bType} Sentinel-2 overlay to map`, 'success');
        Utils.log('info', `Successfully added ${bType} Sentinel-2 overlay for ${regionBand}`);
        return true;
      } else {
        throw new Error('Failed to add Sentinel-2 overlay to map');
      }

    } catch (error) {
      Utils.log('error', `Failed to add ${bType} Sentinel-2 overlay for ${regionBand}:`, error);
      Utils.showNotification(`Failed to add ${bType} Sentinel-2 overlay: ${error.message}`, 'error');
      return false;
    }
  },

  /**
   * Get combined data (both elevation and satellite data)
   */
  async getCombinedData() {
    Utils.log('info', 'Get Combined Data button clicked');

    // Get coordinates from input fields
    let lat = $('#lat-input').val();
    let lng = $('#lng-input').val();
    const regionName = $('#region-name-input').val();

    // If no coordinates are set, use Portland, Oregon as default
    if (!lat || !lng || lat === '' || lng === '') {
      lat = 45.5152;  // Portland, Oregon
      lng = -122.6784;

      // Update the input fields
      $('#lat-input').val(lat);
      $('#lng-input').val(lng);

      // Center map on the location
      MapManager.setView(lat, lng, 12);

      Utils.showNotification('Using Portland, Oregon coordinates for combined data acquisition', 'info');
    }

    // Validate coordinates
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);

    if (!Utils.isValidCoordinate(latNum, lngNum)) {
      Utils.showNotification('Invalid coordinates. Please enter valid latitude and longitude values.', 'error');
      return;
    }

    try {
      this.showProgress('📊 Acquiring combined elevation and satellite data...');

      // Start WebSocket connection for progress updates
      if (window.WebSocketManager) {
        WebSocketManager.connect();
      }

      // Prepare region name for both acquisitions
      const effectiveRegionName = regionName && regionName.trim() !== '' ? regionName.trim() : null;

      // Step 1: Acquire elevation data
      this.updateProgress(25, 'Acquiring elevation data...');
      
      const elevationRequest = {
        lat: latNum,
        lng: lngNum,
        buffer_km: 2.0
      };

      if (effectiveRegionName) {
        elevationRequest.region_name = effectiveRegionName;
      }

      const elevationResponse = await fetch('/api/elevation/download-coordinates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(elevationRequest)
      });

      let elevationResult = null;
      if (elevationResponse.ok) {
        elevationResult = await elevationResponse.json();
        if (elevationResult.success) {
          Utils.log('info', 'Elevation data acquisition completed');
          this.updateProgress(50, 'Elevation data acquired. Starting satellite data download...');
        } else {
          Utils.log('warn', 'Elevation data acquisition failed:', elevationResult.error);
        }
      } else {
        Utils.log('warn', 'Elevation data acquisition request failed:', elevationResponse.status);
      }

      // Step 2: Acquire Sentinel-2 satellite data
      const sentinelRequest = {
        lat: latNum,
        lng: lngNum,
        buffer_km: 5.0,  // Larger buffer for satellite data
        bands: ['B04', 'B08']  // Red and NIR bands
      };

      if (effectiveRegionName) {
        sentinelRequest.region_name = effectiveRegionName;
      }

      this.updateProgress(75, 'Downloading Sentinel-2 satellite data...');

      const sentinelResponse = await fetch('/api/download-sentinel2', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sentinelRequest)
      });

      let sentinelResult = null;
      if (sentinelResponse.ok) {
        sentinelResult = await sentinelResponse.json();
        if (sentinelResult.success) {
          Utils.log('info', 'Sentinel-2 data download completed');
          this.updateProgress(90, 'Converting satellite images...');

          // Auto-convert Sentinel-2 images if we have a region name
          const sentinelRegionName = sentinelResult.metadata?.region_name || effectiveRegionName;
          if (sentinelRegionName) {
            await this.convertAndDisplaySentinel2(sentinelRegionName);
          }
        } else {
          Utils.log('warn', 'Sentinel-2 data download failed:', sentinelResult.error);
        }
      } else {
        Utils.log('warn', 'Sentinel-2 data download request failed:', sentinelResponse.status);
      }

      // Step 3: Summarize results
      this.updateProgress(100, 'Combined data acquisition completed!');

      const elevationSuccess = elevationResult?.success || false;
      const sentinelSuccess = sentinelResult?.success || false;

      if (elevationSuccess && sentinelSuccess) {
        Utils.showNotification(
          'Successfully acquired both elevation and satellite data!',
          'success'
        );
      } else if (elevationSuccess || sentinelSuccess) {
        const acquiredData = elevationSuccess ? 'elevation' : 'satellite';
        const failedData = elevationSuccess ? 'satellite' : 'elevation';
        Utils.showNotification(
          `Partially successful: ${acquiredData} data acquired, ${failedData} data failed`,
          'warning'
        );
      } else {
        throw new Error('Both elevation and satellite data acquisition failed');
      }

      // Refresh file list and region data
      if (window.FileManager && window.FileManager.loadFiles) {
        setTimeout(() => {
          FileManager.loadFiles();
        }, 1000);
      }

      // If we have a region name, try to display both elevation and satellite data
      if (effectiveRegionName || sentinelResult?.metadata?.region_name) {
        const displayRegionName = effectiveRegionName || sentinelResult.metadata.region_name;
        setTimeout(() => {
          this.displayLidarRasterForRegion(displayRegionName);
          this.displaySentinel2ImagesForRegion(displayRegionName);
        }, 1500);
      }

    } catch (error) {
      Utils.log('error', 'Error in combined data acquisition:', error);
      Utils.showNotification(`Error acquiring combined data: ${error.message}`, 'error');
    } finally {
      this.hideProgress();
    }
  },

  /**
   * Parse and display coordinates from the coordinate input field
   */
  parseAndDisplayCoordinates() {
    const coordString = $('#goto-coordinates-input').val().trim();
    
    if (!coordString) {
      // Clear all fields if input is empty
      $('#goto-lat-input').val('');
      $('#goto-lng-input').val('');
      $('#goto-region-name').val('');
      return;
    }

    const parsed = Utils.parseCoordinateString(coordString);
    
    if (parsed) {
      // Update the latitude and longitude fields
      $('#goto-lat-input').val(parsed.lat.toFixed(6));
      $('#goto-lng-input').val(parsed.lng.toFixed(6));
      
      // Generate and display region name
      const regionName = Utils.generateRegionName(parsed.lat, parsed.lng);
      $('#goto-region-name').val(regionName);
      
      // Visual feedback - green border for valid input
      $('#goto-coordinates-input').removeClass('border-red-500').addClass('border-green-500');
      
      Utils.log('info', `Parsed coordinates: ${parsed.lat}, ${parsed.lng} -> Region: ${regionName}`);
    } else {
      // Clear parsed fields for invalid input
      $('#goto-lat-input').val('');
      $('#goto-lng-input').val('');
      $('#goto-region-name').val('');
      
      // Visual feedback - red border for invalid input
      $('#goto-coordinates-input').removeClass('border-green-500').addClass('border-red-500');
    }
  },

  /**
   * Go to coordinates from input fields
   */
  goToCoordinates() {
    // First try to parse from the coordinate string input
    const coordString = $('#goto-coordinates-input').val().trim();
    let lat, lng;
    
    if (coordString) {
      const parsed = Utils.parseCoordinateString(coordString);
      if (parsed) {
        lat = parsed.lat;
        lng = parsed.lng;
      } else {
        Utils.showNotification('Please enter coordinates in a valid format (e.g., "8.845°S, 67.255°W")', 'warning');
        return;
      }
    } else {
      // Fall back to individual lat/lng inputs
      lat = parseFloat($('#goto-lat-input').val());
      lng = parseFloat($('#goto-lng-input').val());
    }

    if (!Utils.isValidCoordinate(lat, lng)) {
      Utils.showNotification('Please enter valid latitude and longitude values', 'warning');
      return;
    }

    try {
      // Set map view to the coordinates
      MapManager.setView(lat, lng, 13);
      
      // Update the coordinate display inputs in the Get Data section
      $('#lat-input').val(lat);
      $('#lng-input').val(lng);
      
      // Generate region name and update Get Data section
      const regionName = Utils.generateRegionName(lat, lng);
      $('#region-name-input').val(regionName);
      
      // Update the parsed coordinate display fields
      $('#goto-lat-input').val(lat.toFixed(6));
      $('#goto-lng-input').val(lng.toFixed(6));
      $('#goto-region-name').val(regionName);
      
      // Add a temporary marker
      MapManager.addMarker(lat, lng, {
        popup: `Go to Location<br>Lat: ${lat}<br>Lng: ${lng}<br>Region: ${regionName}`
      });

      Utils.showNotification(`Map centered on coordinates: ${lat}, ${lng}<br>Region: ${regionName}`, 'success');
      Utils.log('info', `Map navigated to coordinates: ${lat}, ${lng}, Region: ${regionName}`);

    } catch (error) {
      Utils.log('error', 'Failed to navigate to coordinates', error);
      Utils.showNotification('Failed to navigate to coordinates', 'error');
    }
  },

  /**
   * Go to preset location
   * @param {number} lat - Latitude
   * @param {number} lng - Longitude
   * @param {string} locationName - Name of the location
   */
  goToPresetLocation(lat, lng, locationName) {
    try {
      // Set map view to the preset location
      MapManager.setView(lat, lng, 10);
      
      // Update the coordinate inputs in both sections
      $('#goto-lat-input').val(lat);
      $('#goto-lng-input').val(lng);
      $('#lat-input').val(lat);
      $('#lng-input').val(lng);
      
      // Add a marker for the preset location
      MapManager.addMarker(lat, lng, {
        popup: `${locationName}<br>Lat: ${lat}<br>Lng: ${lng}`
      });

      Utils.showNotification(`Map centered on ${locationName}`, 'success');
      Utils.log('info', `Map navigated to preset location: ${locationName} (${lat}, ${lng})`);

    } catch (error) {
      Utils.log('error', `Failed to navigate to ${locationName}`, error);
      Utils.showNotification(`Failed to navigate to ${locationName}`, 'error');
    }
  },

  /**
   * Show progress modal with a message
   * @param {string} message - Progress message to display
   */
  showProgress(message) {
    const modal = $('#progress-modal');
    const title = $('#progress-title');
    const status = $('#progress-status');
    const progressBar = $('#progress-bar');
    const details = $('#progress-details');

    if (title.length) title.text('Processing...');
    if (status.length) status.text(message || 'Initializing...');
    if (progressBar.length) progressBar.css('width', '0%');
    if (details.length) details.text('');

    modal.fadeIn();
    Utils.log('info', `Progress modal shown: ${message}`);
  },

  /**
   * Update progress modal with percentage and status
   * @param {number} percentage - Progress percentage (0-100)
   * @param {string} status - Status message
   * @param {string} details - Optional detailed message
   */
  updateProgress(percentage, status, details) {
    const progressBar = $('#progress-bar');
    const statusEl = $('#progress-status');
    const detailsEl = $('#progress-details');

    if (progressBar.length) {
      progressBar.css('width', `${percentage}%`);
    }
    
    if (status && statusEl.length) {
      statusEl.text(status);
    }
    
    if (details && detailsEl.length) {
      detailsEl.text(details);
    }

    Utils.log('debug', `Progress updated: ${percentage}% - ${status}`);
  },

  /**
   * Hide progress modal
   */
  hideProgress() {
    const modal = $('#progress-modal');
    modal.fadeOut();
    Utils.log('info', 'Progress modal hidden');
  }
};
