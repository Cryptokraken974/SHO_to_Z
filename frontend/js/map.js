/**
 * Map initialization and core map functionality
 */

window.MapManager = {
  map: null,
  drawnItems: null,
  drawControl: null,
  sentinel2TestMarker: null,

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
  }
};
