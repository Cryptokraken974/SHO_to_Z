// GeoTiff Tools Left Panel JavaScript
class GeoTiffLeftPanel {
    constructor() {
        this.selectedFile = null;
        this.fileTree = [];
        this.selectedLazFiles = [];
        this.selectedLazFolders = [];
        this.fileModalLoading = false;
        this.folderModalLoading = false;
        this.lazModalEventsSetup = false;
        this.lazFolderModalEventsSetup = false;
        this.init();
    }

    init() {
        console.log('🔧 Initializing GeoTiff Left Panel');
        this.setupEventListeners();
        this.loadFileTree();
    }

    setupEventListeners() {
        // Refresh file tree button
        const refreshBtn = document.getElementById('refresh-files-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadFileTree());
        }

        // Tool action buttons
        const toolButtons = document.querySelectorAll('.geotiff-tool-btn');
        toolButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleToolAction(e.target.dataset.tool));
        });

        // File upload
        const uploadBtn = document.getElementById('upload-geotiff-btn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => this.handleFileUpload());
        }

        // LAZ file loader
        const loadLazBtn = document.getElementById('load-laz-btn');
        if (loadLazBtn) {
            loadLazBtn.addEventListener('click', () => {
                // Prevent double-clicks while modal is loading
                if (this.fileModalLoading) {
                    console.log('📂 File modal already loading, ignoring click');
                    return;
                }
                this.fileModalLoading = true;
                
                this.openLazFileModal().finally(() => {
                    // Reset loading flag after a delay
                    setTimeout(() => {
                        this.fileModalLoading = false;
                    }, 1000);
                });
            });
        }

        // LAZ folder loader
        const loadLazFolderBtn = document.getElementById('load-laz-folder-btn');
        if (loadLazFolderBtn) {
            loadLazFolderBtn.addEventListener('click', () => {
                // Prevent double-clicks while modal is loading
                if (this.folderModalLoading) {
                    console.log('📂 Folder modal already loading, ignoring click');
                    return;
                }
                this.folderModalLoading = true;
                
                this.openLazFolderModal().finally(() => {
                    // Reset loading flag after a delay
                    setTimeout(() => {
                        this.folderModalLoading = false;
                    }, 1000);
                });
            });
        }

        // Setup LAZ modal events
        this.setupLazModalEvents();
        this.setupLazFolderModalEvents();
    }

    async loadFileTree() {
        console.log('📂 Loading GeoTiff file tree');
        try {
            const response = await geotiff().listGeotiffFiles();
            this.fileTree = response;
            this.renderFileTree();
        } catch (error) {
            console.error('Error loading file tree:', error);
            this.showError('Error loading file tree');
        }
    }

    renderFileTree() {
        const container = document.getElementById('geotiff-file-tree');
        if (!container) return;

        if (!this.fileTree || this.fileTree.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-[#666]">
                    <div class="text-4xl mb-4">📁</div>
                    <p>No GeoTiff files found</p>
                    <p class="text-xs mt-2">Upload some .tif or .tiff files to get started</p>
                </div>
            `;
            return;
        }

        let html = '';
        this.fileTree.forEach(item => {
            if (item.type === 'folder') {
                html += this.renderFolder(item);
            } else {
                html += this.renderFile(item);
            }
        });

        container.innerHTML = html;
        this.attachFileTreeEvents();
    }

    renderFolder(folder) {
        return `
            <div class="file-tree-item folder" data-path="${folder.path}">
                <span class="icon">📁</span>
                <span class="name">${folder.name}</span>
                <span class="count ml-auto text-xs text-[#666]">(${folder.fileCount || 0})</span>
            </div>
        `;
    }

    renderFile(file) {
        const isSelected = this.selectedFile === file.path;
        const sizeFormatted = this.formatFileSize(file.size);
        const icon = this.getFileIcon(file.name);
        
        return `
            <div class="file-tree-item file ${isSelected ? 'selected' : ''}" 
                 data-path="${file.path}" 
                 data-type="file">
                <span class="icon">${icon}</span>
                <span class="name">${file.name}</span>
                <span class="size ml-auto text-xs text-[#666]">${sizeFormatted}</span>
            </div>
        `;
    }

    getFileIcon(filename) {
        const ext = filename.toLowerCase().split('.').pop();
        switch (ext) {
            case 'tif':
            case 'tiff':
                return '🗺️';
            case 'png':
                return '🖼️';
            case 'jpg':
            case 'jpeg':
                return '📸';
            default:
                return '📄';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    attachFileTreeEvents() {
        const fileItems = document.querySelectorAll('.file-tree-item[data-type="file"]');
        fileItems.forEach(item => {
            item.addEventListener('click', () => this.selectFile(item.dataset.path));
        });

        const folderItems = document.querySelectorAll('.file-tree-item.folder');
        folderItems.forEach(item => {
            item.addEventListener('click', () => this.toggleFolder(item.dataset.path));
        });
    }

    selectFile(filePath) {
        console.log('📄 Selecting file:', filePath);
        
        // Update visual selection
        document.querySelectorAll('.file-tree-item').forEach(item => {
            item.classList.remove('selected');
        });
        document.querySelector(`[data-path="${filePath}"]`).classList.add('selected');
        
        this.selectedFile = filePath;
        this.updateToolButtons();
        this.updateFileInfo();
        
        // Notify main canvas
        if (window.geoTiffMainCanvas) {
            this.loadFileMetadata(filePath);
        }
    }

    updateToolButtons() {
        const hasSelection = !!this.selectedFile;
        const buttons = document.querySelectorAll('.geotiff-tool-btn');
        
        buttons.forEach(btn => {
            const requiresFile = btn.dataset.requiresFile === 'true';
            btn.disabled = requiresFile && !hasSelection;
        });
    }

    async handleToolAction(toolType) {
        if (!this.selectedFile && document.querySelector(`[data-tool="${toolType}"]`).dataset.requiresFile === 'true') {
            this.showError('Please select a file first');
            return;
        }

        console.log('🔧 Executing tool:', toolType, 'on file:', this.selectedFile);

        try {
            switch (toolType) {
                case 'info':
                    await this.showFileInfo();
                    break;
                case 'convert':
                    await this.convertFile();
                    break;
                case 'preview':
                    await this.previewFile();
                    break;
                case 'compress':
                    await this.compressFile();
                    break;
                case 'crop':
                    await this.cropFile();
                    break;
                case 'resample':
                    await this.resampleFile();
                    break;
                case 'merge':
                    await this.mergeFiles();
                    break;
                default:
                    console.warn('Unknown tool type:', toolType);
            }
        } catch (error) {
            console.error('Tool execution error:', error);
            this.showError(`Error executing ${toolType}: ${error.message}`);
        }
    }

    async showFileInfo() {
        if (window.geoTiffMainCanvas) {
            window.geoTiffMainCanvas.showFileInfo(this.selectedFile);
        }
    }

    async convertFile() {
        if (window.geoTiffMainCanvas) {
            window.geoTiffMainCanvas.showConversionDialog(this.selectedFile);
        }
    }

    async previewFile() {
        if (window.geoTiffMainCanvas) {
            window.geoTiffMainCanvas.previewFile(this.selectedFile);
        }
    }

    async compressFile() {
        // Note: Compression functionality not available in geotiff_service.py
        this.showError('Compression functionality is not currently available');
        // const result = await geotiff().compressGeotiff(this.selectedFile);
        // this.showSuccess(`File compressed successfully. New size: ${this.formatFileSize(result.newSize)}`);
        // this.loadFileTree(); // Refresh to show new file
    }

    async cropFile() {
        if (window.geoTiffMainCanvas) {
            window.geoTiffMainCanvas.showCropDialog(this.selectedFile);
        }
    }

    async resampleFile() {
        if (window.geoTiffMainCanvas) {
            window.geoTiffMainCanvas.showResampleDialog(this.selectedFile);
        }
    }

    async mergeFiles() {
        if (window.geoTiffMainCanvas) {
            window.geoTiffMainCanvas.showMergeDialog();
        }
    }

    handleFileUpload() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.tif,.tiff,.geotiff';
        input.multiple = true;
        
        input.onchange = async (e) => {
            const files = Array.from(e.target.files);
            if (files.length === 0) return;

            try {
                // Note: Upload functionality not available in geotiff_service.py
                this.showError('Upload functionality is not currently available through the service');
                // const result = await geotiff().uploadGeotiffFiles(files);
                // this.showSuccess(`Uploaded ${result.uploadedCount} file(s) successfully`);
                // this.loadFileTree();
            } catch (error) {
                this.showError(`Upload error: ${error.message}`);
            }
        };

        input.click();
    }

    showError(message) {
        console.error('❌', message);
        // You can integrate with a toast notification system here
        if (window.showToast) {
            window.showToast(message, 'error');
        } else {
            alert('Error: ' + message);
        }
    }

    showSuccess(message) {
        console.log('✅', message);
        // You can integrate with a toast notification system here
        if (window.showToast) {
            window.showToast(message, 'success');
        } else {
            alert('Success: ' + message);
        }
    }

    updateFileInfo() {
        const infoPanel = document.getElementById('geotiff-file-info-content');
        if (!infoPanel) return;

        if (!this.selectedFile) {
            infoPanel.innerHTML = '<p class="text-[#666] text-sm">No file selected</p>';
            return;
        }

        // Find file in tree to get basic info
        const fileInfo = this.findFileInTree(this.selectedFile);
        if (!fileInfo) {
            infoPanel.innerHTML = '<p class="text-[#666] text-sm">File information not available</p>';
            return;
        }

        infoPanel.innerHTML = `
            <div class="file-info-item">
                <span class="font-medium">Name:</span>
                <span class="text-[#666]">${fileInfo.name}</span>
            </div>
            <div class="file-info-item">
                <span class="font-medium">Size:</span>
                <span class="text-[#666]">${this.formatFileSize(fileInfo.size)}</span>
            </div>
            <div class="file-info-item">
                <span class="font-medium">Path:</span>
                <span class="text-[#666] text-xs">${this.selectedFile}</span>
            </div>
            <div class="file-info-item">
                <span class="font-medium">Type:</span>
                <span class="text-[#666]">${this.getFileType(fileInfo.name)}</span>
            </div>
            <div id="detailed-metadata" class="mt-3">
                <div class="loading-indicator text-sm text-[#666]">Loading metadata...</div>
            </div>
        `;
    }

    async loadFileMetadata(filePath) {
        if (!window.geoTiffMainCanvas) {
            console.warn('GeoTiff main canvas not available');
            return;
        }

        try {
            console.log('📊 Loading metadata for:', filePath);
            
            // Load metadata via main canvas
            await window.geoTiffMainCanvas.loadFile(filePath);
            
            // Update detailed metadata in info panel
            const metadata = await geotiff().getGeotiffMetadata(filePath);
            this.updateDetailedMetadata(metadata);
        } catch (error) {
            console.error('Error loading file metadata:', error);
            const metadataDiv = document.getElementById('detailed-metadata');
            if (metadataDiv) {
                metadataDiv.innerHTML = '<p class="text-red-500 text-sm">Failed to load metadata</p>';
            }
        }
    }

    updateDetailedMetadata(metadata) {
        const metadataDiv = document.getElementById('detailed-metadata');
        if (!metadataDiv || !metadata) return;

        let metadataHtml = '<div class="text-sm"><strong>Metadata:</strong></div>';
        
        if (metadata.width && metadata.height) {
            metadataHtml += `
                <div class="file-info-item">
                    <span class="font-medium">Dimensions:</span>
                    <span class="text-[#666]">${metadata.width} × ${metadata.height}</span>
                </div>
            `;
        }
        
        if (metadata.bands) {
            metadataHtml += `
                <div class="file-info-item">
                    <span class="font-medium">Bands:</span>
                    <span class="text-[#666]">${metadata.bands}</span>
                </div>
            `;
        }
        
        if (metadata.dataType) {
            metadataHtml += `
                <div class="file-info-item">
                    <span class="font-medium">Data Type:</span>
                    <span class="text-[#666]">${metadata.dataType}</span>
                </div>
            `;
        }
        
        if (metadata.crs) {
            metadataHtml += `
                <div class="file-info-item">
                    <span class="font-medium">CRS:</span>
                    <span class="text-[#666] text-xs">${metadata.crs}</span>
                </div>
            `;
        }

        metadataDiv.innerHTML = metadataHtml;
    }

    findFileInTree(filePath) {
        const findInLevel = (items) => {
            for (const item of items) {
                if (item.path === filePath) {
                    return item;
                }
                if (item.children) {
                    const found = findInLevel(item.children);
                    if (found) return found;
                }
            }
            return null;
        };
        
        return findInLevel(this.fileTree);
    }

    getFileType(filename) {
        const ext = filename.toLowerCase().split('.').pop();
        switch (ext) {
            case 'tif':
            case 'tiff':
                return 'GeoTIFF';
            case 'png':
                return 'PNG Image';
            case 'jpg':
            case 'jpeg':
                return 'JPEG Image';
            default:
                return 'Unknown';
        }
    }

    getSelectedFile() {
        return this.selectedFile;
    }

    refreshFileTree() {
        this.loadFileTree();
    }

    setupLazModalEvents() {
        // Prevent setting up events multiple times
        if (this.lazModalEventsSetup) {
            console.log('📂 LAZ modal events already set up, skipping...');
            return;
        }

        console.log('📂 Setting up LAZ modal events...');
        
        const modal = document.getElementById('laz-file-modal');
        const closeBtn = document.getElementById('laz-modal-close');
        const cancelBtn = document.getElementById('cancel-laz-modal');
        const browseBtn = document.getElementById('browse-laz-btn');
        const fileInput = document.getElementById('laz-file-input');
        const dropZone = document.getElementById('laz-drop-zone');
        const clearBtn = document.getElementById('clear-laz-files');
        const loadBtn = document.getElementById('load-laz-files');

        // Remove any existing event listeners first to prevent duplicates
        [closeBtn, cancelBtn, browseBtn, clearBtn, loadBtn].forEach(btn => {
            if (btn) {
                // Clone the element to remove all event listeners
                const newBtn = btn.cloneNode(true);
                btn.parentNode.replaceChild(newBtn, btn);
            }
        });

        // Re-get elements after cloning
        const modal2 = document.getElementById('laz-file-modal');
        const closeBtn2 = document.getElementById('laz-modal-close');
        const cancelBtn2 = document.getElementById('cancel-laz-modal');
        const browseBtn2 = document.getElementById('browse-laz-btn');
        const fileInput2 = document.getElementById('laz-file-input');
        const dropZone2 = document.getElementById('laz-drop-zone');
        const clearBtn2 = document.getElementById('clear-laz-files');
        const loadBtn2 = document.getElementById('load-laz-files');

        // Close modal events - use unique handler to prevent conflicts
        [closeBtn2, cancelBtn2].forEach(btn => {
            if (btn) {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.closeLazFileModal();
                });
            }
        });

        // Click outside modal to close
        if (modal2) {
            modal2.addEventListener('click', (e) => {
                if (e.target === modal2) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.closeLazFileModal();
                }
            });
        }

        // Browse button - prevent conflicts with drop zone
        if (browseBtn2 && fileInput2) {
            console.log('📂 Setting up browse button event listener...');
            browseBtn2.addEventListener('click', (e) => {
                // Don't prevent default for browse button - let it work naturally
                e.stopPropagation(); // Still stop propagation to prevent conflicts
                console.log('📂 Browse button clicked, opening file dialog...');
                console.log('📂 File input element:', fileInput2);
                console.log('📂 File input type:', fileInput2.type);
                console.log('📂 File input accept:', fileInput2.accept);
                try {
                    fileInput2.click();
                    console.log('📂 File input click() called successfully');
                } catch (error) {
                    console.error('📂 Error calling fileInput.click():', error);
                }
            });
            console.log('📂 Browse button event listener set up successfully');
        } else {
            console.error('📂 Browse button or file input not found!', {
                browseBtn: browseBtn2,
                fileInput: fileInput2
            });
        }

        // File input change - this is the critical event
        if (fileInput2) {
            fileInput2.addEventListener('change', (e) => {
                console.log('📂 File input changed, files selected:', e.target.files.length);
                if (e.target.files.length > 0) {
                    this.handleLazFileSelection(e.target.files);
                }
            });
        }

        // Drag and drop events
        if (dropZone2) {
            dropZone2.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone2.classList.add('border-[#00bfff]');
            });

            dropZone2.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone2.classList.remove('border-[#00bfff]');
            });

            dropZone2.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone2.classList.remove('border-[#00bfff]');
                console.log('📂 Files dropped, processing...');
                this.handleLazFileSelection(e.dataTransfer.files);
            });

            // Click on drop zone to browse - but prevent conflicts with browse button
            dropZone2.addEventListener('click', (e) => {
                // Only trigger if clicking directly on the drop zone text, not on the button
                if (e.target === dropZone2 || (e.target.classList.contains('text-lg') && e.target.textContent.includes('Drop LAZ files'))) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('📂 Drop zone clicked, opening file dialog...');
                    if (fileInput2) fileInput2.click();
                }
            });
        }

        // Clear files button
        if (clearBtn2) {
            clearBtn2.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearLazFiles();
            });
        }

        // Load files button
        if (loadBtn2) {
            loadBtn2.addEventListener('click', (e) => {
                e.preventDefault();
                this.loadLazFiles();
            });
        }

        // Mark as set up to prevent duplicates
        this.lazModalEventsSetup = true;
        console.log('📂 LAZ modal events setup complete');
    }

    async openLazFileModal(clear = true) { // Made async
        console.log('📂 Opening LAZ file browser modal, clear =', clear);
        console.log('📂 Current selectedLazFiles before modal open:', this.selectedLazFiles ? this.selectedLazFiles.length : 'undefined');

        // Check if modal is already loaded and visible to prevent double loading
        const existingModal = document.getElementById('laz-file-modal');
        if (existingModal && !existingModal.classList.contains('hidden')) {
            console.log('📂 Modal already open, skipping reload');
            return;
        }

        // Store current files before potentially losing them during modal reload
        const currentFiles = this.selectedLazFiles ? [...this.selectedLazFiles] : [];
        console.log('📂 Stored current files for preservation:', currentFiles.length);

        // Load the modal HTML first into the placeholder
        // Ensure loadModule is globally accessible (defined in app_new.js)
        await loadModule('modules/modals/laz-file-modal.html', 'modals-placeholder');

        // Restore files after modal reload if we weren't supposed to clear
        if (!clear && currentFiles.length > 0) {
            this.selectedLazFiles = currentFiles;
            console.log('📂 Restored files after modal reload:', this.selectedLazFiles.length);
        }

        const modal = document.getElementById('laz-file-modal'); // Get from placeholder after loading
        if (modal) {
            console.log('📂 Modal found, setting up events...');
            
            // Reset the flag to allow re-setup since modal was reloaded
            this.lazModalEventsSetup = false;
            
            // Call setup for its internal events AFTER it's in the DOM
            this.setupLazModalEvents(); // This function binds events to elements within #laz-file-modal

            // Add a small delay to ensure DOM is fully ready
            setTimeout(() => {
                const browseBtn = document.getElementById('browse-laz-btn');
                const fileInput = document.getElementById('laz-file-input');
                console.log('📂 After setup - Browse button:', browseBtn);
                console.log('📂 After setup - File input:', fileInput);
                
                // Test the browse button functionality
                if (browseBtn && fileInput) {
                    console.log('📂 Browse button and file input are accessible');
                } else {
                    console.error('📂 Browse button or file input not found after setup!');
                }
            }, 100);

            modal.classList.remove('hidden'); // Show the modal
            $(modal).fadeIn(); // Or use jQuery if preferred for consistency

            if (clear) {
                console.log('📂 Clearing files as requested (clear = true)');
                // Reset modal state
                this.clearLazFiles(); // This updates elements within #laz-file-modal
            } else {
                console.log('📂 Preserving files as requested (clear = false), current count:', this.selectedLazFiles ? this.selectedLazFiles.length : 0);
            }

            // If UIManager has a generic modal re-initializer, call it.
            // This is mainly for standard close buttons or behaviors.
            if (window.UIManager && typeof window.UIManager.reinitializeModalEventHandlers === 'function') {
                window.UIManager.reinitializeModalEventHandlers('#laz-file-modal');
            }
        } else {
            console.error('LAZ File Modal not found after loading.');
        }
    }

    closeLazFileModal() {
        console.log('📂 Closing LAZ file browser modal');
        const modal = document.getElementById('laz-file-modal'); // Target directly if it's always unique
                                                                    // Or use '#modals-placeholder #laz-file-modal'
        if (modal) {
            // modal.classList.add('hidden');
            $(modal).fadeOut(() => {
                 // Optional: if modals-placeholder should only hold one modal at a time
                // $('#modals-placeholder').empty();
            });
            // Clear any selected files
            this.clearLazFiles();
        }
    }

    /* removed duplicate earlier implementation of LAZ folder modal events */

    handleLazFileSelection(files) {
        console.log('📁 LAZ files selected:', files.length);
        
        // Filter for LAZ/LAS files only
        const lazFiles = Array.from(files).filter(file => {
            const ext = file.name.toLowerCase().split('.').pop();
            return ext === 'laz' || ext === 'las';
        });

        if (lazFiles.length === 0) {
            this.showError('Please select valid LAZ or LAS files');
            return;
        }

        if (lazFiles.length !== files.length) {
            this.showError(`${files.length - lazFiles.length} files were skipped (only LAZ/LAS files are supported)`);
        }

        // Store selected files
        this.selectedLazFiles = lazFiles;
        
        // Update UI
        this.updateLazFilesList();
        this.updateLoadButton();
    }

    updateLazFilesList() {
        const filesList = document.getElementById('laz-files-list');
        if (!filesList) return;

        if (!this.selectedLazFiles || this.selectedLazFiles.length === 0) {
            filesList.innerHTML = '<div class="text-[#666] text-sm text-center py-4">No files selected</div>';
            return;
        }

        const filesHtml = this.selectedLazFiles.map((file, index) => `
            <div class="flex items-center justify-between bg-[#1a1a1a] p-3 rounded-lg border border-[#404040]">
                <div class="flex items-center gap-3">
                    <i class="fas fa-file-archive text-[#8e44ad]"></i>
                    <div>
                        <div class="text-white text-sm font-medium">${file.name}</div>
                        <div class="text-[#ababab] text-xs">${this.formatFileSize(file.size)}</div>
                    </div>
                </div>
                <button class="remove-laz-file text-[#dc3545] hover:text-[#c82333] p-1" data-index="${index}">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');

        filesList.innerHTML = filesHtml;

        // Add remove file event listeners
        filesList.querySelectorAll('.remove-laz-file').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.currentTarget.dataset.index);
                this.removeLazFile(index);
            });
        });
    }

    removeLazFile(index) {
        if (this.selectedLazFiles && index >= 0 && index < this.selectedLazFiles.length) {
            this.selectedLazFiles.splice(index, 1);
            this.updateLazFilesList();
            this.updateLoadButton();
        }
    }

    clearLazFiles() {
        console.log('📂 clearLazFiles called - clearing', this.selectedLazFiles ? this.selectedLazFiles.length : 0, 'files');
        console.trace('📂 clearLazFiles call stack'); // This will show us where it's being called from
        
        this.selectedLazFiles = [];
        this.updateLazFilesList();
        this.updateLoadButton();
        
        // Reset file input
        const fileInput = document.getElementById('laz-file-input');
        if (fileInput) {
            fileInput.value = '';
        }
    }

    updateLoadButton() {
        const loadBtn = document.getElementById('load-laz-files');
        if (loadBtn) {
            const hasFiles = this.selectedLazFiles && this.selectedLazFiles.length > 0;
            loadBtn.disabled = !hasFiles;
        }
    }

    // ---------- Folder Modal Logic ----------

    static countLazFilesByFolder(fileList) {
        const counts = {};
        Array.from(fileList).forEach(file => {
            const ext = file.name.toLowerCase().split('.').pop();
            if (ext !== 'laz') return;
            const rel = file.webkitRelativePath || file.name;
            const folder = rel.split('/')[0];
            counts[folder] = (counts[folder] || 0) + 1;
        });
        return counts;
    }

    setupLazFolderModalEvents() {
        // Prevent setting up events multiple times
        if (this.lazFolderModalEventsSetup) {
            console.log('📂 LAZ folder modal events already set up, skipping...');
            return;
        }

        console.log('📂 Setting up LAZ folder modal events...');

        const modal = document.getElementById('laz-folder-modal');
        const closeBtn = document.getElementById('laz-folder-modal-close');
        const cancelBtn = document.getElementById('cancel-laz-folder-modal');
        const browseBtn = document.getElementById('browse-laz-folder-btn');
        const folderInput = document.getElementById('laz-folder-input');
        const dropZone = document.getElementById('laz-folder-drop-zone');
        const clearBtn = document.getElementById('clear-laz-folders');
        const doneBtn = document.getElementById('done-laz-folder');

        [closeBtn, cancelBtn].forEach(btn => {
            if (btn) btn.addEventListener('click', () => this.closeLazFolderModal());
        });

        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.closeLazFolderModal();
            });
        }

        if (browseBtn) {
            browseBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                console.log('📂 Folder browse button clicked');
                if (folderInput) {
                    folderInput.click();
                }
            });
        }

        if (folderInput) {
            folderInput.addEventListener('change', (e) => {
                console.log('📂 Folder input changed, files found:', e.target.files.length);
                this.handleLazFolderSelection(e.target.files);
            });
        }

        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('border-[#5e60ce]');
            });
            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.classList.remove('border-[#5e60ce]');
            });
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('border-[#5e60ce]');
                this.handleLazFolderSelection(e.dataTransfer.files);
            });

            dropZone.addEventListener('click', (e) => {
                if (e.target === dropZone || (e.target.closest('#laz-folder-drop-zone') && !e.target.closest('#browse-laz-folder-btn'))) {
                    if (folderInput) folderInput.click();
                }
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearLazFolders());
        }

        if (doneBtn) {
            doneBtn.addEventListener('click', () => {
                const hasFiles = this.selectedLazFiles && this.selectedLazFiles.length > 0;
                console.log('📂 Done button clicked, has files:', hasFiles);
                console.log('📂 Selected LAZ files before transition:', this.selectedLazFiles);
                console.log('📂 Selected LAZ files count:', this.selectedLazFiles ? this.selectedLazFiles.length : 'undefined');
                
                // Capture NDVI setting from folder modal
                const folderNdviCheckbox = document.getElementById('laz-folder-ndvi-enabled');
                const folderNdviEnabled = folderNdviCheckbox ? folderNdviCheckbox.checked : false;
                console.log('📂 Folder NDVI enabled:', folderNdviEnabled);
                
                // Store files temporarily to ensure they persist
                const filesToTransfer = this.selectedLazFiles ? [...this.selectedLazFiles] : [];
                console.log('📂 Files to transfer:', filesToTransfer.length);
                
                this.closeLazFolderModal();
                
                if (hasFiles && filesToTransfer.length > 0) {
                    // Ensure files are restored after folder modal closes
                    this.selectedLazFiles = filesToTransfer;
                    console.log('📂 Files restored after folder modal close:', this.selectedLazFiles.length);
                    
                    // Open file modal with pre-selected files and start loading automatically
                    this.openLazFileModal(false).then(() => {
                        console.log('📂 File modal opened, files available:', this.selectedLazFiles ? this.selectedLazFiles.length : 0);
                        
                        // Transfer NDVI setting from folder modal to file modal
                        const fileNdviCheckbox = document.getElementById('laz-ndvi-enabled');
                        if (fileNdviCheckbox) {
                            fileNdviCheckbox.checked = folderNdviEnabled;
                            console.log('📂 Transferred NDVI setting to file modal:', folderNdviEnabled);
                        }
                        
                        this.updateLazFilesList();
                        this.updateLoadButton();
                        
                        // Add a small delay before loading to ensure UI is ready
                        setTimeout(() => {
                            console.log('📂 About to call loadLazFiles, current files:', this.selectedLazFiles ? this.selectedLazFiles.length : 0);
                            this.loadLazFiles();
                        }, 500);
                    });
                } else {
                    this.showError('No LAZ files found in selected folder');
                }
            });
        }

        // Mark as set up to prevent duplicates
        this.lazFolderModalEventsSetup = true;
        console.log('📂 LAZ folder modal events setup complete');
    }

    async openLazFolderModal() { // Made async
        console.log('📂 Opening LAZ Folder browser modal');

        // Check if modal is already loaded and visible to prevent double loading
        const existingModal = document.getElementById('laz-folder-modal');
        if (existingModal && !existingModal.classList.contains('hidden')) {
            console.log('📂 Folder modal already open, skipping reload');
            return;
        }

        // Load the modal HTML first into the placeholder
        await loadModule('modules/modals/laz-folder-modal.html', 'modals-placeholder');

        const modal = document.getElementById('laz-folder-modal'); // Get from placeholder
        if (modal) {
            // Reset the flag to allow re-setup since modal was reloaded
            this.lazFolderModalEventsSetup = false;
            
            // Call setup for its internal events AFTER it's in the DOM
            this.setupLazFolderModalEvents();

            modal.classList.remove('hidden');
            $(modal).fadeIn();

            this.clearLazFolders(); // Reset state

            if (window.UIManager && typeof window.UIManager.reinitializeModalEventHandlers === 'function') {
                window.UIManager.reinitializeModalEventHandlers('#laz-folder-modal');
            }
        } else {
            console.error('LAZ Folder Modal not found after loading.');
        }
    }

    closeLazFolderModal() {
        console.log('📂 Closing LAZ folder modal');
        console.log('📂 selectedLazFiles before closing folder modal:', this.selectedLazFiles ? this.selectedLazFiles.length : 0);
        
        const modal = document.getElementById('laz-folder-modal'); // Target directly or via placeholder
        if (modal) {
            // modal.classList.add('hidden');
            $(modal).fadeOut(() => {
                // $('#modals-placeholder').empty();
            });
            this.clearLazFolders(); // This should only clear folders, not files
        }
        
        console.log('📂 selectedLazFiles after closing folder modal:', this.selectedLazFiles ? this.selectedLazFiles.length : 0);
    }

    handleLazFolderSelection(files) {
        console.log('📂 handleLazFolderSelection called with files:', files ? files.length : 0);
        
        if (!files || files.length === 0) {
            console.log('📂 No files provided to handleLazFolderSelection');
            this.showError('No files selected from folder');
            return;
        }

        console.log('📂 Processing folder selection with', files.length, 'total files');
        
        // Reset arrays
        this.selectedLazFolders = [];
        this.selectedLazFiles = [];
        
        // Count LAZ files by folder
        const counts = GeoTiffLeftPanel.countLazFilesByFolder(files);
        console.log('📂 LAZ files found by folder:', counts);
        
        // Store folder information
        Object.entries(counts).forEach(([folder, count]) => {
            this.selectedLazFolders.push({ name: folder, count });
        });
        
        // Filter and store LAZ files
        this.selectedLazFiles = Array.from(files).filter(f => {
            const isLaz = f.name.toLowerCase().endsWith('.laz');
            if (isLaz) {
                console.log('📂 Found LAZ file:', f.name, 'Size:', f.size);
            }
            return isLaz;
        });
        
        console.log('📂 Total LAZ files selected:', this.selectedLazFiles.length);
        console.log('📂 Selected LAZ files:', this.selectedLazFiles.map(f => f.name));
        
        // Update UI
        this.updateLazFolderList();
    }

    updateLazFolderList() {
        const list = document.getElementById('laz-folders-list');
        if (!list) return;
        if (!this.selectedLazFolders || this.selectedLazFolders.length === 0) {
            list.innerHTML = '<div class="text-[#666] text-sm text-center py-4">No folders selected</div>';
            return;
        }
        const html = this.selectedLazFolders.map(f => `
            <div class="flex items-center justify-between bg-[#1a1a1a] p-3 rounded-lg border border-[#404040]">
                <div class="flex items-center gap-3">
                    <i class="fas fa-folder text-[#5e60ce]"></i>
                    <div class="text-white text-sm font-medium">${f.name}</div>
                </div>
                <div class="text-[#ababab] text-sm">${f.count} .laz files</div>
            </div>
        `).join('');
        list.innerHTML = html;
    }

    clearLazFolders() {
        console.log('📂 clearLazFolders called - clearing folders but preserving selectedLazFiles');
        console.log('📂 selectedLazFiles before clearLazFolders:', this.selectedLazFiles ? this.selectedLazFiles.length : 0);
        
        this.selectedLazFolders = [];
        // NOTE: We intentionally do NOT clear selectedLazFiles here as those should persist
        // this.selectedLazFiles = []; // <- This should NOT be here
        
        const input = document.getElementById('laz-folder-input');
        if (input) input.value = '';
        this.updateLazFolderList();
        
        console.log('📂 selectedLazFiles after clearLazFolders:', this.selectedLazFiles ? this.selectedLazFiles.length : 0);
    }

    async loadLazFiles() {
        const files = this.selectedLazFiles;
        console.log('📂 loadLazFiles called with files:', files ? files.length : 0);
        
        if (!files || files.length === 0) {
            console.log('❌ No files available for loading');
            this.showError('No files selected');
            return;
        }

        console.log('📂 Starting LAZ file loading process for', files.length, 'files');
        files.forEach((file, index) => {
            console.log(`📂 File ${index + 1}: ${file.name} (${file.size} bytes)`);
        });

        try {
            this.showLazProgress(true);
            this.updateLazProgress(0, 'Starting upload...');

            // Capture NDVI checkbox state
            const ndviCheckbox = document.getElementById('laz-ndvi-enabled');
            const ndviEnabled = ndviCheckbox ? ndviCheckbox.checked : false;
            console.log('📂 NDVI enabled:', ndviEnabled);

            const formData = new FormData();
            files.forEach(file => {
                formData.append('files', file);
            });
            
            // Add NDVI parameter to form data
            formData.append('ndvi_enabled', ndviEnabled.toString());

            console.log('📂 Sending files to /api/laz/upload...');
            
            // Upload files and get coordinates
            const response = await fetch('/api/laz/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('📂 LAZ upload result:', result);

            this.updateLazProgress(50, 'Files uploaded, processing coordinates...');

            // Store the loaded files info
            const loadedFiles = result.files || [];
            console.log('📂 Loaded files from server:', loadedFiles);

            this.loadFileTree();

            if (loadedFiles.length > 0 && window.FileManager) {
                for (let i = 0; i < loadedFiles.length; i++) {
                    const fileInfo = loadedFiles[i];
                    const fileName = fileInfo.inputFile;
                    const regionName = fileName.replace(/\.[^/.]+$/, '');

                    console.log(`🎯 Processing uploaded LAZ file as region: ${regionName} (${i + 1}/${loadedFiles.length})`);

                    this.updateLazProgress(100 * (i / loadedFiles.length), `Setting up region ${i + 1} of ${loadedFiles.length}...`);

                    // Set region for processing
                    window.FileManager.selectRegion(
                        regionName,
                        null,
                        regionName,
                        `input/LAZ/${fileName}`
                    );

                    // Wait briefly for region setup
                    await new Promise(resolve => setTimeout(resolve, 1000));

                    this.updateLazProgress(100 * (i / loadedFiles.length), `Generating DTM for ${fileName} (${i + 1}/${loadedFiles.length})`);

                    // Step 1: Generate DTM from LAZ file
                    const dtmSuccess = await this.generateDTMFromLAZ(regionName, fileName);
                    
                    if (!dtmSuccess) {
                        console.warn(`⚠️ DTM generation failed for ${regionName}`);
                        this.updateLazProgress(100 * ((i + 1) / loadedFiles.length), `DTM Failed ${fileName} (${i + 1}/${loadedFiles.length})`);
                        continue; // Skip to next file
                    }

                    this.updateLazProgress(100 * (i / loadedFiles.length), `Processing rasters for ${fileName} (${i + 1}/${loadedFiles.length})`);

                    // Step 2: Reset raster processing queue for new file and show progress UI
                    this.resetLazRasterProcessingQueue();
                    this.showLazRasterProgress(true);

                    const success = await this.processAllRastersWithLazModalProgress();

                    if (success) {
                        console.log(`✅ Completed processing for ${regionName}`);
                        this.updateLazProgress(100 * ((i + 1) / loadedFiles.length), `Completed ${fileName} (${i + 1}/${loadedFiles.length})`);
                    } else {
                        console.warn(`⚠️ Processing failed for ${regionName}`);
                        this.updateLazProgress(100 * ((i + 1) / loadedFiles.length), `Failed ${fileName} (${i + 1}/${loadedFiles.length})`);
                    }
                }

                // Close modal after processing all files
                setTimeout(() => {
                    this.closeLazFileModal();
                }, 3000);

            } else {
                console.warn('⚠️ No files loaded or FileManager unavailable');
                this.updateLazProgress(100, 'Upload complete');
                setTimeout(() => {
                    this.closeLazFileModal();
                }, 2000);
            }

        } catch (error) {
            console.error('LAZ loading error:', error);
            this.showError(`Loading failed: ${error.message}`);
            this.showLazProgress(false);
            // Close modal on error
            setTimeout(() => {
                this.closeLazFileModal();
            }, 3000);
        }
    }

    async generateDTMFromLAZ(regionName, fileName) {
        console.log(`🏔️ Generating DTM for region: ${regionName}, file: ${fileName}`);
        
        try {
            const formData = new FormData();
            formData.append('region_name', regionName);
            formData.append('processing_type', 'lidar'); // or appropriate processing type
            formData.append('dtm_resolution', '1.0');
            formData.append('stretch_type', 'stddev');
            
            // 🎯 ENABLE QUALITY MODE: Trigger density analysis → mask generation → LAZ cropping → clean DTM
            formData.append('quality_mode', 'true');
            console.log(`🌟 Quality mode enabled for DTM generation - will trigger complete quality workflow`);

            const response = await fetch('/api/dtm', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`DTM generation failed: ${response.status} - ${errorText}`);
                return false;
            }

            const result = await response.json();
            console.log(`✅ DTM generated successfully for ${regionName} (quality mode workflow completed)`);
            return true;

        } catch (error) {
            console.error(`❌ DTM generation error for ${regionName}:`, error);
            return false;
        }
    }

    showLazProgress(show) {
        const progressSection = document.getElementById('laz-progress-section');
        if (progressSection) {
            if (show) {
                progressSection.classList.remove('hidden');
            } else {
                progressSection.classList.add('hidden');
            }
        }
    }

    updateLazProgress(percent, status) {
        const progressBar = document.getElementById('laz-progress-bar');
        const progressStatus = document.getElementById('laz-progress-status');
        
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
        }
        
        if (progressStatus) {
            progressStatus.textContent = status;
        }
    }

    /**
     * Show/hide LAZ raster generation progress section
     * @param {boolean} show - Whether to show or hide the progress section
     */
    showLazRasterProgress(show) {
        const progressSection = document.getElementById('laz-raster-progress-section');
        const loadButton = document.getElementById('load-laz-files');
        const cancelButton = document.getElementById('cancel-laz-raster-processing');
        
        if (progressSection) {
            if (show) {
                progressSection.classList.remove('hidden');
                // Hide load button and show cancel button
                if (loadButton) loadButton.classList.add('hidden');
                if (cancelButton) cancelButton.classList.remove('hidden');
            } else {
                progressSection.classList.add('hidden');
                // Show load button and hide cancel button
                if (loadButton) loadButton.classList.remove('hidden');
                if (cancelButton) cancelButton.classList.add('hidden');
            }
        }
    }

    /**
     * Update LAZ modal raster processing step display
     * @param {string} stepName - Name of the current step
     * @param {number} currentIndex - Current step index
     * @param {number} totalSteps - Total number of steps
     */
    updateLazRasterProcessingStep(stepName, currentIndex, totalSteps) {
        const stepEl = document.getElementById('laz-current-processing-step');
        const progressTextEl = document.getElementById('laz-processing-progress-text');
        const progressBarEl = document.getElementById('laz-processing-progress-bar');

        if (stepEl) {
            stepEl.textContent = `Processing ${stepName}...`;
        }

        const progressPercent = Math.round(((currentIndex + 1) / totalSteps) * 100);
        
        if (progressTextEl) {
            progressTextEl.textContent = `${progressPercent}%`;
        }

        if (progressBarEl) {
            progressBarEl.style.width = `${progressPercent}%`;
        }
    }

    /**
     * Update LAZ modal processing queue visual display
     * @param {Array} queue - Processing queue array
     * @param {number} currentIndex - Current processing index
     */
    updateLazRasterProcessingQueue(queue, currentIndex) {
        queue.forEach((process, index) => {
            const queueItem = document.getElementById(`laz-queue-${process.type.replace('_', '-')}`);
            if (queueItem) {
                // Reset classes
                queueItem.className = 'p-2 rounded bg-[#1a1a1a] text-center border-l-2';
                
                if (index < currentIndex) {
                    // Completed
                    queueItem.classList.add('border-green-500', 'bg-green-900', 'bg-opacity-20');
                } else if (index === currentIndex) {
                    // Currently processing
                    queueItem.classList.add('border-yellow-500', 'bg-yellow-900', 'bg-opacity-20', 'animate-pulse');
                } else {
                    // Pending
                    queueItem.classList.add('border-[#666]');
                }
            }
        });
    }

    /**
     * Mark a LAZ modal queue item as complete with status
     * @param {string} processType - Type of processing
     * @param {string} status - Status (success, error)
     */
    markLazQueueItemComplete(processType, status) {
        const queueItem = document.getElementById(`laz-queue-${processType.replace('_', '-')}`);
        if (queueItem) {
            queueItem.className = 'p-2 rounded bg-[#1a1a1a] text-center border-l-2';
            
            if (status === 'success') {
                queueItem.classList.add('border-green-500', 'bg-green-900', 'bg-opacity-20');
            } else if (status === 'error') {
                queueItem.classList.add('border-red-500', 'bg-red-900', 'bg-opacity-20');
            }
        }
    }

    /**
     * Show LAZ raster processing completion summary
     * @param {number} successCount - Number of successful processes
     * @param {Array} failedProcesses - Array of failed process names
     */
    showLazRasterProcessingComplete(successCount, failedProcesses) {
        const statusEl = document.getElementById('laz-raster-status-text');
        if (statusEl) {
            if (failedProcesses.length === 0) {
                statusEl.textContent = `All ${successCount} raster products generated successfully! ✅`;
                statusEl.className = 'text-green-400';
            } else {
                statusEl.textContent = `${successCount} successful, ${failedProcesses.length} failed: ${failedProcesses.join(', ')}`;
                statusEl.className = 'text-yellow-400';
            }
        }
    }

    /**
     * Process all rasters with LAZ modal progress integration and quality mode workflow
     * 
     * QUALITY MODE WORKFLOW:
     * This function implements a comprehensive raster processing pipeline that includes quality mode
     * enhancements for improved LAZ file processing. The workflow consists of three main phases:
     * 
     * PHASE 1: QUALITY MODE PREPROCESSING (New Quality Enhancement Steps)
     * 1. Density Analysis (/api/density/analyze):
     *    - Generates density raster from original LAZ file
     *    - Identifies point cloud density variations across the area
     *    - Creates foundation for artifact detection
     * 
     * 2. Mask Generation (integrated with density analysis):
     *    - Creates binary mask based on density thresholds
     *    - Identifies areas with insufficient point density
     *    - Marks regions that may contain processing artifacts
     * 
     * 3. Quality DTM Preparation:
     *    - Prepares optimized DTM using density insights
     *    - Applies quality-based filtering for cleaner raster generation
     *    - Sets foundation for improved subsequent raster products
     * 
     * PHASE 2: STANDARD RASTER PROCESSING
     * 4-15. Individual raster products (hillshades, slope, aspect, etc.)
     * 16-18. Composite products (RGB hillshade, boosted hillshade)
     * 
     * PHASE 3: VALIDATION & CLEANUP
     * - Validates all generated products
     * - Reports success/failure statistics
     * 
     * KEY DIFFERENCES FROM STANDARD PROCESSING:
     * - Quality mode steps (1-3) are executed FIRST before any standard raster generation
     * - Density analysis provides insights that improve all subsequent processing steps
     * - Binary mask enables artifact-aware processing in later steps
     * - This function is specifically designed for LAZ modal UI integration
     * 
     * INTEGRATION NOTES:
     * - Updates LAZ modal processing queue UI in real-time
     * - Mimics ProcessingManager.processAllRasters() but with quality mode enhancements
     * - Quality mode steps are NOT triggered during standard LAZ file loading
     * - Must be explicitly called through the LAZ modal processing interface
     * 
     * @returns {Promise<boolean>} Success status of the complete processing workflow
     */
    async processAllRastersWithLazModalProgress() {
        // Check prerequisites
        const selectedRegion = window.FileManager?.getSelectedRegion();
        const processingRegion = window.FileManager?.getProcessingRegion();
        const selectedFile = typeof window.FileManager?.getSelectedFile === 'function' ? window.FileManager.getSelectedFile() : null;
        
        if (!selectedRegion && !selectedFile) {
            if (window.Utils) window.Utils.showNotification('Please select a region or LAZ file first', 'warning');
            return false;
        }

        // Define processing queue (matching backend process_all_raster_products)
        const processingQueue = [
            // Quality Mode Steps (First Priority)
            { type: 'density_analysis', name: 'Density Analysis', icon: '🔍' },
            { type: 'mask_generation', name: 'Mask Generation', icon: '🎭' },
            { type: 'quality_dtm', name: 'Quality DTM', icon: '🏔️' },
            // Individual hillshades (from hillshade.json)
            { type: 'hs_red', name: 'HS Red', icon: '🔴' },
            { type: 'hs_green', name: 'HS Green', icon: '🟢' },
            { type: 'hs_blue', name: 'HS Blue', icon: '🔵' },
            // CHM processing (uses separate API endpoint)
            { type: 'chm', name: 'CHM', icon: '🌳' },
            // Other raster products
            { type: 'slope', name: 'Slope', icon: '📐' },
            { type: 'aspect', name: 'Aspect', icon: '🧭' },
            { type: 'color_relief', name: 'Color Relief', icon: '🎨' },
            { type: 'slope_relief', name: 'Slope Relief', icon: '🏔️' },
            { type: 'lrm', name: 'LRM', icon: '📏' },
            { type: 'sky_view_factor', name: 'Sky View Factor', icon: '☀️' },
            // Composite products (generated after individual ones)
            { type: 'hillshade_rgb', name: 'RGB Hillshade', icon: '🌈' },
            { type: 'boosted_hillshade', name: 'Boosted HS', icon: '⚡' }
        ];

        // Initialize variables for tracking processing results
        let successCount = 0;
        let failedProcesses = [];

        try {
            // Reset visual queue indicators for new processing session
            this.resetLazRasterProcessingQueue();
            
            // Initialize LAZ modal progress display
            this.updateLazRasterProcessingQueue(processingQueue, -1);
            
            if (window.Utils) window.Utils.showNotification('Starting raster generation...', 'info');
            
            // Instead of processing each raster individually, call the unified backend processing
            try {
                this.updateLazRasterProcessingStep('Processing All Rasters', 0, processingQueue.length);
                
                // Get region information
                const regionName = processingRegion || selectedRegion;
                const regionPath = window.FileManager?.getRegionPath();
                let lazFileName = regionName + '.laz'; // Default fallback
                
                if (regionPath && regionPath.includes('input/LAZ/')) {
                    // Extract actual filename from path like "input/LAZ/CUI_A01.laz"
                    const pathParts = regionPath.split('/');
                    lazFileName = pathParts[pathParts.length - 1];
                }
                
                console.log(`🚀 Processing all rasters for region: ${regionName}, file: ${lazFileName}`);
                
                // Step 1: Quality Mode Processing - Density Analysis
                console.log('🔍 Processing Density Analysis (Quality Mode Step 1)...');
                this.updateLazRasterProcessingStep('Density Analysis', 0, processingQueue.length);
                this.updateLazRasterProcessingQueue(processingQueue, processingQueue.findIndex(p => p.type === 'density_analysis'));
                
                try {
                    const densityFormData = new FormData();
                    densityFormData.append('laz_file_path', `input/LAZ/${lazFileName}`);
                    densityFormData.append('region_name', regionName);
                    densityFormData.append('resolution', '1.0');
                    densityFormData.append('mask_threshold', '3');
                    densityFormData.append('generate_mask', 'true');
                    
                    const densityResponse = await fetch('/api/density/analyze', {
                        method: 'POST',
                        body: densityFormData
                    });
                    
                    if (densityResponse.ok) {
                        const densityResult = await densityResponse.json();
                        this.markLazQueueItemComplete('density-analysis', 'success');
                        this.markLazQueueItemComplete('mask-generation', 'success'); // Mask is generated together
                        console.log('✅ Density analysis and mask generation completed');
                        
                        // Check if clean LAZ was generated for quality DTM
                        if (densityResult.mask_results && densityResult.mask_results.success) {
                            this.markLazQueueItemComplete('quality-dtm', 'success');
                            console.log('✅ Quality mode activated - clean LAZ available for enhanced processing');
                        } else {
                            this.markLazQueueItemComplete('quality-dtm', 'error');
                            console.log('⚠️ Quality DTM preparation failed - will continue with standard mode');
                        }
                    } else {
                        this.markLazQueueItemComplete('density-analysis', 'error');
                        this.markLazQueueItemComplete('mask-generation', 'error');
                        this.markLazQueueItemComplete('quality-dtm', 'error');
                        console.warn('⚠️ Density analysis failed - continuing with standard mode');
                        failedProcesses.push('Density Analysis', 'Mask Generation', 'Quality DTM');
                    }
                } catch (densityError) {
                    console.error('❌ Density analysis error:', densityError);
                    this.markLazQueueItemComplete('density-analysis', 'error');
                    this.markLazQueueItemComplete('mask-generation', 'error');
                    this.markLazQueueItemComplete('quality-dtm', 'error');
                    failedProcesses.push('Density Analysis', 'Mask Generation', 'Quality DTM');
                }
                
                // Step 2: Process CHM separately first (uses LAZ file directly)
                console.log('🌳 Processing CHM (Canopy Height Model)...');
                this.updateLazRasterProcessingStep('CHM', 3, processingQueue.length);
                this.updateLazRasterProcessingQueue(processingQueue, processingQueue.findIndex(p => p.type === 'chm'));
                
                try {
                    const chmFormData = new FormData();
                    chmFormData.append('region_name', regionName);
                    chmFormData.append('processing_type', 'lidar'); // Required for CHM processing
                    chmFormData.append('stretch_type', 'stddev');
                    
                    const chmResponse = await fetch('/api/chm', {
                        method: 'POST',
                        body: chmFormData
                    });
                    
                    if (chmResponse.ok) {
                        this.markLazQueueItemComplete('chm', 'success');
                        console.log('✅ CHM processing completed');
                    } else {
                        this.markLazQueueItemComplete('chm', 'error');
                        console.warn('⚠️ CHM processing failed');
                        failedProcesses.push('CHM');
                    }
                } catch (chmError) {
                    console.error('❌ CHM processing error:', chmError);
                    this.markLazQueueItemComplete('chm', 'error');
                    failedProcesses.push('CHM');
                }
                
                // Step 3: Process all other rasters using unified backend processing
                console.log('🚀 Processing remaining rasters...');
                this.updateLazRasterProcessingStep('Other Rasters', 4, processingQueue.length);
                
                // Call the unified backend processing endpoint
                const formData = new FormData();
                formData.append('region_name', regionName);
                formData.append('file_name', lazFileName);
                formData.append('display_region_name', this.regionDisplayName || regionName);
                
                const response = await fetch('/api/laz/process-all-rasters', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                
                if (result.success) {
                    // Mark all non-CHM and non-quality-mode processing steps as complete
                    for (let i = 0; i < processingQueue.length; i++) {
                        const process = processingQueue[i];
                        
                        // Skip quality mode steps and CHM as they were already processed
                        if (['density_analysis', 'mask_generation', 'quality_dtm', 'chm'].includes(process.type)) continue;
                        
                        this.markLazQueueItemComplete(process.type.replace('_', '-'), 'success');
                        this.updateLazRasterProcessingStep(process.name, i + 1, processingQueue.length);
                        
                        // Small delay for visual effect
                        if (i < processingQueue.length - 1) {
                            await new Promise(resolve => setTimeout(resolve, 200));
                        }
                    }
                    
                    console.log('✅ All raster processing completed successfully');
                    successCount = processingQueue.length - failedProcesses.length;
                } else {
                    throw new Error('Backend processing failed');
                }
                
            } catch (error) {
                console.error('❌ Unified raster processing failed:', error);
                
                // Mark all non-quality-mode and non-CHM as failed (quality mode and CHM were already handled)
                for (const process of processingQueue) {
                    if (!['density_analysis', 'mask_generation', 'quality_dtm', 'chm'].includes(process.type)) {
                        this.markLazQueueItemComplete(process.type.replace('_', '-'), 'error');
                        if (!failedProcesses.includes(process.name)) {
                            failedProcesses.push(process.name);
                        }
                    }
                }
                
                successCount = processingQueue.length - failedProcesses.length;
            }

            // Generate metadata.txt file after all rasters are complete
            if (successCount > 0) {
                try {
                    console.log('📄 Generating metadata.txt file...');
                    this.updateLazRasterProcessingStep('Generating Metadata', processingQueue.length, processingQueue.length + 2);
                    
                    const selectedRegion = window.FileManager?.getSelectedRegion();
                    const processingRegion = window.FileManager?.getProcessingRegion();
                    const regionName = processingRegion || selectedRegion;
                    
                    if (regionName) {
                        // Get the LAZ filename from the region path
                        const regionPath = window.FileManager?.getRegionPath();
                        let lazFileName = regionName + '.laz'; // Default fallback
                        
                        if (regionPath && regionPath.includes('input/LAZ/')) {
                            // Extract actual filename from path like "input/LAZ/CUI_A01.laz"
                            const pathParts = regionPath.split('/');
                            lazFileName = pathParts[pathParts.length - 1];
                        }
                        
                        console.log(`📄 Creating metadata for region: ${regionName}, file: ${lazFileName}`);
                        
                        const formData = new FormData();
                        formData.append('region_name', regionName);
                        formData.append('file_name', lazFileName);
                        
                        const metadataResponse = await fetch('/api/laz/generate-metadata', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (metadataResponse.ok) {
                            const metadataResult = await metadataResponse.json();
                            console.log('✅ Metadata generated successfully:', metadataResult);
                            
                            // Update UI to show metadata generation completed
                            this.updateLazRasterProcessingStep('Metadata Generated', processingQueue.length + 1, processingQueue.length + 2);
                            this.markLazQueueItemComplete('metadata', 'success');
                            
                            // 🛰️ SENTINEL-2 ACQUISITION INTEGRATION
                            // Check if Sentinel-2 acquisition was attempted and show status
                            const sentinel2Status = metadataResult.sentinel2_acquisition;
                            if (sentinel2Status && sentinel2Status.attempted) {
                                console.log('🛰️ Processing Sentinel-2 acquisition results...');
                                this.updateLazRasterProcessingStep('Processing Sentinel-2 Data', processingQueue.length + 2, processingQueue.length + 2);
                                
                                if (sentinel2Status.success) {
                                    console.log('✅ Sentinel-2 acquisition completed successfully');
                                    this.markLazQueueItemComplete('sentinel2', 'success');
                                    
                                    // Show success notification
                                    if (window.Utils && window.Utils.showNotification) {
                                        window.Utils.showNotification('🛰️ Sentinel-2 satellite imagery acquired successfully!', 'success');
                                    }
                                } else {
                                    console.warn('⚠️ Sentinel-2 acquisition failed:', sentinel2Status.result);
                                    this.markLazQueueItemComplete('sentinel2', 'error');
                                    
                                    // Show warning notification
                                    if (window.Utils && window.Utils.showNotification) {
                                        window.Utils.showNotification('⚠️ Sentinel-2 acquisition failed - continuing with LiDAR processing', 'warning');
                                    }
                                }
                            } else {
                                console.log('ℹ️ Sentinel-2 acquisition was not attempted');
                                this.updateLazRasterProcessingStep('Sentinel-2 Skipped', processingQueue.length + 2, processingQueue.length + 2);
                                this.markLazQueueItemComplete('sentinel2', 'skipped');
                            }
                            
                        } else {
                            console.warn('⚠️ Metadata generation failed:', metadataResponse.statusText);
                            this.updateLazRasterProcessingStep('Metadata Generation Failed', processingQueue.length + 1, processingQueue.length + 2);
                            this.markLazQueueItemComplete('metadata', 'error');
                            this.markLazQueueItemComplete('sentinel2', 'skipped');
                        }
                    }
                } catch (error) {
                    console.error('❌ Metadata generation error:', error);
                    this.updateLazRasterProcessingStep('Metadata Generation Error', processingQueue.length + 1, processingQueue.length + 2);
                    this.markLazQueueItemComplete('metadata', 'error');
                    this.markLazQueueItemComplete('sentinel2', 'skipped');
                }
            }

            // Show completion summary in LAZ modal
            this.showLazRasterProcessingComplete(successCount, failedProcesses);
            
            // Final notification
            if (failedProcesses.length === 0) {
                if (window.Utils) window.Utils.showNotification(`All ${successCount} raster products generated successfully!`, 'success');
                
                // Refresh overlay display after successful raster generation
                setTimeout(() => {
                    const selectedRegion = window.FileManager?.getSelectedRegion();
                    const processingRegion = window.FileManager?.getProcessingRegion();
                    
                    if (processingRegion || selectedRegion) {
                        console.log('🔄 Refreshing LIDAR raster display after successful generation...');
                        window.UIManager?.displayLidarRasterForRegion(processingRegion || selectedRegion);
                    }
                }, 2000); // 2 second delay to ensure files are ready
                
            } else if (successCount > 0) {
                if (window.Utils) window.Utils.showNotification(`${successCount} raster products completed, ${failedProcesses.length} failed`, 'warning');
                
                // Still refresh display for successful ones
                setTimeout(() => {
                    const selectedRegion = window.FileManager?.getSelectedRegion();
                    const processingRegion = window.FileManager?.getProcessingRegion();
                    
                    if (processingRegion || selectedRegion) {
                        console.log('🔄 Refreshing LIDAR raster display for successful generations...');
                        window.UIManager?.displayLidarRasterForRegion(processingRegion || selectedRegion);
                    }
                }, 2000);
            } else {
                if (window.Utils) window.Utils.showNotification('Raster generation failed. Please check your input data.', 'error');
            }

            return successCount > 0;

        } catch (error) {
            console.log('Sequential raster processing failed:', error);
            if (window.Utils) window.Utils.showNotification('Sequential raster processing failed', 'error');
            this.showLazRasterProgress(false);
            return false;
        }
    }

    /**
     * Reset LAZ raster processing queue visual indicators to initial state
     * This should be called when starting processing for a new LAZ file
     */
    resetLazRasterProcessingQueue() {
        console.log('🔄 Resetting LAZ raster processing queue visual indicators');
        
        // List of all queue item IDs that need to be reset
        const queueIds = [
            'laz-queue-density-analysis',
            'laz-queue-mask-generation', 
            'laz-queue-quality-dtm',
            'laz-queue-hs-red',
            'laz-queue-hs-green', 
            'laz-queue-hs-blue',
            'laz-queue-chm',
            'laz-queue-slope',
            'laz-queue-aspect',
            'laz-queue-color-relief',
            'laz-queue-slope-relief',
            'laz-queue-lrm',
            'laz-queue-sky-view-factor',
            'laz-queue-hillshade-rgb',
            'laz-queue-boosted-hillshade',
            'laz-queue-metadata',
            'laz-queue-sentinel2'
        ];
        
        // Reset each queue item to default pending state
        queueIds.forEach(queueId => {
            const queueItem = document.getElementById(queueId);
            if (queueItem) {
                // Reset to default pending state (grey border, no status colors)
                queueItem.className = 'p-2 rounded bg-[#1a1a1a] text-center border-l-2 border-[#666]';
            }
        });
        
        console.log('✅ LAZ raster processing queue visual indicators reset');
    }
}

// Export for use by other modules
window.GeoTiffLeftPanel = GeoTiffLeftPanel;
