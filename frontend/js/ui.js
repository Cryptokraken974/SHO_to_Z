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
    this.initializeModals(); // General modals
    this.initializeImageModalEventHandlers(); // Specific for image modal
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
   * @param {string} tabName - Name of the tab to switch to ('map', 'geotiff-tools', or 'analysis')
   */
  switchTab(tabName) {
    // Update tab buttons
    $('.tab-btn').removeClass('active').addClass('text-[#ababab]').removeClass('text-white').removeClass('border-[#00bfff]').addClass('border-transparent');
    $(`.tab-btn[data-tab="${tabName}"]`).addClass('active').removeClass('text-[#ababab]').addClass('text-white').removeClass('border-transparent').addClass('border-[#00bfff]');

    // Update tab content
    $('.tab-content').addClass('hidden');
    $(`#${tabName}-tab`).removeClass('hidden');

    // Initialize specific tabs if switching to them for the first time
    if (tabName === 'analysis') {
      this.initializeAnalysisTab();
      
      // Sync region selection if one is selected globally
      const currentRegion = this.globalSelectedRegion || FileManager.getSelectedRegion();
      if (currentRegion) {
        // Load analysis images for the current region
        this.loadAnalysisImages(currentRegion);
      }
    } else if (tabName === 'geotiff-tools') {
      this.initializeGeoTiffTab();
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
   * @param {string} processingRegion - Region name for processing API calls
   */
  handleGlobalRegionSelection(regionName, coords = null, processingRegion = null, filePath = null) {
    // Update global selector
    this.updateGlobalRegionSelector(regionName);
    
    // Update FileManager's selected region
    // This will also trigger the lat/lon update if it's a LAZ file due to changes in FileManager.selectRegion
    FileManager.selectRegion(regionName, coords, processingRegion, filePath);

    // Switch to Map tab
    this.switchTab('map');
    
    // Set map view and pin if coordinates are available
    // Note: FileManager.selectRegion already handles map view and pin if coords are provided.
    // Redundant calls here might occur but should be harmless or could be optimized.
    if (coords && Utils.isValidCoordinate(coords.lat, coords.lng)) {
      MapManager.setView(coords.lat, coords.lng, 13);
      // FileManager.updateLocationPin is called within FileManager.selectRegion
    }
    
    // Clear satellite gallery immediately when switching regions to prevent showing old images
    const gallery = $('#satellite-gallery');
    if (gallery.length) {
      gallery.empty();
      // Add a loading message to provide immediate visual feedback
      gallery.html('<div class="loading-message text-center text-[#666] p-8">🔄 Switching to new region...</div>');
      Utils.log('info', '🗑️ Cleared satellite gallery for new region selection (including any downloaded images)');
    }
    
    // Load satellite images and LIDAR data for the region
    // ALWAYS load both Sentinel-2 images AND LiDAR data regardless of file type
    // Use processing region name for consistent Sentinel-2 calls
    const sentinel2RegionName = processingRegion || regionName;
    Utils.log('info', `🛰️ === HANDLESELECTION CALLING SENTINEL-2 ===`);
    Utils.log('info', `📍 Display Name: ${regionName}`);
    Utils.log('info', `📍 Processing Region: ${processingRegion}`);
    Utils.log('info', `📍 Using Region Name: ${sentinel2RegionName}`);
    Utils.log('info', `📍 File Path: ${filePath}`);
    this.displaySentinel2ImagesForRegion(sentinel2RegionName);
    
    this.displayLidarRasterForRegion(regionName);
    
    // Show success notification
    Utils.showNotification(`Selected Region: ${regionName}`, 'success', 2000);
    
    Utils.log('info', `Global region selection completed: ${regionName} (processing region: ${processingRegion}, path: ${filePath})`, { coords });
  },

  /**
   * Initialize accordion functionality
   */
  initializeAccordions() {
    // Region accordion
    $('#region-accordion').on('click', () => {
      this.toggleAccordion('region');
    });

    // Get Data accordion (renamed from Test)
    $('#get-data-accordion').on('click', () => {
      this.toggleAccordion('get-data');
    });

    // Generate Rasters accordion
    $('#generate-rasters-accordion').on('click', () => {
      this.toggleAccordion('generate-rasters');
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

    // GeoTiff Tools tab accordions
    $('#geotiff-files-accordion').on('click', () => {
      this.toggleAccordion('geotiff-files');
    });

    $('#geotiff-load-files-accordion').on('click', () => {
      this.toggleAccordion('geotiff-load-files');
    });

    $('#geotiff-tools-accordion').on('click', () => {
      this.toggleAccordion('geotiff-tools');
    });

    $('#geotiff-processing-accordion').on('click', () => {
      this.toggleAccordion('geotiff-processing');
    });

    $('#geotiff-info-accordion').on('click', () => {
      this.toggleAccordion('geotiff-info');
    });

    Utils.log('info', 'Accordions initialized');
  },

  /**
   * Initialize GeoTiff tab with proper accordion states
   */
  initializeGeoTiffTab() {
    // Set default accordion states for GeoTiff tab
    // Load files accordion should be open by default
    const loadFilesContent = $('#geotiff-load-files-content');
    const loadFilesArrow = $('#geotiff-load-files-accordion .accordion-arrow');
    
    if (loadFilesContent.hasClass('collapsed')) {
      loadFilesContent.removeClass('collapsed');
      loadFilesArrow.css('transform', 'rotate(0deg)');
    }

    // Ensure other accordions are properly initialized
    const accordionsToCollapse = ['geotiff-files', 'geotiff-tools', 'geotiff-processing', 'geotiff-info'];
    accordionsToCollapse.forEach(accordionType => {
      const content = $(`#${accordionType}-content`);
      const arrow = $(`#${accordionType}-accordion .accordion-arrow`);
      
      if (!content.hasClass('collapsed')) {
        content.addClass('collapsed');
        arrow.css('transform', 'rotate(-90deg)');
      }
    });

    Utils.log('info', 'GeoTiff tab initialized with default accordion states');
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
      console.log('🔍 Select Region button clicked - Looking up folders:');
      console.log('📁 Primary folder: input/');
      console.log('📊 Source filter: input (only input folder will be searched)');
      
      FileManager.loadFiles('input'); // Only load from input folder
      $('#file-modal').fadeIn();
      // Update modal title to indicate input-only selection
      $('#file-modal h4').text('Select Region (Input Folder)');
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

    // Generate Rasters - Single Button for All Processing
    $('#generate-all-rasters-btn').on('click', () => {
      ProcessingManager.processAllRasters();
    });

    // Cancel All Rasters Processing
    $('#cancel-all-rasters-btn').on('click', () => {
      ProcessingManager.cancelAllRasterProcessing();
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
      // Reset modal title to default
      $('#file-modal h4').text('Select Region');
      // Hide the delete button when modal is closed
      $('#delete-region-btn').addClass('hidden').prop('disabled', false).text('Delete Region');
    });

    // File item selection is now handled in FileManager.displayRegions()
    
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
      const selectedItem = $('.file-item.selected');
      if (selectedItem.length === 0) {
        Utils.showNotification('Please select a region first', 'warning');
        return;
      }

      const regionName = selectedItem.data('region-name'); // Display name
      let processingRegion = selectedItem.data('processing-region'); // Processing region name
      const filePath = selectedItem.data('file-path'); // Get file path

      // Get coordinates from the stored data
      const coords = selectedItem.data('coords');
      
      // Make sure processing region is not just "LAZ" (which would cause problems)
      if (processingRegion === "LAZ") {
        console.warn("⚠️ Processing region is 'LAZ', which is likely incorrect. Using display name instead.");
        processingRegion = regionName;
      }

      // Check which type of selection this is
      const isForGlobal = $('#file-modal').data('for-global');
      const isForAnalysis = $('#file-modal').data('for-analysis');
      
      if (isForGlobal) {
        // Handle global region selection - this includes API calls
        // UIManager.handleGlobalRegionSelection(regionName, coords, processingRegion); // Original
        // For now, let's assume handleGlobalRegionSelection will internally call selectRegion or be updated separately
        // to handle filePath if it needs to directly trigger the lat/lon display.
        // The primary goal here is to ensure selectRegion gets the path.
        FileManager.selectRegion(regionName, coords, processingRegion, filePath); 
        // If handleGlobalRegionSelection itself needs the filePath for other reasons, it should be updated.
        // For now, we ensure that if it *results* in a selection that should show lat/lon,
        // the underlying selectRegion call (if made by handleGlobalRegionSelection or directly) has the path.
        // A more direct approach for global selection might be:
        UIManager.handleGlobalRegionSelection(regionName, coords, processingRegion, filePath);


        // Clear the flag
        $('#file-modal').removeData('for-global');
      } else if (isForAnalysis) {
        // Update Analysis tab
        UIManager.updateAnalysisSelectedRegion(regionName); // This likely doesn't need filePath for lat/lon inputs
        // Clear the flag
        $('#file-modal').removeData('for-analysis');
      } else {
        // Select the region using FileManager for Map tab - this includes API calls
        FileManager.selectRegion(regionName, coords, processingRegion, filePath);
      }
      
      // Close the modal
      $('#file-modal').fadeOut();
      // Reset modal title to default
      $('#file-modal h4').text('Select Region');
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

      // Use overlay service from factory
      const data = await overlays().getTestOverlayData(selectedRegion);

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
   * Test Sentinel-2 Images functionality (DEBUG ONLY)
   * Note: Sentinel-2 images normally load automatically when selecting a region.
   * This function is for testing/debugging coordinate and download functionality.
   */
  async testSentinel2() {
    Utils.log('info', '🧪 === STARTING SENTINEL-2 DEBUG TEST ===');
    
    // Log current region state for debugging
    Utils.log('info', '📊 Current region state:', {
      selectedRegion: FileManager.getSelectedRegion(),
      processingRegion: FileManager.getProcessingRegion(),
      regionPath: FileManager.getRegionPath()
    });
    
    // Check if Sentinel-2 images are already loaded for selected region
    if (FileManager.selectedRegion) {
      const existingImages = $('#satellite-gallery .gallery-item').length;
      if (existingImages > 0) {
        const proceed = confirm(`Sentinel-2 images are already loaded for ${FileManager.selectedRegion}. This test will download additional images. Continue?`);
        if (!proceed) {
          Utils.log('info', 'Test Sentinel-2 cancelled by user - images already loaded');
          return;
        }
      }
    }

    // Get coordinates from input fields
    let lat = $('#lat-input').val();
    let lng = $('#lng-input').val();
    let regionName = $('#region-name-input').val(); // Get region name

    // Check if we have a selected region but no coordinates in input fields
    if ((!lat || !lng || lat === '' || lng === '') && FileManager.selectedRegion) {
      // Try to get coordinates from the selected region
      const selectedItem = $(`.file-item[data-region-name="${FileManager.selectedRegion}"]`);
      let coords = null;
      
      // First try to get coordinates from stored data
      if (selectedItem.length && selectedItem.data('coords')) {
        coords = selectedItem.data('coords');
        Utils.log('info', `Found coordinates in selected item data:`, coords);
      }
      
      // If no coordinates in item data, try to extract from coordinate input fields that might have been set during region selection
      if (!coords && $('#lat-input').val() && $('#lng-input').val()) {
        const inputLat = parseFloat($('#lat-input').val());
        const inputLng = parseFloat($('#lng-input').val());
        if (Utils.isValidCoordinate(inputLat, inputLng)) {
          coords = { lat: inputLat, lng: inputLng };
          Utils.log('info', `Using coordinates from input fields: ${inputLat}, ${inputLng}`);
        }
      }
      
      // If we found valid coordinates, use them
      if (coords && coords.lat && coords.lng && Utils.isValidCoordinate(coords.lat, coords.lng)) {
        lat = coords.lat;
        lng = coords.lng;
        
        // Update the input fields
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        
        Utils.log('info', `Using coordinates from selected region ${FileManager.selectedRegion}: ${lat}, ${lng}`);
      } else {
        Utils.log('warn', `No valid coordinates found for selected region ${FileManager.selectedRegion}`);
      }
    }

    // If still no coordinates are set, use Portland, Oregon as default (good Sentinel-2 coverage)
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
    
    // Check if we have a selected LAZ file but no region name
    if (FileManager.selectedRegion && (!regionName || regionName.trim() === '')) {
      // Extract filename without extension from the selected region
      regionName = FileManager.selectedRegion.replace(/\.[^/.]+$/, '');
      // Update the region name input field
      $('#region-name-input').val(regionName);
      Utils.log('info', `Auto-filled region name from selected file: ${regionName}`);
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

      // Use satellite service from factory
      const result = await satellite().downloadSentinel2Data(requestBody);

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

      // Use satellite service from factory for Sentinel-2 conversion
      const result = await satellite().convertSentinel2ToPNG(regionName);

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
    
    // Clear previous images and loading message
    gallery.empty(); 
    Utils.log('info', '🗑️ Cleared satellite gallery before displaying converted images');

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
                    data-band-type="${bandType}"
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
    // Add comprehensive debugging to track all calls
    const caller = (new Error()).stack.split('\n')[2]?.trim() || 'unknown';
    Utils.log('info', `🛰️ === DISPLAY SENTINEL-2 IMAGES CALLED ===`);
    Utils.log('info', `📍 Region Name: ${regionName}`);
    Utils.log('info', `📞 Called from: ${caller}`);
    Utils.log('info', `📊 Current FileManager state:`, {
      selectedRegion: FileManager.getSelectedRegion(),
      processingRegion: FileManager.getProcessingRegion(),
      regionPath: FileManager.getRegionPath()
    });
    
    Utils.log('info', `Checking for Sentinel-2 images for region: ${regionName}`);

    // Clear the satellite gallery at the start to ensure fresh display
    const gallery = $('#satellite-gallery');
    if (gallery.length) {
      gallery.empty();
      // Add a loading message to provide visual feedback
      gallery.html('<div class="loading-message text-center text-[#666] p-8">🛰️ Loading Sentinel-2 images...</div>');
      Utils.log('info', '🗑️ Cleared satellite gallery and added loading message');
    }

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
          const overlayData = await satellite().getSentinel2Overlay(regionBand);

          if (overlayData && overlayData.image_data) {
            availableBands.push({
              band: band,
              bandType: this.getSentinel2BandDisplayName(band),
              overlayData: overlayData,
              regionName: regionName,
              filename: overlayData.filename || `${regionName}_${band}`
            });
            Utils.log('info', `Found ${band} data for region ${regionName}`);
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
        // Clear the satellite gallery and show a message
        const gallery = $('#satellite-gallery');
        if (gallery.length) {
          gallery.empty().html('<div class="no-files text-center text-[#666] p-8">No satellite images available for this region.</div>');
        }
        return;
      }

      // Display available Sentinel-2 images in the satellite gallery
      this.displaySentinel2BandsGallery(availableBands);
      Utils.log('info', `Displayed ${availableBands.length} Sentinel-2 images for region ${regionName}`);

    } catch (error) {
      Utils.log('error', `Error fetching Sentinel-2 images for region ${regionName}:`, error);
      // Clear the satellite gallery and show an error message
      const gallery = $('#satellite-gallery');
      if (gallery.length) {
        gallery.empty().html('<div class="no-files text-center text-[#666] p-8">Error loading satellite images for this region.</div>');
      }
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
    
    // Clear previous images and loading message
    gallery.empty(); 
    Utils.log('info', '🗑️ Cleared satellite gallery before displaying band images');

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
      // Processing types that match the new backend raster products
      const processingTypes = [
        'hs_red', 'hs_green', 'hs_blue',           // Individual hillshades
        'slope', 'aspect', 'color_relief', 'slope_relief',  // Other raster products
        'hillshade_rgb', 'tint_overlay', 'boosted_hillshade'  // Composite products
      ];
      const availableRasters = [];

      // Check each processing type for available raster data
      for (const processingType of processingTypes) {
        try {
          const overlayData = await overlays().getRasterOverlayData(regionName, processingType);
          
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

    // Start with the base gallery structure (all 8 vignettes)
    this.resetProcessingGalleryToLabels();

    // Update each vignette that has available data
    availableRasters.forEach(raster => {
      const { processingType, display, overlayData, regionName } = raster;
      const imageDataUrl = `data:image/png;base64,${overlayData.image_data}`;
      
      // Find the corresponding gallery cell
      const cell = $(`#cell-${processingType}`);
      
      if (cell.length) {
        // Update the cell content to show the image
        const cellContent = cell.find('.flex-1');
        cellContent.html(`
          <div class="relative w-full h-full">
            <img src="${imageDataUrl}" 
                 alt="${display}" 
                 class="processing-result-image cursor-pointer w-full h-full object-cover"
                 title="Click to view larger image">
            <div class="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ${display}
            </div>
            <div class="absolute top-2 right-2 bg-green-600 bg-opacity-75 text-white text-xs px-2 py-1 rounded">
              ✓ Ready
            </div>
          </div>
        `);

        // Add the "Add to Map" button below the image
        cell.append(`
          <button class="add-to-map-btn bg-[#28a745] hover:bg-[#218838] text-white px-3 py-1 rounded-b-lg text-sm font-medium transition-colors mt-1" 
                  data-target="${processingType}"
                  data-region-name="${regionName}">
            Add to Map
          </button>
        `);

        Utils.log('info', `Updated gallery cell for ${processingType}`);
      }
    });

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

    Utils.log('info', `Updated ${availableRasters.length} LIDAR raster images in Processing Results gallery`);
  },

  /**
   * Reset the Processing Results gallery to show processing labels (text only)
   */
  resetProcessingGalleryToLabels() {
    const gallery = $('#gallery');
    
    // Updated gallery items to match actual backend processing results
    const labelItems = [
      // Individual hillshades
      { id: 'hs_red', label: 'Hillshade Red', color: '#e74c3c' },
      { id: 'hs_green', label: 'Hillshade Green', color: '#27ae60' },
      { id: 'hs_blue', label: 'Hillshade Blue', color: '#3498db' },
      // Other raster products
      { id: 'slope', label: 'Slope', color: '#e17055' },
      { id: 'aspect', label: 'Aspect', color: '#00b894' },
      { id: 'color_relief', label: 'Color Relief', color: '#f39c12' },
      { id: 'slope_relief', label: 'Slope Relief', color: '#9b59b6' },
      // Composite products
      { id: 'hillshade_rgb', label: 'RGB Hillshade', color: '#fdcb6e' },
      { id: 'tint_overlay', label: 'Tint Overlay', color: '#e84393' },
      { id: 'boosted_hillshade', label: 'Boosted Hillshade', color: '#00cec9' }
    ];

    const galleryHTML = labelItems.map(item => `
      <div class="gallery-item flex-shrink-0 w-64 h-48 bg-[#1a1a1a] border border-[#303030] rounded-lg flex flex-col hover:border-[#404040] transition-colors" id="cell-${item.id}">
        <div class="flex-1 flex items-center justify-center">
          <div class="text-white text-lg font-medium" style="color: ${item.color}">${item.label}</div>
        </div>
      </div>
    `).join('');

    gallery.html(`
      <div class="flex gap-4 overflow-x-auto pb-4">
        ${galleryHTML}
      </div>
    `);

    Utils.log('info', 'Reset Processing Results gallery to show new hillshade and raster products');
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
    
    // Initialize the AnalysisManager if it exists and hasn't been initialized
    if (typeof AnalysisManager !== 'undefined' && !this.analysisManagerInitialized) {
      try {
        AnalysisManager.init();
        this.analysisManagerInitialized = true;
        Utils.log('info', 'AnalysisManager initialized');
      } catch (error) {
        Utils.log('error', 'Failed to initialize AnalysisManager:', error);
      }
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
      // Use region API client
      const data = await regions().getRegionImages(regionName);
      
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
            <div class="absolute top-2 right-8 bg-opacity-75 text-white text-xs px-2 py-1 rounded"
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
    const mainArea = $('#analysis-results-content');
    
    if (!this.analysisImages || this.analysisImages.length === 0) {
      mainArea.html(`
        <div class="text-[#ababab] text-center py-8">
          <i class="fas fa-chart-line text-4xl mb-3 text-[#404040]"></i>
          <p>Analysis results will be displayed here after running analysis tools</p>
          <p class="text-sm mt-2">Select an analysis tool from the sidebar to get started</p>
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
      // Legacy processing types
      'laz_to_dem': 'DEM',
      'dtm': 'DTM',
      'dsm': 'DSM',
      'chm': 'CHM',
      'hillshade': 'Hillshade',
      'hillshade_315_45_08': 'Hillshade 315°',
      'hillshade_225_45_08': 'Hillshade 225°',
      'tpi': 'TPI',
      'roughness': 'Roughness',
      
      // New hillshade products
      'hs_red': 'Hillshade Red',
      'hs_green': 'Hillshade Green', 
      'hs_blue': 'Hillshade Blue',
      
      // Raster products
      'slope': 'Slope',
      'aspect': 'Aspect',
      'color_relief': 'Color Relief',
      'slope_relief': 'Slope Relief',
      
      // Composite products
      'hillshade_rgb': 'RGB Hillshade',
      'tint_overlay': 'Tint Overlay',
      'boosted_hillshade': 'Boosted Hillshade'
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
      // Legacy processing types
      'laz_to_dem': '#8B4513',        // Brown for DEM
      'dtm': '#8B4513',               // Brown for DTM
      'dsm': '#228B22',               // Forest Green for DSM
      'chm': '#32CD32',               // Lime Green for CHM
      'hillshade': '#696969',         // Dim Gray for Hillshade
      'hillshade_315_45_08': '#808080', // Gray for Hillshade 315°
      'hillshade_225_45_08': '#A9A9A9', // Dark Gray for Hillshade 225°
      'tpi': '#0984e3',               // Blue for TPI
      'roughness': '#74b9ff',         // Light blue for Roughness
      
      // New hillshade products
      'hs_red': '#e74c3c',            // Red for Red Hillshade
      'hs_green': '#27ae60',          // Green for Green Hillshade
      'hs_blue': '#3498db',           // Blue for Blue Hillshade
      
      // Raster products
      'slope': '#e17055',             // Orange for Slope
      'aspect': '#00b894',            // Teal for Aspect
      'color_relief': '#f39c12',      // Orange for Color Relief
      'slope_relief': '#9b59b6',      // Purple for Slope Relief
      
      // Composite products
      'hillshade_rgb': '#fdcb6e',     // Yellow for RGB Hillshade
      'tint_overlay': '#e84393',      // Pink for Tint Overlay
      'boosted_hillshade': '#00cec9'  // Cyan for Boosted Hillshade
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

      // Use overlay API client for raster overlay data
      const overlayData = await overlays().getRasterOverlayData(regionName, processingType);
      
      if (!overlayData.success || !overlayData.image_data || !overlayData.bounds) {
        throw new Error('Invalid overlay data received from server');
      }

      // Check for optimization metadata
      const isOptimized = overlayData.is_optimized || false;
      const optimizationInfo = overlayData.optimization_info || null;

      // Log detailed coordinate information
      Utils.log('info', `Retrieved overlay data for ${regionName} - Bounds: N:${overlayData.bounds.north}, S:${overlayData.bounds.south}, E:${overlayData.bounds.east}, W:${overlayData.bounds.west}`);

      // Log optimization status
      if (isOptimized) {
        Utils.log('info', `✓ ${displayName} overlay is optimized for browser performance`);
        if (optimizationInfo) {
          Utils.log('info', `Optimization details:`, optimizationInfo);
        }
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
        // Create notification message with optimization status
        let notificationMessage = `Added ${displayName} overlay to map`;
        if (isOptimized) {
          notificationMessage += ' ✓ Optimized for browser performance';
        }
        
        Utils.showNotification(notificationMessage, 'success');
        Utils.log('info', `Successfully added ${displayName} overlay for region ${regionName} with coordinates: North: ${overlayData.bounds.north}, South: ${overlayData.bounds.south}, East: ${overlayData.bounds.east}, West: ${overlayData.bounds.west}`);
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

      // Use satellite service from factory for Sentinel-2 overlay data
      const overlayData = await satellite().getSentinel2Overlay(regionBand);
      
      if (!overlayData.bounds || !overlayData.image_data) {
        throw new Error('Invalid Sentinel-2 overlay data received from server');
      }

      // Check for optimization metadata
      const isOptimized = overlayData.is_optimized || false;
      const optimizationInfo = overlayData.optimization_info || null;

      // Log optimization status
      if (isOptimized) {
        Utils.log('info', `✓ ${bType} Sentinel-2 overlay is optimized for browser performance`);
        if (optimizationInfo) {
          Utils.log('info', `Optimization details:`, optimizationInfo);
        }
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
        // Create notification message with optimization status
        let notificationMessage = `Added ${bType} Sentinel-2 overlay to map`;
        if (isOptimized) {
          notificationMessage += ' ✓ Optimized for browser performance';
        }
        
        Utils.showNotification(notificationMessage, 'success');
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
   * Acquire elevation data from coordinates
   */
  async acquireElevationData() {
    Utils.log('info', 'Get Elevation Data button clicked');

    // Get coordinates from input fields
    let lat = $('#lat-input').val();
    let lng = $('#lng-input').val();
    let regionName = $('#region-name-input').val();

    // Check if we have a selected LAZ file but no region name
    if (FileManager.selectedRegion && (!regionName || regionName.trim() === '')) {
      // Extract filename without extension from the selected region
      regionName = FileManager.selectedRegion.replace(/\.[^/.]+$/, '');
      // Update the region name input field
      $('#region-name-input').val(regionName);
      Utils.log('info', `Auto-filled region name from selected file: ${regionName}`);
    }

    // Check if we have a selected region but no coordinates in input fields
    if ((!lat || !lng || lat === '' || lng === '') && FileManager.selectedRegion) {
      // Try to get coordinates from the selected region
      const selectedItem = $(`.file-item[data-region-name="${FileManager.selectedRegion}"]`);
      let coords = null;
      
      // First try to get coordinates from stored data
      if (selectedItem.length && selectedItem.data('coords')) {
        coords = selectedItem.data('coords');
        Utils.log('info', `Found coordinates in selected item data:`, coords);
      }
      
      // If no coordinates in item data, try to extract from coordinate input fields that might have been set during region selection
      if (!coords && $('#lat-input').val() && $('#lng-input').val()) {
        const inputLat = parseFloat($('#lat-input').val());
        const inputLng = parseFloat($('#lng-input').val());
        if (Utils.isValidCoordinate(inputLat, inputLng)) {
          coords = { lat: inputLat, lng: inputLng };
          Utils.log('info', `Using coordinates from input fields: ${inputLat}, ${inputLng}`);
        }
      }
      
      // If we found valid coordinates, use them
      if (coords && coords.lat && coords.lng && Utils.isValidCoordinate(coords.lat, coords.lng)) {
        lat = coords.lat;
        lng = coords.lng;
        
        // Update the input fields
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        
        Utils.log('info', `Using coordinates from selected region ${FileManager.selectedRegion}: ${lat}, ${lng}`);
      } else {
        Utils.log('warn', `No valid coordinates found for selected region ${FileManager.selectedRegion}`);
      }
    }

    // If still no coordinates are set, use Portland, Oregon as default
    if (!lat || !lng || lat === '' || lng === '') {
      lat = 45.5152;  // Portland, Oregon
      lng = -122.6784;

      // Update the input fields
      $('#lat-input').val(lat);
      $('#lng-input').val(lng);

      // Center map on the location
      MapManager.setView(lat, lng, 12);

      Utils.showNotification('Using Portland, Oregon coordinates for elevation data acquisition', 'info');
    }

    // Validate coordinates
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);

    if (!Utils.isValidCoordinate(latNum, lngNum)) {
      Utils.showNotification('Invalid coordinates. Please enter valid latitude and longitude values.', 'error');
      return;
    }

    try {
      this.showProgress('🏔️ Acquiring elevation data...');

      // Start WebSocket connection for progress updates
      if (window.WebSocketManager) {
        WebSocketManager.connect();
      }

      // Prepare region name for the acquisition
      const effectiveRegionName = regionName && regionName.trim() !== '' ? regionName.trim() : null;

      const elevationRequest = {
        lat: latNum,
        lng: lngNum,
        buffer_km: 2.0
      };      if (effectiveRegionName) {
        elevationRequest.region_name = effectiveRegionName;
      }

      // Use elevation service from factory
      const elevationService = elevation();
      const result = await elevationService.downloadElevationData(elevationRequest);

      if (result && result.success) {
        Utils.log('info', 'Elevation data acquisition completed');
        Utils.showNotification('Successfully acquired elevation data!', 'success');
        
        // Refresh file list and region data
        if (window.FileManager && window.FileManager.loadFiles) {
          setTimeout(() => {
            FileManager.loadFiles();
          }, 1000);
        }
        
        // If we have a region name, try to display elevation data
        if (effectiveRegionName || result.metadata?.region_name) {
          const displayRegionName = effectiveRegionName || result.metadata.region_name;
          setTimeout(() => {
            this.displayLidarRasterForRegion(displayRegionName);
          }, 1500);
        }
      } else {
        throw new Error(result?.error || 'Elevation data acquisition failed');
      }

    } catch (error) {
      Utils.log('error', 'Error in elevation data acquisition:', error);
      Utils.showNotification(`Error acquiring elevation data: ${error.message}`, 'error');
    } finally {
      this.hideProgress();
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
    let regionName = $('#region-name-input').val();

    // Check if we have a selected LAZ file but no region name
    if (FileManager.selectedRegion && (!regionName || regionName.trim() === '')) {
      // Extract filename without extension from the selected region
      regionName = FileManager.selectedRegion.replace(/\.[^/.]+$/, '');
      // Update the region name input field
      $('#region-name-input').val(regionName);
      Utils.log('info', `Auto-filled region name from selected file: ${regionName}`);
    }

    // Check if we have a selected region but no coordinates in input fields
    if ((!lat || !lng || lat === '' || lng === '') && FileManager.selectedRegion) {
      // Try to get coordinates from the selected region
      const selectedItem = $(`.file-item[data-region-name="${FileManager.selectedRegion}"]`);
      let coords = null;
      
      // First try to get coordinates from stored data
      if (selectedItem.length && selectedItem.data('coords')) {
        coords = selectedItem.data('coords');
        Utils.log('info', `Found coordinates in selected item data:`, coords);
      }
      
      // If no coordinates in item data, try to extract from coordinate input fields that might have been set during region selection
      if (!coords && $('#lat-input').val() && $('#lng-input').val()) {
        const inputLat = parseFloat($('#lat-input').val());
        const inputLng = parseFloat($('#lng-input').val());
        if (Utils.isValidCoordinate(inputLat, inputLng)) {
          coords = { lat: inputLat, lng: inputLng };
          Utils.log('info', `Using coordinates from input fields: ${inputLat}, ${inputLng}`);
        }
      }
      
      // If we found valid coordinates, use them
      if (coords && coords.lat && coords.lng && Utils.isValidCoordinate(coords.lat, coords.lng)) {
        lat = coords.lat;
        lng = coords.lng;
        
        // Update the input fields
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        
        Utils.log('info', `Using coordinates from selected region ${FileManager.selectedRegion}: ${lat}, ${lng}`);
      } else {
        Utils.log('warn', `No valid coordinates found for selected region ${FileManager.selectedRegion}`);
      }
    }

    // If still no coordinates are set, use Portland, Oregon as default (good Sentinel-2 coverage)
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

      // Use elevation service from factory
      const elevationService = elevation();
      const elevationResult = await elevationService.downloadElevationData(elevationRequest);
      
      if (elevationResult && elevationResult.success) {
        Utils.log('info', 'Elevation data acquisition completed');
        this.updateProgress(50, 'Elevation data acquired. Starting satellite data download...');
      } else {
        Utils.log('warn', 'Elevation data acquisition failed:', elevationResult?.error);
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

      // Use satellite service from factory
      const satelliteService = satellite();
      const sentinelResult = await satelliteService.downloadSentinel2Data(sentinelRequest);
      
      if (sentinelResult && sentinelResult.success) {
        Utils.log('info', 'Sentinel-2 data download completed');
        this.updateProgress(90, 'Converting satellite images...');

        // Auto-convert Sentinel-2 images if we have a region name
        const sentinelRegionName = sentinelResult.metadata?.region_name || effectiveRegionName;
        if (sentinelRegionName) {
          await this.convertAndDisplaySentinel2(sentinelRegionName);
        }
      } else {
        Utils.log('warn', 'Sentinel-2 data download failed:', sentinelResult?.error);
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
          
          // ALWAYS load both LiDAR raster and Sentinel-2 images regardless of file type
          Utils.log('info', `🛰️ === GETCOMBINEDDATA CALLING SENTINEL-2 ===`);
          Utils.log('info', `📍 Display Region Name: ${displayRegionName}`);
          Utils.log('info', `📍 Effective Region Name: ${effectiveRegionName}`);
          Utils.log('info', `📍 Sentinel Result Region: ${sentinelResult?.metadata?.region_name}`);
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
  },

  /**
   * Show image modal
   * @param {string} imageSrc - Source URL of the image
   * @param {string} imageAlt - Alt text for the image (used as caption)
   */
  showImageModal(imageSrc, imageAlt) {
    const modal = $('#image-modal');
    const imgElement = $('#image-modal-img');
    const captionElement = $('#image-modal-caption');
    const titleElement = $('#image-modal-title');

    if (modal.length && imgElement.length && captionElement.length && titleElement.length) {
      imgElement.attr('src', imageSrc);
      imgElement.attr('alt', imageAlt);
      captionElement.text(imageAlt);
      titleElement.text(imageAlt || 'Image Preview'); // Use alt text as title or default
      
      modal.fadeIn();
      Utils.log('info', `Image modal shown for: ${imageAlt}`);
    } else {
      Utils.log('error', 'Image modal elements not found');
    }
  },

  /**
   * Hide image modal
   */
  hideImageModal() {
    const modal = $('#image-modal');
    if (modal.length) {
      modal.fadeOut();
      // Optional: Clear image source to free memory
      // $('#image-modal-img').attr('src', ''); 
      Utils.log('info', 'Image modal hidden');
    }
  },

  /**
   * Initialize event handlers for the image modal
   */
  initializeImageModalEventHandlers() {
    // Close modal on X button click
    $('#image-modal-close').on('click', () => {
      this.hideImageModal();
    });

    // Close modal on Escape key (ensure this is registered after modal is added to DOM)
    $(document).on('keydown', (e) => {
      if (e.key === 'Escape' && $('#image-modal').is(':visible')) {
        this.hideImageModal();
      }
    });

    // Close modal on background click
    $('#image-modal').on('click', function(e) {
      if (e.target === this) {
        UIManager.hideImageModal();
      }
    });
  },

  /**
   * Fetch and display region coordinates for LAZ files
   * @param {string} regionPath - Path to the LAZ file
   */
  async fetchAndDisplayRegionCoords(regionPath) {
    try {
      Utils.log('info', `Fetching bounds for LAZ file: ${regionPath}`);
      
      // Extract just the filename from the path for the API call
      // The LAZ bounds API expects just the filename, not the full path
      const fileName = regionPath.split('/').pop();
      Utils.log('info', `Extracted filename for API call: ${fileName}`);
      
      // Use LAZ service to get WGS84 bounds
      const lazService = laz();
      const boundsData = await lazService.getLAZFileBounds(fileName);
      
      if (boundsData.error) {
        Utils.log('warn', `Failed to get LAZ bounds: ${boundsData.error}`);
        return;
      }
      
      let coords = null;
      
      // First try to use the center coordinates from WGS84 response (preferred)
      if (boundsData.center && boundsData.center.lat && boundsData.center.lng) {
        coords = {
          lat: boundsData.center.lat,
          lng: boundsData.center.lng
        };
        Utils.log('info', `Using WGS84 center coordinates: lat=${coords.lat}, lng=${coords.lng}`);
      }
      // Fallback to extracting coordinates from bounds data
      else if (boundsData.bounds) {
        coords = this.extractCoordsFromBounds(boundsData.bounds);
        if (coords) {
          Utils.log('info', `LAZ bounds extracted: lat=${coords.lat}, lng=${coords.lng}`);
        }
      }
      
      if (!coords) {
        Utils.log('warn', 'No bounds or center data found in LAZ file');
        return;
      }
      
      if (coords) {
        // Update map view and location pin
        MapManager.setView(coords.lat, coords.lng, 13);
        FileManager.updateLocationPin(coords.lat, coords.lng, regionPath);
        
        // Update coordinate input fields
        $('#goto-lat-input').val(coords.lat.toFixed(6));
        $('#goto-lng-input').val(coords.lng.toFixed(6));
        $('#lat-input').val(coords.lat.toFixed(6));
        $('#lng-input').val(coords.lng.toFixed(6));
        
        Utils.showNotification(`Map centered on LAZ file: ${regionPath.split('/').pop()}`, 'success');
      } else {
        Utils.log('warn', 'Could not extract valid coordinates from LAZ bounds');
      }
      
    } catch (error) {
      Utils.log('error', 'Error fetching LAZ file bounds', error);
      Utils.showNotification('Failed to fetch LAZ file coordinates', 'error');
    }
  },

  /**
   * Extract center coordinates from various bounds formats
   * @param {Object|Array|String} bounds - Bounds data in various formats
   * @returns {Object|null} Object with lat/lng or null if invalid
   */
  extractCoordsFromBounds(bounds) {
    try {
      // Handle different boundary formats from PDAL
      if (typeof bounds === 'string') {
        // Sometimes bounds come as string, try to parse as JSON
        try {
          bounds = JSON.parse(bounds);
        } catch (e) {
          Utils.log('warn', 'Cannot parse bounds string as JSON');
          return null;
        }
      }
      
      if (Array.isArray(bounds)) {
        // Array format: might be [minX, minY, maxX, maxY] or nested arrays
        if (bounds.length >= 4) {
          const [minX, minY, maxX, maxY] = bounds;
          return {
            lat: (minY + maxY) / 2,
            lng: (minX + maxX) / 2
          };
        }
        
        // Handle nested array format like [[x,y],[x,y],[x,y],[x,y]] (polygon)
        if (bounds.length > 0 && Array.isArray(bounds[0])) {
          let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
          
          bounds.forEach(coord => {
            if (Array.isArray(coord) && coord.length >= 2) {
              const [x, y] = coord;
              minX = Math.min(minX, x);
              maxX = Math.max(maxX, x);
              minY = Math.min(minY, y);
              maxY = Math.max(maxY, y);
            }
          });
          
          if (isFinite(minX) && isFinite(maxX) && isFinite(minY) && isFinite(maxY)) {
            return {
              lat: (minY + maxY) / 2,
              lng: (minX + maxX) / 2
            };
          }
        }
      }
      
      if (typeof bounds === 'object' && bounds !== null) {
        // Object format: check for various property names
        const props = bounds;
        
        // Format: { minX, minY, maxX, maxY }
        if ('minX' in props && 'minY' in props && 'maxX' in props && 'maxY' in props) {
          return {
            lat: (props.minY + props.maxY) / 2,
            lng: (props.minX + props.maxX) / 2
          };
        }
        
        // Format: { west, south, east, north }
        if ('west' in props && 'south' in props && 'east' in props && 'north' in props) {
          return {
            lat: (props.south + props.north) / 2,
            lng: (props.west + props.east) / 2
          };
        }
        
        // Format: { min: [x,y], max: [x,y] }
        if ('min' in props && 'max' in props && Array.isArray(props.min) && Array.isArray(props.max)) {
          return {
            lat: (props.min[1] + props.max[1]) / 2,
            lng: (props.min[0] + props.max[0]) / 2
          };
        }
        
        // Format: GeoJSON-like bbox
        if ('bbox' in props && Array.isArray(props.bbox) && props.bbox.length >= 4) {
          const [minX, minY, maxX, maxY] = props.bbox;
          return {
            lat: (minY + maxY) / 2,
            lng: (minX + maxX) / 2
          };
        }
      }
      
      Utils.log('warn', 'Unrecognized bounds format:', bounds);
      return null;
      
    } catch (error) {
      Utils.log('error', 'Error extracting coordinates from bounds', error);
      return null;
    }
  },

};
