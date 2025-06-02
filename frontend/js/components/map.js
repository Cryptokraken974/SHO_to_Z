/**
 * Map Component
 */
window.componentManager.register('map', (props = {}) => {
    const { height = '800px', showCoordinates = true } = props;
    
    return `
        <div class="mb-6 relative">
            <div id="map" class="w-full h-[${height}] bg-[#1a1a1a] border border-[#303030] rounded-lg"></div>
            ${showCoordinates ? `
                <div id="coordinate-display" class="absolute bottom-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded font-mono pointer-events-none z-[1000]">
                    Lat: ---, Lng: ---
                </div>
            ` : ''}
        </div>
    `;
}, {
    onRender: (element, props) => {
        // Initialize map if not already initialized
        if (typeof window.mapManager !== 'undefined') {
            // Map will be initialized by the existing map.js
            console.log('Map component rendered');
        }
    }
});
