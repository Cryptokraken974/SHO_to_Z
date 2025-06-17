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
        this.setupEventListeners();
        this.initializeGalleries();
        this.loadPrompts();
        this.loadRegions();
    }
    
    setupEventListeners() {
        // Select Images button
        document.getElementById('select-images-btn')?.addEventListener('click', () => {
            this.openImageSelectionModal();
        });
        
        // Modal close handlers
        document.getElementById('image-selection-modal-close')?.addEventListener('click', () => {
            this.closeImageSelectionModal();
        });
        
        document.getElementById('cancel-image-selection')?.addEventListener('click', () => {
            this.closeImageSelectionModal();
        });
        
        // Category buttons
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchCategory(e.target.dataset.category);
            });
        });
        
        // Selection controls
        document.getElementById('select-all-btn')?.addEventListener('click', () => {
            this.selectAllVisible();
        });
        
        document.getElementById('clear-selection-btn')?.addEventListener('click', () => {
            this.clearSelection();
        });
        
        // Confirm selection
        document.getElementById('confirm-image-selection')?.addEventListener('click', () => {
            this.confirmSelection();
        });
        
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
        // Initialize image selection gallery
        this.galleryInstance = new ModularGallery('image-selection-gallery', {
            allowSelection: true,
            multipleSelection: true,
            showAddToMap: false,
            itemWidth: 'w-48',
            itemHeight: 'h-36',
            onSelectionChange: (selectedIds) => {
                this.updateSelectionCount(selectedIds);
            },
            onImageClick: (itemId, imageSrc, imageAlt) => {
                this.showImageModal(imageSrc, imageAlt);
            }
        });
        
        // Preview gallery removed
    }
    
    async openImageSelectionModal() {
        console.log('📸 Opening image selection modal');
        
        // Show loading state
        this.galleryInstance.showLoading();
        
        // Load available images
        await this.loadAvailableImages();
        
        // Show modal
        document.getElementById('image-selection-modal').classList.remove('hidden');
        
        // Filter and display images
        this.filterImagesByCategory(this.currentCategory);
    }
    
    closeImageSelectionModal() {
        document.getElementById('image-selection-modal').classList.add('hidden');
    }
    
    async loadAvailableImages() {
        try {
            console.log('🔄 Loading available images for current region');
            
            // Get current region
            const selectedRegion = window.FileManager?.getSelectedRegion();
            if (!selectedRegion) {
                this.galleryInstance.showError('No region selected. Please select a region first.');
                return;
            }
            
            this.availableImages = [];
            
            // Load raster products
            await this.loadRasterImages(selectedRegion);
            
            // Load satellite images
            await this.loadSatelliteImages(selectedRegion);
            
            console.log(`📁 Loaded ${this.availableImages.length} images`);
            
        } catch (error) {
            console.error('Error loading available images:', error);
            this.galleryInstance.showError('Failed to load images');
        }
    }
    
    async loadRasterImages(regionName) {
        const rasterTypes = [
            'hs_red', 'hs_green', 'hs_blue',
            'slope', 'aspect', 'color_relief', 'slope_relief', 'lrm',
            'hillshade_rgb', 'tint_overlay', 'boosted_hillshade'
        ];
        
        for (const rasterType of rasterTypes) {
            try {
                const overlayData = await overlays().getRasterOverlayData(regionName, rasterType);
                
                if (overlayData && overlayData.image_data) {
                    const imageUrl = `data:image/png;base64,${overlayData.image_data}`;
                    
                    this.availableImages.push({
                        id: `raster_${rasterType}_${regionName}`,
                        imageUrl: imageUrl,
                        title: this.getRasterDisplayName(rasterType),
                        subtitle: regionName,
                        category: this.getRasterCategory(rasterType),
                        type: 'raster',
                        rasterType: rasterType,
                        regionName: regionName
                    });
                }
            } catch (error) {
                console.debug(`No ${rasterType} data available for ${regionName}`);
            }
        }
    }
    
    async loadSatelliteImages(regionName) {
        try {
            // This would need to be implemented based on your satellite image API
            // For now, we'll check if there are satellite images in the UI
            const satelliteGallery = document.getElementById('satellite-gallery');
            const satelliteImages = satelliteGallery?.querySelectorAll('.gallery-item img');
            
            if (satelliteImages) {
                satelliteImages.forEach((img, index) => {
                    this.availableImages.push({
                        id: `satellite_${regionName}_${index}`,
                        imageUrl: img.src,
                        title: `Satellite Image ${index + 1}`,
                        subtitle: regionName,
                        category: 'satellite',
                        type: 'satellite',
                        regionName: regionName
                    });
                });
            }
        } catch (error) {
            console.debug('No satellite images available');
        }
    }
    
    getRasterDisplayName(rasterType) {
        const displayNames = {
            'hs_red': 'Hillshade Red',
            'hs_green': 'Hillshade Green',
            'hs_blue': 'Hillshade Blue',
            'slope': 'Slope',
            'aspect': 'Aspect',
            'color_relief': 'Color Relief',
            'slope_relief': 'Slope Relief',
            'lrm': 'Local Relief Model',
            'hillshade_rgb': 'RGB Hillshade',
            'tint_overlay': 'Tint Overlay',
            'boosted_hillshade': 'Boosted Hillshade'
        };
        return displayNames[rasterType] || rasterType;
    }
    
    getRasterCategory(rasterType) {
        if (['hs_red', 'hs_green', 'hs_blue'].includes(rasterType)) {
            return 'hillshades';
        }
        if (['hillshade_rgb', 'tint_overlay', 'boosted_hillshade'].includes(rasterType)) {
            return 'composites';
        }
        return 'rasters';
    }
    
    switchCategory(category) {
        this.currentCategory = category;
        
        // Update category button states
        document.querySelectorAll('.category-btn').forEach(btn => {
            if (btn.dataset.category === category) {
                btn.classList.remove('bg-[#262626]', 'text-[#ababab]');
                btn.classList.add('bg-[#00bfff]', 'text-white');
            } else {
                btn.classList.remove('bg-[#00bfff]', 'text-white');
                btn.classList.add('bg-[#262626]', 'text-[#ababab]');
            }
        });
        
        // Update category title
        const titles = {
            'all': 'All Images',
            'rasters': 'Raster Products',
            'satellite': 'Satellite Images',
            'hillshades': 'Hillshades',
            'composites': 'Composite Images'
        };
        document.getElementById('category-title').textContent = titles[category] || 'Images';
        
        // Filter and display images
        this.filterImagesByCategory(category);
    }
    
    filterImagesByCategory(category) {
        let filteredImages = this.availableImages;
        
        if (category !== 'all') {
            filteredImages = this.availableImages.filter(image => image.category === category);
        }
        
        this.galleryInstance.setItems(filteredImages);
        
        // Restore selection state
        const selectedIds = this.selectedImages.map(img => img.id);
        this.galleryInstance.setSelectedItems(selectedIds);
    }
    
    updateSelectionCount(selectedIds) {
        const count = selectedIds.length;
        document.getElementById('selection-count').textContent = `${count} selected`;
        document.getElementById('modal-selection-summary').textContent = 
            count === 0 ? 'No images selected' : `${count} image${count === 1 ? '' : 's'} selected`;
    }
    
    selectAllVisible() {
        const visibleImages = this.galleryInstance.items;
        const allIds = visibleImages.map(img => img.id);
        this.galleryInstance.setSelectedItems(allIds);
    }
    
    clearSelection() {
        this.galleryInstance.setSelectedItems([]);
    }
    
    confirmSelection() {
        const selectedIds = this.galleryInstance.getSelectedItems();
        this.selectedImages = this.availableImages.filter(img => selectedIds.includes(img.id));
        
        console.log(`✅ Selected ${this.selectedImages.length} images for analysis`);
        
        // Update UI
        this.updateSelectedImagesCount();
        
        // Close modal
        this.closeImageSelectionModal();
    }
    
    updateSelectedImagesPreview() {
        // Preview removed
    }
    
    updateSelectedImagesCount() {
        const count = this.selectedImages.length;
        document.getElementById('selected-images-count').textContent = 
            count === 0 ? 'No images selected' : `${count} image${count === 1 ? '' : 's'} selected`;
    }
    
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
        if (this.selectedImages.length === 0) {
            window.Utils?.showNotification('Please select images for analysis first', 'warning');
            return;
        }
        
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
                    <p class="text-[#ababab] text-sm mb-3">Based on ${this.selectedImages.length} image(s) analyzed</p>
                    
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
        const prompt = document.getElementById('prompt-display').value.trim();
        if (!prompt) {
            window.Utils?.showNotification('No prompt loaded', 'warning');
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
            const data = await prompts().getAllPrompts();
            document.getElementById('prompt-display').value = data.content;
        } catch (err) {
            console.error('Failed to load prompts', err);
        }
    }

    async loadRegions() {
        try {
            const data = await regions().listRegions();
            this.availableRegions = (data.regions || []).map(r => r.name);
            this.renderRegionLists();
            this.updateSelectedRegionsInfo();
        } catch (err) {
            console.error('Failed to load regions', err);
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
        if (!availList || !selList) return;

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
        this.availableRegions.forEach(r => availList.appendChild(createItem(r, 'available')));

        selList.innerHTML = '';
        this.selectedRegions.forEach(r => selList.appendChild(createItem(r, 'selected')));
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('openai-analysis-tab')) {
        window.openAIAnalysis = new OpenAIAnalysis();
    }
});
