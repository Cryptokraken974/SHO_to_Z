class SatelliteOverlayGallery {
    constructor(containerId = 'satellite-gallery', options = {}) {
        this.containerId = containerId;
        this.options = Object.assign({
            bands: ['RED_B04', 'NIR_B08', 'NDVI'],
            onAddToMap: (regionBand, bandType) => this.defaultAddToMap(regionBand, bandType)
        }, options);

        this.gallery = new window.ModularGallery(this.containerId, {
            showAddToMap: true,
            allowSelection: false,
            onAddToMap: (id) => this.handleAddToMap(id)
        });

        this.regionName = null;
        this.items = [];
    }

    async loadImages(regionName) {
        this.regionName = regionName;
        if (!regionName) {
            this.gallery.clear();
            return;
        }

        this.gallery.showLoading();
        const items = [];

        let apiRegionName = regionName;
        if (!regionName.startsWith('region_')) {
            apiRegionName = `region_${regionName.replace(/\./g, '_')}`;
        }

        for (const band of this.options.bands) {
            const regionBand = `${apiRegionName}_${band}`;
            try {
                const data = await satellite().getSentinel2Overlay(regionBand);
                if (data && data.image_data) {
                    const title = this.getBandDisplayName(band);
                    items.push({
                        id: regionBand,
                        imageUrl: `data:image/png;base64,${data.image_data}`,
                        title: title,
                        subtitle: regionName,
                        status: 'ready',
                        bandType: title
                    });
                }
            } catch (e) {
                // ignore missing images
            }
        }

        this.showImages(items);
    }

    showImages(items) {
        this.items = items || [];
        if (!items || items.length === 0) {
            this.gallery.clear();
        } else {
            this.gallery.setItems(items);
        }
    }

    handleAddToMap(itemId) {
        const item = this.items.find(i => i.id === itemId);
        const bandType = item ? item.bandType : '';
        if (typeof this.options.onAddToMap === 'function') {
            this.options.onAddToMap(itemId, bandType);
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
}

window.SatelliteOverlayGallery = SatelliteOverlayGallery;
