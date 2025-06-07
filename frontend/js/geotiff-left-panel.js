// GeoTiff Tools Left Panel JavaScript
class GeoTiffLeftPanel {
    constructor() {
        this.selectedFile = null;
        this.fileTree = [];
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
            loadLazBtn.addEventListener('click', () => this.openLazFileModal());
        }

        // Setup LAZ modal events
        this.setupLazModalEvents();
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
        const modal = document.getElementById('laz-file-modal');
        const closeBtn = document.getElementById('laz-modal-close');
        const cancelBtn = document.getElementById('cancel-laz-modal');
        const browseBtn = document.getElementById('browse-laz-btn');
        const fileInput = document.getElementById('laz-file-input');
        const dropZone = document.getElementById('laz-drop-zone');
        const clearBtn = document.getElementById('clear-laz-files');
        const loadBtn = document.getElementById('load-laz-files');

        // Close modal events
        [closeBtn, cancelBtn].forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => this.closeLazFileModal());
            }
        });

        // Click outside modal to close
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeLazFileModal();
                }
            });
        }

        // Browse button
        if (browseBtn) {
            browseBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent event bubbling to drop zone
                if (fileInput) fileInput.click();
            });
        }

        // File input change
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleLazFileSelection(e.target.files);
            });
        }

        // Drag and drop events
        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('border-[#00bfff]');
            });

            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.classList.remove('border-[#00bfff]');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('border-[#00bfff]');
                this.handleLazFileSelection(e.dataTransfer.files);
            });

            // Click on drop zone to browse (but not on child elements like the button)
            dropZone.addEventListener('click', (e) => {
                // Only trigger if clicking directly on the drop zone or its text, not on the button
                if (e.target === dropZone || (e.target.closest('#laz-drop-zone') && !e.target.closest('#browse-laz-btn'))) {
                    if (fileInput) fileInput.click();
                }
            });
        }

        // Clear files button
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearLazFiles());
        }

        // Load files button
        if (loadBtn) {
            loadBtn.addEventListener('click', () => this.loadLazFiles());
        }
    }

    openLazFileModal() {
        console.log('📂 Opening LAZ file browser modal');
        const modal = document.getElementById('laz-file-modal');
        if (modal) {
            modal.classList.remove('hidden');
            // Reset modal state
            this.clearLazFiles();
        }
    }

    closeLazFileModal() {
        console.log('📂 Closing LAZ file browser modal');
        const modal = document.getElementById('laz-file-modal');
        if (modal) {
            modal.classList.add('hidden');
            // Clear any selected files
            this.clearLazFiles();
        }
    }

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

    async loadLazFiles() {
        if (!this.selectedLazFiles || this.selectedLazFiles.length === 0) {
            this.showError('No files selected for loading');
            return;
        }

        console.log('📂 Loading LAZ files:', this.selectedLazFiles.length);

        // Show progress
        this.showLazProgress(true);
        this.updateLazProgress(0, 'Loading files...');

        try {
            // Load files one by one
            const loadedFiles = [];
            for (let i = 0; i < this.selectedLazFiles.length; i++) {
                const file = this.selectedLazFiles[i];
                const progress = ((i + 1) / this.selectedLazFiles.length) * 100;
                
                this.updateLazProgress(progress, `Loading ${file.name}...`);
                
                const result = await laz().loadLAZFile(file);
                loadedFiles.push(result);
            }

            this.updateLazProgress(100, 'Loading complete!');
            
            // Show success message
            this.showSuccess(`Successfully loaded ${loadedFiles.length} LAZ files`);
            
            // Refresh file tree to show new files
            this.loadFileTree();
            
            // Close modal after a short delay
            setTimeout(() => {
                this.closeLazFileModal();
            }, 1500);

        } catch (error) {
            console.error('LAZ loading error:', error);
            this.showError(`Loading failed: ${error.message}`);
            this.showLazProgress(false);
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
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('geotiff-tools-tab')) {
        window.geoTiffLeftPanel = new GeoTiffLeftPanel();
    }
});
