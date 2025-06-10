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
        const files = this.selectedLazFiles;
        if (!files || files.length === 0) {
            this.showError('No files selected');
            return;
        }

        try {
            this.showLazProgress(true);
            this.updateLazProgress(0, 'Starting upload...');

            const formData = new FormData();
            files.forEach(file => {
                formData.append('files', file);
            });

            // Upload files and get coordinates
            const response = await fetch('/api/laz/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('LAZ upload result:', result);

            this.updateLazProgress(50, 'Files uploaded, processing coordinates...');

            // Store the loaded files info
            const loadedFiles = result.files || [];
            
            this.loadFileTree();
            
            // 🔧 FIX: Automatically select the first uploaded LAZ file as the current region
            if (loadedFiles.length > 0 && window.FileManager) {
                const firstUploadedFile = loadedFiles[0];
                const fileName = firstUploadedFile.inputFile; // This should be the LAZ filename like "CUI_A01.laz"
                const regionName = fileName.replace(/\.[^/.]+$/, ''); // Remove extension to get "CUI_A01"
                
                console.log('🎯 Automatically selecting uploaded LAZ file as region:', regionName);
                console.log('📁 Original filename:', fileName);
                
                this.updateLazProgress(100, 'Setting up region...');
                
                // Set the selected region to use the uploaded LAZ file
                // This ensures ProcessingManager.processAllRasters() will use this region instead of coordinates
                window.FileManager.selectRegion(
                    regionName,                 // displayName: use clean name for output folders (no .laz extension)
                    null,                       // coords: let it be fetched automatically
                    regionName,                 // processingRegion: use the name without extension
                    `input/LAZ/${fileName}`     // regionPath: full path for LAZ file operations
                );
                
                console.log('✅ Region selected:', regionName);
                
                // Wait for region setup to complete before triggering raster generation
                this.updateLazProgress(100, 'Region setup complete. Starting raster generation...');
                
                // Show raster generation progress section
                this.showLazRasterProgress(true);
                
                // Give extra time for the region selection and coordinate fetching to complete
                setTimeout(async () => {
                    // Verify that the region is properly selected before proceeding
                    if (window.FileManager.hasSelectedRegion()) {
                        console.log('🚀 Region setup complete. Triggering automatic raster generation...');
                        
                        // Additional delay to ensure backend file is ready
                        setTimeout(async () => {
                            console.log('🎯 Calling ProcessingManager.processAllRasters() with LAZ modal progress integration');
                            try {
                                // Show notification that rasters are being generated
                                if (window.Utils && window.Utils.showNotification) {
                                    window.Utils.showNotification('🚀 Automatic raster generation started! Progress shown in LAZ loading window.', 'info');
                                }
                                
                                // Start raster processing with LAZ modal progress integration
                                const result = await this.processAllRastersWithLazModalProgress();
                                
                                if (result) {
                                    console.log('✅ Automatic raster generation completed successfully');
                                    // Keep modal open for a bit to show completion status
                                    setTimeout(() => {
                                        this.closeLazFileModal();
                                    }, 3000);
                                } else {
                                    console.warn('⚠️ Automatic raster generation failed');
                                    if (window.Utils && window.Utils.showNotification) {
                                        window.Utils.showNotification('Raster generation failed. Please try the "Generate Rasters" button manually.', 'warning');
                                    }
                                    // Close modal on failure after a delay
                                    setTimeout(() => {
                                        this.closeLazFileModal();
                                    }, 2000);
                                }
                            } catch (error) {
                                console.error('❌ Error during automatic raster generation:', error);
                                if (window.Utils && window.Utils.showNotification) {
                                    window.Utils.showNotification('Error during automatic processing. Please try the "Generate Rasters" button.', 'error');
                                }
                                // Close modal on error after a delay
                                setTimeout(() => {
                                    this.closeLazFileModal();
                                }, 2000);
                            }
                        }, 1000); // Extra 1 second for backend file availability
                        
                    } else {
                        console.warn('⚠️ Region selection not completed, skipping automatic raster generation');
                        this.updateLazProgress(100, 'Region setup incomplete - manual processing required');
                        // Close modal after a delay
                        setTimeout(() => {
                            this.closeLazFileModal();
                        }, 3000);
                    }
                }, 3000); // Increased delay for region setup completion
                
            } else {
                // No files loaded or FileManager not available - fallback to original behavior
                console.log('🚀 Triggering automatic raster generation after LAZ loading...');
                if (window.ProcessingManager && typeof window.ProcessingManager.processAllRasters === 'function') {
                    this.updateLazProgress(100, 'Starting automatic raster generation...');
                    this.showLazRasterProgress(true);
                    
                    setTimeout(async () => {
                        console.log('🎯 Calling ProcessingManager.processAllRasters() with LAZ modal progress integration');
                        try {
                            // Show notification that rasters are being generated  
                            if (window.Utils && window.Utils.showNotification) {
                                window.Utils.showNotification('🚀 Automatic raster generation started! Progress shown in LAZ loading window.', 'info');
                            }
                            
                            // Start raster processing with LAZ modal progress integration
                            const result = await this.processAllRastersWithLazModalProgress();
                            
                            if (result) {
                                console.log('✅ Automatic raster generation completed successfully');
                                // Keep modal open for a bit to show completion status
                                setTimeout(() => {
                                    this.closeLazFileModal();
                                }, 3000);
                            } else {
                                console.warn('⚠️ Automatic raster generation failed');
                                if (window.Utils && window.Utils.showNotification) {
                                    window.Utils.showNotification('Raster generation failed. Please try the "Generate Rasters" button manually.', 'warning');
                                }
                                // Close modal on failure after a delay
                                setTimeout(() => {
                                    this.closeLazFileModal();
                                }, 2000);
                            }
                        } catch (error) {
                            console.error('❌ Error during automatic raster generation:', error);
                            if (window.Utils && window.Utils.showNotification) {
                                window.Utils.showNotification('Error during automatic processing. Please try the "Generate Rasters" button.', 'error');
                            }
                            // Close modal on error after a delay
                            setTimeout(() => {
                                this.closeLazFileModal();
                            }, 2000);
                        }
                    }, 2000);
                } else {
                    console.warn('⚠️ ProcessingManager not available for automatic raster generation');
                    // Close modal if no processing available
                    setTimeout(() => {
                        this.closeLazFileModal();
                    }, 2000);
                }
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
     * Process all rasters with LAZ modal progress integration
     * This mimics ProcessingManager.processAllRasters() but updates the LAZ modal UI
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

        // Define processing queue (same as ProcessingManager)
        const processingQueue = [
            { type: 'dtm', name: 'DTM', icon: '🏔️' },
            { type: 'dsm', name: 'DSM', icon: '🏗️' },
            { type: 'hillshade', name: 'Hillshade', icon: '🌄' },
            { type: 'slope', name: 'Slope', icon: '📐' },
            { type: 'aspect', name: 'Aspect', icon: '🧭' },
            { type: 'tpi', name: 'TPI', icon: '📈' },
            { type: 'roughness', name: 'Roughness', icon: '🪨' },
            { type: 'chm', name: 'CHM', icon: '🌳' }
        ];

        try {
            // Initialize LAZ modal progress display
            this.updateLazRasterProcessingQueue(processingQueue, -1);
            
            if (window.Utils) window.Utils.showNotification('Starting sequential raster generation...', 'info');
            
            let successCount = 0;
            let failedProcesses = [];
            let lazProcessingCancelled = false;

            // Set up cancel button handler
            const cancelButton = document.getElementById('cancel-laz-raster-processing');
            if (cancelButton) {
                const cancelHandler = () => {
                    lazProcessingCancelled = true;
                    console.log('🛑 LAZ raster processing cancelled by user');
                    if (window.Utils) window.Utils.showNotification('Raster processing cancelled', 'info');
                };
                
                cancelButton.addEventListener('click', cancelHandler);
                
                // Clean up event listener when processing completes
                const cleanup = () => {
                    cancelButton.removeEventListener('click', cancelHandler);
                };
                
                // Store cleanup function for later use
                this._lazCancelCleanup = cleanup;
            }

            // Process each item in the queue sequentially
            for (let i = 0; i < processingQueue.length; i++) {
                // Check for cancellation
                if (lazProcessingCancelled) {
                    console.log('LAZ processing cancelled by user');
                    this.showLazRasterProgress(false);
                    return false;
                }

                const process = processingQueue[i];
                
                try {
                    // Update LAZ modal UI to show current processing step
                    this.updateLazRasterProcessingStep(process.name, i, processingQueue.length);
                    this.updateLazRasterProcessingQueue(processingQueue, i);
                    
                    console.log(`Processing ${process.name} (${i + 1}/${processingQueue.length})`);
                    
                    // Execute the processing using ProcessingManager
                    const success = await window.ProcessingManager.sendProcess(process.type);
                    
                    if (success) {
                        successCount++;
                        this.markLazQueueItemComplete(process.type, 'success');
                        console.log(`${process.name} completed successfully`);
                    } else {
                        failedProcesses.push(process.name);
                        this.markLazQueueItemComplete(process.type, 'error');
                        console.log(`${process.name} failed`);
                    }
                    
                    // Small delay between processes
                    if (i < processingQueue.length - 1) {
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }
                    
                } catch (error) {
                    failedProcesses.push(process.name);
                    this.markLazQueueItemComplete(process.type, 'error');
                    console.log(`${process.name} processing failed:`, error);
                }
            }

            // Clean up cancel event listener
            if (this._lazCancelCleanup) {
                this._lazCancelCleanup();
                delete this._lazCancelCleanup;
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
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('geotiff-tools-tab')) {
        window.geoTiffLeftPanel = new GeoTiffLeftPanel();
    }
});
