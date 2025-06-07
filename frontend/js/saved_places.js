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
    
    // Load saved places from storage
    this.loadFromStorage();
    
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
      <div id="save-place-modal" class="fixed inset-0 z-50 hidden bg-black bg-opacity-75 flex items-center justify-center">
        <div class="bg-[#1a1a1a] border border-[#303030] rounded-lg p-6 w-96 max-w-[90vw]">
          <h3 class="text-white text-lg font-semibold mb-4">Save Current Location</h3>
          
          <div class="space-y-4">
            <!-- Place Name Input -->
            <div>
              <label for="place-name-input" class="block text-xs text-[#ababab] mb-1">Place Name</label>
              <input type="text" id="place-name-input" placeholder="Enter a name for this location" 
                     class="w-full bg-[#262626] border border-[#404040] rounded-lg px-3 py-2 text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#00bfff]">
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
              <label class="block text-xs text-[#ababab] mb-1">Generated Region Name</label>
              <input type="text" id="save-region-display" readonly 
                     class="w-full bg-[#141414] border border-[#404040] rounded-lg px-3 py-2 text-white text-sm font-mono">
            </div>
          </div>
          
          <!-- Action Buttons -->
          <div class="flex justify-end gap-3 mt-6">
            <button id="cancel-save-btn" class="px-4 py-2 bg-[#404040] hover:bg-[#505050] text-white rounded-lg transition-colors">
              Cancel
            </button>
            <button id="confirm-save-btn" class="px-4 py-2 bg-[#007bff] hover:bg-[#0056b3] text-white rounded-lg transition-colors">
              Save Place
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
            <label class="block text-xs text-[#ababab]">Saved Places</label>
            <button id="manage-places-btn" class="text-xs text-[#00bfff] hover:text-[#0099cc] transition-colors">
              Manage
            </button>
          </div>
          <div id="saved-places-list" class="space-y-2 max-h-48 overflow-y-auto">
            <!-- Saved places will be dynamically populated here -->
          </div>
          <div id="no-saved-places" class="text-xs text-[#666] text-center py-4 hidden">
            No saved places yet. Click on the map and save a location!
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
              <label class="block text-xs text-[#ababab]">Saved Places</label>
              <button id="manage-places-btn" class="text-xs text-[#00bfff] hover:text-[#0099cc] transition-colors">
                Manage
              </button>
            </div>
            <div id="saved-places-list" class="space-y-2 max-h-48 overflow-y-auto">
              <!-- Saved places will be dynamically populated here -->
            </div>
            <div id="no-saved-places" class="text-xs text-[#666] text-center py-4 hidden">
              No saved places yet. Click on the map and save a location!
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
          💾 Save Current Location
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
  confirmSave() {
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

    const newPlace = {
      id: this.generateId(),
      name: placeName,
      lat: lat,
      lng: lng,
      regionName: regionName,
      createdAt: new Date().toISOString()
    };

    this.addPlace(newPlace);
    this.hideSaveModal();
    
    Utils.showNotification(`Saved "${placeName}" successfully!`, 'success');
  },

  /**
   * Add a new place to saved places
   */
  addPlace(place) {
    this.savedPlaces.push(place);
    this.saveToStorage();
    this.renderPlacesList();
  },

  /**
   * Remove a place from saved places
   */
  removePlace(placeId) {
    this.savedPlaces = this.savedPlaces.filter(place => place.id !== placeId);
    this.saveToStorage();
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

    const placesHTML = this.savedPlaces.map(place => `
      <div class="saved-place-item bg-[#495057] hover:bg-[#6c757d] rounded-lg p-2 transition-colors group">
        <div class="flex items-center justify-between">
          <button class="flex-1 text-left" onclick="window.SavedPlaces.goToPlace(${JSON.stringify(place).replace(/"/g, '&quot;')})">
            <div class="text-white text-sm font-medium">${this.escapeHtml(place.name)}</div>
            <div class="text-[#ababab] text-xs font-mono">${place.lat.toFixed(4)}, ${place.lng.toFixed(4)}</div>
          </button>
          <button class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 text-xs p-1 transition-opacity" 
                  onclick="window.SavedPlaces.confirmRemovePlace('${place.id}')" 
                  title="Delete place">
            🗑️
          </button>
        </div>
      </div>
    `).join('');

    this.placesListContainer.innerHTML = placesHTML;
  },

  /**
   * Confirm removal of a place
   */
  confirmRemovePlace(placeId) {
    const place = this.savedPlaces.find(p => p.id === placeId);
    if (!place) return;

    if (confirm(`Are you sure you want to remove "${place.name}" from saved places?`)) {
      this.removePlace(placeId);
      Utils.showNotification(`Removed "${place.name}" from saved places`, 'info');
    }
  },

  /**
   * Show manage places modal (for future enhancement)
   */
  showManageModal() {
    // For now, just show a simple alert
    // In the future, this could open a comprehensive management interface
    alert('Manage Places feature coming soon!\n\nFor now, you can:\n- Click on any saved place to navigate there\n- Hover over places and click the trash icon to delete them');
  },

  /**
   * Save places to persistent storage
   */
  async saveToStorage() {
    try {
      const response = await savedPlaces().savePlaces(this.savedPlaces);
      Utils.log('info', 'Saved places data saved to storage successfully');
    } catch (error) {
      Utils.log('error', 'Failed to save places to storage', error);
      
      // Fallback to localStorage if API is not available
      try {
        localStorage.setItem('saved_places', JSON.stringify(this.savedPlaces));
        Utils.log('info', 'Saved places data saved to localStorage as fallback');
      } catch (localError) {
        Utils.log('error', 'Failed to save to localStorage', localError);
        Utils.showNotification('Failed to save places data', 'error');
      }
    }
  },

  /**
   * Load places from persistent storage
   */
  async loadFromStorage() {
    try {
      const data = await savedPlaces().getSavedPlaces();
      this.savedPlaces = data.places || [];
      Utils.log('info', `Loaded ${this.savedPlaces.length} saved places from storage`);
    } catch (error) {
      Utils.log('warning', 'Failed to load places from API, trying localStorage', error);
      
      // Fallback to localStorage
      try {
        const storedData = localStorage.getItem('saved_places');
        if (storedData) {
          this.savedPlaces = JSON.parse(storedData);
          Utils.log('info', `Loaded ${this.savedPlaces.length} saved places from localStorage`);
        } else {
          this.savedPlaces = [];
          Utils.log('info', 'No saved places found, starting with empty list');
        }
      } catch (localError) {
        Utils.log('error', 'Failed to load from localStorage', localError);
        this.savedPlaces = [];
      }
    }

    // Render the places list after loading
    setTimeout(() => this.renderPlacesList(), 100);
  },

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
   * Export saved places data
   */
  exportPlaces() {
    const dataStr = JSON.stringify(this.savedPlaces, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = 'saved_places_' + new Date().toISOString().split('T')[0] + '.json';
    link.click();
    
    Utils.showNotification('Saved places exported successfully', 'success');
  },

  /**
   * Import saved places data
   */
  importPlaces(fileInput) {
    const file = fileInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedPlaces = JSON.parse(e.target.result);
        
        if (Array.isArray(importedPlaces)) {
          // Merge with existing places, avoiding duplicates
          const existingNames = new Set(this.savedPlaces.map(p => p.name.toLowerCase()));
          const newPlaces = importedPlaces.filter(place => 
            place.name && place.lat && place.lng && !existingNames.has(place.name.toLowerCase())
          );
          
          this.savedPlaces.push(...newPlaces);
          this.saveToStorage();
          this.renderPlacesList();
          
          Utils.showNotification(`Imported ${newPlaces.length} new places`, 'success');
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
