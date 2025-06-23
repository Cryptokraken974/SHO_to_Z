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

  /**
   * Initialize image modal event handlers
   * This method handles setup for image viewing modals
   */
  initializeImageModalEventHandlers() {
    Utils.log('debug', 'Initializing image modal event handlers');
    
    // Add basic image modal functionality
    // This can be expanded later when image modal features are needed
    $(document).off('click', '.image-modal-close').on('click', '.image-modal-close', function() {
      $(this).closest('.modal').fadeOut();
    });
    
    // Handle image modal background click to close
    $(document).off('click', '#image-modal').on('click', '#image-modal', function(e) {
      if (e.target === this) {
        $(this).fadeOut();
      }
    });
    
    Utils.log('info', 'Image modal event handlers initialized');
  },

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
    
    // Satellite gallery removed - NDVI now handled in raster gallery
    Utils.log('info', '🗑️ Note: Satellite gallery removed - NDVI now available in raster gallery');
    
    // Load satellite images and LIDAR data for the region
    // ALWAYS load both Sentinel-2 images AND LiDAR data regardless of file type
    // Use processing region name for consistent Sentinel-2 calls
    const sentinel2RegionName = processingRegion || regionName;
    Utils.log('info', `🛰️ === HANDLESELECTION (Satellite gallery removed) ===`);
    Utils.log('info', `📍 Display Name: ${regionName}`);
    Utils.log('info', `📍 Processing Region: ${processingRegion}`);
    Utils.log('info', `📍 Using Region Name: ${sentinel2RegionName}`);
    Utils.log('info', `📍 File Path: ${filePath}`);
    // Satellite gallery removed - NDVI now handled in raster gallery
    
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

    // Get Copernicus DSM button - Use event delegation
    $(document).on('click', '#get-copernicus-dsm-btn', () => {
      this.acquireCopernicusDSM();
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
        // Potentially clear #modals-placeholder or specific modal ID here
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

        Utils.showNotification('Test overlay to map! Look for a black rectangle with red border.', 'success');
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
    
    // Check if we have a selected region - satellite gallery removed, NDVI now in raster gallery
    if (FileManager.selectedRegion) {
      Utils.log('info', 'Note: Satellite gallery removed - NDVI now available in raster gallery');
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
        
        // 🛰️ If NDVI processing was completed, refresh satellite gallery
        if (result.ndvi_completed && result.trigger_satellite_refresh) {
          const refreshRegion = result.trigger_satellite_refresh;
          Utils.log('info', `🛰️ NDVI processing completed - refreshing satellite gallery for region: ${refreshRegion}`);
          console.log('🛰️ NDVI COMPLETION DETECTED:', { 
            ndvi_completed: result.ndvi_completed, 
            trigger_satellite_refresh: result.trigger_satellite_refresh,
            refreshRegion 
          });
          
          // NDVI is now handled in raster gallery - no satellite gallery refresh needed
          setTimeout(() => {
            Utils.log('info', '🔄 NDVI now handled in raster gallery - satellite gallery removed');
            // Note: NDVI images are now available in the raster gallery
          }, 2000);
          
          Utils.showNotification('🌱 NDVI imagery updated and available in raster gallery!', 'success');
        } else {
          console.log('🛰️ No NDVI completion detected in result:', { 
            ndvi_completed: result.ndvi_completed, 
            trigger_satellite_refresh: result.trigger_satellite_refresh 
          });
        }
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
   * Get display name for processing types
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
      'tpi': 'TPI',
      'roughness': 'Roughness',
      'sky_view_factor': 'Sky View Factor',
      'ndvi': 'NDVI (Vegetation Index)',
      'hs_red': 'Hillshade Red',
      'hs_green': 'Hillshade Green',
      'hs_blue': 'Hillshade Blue',
      'color_relief': 'Color Relief',
      'slope_relief': 'Slope Relief',
      'lrm': 'Local Relief Model',
      'hillshade_rgb': 'RGB Hillshade',
      'tint_overlay': 'Tint Overlay',
      'boosted_hillshade': 'Boosted Hillshade'
    };
    
    return displayNames[processingType] || processingType.charAt(0).toUpperCase() + processingType.slice(1);
  },

  /**
   * Add LIDAR raster overlay to map
   * @param {string} regionName - Region name
   * @param {string} processingType - Processing type
   * @param {string} displayName - Display name for notifications
   * @returns {Promise<boolean>} Success status
   */
  async addLidarRasterOverlayToMap(regionName, processingType, displayName) {
    try {
      // Try multiple ways to get the raster data
      let data = null;
      
      // Method 1: Use overlays service if available
      if (window.overlays && typeof window.overlays === 'function') {
        try {
          data = await overlays().getRasterOverlayData(regionName, processingType);
        } catch (serviceError) {
          Utils.log('warn', 'Overlays service failed, trying direct API call:', serviceError);
        }
      }
      
      // Method 2: Direct API call as fallback
      if (!data || !data.success) {
        try {
          const response = await fetch(`/api/overlay/raster/${encodeURIComponent(regionName)}_${processingType}`);
          if (response.ok) {
            data = await response.json();
          }
        } catch (apiError) {
          Utils.log('warn', 'Direct API call failed:', apiError);
        }
      }
      
      if (data && data.success && data.bounds && data.image_data) {
        const bounds = [
          [data.bounds.south, data.bounds.west], 
          [data.bounds.north, data.bounds.east]
        ];
        const imageUrl = `data:image/png;base64,${data.image_data}`;
        const overlayKey = `LIDAR_RASTER_${regionName}_${processingType}`;
        
        // Add overlay using OverlayManager
        if (window.OverlayManager && window.OverlayManager.addImageOverlay) {
          const success = window.OverlayManager.addImageOverlay(overlayKey, imageUrl, bounds);
          if (success) {
            Utils.showNotification(`Added ${displayName} overlay to map`, 'success');
            return true;
          }
        }
      }
      
      Utils.showNotification(`Failed to add ${displayName} overlay to map`, 'error');
      return false;
    } catch (error) {
      Utils.log('error', `Failed to add LIDAR raster overlay: ${error}`);
      Utils.showNotification(`Error adding ${displayName} overlay: ${error.message}`, 'error');
      return false;
    }
  },

  /**
   * Event listener for the reload raster gallery button
   */
  initializeReloadRasterButton() {
    $(document).on('click', '#reload-raster-gallery-btn', function() {
      console.log("Reloading raster gallery...");
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
      
      if (selectedItem.length && selectedItem.data('coords')) {
        coords = selectedItem.data('coords');
        Utils.log('info', `Found coordinates in selected item data:`, coords);
      }
      
      if (!coords && $('#lat-input').val() && $('#lng-input').val()) {
        const inputLat = parseFloat($('#lat-input').val());
        const inputLng = parseFloat($('#lng-input').val());
        
        if (Utils.isValidCoordinate(inputLat, inputLng)) {
          coords = { lat: inputLat, lng: inputLng };
          Utils.log('info', `Using coordinates from input fields:`, coords);
        }
      }
      
      if (coords && Utils.isValidCoordinate(coords.lat, coords.lng)) {
        lat = coords.lat;
        lng = coords.lng;
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        Utils.log('info', `Using coordinates from selected region: ${lat}, ${lng}`);
      }
    }

    // If still no coordinates are set, use map center or default location
    if (!lat || !lng || lat === '' || lng === '') {
      // Try to get current map center
      if (window.MapManager && MapManager.map) {
        const center = MapManager.map.getCenter();
        lat = center.lat;
        lng = center.lng;
        
        // Update the input fields
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        
        Utils.showNotification('Using current map center for elevation data acquisition', 'info');
      } else {
        // Fall back to Portland, Oregon
        lat = 45.5152;
        lng = -122.6784;
        
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        
        Utils.showNotification('Using Portland, Oregon coordinates for elevation data acquisition', 'info');
      }
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
   * Acquire Copernicus DSM data for the current coordinates
   */
  async acquireCopernicusDSM() {
    Utils.log('info', 'Get Copernicus DSM button clicked');

    // Get coordinates from input fields
    let lat = $('#lat-input').val();
    let lng = $('#lng-input').val();
    let regionName = $('#region-name-input').val();

    // Check if we have a selected region but no region name
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
      
      if (selectedItem.length && selectedItem.data('coords')) {
        coords = selectedItem.data('coords');
        Utils.log('info', `Found coordinates in selected item data:`, coords);
      }
      
      if (!coords && $('#lat-input').val() && $('#lng-input').val()) {
        const inputLat = parseFloat($('#lat-input').val());
        const inputLng = parseFloat($('#lng-input').val());
        
        if (Utils.isValidCoordinate(inputLat, inputLng)) {
          coords = { lat: inputLat, lng: inputLng };
          Utils.log('info', `Using coordinates from input fields:`, coords);
        }
      }
      
      if (coords && Utils.isValidCoordinate(coords.lat, coords.lng)) {
        lat = coords.lat;
        lng = coords.lng;
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        Utils.log('info', `Using coordinates from selected region: ${lat}, ${lng}`);
      }
    }

    // If still no coordinates are set, use map center or default location
    if (!lat || !lng || lat === '' || lng === '') {
      // Try to get current map center
      if (window.MapManager && MapManager.map) {
        const center = MapManager.map.getCenter();
        lat = center.lat;
        lng = center.lng;
        
        // Update the input fields
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        
        Utils.showNotification('Using current map center for DSM data acquisition', 'info');
      } else {
        // Fall back to Portland, Oregon
        lat = 45.5152;
        lng = -122.6784;
        
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        
        Utils.showNotification('Using Portland, Oregon coordinates for DSM data acquisition', 'info');
      }
    }

    // Validate coordinates
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);

    if (!Utils.isValidCoordinate(latNum, lngNum)) {
      Utils.showNotification('Invalid coordinates. Please enter valid latitude and longitude values.', 'error');
      return;
    }

    // Generate region name if not provided
    if (!regionName || regionName.trim() === '') {
      regionName = `${Math.abs(latNum).toFixed(2)}${latNum >= 0 ? 'N' : 'S'}_${Math.abs(lngNum).toFixed(2)}${lngNum >= 0 ? 'E' : 'W'}`;
      $('#region-name-input').val(regionName);
      Utils.log('info', `Auto-generated region name: ${regionName}`);
    }

    try {
      this.showProgress('🌍 Downloading Copernicus DSM data...');

      const requestData = {
        region_name: regionName,
        latitude: latNum,
        longitude: lngNum,
        buffer_km: 5.0,  // Default 5km buffer
        resolution: '30m'  // Default 30m resolution
      };

      Utils.log('info', 'Sending Copernicus DSM request:', requestData);

      const response = await fetch('/api/download-copernicus-dsm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.success) {
        Utils.log('info', 'Copernicus DSM download successful:', result);
        
        // Create success message with details
        let message = `Copernicus DSM downloaded successfully for region '${regionName}'`;
        if (result.tiles_downloaded) {
          message += ` (${result.tiles_downloaded} tiles merged)`;
        }
        if (result.method) {
          message += ` via ${result.method}`;
        }
        
        Utils.showNotification(message, 'success', 5000);
        
        // Update the map view to the coordinates
        if (MapManager && MapManager.map) {
          MapManager.setView(latNum, lngNum, 13);
        }
        
        // Refresh region list if FileManager is available
        if (window.FileManager && typeof FileManager.loadFiles === 'function') {
          setTimeout(() => {
            FileManager.loadFiles();
          }, 1000);
        }
        
      } else {
        throw new Error(result.message || 'Unknown error occurred');
      }

    } catch (error) {
      Utils.log('error', 'Error in Copernicus DSM acquisition:', error);
      Utils.showNotification(`Error downloading DSM data: ${error.message}`, 'error');
    } finally {
      this.hideProgress();
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
   * Acquire combined data: DTM, DSM, CHM, and Sentinel-2 for current coordinates
   * This method orchestrates the complete data acquisition workflow
   */
  async getCombinedData() {
    Utils.log('info', 'Combined data acquisition started');

    // Get coordinates from input fields
    let lat = $('#lat-input').val();
    let lng = $('#lng-input').val();
    let regionName = $('#region-name-input').val();

    // Check if we have a selected region but no region name

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
      
      if (selectedItem.length && selectedItem.data('coords')) {
        coords = selectedItem.data('coords');
        Utils.log('info', `Found coordinates in selected item data:`, coords);
      }
      
      if (!coords && $('#lat-input').val() && $('#lng-input').val()) {
        const inputLat = parseFloat($('#lat-input').val());
        const inputLng = parseFloat($('#lng-input').val());
        
        if (Utils.isValidCoordinate(inputLat, inputLng)) {
          coords = { lat: inputLat, lng: inputLng };
          Utils.log('info', `Using coordinates from input fields:`, coords);
        }
      }
      
      if (coords && Utils.isValidCoordinate(coords.lat, coords.lng)) {
        lat = coords.lat;
        lng = coords.lng;
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        Utils.log('info', `Using coordinates from selected region: ${lat}, ${lng}`);
      }
    }

    // If still no coordinates are set, use map center or default location
    if (!lat || !lng || lat === '' || lng === '') {
      // Try to get current map center
      if (window.MapManager && MapManager.map) {
        const center = MapManager.map.getCenter();
        lat = center.lat;
        lng = center.lng;
        
        // Update the input fields
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        
        Utils.showNotification('Using current map center for combined data acquisition', 'info');
      } else {
        // Fall back to Portland, Oregon
        lat = 45.5152;
        lng = -122.6784;
        
        $('#lat-input').val(lat);
        $('#lng-input').val(lng);
        
        Utils.showNotification('Using Portland, Oregon coordinates for combined data acquisition', 'info');
      }
    }

    // Validate coordinates
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);

    if (!Utils.isValidCoordinate(latNum, lngNum)) {
      Utils.showNotification('Invalid coordinates. Please enter valid latitude and longitude values.', 'error');
      return;
    }

    try {
      this.showProgress('🌍 Acquiring combined data (DTM + DSM + CHM + Sentinel-2)...');

      // Start WebSocket connection for progress updates
      if (window.WebSocketManager) {
        WebSocketManager.connect();
      }

      // Prepare region name for the acquisition
      const effectiveRegionName = regionName && regionName.trim() !== '' ? regionName.trim() : null;

      // Step 1: Acquire elevation data (DTM)
      Utils.log('info', 'Step 1/4: Acquiring elevation data (DTM)...');
      this.showProgress('🏔️ Step 1/4: Acquiring elevation data (DTM)...');
      
      try {
        const elevationRequest = {
          lat: latNum,
          lng: lngNum,
          buffer_km: 5.0,
          region_name: effectiveRegionName
        };

        // Use elevation service from factory
        const elevationService = elevation();
        const elevationResult = await elevationService.downloadElevationData(elevationRequest);

        if (!elevationResult || !elevationResult.success) {
          throw new Error(elevationResult?.error || 'Elevation data acquisition failed');
        }

        Utils.log('info', 'Step 1/4: Elevation data acquisition completed successfully');
        Utils.showNotification('Step 1/4: Elevation data acquired successfully!', 'success', 3000);
      } catch (elevationError) {
        Utils.log('warn', 'Step 1/4: Elevation data acquisition failed:', elevationError);
        Utils.showNotification(`Step 1/4: Elevation data failed: ${elevationError.message}`, 'warning', 4000);
        // Continue with other steps even if elevation fails
      }

      // Step 2: Acquire Copernicus DSM data
      Utils.log('info', 'Step 2/4: Acquiring Copernicus DSM data...');
      this.showProgress('🌍 Step 2/4: Acquiring Copernicus DSM data...');
      
      try {
        const dsmRequestData = {
          region_name: effectiveRegionName || `${Math.abs(latNum).toFixed(2)}${latNum >= 0 ? 'N' : 'S'}_${Math.abs(lngNum).toFixed(2)}${lngNum >= 0 ? 'E' : 'W'}`,
          latitude: latNum,
          longitude: lngNum,
          buffer_km: 5.0,
          resolution: '30m'
        };

        const dsmResponse = await fetch('/api/download-copernicus-dsm', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(dsmRequestData)
        });

        if (!dsmResponse.ok) {
          const errorData = await dsmResponse.json();
          throw new Error(errorData.detail || `HTTP ${dsmResponse.status}: ${dsmResponse.statusText}`);
        }

        const dsmResult = await dsmResponse.json();
        
        if (!dsmResult.success) {
          throw new Error(dsmResult.message || 'Copernicus DSM acquisition failed');
        }

        Utils.log('info', 'Step 2/4: Copernicus DSM acquisition completed successfully');
        Utils.showNotification('Step 2/4: Copernicus DSM acquired successfully!', 'success', 3000);
      } catch (dsmError) {
        Utils.log('warn', 'Step 2/4: Copernicus DSM acquisition failed:', dsmError);
        Utils.showNotification(`Step 2/4: Copernicus DSM failed: ${dsmError.message}`, 'warning', 4000);
        // Continue with next step even if DSM fails
      }

      // Step 3: Generate CHM (Canopy Height Model)
      Utils.log('info', 'Step 3/4: Generating CHM (Canopy Height Model)...');
      this.showProgress('🌳 Step 3/4: Generating CHM (Canopy Height Model)...');
      
      try {
        const chmRequestData = {
          region_name: effectiveRegionName || `${Math.abs(latNum).toFixed(2)}${latNum >= 0 ? 'N' : 'S'}_${Math.abs(lngNum).toFixed(2)}${lngNum >= 0 ? 'E' : 'W'}`,
          latitude: latNum,
          longitude: lngNum
        };

        const chmResponse = await fetch('/api/generate-coordinate-chm', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(chmRequestData)
        });

        if (!chmResponse.ok) {
          const errorData = await chmResponse.json();
          throw new Error(errorData.detail || `HTTP ${chmResponse.status}: ${chmResponse.statusText}`);
        }

        const chmResult = await chmResponse.json();
        
        if (!chmResult.success) {
          throw new Error(chmResult.message || 'CHM generation failed');
        }

        Utils.log('info', 'Step 3/4: CHM generation completed successfully');
        Utils.showNotification('Step 3/4: CHM (vegetation height) generated successfully!', 'success', 3000);
      } catch (chmError) {
        Utils.log('warn', 'Step 3/4: CHM generation failed:', chmError);
        Utils.showNotification(`Step 3/4: CHM failed: ${chmError.message}`, 'warning', 4000);
        // Continue with next step even if CHM fails
      }

      // Step 4: Check if NDVI is enabled before acquiring Sentinel-2 data
      Utils.log('info', 'Step 4/4: Checking NDVI status before Sentinel-2 acquisition...');
      this.showProgress('🛰️ Step 4/4: Checking NDVI status...');
      
      try {
        const regionNameForCheck = effectiveRegionName || `${Math.abs(latNum).toFixed(2)}${latNum >= 0 ? 'N' : 'S'}_${Math.abs(lngNum).toFixed(2)}${lngNum >= 0 ? 'E' : 'W'}`;
        
        // Check if NDVI is enabled for this region
        const ndviCheckResponse = await fetch(`/api/regions/${encodeURIComponent(regionNameForCheck)}/ndvi-status`);
        let ndviEnabled = false;
        
        if (ndviCheckResponse.ok) {
          const ndviData = await ndviCheckResponse.json();
          ndviEnabled = ndviData.ndvi_enabled;
          Utils.log('info', `NDVI status for region ${regionNameForCheck}: ${ndviEnabled}`);
        } else {
          Utils.log('warn', `Could not check NDVI status for region ${regionNameForCheck}, defaulting to false`);
        }
        
        if (ndviEnabled) {
          Utils.log('info', '🌱 NDVI is enabled - Acquiring Sentinel-2 satellite data...');
          this.showProgress('🛰️ Step 4/4: NDVI enabled - Acquiring Sentinel-2 satellite data...');
          
          const sentinelRequestData = {
            region_name: regionNameForCheck,
            latitude: latNum,
            longitude: lngNum,
            buffer_km: 5.0
          };

          const sentinelResponse = await fetch('/api/download-sentinel2', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(sentinelRequestData)
          });

          if (!sentinelResponse.ok) {
            const errorData = await sentinelResponse.json();
            throw new Error(errorData.detail || `HTTP ${sentinelResponse.status}: ${sentinelResponse.statusText}`);
          }

          const sentinelResult = await sentinelResponse.json();
          
          if (!sentinelResult.success) {
            throw new Error(sentinelResult.message || 'Sentinel-2 acquisition failed');
          }

          Utils.log('info', 'Step 4/4: Sentinel-2 acquisition completed successfully');
          Utils.showNotification('Step 4/4: Sentinel-2 data acquired successfully!', 'success', 3000);
        } else {
          Utils.log('info', '🚫 NDVI is disabled - Skipping Sentinel-2 acquisition');
          this.showProgress('🚫 Step 4/4: NDVI disabled - Skipping Sentinel-2 acquisition...');
          Utils.showNotification('Step 4/4: NDVI disabled - Skipping Sentinel-2 data acquisition', 'info', 3000);
        }
      } catch (sentinelError) {
        Utils.log('warn', 'Step 4/4: Sentinel-2 acquisition failed:', sentinelError);
        Utils.showNotification(`Step 4/4: Sentinel-2 failed: ${sentinelError.message}`, 'warning', 4000);
      }

      // Final success message
      Utils.log('info', 'Combined data acquisition workflow completed');
      Utils.showNotification('Combined data acquisition completed! Check your data folder for results.', 'success', 5000);
      
      // Update the map view to the coordinates
      if (MapManager && MapManager.map) {
        MapManager.setView(latNum, lngNum, 13);
      }
      
      // Refresh region list if FileManager is available
      if (window.FileManager && typeof FileManager.loadFiles === 'function') {
        setTimeout(() => {
          FileManager.loadFiles();
        }, 2000);
      }

      // If we have a region name, try to display data
      if (effectiveRegionName) {
        setTimeout(() => {
          this.displayLidarRasterForRegion(effectiveRegionName);
        }, 3000);
      }

    } catch (error) {
      Utils.log('error', 'Error in combined data acquisition:', error);
      Utils.showNotification(`Error in combined data acquisition: ${error.message}`, 'error');
    } finally {
      this.hideProgress();
    }
  },

  /**
   * Show progress modal with message
   * @param {string} message - Progress message to display
   */
  showProgress(message = 'Processing...') {
    try {
      // Use the component system to show progress modal
      if (window.componentUtils && window.componentUtils.showProgressModal) {
        window.componentUtils.showProgressModal('Processing', message);
      } else {
        // Fallback: try to show progress modal directly
        const progressModal = document.getElementById('progress-modal');
        if (progressModal) {
          const statusElement = progressModal.querySelector('#progress-status');
          if (statusElement) {
            statusElement.textContent = message;
          }
          progressModal.classList.remove('hidden');
        } else {
          // Load progress modal into modals placeholder if it doesn't exist
          this.loadProgressModal(message);
        }
      }
      Utils.log('info', `Progress modal shown: ${message}`);
    } catch (error) {
      Utils.log('error', 'Error showing progress modal:', error);
      // Fallback to notification
      Utils.showNotification(message, 'info');
    }
  },

  /**
   * Update progress modal with percentage and message
   * @param {number} percentage - Progress percentage (0-100)
   * @param {string} message - Progress message
   * @param {string} details - Optional details
   */
  updateProgress(percentage, message, details = null) {
    try {
      // Use the component system to update progress
      if (window.componentUtils && window.componentUtils.updateProgress) {
        window.componentUtils.updateProgress(percentage, message, details);
      } else {
        // Fallback: update progress modal directly
        const progressModal = document.getElementById('progress-modal');
        if (progressModal) {
          const progressBar = progressModal.querySelector('#progress-bar');
          const statusElement = progressModal.querySelector('#progress-status');
          const detailsElement = progressModal.querySelector('#progress-details');
          
          if (progressBar) {
            progressBar.style.width = `${percentage}%`;
          }
          if (statusElement && message) {
            statusElement.textContent = message;
          }
          if (detailsElement && details) {
            detailsElement.textContent = details;
          }
        }
      }
      Utils.log('info', `Progress updated: ${percentage}% - ${message}`);
    } catch (error) {
      Utils.log('error', 'Error updating progress:', error);
    }
  },

  /**
   * Hide progress modal
   */
  hideProgress() {
    try {
      // Use the component system to hide progress modal
      if (window.componentUtils && window.componentUtils.hideProgressModal) {
        window.componentUtils.hideProgressModal();
      } else {
        // Fallback: hide progress modal directly
        const progressModal = document.getElementById('progress-modal');
        if (progressModal) {
          progressModal.classList.add('hidden');
        }
      }
      Utils.log('info', 'Progress modal hidden');
    } catch (error) {
      Utils.log('error', 'Error hiding progress modal:', error);
    }
  },

  /**
   * Load progress modal into modals placeholder
   * @param {string} initialMessage - Initial message to display
   */
  loadProgressModal(initialMessage = 'Processing...') {
    try {
      const modalsPlaceholder = document.getElementById('modals-placeholder');
      if (modalsPlaceholder) {
        // Load progress modal HTML
        const progressModalHTML = `
          <div id="progress-modal" class="modal fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
            <div class="modal-content bg-[#1a1a1a] border border-[#303030] rounded-lg w-[90%] max-w-md">
              <div class="modal-header flex justify-between items-center p-6 border-b border-[#303030]">
                <h3 class="text-white text-lg font-semibold" id="progress-title">Processing</h3>
                <button class="close text-[#ababab] hover:text-white text-xl font-bold" id="progress-close">&times;</button>
              </div>
              <div class="modal-body p-6">
                <div class="text-white mb-4" id="progress-status">${initialMessage}</div>
                <div class="w-full bg-[#303030] rounded-full h-2 mb-4">
                  <div class="bg-[#00bfff] h-2 rounded-full transition-all duration-300" id="progress-bar" style="width: 0%"></div>
                </div>
                <div class="text-[#ababab] text-sm" id="progress-details"></div>
              </div>
              <div class="modal-footer flex justify-end gap-3 p-6 border-t border-[#303030]">
                <button id="cancel-progress" class="cancel-btn bg-[#dc3545] hover:bg-[#c82333] text-white px-4 py-2 rounded-lg font-medium transition-colors">Cancel</button>
              </div>
            </div>
          </div>
        `;
        
        modalsPlaceholder.innerHTML = progressModalHTML;
        
        // Set up event handlers for the modal
        const progressModal = document.getElementById('progress-modal');
        const closeBtn = document.getElementById('progress-close');
        const cancelBtn = document.getElementById('cancel-progress');
        
        [closeBtn, cancelBtn].forEach(btn => {
          if (btn) {
            btn.addEventListener('click', () => {
              this.hideProgress();
            });
          }
        });
        
        // Show the modal
        progressModal.classList.remove('hidden');
      }
    } catch (error) {
      Utils.log('error', 'Error loading progress modal:', error);
    }
  },
};
