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
        this.allRegions = []; // Store all regions before filtering
        this.ndviFilterEnabled = false; // Track NDVI filter state
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

        // Prompt preview modal
        document.getElementById('prompt-preview-btn')?.addEventListener('click', () => {
            this.showPromptPreview();
        });

        document.getElementById('prompt-preview-close')?.addEventListener('click', () => {
            this.hidePromptPreview();
        });

        document.getElementById('prompt-preview-close-btn')?.addEventListener('click', () => {
            this.hidePromptPreview();
        });

        document.getElementById('prompt-preview-copy')?.addEventListener('click', () => {
            this.copyPromptToClipboard();
        });

        // Close modal when clicking outside
        document.getElementById('prompt-preview-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'prompt-preview-modal') {
                this.hidePromptPreview();
            }
        });

        // Keyboard navigation for prompt parts
        document.addEventListener('keydown', (e) => {
            // Handle modal close with ESC key
            if (e.key === 'Escape') {
                const modal = document.getElementById('prompt-preview-modal');
                if (modal && !modal.classList.contains('hidden')) {
                    this.hidePromptPreview();
                    return;
                }
            }
            
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

        // NDVI Filter checkbox event listener
        const ndviFilterCheckbox = document.getElementById('ndvi-filter-checkbox');
        ndviFilterCheckbox?.addEventListener('change', (e) => {
            this.ndviFilterEnabled = e.target.checked;
            console.log('🌱 NDVI filter', this.ndviFilterEnabled ? 'enabled' : 'disabled');
            
            // Reload prompts for the appropriate workflow
            this.loadPrompts();
            
            // Apply region filter
            this.applyNdviFilter();
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
                    // Ensure content is a string
                    let content = '';
                    if (typeof currentPrompt.content === 'string') {
                        content = currentPrompt.content;
                    } else if (typeof currentPrompt.content === 'object') {
                        if (currentPrompt.content && currentPrompt.content.content) {
                            content = String(currentPrompt.content.content);
                        } else {
                            content = JSON.stringify(currentPrompt.content, null, 2);
                        }
                    } else if (currentPrompt.content) {
                        content = String(currentPrompt.content);
                    }
                    
                    textareaElement.value = content;
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
                // Ensure content is a string
                let content = '';
                if (typeof currentPrompt.content === 'string') {
                    content = currentPrompt.content;
                } else if (typeof currentPrompt.content === 'object') {
                    if (currentPrompt.content && currentPrompt.content.content) {
                        content = String(currentPrompt.content.content);
                    } else {
                        content = JSON.stringify(currentPrompt.content, null, 2);
                    }
                } else if (currentPrompt.content) {
                    content = String(currentPrompt.content);
                }
                
                textareaElement.value = content;
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
    
    showPromptPreview() {
        // Save current prompt content before showing preview
        const currentTextarea = document.getElementById('current-prompt-textarea');
        if (currentTextarea && this.promptParts[this.currentPromptIndex]) {
            this.promptParts[this.currentPromptIndex].content = currentTextarea.value;
        }

        // Debug: Log the prompt parts to see what we're working with
        console.log('📋 Prompt parts for preview:', this.promptParts);

        // Collect all prompt parts with titles
        let promptSections = [];
        this.promptParts.forEach((promptPart, index) => {
            // Ensure content is a string and handle different data types
            let content = '';
            if (typeof promptPart.content === 'string') {
                content = promptPart.content.trim();
            } else if (typeof promptPart.content === 'object') {
                // If content is an object, try to extract the content field or stringify it
                if (promptPart.content && promptPart.content.content) {
                    content = String(promptPart.content.content).trim();
                } else {
                    content = JSON.stringify(promptPart.content, null, 2);
                }
            } else if (promptPart.content) {
                // Convert to string if it's some other type
                content = String(promptPart.content).trim();
            }

            if (content) {
                // Add section header with title
                promptSections.push(`=== ${promptPart.title || `Part ${index + 1}`} ===`);
                promptSections.push(content);
                promptSections.push(''); // Empty line between sections
            }
        });
        
        // Remove the last empty line
        if (promptSections.length > 0 && promptSections[promptSections.length - 1] === '') {
            promptSections.pop();
        }
        
        const completePrompt = promptSections.join('\n');

        // Update modal content
        const modal = document.getElementById('prompt-preview-modal');
        const content = document.getElementById('prompt-preview-content');
        const stats = document.getElementById('prompt-preview-stats');

        if (content) {
            content.textContent = completePrompt || 'No prompt content available';
        }

        if (stats) {
            const charCount = completePrompt.length;
            const wordCount = completePrompt.trim() ? completePrompt.trim().split(/\s+/).length : 0;
            stats.textContent = `${charCount} characters, ${wordCount} words`;
        }

        // Show modal
        if (modal) {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        }
    }

    hidePromptPreview() {
        const modal = document.getElementById('prompt-preview-modal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = ''; // Restore scrolling
        }
    }

    async copyPromptToClipboard() {
        const content = document.getElementById('prompt-preview-content');
        if (content && content.textContent) {
            try {
                await navigator.clipboard.writeText(content.textContent);
                window.Utils?.showNotification('Prompt copied to clipboard!', 'success');
                
                // Visual feedback on copy button
                const copyBtn = document.getElementById('prompt-preview-copy');
                if (copyBtn) {
                    const originalText = copyBtn.textContent;
                    copyBtn.textContent = '✓ Copied!';
                    copyBtn.classList.add('bg-green-600');
                    
                    setTimeout(() => {
                        copyBtn.textContent = originalText;
                        copyBtn.classList.remove('bg-green-600');
                    }, 2000);
                }
            } catch (err) {
                console.error('Failed to copy to clipboard:', err);
                window.Utils?.showNotification('Failed to copy to clipboard', 'error');
            }
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
        try {
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
                // Ensure content is a string and handle different data types
                let content = '';
                if (typeof promptPart.content === 'string') {
                    content = promptPart.content.trim();
                } else if (typeof promptPart.content === 'object') {
                    // If content is an object, try to extract the content field or stringify it
                    if (promptPart.content && promptPart.content.content) {
                        content = String(promptPart.content.content).trim();
                    } else {
                        content = JSON.stringify(promptPart.content, null, 2);
                    }
                } else if (promptPart.content) {
                    // Convert to string if it's some other type
                    content = String(promptPart.content).trim();
                }

                if (content) {
                    promptParts.push(content);
                }
            });
            const prompt = promptParts.join('\n\n');

            if (!prompt.trim()) {
                window.Utils?.showNotification('No prompt content loaded or entered', 'warning');
                return;
            }
            // Coordinates are optional for OpenAI analysis - they can be used to provide location context
            // but aren't required for image analysis
            const coords = null; // Could be enhanced later to get coordinates from selected region metadata

            const targetRegions = this.selectedRegions.length > 0
                ? this.selectedRegions
                : [window.FileManager?.getSelectedRegion()].filter(Boolean);

            if (targetRegions.length === 0) {
                window.Utils?.showNotification('No region selected', 'warning');
                return;
            }

            // Show loading overlay
            this.showLoadingOverlay(targetRegions);

            let successCount = 0;
            let totalRegions = targetRegions.length;

            for (const region of targetRegions) {
                const imageDataUrls = this.selectedRegions.length > 0
                    ? this.getImagesForRegion(region)
                    : this.selectedImages.map(img => img.imageUrl);

                try {
                    // Update loading message for current region
                    this.updateLoadingMessage(`Processing region: ${region}`, `Analyzing ${imageDataUrls.length} images...`);

                    // Step 1: Save images to file system first
                    let imagePaths = [];
                    let tempFolderName = null; // Store temp folder name for backend
                    if (imageDataUrls && imageDataUrls.length > 0) {
                        console.log(`💾 Saving ${imageDataUrls.length} images for region ${region}...`);
                        
                        // Extract meaningful image names from gallery data
                        const imagesData = imageDataUrls.map((dataUrl, index) => {
                            let imageName = `image_${index + 1}`;
                            
                            // Try to get meaningful names from gallery items
                            const galleries = this.regionGalleries[region];
                            if (galleries) {
                                const allItems = [
                                    ...(galleries.raster?.gallery?.items || []),
                                    ...(galleries.sentinel?.items || [])
                                ];
                                
                                const matchingItem = allItems.find(item => item.imageUrl === dataUrl);
                                if (matchingItem) {
                                    // Create meaningful filename from title
                                    imageName = matchingItem.title
                                        .toLowerCase()
                                        .replace(/[^a-z0-9_-]/g, '_')
                                        .replace(/_+/g, '_');
                                }
                            }
                            
                            return {
                                name: imageName,
                                data: dataUrl
                            };
                        });
                        
                        // Save images to backend
                        const savePayload = {
                            region_name: region,
                            images: imagesData
                        };
                        
                        const saveResult = await openai().saveImages(savePayload);
                        if (saveResult.saved_images && saveResult.saved_images.length > 0) {
                            imagePaths = saveResult.saved_images.map(img => img.path);
                            console.log(`✅ Saved images to: ${imagePaths.join(', ')}`);
                            
                            // Store temp folder name for sending to backend
                            tempFolderName = saveResult.temp_folder_name;
                        } else {
                            console.warn('⚠️ No images were saved, proceeding with data URLs');
                            imagePaths = imageDataUrls;
                        }
                    } else {
                        console.log(`ℹ️ No images found for region ${region}`);
                    }

                    // Step 2: Send prompt with saved image paths
                    this.updateLoadingMessage(`Sending to OpenAI...`, `Waiting for AI analysis response...`);
                    
                    const payload = {
                        prompt,
                        images: imagePaths, // Use file paths instead of data URLs
                        laz_name: region,
                        coordinates: coords,
                        model_name: modelName,
                        temp_folder_name: tempFolderName, // Pass temp folder name to backend
                    };
                    
                    const data = await openai().sendPrompt(payload);
                    console.log('OpenAI response', data);
                    successCount++;
                    
                    window.Utils?.showNotification(
                        `Analysis completed for ${region}`,
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

            // Show completion notification
            if (successCount === totalRegions) {
                window.Utils?.showNotification(
                    `Analysis completed for all ${successCount} region(s)! Switching to Results tab...`,
                    'success'
                );
                
                // Automatically switch to Results tab after a short delay
                setTimeout(() => {
                    this.switchToResultsTab();
                }, 1500);
            } else if (successCount > 0) {
                window.Utils?.showNotification(
                    `Analysis completed for ${successCount} of ${totalRegions} regions. Check Results tab for details.`,
                    'warning'
                );
                
                // Still switch to results tab to show partial results
                setTimeout(() => {
                    this.switchToResultsTab();
                }, 2000);
            }
        } catch (error) {
            console.error('Unexpected error in sendPromptToOpenAI:', error);
            window.Utils?.showNotification(
                'An unexpected error occurred during analysis',
                'error'
            );
        } finally {
            // Always hide loading overlay, regardless of success or failure
            this.hideLoadingOverlay();
        }
    }

    async loadPrompts(forceWorkflow = null) {
        try {
            console.log('📋 Loading prompts for OpenAI analysis...');
            
            // Determine which workflow to use
            let workflow = forceWorkflow;
            if (!workflow) {
                // Use NDVI filter state to determine workflow
                workflow = this.ndviFilterEnabled ? 'workflow' : 'workflow_no_ndvi';
            }
            
            console.log(`📋 Loading prompts from workflow: ${workflow}`);
            
            const response = await prompts().getWorkflowPrompts(workflow);
            const promptData = response.prompts;

            const container = document.getElementById('dynamic-prompt-parts-container');
            if (!container) {
                console.error('❌ Error: The div with ID "dynamic-prompt-parts-container" was not found in the DOM.');
                console.error('❌ This indicates the OpenAI tab content was not properly loaded.');
                return;
            }

            console.log('✅ Prompt container found');

            if (promptData && Array.isArray(promptData) && promptData.length > 0) {
                console.log(`📋 Loading ${promptData.length} prompt parts from ${workflow}...`);
                
                // Store prompt parts
                this.promptParts = promptData.map(part => ({
                    title: part.title,
                    content: part.content
                }));
                
                // Reset to first prompt
                this.currentPromptIndex = 0;
                
                // Display the first prompt
                this.displayCurrentPrompt();
                
                console.log(`✅ Prompt parts loaded successfully from ${workflow} workflow`);
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
            
            // Load regions from OUTPUT folder where processed data and coordinate-based regions are stored
            const data = await regions().listRegions('output');
            console.log('📊 API response:', data);
            
            // Store all regions with their metadata
            this.allRegions = data.regions || [];
            console.log('📋 All regions loaded from output folder:', this.allRegions.map(r => r.name));
            
            // Apply initial filter (will set this.availableRegions)
            this.applyNdviFilter();
            
            console.log('✅ Regions loaded successfully from output folder');
        } catch (err) {
            console.error('❌ Failed to load regions:', err);
            // Show error in UI if elements exist
            const availList = document.getElementById('available-region-list');
            if (availList) {
                availList.innerHTML = '<li class="text-red-400 p-2">Failed to load regions</li>';
            }
        }
    }

    async applyNdviFilter() {
        try {
            if (!this.allRegions || this.allRegions.length === 0) {
                console.log('🔄 No regions loaded yet, filter will be applied after loading');
                return;
            }

            console.log('🌱 Applying NDVI filter...', this.ndviFilterEnabled ? 'SHOW NDVI-ENABLED' : 'SHOW NDVI-DISABLED');
            
            // Show loading state during filter
            const availList = document.getElementById('available-region-list');
            if (availList) {
                availList.innerHTML = '<li class="text-[#ababab] p-2">🔄 Checking NDVI status...</li>';
            }
            
            // Always filter regions based on NDVI status
            console.log('🔍 Checking NDVI status for each region...');
            
            const filteredRegions = [];
            
            for (const region of this.allRegions) {
                try {
                    // Check NDVI status for this region
                    const response = await fetch(`/api/regions/${encodeURIComponent(region.name)}/ndvi-status`);
                    
                    if (response.ok) {
                        const ndviData = await response.json();
                        const ndviEnabled = ndviData.ndvi_enabled;
                        
                        console.log(`   📊 ${region.name}: NDVI ${ndviEnabled ? 'enabled' : 'disabled'}`);
                        
                        // Include region based on filter toggle
                        if (this.ndviFilterEnabled && ndviEnabled) {
                            // Show only NDVI-enabled regions
                            filteredRegions.push(region.name);
                        } else if (!this.ndviFilterEnabled && !ndviEnabled) {
                            // Show only NDVI-disabled regions
                            filteredRegions.push(region.name);
                        }
                    } else {
                        console.warn(`   ⚠️ Could not check NDVI status for ${region.name}`);
                        // Include region if we can't check (fail open)
                        filteredRegions.push(region.name);
                    }
                } catch (error) {
                    console.warn(`   ❌ Error checking NDVI status for ${region.name}:`, error);
                    // Include region if there's an error (fail open)
                    filteredRegions.push(region.name);
                }
            }
            
            this.availableRegions = filteredRegions.filter(regionName => 
                !this.selectedRegions.includes(regionName)
            );
            
            if (this.ndviFilterEnabled) {
                console.log(`✅ NDVI filter applied: Showing ${filteredRegions.length}/${this.allRegions.length} NDVI-enabled regions`);
            } else {
                console.log(`✅ NDVI filter applied: Showing ${filteredRegions.length}/${this.allRegions.length} NDVI-disabled regions`);
            }
            
            this.renderRegionLists();
            this.updateSelectedRegionsInfo();
            
        } catch (error) {
            console.error('❌ Error applying NDVI filter:', error);
            // Fall back to showing all regions
            this.availableRegions = this.allRegions
                .map(r => r.name)
                .filter(regionName => !this.selectedRegions.includes(regionName));
            this.renderRegionLists();
            this.updateSelectedRegionsInfo();
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
            if (this.selectedRegions.includes(r)) {
                this.selectedRegions = this.selectedRegions.filter(s => s !== r);
            }
        });
        // Re-apply filter to ensure the moved regions appear in available list based on current filter
        this.applyNdviFilter();
    }

    // Loading overlay methods
    showLoadingOverlay(regions) {
        const overlay = document.getElementById('openai-loading-overlay');
        if (overlay) {
            // Update message based on number of regions
            const regionText = regions.length === 1 
                ? `region: ${regions[0]}` 
                : `${regions.length} regions`;
            
            this.updateLoadingMessage(
                `🤖 AI Analysis Started`,
                `Processing ${regionText}...<br><small>Preparing images and sending to OpenAI</small>`
            );
            
            overlay.classList.add('show');
            
            // Disable page interactions
            document.body.style.pointerEvents = 'none';
            overlay.style.pointerEvents = 'auto'; // Keep overlay interactive
        }
    }

    hideLoadingOverlay() {
        const overlay = document.getElementById('openai-loading-overlay');
        if (overlay) {
            overlay.classList.remove('show');
            
            // Re-enable page interactions
            document.body.style.pointerEvents = 'auto';
        }
    }

    updateLoadingMessage(title, message) {
        const titleElement = document.querySelector('.openai-loading-title');
        const messageElement = document.querySelector('.openai-loading-message');
        
        if (titleElement) {
            titleElement.innerHTML = title;
        }
        if (messageElement) {
            messageElement.innerHTML = message;
        }
    }

    switchToResultsTab() {
        // Find and click the Results tab to switch to it
        const resultsTab = document.querySelector('[data-tab="results"]');
        if (resultsTab) {
            resultsTab.click();
            console.log('✅ Automatically switched to Results tab');
        } else {
            console.warn('⚠️ Results tab not found, cannot auto-switch');
            // Try alternative selectors
            const altResultsTab = document.getElementById('results-tab') || 
                                 document.querySelector('.tab-button[data-target="results"]') ||
                                 document.querySelector('button[data-tab="results"]');
            if (altResultsTab) {
                altResultsTab.click();
                console.log('✅ Automatically switched to Results tab (alternative selector)');
            }
        }
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
