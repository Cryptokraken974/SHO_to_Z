/**
 * Modal Components
 */

/**
 * File Selection Modal
 */
window.componentManager.register('file-modal', (props = {}) => {
    const { title = 'Select Region' } = props;
    
    return `
        <div id="file-modal" class="modal fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center hidden z-50">
            <div class="modal-content bg-[#2c2c2c] p-6 rounded-lg shadow-xl w-full max-w-lg max-h-[80vh] flex flex-col">
                <div class="flex justify-between items-center mb-4">
                    <h4 class="text-white text-lg font-semibold m-0">${title}</h4>
                    <button class="modal-close text-gray-400 hover:text-white text-2xl leading-none">&times;</button>
                </div>
                <div class="mb-4">
                    <input type="text" id="file-search-input" placeholder="Search files..." class="w-full bg-[#262626] border border-[#404040] rounded-lg px-3 py-2 text-white placeholder-[#ababab] focus:outline-none focus:border-[#00bfff]">
                </div>
                <div class="file-list max-h-[400px] overflow-y-auto" id="file-list">
                    <!-- Files will be populated here -->
                </div>
                <div class="flex justify-between gap-3 mt-4">
                    <button id="delete-region-btn" class="px-4 py-2 bg-[#dc3545] hover:bg-[#c82333] text-white rounded-lg font-medium transition-colors hidden">Delete Region</button>
                    <div class="flex gap-3">
                        <button id="cancel-select" class="cancel-btn bg-[#666] hover:bg-[#555] text-white px-4 py-2 rounded-lg font-medium transition-colors">Cancel</button>
                        <button id="confirm-region-selection" class="px-6 py-2.5 bg-[#007bff] hover:bg-[#0056b3] text-white rounded-lg font-medium transition-colors">Select Region</button>
                    </div>
                </div>
            </div>
        </div>
    `;
}, {
    onRender: (element) => {
        setupFileModal(element);
    }
});

/**
 * Progress Modal
 */
window.componentManager.register('progress-modal', (props = {}) => {
    const { 
        title = 'Processing...',
        status = 'Initializing...',
        showCancel = true 
    } = props;
    
    return `
        <div id="progress-modal" class="modal hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
            <div class="modal-content bg-[#1a1a1a] border border-[#303030] rounded-lg w-[90%] max-w-md">
                <div class="modal-header flex justify-between items-center p-6 border-b border-[#303030]">
                    <h3 class="text-white text-lg font-semibold" id="progress-title">${title}</h3>
                    <button class="close text-[#ababab] hover:text-white text-xl font-bold" id="progress-close">&times;</button>
                </div>
                <div class="modal-body p-6">
                    <div class="text-white mb-4" id="progress-status">${status}</div>
                    <div class="w-full bg-[#303030] rounded-full h-2 mb-4">
                        <div class="bg-[#00bfff] h-2 rounded-full transition-all duration-300" id="progress-bar" style="width: 0%"></div>
                    </div>
                    <div class="text-[#ababab] text-sm" id="progress-details"></div>
                </div>
                ${showCancel ? `
                    <div class="modal-footer flex justify-end gap-3 p-6 border-t border-[#303030]">
                        <button id="cancel-progress" class="cancel-btn bg-[#dc3545] hover:bg-[#c82333] text-white px-4 py-2 rounded-lg font-medium transition-colors">Cancel</button>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}, {
    onRender: (element) => {
        setupProgressModal(element);
    }
});

function setupFileModal(container) {
    const modal = container.querySelector('#file-modal');
    const closeBtn = container.querySelector('.modal-close');
    const cancelBtn = container.querySelector('#cancel-select');
    
    // Close modal handlers
    [closeBtn, cancelBtn].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                modal.classList.add('hidden');
            });
        }
    });
    
    // Close on backdrop click
    modal?.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });
}

function setupProgressModal(container) {
    const modal = container.querySelector('#progress-modal');
    const closeBtn = container.querySelector('#progress-close');
    
    // Close modal handler
    closeBtn?.addEventListener('click', () => {
        modal.classList.add('hidden');
    });
}
