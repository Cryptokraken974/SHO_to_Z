/**
 * Component Utilities and Demo Functions
 * Shows how to use the component system for dynamic updates
 */

/**
 * Update sidebar with new region selection
 */
function updateSelectedRegion(regionName) {
    window.componentManager.update('sidebar', { selectedRegion: regionName });
}

/**
 * Update gallery with custom items
 */
function updateGallery(customItems) {
    window.componentManager.update('gallery', { items: customItems });
}

/**
 * Show/hide modals using component system
 */
function showFileModal() {
    const modal = window.componentManager.getElement('file-modal');
    if (modal) {
        modal.querySelector('#file-modal').classList.remove('hidden');
    }
}

function hideFileModal() {
    const modal = window.componentManager.getElement('file-modal');
    if (modal) {
        modal.querySelector('#file-modal').classList.add('hidden');
    }
}

function showProgressModal(title = 'Processing...', status = 'Initializing...') {
    window.componentManager.update('progress-modal', { title, status });
    const modal = window.componentManager.getElement('progress-modal');
    if (modal) {
        modal.querySelector('#progress-modal').classList.remove('hidden');
    }
}

function hideProgressModal() {
    const modal = window.componentManager.getElement('progress-modal');
    if (modal) {
        modal.querySelector('#progress-modal').classList.add('hidden');
    }
}

/**
 * Update progress bar
 */
function updateProgress(percentage, status = null, details = null) {
    const modal = window.componentManager.getElement('progress-modal');
    if (modal) {
        const progressBar = modal.querySelector('#progress-bar');
        const statusEl = modal.querySelector('#progress-status');
        const detailsEl = modal.querySelector('#progress-details');
        
        if (progressBar) progressBar.style.width = `${percentage}%`;
        if (status && statusEl) statusEl.textContent = status;
        if (details && detailsEl) detailsEl.textContent = details;
    }
}

/**
 * Add chat message
 */
function addChatMessage(message, isUser = false) {
    const chat = window.componentManager.getElement('chat');
    if (chat) {
        const chatLog = chat.querySelector('#chat-log');
        const messageEl = document.createElement('div');
        messageEl.className = `p-2 rounded-lg ${isUser ? 'bg-[#007bff] text-white ml-8' : 'bg-[#262626] text-[#ababab] mr-8'}`;
        messageEl.textContent = message;
        chatLog.appendChild(messageEl);
        chatLog.scrollTop = chatLog.scrollHeight;
    }
}

/**
 * Demo function to show component capabilities
 */
function demoComponentSystem() {
    console.log('=== Component System Demo ===');
    
    // 1. Update sidebar with a selected region
    setTimeout(() => {
        console.log('1. Updating sidebar with selected region...');
        updateSelectedRegion('Demo Region Selected');
    }, 1000);
    
    // 2. Show progress modal
    setTimeout(() => {
        console.log('2. Showing progress modal...');
        showProgressModal('Demo Processing', 'Starting demo...');
    }, 2000);
    
    // 3. Update progress
    setTimeout(() => {
        console.log('3. Updating progress to 25%...');
        updateProgress(25, 'Processing terrain data...', 'Analyzing elevation points');
    }, 3000);
    
    setTimeout(() => {
        console.log('4. Updating progress to 75%...');
        updateProgress(75, 'Generating visualizations...', 'Creating hillshade renders');
    }, 4000);
    
    setTimeout(() => {
        console.log('5. Completing demo...');
        updateProgress(100, 'Complete!', 'All processing finished');
        setTimeout(() => hideProgressModal(), 1000);
    }, 5000);
    
    // 6. Add chat messages
    setTimeout(() => {
        console.log('6. Adding chat messages...');
        addChatMessage('Demo: Component system is working!', false);
        addChatMessage('This is a user message example', true);
    }, 6000);
    
    // 7. Update gallery with custom items
    setTimeout(() => {
        console.log('7. Updating gallery with custom items...');
        const customGalleryItems = [
            { id: 'demo1', label: 'Demo Item 1', target: 'demo1' },
            { id: 'demo2', label: 'Demo Item 2', target: 'demo2' }
        ];
        updateGallery(customGalleryItems);
    }, 7000);
    
    console.log('Demo sequence initiated. Watch the components update!');
}

// Export functions for global access
window.componentUtils = {
    updateSelectedRegion,
    updateGallery,
    showFileModal,
    hideFileModal,
    showProgressModal,
    hideProgressModal,
    updateProgress,
    addChatMessage,
    demoComponentSystem
};

// Auto-run demo if in development mode
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('Component utilities loaded. Run demoComponentSystem() to see the system in action!');
}
