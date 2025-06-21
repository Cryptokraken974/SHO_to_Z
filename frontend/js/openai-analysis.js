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
        this.promptParts = []; // Store loaded prompt parts
        this.currentPromptIndex = 0; // Track current prompt part

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
        // Send prompt to OpenAI
        document.getElementById('send-to-openai')?.addEventListener('click', () => {
            this.sendPromptToOpenAI();
        });

        // Prompt navigation
        document.getElementById('prompt-nav-prev')?.addEventListener('click', () => {
            this.navigatePrompt(-1);
        });

        document.getElementById('prompt-nav-next')?.addEventListener('click', () => {
            this.navigatePrompt(1);
        });

        // Keyboard navigation for prompt parts
        document.addEventListener('keydown', (e) => {
            // Only handle keyboard navigation when textarea is focused
            const currentTextarea = document.getElementById('current-prompt-textarea');
            if (document.activeElement === currentTextarea) {
                if (e.ctrlKey || e.metaKey) { // Ctrl/Cmd + Arrow keys
                    if (e.key === 'ArrowLeft') {
                        e.preventDefault();
                        this.navigatePrompt(-1);
                    } else if (e.key === 'ArrowRight') {
                        e.preventDefault();
                        this.navigatePrompt(1);
                    }
                }
            }
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
    
    navigatePrompt(direction) {
        if (this.promptParts.length === 0) return;
        
        // Save current prompt content
        const currentTextarea = document.getElementById('current-prompt-textarea');
        if (currentTextarea && this.promptParts[this.currentPromptIndex]) {
            this.promptParts[this.currentPromptIndex].content = currentTextarea.value;
        }
        
        // Update index
        this.currentPromptIndex += direction;
        if (this.currentPromptIndex < 0) {
            this.currentPromptIndex = this.promptParts.length - 1;
        } else if (this.currentPromptIndex >= this.promptParts.length) {
            this.currentPromptIndex = 0;
        }
        
        this.displayCurrentPrompt();
    }
    
    displayCurrentPrompt() {
        if (this.promptParts.length === 0) return;
        
        const currentPrompt = this.promptParts[this.currentPromptIndex];
        
        // Update UI elements
        const titleElement = document.getElementById('prompt-title');
        const counterElement = document.getElementById('prompt-counter');
        const textareaElement = document.getElementById('current-prompt-textarea');
        const prevButton = document.getElementById('prompt-nav-prev');
        const nextButton = document.getElementById('prompt-nav-next');
        const contentArea = document.getElementById('prompt-content-area');
        
        // Add transition animation
        if (contentArea) {
            contentArea.classList.add('prompt-nav-transition');
            
            setTimeout(() => {
                if (titleElement) titleElement.textContent = currentPrompt.title;
                if (counterElement) counterElement.textContent = `${this.currentPromptIndex + 1} / ${this.promptParts.length}`;
                if (textareaElement) {
                    textareaElement.value = currentPrompt.content;
                    textareaElement.placeholder = `Editing: ${currentPrompt.title}`;
                }
                
                contentArea.classList.add('active');
            }, 100);
            
            setTimeout(() => {
                contentArea.classList.remove('prompt-nav-transition');
            }, 300);
        } else {
            // Fallback without animation
            if (titleElement) titleElement.textContent = currentPrompt.title;
            if (counterElement) counterElement.textContent = `${this.currentPromptIndex + 1} / ${this.promptParts.length}`;
            if (textareaElement) {
                textareaElement.value = currentPrompt.content;
                textareaElement.placeholder = `Editing: ${currentPrompt.title}`;
            }
        }
        
        // Update button states (always allow cycling)
        if (prevButton) {
            prevButton.disabled = this.promptParts.length <= 1;
        }
        if (nextButton) {
            nextButton.disabled = this.promptParts.length <= 1;
        }
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

        // Save current prompt content before sending
        const currentTextarea = document.getElementById('current-prompt-textarea');
        if (currentTextarea && this.promptParts[this.currentPromptIndex]) {
            this.promptParts[this.currentPromptIndex].content = currentTextarea.value;
        }

        // Collect all prompt parts
        let promptParts = [];
        this.promptParts.forEach(promptPart => {
            promptParts.push(promptPart.content);
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

            console.log('✅ Prompt container found');

            if (promptData && Array.isArray(promptData) && promptData.length > 0) {
                console.log(`📋 Loading ${promptData.length} prompt parts...`);
                
                // Store prompt parts
                this.promptParts = promptData.map(part => ({
                    title: part.title,
                    content: part.content
                }));
                
                // Reset to first prompt
                this.currentPromptIndex = 0;
                
                // Display the first prompt
                this.displayCurrentPrompt();
                
                console.log('✅ Prompt parts loaded successfully');
            } else {
                console.error('Failed to load prompts or prompts data is not in the expected format:', response);
                
                // Show error state
                const titleElement = document.getElementById('prompt-title');
                const counterElement = document.getElementById('prompt-counter');
                const textareaElement = document.getElementById('current-prompt-textarea');
                
                if (titleElement) titleElement.textContent = 'Error loading prompts';
                if (counterElement) counterElement.textContent = '0 / 0';
                if (textareaElement) textareaElement.placeholder = 'Error loading prompts. See console for details.';
            }
        } catch (err) {
            console.error('Failed to load prompts API:', err);
            
            // Show error state
            const titleElement = document.getElementById('prompt-title');
            const counterElement = document.getElementById('prompt-counter');
            const textareaElement = document.getElementById('current-prompt-textarea');
            
            if (titleElement) titleElement.textContent = 'Failed to load prompts';
            if (counterElement) counterElement.textContent = '0 / 0';
            if (textareaElement) textareaElement.placeholder = `Failed to fetch prompts: ${err.message}`;
            
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
