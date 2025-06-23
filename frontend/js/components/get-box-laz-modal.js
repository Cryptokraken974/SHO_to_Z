/**
 * Get Box LAZ Modal Component
 * Handles the modal for LAZ data acquisition within a drawn box
 */

window.GetBoxLazModal = {
  modal: null,
  selectedRegionCount: 5,
  
  /**
   * Initialize the Get Box LAZ modal functionality
   */
  init() {
    this.modal = document.getElementById('get-box-laz-modal');
    this.setupEventHandlers();
    Utils.log('info', 'Get Box LAZ Modal initialized');
  },
  
  /**
   * Setup event handlers for modal interactions
   */
  setupEventHandlers() {
    // Open modal button
    const openBtn = document.getElementById('get-box-laz-btn');
    if (openBtn) {
      openBtn.addEventListener('click', () => {
        this.openModal();
      });
    }
    
    // Close modal buttons
    const closeBtn = document.getElementById('close-get-box-laz-modal');
    const cancelBtn = document.getElementById('cancel-get-box-laz');
    
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        this.closeModal();
      });
    }
    
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        this.closeModal();
      });
    }
    
    // Close modal when clicking outside
    if (this.modal) {
      this.modal.addEventListener('click', (e) => {
        if (e.target === this.modal) {
          this.closeModal();
        }
      });
    }
    
    // Region count buttons
    const regionCountBtns = document.querySelectorAll('.region-count-btn');
    regionCountBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        this.selectRegionCount(parseInt(btn.dataset.count));
      });
    });
    
    // Start button
    const startBtn = document.getElementById('start-get-box-laz');
    if (startBtn) {
      startBtn.addEventListener('click', () => {
        this.handleStart();
      });
    }
    
    // ESC key to close modal
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isModalOpen()) {
        this.closeModal();
      }
    });
  },
  
  /**
   * Open the modal
   */
  openModal() {
    if (!this.modal) return;
    
    // Check if there's a drawn box or path
    if (!MapManager.currentBox && !MapManager.currentPath) {
      Utils.showNotification('Please draw a box or create a path on the map first', 'warning', 3000);
      return;
    }
    
    this.modal.classList.remove('hidden');
    this.resetForm();
    
    // Update modal title and content based on what's available
    this.updateModalContent();
    
    // Focus on region name input
    const regionNameInput = document.getElementById('box-laz-region-name');
    if (regionNameInput) {
      setTimeout(() => regionNameInput.focus(), 100);
    }
    
    Utils.log('info', 'Get LAZ modal opened');
  },
  
  /**
   * Close the modal
   */
  closeModal() {
    if (!this.modal) return;
    
    this.modal.classList.add('hidden');
    Utils.log('info', 'Get Box LAZ modal closed');
  },
  
  /**
   * Update modal content based on available geometry (box or path)
   */
  updateModalContent() {
    const modalTitle = document.querySelector('#get-box-laz-modal h3');
    const regionCountSection = document.querySelector('#get-box-laz-modal .space-y-4 > div:first-child');
    
    if (MapManager.currentBox && MapManager.currentPath) {
      // Both box and path available - prioritize box for region subdivision
      if (modalTitle) modalTitle.textContent = 'Get LAZ Data';
      if (regionCountSection) regionCountSection.style.display = 'block';
    } else if (MapManager.currentBox) {
      // Only box available
      if (modalTitle) modalTitle.textContent = 'Get Box LAZ Data';
      if (regionCountSection) regionCountSection.style.display = 'block';
    } else if (MapManager.currentPath) {
      // Only path available - allow region subdivision along path
      if (modalTitle) modalTitle.textContent = 'Get Path LAZ Data';
      if (regionCountSection) regionCountSection.style.display = 'block';
    }
  },
  
  /**
   * Check if modal is currently open
   * @returns {boolean}
   */
  isModalOpen() {
    return this.modal && !this.modal.classList.contains('hidden');
  },
  
  /**
   * Reset the form to default values
   */
  resetForm() {
    // Reset region count selection
    this.selectRegionCount(5);
    
    // Clear region name input
    const regionNameInput = document.getElementById('box-laz-region-name');
    if (regionNameInput) {
      regionNameInput.value = '';
    }
  },
  
  /**
   * Select a region count option
   * @param {number} count - Number of regions to select
   */
  selectRegionCount(count) {
    this.selectedRegionCount = count;
    
    // Update button states
    const regionCountBtns = document.querySelectorAll('.region-count-btn');
    regionCountBtns.forEach(btn => {
      const btnCount = parseInt(btn.dataset.count);
      if (btnCount === count) {
        btn.classList.remove('bg-[#303030]', 'hover:bg-[#404040]');
        btn.classList.add('bg-[#6f42c1]', 'hover:bg-[#5a2d91]');
      } else {
        btn.classList.remove('bg-[#6f42c1]', 'hover:bg-[#5a2d91]');
        btn.classList.add('bg-[#303030]', 'hover:bg-[#404040]');
      }
    });
    
    Utils.log('info', `Selected region count: ${count}`);
  },
  
  /**
   * Handle the start button click
   */
  async handleStart() {
    try {
      // Validate inputs
      if (!this.selectedRegionCount) {
        Utils.showNotification('Please select the number of regions', 'error');
        return;
      }

      const regionNameInput = document.getElementById('box-laz-region-name');
      const regionName = regionNameInput?.value?.trim();
      
      if (!regionName) {
        Utils.showNotification('Please enter a region name', 'error');
        return;
      }

      // Check if a box or path is drawn
      const hasBox = window.MapManager?.currentBox;
      const hasPath = window.MapManager?.currentPath;
      
      if (!hasBox && !hasPath) {
        Utils.showNotification('Please draw a box or path on the map first', 'error');
        return;
      }

      const startBtn = document.getElementById('start-get-box-laz');
      startBtn.disabled = true;
      startBtn.textContent = 'Processing...';

      const geometryType = hasBox ? 'box' : 'path';
      Utils.log('info', `Starting LAZ region creation from ${geometryType}: ${this.selectedRegionCount} regions named ${regionName}_X`);
      
      let createdRegions = [];
      
      if (hasBox) {
        // Handle box-based region creation (existing logic)
        createdRegions = await this.createRegionsFromBox(regionName);
      } else if (hasPath) {
        // Handle path-based region creation (new logic)
        createdRegions = await this.createRegionsFromPath(regionName);
      }

      // Show results
      if (createdRegions.length > 0) {
        Utils.showNotification(`Successfully created ${createdRegions.length} regions!`, 'success');
        
        // Refresh the region list to show new regions
        if (window.FileManager && typeof FileManager.loadFiles === 'function') {
          setTimeout(() => {
            FileManager.loadFiles();
          }, 1000);
        }

        // Close modal
        this.closeModal();
      } else {
        Utils.showNotification('Failed to create any regions', 'error');
      }

    } catch (error) {
      Utils.log('error', 'Error in handleStart:', error);
      Utils.showNotification('Error creating regions', 'error');
    } finally {
      // Reset button
      const startBtn = document.getElementById('start-get-box-laz');
      if (startBtn) {
        startBtn.disabled = false;
        startBtn.textContent = 'Start';
      }
    }
  },
  
  /**
   * Create regions from a box geometry
   * @param {string} regionName - Base name for regions
   * @returns {Array} Array of created regions
   */
  async createRegionsFromBox(regionName) {
    const box = window.MapManager.currentBox;
    const bounds = box.getBounds();
    const north = bounds.getNorth();
    const south = bounds.getSouth();
    const east = bounds.getEast();
    const west = bounds.getWest();

    Utils.log('info', `Box bounds: N=${north}, S=${south}, E=${east}, W=${west}`);

    // Calculate grid dimensions
    const gridSize = this.calculateGridSize(this.selectedRegionCount);
    Utils.log('info', `Grid size: ${gridSize.rows} x ${gridSize.cols}`);

    // Calculate region size
    const latStep = (north - south) / gridSize.rows;
    const lngStep = (east - west) / gridSize.cols;

    Utils.showNotification(`Creating ${this.selectedRegionCount} regions from box...`, 'info');

    // Create regions
    const createdRegions = [];
    let regionId = 1;

    for (let row = 0; row < gridSize.rows; row++) {
      for (let col = 0; col < gridSize.cols; col++) {
        if (regionId > this.selectedRegionCount) break;

        // Calculate region bounds
        const regionSouth = south + (row * latStep);
        const regionNorth = south + ((row + 1) * latStep);
        const regionWest = west + (col * lngStep);
        const regionEast = west + ((col + 1) * lngStep);

        // Calculate center coordinates
        const centerLat = (regionSouth + regionNorth) / 2;
        const centerLng = (regionWest + regionEast) / 2;

        // Create region name
        const currentRegionName = `${regionName}_${regionId}`;

        // Create region data for API
        const regionData = {
          region_name: currentRegionName,
          coordinates: {
            lat: centerLat,
            lng: centerLng
          },
          place_name: currentRegionName,
          ndvi_enabled: false,
          created_at: new Date().toISOString(),
          bounds: {
            north: regionNorth,
            south: regionSouth,
            east: regionEast,
            west: regionWest
          }
        };

        try {
          Utils.log('info', `Creating region ${currentRegionName} at (${centerLat.toFixed(6)}, ${centerLng.toFixed(6)})`);
          
          // Create region using the same API as "Create Region"
          const result = await window.APIClient.region.createRegion(regionData);
          
          if (result.success) {
            createdRegions.push({
              name: currentRegionName,
              lat: centerLat,
              lng: centerLng,
              bounds: regionData.bounds
            });
            Utils.log('info', `✅ Successfully created region: ${currentRegionName}`);
          } else {
            Utils.log('error', `❌ Failed to create region: ${currentRegionName}`, result);
          }

        } catch (error) {
          Utils.log('error', `Error creating region ${currentRegionName}:`, error);
        }

        regionId++;
      }
      if (regionId > this.selectedRegionCount) break;
    }

    return createdRegions;
  },
  
  /**
   * Create regions from a path geometry
   * @param {string} regionName - Base name for regions
   * @returns {Array} Array of created regions
   */
  async createRegionsFromPath(regionName) {
    const path = window.MapManager.currentPath;
    const pathLatLngs = path.getLatLngs();
    
    if (pathLatLngs.length < 2) {
      throw new Error('Path must have at least 2 points');
    }

    Utils.log('info', `Path has ${pathLatLngs.length} points`);
    Utils.showNotification(`Creating ${this.selectedRegionCount} regions along path...`, 'info');

    // Calculate total path distance
    let totalDistance = 0;
    for (let i = 0; i < pathLatLngs.length - 1; i++) {
      totalDistance += pathLatLngs[i].distanceTo(pathLatLngs[i + 1]);
    }
    
    Utils.log('info', `Total path distance: ${(totalDistance / 1000).toFixed(2)} km`);

    // Calculate equidistant spacing
    // For N regions, we want N+1 segments, so regions are evenly distributed
    const segmentDistance = totalDistance / (this.selectedRegionCount + 1);
    Utils.log('info', `Distance between region centers: ${(segmentDistance / 1000).toFixed(2)} km`);

    const createdRegions = [];
    let regionId = 1;

    // Create regions along the path at equidistant intervals
    for (let regionIndex = 0; regionIndex < this.selectedRegionCount; regionIndex++) {
      // Calculate distance for this region (1st region at 1*segmentDistance, 2nd at 2*segmentDistance, etc.)
      const currentDistance = segmentDistance * (regionIndex + 1);
      
      // Find the point along the path at currentDistance
      const pathPoint = this.getPointAlongPath(pathLatLngs, currentDistance);
      
      if (!pathPoint) {
        Utils.log('warn', `Could not find point along path for region ${regionId}`);
        break;
      }

      // Create region name
      const currentRegionName = `${regionName}_${regionId}`;

      // Calculate a bounding box around the point (approximate 1km radius)
      const buffer = 0.009; // Approximately 1km in degrees (varies by latitude)
      
      const regionData = {
        region_name: currentRegionName,
        coordinates: {
          lat: pathPoint.lat,
          lng: pathPoint.lng
        },
        place_name: currentRegionName,
        ndvi_enabled: false,
        created_at: new Date().toISOString(),
        bounds: {
          north: pathPoint.lat + buffer,
          south: pathPoint.lat - buffer,
          east: pathPoint.lng + buffer,
          west: pathPoint.lng - buffer
        }
      };

      try {
        Utils.log('info', `Creating region ${currentRegionName} at (${pathPoint.lat.toFixed(6)}, ${pathPoint.lng.toFixed(6)}) - Distance: ${(currentDistance / 1000).toFixed(2)} km`);
        
        // Create region using the same API as "Create Region"
        const result = await window.APIClient.region.createRegion(regionData);
        
        if (result.success) {
          createdRegions.push({
            name: currentRegionName,
            lat: pathPoint.lat,
            lng: pathPoint.lng,
            bounds: regionData.bounds
          });
          Utils.log('info', `✅ Successfully created region: ${currentRegionName}`);
        } else {
          Utils.log('error', `❌ Failed to create region: ${currentRegionName}`, result);
        }

      } catch (error) {
        Utils.log('error', `Error creating region ${currentRegionName}:`, error);
      }

      regionId++;
    }

    return createdRegions;
  },
  
  /**
   * Get a point along the path at a specific distance
   * @param {Array} pathLatLngs - Array of path points
   * @param {number} targetDistance - Distance along path in meters
   * @returns {Object|null} Point with lat/lng properties or null if not found
   */
  getPointAlongPath(pathLatLngs, targetDistance) {
    let currentDistance = 0;
    
    for (let i = 0; i < pathLatLngs.length - 1; i++) {
      const segmentStart = pathLatLngs[i];
      const segmentEnd = pathLatLngs[i + 1];
      const segmentLength = segmentStart.distanceTo(segmentEnd);
      
      if (currentDistance + segmentLength >= targetDistance) {
        // The target point is within this segment
        const distanceIntoSegment = targetDistance - currentDistance;
        const ratio = distanceIntoSegment / segmentLength;
        
        // Interpolate between segment start and end
        const lat = segmentStart.lat + (segmentEnd.lat - segmentStart.lat) * ratio;
        const lng = segmentStart.lng + (segmentEnd.lng - segmentStart.lng) * ratio;
        
        return { lat, lng };
      }
      
      currentDistance += segmentLength;
    }
    
    // If we get here, the target distance is beyond the path end
    // Return the last point
    const lastPoint = pathLatLngs[pathLatLngs.length - 1];
    return { lat: lastPoint.lat, lng: lastPoint.lng };
  },

  /**
   * Calculate optimal grid dimensions for the given number of regions
   * @param {number} regionCount - Number of regions to create
   * @returns {Object} Grid dimensions {rows, cols}
   */
  calculateGridSize(regionCount) {
    // Find the best rectangular grid that accommodates regionCount
    let bestRows = 1;
    let bestCols = regionCount;
    let bestRatio = Math.abs(bestCols / bestRows - 1); // Prefer square-ish grids

    for (let rows = 1; rows <= regionCount; rows++) {
      const cols = Math.ceil(regionCount / rows);
      const ratio = Math.abs(cols / rows - 1);
      
      if (ratio < bestRatio) {
        bestRows = rows;
        bestCols = cols;
        bestRatio = ratio;
      }
    }

    return { rows: bestRows, cols: bestCols };
  },
  
  /**
   * Get the current modal state
   * @returns {Object} Current modal state
   */
  getState() {
    return {
      isOpen: this.isModalOpen(),
      selectedRegionCount: this.selectedRegionCount,
      regionName: document.getElementById('box-laz-region-name')?.value || ''
    };
  }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  GetBoxLazModal.init();
});
