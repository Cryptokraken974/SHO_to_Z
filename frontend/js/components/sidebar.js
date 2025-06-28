/**
 * Sidebar Component with Accordion Sections
 */
window.componentManager.register('sidebar', (props = {}) => {
    const { selectedRegion = 'No region selected' } = props;
    
    return `
        <div id="sidebar" class="bg-[#1a1a1a] border-r border-[#303030] w-64 p-6 flex flex-col overflow-y-auto">
            <!-- LAZ File Selection Section -->
            <div class="accordion-section mb-6">
                <div class="accordion-header bg-[#303030] hover:bg-[#404040] cursor-pointer p-3 rounded-lg transition-colors" id="region-select-accordion">
                    <h3 class="text-white font-semibold flex justify-between items-center m-0">
                        Select Region
                        <span class="accordion-arrow text-sm transition-transform">▼</span>
                    </h3>
                </div>
                <div class="accordion-content bg-[#262626] rounded-lg mt-2 p-3" id="region-select-content">
                    <div class="selected-file space-y-2">
                        <div id="selected-region-name" class="text-[#666] text-sm">${selectedRegion}</div>
                    </div>
                </div>
            </div>

            <!-- Region Section -->
            <div class="accordion-section mb-6">
                <div class="accordion-header bg-[#303030] hover:bg-[#404040] cursor-pointer p-3 rounded-lg transition-colors" id="region-accordion">
                    <h3 class="text-white font-semibold flex justify-between items-center m-0">
                        Region
                        <span class="accordion-arrow text-sm transition-transform">▼</span>
                    </h3>
                </div>
                <div class="accordion-content bg-[#262626] rounded-lg mt-2 p-3" id="region-content">
                    <div class="space-y-3">
                        <!-- Coordinate Input Fields -->
                        <div class="grid grid-cols-2 gap-2">
                            <div>
                                <label for="lat-input" class="block text-xs text-[#ababab] mb-1">Latitude</label>
                                <input type="text" id="lat-input" placeholder="Click map to capture" class="w-full bg-[#1a1a1a] border border-[#404040] rounded-lg px-3 py-2 text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#00bfff] font-mono" readonly>
                            </div>
                            <div>
                                <label for="lng-input" class="block text-xs text-[#ababab] mb-1">Longitude</label>
                                <input type="text" id="lng-input" placeholder="Click map to capture" class="w-full bg-[#1a1a1a] border border-[#404040] rounded-lg px-3 py-2 text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#00bfff] font-mono" readonly>
                            </div>
                        </div>
                        
                        <!-- Region Name Field -->
                        <div class="mt-2">
                            <label for="region-name-input" class="block text-xs text-[#ababab] mb-1">Region Name</label>
                            <input type="text" id="region-name-input" placeholder="Auto-generated from coordinates" class="w-full bg-[#1a1a1a] border border-[#404040] rounded-lg px-3 py-2 text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#00bfff] font-mono">
                        </div>
                        
                        <!-- Save Current Location button will be added here by SavedPlaces system -->
                    </div>
                </div>
            </div>

            <!-- Get Data Section -->
            <div class="accordion-section mb-6">
                <div class="accordion-header bg-[#303030] hover:bg-[#404040] cursor-pointer p-3 rounded-lg transition-colors" id="get-data-accordion">
                    <h3 class="text-white font-semibold flex justify-between items-center m-0">
                        Get Data
                        <span class="accordion-arrow text-sm transition-transform">▼</span>
                    </h3>
                </div>
                <div class="accordion-content bg-[#262626] rounded-lg mt-2 p-3" id="get-data-content">
                    <div class="space-y-3">
                        <!-- Sentinel-2 Test Button -->
                        <button id="test-sentinel2-btn" class="w-full bg-[#6c757d] hover:bg-[#5a6268] text-white px-4 py-3 rounded-lg font-medium transition-colors mt-2 text-sm">🧪 Get Sentinel-2 Images</button>
                        
                        <!-- Get Elevation Data Button -->
                        <button id="get-lidar-btn" class="w-full bg-[#6c5ce7] hover:bg-[#5a4fcf] text-white px-4 py-3 rounded-lg font-medium transition-colors mt-2">🏔️ Get Elevation Data</button>
                        
                        <!-- Get Data Button (Combined) -->
                        <button id="get-data-btn" class="w-full bg-[#28a745] hover:bg-[#218838] text-white px-4 py-3 rounded-lg font-medium transition-colors mt-2">📊 Get Data (Elevation + Satellite)</button>
                    </div>
                </div>
            </div>

            <!-- Go to Section -->
            <div class="accordion-section mb-6">
                <div class="accordion-header bg-[#303030] hover:bg-[#404040] cursor-pointer p-3 rounded-lg transition-colors" id="go-to-accordion">
                    <h3 class="text-white font-semibold flex justify-between items-center m-0">
                        Go to
                        <span class="accordion-arrow text-sm transition-transform">▼</span>
                    </h3>
                </div>
                <div class="accordion-content bg-[#262626] rounded-lg mt-2 p-3" id="go-to-content">
                    <div class="space-y-3">
                        <!-- Coordinate Go-to Fields -->
                        <div class="grid grid-cols-2 gap-2">
                            <div>
                                <label for="goto-lat-input" class="block text-xs text-[#ababab] mb-1">Latitude</label>
                                <input type="number" id="goto-lat-input" placeholder="Enter latitude" class="w-full bg-[#1a1a1a] border border-[#404040] rounded-lg px-3 py-2 text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#00bfff] font-mono" step="any">
                            </div>
                            <div>
                                <label for="goto-lng-input" class="block text-xs text-[#ababab] mb-1">Longitude</label>
                                <input type="number" id="goto-lng-input" placeholder="Enter longitude" class="w-full bg-[#1a1a1a] border border-[#404040] rounded-lg px-3 py-2 text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#00bfff] font-mono" step="any">
                            </div>
                        </div>
                        
                        <!-- Go Button -->
                        <button id="go-to-coordinates-btn" class="w-full bg-[#17a2b8] hover:bg-[#138496] text-white px-4 py-3 rounded-lg font-medium transition-colors">🎯 Go to Coordinates</button>
                        
                        <!-- Preset Locations -->
                        <div class="mt-4">
                            <label class="block text-xs text-[#ababab] mb-2">Quick Locations</label>
                            <div class="space-y-2">
                                <button class="preset-location w-full bg-[#495057] hover:bg-[#6c757d] text-white px-3 py-2 rounded text-sm transition-colors" data-lat="40.7128" data-lng="-74.0060">📍 New York City</button>
                                <button class="preset-location w-full bg-[#495057] hover:bg-[#6c757d] text-white px-3 py-2 rounded text-sm transition-colors" data-lat="34.0522" data-lng="-118.2437">📍 Los Angeles</button>
                                <button class="preset-location w-full bg-[#495057] hover:bg-[#6c757d] text-white px-3 py-2 rounded text-sm transition-colors" data-lat="51.5074" data-lng="-0.1278">📍 London</button>
                                <button class="preset-location w-full bg-[#495057] hover:bg-[#6c757d] text-white px-3 py-2 rounded text-sm transition-colors" data-lat="35.6762" data-lng="139.6503">📍 Tokyo</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}, {
    onRender: (element) => {
        // Set up accordion functionality
        setupAccordions(element);
    }
});

function setupAccordions(container) {
    const accordions = container.querySelectorAll('.accordion-header');
    accordions.forEach(header => {
        header.addEventListener('click', () => {
            const content = header.nextElementSibling;
            const arrow = header.querySelector('.accordion-arrow');
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                arrow.style.transform = 'rotate(180deg)';
            } else {
                content.style.display = 'none';
                arrow.style.transform = 'rotate(0deg)';
            }
        });
    });
}
