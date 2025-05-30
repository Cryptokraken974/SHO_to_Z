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
  }, 100);

  // Accordion functionality
  $('#laz-accordion').on('click', function() {
    const content = $('#laz-content');
    const arrow = $('.accordion-arrow');

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

  // Event handlers for processing buttons
  $('.proc-btn[data-target]').on('click', function () {
    const target = $(this).data('target');
    console.log('Button clicked, target:', target);
    console.log('Button element:', this);
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
  
});
