/**
 * Sidebar Component with Accordion Sections
 */
window.componentManager.register('sidebar', (props = {}) => {
    const { selectedRegion = 'No region selected' } = props;
    
    return `
        <div id="sidebar" class="bg-[#1a1a1a] border-r border-[#303030] w-64 p-6 flex flex-col overflow-y-auto">
            <!-- LAZ File Selection Section -->
            <div class="accordion-section mb-6">
                <div class="accordion-header bg-[#303030] hover:bg-[#404040] cursor-pointer p-3 rounded-lg transition-colors" id="region-accordion">
                    <h3 class="text-white font-semibold flex justify-between items-center m-0">
                        Select Region
                        <span class="accordion-arrow text-sm transition-transform">▼</span>
                    </h3>
                </div>
                <div class="accordion-content bg-[#262626] rounded-lg mt-2 p-3" id="region-content">
                    <div class="selected-file space-y-2">
                        <div id="selected-region-name" class="text-[#666] text-sm">${selectedRegion}</div>
                        <button id="browse-regions-btn" class="bg-[#007bff] hover:bg-[#0056b3] text-white font-semibold py-2 px-4 rounded-lg shadow-md transition-colors duration-150 ease-in-out w-full text-sm tooltip" data-tooltip="Browse and select a region to process or visualize">
                            Select Region
                        </button>
                    </div>
                </div>
            </div>

            <!-- Test Section -->
            <div class="accordion-section mb-6">
                <div class="accordion-header bg-[#303030] hover:bg-[#404040] cursor-pointer p-3 rounded-lg transition-colors" id="test-accordion">
                    <h3 class="text-white font-semibold flex justify-between items-center m-0">
                        Test
                        <span class="accordion-arrow text-sm transition-transform">▼</span>
                    </h3>
                </div>
                <div class="accordion-content bg-[#262626] rounded-lg mt-2 p-3" id="test-content">
                    <div class="space-y-3">
                        <!-- Test Overlay Button -->
                        <button id="test-overlay-btn" class="w-full bg-[#ff6b35] hover:bg-[#e55a2e] text-white px-4 py-3 rounded-lg font-medium transition-colors">🧪 Test Overlay</button>
                        
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
                        
                        <!-- Sentinel-2 Test Button -->
                        <button id="test-sentinel2-btn" class="w-full bg-[#dc3545] hover:bg-[#c82333] text-white px-4 py-3 rounded-lg font-medium transition-colors mt-2">🛰️ Test: Sentinel-2 Images</button>
                        
                        <!-- Get Elevation Data Button -->
                        <button id="get-lidar-btn" class="w-full bg-[#6c5ce7] hover:bg-[#5a4fcf] text-white px-4 py-3 rounded-lg font-medium transition-colors mt-2">🏔️ Get Elevation Data</button>
                    </div>
                </div>
            </div>

            <!-- Processing Steps -->
            <div class="accordion-section flex-1">
                <div class="accordion-header bg-[#303030] hover:bg-[#404040] cursor-pointer p-3 rounded-lg transition-colors" id="processing-accordion">
                    <h3 class="text-white font-semibold flex justify-between items-center m-0">
                        Processing Steps
                        <span class="accordion-arrow text-sm transition-transform">▼</span>
                    </h3>
                </div>
                <div class="accordion-content bg-[#262626] rounded-lg mt-2 p-3" id="processing-content">
                    <div class="space-y-2" id="processing-steps-container">
                        ${generateProcessingSteps()}
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

function generateProcessingSteps() {
    const steps = [
        { id: 'dem', target: 'laz_to_dem', label: 'DEM', checked: false },
        { id: 'dsm', target: 'dsm', label: 'DSM', checked: false },
        { id: 'chm', target: 'chm', label: 'CHM', checked: false },
        { id: 'dtm', target: 'dtm', label: 'DTM', checked: true },
        { id: 'hillshade', target: 'hillshade', label: 'Hillshade (Standard)', checked: true },
        { id: 'hillshade315', target: 'hillshade_315_45_08', label: 'Hillshade 315° (0.8z)', checked: false },
        { id: 'hillshade225', target: 'hillshade_225_45_08', label: 'Hillshade 225° (0.8z)', checked: false },
        { id: 'slope', target: 'slope', label: 'Slope', checked: true },
        { id: 'aspect', target: 'aspect', label: 'Aspect', checked: false },
        { id: 'color_relief', target: 'color_relief', label: 'Color Relief', checked: true },
        { id: 'tri', target: 'tri', label: 'TRI', checked: false },
        { id: 'tpi', target: 'tpi', label: 'TPI', checked: false },
        { id: 'roughness', target: 'roughness', label: 'Roughness', checked: false }
    ];

    return steps.map(step => `
        <div>
            <input type="checkbox" id="${step.id}-checkbox" data-target="${step.target}" class="form-checkbox h-5 w-5 text-blue-600 bg-gray-800 border-gray-600 rounded focus:ring-blue-500" ${step.checked ? 'checked' : ''}>
            <label for="${step.id}-checkbox" class="ml-2 text-white">${step.label}</label>
        </div>
    `).join('');
}

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
