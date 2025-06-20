/**
 * Modular Gallery Component
 * Reusable gallery for displaying images with preview and selection functionality
 */

class ModularGallery {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            allowSelection: options.allowSelection || false,
            multipleSelection: options.multipleSelection || false,
            showAddToMap: options.showAddToMap || false,
            itemClass: options.itemClass || 'gallery-item',
            itemWidth: options.itemWidth || 'w-full',  // Full width of grid cell
            itemHeight: options.itemHeight || 'h-40',  // Slightly smaller height for better grid fit
            onSelectionChange: options.onSelectionChange || (() => {}),
            onAddToMap: options.onAddToMap || (() => {}),
            onImageClick: options.onImageClick || null,
            getOverlayState: options.getOverlayState || (() => false), // Function to check if overlay is active
            ...options
        };
        
        this.selectedItems = new Set();
        this.items = [];
        this.overlayStates = new Map(); // Track overlay states for each item
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error(`Gallery container with ID '${this.containerId}' not found`);
            return;
        }
        
        // Add CSS classes for gallery
        this.container.classList.add('modular-gallery');
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Event delegation for gallery items
        this.container.addEventListener('click', (e) => {
            const galleryItem = e.target.closest(`.${this.options.itemClass}`);
            if (!galleryItem) return;
            
            const itemId = galleryItem.dataset.itemId;
            if (!itemId) return;
            
            // Handle selection
            if (e.target.classList.contains('gallery-item-selector') || 
                (this.options.allowSelection && !e.target.closest('.add-to-map-btn'))) {
                this.toggleSelection(itemId);
            }
            
            // Handle add to map
            if (e.target.closest('.add-to-map-btn')) {
                e.preventDefault();
                this.options.onAddToMap(itemId, galleryItem);
            }
            
            // Handle image click for modal view
            if (e.target.classList.contains('gallery-image') && this.options.onImageClick) {
                this.options.onImageClick(itemId, e.target.src, e.target.alt);
            }
        });
    }
    
    /**
     * Set items to display in the gallery
     * @param {Array} items - Array of item objects
     */
    setItems(items) {
        this.items = items;
        this.render();
    }
    
    /**
     * Add items to the gallery
     * @param {Array} newItems - Array of new item objects
     */
    addItems(newItems) {
        this.items = [...this.items, ...newItems];
        this.render();
    }
    
    /**
     * Clear all items from the gallery
     */
    clear() {
        this.items = [];
        this.selectedItems.clear();
        this.render();
    }
    
    /**
     * Toggle selection of an item
     * @param {string} itemId - ID of the item to toggle
     */
    toggleSelection(itemId) {
        if (!this.options.allowSelection) return;
        
        if (this.selectedItems.has(itemId)) {
            this.selectedItems.delete(itemId);
        } else {
            if (!this.options.multipleSelection) {
                this.selectedItems.clear();
            }
            this.selectedItems.add(itemId);
        }
        
        this.updateSelectionUI();
        this.options.onSelectionChange(Array.from(this.selectedItems));
    }
    
    /**
     * Get selected item IDs
     * @returns {Array} Array of selected item IDs
     */
    getSelectedItems() {
        return Array.from(this.selectedItems);
    }
    
    /**
     * Set selected items
     * @param {Array} itemIds - Array of item IDs to select
     */
    setSelectedItems(itemIds) {
        this.selectedItems = new Set(itemIds);
        this.updateSelectionUI();
        this.options.onSelectionChange(Array.from(this.selectedItems));
    }
    
    /**
     * Update selection UI
     */
    updateSelectionUI() {
        this.container.querySelectorAll(`.${this.options.itemClass}`).forEach(item => {
            const itemId = item.dataset.itemId;
            const isSelected = this.selectedItems.has(itemId);
            
            item.classList.toggle('selected', isSelected);
            
            const selector = item.querySelector('.gallery-item-selector');
            if (selector) {
                selector.innerHTML = isSelected ? '✓' : '';
                selector.classList.toggle('selected', isSelected);
            }
        });
    }

    /**
     * Update overlay button states
     */
    updateOverlayButtonStates() {
        if (!this.options.showAddToMap) return;
        
        this.container.querySelectorAll(`.${this.options.itemClass}`).forEach(item => {
            const itemId = item.dataset.itemId;
            const button = item.querySelector('.add-to-map-btn');
            if (button) {
                const isOnMap = this.options.getOverlayState(itemId);
                this.updateButtonState(button, isOnMap);
            }
        });
    }

    /**
     * Update a single button's state
     * @param {HTMLElement} button - The button element
     * @param {boolean} isOnMap - Whether the overlay is on the map
     */
    updateButtonState(button, isOnMap) {
        if (isOnMap) {
            button.textContent = 'Remove from Map';
            button.classList.remove('bg-[#28a745]', 'hover:bg-[#218838]');
            button.classList.add('bg-[#dc3545]', 'hover:bg-[#c82333]');
            button.dataset.overlayState = 'active';
        } else {
            button.textContent = 'Add to Map';
            button.classList.remove('bg-[#dc3545]', 'hover:bg-[#c82333]');
            button.classList.add('bg-[#28a745]', 'hover:bg-[#218838]');
            button.dataset.overlayState = 'inactive';
        }
    }

    /**
     * Update button state for a specific item
     * @param {string} itemId - ID of the item to update
     * @param {boolean} isOnMap - Whether the overlay is on the map
     */
    updateItemOverlayState(itemId, isOnMap) {
        const item = this.container.querySelector(`[data-item-id="${itemId}"]`);
        if (item) {
            const button = item.querySelector('.add-to-map-btn');
            if (button) {
                this.updateButtonState(button, isOnMap);
            }
        }
    }
    
    /**
     * Render the gallery
     */
    render() {
        if (this.items.length === 0) {
            this.container.innerHTML = `
                <div class="text-center py-8 text-[#666]">
                    <div class="text-4xl mb-4">📁</div>
                    <p>No images available</p>
                </div>
            `;
            return;
        }
        
        const galleryHTML = this.items.map(item => this.renderItem(item)).join('');
        
        // Use grid layout for full display without scrolling
        this.container.innerHTML = `
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 pb-4">
                ${galleryHTML}
            </div>
        `;
        
        this.updateSelectionUI();
        this.updateOverlayButtonStates();
    }
    
    /**
     * Render a single gallery item
     * @param {Object} item - Item to render
     * @returns {string} HTML string for the item
     */
    renderItem(item) {
        const {
            id,
            imageUrl,
            title,
            subtitle,
            status,
            color,
            type = 'image'
        } = item;
        
        let content = '';
        
        if (type === 'placeholder') {
            content = `
                <div class="flex-1 flex items-center justify-center">
                    <div class="text-white text-lg font-medium" style="color: ${color || '#fff'}">${title}</div>
                </div>
            `;
        } else if (imageUrl) {
            content = `
                <div class="relative w-full h-full">
                    <img src="${imageUrl}" 
                         alt="${title}" 
                         class="gallery-image cursor-pointer w-full h-full object-cover"
                         title="Click to view larger image">
                    <div class="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                        ${title}
                    </div>
                    ${subtitle ? `
                        <div class="absolute bottom-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                            ${subtitle}
                        </div>
                    ` : ''}
                    ${status ? `
                        <div class="absolute top-2 right-2 bg-${status === 'ready' ? 'green' : 'yellow'}-600 bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                            ${status === 'ready' ? '✓ Ready' : '⏳ Processing'}
                        </div>
                    ` : ''}
                </div>
            `;
        } else {
            content = `
                <div class="flex-1 flex items-center justify-center">
                    <div class="text-[#666] text-center">
                        <div class="text-2xl mb-2">📷</div>
                        <div>${title}</div>
                    </div>
                </div>
            `;
        }
        
        return `
            <div class="${this.options.itemClass} ${this.options.itemWidth} ${this.options.itemHeight} bg-[#1a1a1a] border border-[#303030] rounded-lg flex flex-col hover:border-[#404040] transition-colors relative" 
                 data-item-id="${id}">
                ${this.options.allowSelection ? `
                    <div class="gallery-item-selector absolute top-2 right-2 w-6 h-6 bg-black bg-opacity-50 rounded-full flex items-center justify-center text-white text-sm cursor-pointer z-10">
                    </div>
                ` : ''}
                ${content}
                ${this.options.showAddToMap && imageUrl ? `
                    <button class="add-to-map-btn bg-[#28a745] hover:bg-[#218838] text-white px-3 py-1 rounded-b-lg text-sm font-medium transition-colors mt-1" 
                            data-item-id="${id}">
                        Add to Map
                    </button>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * Show loading state
     */
    showLoading() {
        this.container.innerHTML = `
            <div class="text-center py-8 text-[#666]">
                <div class="text-4xl mb-4">🔄</div>
                <p>Loading images...</p>
            </div>
        `;
    }
    
    /**
     * Show error state
     * @param {string} message - Error message to display
     */
    showError(message) {
        this.container.innerHTML = `
            <div class="text-center py-8 text-[#666]">
                <div class="text-4xl mb-4">❌</div>
                <p>Error: ${message}</p>
            </div>
        `;
    }
}

// Export for use in other modules
window.ModularGallery = ModularGallery;
