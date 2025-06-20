/**
 * Main application entry point - Modular SHO to Z Web Interface
 * Coordinates all modules and initializes the application
 */

async function loadModule(modulePath, targetElementId) {
  try {
    console.log('🔍 DEBUG: loadModule called with:', modulePath, targetElementId);
    // Adjust path if necessary. Assuming /static/ maps to frontend/
    const fetchPath = modulePath.startsWith('/') ? modulePath : `/static/${modulePath}`;
    console.log('🔍 DEBUG: Final fetch path:', fetchPath);
    
    const response = await fetch(fetchPath);
    console.log('🔍 DEBUG: Fetch response status:', response.status, response.statusText);
    
    if (!response.ok) {
      throw new Error(`Failed to load module ${fetchPath}: ${response.statusText}`);
    }
    const html = await response.text();
    console.log('🔍 DEBUG: HTML content length:', html.length);
    console.log('🔍 DEBUG: HTML preview (first 200 chars):', html.substring(0, 200));
    
    const targetElement = document.getElementById(targetElementId);
    if (targetElement) {
      console.log('🔍 DEBUG: Found target element, setting innerHTML');
      targetElement.innerHTML = html;
      
      // Verify what was actually loaded
      const openaiTab = document.getElementById('openai-analysis-tab');
      console.log('🔍 DEBUG: After innerHTML, openai-analysis-tab exists:', !!openaiTab);
      
      // Call the global initializer function after content is loaded
      if (typeof window.initializeDynamicContent === 'function') {
        console.log('🔍 DEBUG: Calling initializeDynamicContent');
        // modulePath can serve as a hint for what was loaded.
        // Or, a more specific contextName could be passed from where loadModule is called.
        window.initializeDynamicContent(targetElement, modulePath);
      } else {
        console.error('🔍 DEBUG: initializeDynamicContent not available');
      }
    } else {
      console.error(`Target element ${targetElementId} not found for module ${fetchPath}`);
    }
  } catch (error) {
    console.error(`Error loading module ${modulePath}:`, error);
  }
}

// Import all modules (using script tags in HTML, but documented here for clarity)
// - utils.js - Utility functions and helpers
// - map.js - Map initialization and management
// - fileManager.js - File loading and LAZ file management
// - overlays.js - Map overlay management
// - processing.js - Processing operations
// - websocket.js - WebSocket communication
// - ui.js - UI interactions and interface management

// Global application state
const SHOtoZ = {
  version: '2.0.0',
  initialized: false,
  modules: {}
};

/**
 * Initialize the application
 */
async function initializeApplication() {
  console.log('*** SHO to Z - Starting Application Initialization ***');
  
  try {
    // Wait for DOM to be ready
    await waitForDOM();

    // Load essential layout modules first
    await loadModule('modules/header.html', 'header-placeholder');
    await loadModule('modules/global-region-selector.html', 'global-region-selector-placeholder');
    await loadModule('modules/tab-navigation.html', 'tab-nav-placeholder');
    // Add other essential layout modules here if needed, e.g.:
    // await loadModule('modules/modals.html', 'modals-placeholder');
    
    // Initialize modules in order
    await initializeModules();
    
    // Setup global event listeners
    setupGlobalEventListeners();
    
    // Load user preferences
    loadApplicationPreferences();
    
    // Mark as initialized
    SHOtoZ.initialized = true;

    // Load default tab content (e.g., map tab)
    if (window.UIManager && typeof UIManager.loadTabContent === 'function') {
      await UIManager.loadTabContent('map');
    } else {
      console.error("UIManager.loadTabContent is not available to load default tab.");
    }
    
    console.log('*** SHO to Z - Application Initialized Successfully ***');
    Utils.showNotification('Application initialized successfully', 'success', 2000);
    
  } catch (error) {
    console.error('*** SHO to Z - Application Initialization Failed ***', error);
    Utils.showNotification('Application initialization failed', 'error', 0);
  }
}

/**
 * Wait for DOM to be ready
 */
function waitForDOM() {
  return new Promise((resolve) => {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', resolve);
    } else {
      resolve();
    }
  });
}

/**
 * Initialize all modules
 */
async function initializeModules() {
  console.log('*** Initializing Modules ***');
  
  // Check if all required modules are available
  const requiredModules = ['Utils', 'MapManager', 'FileManager', 'OverlayManager', 'ProcessingManager', 'WebSocketManager', 'UIManager', 'SavedPlaces'];
  const missingModules = requiredModules.filter(module => !window[module]);
  
  if (missingModules.length > 0) {
    throw new Error(`Missing required modules: ${missingModules.join(', ')}`);
  }
  
  // Store module references
  SHOtoZ.modules = {
    utils: Utils,
    map: MapManager,
    fileManager: FileManager,
    overlayManager: OverlayManager,
    processingManager: ProcessingManager,
    webSocket: WebSocketManager,
    ui: UIManager,
    savedPlaces: SavedPlaces
  };
  
  // Initialize modules in dependency order
  try {
    // 1. Initialize UI Manager first (sets up basic interface)
    console.log('*** Initializing UI Manager ***');
    UIManager.init();
    
    // 2. Map Manager will be initialized when map tab content is loaded
    console.log('*** Map Manager initialization deferred to tab loading ***');
    // MapManager.init() will be called from initializeDynamicContent when map tab is loaded
    
    // 3. Initialize WebSocket Manager (for real-time updates)
    console.log('*** Initializing WebSocket Manager ***');
    WebSocketManager.init();
    
    // 4. Initialize Saved Places (after map is ready)
    console.log('*** Initializing Saved Places ***');
    SavedPlaces.init();
    
    // 5. Load files after all UI components are ready
    console.log('*** Loading LAZ Files ***');
    await FileManager.loadFiles();
    
    console.log('*** All modules initialized successfully ***');
    
  } catch (error) {
    console.error('*** Module initialization failed ***', error);
    throw error;
  }
}

