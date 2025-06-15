/**
 * Gallery Component for Processing Results
 */
window.componentManager.register('gallery', (props = {}) => {
    const { title = 'Processing Results', items = null } = props;
    
    const defaultItems = [
        { id: 'laz_to_dem', label: 'DEM', target: 'laz_to_dem' },
        { id: 'dtm', label: 'DTM', target: 'dtm' },
        { id: 'dsm', label: 'DSM', target: 'dsm' },
        { id: 'chm', label: 'CHM', target: 'chm' },
        { id: 'hillshade', label: 'Hillshade (Std)', target: 'hillshade' },
        { id: 'hillshade_315_45_08', label: 'Hillshade 315°', target: 'hillshade_315_45_08' },
        { id: 'hillshade_225_45_08', label: 'Hillshade 225°', target: 'hillshade_225_45_08' },
        { id: 'slope', label: 'Slope', target: 'slope' },
        { id: 'aspect', label: 'Aspect', target: 'aspect' },
        { id: 'tpi', label: 'TPI', target: 'tpi' },
        { id: 'roughness', label: 'Roughness', target: 'roughness' },
        { id: 'sky_view_factor', label: 'Sky View Factor', target: 'sky_view_factor' }
    ];
    
    const galleryItems = items || defaultItems;
    
    return `
        <div class="mb-4">
            <h2 class="text-white text-lg font-semibold mb-4">${title}</h2>
            <div id="gallery" class="flex gap-4 overflow-x-auto pb-4">
                ${galleryItems.map(item => generateGalleryItem(item)).join('')}
            </div>
        </div>
    `;
});

/**
 * Satellite Gallery Component
 */
window.componentManager.register('satellite-gallery', (props = {}) => {
    const { title = 'Downloaded Satellite Images' } = props;
    
    return `
        <div class="mb-4">
            <h2 class="text-white text-lg font-semibold mb-4">${title}</h2>
            <div id="satellite-gallery" class="flex gap-4 overflow-x-auto pb-4">
                <!-- Downloaded satellite images will be displayed here -->
            </div>
        </div>
    `;
});

function generateGalleryItem(item) {
    return `
        <div class="gallery-item flex-shrink-0 w-64 h-48 bg-[#1a1a1a] border border-[#303030] rounded-lg flex flex-col hover:border-[#404040] transition-colors" id="cell-${item.id}">
            <div class="flex-1 flex items-center justify-center">
                <div class="text-white text-lg font-medium">${item.label}</div>
            </div>
        </div>
    `;
}

/**
 * Raster Overlay Gallery Component
 */
window.componentManager.register('raster-overlay-gallery', (props = {}) => {
    const { title = 'Raster Overlays' } = props;
    return `
        <div class="mb-4">
            <h2 class="text-white text-lg font-semibold mb-4">${title}</h2>
            <div id="raster-overlay-gallery" class="flex gap-4 overflow-x-auto pb-4"></div>
        </div>
    `;
});
