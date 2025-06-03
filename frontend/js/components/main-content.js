/**
 * Main Content Component
 */
window.componentManager.register('main-content', (props = {}) => {
    const { 
        title = 'Terrain Analysis Results',
        subtitle = 'Select a region and click on a processing button to generate terrain analysis'
    } = props;
    
    return `
        <div id="main" class="flex-1 p-6 bg-[#141414] overflow-y-auto">
            <div class="mb-6">
                <h1 class="text-white text-2xl font-bold">${title}</h1>
                <p class="text-[#ababab] text-sm mt-2">${subtitle}</p>
            </div>
            
            <!-- Map will be inserted here -->
            <div id="map-container"></div>
            
            <!-- Galleries will be inserted here -->
            <div id="gallery-container"></div>
            <div id="satellite-gallery-container"></div>
        </div>
    `;
}, {
    onRender: async (element) => {
        // Render map component
        await window.componentManager.render('map', '#map-container');
        
        // Render gallery components
        await window.componentManager.render('gallery', '#gallery-container');
        await window.componentManager.render('satellite-gallery', '#satellite-gallery-container');
    },
    dependencies: ['map', 'gallery', 'satellite-gallery']
});
