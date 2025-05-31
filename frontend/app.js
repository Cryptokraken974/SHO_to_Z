$(function () {
  console.log('*** jQuery document ready fired! ***');
  console.log('*** Leaflet available:', typeof L !== 'undefined' ? 'YES' : 'NO');
  
  let selectedLazFile = null; // No default file - user must select one
  let map; // Leaflet map instance
  let mapOverlays = {}; // Store active overlays by processing type
  let currentLocationPin = null; // Store current LAZ file location pin

  // Initialize Leaflet map
  function initializeMap() {
    console.log('*** initializeMap function called ***');
    // Check if map element exists
    if (!document.getElementById('map')) {
      console.error('*** ERROR: Map element not found! ***');
      return;
    }
    console.log('*** Map element found successfully ***');
    
    try {
      console.log('*** Creating Leaflet map instance ***');
      map = L.map('map').setView([-14.2350, -51.9253], 4); // Center on Brazil by default
      console.log('*** Map instance created successfully ***');
      
      // Add tile layer
      console.log('*** Adding tile layer ***');
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
      }).addTo(map);
      console.log('*** Tile layer added successfully ***');
      
      console.log('*** Map initialized successfully ***');
    } catch (error) {
      console.error('*** ERROR initializing map:', error);
      return;
    }

    // Add markers for available LAZ file locations
    console.log('*** Adding markers to map ***');
    const markers = [
      {
        coords: [44.4268, -68.2048], // Fox Island, Maine
        popup: "Fox Island, Maine",
        file: "input/foxisland/FoxIsland.laz"
      },
      {
        coords: [42.9446, -122.1090], // Wizard Island, Oregon (Crater Lake)
        popup: "Wizard Island, Oregon",
        file: "input/wizardisland/OR_WizardIsland.laz"
      }
    ];

    markers.forEach((marker, index) => {
      console.log(`*** Adding marker ${index + 1}: ${marker.popup} ***`);
      L.marker(marker.coords)
        .addTo(map)
        .bindPopup(marker.popup)
        .on('click', function() {
          selectedLazFile = marker.file;
          $('#selected-file-name').text(marker.file.split('/').pop())
                                   .removeClass('text-[#666]').addClass('text-[#00bfff]');
          
          // Center map on the clicked marker coordinates
          map.setView(marker.coords, 13);
        });
    });
    console.log('*** All markers added successfully ***');

    // Initialize drawing controls
    console.log('*** Setting up drawing controls ***');
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
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
        featureGroup: drawnItems,
        remove: true
      }
    });
    map.addControl(drawControl);
    console.log('*** Drawing controls added successfully ***');

    // Handle drawing events
    map.on(L.Draw.Event.CREATED, function (e) {
      const layer = e.layer;
      drawnItems.addLayer(layer);
      
      if (e.layerType === 'rectangle') {
        const bounds = layer.getBounds();
        console.log('Rectangle drawn:', bounds);
        // Here you can add functionality to process the selected area
        showAreaDialog(bounds);
      }
    });

    map.on(L.Draw.Event.DELETED, function (e) {
      console.log('Shapes deleted');
    });
    
    // Add coordinate display functionality
    map.on('mousemove', function(e) {
      const lat = e.latlng.lat.toFixed(6);
      const lng = e.latlng.lng.toFixed(6);
      document.getElementById('coordinate-display').textContent = `Lat: ${lat}, Lng: ${lng}`;
    });
    
    // Hide coordinates when mouse leaves the map
    map.on('mouseout', function(e) {
      document.getElementById('coordinate-display').textContent = 'Lat: ---, Lng: ---';
    });
    
    // Capture coordinates on map click
    map.on('click', function(e) {
      const lat = e.latlng.lat.toFixed(6);
      const lng = e.latlng.lng.toFixed(6);
      
      // Update the coordinate input fields in the Test accordion
      const latInput = document.getElementById('lat-input');
      const lngInput = document.getElementById('lng-input');
      
      if (latInput && lngInput) {
        latInput.value = lat;
        lngInput.value = lng;
        
        // Add visual feedback with temporary border color change
        latInput.style.borderColor = '#00bfff';
        lngInput.style.borderColor = '#00bfff';
        
        setTimeout(() => {
          latInput.style.borderColor = '#404040';
          lngInput.style.borderColor = '#404040';
        }, 1000);
        
        // Note: Removed checkDataAvailability call to prevent modal interference
        // since we've eliminated the data source dropdown functionality
      }
      
      console.log(`Map clicked at: ${lat}, ${lng}`);
    });
  }

  // Function to show dialog for processing selected area
  function showAreaDialog(bounds) {
    const ne = bounds.getNorthEast();
    const sw = bounds.getSouthWest();
    
    const message = `Area selected:\nNorth: ${ne.lat.toFixed(4)}\nSouth: ${sw.lat.toFixed(4)}\nEast: ${ne.lng.toFixed(4)}\nWest: ${sw.lng.toFixed(4)}\n\nWould you like to process this area?`;
    
    if (confirm(message)) {
      // Here you can add functionality to process the selected area
      // For example, send coordinates to backend for area-specific processing
      console.log('Processing area:', { north: ne.lat, south: sw.lat, east: ne.lng, west: sw.lng });
    }
  }

  // Initialize map when DOM is ready with delay
  console.log('*** Setting timeout to initialize map ***');
  setTimeout(function() {
    console.log('*** Timeout fired - Attempting to initialize map... ***');
    initializeMap();
    
    // Initialize WebSocket connection for progress updates
    console.log('*** Initializing WebSocket for progress updates ***');
    initializeProgressWebSocket();
  }, 100);

  // Accordion functionality
  $('#laz-accordion').on('click', function() {
    const content = $('#laz-content');
    const arrow = $(this).find('.accordion-arrow');

    if (content.hasClass('collapsed')) {
      content.removeClass('collapsed');
      arrow.css('transform', 'rotate(0deg)');
    } else {
      content.addClass('collapsed');
      arrow.css('transform', 'rotate(-90deg)');
    }
  });

  // Test accordion functionality
  $('#test-accordion').on('click', function() {
    const content = $('#test-content');
    const arrow = $(this).find('.accordion-arrow');

    if (content.hasClass('collapsed')) {
      content.removeClass('collapsed');
      arrow.css('transform', 'rotate(0deg)');
    } else {
      content.addClass('collapsed');
      arrow.css('transform', 'rotate(-90deg)');
    }
  });

  // Processing accordion functionality
  $('#processing-accordion').on('click', function() {
    const content = $('#processing-content');
    const arrow = $(this).find('.accordion-arrow');

    if (content.hasClass('collapsed')) {
      content.removeClass('collapsed');
      arrow.css('transform', 'rotate(0deg)');
    } else {
      content.addClass('collapsed');
      arrow.css('transform', 'rotate(-90deg)');
    }
  });

  // Browse files button
  $('#browse-files').on('click', function() {
    loadFiles();
    $('#file-modal').show();
  });

  // Close modal
  $('.close, #cancel-select').on('click', function() {
    $('#file-modal').hide();
  });

  // Close modal when clicking outside
  $('#file-modal').on('click', function(e) {
    if (e.target === this) {
      $(this).hide();
    }
  });

  // Download LAZ Files button
  $('#download-laz-btn').on('click', function() {
    // Note: Removed checkDataAvailability call since we've eliminated the data source dropdown functionality
    // Instead, show a message that this feature has been removed
    alert("Data source selection has been removed. Use the test buttons to download specific data types (Portland test for LAZ files, Sentinel-2 test for satellite imagery).");
  });

  // Test Data Button - Real data test location
  $('#test-data-btn').on('click', function() {
    // Portland, Oregon area (known to have USGS 3DEP LiDAR coverage)
    const testLat = 45.5152;
    const testLng = -122.6784;
    
    // Update coordinate inputs
    $('#lat-input').val(testLat);
    $('#lng-input').val(testLng);
    
    // Center map on the test location
    if (map) {
      map.setView([testLat, testLng], 15);
      
      // Add a marker for the test location
      if (window.testMarker) {
        map.removeLayer(window.testMarker);
      }
      window.testMarker = L.marker([testLat, testLng]).addTo(map)
        .bindPopup('Test Location: Portland, OR<br>USGS 3DEP LiDAR coverage area<br>Lat: ' + testLat + '<br>Lng: ' + testLng)
        .openPopup();
    }
    
    // Note: Removed automatic checkDataAvailability call to prevent modal interference
    // Users can manually trigger data acquisition if needed by clicking the Download Data button
  });

  // Sentinel-2 Test Button - Download red and NIR bands
  $('#test-sentinel2-btn').on('click', function() {
    let lat = $('#lat-input').val();
    let lng = $('#lng-input').val();
    
    // If no coordinates are set, use Portland, Oregon as default (good Sentinel-2 coverage)
    if (!lat || !lng || lat === '' || lng === '') {
      lat = 45.5152;  // Portland, Oregon
      lng = -122.6784;
      
      // Update the input fields
      $('#lat-input').val(lat);
      $('#lng-input').val(lng);
      
      // Center map on the location
      if (map) {
        map.setView([lat, lng], 12);
        
        // Add a marker
        if (window.sentinel2TestMarker) {
          map.removeLayer(window.sentinel2TestMarker);
        }
        window.sentinel2TestMarker = L.marker([lat, lng]).addTo(map)
          .bindPopup('Sentinel-2 Test Location: Portland, OR<br>Good satellite coverage area<br>Lat: ' + lat + '<br>Lng: ' + lng)
          .openPopup();
      }
      
      alert('Using Portland, Oregon coordinates for Sentinel-2 test (good satellite coverage area).');
    }
    
    // Validate coordinates are reasonable (not in the middle of an ocean)
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);
    
    if (isNaN(latNum) || isNaN(lngNum)) {
      alert('Invalid coordinates. Please enter valid latitude and longitude values.');
      return;
    }
    
    if (Math.abs(latNum) > 90 || Math.abs(lngNum) > 180) {
      alert('Coordinates out of range. Latitude must be between -90 and 90, longitude between -180 and 180.');
      return;
    }
    
    downloadSentinel2Images(latNum, lngNum);
  });

  // Close Download LAZ modal
  $('.close-download, #cancel-download').on('click', function() {
    $('#download-laz-modal').hide();
  });

  // Close Download LAZ modal when clicking outside
  $('#download-laz-modal').on('click', function(e) {
    if (e.target === this) {
      $(this).hide();
    }
  });

  // File search functionality
  $('#file-search-input').on('input', function() {
    const searchTerm = $(this).val().toLowerCase();
    $('.file-item').each(function() {
      const fileName = $(this).text().toLowerCase();
      if (fileName.includes(searchTerm)) {
        $(this).show();
      } else {
        $(this).hide();
      }
    });
  });

  // File selection
  $(document).on('click', '.file-item', function() {
    $('.file-item').removeClass('selected');
    $(this).addClass('selected');
  });

  // Select file button
  $('#select-file').on('click', function() {
    const selectedFile = $('.file-item.selected').data('file');
    if (selectedFile) {
      selectedLazFile = selectedFile;
      $('#selected-file-name').text(selectedFile.split('/').pop())
                               .removeClass('text-[#666]').addClass('text-[#00bfff]');
      $('#file-modal').hide();
      
      // Try to center map on the selected file if we have a marker for it
      const markers = [
        {
          coords: [44.4268, -68.2048], // Fox Island, Maine
          file: "input/foxisland/FoxIsland.laz"
        },
        {
          coords: [42.9446, -122.1090], // Wizard Island, Oregon (Crater Lake)
          file: "input/wizardisland/OR_WizardIsland.laz"
        }
      ];
      
      const matchingMarker = markers.find(m => m.file === selectedFile);
      if (matchingMarker && map) {
        map.setView(matchingMarker.coords, 13);
        console.log(`*** Map centered on file: ${selectedFile} ***`);
      }
    }
  });

  // Load files from server
  function loadFiles() {
    $.get('/api/list-laz-files', function(data) {
      const fileList = $('#file-list');
      fileList.empty();

      data.files.forEach(function(file) {
        const fileItem = $(`<div class="file-item" data-file="${file}">${file}</div>`);
        fileList.append(fileItem);
      });
    }).fail(function() {
      // Show error message if endpoint doesn't exist
      const fileList = $('#file-list');
      fileList.empty();
      fileList.append('<div class="text-red-400 p-3">Error loading files from server</div>');
    });
  }

  // Function to add image overlay to map
  function addImageOverlayToMap(processingType) {
    console.log(`*** Adding ${processingType} overlay to map ***`);
    
    // Extract base filename from selected LAZ file
    const baseFilename = selectedLazFile.split('/').pop().replace('.laz', '').replace('.copc', '');
    console.log(`*** Selected LAZ file: ${selectedLazFile} ***`);
    console.log(`*** Base filename: ${baseFilename} ***`);
    console.log(`*** Processing type: ${processingType} ***`);
    
    const apiUrl = `/api/overlay/${processingType}/${baseFilename}`;
    console.log(`*** API URL: ${apiUrl} ***`);
    
    // Call the overlay API
    $.get(apiUrl)
      .done(function(overlayData) {
        console.log(`*** Overlay data received for ${processingType}:`, overlayData);
        
        if (!overlayData.bounds || !overlayData.image_data) {
          console.error('*** Invalid overlay data received ***');
          console.error('*** Bounds:', overlayData.bounds);
          console.error('*** Image data length:', overlayData.image_data ? overlayData.image_data.length : 'undefined');
          alert('Failed to get valid overlay data');
          return;
        }
        
        // Remove existing overlay of this type if it exists
        if (mapOverlays[processingType]) {
          console.log(`*** Removing existing ${processingType} overlay ***`);
          map.removeLayer(mapOverlays[processingType]);
        }
        
        // Create image overlay
        const bounds = overlayData.bounds;
        const imageBounds = [
          [bounds.south, bounds.west],  // Southwest corner
          [bounds.north, bounds.east]   // Northeast corner
        ];
        
        console.log(`*** Bounds received:`, bounds);
        console.log(`*** Image bounds for Leaflet:`, imageBounds);
        console.log(`*** Image data size: ${overlayData.image_data.length} characters ***`);
        
        // Validate bounds are reasonable
        if (bounds.north < -90 || bounds.north > 90 || bounds.south < -90 || bounds.south > 90) {
          console.error('*** Invalid latitude bounds:', bounds);
          alert('Invalid latitude coordinates in overlay data');
          return;
        }
        if (bounds.east < -180 || bounds.east > 180 || bounds.west < -180 || bounds.west > 180) {
          console.error('*** Invalid longitude bounds:', bounds);
          alert('Invalid longitude coordinates in overlay data');
          return;
        }
        
        const imageUrl = `data:image/png;base64,${overlayData.image_data}`;
        console.log(`*** Creating overlay with imageUrl length: ${imageUrl.length} ***`);
        
        const overlay = L.imageOverlay(imageUrl, imageBounds, {
          opacity: 0.7,
          interactive: true
        });
        
        console.log(`*** Created Leaflet overlay object ***`);
        
        // Add overlay to map and store reference
        overlay.addTo(map);
        mapOverlays[processingType] = overlay;
        
        console.log(`*** Overlay added to map ***`);
        
        // Don't change map position - keep it centered on LAZ coordinates
        // The overlay should appear at its correct geographic location
        
        console.log(`*** ${processingType} overlay added successfully ***`);
        
        // Show success message
        showOverlayNotification(`${processingType.toUpperCase()} overlay added to map`, 'success');
        
        // Update button state
        updateAddToMapButtonState(processingType, true);
      })
      .fail(function(xhr, status, error) {
        console.error(`*** Failed to get overlay data for ${processingType}:`, status, error);
        console.error('*** XHR Status:', xhr.status);
        console.error('*** XHR Response Text:', xhr.responseText);
        console.error('*** XHR Response JSON:', xhr.responseJSON);
        
        let errorMessage = 'Failed to add overlay to map';
        if (xhr.responseJSON && xhr.responseJSON.error) {
          errorMessage = xhr.responseJSON.error;
        }
        
        showOverlayNotification(errorMessage, 'error');
      });
  }

  // Function to show overlay notification
  function showOverlayNotification(message, type = 'info') {
    // Remove existing notifications
    $('.overlay-notification').remove();
    
    const notificationClass = type === 'success' ? 'bg-green-600' : 
                              type === 'error' ? 'bg-red-600' : 'bg-blue-600';
    
    const notification = $(`
      <div class="overlay-notification fixed top-4 right-4 ${notificationClass} text-white px-4 py-2 rounded-lg shadow-lg z-[1000] transition-opacity duration-300">
        ${message}
      </div>
    `);
    
    $('body').append(notification);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
      notification.fadeOut(300, function() {
        $(this).remove();
      });
    }, 3000);
  }

  // Function to update Add to Map button state
  function updateAddToMapButtonState(processingType, isActive) {
    const button = $(`.add-to-map-btn[data-target="${processingType}"]`);
    if (isActive) {
      button.removeClass('bg-[#28a745] hover:bg-[#218838]')
             .addClass('bg-red-600 hover:bg-red-700')
             .text('Remove from Map');
    } else {
      button.removeClass('bg-red-600 hover:bg-red-700')
             .addClass('bg-[#28a745] hover:bg-[#218838]')
             .text('Add to Map');
    }
  }

  // Function to remove overlay from map
  function removeOverlayFromMap(processingType) {
    if (mapOverlays[processingType]) {
      console.log(`*** Removing ${processingType} overlay from map ***`);
      map.removeLayer(mapOverlays[processingType]);
      delete mapOverlays[processingType];
      updateAddToMapButtonState(processingType, false);
      showOverlayNotification(`${processingType.toUpperCase()} overlay removed from map`, 'info');
    }
  }

  // Function to show Add to Map button after successful processing
  function showAddToMapButton(processingType) {
    const button = $(`.add-to-map-btn[data-target="${processingType}"]`);
    button.removeClass('hidden');
    console.log(`*** Add to Map button shown for ${processingType} ***`);
  }

  function sendProcess(target) {
    console.log('sendProcess called with target:', target);
    console.log('selectedLazFile:', selectedLazFile);
    
    // Validate that a LAZ file is selected
    if (!selectedLazFile) {
      alert('Please select a LAZ file before processing.');
      return;
    }
    
    // Hide the Add to Map button initially
    $(`.add-to-map-btn[data-target="${target}"]`).addClass('hidden');
    
    // Use the selected LAZ file
    $.post(`/api/${target}`, { input_file: selectedLazFile }, function (data) {
      console.log('Success response:', data);
      const img = `<img src="data:image/png;base64,${data.image}" class="w-full h-full object-contain rounded-t-lg" />`;
      
      // Replace only the content area, not the entire gallery item
      $(`#cell-${target} .flex-1`).html(img);
      
      // Show the Add to Map button after successful processing
      showAddToMapButton(target);
    }).fail(function(xhr, status, error) {
      console.error('Request failed:', status, error);
      console.error('Response:', xhr.responseText);
    });
  }

  // Event handlers for processing checkboxes
  $('#processing-steps-container input[type="checkbox"]').on('change', function () {
    const target = $(this).data('target');
    const galleryItem = $(`#cell-${target}`);
    const procButtonInGallery = galleryItem.find('.proc-btn');

    if ($(this).is(':checked')) {
      galleryItem.show();
      // If the item was not processed yet, trigger processing
      // This assumes that if an image isn't there, it needs processing.
      // You might need a more robust check, e.g., checking if the image src is a placeholder
      if (!procButtonInGallery.next('.add-to-map-btn').length || procButtonInGallery.next('.add-to-map-btn').hasClass('hidden')) {
          if (selectedLazFile) { // Only process if a file is selected
            sendProcess(target);
          } else {
            // Optionally, you could show a placeholder or a message to select a file
            console.log(`Checkbox for ${target} checked, but no LAZ file selected. Processing deferred.`);
          }
      }
    } else {
      galleryItem.hide();
      // Optionally, remove overlay if it's on the map when unchecking
      if (mapOverlays[target]) {
        removeOverlayFromMap(target);
      }
    }
  });

  // Function to initialize gallery visibility based on checkboxes
  function initializeGalleryVisibility() {
    $('#processing-steps-container input[type="checkbox"]').each(function() {
      const target = $(this).data('target');
      const galleryItem = $(`#cell-${target}`);
      if ($(this).is(':checked')) {
        galleryItem.show();
      } else {
        galleryItem.hide();
      }
    });
  }

  // Call on page load to set initial visibility
  initializeGalleryVisibility();


  // Event handlers for processing buttons (within gallery items)
  // These remain to allow re-processing if needed, or initial processing if checkbox is checked later
  $(document).on('click', '.gallery-item .proc-btn', function () {
    const target = $(this).data('target');
    console.log('Gallery process button clicked, target:', target);
    sendProcess(target);
  });


  // Event handlers for Add to Map buttons
  $(document).on('click', '.add-to-map-btn[data-target]', function() {
    const processingType = $(this).data('target');
    const isActive = mapOverlays[processingType] !== undefined;
    
    if (isActive) {
      removeOverlayFromMap(processingType);
    } else {
      addImageOverlayToMap(processingType);
    }
  });

  // Event handler for Test Overlay button
  $('#test-overlay-btn').on('click', function() {
    console.log('🧪 Test Overlay button clicked');
    
    if (!selectedLazFile) {
      alert('Please select a LAZ file first before testing overlay.');
      return;
    }
    
    // Extract base filename from selected LAZ file path
    const baseFilename = selectedLazFile.split('/').pop().replace('.laz', '');
    console.log('🧪 Testing overlay for base filename:', baseFilename);
    
    // Call the test overlay API endpoint
    fetch(`/api/test-overlay/${baseFilename}`)
      .then(response => {
        if (!response.ok) {
          return response.json().then(errorData => {
            throw new Error(errorData.error || `HTTP ${response.status}`);
          });
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          console.log('🧪 Test overlay successful:', data);
          
          // Add the test overlay to the map
          const bounds = [
            [data.bounds.south, data.bounds.west],
            [data.bounds.north, data.bounds.east]
          ];
          
          const testOverlay = L.imageOverlay(
            `data:image/png;base64,${data.image_data}`,
            bounds,
            {
              opacity: 0.7,
              interactive: false
            }
          ).addTo(map);
          
          // Store the test overlay so it can be removed
          mapOverlays['TEST'] = testOverlay;
          
          console.log('🧪 Test overlay added to map with bounds:', bounds);
          alert('Test overlay added to map! Look for a black rectangle with red border at the LAZ file coordinates.');
          
        } else {
          console.error('🧪 Test overlay failed:', data.error || 'Unknown error');
          alert(`Test overlay failed: ${data.error || 'Unknown error'}`);
        }
      })
      .catch(error => {
        console.error('🧪 Error calling test overlay API:', error);
        alert(`Error testing overlay: ${error.message}`);
      });
  });

  $('#chat-send').on('click', function () {
    const prompt = $('#chat-input').val();
    const model = $('#chat-model').val();
    $('#chat-log').append(`<div class='user'><strong>You:</strong> ${prompt}</div>`);
    $.post('/api/chat', JSON.stringify({ prompt: prompt, model: model }), function (data) {
      $('#chat-log').append(`<div class='llm'><strong>LLM:</strong> ${data.response}</div>`);
    }, 'json');
    $('#chat-input').val('');
  });
  
  // Data Acquisition Functions
  
  async function checkDataAvailability(lat, lng) {
    console.log(`*** Checking data availability for ${lat}, ${lng} ***`);
    
    try {
      const response = await fetch('/api/check-data-availability', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lat: parseFloat(lat),
          lng: parseFloat(lng),
          buffer_km: 1.0
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('*** Data availability response:', data);
        
        // Update UI with availability information
        updateDataAvailabilityUI(data.availability);
        
        // Show data acquisition dialog
        showDataAcquisitionDialog(lat, lng, data.availability);
      } else {
        console.error('*** Failed to check data availability:', response.statusText);
        showErrorMessage('Failed to check data availability');
      }
    } catch (error) {
      console.error('*** Error checking data availability:', error);
      showErrorMessage('Error checking data availability: ' + error.message);
    }
  }
  
  function updateDataAvailabilityUI(availability) {
    // Create or update availability indicator
    let indicator = document.getElementById('data-availability-indicator');
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'data-availability-indicator';
      indicator.className = 'data-availability-indicator';
      document.body.appendChild(indicator);
    }
    
    const availableData = [];
    if (availability.high_res_lidar) availableData.push('High-res LiDAR');
    if (availability.srtm_dem) availableData.push('SRTM DEM');
    if (availability.sentinel2) availableData.push('Sentinel-2');
    if (availability.landsat) availableData.push('Landsat');
    
    indicator.innerHTML = `
      <div class="availability-header">Available Data Sources:</div>
      <div class="availability-list">
        ${availableData.map(data => `<div class="availability-item">✓ ${data}</div>`).join('')}
      </div>
    `;
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      if (indicator && indicator.parentNode) {
        indicator.parentNode.removeChild(indicator);
      }
    }, 5000);
  }
  
  function showDataAcquisitionDialog(lat, lng, availability) {
    // Create dialog HTML
    const dialogHtml = `
      <div id="data-acquisition-dialog" class="data-acquisition-dialog">
        <div class="dialog-content">
          <div class="dialog-header">
            <h3>Acquire Data for Location</h3>
            <button class="close-dialog" onclick="closeDataAcquisitionDialog()">&times;</button>
          </div>
          <div class="dialog-body">
            <div class="location-info">
              <strong>Location:</strong> ${lat}, ${lng}
            </div>
            
            <div class="acquisition-options">
              <label for="buffer-km">Buffer (km):</label>
              <input type="number" id="buffer-km" value="1.0" min="0.1" max="10" step="0.1">
              
              <label for="data-sources">Data Sources:</label>
              <select id="data-sources" multiple>
                ${availability.high_res_lidar ? '<option value="high_res_lidar">High-Res LiDAR</option>' : ''}
                ${availability.srtm_dem ? '<option value="opentopography">OpenTopography (SRTM)</option>' : ''}
                ${availability.sentinel2 ? '<option value="sentinel2">Sentinel-2 Imagery</option>' : ''}
                ${availability.landsat ? '<option value="landsat">Landsat Imagery</option>' : ''}
                <option value="mock_test" selected>🧪 Mock Test Data (Always Available)</option>
              </select>
              
              <label for="max-file-size">Max File Size (MB):</label>
              <input type="number" id="max-file-size" value="500" min="10" max="2000" step="10">
            </div>
            
            <div class="dialog-actions">
              <button class="estimate-btn" onclick="estimateDownloadSize('${lat}', '${lng}')">
                Estimate Size
              </button>
              <button class="acquire-btn" onclick="acquireData('${lat}', '${lng}')">
                Acquire Data
              </button>
            </div>
            
            <div id="acquisition-status" class="acquisition-status"></div>
          </div>
        </div>
      </div>
    `;
    
    // Remove existing dialog if present
    const existingDialog = document.getElementById('data-acquisition-dialog');
    if (existingDialog) {
      existingDialog.remove();
    }
    
    // Add dialog to page
    document.body.insertAdjacentHTML('beforeend', dialogHtml);
  }
  
  function closeDataAcquisitionDialog() {
    const dialog = document.getElementById('data-acquisition-dialog');
    if (dialog) {
      dialog.remove();
    }
  }
  
  async function estimateDownloadSize(lat, lng) {
    const bufferKm = parseFloat(document.getElementById('buffer-km').value);
    const statusDiv = document.getElementById('acquisition-status');
    
    statusDiv.innerHTML = '<div class="status-loading">Estimating download size...</div>';
    
    try {
      const response = await fetch('/api/estimate-download-size', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lat: parseFloat(lat),
          lng: parseFloat(lng),
          buffer_km: bufferKm
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        const estimates = data.estimates_mb;
        
        let estimateHtml = '<div class="size-estimates"><h4>Estimated Download Sizes:</h4>';
        for (const [dataType, sizeMb] of Object.entries(estimates)) {
          estimateHtml += `<div class="estimate-item">${dataType}: ${sizeMb.toFixed(1)} MB</div>`;
        }
        estimateHtml += '</div>';
        
        statusDiv.innerHTML = estimateHtml;
      } else {
        statusDiv.innerHTML = '<div class="status-error">Failed to estimate download size</div>';
      }
    } catch (error) {
      console.error('Error estimating download size:', error);
      statusDiv.innerHTML = '<div class="status-error">Error estimating download size</div>';
    }
  }
  
  async function acquireData(lat, lng) {
    const bufferKm = parseFloat(document.getElementById('buffer-km').value);
    const maxFileSizeMb = parseFloat(document.getElementById('max-file-size').value);
    const dataSourcesSelect = document.getElementById('data-sources');
    const selectedSources = Array.from(dataSourcesSelect.selectedOptions).map(option => option.value);
    const statusDiv = document.getElementById('acquisition-status');
    
    // Show loading status
    statusDiv.innerHTML = `
      <div class="status-loading">
        <div class="loading-spinner"></div>
        Acquiring data... This may take a few minutes.
      </div>
    `;
    
    try {
      const response = await fetch('/api/acquire-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lat: parseFloat(lat),
          lng: parseFloat(lng),
          buffer_km: bufferKm,
          data_sources: selectedSources.length > 0 ? selectedSources : null,
          max_file_size_mb: maxFileSizeMb
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.success) {
          let resultHtml = `
            <div class="status-success">
              <h4>✓ Data Acquisition Successful!</h4>
              <div class="result-details">
                <div><strong>Source:</strong> ${result.source_used}</div>
                <div><strong>Download Size:</strong> ${result.download_size_mb.toFixed(1)} MB</div>
                <div><strong>Processing Time:</strong> ${result.processing_time_seconds.toFixed(1)}s</div>
              </div>
              <div class="acquired-files">
                <h5>Files:</h5>
          `;
          
          for (const [dataType, filePath] of Object.entries(result.files)) {
            resultHtml += `<div class="file-item">${dataType}: ${filePath}</div>`;
          }
          
          resultHtml += '</div></div>';
          
          statusDiv.innerHTML = resultHtml;
          
          // Optional: Add acquired data to map as overlay
          addAcquiredDataToMap(result);
          
        } else {
          statusDiv.innerHTML = `
            <div class="status-error">
              <h4>✗ Data Acquisition Failed</h4>
              <div class="error-details">
                ${result.errors.map(error => `<div>${error}</div>`).join('')}
              </div>
            </div>
          `;
        }
      } else {
        statusDiv.innerHTML = '<div class="status-error">Failed to acquire data</div>';
      }
    } catch (error) {
      console.error('Error acquiring data:', error);
      statusDiv.innerHTML = '<div class="status-error">Error acquiring data: ' + error.message + '</div>';
    }
  }
  
  function addAcquiredDataToMap(result) {
    // This function would add the acquired data as an overlay on the map
    // For now, we'll just log the result
    console.log('*** Data acquired successfully:', result);
    
    // You could implement map overlay functionality here
    // For example, adding a WMS layer or processed image overlay
  }
  
  function showErrorMessage(message) {
    // Create error notification
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-notification';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #ff4444;
      color: white;
      padding: 12px 20px;
      border-radius: 4px;
      z-index: 10000;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (errorDiv && errorDiv.parentNode) {
        errorDiv.parentNode.removeChild(errorDiv);
      }
    }, 5000);
  }

  function showSuccessMessage(message) {
    // Create success notification
    const successDiv = document.createElement('div');
    successDiv.className = 'success-notification';
    successDiv.textContent = message;
    successDiv.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #28a745;
      color: white;
      padding: 12px 20px;
      border-radius: 4px;
      z-index: 10000;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    `;
    
    document.body.appendChild(successDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (successDiv && successDiv.parentNode) {
        successDiv.parentNode.removeChild(successDiv);
      }
    }, 5000);
  }

  // WebSocket connection for real-time progress updates
  let progressSocket = null;
  let progressDisplay = null;
  let downloadAborted = false;
  let currentDownloadController = null;
  let currentDownloadId = null;

  function initializeProgressWebSocket() {
    if (progressSocket && progressSocket.readyState === WebSocket.OPEN) {
      return Promise.resolve(); // Already connected
    }

    return new Promise((resolve, reject) => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/progress`;
      
      console.log('*** Connecting to WebSocket:', wsUrl, '***');
      progressSocket = new WebSocket(wsUrl);
      
      progressSocket.onopen = function(event) {
        console.log('*** WebSocket connected for progress updates ***');
        resolve();
      };
      
      progressSocket.onmessage = function(event) {
        try {
          const data = JSON.parse(event.data);
          console.log('*** WebSocket message received:', data, '***');
          updateProgressDisplay(data);
        } catch (error) {
          console.error('*** Error parsing WebSocket message:', error);
        }
      };
      
      progressSocket.onclose = function(event) {
        console.log('*** WebSocket disconnected ***');
        // Reconnect after a delay if not intentionally closed
        if (!downloadAborted) {
          setTimeout(initializeProgressWebSocket, 3000);
        }
      };
      
      progressSocket.onerror = function(error) {
        console.error('*** WebSocket error:', error);
        reject(error);
      };
    });
  }

  function showProgressDisplay() {
    if (progressDisplay) {
      progressDisplay.remove();
    }
    
    downloadAborted = false;
    
    progressDisplay = $(`
      <div id="progress-overlay" style="
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        z-index: 1000;
        min-width: 500px;
        max-width: 700px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
          <h3 style="margin: 0; color: #333;">🛰️ Sentinel-2 Download Progress</h3>
          <button id="progress-cancel" style="
            background: #ff4444;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
          ">Cancel Download</button>
        </div>
        <div id="progress-content" style="
          max-height: 300px;
          overflow-y: auto;
          margin-bottom: 15px;
        ">
          <div class="progress-item" style="
            padding: 8px 0;
            border-bottom: 1px solid #eee;
            font-size: 14px;
          ">
            <strong>Status:</strong> <span id="progress-status">Initializing connection...</span>
          </div>
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 10px;">
          <button id="progress-close" style="
            background: #6c757d;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
          ">Close</button>
        </div>
      </div>
      <div id="progress-backdrop" style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 999;
      "></div>
    `);
    
    $('body').append(progressDisplay);
    
    $('#progress-close').on('click', function() {
      hideProgressDisplay();
    });
    
    $('#progress-cancel').on('click', function() {
      cancelDownload();
    });
    
    console.log('*** Progress display shown ***');
  }

  function cancelDownload() {
    console.log('*** Canceling Sentinel-2 download ***');
    downloadAborted = true;
    
    // Send cancellation message via WebSocket first
    if (progressSocket && progressSocket.readyState === WebSocket.OPEN && currentDownloadId) {
      const cancellationMessage = {
        type: "cancel_download",
        download_id: currentDownloadId
      };
      
      console.log('*** Sending cancellation message via WebSocket:', cancellationMessage, '***');
      progressSocket.send(JSON.stringify(cancellationMessage));
    }
    
    // Abort the fetch request if possible
    if (currentDownloadController) {
      currentDownloadController.abort();
    }
    
    // Update UI
    $('#progress-status').text('Cancelling download...');
    $('#progress-cancel').prop('disabled', true).text('Cancelling...');
    
    // Reset button state
    const button = $('#test-sentinel2-btn');
    button.text('🛰️ Download Sentinel-2').prop('disabled', false);
  }

  function hideProgressDisplay() {
    if (progressDisplay) {
      progressDisplay.remove();
      progressDisplay = null;
    }
    downloadAborted = false;
    currentDownloadController = null;
    currentDownloadId = null;
    
    // Close WebSocket
    if (progressSocket && progressSocket.readyState === WebSocket.OPEN) {
      progressSocket.close();
      progressSocket = null;
    }
  }

  function updateProgressDisplay(data) {
    console.log('*** Updating progress display with:', data, '***');
    
    if (!progressDisplay) {
      console.log('*** No progress display to update ***');
      return;
    }
    
    // Capture download ID when available
    if (data.download_id && !currentDownloadId) {
      currentDownloadId = data.download_id;
      console.log('*** Captured download ID:', currentDownloadId, '***');
    }
    
    const content = $('#progress-content');
    const status = $('#progress-status');
    
    // Update based on message type
    switch (data.type) {
      case 'download_start':
        status.text(`Starting download of ${data.band} band...`);
        addProgressItem(data.band, 'Starting download...', '🟡');
        break;
        
      case 'download_info':
        const fileSizeText = data.total_size_mb ? 
          `File size: ${data.total_size_mb.toFixed(2)} MB` : 
          'File information available';
        addProgressItem(data.band, fileSizeText, '📊');
        break;
        
      case 'download_progress':
        let progressText;
        if (data.progress && data.downloaded_mb && data.total_mb) {
          progressText = `${data.progress.toFixed(1)}% (${data.downloaded_mb.toFixed(2)}/${data.total_mb.toFixed(2)} MB)`;
        } else if (data.downloaded_mb) {
          progressText = `${data.downloaded_mb.toFixed(2)} MB downloaded`;
        } else {
          progressText = 'Downloading...';
        }
        status.text(`Downloading ${data.band}: ${progressText}`);
        updateOrAddProgressItem(data.band, progressText, '⬇️');
        break;
        
      case 'download_complete':
        status.text(`${data.band} download complete!`);
        const completionText = data.final_size_mb ? 
          `Download complete: ${data.final_size_mb.toFixed(2)} MB` : 
          'Download complete!';
        updateOrAddProgressItem(data.band, completionText, '✅');
        break;
        
      case 'crop_start':
        status.text(`Cropping ${data.band} band...`);
        updateOrAddProgressItem(data.band, 'Cropping to requested area...', '✂️');
        break;
        
      case 'crop_complete':
        updateOrAddProgressItem(data.band, `Cropped: ${data.size_reduction.toFixed(1)}% size reduction`, '✅');
        break;
        
      case 'download_cancelled':
        status.text('Download cancelled by user');
        updateOrAddProgressItem(data.band, 'Download cancelled', '❌');
        $('#progress-cancel').prop('disabled', true).text('Cancelled');
        
        // Show error message and hide after delay
        showErrorMessage('Download cancelled by user');
        setTimeout(() => {
          hideProgressDisplay();
        }, 2000);
        break;
        
      case 'cancellation_response':
        if (data.success) {
          console.log('*** Backend confirmed cancellation ***');
          status.text('Cancellation confirmed');
        } else {
          console.log('*** Backend cancellation failed ***');
          status.text('Cancellation failed - download may continue');
        }
        break;
        
      case 'download_error':
      case 'crop_error':
        status.text(`Error: ${data.message}`);
        updateOrAddProgressItem(data.band, `Error: ${data.message}`, '❌');
        break;
        
      default:
        console.log('*** Unknown progress message type:', data.type, '***');
    }
  }

  function addProgressItem(band, message, icon) {
    const content = $('#progress-content');
    const itemId = `progress-${band}`;
    
    if ($(`#${itemId}`).length === 0) {
      content.append(`
        <div id="${itemId}" class="progress-item" style="
          padding: 8px 0;
          border-bottom: 1px solid #eee;
          font-size: 14px;
        ">
          <span class="progress-icon">${icon}</span>
          <strong>${band}:</strong> 
          <span class="progress-message">${message}</span>
        </div>
      `);
    }
    
    // Scroll to bottom
    content.scrollTop(content[0].scrollHeight);
  }

  function updateOrAddProgressItem(band, message, icon) {
    const itemId = `progress-${band}`;
    const existingItem = $(`#${itemId}`);
    
    if (existingItem.length > 0) {
      existingItem.find('.progress-icon').text(icon);
      existingItem.find('.progress-message').text(message);
    } else {
      addProgressItem(band, message, icon);
    }
    
    // Scroll to bottom
    const content = $('#progress-content');
    content.scrollTop(content[0].scrollHeight);
  }

  // Download Sentinel-2 red and NIR bands for specified coordinates
  async function downloadSentinel2Images(lat, lng) {
    console.log(`*** Downloading Sentinel-2 images for ${lat}, ${lng} ***`);
    
    // Show progress display first
    showProgressDisplay();
    
    try {
      // Initialize WebSocket connection and wait for it to be ready
      console.log('*** Establishing WebSocket connection... ***');
      await initializeProgressWebSocket();
      console.log('*** WebSocket ready, starting download... ***');
      
      // Update initial status
      $('#progress-status').text('WebSocket connected, preparing download...');
      
    } catch (error) {
      console.error('*** Failed to establish WebSocket connection:', error, '***');
      $('#progress-status').text('WebSocket connection failed, continuing without live updates...');
    }
    
    // Show loading message on button
    const button = $('#test-sentinel2-btn');
    const originalText = button.text();
    button.text('🛰️ Downloading...').prop('disabled', true);
    
    // Create AbortController for cancellation
    currentDownloadController = new AbortController();
    
    try {
      $('#progress-status').text('Sending download request...');
      
      const response = await fetch('/api/download-sentinel2', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lat: parseFloat(lat),
          lng: parseFloat(lng),
          buffer_km: 5.0,  // 5km radius for 10km x 10km area
          bands: ['B04', 'B08']  // Sentinel-2 red and NIR band identifiers
        }),
        signal: currentDownloadController.signal  // Add abort signal
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.success) {
          // Show success message for download
          showSuccessMessage(`Successfully downloaded Sentinel-2 images! 
            File size: ${result.file_size_mb.toFixed(2)} MB
            Acquisition date: ${result.metadata.acquisition_date || 'Unknown'}
            Cloud cover: ${result.metadata.cloud_cover}%`);
          
          console.log('*** Sentinel-2 download successful:', result);
          
          // Close progress display after a short delay
          setTimeout(() => {
            hideProgressDisplay();
          }, 2000);
          
          // Automatically convert TIF files to PNG and display them
          const regionName = result.metadata.region_name;
          if (regionName) {
            console.log(`*** Converting Sentinel-2 TIFs to PNG for region: ${regionName} ***`);
            await convertAndDisplaySentinel2(regionName);
          } else {
            console.error('*** No region name found in Sentinel-2 result ***');
          }
        } else {
          showErrorMessage('Sentinel-2 download failed: ' + result.error_message);
          hideProgressDisplay();
        }
      } else {
        const errorText = await response.text();
        showErrorMessage('Failed to download Sentinel-2 images: ' + errorText);
        hideProgressDisplay();
      }
    } catch (error) {
      console.error('*** Error downloading Sentinel-2 images:', error);
      
      // Handle different error types
      if (error.name === 'AbortError') {
        console.log('*** Download was aborted by user ***');
        // Don't show error message for user-initiated cancellation
        if (!downloadAborted) {
          showErrorMessage('Download was cancelled');
        }
      } else {
        showErrorMessage('Error downloading Sentinel-2 images: ' + error.message);
      }
      
      hideProgressDisplay();
    } finally {
      // Reset button
      button.text(originalText).prop('disabled', false);
    }
  }

  // Function to convert Sentinel-2 TIF files to PNG and display them
  async function convertAndDisplaySentinel2(regionName) {
    console.log(`*** Converting Sentinel-2 images for region: ${regionName} ***`);
    
    try {
      // Convert TIF files to PNG
      const formData = new FormData();
      formData.append('region_name', regionName);
      
      const response = await fetch('/api/convert-sentinel2', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.success && result.files && result.files.length > 0) {
          console.log(`*** Successfully converted ${result.files.length} Sentinel-2 images ***`);
          
          // Display each converted image in the grid
          result.files.forEach(file => {
            displaySentinel2Image(file, regionName);
          });
          
          showSuccessMessage(`Converted and displayed ${result.files.length} Sentinel-2 images: ${result.files.map(f => f.band).join(', ')}`);
        } else {
          // Handle both single error and multiple errors
          const errorMsg = result.error_message || (result.errors && result.errors.length > 0 ? result.errors.join(', ') : 'Unknown error');
          console.error('*** Sentinel-2 conversion failed:', errorMsg);
          showErrorMessage('Failed to convert Sentinel-2 images: ' + errorMsg);
        }
      } else {
        const errorText = await response.text();
        console.error('*** Sentinel-2 conversion request failed:', errorText);
        showErrorMessage('Failed to convert Sentinel-2 images: ' + errorText);
      }
    } catch (error) {
      console.error('*** Error converting Sentinel-2 images:', error);
      showErrorMessage('Error converting Sentinel-2 images: ' + error.message);
    }
  }

  // Function to display a single Sentinel-2 image in the grid
  function displaySentinel2Image(fileInfo, regionName) {
    console.log(`*** Displaying Sentinel-2 ${fileInfo.band} band for region ${regionName} ***`);
    
    const imageContainer = document.getElementById('image-container');
    if (!imageContainer) {
      console.error('*** Image container not found ***');
      return;
    }
    
    // Create image cell
    const imageCell = document.createElement('div');
    imageCell.className = 'image-cell';
    imageCell.innerHTML = `
      <div class="image-header">
        <h3>🛰️ Sentinel-2 ${fileInfo.band}</h3>
        <p class="image-subtitle">Region: ${regionName}</p>
        <p class="image-info">Size: ${fileInfo.size_mb.toFixed(2)} MB</p>
      </div>
      <div class="image-content">
        <img src="data:image/png;base64,${fileInfo.image}" alt="Sentinel-2 ${fileInfo.band} Band">
        <div class="image-actions">
          <button class="btn btn-map" onclick="addSentinel2ToMap('${regionName}', '${fileInfo.band}')">
            📍 Add to Map
          </button>
          <button class="btn btn-download" onclick="downloadSentinel2PNG('${fileInfo.png_path}', '${regionName}_${fileInfo.band}')">
            💾 Download PNG
          </button>
        </div>
      </div>
    `;
    
    // Add to the beginning of the container (newest first)
    imageContainer.insertBefore(imageCell, imageContainer.firstChild);
    
    console.log(`*** Successfully displayed Sentinel-2 ${fileInfo.band} image ***`);
  }

  // Function to add Sentinel-2 image as overlay on the map
  window.addSentinel2ToMap = async function(regionName, bandName) {
    console.log(`*** Adding Sentinel-2 ${bandName} to map for region: ${regionName} ***`);
    
    try {
      // Get overlay data for the Sentinel-2 image
      const response = await fetch(`/api/overlay/sentinel2/${regionName}_${bandName}`);
      
      if (response.ok) {
        const overlayData = await response.json();
        
        if (overlayData.success && overlayData.bounds && overlayData.image_data) {
          // Remove existing Sentinel-2 overlay if any
          const overlayKey = `sentinel2_${bandName}`;
          if (mapOverlays[overlayKey]) {
            map.removeLayer(mapOverlays[overlayKey]);
          }
          
          // Create image overlay
          const bounds = [
            [overlayData.bounds.south, overlayData.bounds.west],
            [overlayData.bounds.north, overlayData.bounds.east]
          ];
          
          const imageUrl = `data:image/png;base64,${overlayData.image_data}`;
          const overlay = L.imageOverlay(imageUrl, bounds, {
            opacity: 0.7,
            attribution: `Sentinel-2 ${bandName} - ${regionName}`
          });
          
          overlay.addTo(map);
          mapOverlays[overlayKey] = overlay;
          
          // Fit map to overlay bounds
          map.fitBounds(bounds);
          
          showSuccessMessage(`Added Sentinel-2 ${bandName} overlay to map`);
          console.log(`*** Successfully added Sentinel-2 ${bandName} overlay to map ***`);
        } else {
          showErrorMessage('Failed to get overlay data for Sentinel-2 image');
        }
      } else {
        showErrorMessage('Failed to load Sentinel-2 overlay data');
      }
    } catch (error) {
      console.error('*** Error adding Sentinel-2 to map:', error);
      showErrorMessage('Error adding Sentinel-2 to map: ' + error.message);
    }
  };

  // Function to download Sentinel-2 PNG file
  window.downloadSentinel2PNG = function(pngPath, filename) {
    console.log(`*** Downloading Sentinel-2 PNG: ${pngPath} ***`);
    
    // Create a download link - pngPath is already relative to output directory
    const link = document.createElement('a');
    link.href = `/output/${pngPath.replace('output/', '')}`;  // Remove output/ prefix if present
    link.download = `${filename}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showSuccessMessage(`Downloaded ${filename}.png`);
  };

  // ...existing code...
});
