/**
 * Saved Places Management System
 * Provides persistent storage and management of user-saved coordinate locations
 */

window.SavedPlaces = {
  // Storage configuration
  STORAGE_FILE_PATH: '/api/saved-places',
  savedPlaces: [],
  
  // UI elements
  saveModal: null,
  placesListContainer: null,
  
  /**
   * Initialize the Saved Places system
   */
  init() {
    Utils.log('info', 'Initializing Saved Places system');
    
    // Initialize with empty array (no persistent storage)
    this.savedPlaces = [];
    
    // Create UI components
    this.createUI();
    
    // Setup event handlers
    this.setupEventHandlers();
    
    Utils.log('info', 'Saved Places system initialized successfully');
  },

  /**
   * Create UI components for Saved Places
   */
  createUI() {
    // Create save place modal
    this.createSaveModal();
    
    // Create places list container
    this.createPlacesListContainer();
    
    // Add save button to coordinate section
    this.addSaveButton();
  },

  /**
   * Create the save place modal
   */
  createSaveModal() {
    const modalHTML = `
      <div id="save-place-modal" class="fixed inset-0 z-[9999] hidden bg-black bg-opacity-75 flex items-center justify-center">
        <div class="bg-[#1a1a1a] border border-[#303030] rounded-lg p-6 w-96 max-w-[90vw]">
          <h3 class="text-white text-lg font-semibold mb-4">Save Current Location</h3>
          
          <div class="space-y-4">
            <!-- Info Banner -->
            <div class="bg-[#0d4a6b] border border-[#00bfff] rounded-lg p-3">
              <div class="flex items-center gap-2 text-[#00bfff] text-xs">
                📁 <span>This will create a complete region with input/output folders</span>
              </div>
            </div>
            
            <!-- Place Name Input -->
            <div>
              <label for="place-name-input" class="block text-xs text-[#ababab] mb-1">Region Name</label>
              <input type="text" id="place-name-input" placeholder="Enter a name for this region" 
                     class="w-full bg-[#262626] border border-[#404040] rounded-lg px-3 py-2 text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#00bfff]">
              <div class="text-xs text-[#666] mt-1">Will create: input/{region_name}/ and output/{region_name}/</div>
            </div>
            
            <!-- Coordinates Display -->
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-xs text-[#ababab] mb-1">Latitude</label>
                <input type="text" id="save-lat-display" readonly 
                       class="w-full bg-[#141414] border border-[#404040] rounded-lg px-3 py-2 text-white text-sm font-mono">
              </div>
              <div>
                <label class="block text-xs text-[#ababab] mb-1">Longitude</label>
                <input type="text" id="save-lng-display" readonly 
                       class="w-full bg-[#141414] border border-[#404040] rounded-lg px-3 py-2 text-white text-sm font-mono">
              </div>
            </div>
            
            <!-- Region Name Display -->
            <div>
              <label class="block text-xs text-[#ababab] mb-1">Suggested Region Name</label>
              <input type="text" id="save-region-display" readonly 
                     class="w-full bg-[#141414] border border-[#404040] rounded-lg px-3 py-2 text-white text-sm font-mono">
            </div>

            <!-- NDVI Enable Option -->
            <div class="bg-[#1a1a1a] border border-[#404040] rounded-lg p-3">
              <div class="flex items-center gap-3">
                <input type="checkbox" id="save-ndvi-enabled" class="w-4 h-4 text-[#00bfff] bg-[#262626] border-[#404040] rounded focus:ring-[#00bfff] focus:ring-2">
                <div>
                  <label for="save-ndvi-enabled" class="text-white font-medium cursor-pointer">NDVI Enabled</label>
                  <p class="text-[#ababab] text-xs mt-1">Enable NDVI processing for vegetation analysis</p>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Action Buttons -->
          <div class="flex justify-end gap-3 mt-6">
            <button id="cancel-save-btn" class="px-4 py-2 bg-[#404040] hover:bg-[#505050] text-white rounded-lg transition-colors">
              Cancel
            </button>
            <button id="confirm-save-btn" class="px-4 py-2 bg-[#007bff] hover:bg-[#0056b3] text-white rounded-lg transition-colors">
              Create Region
            </button>
          </div>
        </div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    this.saveModal = document.getElementById('save-place-modal');
  },

  /**
   * Create the places list container to replace Quick Locations
   */
  createPlacesListContainer() {
    // Find the existing Quick Locations section and replace it
    const quickLocationsLabel = document.querySelector('label[class*="block text-xs text-[#ababab] mb-2"]');
    let targetDiv = null;
    
    // Look for the Quick Locations label specifically
    if (quickLocationsLabel && quickLocationsLabel.textContent.includes('Quick Locations')) {
      targetDiv = quickLocationsLabel.parentElement;
    }
    
    if (targetDiv) {
      // Create new Saved Places section
      const savedPlacesHTML = `
        <div class="mt-4">
          <div class="flex justify-between items-center mb-2">
            <label class="block text-xs text-[#ababab]">Session Places</label>
            <button id="manage-places-btn" class="text-xs text-[#00bfff] hover:text-[#0099cc] transition-colors">
              Info
            </button>
          </div>
          <div id="saved-places-list" class="space-y-2 max-h-48 overflow-y-auto">
            <!-- Session places will be dynamically populated here -->
          </div>
          <div id="no-saved-places" class="text-xs text-[#666] text-center py-4 hidden">
            No session places yet. Create a region to save permanently!
          </div>
        </div>
      `;
      
      targetDiv.innerHTML = savedPlacesHTML;
      this.placesListContainer = document.getElementById('saved-places-list');
      
      Utils.log('info', 'Replaced Quick Locations with Saved Places');
    } else {
      Utils.log('warning', 'Quick Locations section not found, Saved Places will be added elsewhere');
      
      // Fallback: Add to the Go to section if Quick Locations not found
      const gotoContent = document.getElementById('go-to-content');
      if (gotoContent) {
        const savedPlacesHTML = `
          <div class="mt-4">
            <div class="flex justify-between items-center mb-2">
              <label class="block text-xs text-[#ababab]">Session Places</label>
              <button id="manage-places-btn" class="text-xs text-[#00bfff] hover:text-[#0099cc] transition-colors">
                Info
              </button>
            </div>
            <div id="saved-places-list" class="space-y-2 max-h-48 overflow-y-auto">
              <!-- Session places will be dynamically populated here -->
            </div>
            <div id="no-saved-places" class="text-xs text-[#666] text-center py-4 hidden">
              No session places yet. Create a region to save permanently!
            </div>
          </div>
        `;
        
        gotoContent.insertAdjacentHTML('beforeend', savedPlacesHTML);
        this.placesListContainer = document.getElementById('saved-places-list');
        
        Utils.log('info', 'Added Saved Places to Go to section as fallback');
      }
    }
  },

  /**
   * Add save button to the coordinate input section
   */
  addSaveButton() {
    const regionNameInput = document.getElementById('region-name-input');
    if (regionNameInput && regionNameInput.parentElement) {
      const saveButtonHTML = `
        <button id="save-current-place-btn" class="w-full bg-[#ffc107] hover:bg-[#e0a800] text-black px-4 py-2 rounded-lg font-medium transition-colors mt-2 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
          📁 Create Region
        </button>
      `;
      
      regionNameInput.parentElement.insertAdjacentHTML('afterend', saveButtonHTML);
    }
  },

  /**
   * Setup event handlers for Saved Places functionality
   */
  setupEventHandlers() {
    // Save current place button
    const saveBtn = document.getElementById('save-current-place-btn');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => this.showSaveModal());
    }

    // Modal buttons
    const confirmBtn = document.getElementById('confirm-save-btn');
    const cancelBtn = document.getElementById('cancel-save-btn');
    
    if (confirmBtn) {
      confirmBtn.addEventListener('click', () => this.confirmSave());
    }
    
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => this.hideSaveModal());
    }

    // Close modal on background click
    if (this.saveModal) {
      this.saveModal.addEventListener('click', (e) => {
        if (e.target === this.saveModal) {
          this.hideSaveModal();
        }
      });
    }

    // Manage places button
    const manageBtn = document.getElementById('manage-places-btn');
    if (manageBtn) {
      manageBtn.addEventListener('click', () => this.showManageModal());
    }

    // Listen for coordinate changes to enable/disable save button - USING CORRECT IDs
    const latInput = document.getElementById('lat-input');        // Get Data section
    const lngInput = document.getElementById('lng-input');        // Get Data section
    const gotoCoordinatesInput = document.getElementById('goto-coordinates-input'); // Go To section
    
    if (latInput && lngInput) {
      [latInput, lngInput].forEach(input => {
        input.addEventListener('input', () => this.updateSaveButtonState());
      });
    }
    
    // Also listen for changes in the goto-coordinates-input field
    if (gotoCoordinatesInput) {
      gotoCoordinatesInput.addEventListener('input', () => {
        // Parse the coordinates and update the Get Data section fields
        const coordString = gotoCoordinatesInput.value.trim();
        if (coordString) {
          const parsed = Utils.parseCoordinateString(coordString);
          if (parsed && latInput && lngInput) {
            latInput.value = parsed.lat.toFixed(6);
            lngInput.value = parsed.lng.toFixed(6);
            
            // Update region name if field exists
            const regionNameInput = document.getElementById('region-name-input');
            if (regionNameInput) {
              regionNameInput.value = Utils.generateRegionName(parsed.lat, parsed.lng);
            }
          }
        }
        this.updateSaveButtonState();
      });
    }

    // Listen for coordinate capture from map clicks
    if (window.MapManager && window.MapManager.map) {
      window.MapManager.map.on('click', () => {
        setTimeout(() => this.updateSaveButtonState(), 100);
      });
    }
  },

  /**
   * Update save button state based on coordinate availability
   */
  updateSaveButtonState() {
    const saveBtn = document.getElementById('save-current-place-btn');
    const latInput = document.getElementById('lat-input');        // Get Data section
    const lngInput = document.getElementById('lng-input');        // Get Data section
    
    if (saveBtn && latInput && lngInput) {
      const hasCoordinates = latInput.value.trim() !== '' && lngInput.value.trim() !== '';
      saveBtn.disabled = !hasCoordinates;
    }
  },

  /**
   * Show the save place modal
   */
  showSaveModal() {
    const latInput = document.getElementById('lat-input');
    const lngInput = document.getElementById('lng-input');
    const regionNameInput = document.getElementById('region-name-input');
    
    if (!latInput.value || !lngInput.value) {
      Utils.showNotification('Please select coordinates on the map first', 'warning');
      return;
    }

    // Populate modal with current values
    document.getElementById('save-lat-display').value = latInput.value;
    document.getElementById('save-lng-display').value = lngInput.value;
    document.getElementById('save-region-display').value = regionNameInput.value || 'Auto-generated';
    
    // Clear and focus place name input
    const placeNameInput = document.getElementById('place-name-input');
    placeNameInput.value = regionNameInput.value || '';
    
    this.saveModal.classList.remove('hidden');
    placeNameInput.focus();
  },

  /**
   * Hide the save place modal
   */
  hideSaveModal() {
    this.saveModal.classList.add('hidden');
  },

  /**
   * Confirm and save the current place
   */
  async confirmSave() {
    const placeNameInput = document.getElementById('place-name-input');
    const placeName = placeNameInput.value.trim();
    
    if (!placeName) {
      Utils.showNotification('Please enter a name for this place', 'warning');
      placeNameInput.focus();
      return;
    }

    // Check for duplicate names
    if (this.savedPlaces.some(place => place.name.toLowerCase() === placeName.toLowerCase())) {
      Utils.showNotification('A place with this name already exists', 'warning');
      placeNameInput.focus();
      return;
    }

    const lat = parseFloat(document.getElementById('save-lat-display').value);
    const lng = parseFloat(document.getElementById('save-lng-display').value);
    const regionName = document.getElementById('save-region-display').value;
    const ndviEnabled = document.getElementById('save-ndvi-enabled').checked;

    // Show loading state
    const confirmBtn = document.getElementById('confirm-save-btn');
    const originalText = confirmBtn.textContent;
    confirmBtn.textContent = 'Creating Region...';
    confirmBtn.disabled = true;

    try {
      // Create region folder structure via API
      const regionData = {
        region_name: placeName, // Use place name as region name
        coordinates: {
          lat: lat,
          lng: lng
        },
        place_name: placeName,
        ndvi_enabled: ndviEnabled,
        created_at: new Date().toISOString()
      };

      Utils.log('info', 'Creating region folder structure for saved place:', regionData);
      
      const regionResult = await regions().createRegion(regionData);
      
      if (regionResult.success) {
        Utils.log('info', 'Region folder structure created successfully:', regionResult);
        
        // Create the place object for local storage
        const newPlace = {
          id: this.generateId(),
          name: placeName,
          lat: lat,
          lng: lng,
          regionName: regionResult.region_name || placeName, // Use the sanitized region name from backend
          createdAt: new Date().toISOString(),
          hasRegionFolder: true // Flag to indicate this place has actual region folders
        };

        this.addPlace(newPlace);
        this.hideSaveModal();
        
        Utils.showNotification(`Created region "${placeName}" with folder structure!`, 'success');
        
        // Optionally refresh the region list to show the new region
        if (window.FileManager) {
          window.FileManager.loadFiles();
        }
      } else {
        throw new Error(regionResult.message || 'Failed to create region');
      }
    } catch (error) {
      Utils.log('error', 'Failed to create region folder structure:', error);
      Utils.showNotification(`Failed to create region: ${error.message}`, 'error');
    } finally {
      // Restore button state
      confirmBtn.textContent = originalText;
      confirmBtn.disabled = false;
    }
  },

  /**
   * Add a new place to saved places (local session only)
   */
  addPlace(place) {
    this.savedPlaces.push(place);
    this.renderPlacesList();
  },

  /**
   * Remove a place from saved places (local session only)
   */
  removePlace(placeId) {
    this.savedPlaces = this.savedPlaces.filter(place => place.id !== placeId);
    this.renderPlacesList();
  },

  /**
   * Navigate to a saved place
   */
  goToPlace(place) {
    // Update coordinate inputs
    const latInput = document.getElementById('lat-input');
    const lngInput = document.getElementById('lng-input');
    const regionNameInput = document.getElementById('region-name-input');
    
    if (latInput && lngInput) {
      latInput.value = place.lat.toFixed(6);
      lngInput.value = place.lng.toFixed(6);
      
      if (regionNameInput) {
        regionNameInput.value = place.regionName || place.name;
      }

      // Update map view
      if (window.MapManager) {
        window.MapManager.setView(place.lat, place.lng, 13);
      }

      // Update save button state
      this.updateSaveButtonState();
      
      Utils.showNotification(`Navigated to "${place.name}"`, 'info');
    }
  },

  /**
   * Render the saved places list
   */
  renderPlacesList() {
    if (!this.placesListContainer) return;

    const noPlacesDiv = document.getElementById('no-saved-places');
    
    if (this.savedPlaces.length === 0) {
      this.placesListContainer.innerHTML = '';
      if (noPlacesDiv) noPlacesDiv.classList.remove('hidden');
      return;
    }

    if (noPlacesDiv) noPlacesDiv.classList.add('hidden');

    const placesHTML = this.savedPlaces.map(place => {
      const hasRegionFolder = place.hasRegionFolder;
      const folderIcon = hasRegionFolder ? '📁' : '📍';
      const folderTooltip = hasRegionFolder ? 'Created permanent region folder' : 'Session bookmark only';
      
      return `
        <div class="saved-place-item bg-[#495057] hover:bg-[#6c757d] rounded-lg p-2 transition-colors group">
          <div class="flex items-center justify-between">
            <button class="flex-1 text-left" onclick="window.SavedPlaces.goToPlace(${JSON.stringify(place).replace(/"/g, '&quot;')})">
              <div class="flex items-center gap-2">
                <span title="${folderTooltip}">${folderIcon}</span>
                <div>
                  <div class="text-white text-sm font-medium">${this.escapeHtml(place.name)}</div>
                  <div class="text-[#ababab] text-xs font-mono">${place.lat.toFixed(4)}, ${place.lng.toFixed(4)}</div>
                </div>
              </div>
            </button>
            <button class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 text-xs p-1 transition-opacity" 
                    onclick="window.SavedPlaces.confirmRemovePlace('${place.id}')" 
                    title="Remove from session">
              🗑️
            </button>
          </div>
        </div>
      `;
    }).join('');

    this.placesListContainer.innerHTML = placesHTML;
  },

  /**
   * Confirm removal of a place from session
   */
  confirmRemovePlace(placeId) {
    const place = this.savedPlaces.find(p => p.id === placeId);
    if (!place) return;

    if (confirm(`Remove "${place.name}" from session places?\n\nNote: This only removes it from the current session list.\nThe region folder (if created) will remain intact.`)) {
      this.removePlace(placeId);
      Utils.showNotification(`Removed "${place.name}" from session`, 'info');
    }
  },

  /**
   * Show manage places modal
   */
  showManageModal() {
    alert('Saved Places Management\n\n' +
          'Saved places are now stored as actual region folders!\n\n' +
          '• Each saved place creates input/{name}/ and output/{name}/ folders\n' +
          '• Session places shown here are for quick navigation only\n' +
          '• Permanent regions are listed in the region selector\n\n' +
          'To manage regions permanently, use the region management features.');
  },

  // Removed persistent storage methods since we now create actual region folders
  // The following methods are no longer needed:
  // - saveToStorage()
  // - loadFromStorage()
  
  /**
   * Generate a unique ID for places
   */
  generateId() {
    return 'place_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  },

  /**
   * Escape HTML for safe rendering
   */
  escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  },
  
  /**
   * Export session places (temporary list only)
   */
  exportPlaces() {
    if (this.savedPlaces.length === 0) {
      Utils.showNotification('No session places to export', 'warning');
      return;
    }
    
    const dataStr = JSON.stringify(this.savedPlaces, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = 'session_places_' + new Date().toISOString().split('T')[0] + '.json';
    link.click();
    
    Utils.showNotification('Session places exported successfully', 'success');
  },

  /**
   * Import places (session only - for quick navigation)
   */
  importPlaces(fileInput) {
    const file = fileInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedPlaces = JSON.parse(e.target.result);
        
        if (Array.isArray(importedPlaces)) {
          // Merge with existing session places, avoiding duplicates
          const existingNames = new Set(this.savedPlaces.map(p => p.name.toLowerCase()));
          const newPlaces = importedPlaces.filter(place => 
            place.name && place.lat && place.lng && !existingNames.has(place.name.toLowerCase())
          );
          
          this.savedPlaces.push(...newPlaces);
          this.renderPlacesList();
          
          Utils.showNotification(`Imported ${newPlaces.length} session places`, 'success');
        } else {
          throw new Error('Invalid file format');
        }
      } catch (error) {
        Utils.log('error', 'Failed to import places', error);
        Utils.showNotification('Failed to import places. Please check the file format.', 'error');
      }
    };
    
    reader.readAsText(file);
  }
};
