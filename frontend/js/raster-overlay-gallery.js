class RasterOverlayGallery {
    constructor(containerId = 'raster-overlay-gallery', options = {}) {
        this.containerId = containerId;
        this.options = Object.assign({
            onAddToMap: (type) => this.defaultAddToMap(type)
        }, options);

        // Create underlying ModularGallery with overlay state tracking
        this.gallery = new window.ModularGallery(this.containerId, {
            showAddToMap: true,
            allowSelection: false,
            onAddToMap: (id) => this.handleAddToMap(id),
            getOverlayState: (id) => this.isOverlayActive(id)
        });

        this.regionName = null;
        
        // Register for overlay state changes
        this.overlayStateCallback = (overlayId, isActive) => {
            // Check if this overlay belongs to our region
            if (this.regionName && overlayId.includes(`LIDAR_RASTER_${this.regionName}_`)) {
                const processingType = overlayId.replace(`LIDAR_RASTER_${this.regionName}_`, '');
                this.updateButtonState(processingType, isActive);
            }
        };
        
        if (window.OverlayManager) {
            window.OverlayManager.registerOverlayStateCallback(this.overlayStateCallback);
        }
    }

    init() {
        console.log('RasterOverlayGallery.init() called');
        // Initialize the gallery - this method is expected by the UI system
        // The actual gallery initialization is done in the constructor via ModularGallery
        // This method exists to satisfy the UI initialization requirements
        return this;
    }

    async loadRasters(regionName) {
        console.log('RasterOverlayGallery.loadRasters called with region:', regionName);
        this.regionName = regionName;
        if (!regionName) {
            console.log('No region name provided, clearing gallery');
            this.gallery.clear();
            return;
        }

        console.log('Showing loading state for gallery');
        this.gallery.showLoading();
        const items = [];
        
        try {
            // Get available PNG files for this region dynamically
            console.log('Fetching PNG files for region:', regionName);
            const pngData = await regions().getRegionPngFiles(regionName);
            console.log('PNG data received:', pngData);
            
            if (pngData && pngData.png_files && pngData.png_files.length > 0) {
                console.log(`Found ${pngData.png_files.length} PNG files for region`);
                // Process each available PNG file
                for (const pngFile of pngData.png_files) {
                    console.log('Processing PNG file:', pngFile);
                    try {
                        const processingType = pngFile.processing_type;
                        if (!processingType) {
                            console.warn('PNG file missing processing_type:', pngFile);
                            continue;
                        }
                        
                        // Get overlay data for this processing type
                        console.log('Fetching overlay data for processing type:', processingType);
                        const data = await overlays().getRasterOverlayData(regionName, processingType);
                        console.log('Overlay data received for', processingType, ':', data ? 'SUCCESS' : 'FAILED');
                        if (data && data.image_data) {
                            const item = {
                                id: processingType,
                                imageUrl: `data:image/png;base64,${data.image_data}`,
                                title: pngFile.display_name || this.getProcessingDisplayName(processingType),
                                subtitle: `${pngFile.file_size_mb} MB`,
                                status: 'ready'
                            };
                            console.log('Adding item to gallery:', item.title);
                            items.push(item);
                        }
                    } catch (err) {
                        console.warn('Failed to load overlay data for', pngFile.processing_type, ':', err);
                        // Ignore missing or failed overlay data for individual files
                    }
                }
            } else {
                console.log('No PNG files found for region or empty response');
            }
        } catch (error) {
            console.error('Failed to load PNG files for region:', error);
            // Fallback to empty list
        }
        
        console.log(`Finished loading rasters, found ${items.length} items`);
        this.showRasters(items);
    }

    showRasters(items) {
        console.log('showRasters called with items:', items);
        if (!items || items.length === 0) {
            console.log('No items to show, clearing gallery');
            this.gallery.clear();
        } else {
            console.log(`Setting ${items.length} items in gallery`);
            this.gallery.setItems(items);
        }
    }

    handleAddToMap(itemId) {
        const processingType = itemId;
        
        // Check current overlay state
        const isCurrentlyActive = this.isOverlayActive(processingType);
        
        if (isCurrentlyActive) {
            // Remove overlay
            this.removeOverlay(processingType);
        } else {
            // Add overlay
            if (typeof this.options.onAddToMap === 'function') {
                this.options.onAddToMap(processingType);
            }
        }
        
        // Short delay to allow overlay state to update, then refresh button
        setTimeout(() => {
            this.gallery.updateItemOverlayState(itemId, !isCurrentlyActive);
        }, 100);
    }

    /**
     * Check if an overlay is currently active on the map
     * @param {string} processingType - Processing type to check
     * @returns {boolean} True if overlay is active
     */
    isOverlayActive(processingType) {
        if (!this.regionName || !window.OverlayManager) return false;
        
        // Check for overlay using the expected key format
        const overlayKey = `LIDAR_RASTER_${this.regionName}_${processingType}`;
        return overlayKey in window.OverlayManager.mapOverlays;
    }

    /**
     * Remove overlay from map
     * @param {string} processingType - Processing type to remove
     */
    removeOverlay(processingType) {
        if (!this.regionName || !window.OverlayManager) return;
        
        const overlayKey = `LIDAR_RASTER_${this.regionName}_${processingType}`;
        window.OverlayManager.removeOverlay(overlayKey);
        
        // Show notification
        const displayName = this.getProcessingDisplayName(processingType);
        if (window.Utils) {
            window.Utils.showNotification(`Removed ${displayName} overlay from map`, 'success');
        }
    }

    async defaultAddToMap(processingType) {
        if (window.UIManager?.handleProcessingResultsAddToMap) {
            const dummyBtn = window.jQuery ? window.jQuery('<button></button>') : { data: () => this.regionName };
            if (dummyBtn.data) dummyBtn.data('region-name', this.regionName);
            window.UIManager.handleProcessingResultsAddToMap(processingType, dummyBtn);
        } else if (window.OverlayManager?.addImageOverlay) {
            try {
                const data = await overlays().getRasterOverlayData(this.regionName, processingType);
                if (data && data.bounds && data.image_data) {
                    const bounds = [[data.bounds.south, data.bounds.west], [data.bounds.north, data.bounds.east]];
                    const imageUrl = `data:image/png;base64,${data.image_data}`;
                    const key = `LIDAR_RASTER_${this.regionName}_${processingType}`;
                    window.OverlayManager.addImageOverlay(key, imageUrl, bounds);
                }
            } catch (e) {
                console.error('Failed to add overlay', e);
            }
        }
    }

    getProcessingDisplayName(type) {
        // Map processing types to user-friendly display names
        const displayNames = {
            'lrm': 'Local Relief Model',
            'sky_view_factor': 'Sky View Factor',
            'slope': 'Slope',
            'aspect': 'Aspect',
            'chm': 'Canopy Height Model',
            'hillshade_rgb': 'Hillshade RGB',
            'tint_overlay': 'Tint Overlay',
            'color_relief': 'Color Relief',
            'slope_relief': 'Slope Relief',
            'boosted_hillshade': 'Boosted Hillshade',
            'hs_red': 'Hillshade Red',
            'hs_green': 'Hillshade Green',
            'hs_blue': 'Hillshade Blue'
        };
        
        return displayNames[type] || type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Refresh button states for all items in the gallery
     * Call this method when overlay states change externally
     */
    refreshButtonStates() {
        this.gallery.updateOverlayButtonStates();
    }

    /**
     * Update button state for a specific processing type
     * @param {string} processingType - Processing type
     * @param {boolean} isActive - Whether overlay is active
     */
    updateButtonState(processingType, isActive) {
        this.gallery.updateItemOverlayState(processingType, isActive);
    }
}

window.RasterOverlayGallery = RasterOverlayGallery;
