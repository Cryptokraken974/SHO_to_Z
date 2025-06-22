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
    this.initializeReloadRasterButton(); // Initialize reload raster gallery button

    this.resultsTabInitialized = false; // Initialize flag for Results tab
    
    Utils.log('info', 'UI Manager initialized');
  },

  // This function will be called after new HTML content is loaded into a part of the page.
  // contextElement is the DOM element into which content was loaded.
  // contextName is a string (e.g., tab name or modal name) to identify the content.
  async initializeDynamicContent(contextElement, contextName) {
    console.log('🔍 DEBUG: initializeDynamicContent called with contextName:', contextName);
    console.log(`UI: Initializing dynamic content for context: ${contextName} in element:`, contextElement);

    // General initializers
    // These should ideally accept contextElement to scope their actions or be idempotent
    // Pass contextElement to UIManager's own methods if they are designed to target specific elements
    if (typeof this.initializeAccordions === 'function') this.initializeAccordions(contextElement);
    if (typeof this.initializeResizablePanels === 'function') this.initializeResizablePanels(contextElement);
    if (typeof this.initializeTooltips === 'function') this.initializeTooltips(contextElement);

    // Tab-specific initializations
    // Note: contextName here is the modulePath like 'modules/map-tab-content.html'
    if (contextName.includes('map-tab-content.html')) {
        // Always reinitialize map when tab content is loaded
        if (document.getElementById('map') && window.MapManager) {
            console.log('*** Reinitializing Map Manager from tab content ***');
            const mapInitialized = window.MapManager.init();
            if (!mapInitialized) {
                console.error('Failed to initialize map from tab content');
            } else {
                // Load region markers when map is ready
                if (window.FileManager && typeof FileManager.loadFiles === 'function') {
                    console.log('*** Loading region markers for map ***');
                    setTimeout(() => {
                        FileManager.loadFiles(); // Load ALL regions (input + output) and create markers
                    }, 500); // Small delay to ensure map is fully ready
                }
            }
        } else {
            console.error('Map element or MapManager not found for tab content');
        }
        if (window.SavedPlaces && typeof SavedPlaces.init === 'function') SavedPlaces.init(); // May need context

        // Initialize galleries if they are specific to this tab
        if (window.RasterOverlayGallery && document.getElementById('gallery')) {
            console.log('Initializing RasterOverlayGallery for #gallery element');
            window.rasterOverlayGallery = new RasterOverlayGallery('gallery');
            window.rasterOverlayGallery.init();
            console.log('RasterOverlayGallery initialized successfully');
        }
        if (window.SatelliteOverlayGallery && document.getElementById('satellite-gallery')) {
            // Example: new SatelliteOverlayGallery('satellite-gallery').init();
        }
        // this.initializeMapTabEventHandlers(contextElement); // For tab-specific non-delegated event handlers

    } else if (contextName.includes('geotiff-tools-tab-content.html')) {
        if (window.GeoTiffLeftPanel && document.getElementById('geotiff-sidebar')) {
            if (!window.geoTiffLeftPanelInstance) {
                window.geoTiffLeftPanelInstance = new GeoTiffLeftPanel();
            } else {
                // Re-initialize event listeners for newly loaded DOM elements
                window.geoTiffLeftPanelInstance.init();
            }
        }
        if (window.GeoTiffMainCanvas && document.getElementById('geotiff-main-canvas')) {
             if (!window.geoTiffMainCanvasInstance) window.geoTiffMainCanvasInstance = new GeoTiffMainCanvas();
            else window.geoTiffMainCanvasInstance.init();
        }
        // this.initializeGeoTiffTabEventHandlers(contextElement);

    } else if (contextName.includes('openai-analysis-tab-content.html')) {
        console.log('🤖 OpenAI tab content detected - initializing...');
        
        // Clear any existing instance to ensure clean state
        if (window.openAIAnalysisInstance) {
            console.log('🤖 Clearing existing OpenAI Analysis instance');
            window.openAIAnalysisInstance = null;
        }
        
        // Always create/recreate the instance when dynamic content loads
        if (window.OpenAIAnalysis) {
            console.log('🤖 Creating OpenAI Analysis instance for dynamic content');
            try {
                window.openAIAnalysisInstance = new OpenAIAnalysis();
                console.log('🤖 OpenAI Analysis instance created successfully');
            } catch (error) {
                console.error('🤖 Failed to create OpenAI Analysis instance:', error);
                window.openAIAnalysisInstance = null;
            }
        }

    } else if (contextName.includes('results-tab-content.html')) {
        this.initializeResultsTab();
        // Always refresh the results list when switching to the Results tab
        if (window.ResultsManager && typeof window.ResultsManager.fetchResultsList === 'function') {
            window.ResultsManager.fetchResultsList();
        }
        // this.initializeResultsTabEventHandlers(contextElement);
    }

    // Modal-specific initializations
    // contextElement for modals is 'modals-placeholder'. The actual modal is its first child.
    if (contextElement && contextElement.id === 'modals-placeholder' && contextElement.firstElementChild && contextElement.firstElementChild.classList.contains('modal')) {
        const modalElement = contextElement.firstElementChild;
        const modalId = modalElement.id;

        this.reinitializeModalEventHandlers(`#${modalId}`, contextElement); // Pass placeholder as context for find

        // Specific modal setups after generic handlers
        if (modalId === 'laz-file-modal' && window.geoTiffLeftPanelInstance) {
             window.geoTiffLeftPanelInstance.setupLazModalEvents();
        } else if (modalId === 'laz-folder-modal' && window.geoTiffLeftPanelInstance) {
             window.geoTiffLeftPanelInstance.setupLazFolderModalEvents();
        } else if (modalId === 'image-selection-modal' && window.openAIAnalysisInstance) {
            window.openAIAnalysisInstance.setupEventListeners();
            window.openAIAnalysisInstance.initializeGalleries();
        } else if (modalId === 'image-modal') {
            this.initializeImageModalEventHandlers(); // This might need to target elements within the loaded modal
        }
        // Ensure the newly loaded modal is made visible
        $(modalElement).filter(':hidden').fadeIn();
    }

    console.log(`UI: Dynamic content initialization attempt complete for ${contextName}`);
  },

  // Placeholder for more granular event handler initialization (if needed beyond component init methods)
  initializeMapTabEventHandlers(contextElement) { Utils.log('debug', `TODO: MapTabEventHandlers for ${contextElement}`); },
  initializeGeoTiffTabEventHandlers(contextElement) { Utils.log('debug', `TODO: GeoTiffTabEventHandlers for ${contextElement}`); },
  initializeOpenAITabEventHandlers(contextElement) { Utils.log('debug', `TODO: OpenAITabEventHandlers for ${contextElement}`); },
  initializeResultsTabEventHandlers(contextElement) { Utils.log('debug', `TODO: ResultsTabEventHandlers for ${contextElement}`); },

  reinitializeModalEventHandlers(modalSelector, contextElementPassed) {
    const contextNode = contextElementPassed || document.getElementById('modals-placeholder') || document;
    const $modal = modalSelector ? $(contextNode).find(modalSelector) : $(contextNode);

    if (!$modal.length || !$modal.hasClass('modal')) {
        if(modalSelector) console.warn(`Modal not found with selector ${modalSelector} in reinitializeModalEventHandlers.`);
        else if(!$(contextNode).hasClass('modal')) console.warn('Provided contextElement is not a modal itself for reinitialization.');
        return;
    }

    const modalId = $modal.attr('id');
    Utils.log('info', `Re-initializing generic event handlers for modal: ${modalId || 'unknown modal'}`);

    // Standard close button with class 'modal-close'
    $modal.find('.modal-close').off('click').on('click', function() {
        $modal.fadeOut(() => {
            // if ($modal.parent().is('#modals-placeholder')) { $('#modals-placeholder').empty(); }
        });
    });
  },

  /**
   * Initialize tab functionality
   */
  initializeTabs() {
    // Tab switching event handlers
    $('.tab-btn').on('click', async (e) => {
      const tabName = $(e.currentTarget).data('tab'); // Use currentTarget for reliability

      // Update active button style
      $('.tab-btn').removeClass('active border-[#00bfff] text-white').addClass('border-transparent text-[#ababab]');
      $(e.currentTarget).addClass('active border-[#00bfff] text-white').removeClass('border-transparent text-[#ababab]');

      await this.loadTabContent(tabName);
      
      // Special handling for OpenAI Analysis tab - immediate loading without retries
      if (tabName === 'openai-analysis') {
        console.log('🤖 OpenAI Analysis tab activated - loading regions immediately');
        
        // Direct, immediate region loading without any delays or retries
        if (window.openAIAnalysisInstance && typeof window.openAIAnalysisInstance.loadRegions === 'function') {
          console.log('🤖 Loading regions immediately for OpenAI Analysis tab');
          window.openAIAnalysisInstance.loadRegions();
        } else if (window.OpenAIAnalysis) {
          console.log('🤖 Creating OpenAI Analysis instance and loading regions immediately');
          try {
            window.openAIAnalysisInstance = new OpenAIAnalysis();
            if (window.openAIAnalysisInstance && typeof window.openAIAnalysisInstance.loadRegions === 'function') {
              window.openAIAnalysisInstance.loadRegions();
            }
          } catch (error) {
            console.error('🤖 Failed to create OpenAI Analysis instance:', error);
          }
        } else {
          console.warn('🤖 OpenAI Analysis class not available - tab will load without regions');
        }
      }
    });

    Utils.log('info', 'Tabs initialized');
  },

  /**
   * Load content for a specific tab
   * @param {string} tabName - Name of the tab to load
   */
  async loadTabContent(tabName) {
    console.log('🔍 DEBUG: Loading tab content for:', tabName);
    
    const mainContentPlaceholder = document.getElementById('main-content-placeholder');
    if (!mainContentPlaceholder) {
      console.error('Main content placeholder not found');
      Utils.showNotification('Error: Main content placeholder missing.', 'error');
      return;
    }

    console.log('🔍 DEBUG: Found main content placeholder');
    mainContentPlaceholder.innerHTML = '<div class="loading-message text-center text-[#666] p-8">🔄 Loading tab content...</div>';
    const modulePath = `modules/${tabName}-tab-content.html`;
    console.log('🔍 DEBUG: Module path:', modulePath);

    try {
      // loadModule (in app_new.js) now calls window.initializeDynamicContent itself after success.
      console.log('🔍 DEBUG: About to call loadModule with path:', modulePath);
      await loadModule(modulePath, 'main-content-placeholder');
      console.log('🔍 DEBUG: loadModule completed successfully');
      
      // Verify the content was loaded
      const openaiTab = document.getElementById('openai-analysis-tab');
      console.log('🔍 DEBUG: After loading, openai-analysis-tab found:', !!openaiTab);
      if (openaiTab) {
        const availableList = document.getElementById('available-region-list');
        const selectedList = document.getElementById('selected-region-list');
        console.log('🔍 DEBUG: Region lists found - available:', !!availableList, 'selected:', !!selectedList);
      }
      
      Utils.log('info', `Triggered loading for ${tabName} tab. Post-load initialization handled by initializeDynamicContent.`);
    } catch (error) {
        console.error('🔍 DEBUG: Error in loadTabContent:', error);
        mainContentPlaceholder.innerHTML = `<div class="error-message text-center text-red-500 p-8">❌ Error loading ${tabName} tab. Check console for details.</div>`;
        console.error(`Error in loadTabContent for ${tabName}:`, error);
        Utils.showNotification(`Error loading ${tabName} tab.`, 'error');
    }
  },

  /**
   * Placeholder for tab-specific accordion initialization.
   * This might be needed if accordions are dynamically added with tab content.
   * @param {string} tabName
   */
  initializeAccordionsForTab(tabName) {
    Utils.log('info', `Initializing accordions for tab: ${tabName}`);
    // Example: if map tab has specific accordions:
    if (tabName === 'map') {
        $('#region-accordion').off('click').on('click', () => this.toggleAccordion('region'));
        $('#get-data-accordion').off('click').on('click', () => this.toggleAccordion('get-data'));
        $('#generate-rasters-accordion').off('click').on('click', () => this.toggleAccordion('generate-rasters'));
        $('#go-to-accordion').off('click').on('click', () => this.toggleAccordion('go-to'));
    }
    // Add more for other tabs if needed
    // This ensures event handlers are attached to newly loaded DOM elements.
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
    // Also set on window for compatibility
    window.globalSelectedRegion = regionName;
    
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
  async handleGlobalRegionSelection(regionName, coords = null, processingRegion = null, filePath = null) {
    // Update global selector
    this.updateGlobalRegionSelector(regionName);
    
    // Update FileManager's selected region
    if (window.FileManager) {
        FileManager.selectRegion(regionName, coords, processingRegion, filePath);
    }

    // Switch to Map tab using the new method
    await this.loadTabContent('map');
    // Ensure the 'map' tab button is styled as active after loading
    $('.tab-btn').removeClass('active border-[#00bfff] text-white').addClass('border-transparent text-[#ababab]');
    $(`.tab-btn[data-tab="map"]`).addClass('active border-[#00bfff] text-white').removeClass('border-transparent text-[#ababab]');

    // Set map view and pin if coordinates are available
    if (coords && Utils.isValidCoordinate(coords.lat, coords.lng) && window.MapManager) {
      MapManager.setView(coords.lat, coords.lng, 13);
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
   * @param {Element} contextElement - Optional context element to scope selectors
   */
  initializeAccordions(contextElement = document) {
    const $context = $(contextElement);
    
    // Region accordion
    $context.find('#region-accordion').off('click').on('click', () => {
      this.toggleAccordion('region');
    });

    // Get Data accordion (renamed from Test)
    $context.find('#get-data-accordion').off('click').on('click', () => {
      this.toggleAccordion('get-data');
    });

    // Generate Rasters accordion
    $context.find('#generate-rasters-accordion').off('click').on('click', () => {
      this.toggleAccordion('generate-rasters');
    });

    // Go to accordion
    $context.find('#go-to-accordion').off('click').on('click', () => {
      this.toggleAccordion('go-to');
    });

    // GeoTiff Tools tab accordions
    $context.find('#geotiff-files-accordion').off('click').on('click', () => {
      this.toggleAccordion('geotiff-files');
    });

    $context.find('#geotiff-load-files-accordion').off('click').on('click', () => {
      this.toggleAccordion('geotiff-load-files');
    });

    $context.find('#geotiff-tools-accordion').off('click').on('click', () => {
      this.toggleAccordion('geotiff-tools');
    });

    $context.find('#geotiff-processing-accordion').off('click').on('click', () => {
      this.toggleAccordion('geotiff-processing');
    });

    $context.find('#geotiff-info-accordion').off('click').on('click', () => {
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
    $('#global-browse-regions-btn').on('click', async () => { // Made async
      console.log('🔍 Select Region button clicked - Looking up folders:');
      console.log('📁 Primary folder: input/');
      console.log('📁 Secondary folder: output/');
      console.log('📊 Source filter: all (both input and output folders will be searched)');
      
      // Load the modal HTML first
      await loadModule('modules/modals/file-modal.html', 'modals-placeholder'); // Ensure loadModule is accessible

      // After modal HTML is loaded, then proceed with original logic
      // Note: Event handlers for elements inside file-modal.html (#cancel-select, #confirm-region-selection, etc.)
      // should ideally be re-attached here or in a callback after loadModule.
      // For now, assuming they might be globally attached or need addressing in Step 13.

      FileManager.loadFiles(); // Load from ALL directories (both input and output)

      const fileModal = document.getElementById('file-modal');
      if (fileModal) {
        $(fileModal).fadeIn(); // Use jQuery if it's still primary for show/hide
        $('#file-modal h4').text('Select Region (All Available)'); // Use jQuery for consistency if fileModal is a jQuery object
        $(fileModal).data('for-global', true);
        $('#delete-region-btn').addClass('hidden').prop('disabled', false).text('Delete Region');

        // Re-attach internal modal event handlers if they were part of the loaded HTML fragment
        this.reinitializeModalEventHandlers('#file-modal');
      } else {
        console.error('File modal not found after loading.');
      }
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

    // Test Sentinel-2 button - Use event delegation
    $(document).on('click', '#test-sentinel2-btn', () => {
      this.testSentinel2();
    });

    // Get Elevation Data button - Use event delegation
    $(document).on('click', '#get-lidar-btn', () => {
      this.acquireElevationData();
    });

    // Get Data button (Combined: Elevation + Satellite) - Use event delegation
    $(document).on('click', '#get-data-btn', () => {
      this.getCombinedData();
    });

    // Generate Rasters - Single Button for All Processing - Use event delegation
    $(document).on('click', '#generate-all-rasters-btn', () => {
      ProcessingManager.processAllRasters();
    });

    // Cancel All Rasters Processing - Use event delegation
    $(document).on('click', '#cancel-all-rasters-btn', () => {
      ProcessingManager.cancelAllRasterProcessing();
    });

    // Go to coordinates button - Use event delegation
    $(document).on('click', '#go-to-coordinates-btn', () => {
      this.goToCoordinates();
    });

    // Coordinate input parser - Use event delegation
    $(document).on('input', '#goto-coordinates-input', Utils.debounce(() => {
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

    // File modal close buttons - These might need to be delegated if modals-placeholder is emptied often
    // or re-attached in reinitializeModalEventHandlers
    // For now, assume they are handled if reinitializeModalEventHandlers is effective.
    // Original direct bindings:
    // $('.close, #cancel-select').on('click', function() { ... });
    // $('#delete-region-btn').on('click', function() { ... });
    // $('#confirm-region-selection').on('click', function() { ... });

    // Delegate event handlers for elements within dynamically loaded modals
    // This is a more robust way than re-attaching if the modal content is frequently replaced.
    $(document).on('click', '#modals-placeholder .modal-close', function() {
        $(this).closest('.modal').fadeOut();
        // Potentially clear #modals-placeholder or specific modal content here
        // $('#modals-placeholder').empty(); // Or target specific modal ID
    });

    $(document).on('click', '#modals-placeholder #cancel-select', function() {
        $(this).closest('.modal').fadeOut();
        // $('#modals-placeholder').empty();
    });
    
    $(document).on('click', '#modals-placeholder #delete-region-btn', function() {
      const selectedItem = $('#modals-placeholder .file-item.selected'); // Ensure targeting within placeholder
      if (selectedItem.length === 0) {
        Utils.showNotification('Please select a region first', 'warning');
        return;
      }
      
      const regionName = selectedItem.data('region-name');
      const $deleteButton = $(this); // Reference to the delete button itself

      if (confirm(`Are you sure you want to delete the region "${regionName}"? This will permanently delete all files in input/${regionName} and output/${regionName}.`)) {
        $deleteButton.prop('disabled', true).text('Deleting...');
        
        FileManager.deleteRegion(regionName)
          .then(result => {
            if (result.success) {
              Utils.showNotification(`Region "${regionName}" deleted successfully`, 'success');
              selectedItem.remove();
              $deleteButton.addClass('hidden').prop('disabled', false).text('Delete Region');
              if (FileManager.getSelectedRegion() === regionName) {
                $('#selected-region-name').text('No region selected').removeClass('text-[#00bfff]').addClass('text-[#666]');
              }
            } else {
              Utils.showNotification(`Failed to delete region: ${result.message}`, 'error');
              $deleteButton.prop('disabled', false).text('Delete Region');
            }
          })
          .catch(error => {
            console.error('Error deleting region:', error);
            Utils.showNotification(`Error deleting region: ${error.message}`, 'error');
            $deleteButton.prop('disabled', false).text('Delete Region');
          });
      }
    });

    $(document).on('click', '#modals-placeholder #confirm-region-selection', function() {
        const selectedItem = $('#modals-placeholder .file-item.selected');
        if (selectedItem.length === 0) {
            Utils.showNotification('Please select a region first', 'warning');
            return;
        }

        const regionName = selectedItem.data('region-name');
        let processingRegion = selectedItem.data('processing-region');
        const filePath = selectedItem.data('file-path');
        const coords = selectedItem.data('coords');

        if (processingRegion === "LAZ") {
            console.warn("⚠️ Processing region is 'LAZ', using display name instead.");
            processingRegion = regionName;
        }

        // Access data attribute from the modal itself, not the placeholder
        const fileModalElement = document.getElementById('file-modal'); // Get the actual modal element
        const isForGlobal = $(fileModalElement).data('for-global');

        if (isForGlobal) {
            UIManager.handleGlobalRegionSelection(regionName, coords, processingRegion, filePath);
            $(fileModalElement).removeData('for-global');
        } else {
            FileManager.selectRegion(regionName, coords, processingRegion, filePath);
        }

        // Ensure region markers remain visible after selection
        if (window.FileManager && typeof FileManager.ensureRegionMarkersVisible === 'function') {
            // Give a small delay to ensure the selection is processed first
            setTimeout(() => {
                FileManager.ensureRegionMarkersVisible();
            }, 100);
        }

        $(this).closest('.modal').fadeOut();
        // Optionally clear the placeholder if modals are always reloaded:
        // $('#modals-placeholder').empty();
    });

    // Progress modal close buttons - delegate if it's also loaded into modals-placeholder
    $(document).on('click', '#modals-placeholder #progress-close, #modals-placeholder #cancel-progress', () => {
        this.hideProgress(); // Assumes hideProgress targets #progress-modal correctly even if nested
    });

    // Coordinate input field event handlers for region name generation - Use event delegation
    $(document).on('input change', '#lat-input, #lng-input', Utils.debounce(() => {
      this.updateRegionNameFromCoordinates();
    }, 500));

    // Manual region name editing - Use event delegation
    $(document).on('input', '#region-name-input', () => {
      // Allow manual editing of region name
      Utils.log('info', 'Region name manually edited');
    });

    // Event listener for the reload button
    $(document).on('click', '#reload-raster-gallery-btn', function() {
        console.log("Reloading raster gallery...");
        const selectedRegion = UIManager.globalSelectedRegion;
        if (selectedRegion) {
            rasterOverlayGallery.loadRasters(selectedRegion);
        } else {
            console.warn("No region selected, cannot reload raster gallery.");
            Utils.showToast("Please select a region first.", "warning");
        }
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
    // General modal close logic (background click, Escape key)
    // This should ideally target modals within #modals-placeholder if they are dynamically loaded there.
    // However, the original was global, so keeping it global for now, but might need refinement.
    $(document).on('click', '.modal', function(e) { // Changed to document to catch dynamically loaded modals
        if (e.target === this) { // Ensure it's the modal background, not content
            $(this).fadeOut();
            // Consider $('#modals-placeholder').empty(); if modals are always reloaded
        }
    });

    $(document).on('keydown', function(e) {
        if (e.key === 'Escape') {
            $('#modals-placeholder .modal:visible').fadeOut(); // Target visible modals in placeholder
            // Consider $('#modals-placeholder').empty();
        }
    });

    Utils.log('info', 'Delegated modal event handlers initialized');
  },

  /**
   * Re-initializes event handlers for a specific modal after it's loaded.
   * This is a helper to keep internal modal logic working.
   * @param {string} modalSelector - The CSS selector for the modal (e.g., '#file-modal') or null if contextElement is the modal.
   * @param {HTMLElement} contextElement - The DOM element where the modal was loaded (usually 'modals-placeholder').
   */
  reinitializeModalEventHandlers(modalSelector, contextElementPassed) {
    // If contextElementPassed is not given, default to #modals-placeholder or document
    const contextNode = contextElementPassed || document.getElementById('modals-placeholder') || document;
    const $modal = modalSelector ? $(contextNode).find(modalSelector) : $(contextNode); // If no selector, contextNode might be the modal itself.

    if (!$modal.length || !$modal.hasClass('modal')) { // Check if a modal was actually found or passed
        // If modalSelector was null and contextNode was modals-placeholder, this is not an error.
        // If modalSelector was provided, then it's an issue.
        if(modalSelector) console.warn(`Modal not found with selector ${modalSelector} in reinitializeModalEventHandlers.`);
        return;
    }

    const modalId = $modal.attr('id');
    Utils.log('info', `Re-initializing event handlers for modal: ${modalId || 'unknown modal'}`);

    // General close buttons if not already covered by global delegation
    // This ensures that if a modal's HTML is simple and relies on a common '.modal-close' class, it works.
    $modal.find('.modal-close').off('click').on('click', function() {
        $modal.fadeOut(() => {
            if ($modal.parent().is('#modals-placeholder')) {
                // $modal.remove(); // Or $('#modals-placeholder').empty(); if only one modal at a time
            }
        });
    });

    // Specific re-initializations based on modal ID
    // This is where you'd call specific setup functions for each modal's unique interactions
    // if they are not handled by broader delegated event listeners or class initializations.
    // For example, if 'laz-file-modal' has complex internal event logic not covered by its class's init:
    // if (modalId === 'laz-file-modal' && window.geoTiffLeftPanelInstance) {
    //    window.geoTiffLeftPanelInstance.setupSpecificLazModalInteractions($modal);
    // }
    // Most of our modal-specific JS is now called from initializeDynamicContent via class init methods.
    // This function can serve as a fallback or for very generic re-bindings.
  },

  /**
   * Initialize resizable panels
   * @param {Element} contextElement - Optional context element to scope selectors
   */
  initializeResizablePanels(contextElement = document) {
    const $context = $(contextElement);
    let isResizing = false;
    let currentPanel = null;
    let startX = 0;
    let startWidth = 0;

    // Handle mousedown on resize handles
    $context.find('.resize-handle').off('mousedown').on('mousedown', function(e) {
      e.preventDefault();
      isResizing = true;
      currentPanel = $(this).parent();
      startX = e.pageX;
      startWidth = currentPanel.outerWidth();
      
      $(this).addClass('dragging');
      $('body').addClass('resize-active');
      
      Utils.log('debug', 'Started resizing panel');
    });

    // Handle mousemove for resizing (document level event, only bind once)
    if (!this._resizeMoveHandler) {
      this._resizeMoveHandler = function(e) {
        if (!isResizing || !currentPanel) return;
        
        e.preventDefault();
        const deltaX = e.pageX - startX;
        const newWidth = Math.max(200, Math.min(600, startWidth + deltaX));
        
        currentPanel.css('width', newWidth + 'px');
      };
      $(document).on('mousemove', this._resizeMoveHandler);
    }

    // Handle mouseup to stop resizing (document level event, only bind once)
    if (!this._resizeUpHandler) {
      this._resizeUpHandler = function(e) {
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
      };
      $(document).on('mouseup', this._resizeUpHandler);
    }

    // Load saved panel widths
    $context.find('.resizable-panel').each(function() {
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
    if (!window.satelliteOverlayGallery) {
      Utils.log('warn', 'SatelliteOverlayGallery not initialized, attempting to initialize...');
      
      // Check if the satellite gallery container exists
      const satelliteGalleryContainer = document.getElementById('satellite-gallery');
      if (!satelliteGalleryContainer) {
        Utils.log('warn', 'Satellite gallery container not found, Sentinel-2 images will be displayed when map tab is accessed');
        return;
      }
      
      // Initialize the gallery if container exists
      try {
        window.satelliteOverlayGallery = new window.SatelliteOverlayGallery('satellite-gallery', {
          onAddToMap: (regionBand, bandType) => {
            if (window.UIManager?.addSentinel2OverlayToMap) {
              window.UIManager.addSentinel2OverlayToMap(regionBand, bandType);
            }
          }
        });
        Utils.log('info', 'SatelliteOverlayGallery initialized successfully');
      } catch (error) {
        Utils.log('error', 'Failed to initialize SatelliteOverlayGallery:', error);
        return;
      }
    }

    const items = (files || []).map(fileObj => {
      const band = fileObj.band;
      let apiRegionName = regionName;
      if (!regionName.startsWith('region_')) {
        apiRegionName = `region_${regionName.replace(/\./g, '_')}`;
      }
      const regionBand = `${apiRegionName}_${band}`;
      const title = window.satelliteOverlayGallery.getBandDisplayName
        ? window.satelliteOverlayGallery.getBandDisplayName(band)
        : band;
      return {
        id: regionBand,
        imageUrl: `data:image/png;base64,${fileObj.image}`,
        title,
        subtitle: regionName,
        status: 'ready',
        bandType: title
      };
    });

    window.satelliteOverlayGallery.showImages(items);
  },

  /**
   * Fetches and displays Sentinel-2 images for a given region.
   * Checks for available Sentinel-2 processing results and displays them in the satellite gallery.
   * @param {string} regionName - The name of the region.
   */
  async displaySentinel2ImagesForRegion(regionName) {
    if (!window.satelliteOverlayGallery) {
      Utils.log('warn', 'SatelliteOverlayGallery not initialized, attempting to initialize...');
      
      // Check if the satellite gallery container exists
      const satelliteGalleryContainer = document.getElementById('satellite-gallery');
      if (!satelliteGalleryContainer) {
        Utils.log('warn', 'Satellite gallery container not found, Sentinel-2 images will be loaded when map tab is accessed');
        return;
      }
      
      // Initialize the gallery if container exists
      try {
        window.satelliteOverlayGallery = new window.SatelliteOverlayGallery('satellite-gallery', {
          onAddToMap: (regionBand, bandType) => {
            if (window.UIManager?.addSentinel2OverlayToMap) {
              window.UIManager.addSentinel2OverlayToMap(regionBand, bandType);
            }
          }
        });
        Utils.log('info', 'SatelliteOverlayGallery initialized successfully');
      } catch (error) {
        Utils.log('error', 'Failed to initialize SatelliteOverlayGallery:', error);
        return;
      }
    }
    
    await window.satelliteOverlayGallery.loadImages(regionName);
  },

  /**
   * Display Sentinel-2 band images in the satellite gallery
   * @param {Array} availableBands - Array of available band data
   */
  displaySentinel2BandsGallery(availableBands) {
    if (!window.satelliteOverlayGallery) {
      Utils.log('warn', 'SatelliteOverlayGallery not initialized, attempting to initialize...');
      
      // Check if the satellite gallery container exists
      const satelliteGalleryContainer = document.getElementById('satellite-gallery');
      if (!satelliteGalleryContainer) {
        Utils.log('warn', 'Satellite gallery container not found, Sentinel-2 images will be displayed when map tab is accessed');
        return;
      }
      
      // Initialize the gallery if container exists
      try {
        window.satelliteOverlayGallery = new window.SatelliteOverlayGallery('satellite-gallery', {
          onAddToMap: (regionBand, bandType) => {
            if (window.UIManager?.addSentinel2OverlayToMap) {
              window.UIManager.addSentinel2OverlayToMap(regionBand, bandType);
            }
          }
        });
        Utils.log('info', 'SatelliteOverlayGallery initialized successfully');
      } catch (error) {
        Utils.log('error', 'Failed to initialize SatelliteOverlayGallery:', error);
        return;
      }
    }

    const items = (availableBands || []).map(bandData => {
      const { band, overlayData, regionName } = bandData;
      const imageB64 = overlayData.image_data;

      let apiRegionName = regionName;
      if (!regionName.startsWith('region_')) {
        apiRegionName = `region_${regionName.replace(/\./g, '_')}`;
      }
      const regionBand = `${apiRegionName}_${band}`;
      const title = window.satelliteOverlayGallery.getBandDisplayName
        ? window.satelliteOverlayGallery.getBandDisplayName(band)
        : band;

      return {
        id: regionBand,
        imageUrl: `data:image/png;base64,${imageB64}`,
        title,
        subtitle: regionName,
        status: 'ready',
        bandType: title
      };
    });

    window.satelliteOverlayGallery.showImages(items);
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
    console.log('displayLidarRasterForRegion called with region:', regionName);
    if (window.rasterOverlayGallery) {
      console.log('RasterOverlayGallery found, calling loadRasters');
      window.rasterOverlayGallery.loadRasters(regionName);
    } else {
      console.error('window.rasterOverlayGallery not found!');
    }
  },

  /**
   * Display LIDAR raster images in the Processing Results gallery
   * @param {Array} availableRasters - Array of available raster data
   */
  displayLidarRasterGallery(availableRasters) {
    console.log('displayLidarRasterGallery called with rasters:', availableRasters);
    if (window.rasterOverlayGallery) {
      console.log('RasterOverlayGallery found, preparing items');
      const items = availableRasters.map(r => ({
        id: r.processingType,
        imageUrl: `data:image/png;base64,${r.overlayData.image_data}`,
        title: r.display,
        status: 'ready'
      }));
      console.log('Mapped items for gallery:', items);
      window.rasterOverlayGallery.showRasters(items);
    } else {
      console.error('window.rasterOverlayGallery not found in displayLidarRasterGallery!');
    }
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
      { id: 'lrm', label: 'Local Relief Model', color: '#1abc9c' },
      { id: 'sky_view_factor', label: 'Sky View Factor', color: '#ffeaa7' },
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
  async showProgress(message) { // Made async
    // Load the modal HTML first into the placeholder
    await loadModule('modules/modals/progress-modal.html', 'modals-placeholder'); // Ensure loadModule is accessible

    // After modal HTML is loaded, then proceed with original logic
    // Note: The modal ID is #progress-modal as defined in progress-modal.html
    const modal = $('#modals-placeholder #progress-modal'); // Target within placeholder
    if (!modal.length) {
      console.error('Progress modal not found after loading.');
      return;
    }

    const title = modal.find('#progress-title');
    const status = modal.find('#progress-status');
    const progressBar = modal.find('#progress-bar');
    const details = modal.find('#progress-details');

    if (title.length) title.text('Processing...');
    if (status.length) status.text(message || 'Initializing...');
    if (progressBar.length) progressBar.css('width', '0%');
    if (details.length) details.text('');

    modal.fadeIn(); // Show the loaded modal
    Utils.log('info', `Progress modal shown: ${message}`);

    // It's good practice to re-initialize specific handlers if not fully covered by delegation,
    // especially if there are complex interactions within this modal beyond just close.
    // this.reinitializeModalEventHandlers('#modals-placeholder #progress-modal');
    // For now, existing delegation for close buttons should work.
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
    // Ensure we are targeting the modal within the placeholder if it's loaded there
    const modal = $('#modals-placeholder #progress-modal');
    if (modal.length) {
        modal.fadeOut(() => {
            // Optional: remove the specific modal from placeholder to keep DOM clean
            // modal.remove();
            // Or if modals-placeholder should only ever hold one modal at a time:
            // $('#modals-placeholder').empty();
        });
    } else {
        // Fallback for modals not in placeholder (if any are left)
        $('#progress-modal').fadeOut();
    }
    Utils.log('info', 'Progress modal hidden');
  },

  /**
   * Show image modal
   * @param {string} imageSrc - Source URL of the image
   * @param {string} imageAlt - Alt text for the image (used as caption)
   */
  async showImageModal(imageSrc, imageAlt) { // Made async
    await loadModule('modules/modals/image-modal.html', 'modals-placeholder');

    const modal = $('#modals-placeholder #image-modal'); // Target within placeholder
    if (!modal.length) {
        console.error('Image modal not found after loading.');
        Utils.log('error', 'Image modal elements not found after loading.');
        return;
    }

    const imgElement = modal.find('#image-modal-img');
    const captionElement = modal.find('#image-modal-caption');
    const titleElement = modal.find('#image-modal-title');

    if (imgElement.length && captionElement.length && titleElement.length) {
      imgElement.attr('src', imageSrc);
      imgElement.attr('alt', imageAlt);
      captionElement.text(imageAlt);
      titleElement.text(imageAlt || 'Image Preview');
      
      modal.fadeIn();
      Utils.log('info', `Image modal shown for: ${imageAlt}`);

      // Re-attach specific handlers if needed, though close is delegated
      // this.reinitializeModalEventHandlers('#modals-placeholder #image-modal');
    } else {
      Utils.log('error', 'Image modal internal elements not found after loading.');
    }
  },

  /**
   * Hide image modal
   */
  hideImageModal() {
    const modal = $('#modals-placeholder #image-modal'); // Target within placeholder
    if (modal.length) {
      modal.fadeOut(() => {
        // Optional: Clear image source to free memory
        // modal.find('#image-modal-img').attr('src', '');
        // $('#modals-placeholder').empty(); // Or modal.remove();
      });
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

  /**
   * Initialize the Results tab
   */
  initializeResultsTab() {
    if (!this.resultsTabInitialized) {
      Utils.log('info', 'Initializing Results tab for the first time.');
      if (window.ResultsManager && typeof window.ResultsManager.init === 'function') {
        window.ResultsManager.init();
      } else {
        Utils.log('warn', 'ResultsManager not found or init function missing.');
      }
      this.resultsTabInitialized = true;
    } else {
      Utils.log('info', 'Results tab switched - refreshing anomaly filters and event listeners.');
      // Re-attach event listeners in case the DOM was reloaded
      if (window.ResultsManager && typeof window.ResultsManager.attachEventListeners === 'function') {
        window.ResultsManager.attachEventListeners();
      }
      // Always refresh anomaly filters when tab is accessed
      if (window.ResultsManager && typeof window.ResultsManager.refreshAnomalyFilters === 'function') {
        window.ResultsManager.refreshAnomalyFilters();
      }
    }
  },

  /**
   * Re-initializes event handlers for a specific modal after it's loaded.
   * @param {string} modalSelector - The CSS selector for the modal (e.g., '#file-modal') or null if contextElement is the modal.
   * @param {HTMLElement} contextElementPassed - The DOM element where the modal was loaded (usually 'modals-placeholder').
   */
  reinitializeModalEventHandlers(modalSelector, contextElementPassed) {
    const contextNode = contextElementPassed || document.getElementById('modals-placeholder') || document;
    const $modal = modalSelector ? $(contextNode).find(modalSelector) : $(contextNode);

    if (!$modal.length || !$modal.hasClass('modal')) {
        if(modalSelector) console.warn(`Modal not found with selector ${modalSelector} in reinitializeModalEventHandlers.`);
        return;
    }

    const modalId = $modal.attr('id');
    Utils.log('info', `Re-initializing event handlers for modal: ${modalId || 'unknown modal'}`);

    // General close buttons if not already covered by global delegation
    // This ensures that if a modal's HTML is simple and relies on a common '.modal-close' class, it works.
    $modal.find('.modal-close').off('click').on('click', function() {
        $modal.fadeOut(() => {
            if ($modal.parent().is('#modals-placeholder')) {
                // $modal.remove(); // Or $('#modals-placeholder').empty(); if only one modal at a time
            }
        });
    });

    // Specific re-initializations based on modal ID
    // This is where you'd call specific setup functions for each modal's unique interactions
    // if they are not handled by broader delegated event listeners or class initializations.
    // For example, if 'laz-file-modal' has complex internal event logic not covered by its class's init:
    // if (modalId === 'laz-file-modal' && window.geoTiffLeftPanelInstance) {
    //    window.geoTiffLeftPanelInstance.setupSpecificLazModalInteractions($modal);
    // }
    // Most of our modal-specific JS is now called from initializeDynamicContent via class init methods.
    // This function can serve as a fallback or for very generic re-bindings.
  },

  /**
   * Initialize resizable panels
   * @param {Element} contextElement - Optional context element to scope selectors
   */
  initializeResizablePanels(contextElement = document) {
    const $context = $(contextElement);
    let isResizing = false;
    let currentPanel = null;
    let startX = 0;
    let startWidth = 0;

    // Handle mousedown on resize handles
    $context.find('.resize-handle').off('mousedown').on('mousedown', function(e) {
      e.preventDefault();
      isResizing = true;
      currentPanel = $(this).parent();
      startX = e.pageX;
      startWidth = currentPanel.outerWidth();
      
      $(this).addClass('dragging');
      $('body').addClass('resize-active');
      
      Utils.log('debug', 'Started resizing panel');
    });

    // Handle mousemove for resizing (document level event, only bind once)
    if (!this._resizeMoveHandler) {
      this._resizeMoveHandler = function(e) {
        if (!isResizing || !currentPanel) return;
        
        e.preventDefault();
        const deltaX = e.pageX - startX;
        const newWidth = Math.max(200, Math.min(600, startWidth + deltaX));
        
        currentPanel.css('width', newWidth + 'px');
      };
      $(document).on('mousemove', this._resizeMoveHandler);
    }

    // Handle mouseup to stop resizing (document level event, only bind once)
    if (!this._resizeUpHandler) {
      this._resizeUpHandler = function(e) {
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
      };
      $(document).on('mouseup', this._resizeUpHandler);
    }

    // Load saved panel widths
    $context.find('.resizable-panel').each(function() {
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
    if (!window.satelliteOverlayGallery) {
      Utils.log('warn', 'SatelliteOverlayGallery not initialized, attempting to initialize...');
      
      // Check if the satellite gallery container exists
      const satelliteGalleryContainer = document.getElementById('satellite-gallery');
      if (!satelliteGalleryContainer) {
        Utils.log('warn', 'Satellite gallery container not found, Sentinel-2 images will be displayed when map tab is accessed');
        return;
      }
      
      // Initialize the gallery if container exists
      try {
        window.satelliteOverlayGallery = new window.SatelliteOverlayGallery('satellite-gallery', {
          onAddToMap: (regionBand, bandType) => {
            if (window.UIManager?.addSentinel2OverlayToMap) {
              window.UIManager.addSentinel2OverlayToMap(regionBand, bandType);
            }
          }
        });
        Utils.log('info', 'SatelliteOverlayGallery initialized successfully');
      } catch (error) {
        Utils.log('error', 'Failed to initialize SatelliteOverlayGallery:', error);
        return;
      }
    }

    const items = (files || []).map(fileObj => {
      const band = fileObj.band;
      let apiRegionName = regionName;
      if (!regionName.startsWith('region_')) {
        apiRegionName = `region_${regionName.replace(/\./g, '_')}`;
      }
      const regionBand = `${apiRegionName}_${band}`;
      const title = window.satelliteOverlayGallery.getBandDisplayName
        ? window.satelliteOverlayGallery.getBandDisplayName(band)
        : band;
      return {
        id: regionBand,
        imageUrl: `data:image/png;base64,${fileObj.image}`,
        title,
        subtitle: regionName,
        status: 'ready',
        bandType: title
      };
    });

    window.satelliteOverlayGallery.showImages(items);
  },

  /**
   * Fetches and displays Sentinel-2 images for a given region.
   * Checks for available Sentinel-2 processing results and displays them in the satellite gallery.
   * @param {string} regionName - The name of the region.
   */
  async displaySentinel2ImagesForRegion(regionName) {
    if (!window.satelliteOverlayGallery) {
      Utils.log('warn', 'SatelliteOverlayGallery not initialized, attempting to initialize...');
      
      // Check if the satellite gallery container exists
      const satelliteGalleryContainer = document.getElementById('satellite-gallery');
      if (!satelliteGalleryContainer) {
        Utils.log('warn', 'Satellite gallery container not found, Sentinel-2 images will be loaded when map tab is accessed');
        return;
      }
      
      // Initialize the gallery if container exists
      try {
        window.satelliteOverlayGallery = new window.SatelliteOverlayGallery('satellite-gallery', {
          onAddToMap: (regionBand, bandType) => {
            if (window.UIManager?.addSentinel2OverlayToMap) {
              window.UIManager.addSentinel2OverlayToMap(regionBand, bandType);
            }
          }
        });
        Utils.log('info', 'SatelliteOverlayGallery initialized successfully');
      } catch (error) {
        Utils.log('error', 'Failed to initialize SatelliteOverlayGallery:', error);
        return;
      }
    }
    
    await window.satelliteOverlayGallery.loadImages(regionName);
  },

  /**
   * Display Sentinel-2 band images in the satellite gallery
   * @param {Array} availableBands - Array of available band data
   */
  displaySentinel2BandsGallery(availableBands) {
    if (!window.satelliteOverlayGallery) {
      Utils.log('warn', 'SatelliteOverlayGallery not initialized, attempting to initialize...');
      
      // Check if the satellite gallery container exists
      const satelliteGalleryContainer = document.getElementById('satellite-gallery');
      if (!satelliteGalleryContainer) {
        Utils.log('warn', 'Satellite gallery container not found, Sentinel-2 images will be displayed when map tab is accessed');
        return;
      }
      
      // Initialize the gallery if container exists
      try {
        window.satelliteOverlayGallery = new window.SatelliteOverlayGallery('satellite-gallery', {
          onAddToMap: (regionBand, bandType) => {
            if (window.UIManager?.addSentinel2OverlayToMap) {
              window.UIManager.addSentinel2OverlayToMap(regionBand, bandType);
            }
          }
        });
        Utils.log('info', 'SatelliteOverlayGallery initialized successfully');
      } catch (error) {
        Utils.log('error', 'Failed to initialize SatelliteOverlayGallery:', error);
        return;
      }
    }

    const items = (availableBands || []).map(bandData => {
      const { band, overlayData, regionName } = bandData;
      const imageB64 = overlayData.image_data;

      let apiRegionName = regionName;
      if (!regionName.startsWith('region_')) {
        apiRegionName = `region_${regionName.replace(/\./g, '_')}`;
      }
      const regionBand = `${apiRegionName}_${band}`;
      const title = window.satelliteOverlayGallery.getBandDisplayName
        ? window.satelliteOverlayGallery.getBandDisplayName(band)
        : band;

      return {
        id: regionBand,
        imageUrl: `data:image/png;base64,${imageB64}`,
        title,
        subtitle: regionName,
        status: 'ready',
        bandType: title
      };
    });

    window.satelliteOverlayGallery.showImages(items);
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
    console.log('displayLidarRasterForRegion called with region:', regionName);
    if (window.rasterOverlayGallery) {
      console.log('RasterOverlayGallery found, calling loadRasters');
      window.rasterOverlayGallery.loadRasters(regionName);
    } else {
      console.error('window.rasterOverlayGallery not found!');
    }
  },

  /**
   * Display LIDAR raster images in the Processing Results gallery
   * @param {Array} availableRasters - Array of available raster data
   */
  displayLidarRasterGallery(availableRasters) {
    console.log('displayLidarRasterGallery called with rasters:', availableRasters);
    if (window.rasterOverlayGallery) {
      console.log('RasterOverlayGallery found, preparing items');
      const items = availableRasters.map(r => ({
        id: r.processingType,
        imageUrl: `data:image/png;base64,${r.overlayData.image_data}`,
        title: r.display,
        status: 'ready'
      }));
      console.log('Mapped items for gallery:', items);
      window.rasterOverlayGallery.showRasters(items);
    } else {
      console.error('window.rasterOverlayGallery not found in displayLidarRasterGallery!');
    }
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
      { id: 'lrm', label: 'Local Relief Model', color: '#1abc9c' },
      { id: 'sky_view_factor', label: 'Sky View Factor', color: '#ffeaa7' },
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
   * Event listener for the reload raster gallery button
   */
  initializeReloadRasterButton() {
    $(document).on('click', '#reload-raster-gallery-btn', function() {
      console.log("🔄 Reload Raster Gallery button clicked");
      console.log("🔍 Checking for selected region...");
      
      // Debug: Log all potential region sources
      console.log("UIManager.globalSelectedRegion:", UIManager.globalSelectedRegion);
      console.log("Global region selector element:", $('#global-region-selector'));
      console.log("Global region selector value:", $('#global-region-selector').val());
      
      // Try multiple ways to get the selected region
      let selectedRegion = UIManager.globalSelectedRegion;
      
      // If not found, try to get it from the global region selector
      if (!selectedRegion) {
        const regionSelector = $('#global-region-selector');
        if (regionSelector.length && regionSelector.val()) {
          selectedRegion = regionSelector.val();
          console.log("✅ Found region from selector:", selectedRegion);
        }
      }
      
      // If still not found, try to get it from the current URL or other sources
      if (!selectedRegion) {
        // Check if there are any regions available and use the first one as fallback
        const regionOptions = $('#global-region-selector option');
        console.log("Available region options:", regionOptions.length);
        regionOptions.each(function(i, option) {
          console.log(`  Option ${i}: ${$(option).val()} - ${$(option).text()}`);
        });
        
        if (regionOptions.length > 1) { // More than just the default option
          selectedRegion = regionOptions.eq(1).val(); // Get first actual region
          console.log("🔄 Using fallback region:", selectedRegion);
        }
      }
      
      if (selectedRegion && selectedRegion !== 'default' && selectedRegion !== '') {
        console.log("🚀 Loading rasters for region:", selectedRegion);
        if (window.rasterOverlayGallery) {
          window.rasterOverlayGallery.loadRasters(selectedRegion);
          Utils.showToast(`Reloading rasters for ${selectedRegion}...`, "info");
        } else {
          console.error('❌ RasterOverlayGallery not found!');
          Utils.showToast("Gallery not initialized. Please refresh the page.", "error");
        }
      } else {
        console.warn("⚠️ No valid region found for reload");
        Utils.showToast("Please select a region first, or wait for regions to load.", "warning");
      }
    });
  }
};
