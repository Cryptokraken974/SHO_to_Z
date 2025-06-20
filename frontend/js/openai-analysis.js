/**
 * OpenAI Analysis Module
 * Handles the OpenAI Analysis tab functionality including image selection and AI analysis
 */

class OpenAIAnalysis {
    constructor() {
        this.selectedImages = [];
        this.availableImages = [];
        this.currentCategory = 'all';
        this.galleryInstance = null;
        this.selectedRegions = [];
        this.regionGalleries = {};
        this.availableRegions = [];

        this.init();
    }
    
    init() {
        console.log('🤖 Initializing OpenAI Analysis module');
        
        // Initialize immediately without DOM checks or retries
        console.log('✅ Proceeding with immediate initialization');
        this.setupEventListeners();
        this.initializeGalleries();
        this.loadPrompts();
        this.loadRegions();
    }
    
    setupEventListeners() {
        // Analysis controls
        document.getElementById('start-openai-analysis-btn')?.addEventListener('click', () => {
            this.startAnalysis();
        });
        
        document.getElementById('stop-openai-analysis-btn')?.addEventListener('click', () => {
            this.stopAnalysis();
        });

        // Send prompt to OpenAI
        document.getElementById('send-to-openai')?.addEventListener('click', () => {
            this.sendPromptToOpenAI();
        });
        
        // Analysis type change handler
        document.querySelectorAll('input[name="analysis-type"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.updateAnalysisPrompt();
            });
        });

        const addBtn = document.getElementById('add-region-btn');
        const removeBtn = document.getElementById('remove-region-btn');
        const availList = document.getElementById('available-region-list');
        const selList = document.getElementById('selected-region-list');

        addBtn?.addEventListener('click', () => {
            const selected = Array.from(availList.querySelectorAll('li.selected')).map(li => li.dataset.region);
            this.moveToSelected(selected);
        });

        removeBtn?.addEventListener('click', () => {
            const selected = Array.from(selList.querySelectorAll('li.selected')).map(li => li.dataset.region);
            this.moveToAvailable(selected);
        });

        [availList, selList].forEach(list => {
            list?.addEventListener('dragover', e => e.preventDefault());
        });

        availList?.addEventListener('drop', e => {
            e.preventDefault();
            const data = JSON.parse(e.dataTransfer.getData('text/plain'));
            if (data.from === 'selected') this.moveToAvailable([data.region]);
        });

        selList?.addEventListener('drop', e => {
            e.preventDefault();
            const data = JSON.parse(e.dataTransfer.getData('text/plain'));
            if (data.from === 'available') this.moveToSelected([data.region]);
        });
    }
    
    initializeGalleries() {
        // Image selection functionality removed
        console.log('✅ Image selection functionality removed');
    }
    
    // Image selection functionality removed
    
    // Image loading functionality removed
    
    updateAnalysisPrompt() {
        const selectedType = document.querySelector('input[name="analysis-type"]:checked')?.value;
        const promptTextarea = document.getElementById('analysis-prompt');
        
        const prompts = {
            'terrain': 'Analyze the terrain characteristics including elevation patterns, slope gradients, aspect distributions, and topographic features. Identify potential geological hazards and terrain stability.',
            'vegetation': 'Assess vegetation coverage, health, and distribution patterns. Identify different vegetation types, canopy density, and potential areas of vegetation stress or change.',
            'change-detection': 'Compare temporal changes in the landscape including vegetation changes, terrain modifications, and land use alterations. Highlight significant changes and their potential causes.',
            'custom': 'Please describe your custom analysis requirements...'
        };
        
        if (selectedType && prompts[selectedType]) {
            promptTextarea.value = prompts[selectedType];
        }
    }
    
    async startAnalysis() {
        const prompt = document.getElementById('analysis-prompt').value.trim();
        if (!prompt) {
            window.Utils?.showNotification('Please enter an analysis prompt', 'warning');
            return;
        }
        
        console.log('🚀 Starting OpenAI analysis...');
        
        // Update UI
        document.getElementById('start-openai-analysis-btn').classList.add('hidden');
        document.getElementById('stop-openai-analysis-btn').classList.remove('hidden');
        document.getElementById('openai-analysis-status').textContent = 'Analyzing...';
        
        // Show processing state
        document.getElementById('openai-analysis-results').innerHTML = `
            <div class="text-center py-8">
                <div class="text-4xl mb-4">🤖</div>
                <p class="text-white">AI analysis in progress...</p>
                <div class="mt-4">
                    <div class="w-full bg-[#303030] rounded-full h-2">
                        <div class="bg-[#00bfff] h-2 rounded-full animate-pulse" style="width: 30%"></div>
                    </div>
                </div>
            </div>
        `;
        
        try {
            // Here you would implement the actual OpenAI API call
            // For now, we'll simulate the analysis
            await this.simulateAnalysis(prompt);
            
        } catch (error) {
            console.error('Analysis failed:', error);
            this.showAnalysisError(error.message);
        } finally {
            // Reset UI
            document.getElementById('start-openai-analysis-btn').classList.remove('hidden');
            document.getElementById('stop-openai-analysis-btn').classList.add('hidden');
            document.getElementById('openai-analysis-status').textContent = 'Analysis complete';
        }
    }
    
    async simulateAnalysis(prompt) {
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Simulate response
        const response = `
            <div class="space-y-4">
                <div class="bg-[#262626] rounded-lg p-4">
                    <h4 class="text-white font-semibold mb-2">🤖 AI Analysis Results</h4>
                    <p class="text-[#ababab] text-sm mb-3">Analysis based on selected regions</p>
                    
                    <div class="text-white space-y-3">
                        <p><strong>Analysis Prompt:</strong> ${prompt}</p>
                        
                        <div class="border-t border-[#404040] pt-3">
                            <p><strong>Key Findings:</strong></p>
                            <ul class="list-disc list-inside space-y-1 text-[#ababab] mt-2">
                                <li>Terrain shows varied elevation patterns with significant relief</li>
                                <li>Slope analysis indicates areas of potential instability</li>
                                <li>Vegetation coverage appears healthy in most areas</li>
                                <li>Some areas show signs of erosion or land use change</li>
                            </ul>
                        </div>
                        
                        <div class="border-t border-[#404040] pt-3">
                            <p><strong>Recommendations:</strong></p>
                            <ul class="list-disc list-inside space-y-1 text-[#ababab] mt-2">
                                <li>Further monitoring recommended for steep slope areas</li>
                                <li>Consider additional vegetation analysis in sparse areas</li>
                                <li>Regular temporal analysis to track changes</li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="flex gap-3">
                    <button class="bg-[#28a745] hover:bg-[#218838] text-white px-4 py-2 rounded font-medium transition-colors">
                        📄 Export Report
                    </button>
                    <button class="bg-[#007bff] hover:bg-[#0056b3] text-white px-4 py-2 rounded font-medium transition-colors">
                        🔄 Run New Analysis
                    </button>
                </div>
            </div>
        `;
        
        document.getElementById('openai-analysis-results').innerHTML = response;
    }
    
    stopAnalysis() {
        console.log('🛑 Stopping analysis...');
        
        // Reset UI
        document.getElementById('start-openai-analysis-btn').classList.remove('hidden');
        document.getElementById('stop-openai-analysis-btn').classList.add('hidden');
        document.getElementById('openai-analysis-status').textContent = 'Analysis stopped';
        
        document.getElementById('openai-analysis-results').innerHTML = `
            <div class="text-center text-[#666] py-8">
                <div class="text-4xl mb-4">⏹️</div>
                <p>Analysis stopped by user</p>
            </div>
        `;
    }
    
    showAnalysisError(message) {
        document.getElementById('openai-analysis-results').innerHTML = `
            <div class="text-center text-[#dc3545] py-8">
                <div class="text-4xl mb-4">❌</div>
                <p>Analysis failed: ${message}</p>
            </div>
        `;
    }
    
    showImageModal(imageSrc, imageAlt) {
        // Reuse existing image modal if available
        if (window.UIManager && window.UIManager.showImageModal) {
            window.UIManager.showImageModal(imageSrc, imageAlt);
        } else {
            console.log('Image modal not available');
        }
    }

    getImagesForRegion(region) {
        const galleries = this.regionGalleries[region];
        if (!galleries) return [];

        const rasterImages =
            (galleries.raster?.gallery?.items || []).map(i => i.imageUrl);
        const sentinelImages =
            (galleries.sentinel?.items || []).map(i => i.imageUrl);

        return [...rasterImages, ...sentinelImages];
    }

    async sendPromptToOpenAI() {
        // Get the selected model name
        const modelSelect = document.getElementById('openai-model'); // Corrected ID
        const modelName = modelSelect ? modelSelect.value : 'gpt-4-vision-preview'; // Kept default as 'gpt-4-vision-preview'

        const promptPartsContainer = document.getElementById('dynamic-prompt-parts-container');
        if (!promptPartsContainer) {
            window.Utils?.showNotification('Prompt container not found', 'warning');
            return;
        }

        const textareas = promptPartsContainer.querySelectorAll('.prompt-part-textarea');
        let promptParts = [];
        textareas.forEach(textarea => {
            promptParts.push(textarea.value);
        });
        const prompt = promptParts.join('\n');

        if (!prompt.trim()) {
            window.Utils?.showNotification('No prompt content loaded or entered', 'warning');
            return;
        }
        const lat = parseFloat(document.getElementById('lat-input').value);
        const lng = parseFloat(document.getElementById('lng-input').value);
        const coords = (!isNaN(lat) && !isNaN(lng)) ? { lat, lng } : null;

        const targetRegions = this.selectedRegions.length > 0
            ? this.selectedRegions
            : [window.FileManager?.getSelectedRegion()].filter(Boolean);

        if (targetRegions.length === 0) {
            window.Utils?.showNotification('No region selected', 'warning');
            return;
        }

        for (const region of targetRegions) {
            const images = this.selectedRegions.length > 0
                ? this.getImagesForRegion(region)
                : this.selectedImages.map(img => img.imageUrl);

            try {
                const payload = {
                    prompt,
                    images,
                    laz_name: region,
                    coordinates: coords,
                    model_name: modelName, // Add model_name to the payload
                };
                const data = await openai().sendPrompt(payload);
                console.log('OpenAI response', data);
                window.Utils?.showNotification(
                    `Prompt sent for ${region}`,
                    'success'
                );
            } catch (err) {
                console.error('Failed to send to OpenAI', err);
                window.Utils?.showNotification(
                    `Failed to send prompt for ${region}`,
                    'error'
                );
            }
        }
    }

    async loadPrompts() {
        try {
            console.log('📋 Loading prompts for OpenAI analysis...');
            const response = await prompts().getAllPrompts(); // Expects {"prompts": [{"title": "...", "content": "..."}, ...]}
            const promptData = response.prompts;

            const container = document.getElementById('dynamic-prompt-parts-container');
            if (!container) {
                console.error('❌ Error: The div with ID "dynamic-prompt-parts-container" was not found in the DOM.');
                console.error('❌ This indicates the OpenAI tab content was not properly loaded.');
                return;
            }

            container.innerHTML = ''; // Clear existing content
            console.log('✅ Prompt container found and cleared');

            if (promptData && Array.isArray(promptData)) {
                console.log(`📋 Loading ${promptData.length} prompt parts...`);
                promptData.forEach((promptPart, index) => {
                    const titleElement = document.createElement('h3');
                    titleElement.textContent = promptPart.title;
                    titleElement.classList.add('text-lg', 'font-semibold', 'mt-2', 'mb-1', 'text-white'); // Added some styling

                    const textareaElement = document.createElement('textarea');
                    textareaElement.value = promptPart.content;
                    textareaElement.classList.add('prompt-part-textarea', 'w-full', 'p-2', 'border', 'border-gray-600', 'rounded-md', 'bg-gray-700', 'text-gray-200', 'h-48'); // Added some styling and h-48 for height
                    textareaElement.dataset.promptTitle = promptPart.title; // Store title for potential future use
                    textareaElement.id = `prompt-part-${index}`; // Unique ID

                    container.appendChild(titleElement);
                    container.appendChild(textareaElement);
                });
            } else {
                console.error('Failed to load prompts or prompts data is not in the expected format:', response);
                container.innerHTML = '<p class="text-red-500">Error loading prompts. See console for details.</p>';
            }
        } catch (err) {
            console.error('Failed to load prompts API:', err);
            const container = document.getElementById('dynamic-prompt-parts-container');
            if (container) {
                 container.innerHTML = `<p class="text-red-500">Failed to fetch prompts: ${err.message}. Check API and network.</p>`;
            }
             window.Utils?.showNotification(`Failed to load prompts: ${err.message}`, 'error');
        }
    }

    async loadRegions() {
        try {
            console.log('🔄 Loading regions for OpenAI analysis...');
            
            // Load regions directly using the input folder API call (matching "Select Region" button)
            const data = await regions().listRegions('input');
            console.log('📊 API response:', data);
            
            this.availableRegions = (data.regions || []).map(r => r.name);
            console.log('📋 Available regions:', this.availableRegions);
            
            this.renderRegionLists();
            this.updateSelectedRegionsInfo();
            
            console.log('✅ Regions loaded successfully');
        } catch (err) {
            console.error('❌ Failed to load regions:', err);
            // Show error in UI if elements exist
            const availList = document.getElementById('available-region-list');
            if (availList) {
                availList.innerHTML = '<li class="text-red-400 p-2">Failed to load regions</li>';
            }
        }
    }

    updateSelectedRegionsInfo() {
        const info = document.getElementById('selected-region-names');
        if (!info) return;
        if (this.selectedRegions.length === 0) {
            info.textContent = 'No regions selected';
        } else {
            info.textContent = `Selected: ${this.selectedRegions.join(', ')}`;
        }

        this.updateRegionGalleries();
    }

    updateRegionGalleries() {
        const container = document.getElementById('region-galleries');
        if (!container) return;

        // Remove galleries for deselected regions
        Object.keys(this.regionGalleries).forEach(region => {
            if (!this.selectedRegions.includes(region)) {
                const elem = container.querySelector(`.region-gallery[data-region="${region}"]`);
                if (elem) elem.remove();
                delete this.regionGalleries[region];
            }
        });

        // Add galleries for new regions
        this.selectedRegions.forEach(region => {
            if (!this.regionGalleries[region]) {
                const safe = region.replace(/[^a-zA-Z0-9_-]/g, '_');
                const section = document.createElement('div');
                section.className = 'accordion-section mb-4 region-gallery';
                section.dataset.region = region;
                section.innerHTML = `
                    <div class="accordion-header bg-[#303030] hover:bg-[#404040] cursor-pointer p-3 rounded-lg transition-colors" id="${safe}-accordion">
                        <h3 class="text-white font-semibold flex justify-between items-center m-0">
                            ${region}
                            <span class="accordion-arrow text-sm transition-transform">▼</span>
                        </h3>
                    </div>
                    <div class="accordion-content bg-[#262626] rounded-lg mt-2 p-3 collapsed" id="${safe}-content">
                        <div id="raster-gallery-${safe}" class="mb-4"></div>
                        <div id="sentinel-gallery-${safe}" class="mb-4"></div>
                    </div>`;
                container.appendChild(section);

                // Toggle behavior
                const header = section.querySelector('.accordion-header');
                const content = section.querySelector('.accordion-content');
                const arrow = section.querySelector('.accordion-arrow');
                header.addEventListener('click', () => {
                    const collapsed = content.classList.toggle('collapsed');
                    arrow.style.transform = collapsed ? 'rotate(-90deg)' : 'rotate(0deg)';
                });

                const raster = new RasterOverlayGallery(`raster-gallery-${safe}`);
                raster.loadRasters(region);
                const sentinel = new SatelliteOverlayGallery(`sentinel-gallery-${safe}`);
                sentinel.loadImages(region);

                this.regionGalleries[region] = { raster, sentinel };
            }
        });
    }

    renderRegionLists() {
        const availList = document.getElementById('available-region-list');
        const selList = document.getElementById('selected-region-list');
        
        if (!availList || !selList) {
            console.error('❌ Region list elements not found:');
            console.error('   - available-region-list:', !!availList);
            console.error('   - selected-region-list:', !!selList);
            console.error('   - openai-analysis-tab:', !!document.getElementById('openai-analysis-tab'));
            return;
        }

        console.log('✅ Found region list elements, rendering...');

        const createItem = (region, from) => {
            const li = document.createElement('li');
            li.textContent = region;
            li.dataset.region = region;
            li.draggable = true;
            li.addEventListener('click', () => {
                li.classList.toggle('selected');
            });
            li.addEventListener('dragstart', e => {
                li.classList.add('dragging');
                e.dataTransfer.setData('text/plain', JSON.stringify({ region, from }));
            });
            li.addEventListener('dragend', () => li.classList.remove('dragging'));
            return li;
        };

        availList.innerHTML = '';
        this.availableRegions.forEach(r => {
            availList.appendChild(createItem(r, 'available'));
        });

        selList.innerHTML = '';
        this.selectedRegions.forEach(r => {
            selList.appendChild(createItem(r, 'selected'));
        });
        
        console.log('✅ Region lists rendered with', this.availableRegions.length, 'available and', this.selectedRegions.length, 'selected regions');
    }

    moveToSelected(regions) {
        regions.forEach(r => {
            if (!this.selectedRegions.includes(r)) {
                this.selectedRegions.push(r);
                this.availableRegions = this.availableRegions.filter(a => a !== r);
            }
        });
        this.renderRegionLists();
        this.updateSelectedRegionsInfo();
    }

    moveToAvailable(regions) {
        regions.forEach(r => {
            if (!this.availableRegions.includes(r)) {
                this.availableRegions.push(r);
                this.selectedRegions = this.selectedRegions.filter(s => s !== r);
            }
        });
        this.renderRegionLists();
        this.updateSelectedRegionsInfo();
    }
}

// Make the class available globally
window.OpenAIAnalysis = OpenAIAnalysis;

// Initialize when DOM is ready (fallback for static content)
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚨 DOMContentLoaded fired');
    const openaiTab = document.getElementById('openai-analysis-tab');
    console.log('🚨 Found openai-analysis-tab:', !!openaiTab);
    
    if (openaiTab) {
        console.log('🚨 Creating OpenAI Analysis instance (static content)');
        window.openAIAnalysisInstance = new OpenAIAnalysis();
    } else {
        console.log('🚨 No openai-analysis-tab found on DOMContentLoaded - will wait for dynamic loading');
    }
});
