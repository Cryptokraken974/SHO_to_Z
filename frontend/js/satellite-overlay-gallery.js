class SatelliteOverlayGallery {
    constructor(containerId = 'satellite-gallery', options = {}) {
        this.containerId = containerId;
        this.options = Object.assign({
            bands: ['NDVI'], // Only load NDVI, not individual B04/B08 bands
            onAddToMap: (regionBand, bandType) => this.defaultAddToMap(regionBand, bandType)
        }, options);

        this.gallery = new window.ModularGallery(this.containerId, {
            showAddToMap: true,
            allowSelection: false,
            onAddToMap: (id) => this.handleAddToMap(id),
            getOverlayState: (id) => this.isOverlayActive(id)
        });

        this.regionName = null;
        this.items = [];
        
        // Register for overlay state changes
        this.overlayStateCallback = (overlayId, isActive) => {
            // Check if this overlay is a Sentinel-2 overlay (correct key format)
            if (overlayId.startsWith('SENTINEL2_')) {
                // Extract regionBand from overlay ID (e.g., SENTINEL2_region_xxx_RED_B04 -> region_xxx_RED_B04)
                const regionBand = overlayId.replace('SENTINEL2_', '');
                // Find the item with this regionBand as ID
                const item = this.items.find(item => item.id === regionBand);
                if (item) {
                    this.updateButtonState(item.id, isActive);
                }
            }
        };
        
        if (window.OverlayManager) {
            window.OverlayManager.registerOverlayStateCallback(this.overlayStateCallback);
        }
    }

    async loadImages(regionName) {
        this.regionName = regionName;
        if (!regionName) {
            this.gallery.clear();
            return;
        }

        console.log(`🛰️ SatelliteOverlayGallery: Loading images for region: ${regionName}`);
        this.gallery.showLoading();
        const items = [];

        let apiRegionName = regionName;
        // Only add region_ prefix for coordinate-based regions (contain dots)
        if (!regionName.startsWith('region_') && regionName.includes('.')) {
            apiRegionName = `region_${regionName.replace(/\./g, '_')}`;
        }
        console.log(`🛰️ API region name: ${apiRegionName}`);

        for (const band of this.options.bands) {
            const regionBand = `${apiRegionName}_${band}`;
            console.log(`🛰️ Loading band: ${band}, regionBand: ${regionBand}`);
            try {
                const data = await satellite().getSentinel2Overlay(regionBand);
                if (data && data.image_data) {
                    console.log(`✅ Successfully loaded band ${band}`);
                    const title = this.getBandDisplayName(band);
                    items.push({
                        id: regionBand,
                        imageUrl: `data:image/png;base64,${data.image_data}`,
                        title: title,
                        subtitle: regionName,
                        status: 'ready',
                        bandType: band // Use the raw band name, not the display name
                    });
                } else {
                    console.warn(`❌ No image data for band ${band}`);
                }
            } catch (e) {
                console.error(`Failed to load Sentinel-2 band ${band} for region ${regionBand}:`, e);
                // ignore missing images but log the error
            }
        }

        console.log(`🛰️ Loaded ${items.length} satellite images`);
        this.showImages(items);
    }

    showImages(items) {
        console.log(`🛰️ showImages called with ${items ? items.length : 0} items:`, items);
        this.items = items || [];
        if (!items || items.length === 0) {
            console.log('🛰️ Clearing gallery - no items');
            this.gallery.clear();
        } else {
            console.log('🛰️ Setting gallery items');
            this.gallery.setItems(items);
        }
    }

    handleAddToMap(itemId) {
        const item = this.items.find(i => i.id === itemId);
        if (!item) return;
        
        const bandType = item.bandType; // This is now the raw band name
        
        // Check current overlay state
        const isCurrentlyActive = this.isOverlayActive(itemId);
        
        if (isCurrentlyActive) {
            // Remove overlay
            this.removeOverlay(itemId, bandType);
        } else {
            // Add overlay
            if (typeof this.options.onAddToMap === 'function') {
                this.options.onAddToMap(itemId, bandType);
            }
        }
        
        // Short delay to allow overlay state to update, then refresh button
        setTimeout(() => {
            this.gallery.updateItemOverlayState(itemId, !isCurrentlyActive);
        }, 100);
    }

    /**
     * Check if a satellite overlay is currently active on the map
     * @param {string} itemId - Item ID to check (typically regionBand format)
     * @returns {boolean} True if overlay is active
     */
    isOverlayActive(itemId) {
        if (!window.OverlayManager) return false;
        
        // Check for Sentinel-2 overlay using the correct key format (SENTINEL2_ prefix)
        const overlayKey = `SENTINEL2_${itemId}`;
        return overlayKey in window.OverlayManager.mapOverlays;
    }

    /**
     * Remove satellite overlay from map
     * @param {string} itemId - Item ID (regionBand format)
     * @param {string} bandType - Band type for display in notification
     */
    removeOverlay(itemId, bandType) {
        if (!window.OverlayManager) return;
        
        // Use the correct Sentinel-2 overlay key format
        const overlayKey = `SENTINEL2_${itemId}`;
        window.OverlayManager.removeOverlay(overlayKey);
        
        // Show notification
        const displayName = this.getBandDisplayName(bandType);
        if (window.Utils) {
            window.Utils.showNotification(`Removed ${displayName} overlay from map`, 'success');
        }
    }

    async defaultAddToMap(regionBand, bandType) {
        if (window.UIManager?.addSentinel2OverlayToMap) {
            await window.UIManager.addSentinel2OverlayToMap(regionBand, bandType);
        }
    }

    getBandDisplayName(band) {
        if (band === 'NDVI') return 'NDVI';
        if (band.includes('NIR_B08')) return 'NIR (B08)';
        if (band.includes('RED_B04')) return 'Red (B04)';
        return band;
    }

    /**
     * Refresh button states for all items in the gallery
     * Call this method when overlay states change externally
     */
    refreshButtonStates() {
        this.gallery.updateOverlayButtonStates();
    }

    /**
     * Update button state for a specific item
     * @param {string} itemId - Item ID
     * @param {boolean} isActive - Whether overlay is active
     */
    updateButtonState(itemId, isActive) {
        this.gallery.updateItemOverlayState(itemId, isActive);
    }
    
    /**
     * Refresh the gallery for the current region
     * This reloads images without needing to know the region name
     */
    async refresh() {
        console.log('🔄 SatelliteOverlayGallery.refresh() called');
        if (this.regionName) {
            console.log(`🔄 Refreshing gallery for region: ${this.regionName}`);
            // Show loading state immediately
            this.gallery.showLoading();
            // Wait a moment to ensure any recent processing has completed
            await new Promise(resolve => setTimeout(resolve, 1000));
            await this.loadImages(this.regionName);
        } else {
            console.log('🔄 No region name stored, cannot refresh');
        }
    }
}

window.SatelliteOverlayGallery = SatelliteOverlayGallery;
