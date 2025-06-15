class RasterOverlayGallery {
    constructor(containerId = 'raster-overlay-gallery', options = {}) {
        this.containerId = containerId;
        this.options = Object.assign({
            processingTypes: [
                'hs_red', 'hs_green', 'hs_blue',
                'slope', 'aspect', 'color_relief', 'slope_relief',
                'hillshade_rgb', 'tint_overlay', 'boosted_hillshade'
            ],
            onAddToMap: (type) => this.defaultAddToMap(type)
        }, options);

        // Create underlying ModularGallery
        this.gallery = new window.ModularGallery(this.containerId, {
            showAddToMap: true,
            allowSelection: false,
            onAddToMap: (id) => this.handleAddToMap(id)
        });

        this.regionName = null;
    }

    async loadRasters(regionName) {
        this.regionName = regionName;
        if (!regionName) {
            this.gallery.clear();
            return;
        }

        this.gallery.showLoading();
        const items = [];
        for (const type of this.options.processingTypes) {
            try {
                const data = await overlays().getRasterOverlayData(regionName, type);
                if (data && data.image_data) {
                    items.push({
                        id: type,
                        imageUrl: `data:image/png;base64,${data.image_data}`,
                        title: window.UIManager?.getProcessingDisplayName
                            ? window.UIManager.getProcessingDisplayName(type)
                            : type,
                        subtitle: null,
                        status: 'ready'
                    });
                }
            } catch (err) {
                // ignore missing rasters
            }
        }
        this.showRasters(items);
    }

    showRasters(items) {
        if (!items || items.length === 0) {
            this.gallery.clear();
        } else {
            this.gallery.setItems(items);
        }
    }

    handleAddToMap(itemId) {
        const processingType = itemId;
        if (typeof this.options.onAddToMap === 'function') {
            this.options.onAddToMap(processingType);
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
}

window.RasterOverlayGallery = RasterOverlayGallery;