/**
 * Setup global event listeners
 */
function setupGlobalEventListeners() {
  console.log('*** Setting up global event listeners ***');
  
  // Handle window resize
  window.addEventListener('resize', Utils.debounce(() => {
    if (MapManager.map) {
      MapManager.map.invalidateSize();
    }
  }, 250));
  
  // Handle page visibility changes
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // Page is hidden - could pause some operations
      console.log('*** Page hidden - reducing activity ***');
    } else {
      // Page is visible - resume operations
      console.log('*** Page visible - resuming activity ***');
      
      // Refresh file list if needed
      if (FileManager.loadFiles) {
        FileManager.loadFiles();
      }
    }
  });
  
  // Handle before page unload
  window.addEventListener('beforeunload', (event) => {
    // Save preferences
    if (UIManager.savePreferences) {
      UIManager.savePreferences();
    }
    
    // Close WebSocket connection
    if (WebSocketManager.disconnect) {
      WebSocketManager.disconnect();
    }
    
    // Check for active processes
    if (ProcessingManager.hasActiveProcesses && ProcessingManager.hasActiveProcesses()) {
      event.preventDefault();
      event.returnValue = 'You have active processing operations. Are you sure you want to leave?';
    }
  });
  
  // Handle errors
  window.addEventListener('error', (event) => {
    Utils.log('error', 'Global error caught', {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: event.error
    });
  });
  
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    Utils.log('error', 'Unhandled promise rejection', event.reason);
    event.preventDefault(); // Prevent console logging
  });
  
  console.log('*** Global event listeners setup complete ***');
}

/**
 * Load application preferences
 */
function loadApplicationPreferences() {
  console.log('*** Loading application preferences ***');
  
  // Load UI preferences
  if (UIManager.loadPreferences) {
    UIManager.loadPreferences();
  }
  
  // Load other preferences as needed
  // TODO: Add more preference loading as modules grow
  
  console.log('*** Application preferences loaded ***');
}

/**
 * Get application status
 */
function getApplicationStatus() {
  return {
    initialized: SHOtoZ.initialized,
    version: SHOtoZ.version,
    modules: Object.keys(SHOtoZ.modules),
    mapReady: !!MapManager.map,
    selectedFile: FileManager.getSelectedFile(),
    activeProcesses: ProcessingManager.getActiveProcesses(),
    webSocketStatus: WebSocketManager.getConnectionStatus(),
    activeOverlays: OverlayManager.getActiveOverlays()
  };
}

/**
 * Restart application (for debugging/development)
 */
function restartApplication() {
  console.log('*** Restarting application ***');
  
  // Clear overlays
  if (OverlayManager.clearAllOverlays) {
    OverlayManager.clearAllOverlays();
  }
  
  // Disconnect WebSocket
  if (WebSocketManager.disconnect) {
    WebSocketManager.disconnect();
  }
  
  // Clear file selection
  if (FileManager.clearSelection) {
    FileManager.clearSelection();
  }
  
  // Reload page
  window.location.reload();
}

// Expose global functions for debugging and external access
window.SHOtoZ = SHOtoZ;
window.getApplicationStatus = getApplicationStatus;
window.restartApplication = restartApplication;
window.loadModule = loadModule; // Make loadModule globally available

// jQuery document ready - start the application
$(function () {
  console.log('*** jQuery document ready fired! ***');
  console.log('*** Leaflet available:', typeof L !== 'undefined' ? 'YES' : 'NO');
  
  // Add a small delay to ensure all scripts are loaded
  setTimeout(() => {
    initializeApplication();
  }, 100);
});

/**
 * Legacy compatibility layer for old app.js functionality
 * These functions maintain compatibility with existing HTML event handlers
 */

// Legacy function names that might be called from HTML
window.sendProcess = function(target) {
  if (ProcessingManager && ProcessingManager.sendProcess) {
    return ProcessingManager.sendProcess(target);
  }
};

window.addImageOverlayToMap = function(processingType) {
  if (OverlayManager && OverlayManager.addProcessingOverlay) {
    return OverlayManager.addProcessingOverlay(processingType);
  }
};

window.loadFiles = function() {
  if (FileManager && FileManager.loadFiles) {
    return FileManager.loadFiles();
  }
};

// Export for module system compatibility
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SHOtoZ, initializeApplication };
}
