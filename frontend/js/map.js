/**
 * Map initialization and core map functionality
 */

window.MapManager = {
  map: null,
  drawnItems: null,
  drawControl: null,
  sentinel2TestMarker: null,
  
  // Path building functionality
  pathBuildingMode: false,
  currentPath: null,
  pathPoints: [],
  tempMarkers: [],
  
  // Box drawing functionality
  boxDrawingMode: false,
  currentBox: null,
  boxStartPoint: null,
  boxStartMarker: null,
  boxPreview: null,
  
  // Map mode management
  currentMode: 'move', // 'move', 'path', 'box'

  /**
   * Clean up existing map instance
   */
  cleanup() {
    if (this.map) {
      Utils.log('info', 'Cleaning up existing map instance');
      try {
        this.map.remove();
      } catch (error) {
        Utils.log('warn', 'Error during map cleanup', error);
      }
      this.map = null;
      this.drawnItems = null;
      this.drawControl = null;
      this.sentinel2TestMarker = null;
    }
  },

  /**
   * Initialize the Leaflet map
   */
  init() {
    Utils.log('info', 'Initializing map');
    
    // Check if map element exists
    if (!document.getElementById('map')) {
      Utils.log('error', 'Map element not found!');
      return false;
    }
    
    // Clean up any existing map instance first
    this.cleanup();
    
    try {
      // Create map instance centered on Brazil by default
      this.map = L.map('map').setView([-14.2350, -51.9253], 4);
      Utils.log('info', 'Map instance created successfully');
      
      // Add tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
      }).addTo(this.map);
      Utils.log('info', 'Tile layer added successfully');
         // Initialize drawing controls
    this.initDrawingControls();
    
    // Setup event handlers
    this.setupEventHandlers();
    
    // Setup path building handlers (with a small delay to ensure buttons are rendered)
    setTimeout(() => {
      this.setupPathBuildingHandlers();
    }, 100);

    // Create pending region markers if any exist
    if (window.FileManager && typeof FileManager.createPendingRegionMarkers === 'function') {
      FileManager.createPendingRegionMarkers();
    }

    Utils.log('info', 'Map initialized successfully');
    return true;
      
    } catch (error) {
      Utils.log('error', 'Failed to initialize map', error);
      return false;
    }
  },

  /**
   * Initialize drawing controls for area selection
   */
  initDrawingControls() {
    Utils.log('info', 'Setting up drawing controls');
    
    this.drawnItems = new L.FeatureGroup();
    this.map.addLayer(this.drawnItems);

    this.drawControl = new L.Control.Draw({
      position: 'topright',
      draw: {
        polygon: false,
        polyline: false,
        circle: false,
        marker: false,
        circlemarker: false,
        rectangle: {
          shapeOptions: {
            clickable: false,
            color: '#00bfff',
            weight: 2,
            opacity: 0.8,
            fillOpacity: 0.2
          }
        }
      },
      edit: {
        featureGroup: this.drawnItems,
        remove: true
      }
    });
    
    this.map.addControl(this.drawControl);
    Utils.log('info', 'Drawing controls added successfully');
  },

  /**
   * Setup map event handlers
   */
  setupEventHandlers() {
    // Handle drawing events
    this.map.on(L.Draw.Event.CREATED, (e) => {
      const layer = e.layer;
      this.drawnItems.addLayer(layer);
      
      if (e.layerType === 'rectangle') {
        const bounds = layer.getBounds();
        Utils.log('info', 'Rectangle drawn', bounds);
        this.showAreaDialog(bounds);
      }
    });

    this.map.on(L.Draw.Event.DELETED, (e) => {
      Utils.log('info', 'Shapes deleted');
    });
    
    // Coordinate display functionality
    this.map.on('mousemove', (e) => {
      const lat = e.latlng.lat.toFixed(6);
      const lng = e.latlng.lng.toFixed(6);
      const display = document.getElementById('coordinate-display');
      if (display) {
        display.textContent = `Lat: ${lat}, Lng: ${lng}`;
      }
    });
    
    // Hide coordinates when mouse leaves the map
    this.map.on('mouseout', (e) => {
      const display = document.getElementById('coordinate-display');
      if (display) {
        display.textContent = 'Lat: ---, Lng: ---';
      }
    });

    // Capture coordinates on map click
    this.map.on('click', (e) => {
      // Check if we're in path building mode
      if (this.pathBuildingMode) {
        this.addPathPoint(e.latlng);
        return; // Don't run normal coordinate capture when building paths
      }
      
      // Check if we're in box drawing mode
      if (this.boxDrawingMode) {
        this.handleBoxDrawingClick(e.latlng);
        return; // Don't run normal coordinate capture when drawing boxes
      }
      
      const lat = e.latlng.lat.toFixed(6);
      const lng = e.latlng.lng.toFixed(6);
      
      // Update coordinate input fields if they exist
      const latInput = document.getElementById('lat-input');
      const lngInput = document.getElementById('lng-input');
      const regionNameInput = document.getElementById('region-name-input');
      const gotoCoordinatesInput = document.getElementById('goto-coordinates-input');
      const gotoLatInput = document.getElementById('goto-lat-input');
      const gotoLngInput = document.getElementById('goto-lng-input');
      const gotoRegionNameInput = document.getElementById('goto-region-name');
      
      // Update Get Data section fields
      if (latInput && lngInput) {
        latInput.value = lat;
        lngInput.value = lng;
        
        // Generate and update region name
        if (regionNameInput) {
          const regionName = Utils.generateRegionName(parseFloat(lat), parseFloat(lng));
          regionNameInput.value = regionName;
          
          // Visual feedback for region name field
          regionNameInput.style.borderColor = '#00bfff';
          setTimeout(() => {
            regionNameInput.style.borderColor = '';
          }, 1000);
        }
        
        // Visual feedback for coordinate fields
        [latInput, lngInput].forEach(input => {
          input.style.borderColor = '#00bfff';
          setTimeout(() => {
            input.style.borderColor = '';
          }, 1000);
        });
      }
      
      // Update Go To section fields
      if (gotoCoordinatesInput) {
        // Format coordinates in a readable format for the goto-coordinates-input field
        const latValue = parseFloat(lat);
        const lngValue = parseFloat(lng);
        const latDir = latValue >= 0 ? 'N' : 'S';
        const lngDir = lngValue >= 0 ? 'E' : 'W';
        const formattedCoords = `${Math.abs(latValue).toFixed(4)}°${latDir}, ${Math.abs(lngValue).toFixed(4)}°${lngDir}`;
        
        gotoCoordinatesInput.value = formattedCoords;
        
        // Visual feedback for goto coordinates input
        gotoCoordinatesInput.style.borderColor = '#00bfff';
        setTimeout(() => {
          gotoCoordinatesInput.style.borderColor = '';
        }, 1000);
      }
      
      // Update parsed coordinate fields in Go To section
      if (gotoLatInput && gotoLngInput) {
        gotoLatInput.value = lat;
        gotoLngInput.value = lng;
        
        // Visual feedback for parsed coordinate fields
        [gotoLatInput, gotoLngInput].forEach(input => {
          input.style.borderColor = '#00bfff';
          setTimeout(() => {
            input.style.borderColor = '';
          }, 1000);
        });
      }
      
      // Update region name in Go To section
      if (gotoRegionNameInput) {
        const regionName = Utils.generateRegionName(parseFloat(lat), parseFloat(lng));
        gotoRegionNameInput.value = regionName;
        
        // Visual feedback for goto region name
        gotoRegionNameInput.style.borderColor = '#00bfff';
        setTimeout(() => {
          gotoRegionNameInput.style.borderColor = '';
        }, 1000);
      }
      
      Utils.log('info', `Coordinates captured: ${lat}, ${lng} - Updated all coordinate fields`);
    });
  },

  /**
   * Show dialog for processing selected area
   * @param {L.LatLngBounds} bounds - Selected area bounds
   */
  showAreaDialog(bounds) {
    const ne = bounds.getNorthEast();
    const sw = bounds.getSouthWest();
    
    const message = `Area selected:\nNorth: ${ne.lat.toFixed(4)}\nSouth: ${sw.lat.toFixed(4)}\nEast: ${ne.lng.toFixed(4)}\nWest: ${sw.lng.toFixed(4)}\n\nWould you like to process this area?`;
    
    if (confirm(message)) {
      const area = {
        north: ne.lat,
        south: sw.lat,
        east: ne.lng,
        west: sw.lng
      };
      Utils.log('info', 'Processing area', area);
      // TODO: Implement area processing functionality
    }
  },

  /**
   * Set map view to specific coordinates
   * @param {number} lat - Latitude
   * @param {number} lng - Longitude
   * @param {number} zoom - Zoom level (optional)
   */
  setView(lat, lng, zoom = 13) {
    if (this.map && Utils.isValidCoordinate(lat, lng)) {
      this.map.setView([lat, lng], zoom);
      Utils.log('info', `Map view set to ${lat}, ${lng} at zoom ${zoom}`);
    }
  },

  /**
   * Add a marker to the map
   * @param {number} lat - Latitude
   * @param {number} lng - Longitude
   * @param {Object} options - Marker options
   * @returns {L.Marker} The created marker
   */
  addMarker(lat, lng, options = {}) {
    if (!this.map || !Utils.isValidCoordinate(lat, lng)) {
      return null;
    }

    const marker = L.marker([lat, lng], options).addTo(this.map);
    
    if (options.popup) {
      marker.bindPopup(options.popup);
    }

    if (options.label) {
      marker.bindTooltip(options.label, { permanent: true, direction: 'top', className: 'region-label' });
    }
    
    if (options.onClick) {
      marker.on('click', options.onClick);
    }
    
    return marker;
  },

  /**
   * Remove a marker from the map
   * @param {L.Marker} marker - Marker to remove
   */
  removeMarker(marker) {
    if (this.map && marker) {
      this.map.removeLayer(marker);
    }
  },

  /**
   * Add Sentinel-2 test marker
   * @param {number} lat - Latitude
   * @param {number} lng - Longitude
   */
  addSentinel2TestMarker(lat, lng) {
    // Remove existing Sentinel-2 test marker if present
    if (this.sentinel2TestMarker) {
      this.removeMarker(this.sentinel2TestMarker);
    }

    // Add new marker
    this.sentinel2TestMarker = this.addMarker(lat, lng, {
      popup: `Sentinel-2 Test Location: Portland, OR<br>Good satellite coverage area<br>Lat: ${lat}<br>Lng: ${lng}`
    });

    if (this.sentinel2TestMarker) {
      this.sentinel2TestMarker.openPopup();
    }

    Utils.log('info', `Added Sentinel-2 test marker at ${lat}, ${lng}`);
  },

  /**
   * Get the current map instance
   * @returns {L.Map} The Leaflet map instance
   */
  getMap() {
    return this.map;
  },

  /**
   * Set map mode (move, path, or box)
   * @param {string} mode - The mode to set ('move', 'path', 'box')
   */
  setMapMode(mode) {
    // Exit current mode first
    this.exitCurrentMode();
    
    // Update current mode
    this.currentMode = mode;
    
    // Update checkbox states
    this.updateModeCheckboxes();
    
    // Enter new mode
    switch (mode) {
      case 'move':
        this.enterMoveMode();
        break;
      case 'path':
        this.enterPathMode();
        break;
      case 'box':
        this.enterBoxMode();
        break;
      default:
        Utils.log('warn', `Unknown mode: ${mode}`);
        this.currentMode = 'move';
        this.enterMoveMode();
    }
    
    // Update clear button visibility
    this.updateClearButtonVisibility();
  },

  /**
   * Exit current mode and reset states
   */
  exitCurrentMode() {
    // Reset cursor
    this.map.getContainer().style.cursor = '';
    
    // Exit specific mode states
    this.pathBuildingMode = false;
    this.boxDrawingMode = false;
  },

  /**
   * Enter move mode
   */
  enterMoveMode() {
    Utils.log('info', 'Move mode activated');
    Utils.showNotification('Move mode activated', 'info', 2000);
  },

  /**
   * Enter path building mode
   */
  enterPathMode() {
    this.pathBuildingMode = true;
    
    // Change cursor
    this.map.getContainer().style.cursor = 'crosshair';
    
    // Initialize path if first time
    if (!this.currentPath) {
      this.pathPoints = [];
    }
    
    Utils.log('info', 'Path mode activated - Click points on the map to build a path');
    Utils.showNotification('Path mode activated - Click points on the map', 'info', 3000);
  },

  /**
   * Enter box drawing mode
   */
  enterBoxMode() {
    this.boxDrawingMode = true;
    
    // Change cursor
    this.map.getContainer().style.cursor = 'crosshair';
    
    // Reset box state
    this.boxStartPoint = null;
    if (this.boxStartMarker) {
      this.map.removeLayer(this.boxStartMarker);
      this.boxStartMarker = null;
    }
    if (this.boxPreview) {
      this.map.removeLayer(this.boxPreview);
      this.boxPreview = null;
    }
    
    Utils.log('info', 'Box mode activated - Click to set start point, then click again for opposite corner');
    Utils.showNotification('Box mode activated - Click to set start point, then click again for opposite corner', 'info', 4000);
  },

  /**
   * Update mode checkbox visual states
   */
  updateModeCheckboxes() {
    const modes = ['move', 'path', 'box'];
    
    modes.forEach(mode => {
      const checkbox = document.querySelector(`#${mode}-mode-checkbox`);
      const customDiv = checkbox?.nextElementSibling;
      
      if (customDiv) {
        if (this.currentMode === mode) {
          // Active state
          customDiv.classList.remove('inactive', 'bg-[#303030]', 'hover:bg-[#404040]');
          customDiv.classList.add('active', 'bg-[#28a745]', 'hover:bg-[#218838]');
          checkbox.checked = true;
        } else {
          // Inactive state
          customDiv.classList.remove('active', 'bg-[#28a745]', 'hover:bg-[#218838]');
          customDiv.classList.add('inactive', 'bg-[#303030]', 'hover:bg-[#404040]');
          checkbox.checked = false;
        }
      }
    });
  },

  /**
   * Update clear button visibility based on current content and mode
   */
  updateClearButtonVisibility() {
    const clearPathBtn = document.getElementById('clear-path-btn');
    const clearBoxBtn = document.getElementById('clear-box-btn');
    const getLazBtn = document.getElementById('get-box-laz-btn');
    
    // Show Clear Path button if there's a path or we're in path mode
    if (clearPathBtn) {
      if (this.currentPath || this.pathBuildingMode) {
        clearPathBtn.classList.remove('hidden');
      } else {
        clearPathBtn.classList.add('hidden');
      }
    }
    
    // Show Clear Box button if there's a box or we're in box mode
    if (clearBoxBtn) {
      if (this.currentBox || this.boxDrawingMode) {
        clearBoxBtn.classList.remove('hidden');
      } else {
        clearBoxBtn.classList.add('hidden');
      }
    }
    
    // Show Get LAZ button if there's a path or box (regardless of mode)
    if (getLazBtn) {
      if (this.currentPath || this.currentBox) {
        getLazBtn.classList.remove('hidden');
      } else {
        getLazBtn.classList.add('hidden');
      }
    }
  },

  /**
   * Add a point to the current path
   * @param {L.LatLng} latlng - Point coordinates
   */
  addPathPoint(latlng) {
    if (!this.pathBuildingMode) return;
    
    this.pathPoints.push(latlng);
    
    // Add a temporary marker for the point
    const marker = L.circleMarker(latlng, {
      radius: 6,
      fillColor: '#ff7800',
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.8
    }).addTo(this.map);
    
    // Add popup with point info
    marker.bindPopup(`Point ${this.pathPoints.length}<br>Lat: ${latlng.lat.toFixed(6)}<br>Lng: ${latlng.lng.toFixed(6)}`);
    
    this.tempMarkers.push(marker);
    
    // Update or create the path line
    this.updatePath();
    
    Utils.log('info', `Added path point ${this.pathPoints.length}: ${latlng.lat.toFixed(6)}, ${latlng.lng.toFixed(6)}`);
  },

  /**
   * Update the path polyline
   */
  updatePath() {
    if (this.pathPoints.length < 2) return;
    
    // Remove existing path
    if (this.currentPath) {
      this.map.removeLayer(this.currentPath);
    }
    
    // Create new path
    this.currentPath = L.polyline(this.pathPoints, {
      color: '#ff7800',
      weight: 4,
      opacity: 0.8,
      smoothFactor: 1
    }).addTo(this.map);
    
    // Add popup to show path info
    const totalDistance = this.calculatePathDistance();
    this.currentPath.bindPopup(`
      <strong>Path Information</strong><br>
      Points: ${this.pathPoints.length}<br>
      Total Distance: ${totalDistance.toFixed(2)} km<br>
      <small>Click points to continue building</small>
    `);
    
    // Update clear button visibility
    this.updateClearButtonVisibility();
  },

  /**
   * Calculate total path distance
   * @returns {number} Distance in kilometers
   */
  calculatePathDistance() {
    if (this.pathPoints.length < 2) return 0;
    
    let totalDistance = 0;
    for (let i = 1; i < this.pathPoints.length; i++) {
      totalDistance += this.pathPoints[i-1].distanceTo(this.pathPoints[i]) / 1000; // Convert to km
    }
    return totalDistance;
  },

  /**
   * Clear the current path
   */
  clearPath() {
    // Remove path line
    if (this.currentPath) {
      this.map.removeLayer(this.currentPath);
      this.currentPath = null;
    }
    
    // Remove temporary markers
    this.tempMarkers.forEach(marker => {
      this.map.removeLayer(marker);
    });
    this.tempMarkers = [];
    
    // Clear points array
    this.pathPoints = [];
    
    // Update clear button visibility
    this.updateClearButtonVisibility();
    
    Utils.log('info', 'Path cleared');
    Utils.showNotification('Path cleared', 'success', 2000);
  },

  /**
   * Handle box drawing clicks (two-click approach)
   * @param {L.LatLng} latlng - Click coordinates
   */
  handleBoxDrawingClick(latlng) {
    if (!this.boxDrawingMode) return;
    
    if (!this.boxStartPoint) {
      // First click - set start point
      this.boxStartPoint = latlng;
      
      // Add a temporary marker for the start point
      this.boxStartMarker = L.circleMarker(latlng, {
        radius: 8,
        fillColor: '#007bff',
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      }).addTo(this.map);
      
      this.boxStartMarker.bindPopup(`Box Start Point<br>Lat: ${latlng.lat.toFixed(6)}<br>Lng: ${latlng.lng.toFixed(6)}`);
      
      Utils.log('info', `Box start point set: ${latlng.lat.toFixed(6)}, ${latlng.lng.toFixed(6)}`);
      Utils.showNotification('Box start point set - Click again to set opposite corner', 'info', 3000);
    } else {
      // Second click - finish the box
      this.finishBoxDrawing(latlng);
    }
  },

  /**
   * Start drawing a box (now handled by first click)
   * @param {L.LatLng} latlng - Starting point coordinates
   */
  startBoxDrawing(latlng) {
    // This function is now handled by handleBoxDrawingClick
    // Keeping for compatibility but functionality moved to handleBoxDrawingClick
  },

  /**
   * Update box preview during mouse move (removed - no longer needed for click approach)
   * @param {L.LatLng} latlng - Current mouse position
   */
  updateBoxPreview(latlng) {
    // No longer needed for click-based approach
    // Keeping for compatibility but no functionality
  },

  /**
   * Finish drawing the box
   * @param {L.LatLng} latlng - End point coordinates
   */
  finishBoxDrawing(latlng) {
    if (!this.boxDrawingMode || !this.boxStartPoint) return;
    
    // Remove start marker
    if (this.boxStartMarker) {
      this.map.removeLayer(this.boxStartMarker);
      this.boxStartMarker = null;
    }
    
    // Remove preview (legacy support)
    if (this.boxPreview) {
      this.map.removeLayer(this.boxPreview);
      this.boxPreview = null;
    }
    
    // Create final rectangle bounds
    const bounds = L.latLngBounds(this.boxStartPoint, latlng);
    
    // Remove existing box
    if (this.currentBox) {
      this.map.removeLayer(this.currentBox);
    }
    
    // Create final box
    this.currentBox = L.rectangle(bounds, {
      color: '#007bff',
      weight: 3,
      opacity: 1,
      fillColor: '#007bff',
      fillOpacity: 0.3
    }).addTo(this.map);
    
    // Calculate area and dimensions
    const area = this.calculateBoxArea(bounds);
    const dimensions = this.calculateBoxDimensions(bounds);
    
    // Add popup with box info
    this.currentBox.bindPopup(`
      <strong>Box Information</strong><br>
      North: ${bounds.getNorth().toFixed(6)}<br>
      South: ${bounds.getSouth().toFixed(6)}<br>
      East: ${bounds.getEast().toFixed(6)}<br>
      West: ${bounds.getWest().toFixed(6)}<br>
      Width: ${dimensions.width.toFixed(2)} km<br>
      Height: ${dimensions.height.toFixed(2)} km<br>
      Area: ${area.toFixed(2)} km²
    `);
    
    // Reset drawing state
    this.boxStartPoint = null;
    
    // Update clear button visibility
    this.updateClearButtonVisibility();
    
    Utils.log('info', `Box drawn: ${bounds.getSouth().toFixed(6)}, ${bounds.getWest().toFixed(6)} to ${bounds.getNorth().toFixed(6)}, ${bounds.getEast().toFixed(6)}`);
    Utils.showNotification('Box drawn successfully', 'success', 2000);
  },

  /**
   * Calculate box area in square kilometers
   * @param {L.LatLngBounds} bounds - Box bounds
   * @returns {number} Area in square kilometers
   */
  calculateBoxArea(bounds) {
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    const se = L.latLng(sw.lat, ne.lng);
    const nw = L.latLng(ne.lat, sw.lng);
    
    const width = sw.distanceTo(se) / 1000; // Convert to km
    const height = sw.distanceTo(nw) / 1000; // Convert to km
    
    return width * height;
  },

  /**
   * Calculate box dimensions in kilometers
   * @param {L.LatLngBounds} bounds - Box bounds
   * @returns {object} Object with width and height in kilometers
   */
  calculateBoxDimensions(bounds) {
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    const se = L.latLng(sw.lat, ne.lng);
    const nw = L.latLng(ne.lat, sw.lng);
    
    const width = sw.distanceTo(se) / 1000; // Convert to km
    const height = sw.distanceTo(nw) / 1000; // Convert to km
    
    return { width, height };
  },

  /**
   * Clear the current box
   */
  clearBox() {
    // Remove box
    if (this.currentBox) {
      this.map.removeLayer(this.currentBox);
      this.currentBox = null;
    }
    
    // Remove start marker
    if (this.boxStartMarker) {
      this.map.removeLayer(this.boxStartMarker);
      this.boxStartMarker = null;
    }
    
    // Remove preview if exists (legacy support)
    if (this.boxPreview) {
      this.map.removeLayer(this.boxPreview);
      this.boxPreview = null;
    }
    
    // Reset drawing state
    this.boxStartPoint = null;
    
    // Update clear button visibility
    this.updateClearButtonVisibility();
    
    Utils.log('info', 'Box cleared');
    Utils.showNotification('Box cleared', 'success', 2000);
  },

  /**
   * Setup path building and box drawing event handlers
   */
  setupPathBuildingHandlers() {
    // Mode selection checkboxes
    const moveCheckbox = document.getElementById('move-mode-checkbox');
    const pathCheckbox = document.getElementById('path-mode-checkbox');
    const boxCheckbox = document.getElementById('box-mode-checkbox');
    
    if (moveCheckbox) {
      moveCheckbox.addEventListener('change', () => {
        if (moveCheckbox.checked) {
          this.setMapMode('move');
        }
      });
    }
    
    if (pathCheckbox) {
      pathCheckbox.addEventListener('change', () => {
        if (pathCheckbox.checked) {
          this.setMapMode('path');
        }
      });
    }
    
    if (boxCheckbox) {
      boxCheckbox.addEventListener('change', () => {
        if (boxCheckbox.checked) {
          this.setMapMode('box');
        }
      });
    }
    
    // Alternative: Handle clicks on the custom divs
    const moveCustomDiv = document.querySelector('#move-mode-checkbox + .mode-checkbox-custom');
    const pathCustomDiv = document.querySelector('#path-mode-checkbox + .mode-checkbox-custom');
    const boxCustomDiv = document.querySelector('#box-mode-checkbox + .mode-checkbox-custom');
    
    if (moveCustomDiv) {
      moveCustomDiv.addEventListener('click', () => {
        this.setMapMode('move');
      });
    }
    
    if (pathCustomDiv) {
      pathCustomDiv.addEventListener('click', () => {
        this.setMapMode('path');
      });
    }
    
    if (boxCustomDiv) {
      boxCustomDiv.addEventListener('click', () => {
        this.setMapMode('box');
      });
    }
    
    // Clear path button
    const clearBtn = document.getElementById('clear-path-btn');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        this.clearPath();
      });
    }
    
    // Clear box button
    const clearBoxBtn = document.getElementById('clear-box-btn');
    if (clearBoxBtn) {
      clearBoxBtn.addEventListener('click', () => {
        this.clearBox();
      });
    }
    
    // Initialize default mode
    this.setMapMode('move');
  }
};
