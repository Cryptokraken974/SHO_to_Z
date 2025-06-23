// GeoTiff Tools Main Canvas JavaScript
class GeoTiffMainCanvas {
    constructor() {
        this.currentFile = null;
        this.processingResults = [];
        this.previewMode = 'metadata'; // 'metadata', 'preview', 'histogram', 'stats'
        this.init();
    }

    init() {
        console.log('🖼️ Initializing GeoTiff Main Canvas');
        this.setupEventListeners();
        this.initializeCanvas();
    }

    setupEventListeners() {
        // Preview mode tabs
        const previewTabs = document.querySelectorAll('.preview-tab');
        previewTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchPreviewMode(e.target.dataset.mode);
            });
        });

        // Processing result cards
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('result-card')) {
                this.selectProcessingResult(e.target.dataset.resultId);
            }
        });

        // Export buttons
        const exportBtn = document.getElementById('export-result-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportCurrentResult());
        }

        // Download buttons
        const downloadBtn = document.getElementById('download-result-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadCurrentResult());
        }
    }

    initializeCanvas() {
        this.showWelcomeMessage();
    }

    showWelcomeMessage() {
        const canvas = document.getElementById('geotiff-main-canvas');
        if (canvas) {
            canvas.innerHTML = `
                <div class="flex items-center justify-center h-full">
                    <div class="text-center">
                        <div class="mb-4">
                            <i class="fas fa-map text-6xl text-[#00bfff] mb-4"></i>
                        </div>
                        <h3 class="text-white text-xl font-semibold mb-2">GeoTiff Tools</h3>
                        <p class="text-[#ababab] text-sm mb-4">Select a GeoTiff file from the left panel to begin analysis</p>
                        <div class="flex flex-wrap gap-2 justify-center">
                            <span class="px-3 py-1 bg-[#303030] text-[#ababab] rounded-full text-xs">Metadata Analysis</span>
                            <span class="px-3 py-1 bg-[#303030] text-[#ababab] rounded-full text-xs">Image Preview</span>
                            <span class="px-3 py-1 bg-[#303030] text-[#ababab] rounded-full text-xs">Statistical Analysis</span>
                            <span class="px-3 py-1 bg-[#303030] text-[#ababab] rounded-full text-xs">Processing Tools</span>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    displayFilePreview(fileData) {
        console.log('🖼️ Displaying file preview:', fileData);
        this.currentFile = fileData;
        
        const canvas = document.getElementById('geotiff-main-canvas');
        if (!canvas) return;

        canvas.innerHTML = `
            <div class="h-full flex flex-col">
                <!-- File Header -->
                <div class="flex items-center justify-between p-4 bg-[#1a1a1a] border-b border-[#303030]">
                    <div class="flex items-center gap-3">
                        <i class="fas fa-file-image text-[#00bfff]"></i>
                        <div>
                            <h3 class="text-white font-semibold">${fileData.name}</h3>
                            <p class="text-[#ababab] text-sm">${fileData.size || 'Unknown size'}</p>
                        </div>
                    </div>
                    <div class="flex gap-2">
                        <button id="export-result-btn" class="px-4 py-2 bg-[#28a745] hover:bg-[#218838] text-white rounded-lg text-sm transition-colors">
                            <i class="fas fa-download mr-2"></i>Export
                        </button>
                        <button id="download-result-btn" class="px-4 py-2 bg-[#007bff] hover:bg-[#0056b3] text-white rounded-lg text-sm transition-colors">
                            <i class="fas fa-save mr-2"></i>Save
                        </button>
                    </div>
                </div>

                <!-- Preview Mode Tabs -->
                <div class="flex bg-[#262626] border-b border-[#303030]">
                    <button class="preview-tab ${this.previewMode === 'metadata' ? 'active' : ''} px-4 py-2 text-sm font-medium border-b-2 transition-colors" data-mode="metadata">
                        📋 Metadata
                    </button>
                    <button class="preview-tab ${this.previewMode === 'preview' ? 'active' : ''} px-4 py-2 text-sm font-medium border-b-2 transition-colors" data-mode="preview">
                        🖼️ Preview
                    </button>
                    <button class="preview-tab ${this.previewMode === 'histogram' ? 'active' : ''} px-4 py-2 text-sm font-medium border-b-2 transition-colors" data-mode="histogram">
                        📊 Histogram
                    </button>
                    <button class="preview-tab ${this.previewMode === 'stats' ? 'active' : ''} px-4 py-2 text-sm font-medium border-b-2 transition-colors" data-mode="stats">
                        📈 Statistics
                    </button>
                </div>

                <!-- Preview Content -->
                <div id="preview-content" class="flex-1 overflow-y-auto p-4">
                    ${this.renderPreviewContent()}
                </div>
            </div>
        `;

        this.setupEventListeners();
    }

    renderPreviewContent() {
        switch (this.previewMode) {
            case 'metadata':
                return this.renderMetadata();
            case 'preview':
                return this.renderImagePreview();
            case 'histogram':
                return this.renderHistogram();
            case 'stats':
                return this.renderStatistics();
            default:
                return '<div class="text-[#666] text-center py-8">Select a preview mode</div>';
        }
    }

    renderMetadata() {
        const metadata = this.currentFile?.metadata || {};
        return `
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Basic Information -->
                <div class="bg-[#1a1a1a] border border-[#303030] rounded-lg p-4">
                    <h4 class="text-white font-semibold mb-3">📄 Basic Information</h4>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">Format:</span>
                            <span class="text-white">${metadata.format || 'GeoTIFF'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">Width:</span>
                            <span class="text-white">${metadata.width || '--'} px</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">Height:</span>
                            <span class="text-white">${metadata.height || '--'} px</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">Bands:</span>
                            <span class="text-white">${metadata.bands || '--'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">Data Type:</span>
                            <span class="text-white">${metadata.dataType || '--'}</span>
                        </div>
                    </div>
                </div>

                <!-- Spatial Information -->
                <div class="bg-[#1a1a1a] border border-[#303030] rounded-lg p-4">
                    <h4 class="text-white font-semibold mb-3">🌍 Spatial Information</h4>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">CRS:</span>
                            <span class="text-white font-mono text-xs">${metadata.crs || '--'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">Extent:</span>
                            <span class="text-white font-mono text-xs">${metadata.extent || '--'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">Resolution:</span>
                            <span class="text-white">${metadata.resolution || '--'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">NoData Value:</span>
                            <span class="text-white">${metadata.nodata || '--'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderImagePreview() {
        return `
            <div class="bg-[#1a1a1a] border border-[#303030] rounded-lg p-4">
                <h4 class="text-white font-semibold mb-3">🖼️ Image Preview</h4>
                <div class="bg-[#262626] rounded-lg p-4 min-h-[400px] flex items-center justify-center">
                    <div class="text-center">
                        <i class="fas fa-image text-4xl text-[#666] mb-3"></i>
                        <p class="text-[#666]">Image preview will be displayed here</p>
                        <p class="text-[#666] text-sm mt-2">Processing large GeoTiff files...</p>
                    </div>
                </div>
            </div>
        `;
    }

    renderHistogram() {
        return `
            <div class="bg-[#1a1a1a] border border-[#303030] rounded-lg p-4">
                <h4 class="text-white font-semibold mb-3">📊 Data Histogram</h4>
                <div class="bg-[#262626] rounded-lg p-4 min-h-[300px] flex items-center justify-center">
                    <div class="text-center">
                        <i class="fas fa-chart-bar text-4xl text-[#666] mb-3"></i>
                        <p class="text-[#666]">Histogram chart will be displayed here</p>
                    </div>
                </div>
            </div>
        `;
    }

    renderStatistics() {
        const stats = this.currentFile?.statistics || {};
        return `
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Band Statistics -->
                <div class="bg-[#1a1a1a] border border-[#303030] rounded-lg p-4">
                    <h4 class="text-white font-semibold mb-3">📈 Band Statistics</h4>
                    <div class="space-y-3">
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-[#ababab]">Minimum:</span>
                                <span class="text-white">${stats.min || '--'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-[#ababab]">Maximum:</span>
                                <span class="text-white">${stats.max || '--'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-[#ababab]">Mean:</span>
                                <span class="text-white">${stats.mean || '--'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-[#ababab]">Std Dev:</span>
                                <span class="text-white">${stats.stddev || '--'}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Quality Metrics -->
                <div class="bg-[#1a1a1a] border border-[#303030] rounded-lg p-4">
                    <h4 class="text-white font-semibold mb-3">🔍 Quality Metrics</h4>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">Valid Pixels:</span>
                            <span class="text-white">${stats.validPixels || '--'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">NoData Pixels:</span>
                            <span class="text-white">${stats.nodataPixels || '--'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[#ababab]">Coverage:</span>
                            <span class="text-white">${stats.coverage || '--'}%</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    switchPreviewMode(mode) {
        this.previewMode = mode;
        
        // Update tab states
        document.querySelectorAll('.preview-tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.mode === mode) {
                tab.classList.add('active');
            }
        });

        // Update content
        const contentDiv = document.getElementById('preview-content');
        if (contentDiv) {
            contentDiv.innerHTML = this.renderPreviewContent();
        }
    }

    displayProcessingResults(results) {
        console.log('📊 Displaying processing results:', results);
        this.processingResults = results;

        const canvas = document.getElementById('geotiff-main-canvas');
        if (!canvas) return;

        canvas.innerHTML = `
            <div class="h-full flex flex-col">
                <div class="p-4 bg-[#1a1a1a] border-b border-[#303030]">
                    <h3 class="text-white font-semibold">🔄 Processing Results</h3>
                    <p class="text-[#ababab] text-sm">View and manage processing results</p>
                </div>
                
                <div class="flex-1 overflow-y-auto p-4">
                    <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                        ${results.map(result => this.renderResultCard(result)).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    renderResultCard(result) {
        return `
            <div class="result-card bg-[#1a1a1a] border border-[#303030] rounded-lg p-4 cursor-pointer hover:border-[#00bfff] transition-colors" data-result-id="${result.id}">
                <div class="flex items-center gap-3 mb-3">
                    <i class="fas fa-cog text-[#00bfff]"></i>
                    <div>
                        <h4 class="text-white font-medium">${result.operation}</h4>
                        <p class="text-[#ababab] text-sm">${result.timestamp}</p>
                    </div>
                </div>
                <div class="text-sm text-[#ababab]">
                    ${result.status === 'completed' ? '✅ Completed' : result.status === 'processing' ? '⏳ Processing' : '❌ Failed'}
                </div>
                ${result.preview ? `<div class="mt-3"><img src="${result.preview}" class="w-full h-24 object-cover rounded border border-[#303030]" alt="Preview"></div>` : ''}
            </div>
        `;
    }

    selectProcessingResult(resultId) {
        const result = this.processingResults.find(r => r.id === resultId);
        if (result) {
            console.log('📋 Selected processing result:', result);
            // Display detailed result information
            this.displayResultDetails(result);
        }
    }

    displayResultDetails(result) {
        // Implementation for showing detailed result information
        console.log('🔍 Displaying result details:', result);
    }

    exportCurrentResult() {
        if (this.currentFile) {
            console.log('💾 Exporting current result:', this.currentFile);
            // Implementation for exporting results
        }
    }

    downloadCurrentResult() {
        if (this.currentFile) {
            console.log('⬇️ Downloading current result:', this.currentFile);
            // Implementation for downloading results
        }
    }

    /**
     * Show crop dialog for a GeoTIFF file
     * @param {string} filePath - Path to the file to crop
     */
    async showCropDialog(filePath) {
        const dialog = document.createElement('div');
        dialog.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]';
        dialog.innerHTML = `
            <div class="bg-[#2a2a2a] rounded-lg p-6 max-w-md w-full mx-4">
                <h3 class="text-white text-lg font-semibold mb-4">Crop GeoTIFF</h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-[#ababab] text-sm mb-1">Min X (West)</label>
                        <input type="number" id="crop-min-x" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" step="any">
                    </div>
                    <div>
                        <label class="block text-[#ababab] text-sm mb-1">Min Y (South)</label>
                        <input type="number" id="crop-min-y" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" step="any">
                    </div>
                    <div>
                        <label class="block text-[#ababab] text-sm mb-1">Max X (East)</label>
                        <input type="number" id="crop-max-x" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" step="any">
                    </div>
                    <div>
                        <label class="block text-[#ababab] text-sm mb-1">Max Y (North)</label>
                        <input type="number" id="crop-max-y" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" step="any">
                    </div>
                    <div>
                        <label class="block text-[#ababab] text-sm mb-1">Output Path (optional)</label>
                        <input type="text" id="crop-output-path" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" placeholder="Leave empty for auto-generated">
                    </div>
                </div>
                <div class="flex gap-3 mt-6">
                    <button id="crop-cancel" class="flex-1 bg-[#3a3a3a] text-white px-4 py-2 rounded hover:bg-[#4a4a4a]">Cancel</button>
                    <button id="crop-submit" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Crop</button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // Event listeners
        dialog.querySelector('#crop-cancel').addEventListener('click', () => {
            document.body.removeChild(dialog);
        });

        dialog.querySelector('#crop-submit').addEventListener('click', async () => {
            const bounds = {
                min_x: parseFloat(document.getElementById('crop-min-x').value),
                min_y: parseFloat(document.getElementById('crop-min-y').value),
                max_x: parseFloat(document.getElementById('crop-max-x').value),
                max_y: parseFloat(document.getElementById('crop-max-y').value)
            };
            const outputPath = document.getElementById('crop-output-path').value || null;

            try {
                const result = await geotiff().cropGeotiff(filePath, bounds, outputPath);
                console.log('Crop result:', result);
                this.showSuccessMessage('File cropped successfully');
                document.body.removeChild(dialog);
            } catch (error) {
                console.error('Crop error:', error);
                this.showErrorMessage(`Crop failed: ${error.message}`);
            }
        });
    }

    /**
     * Show conversion dialog for a GeoTIFF file
     * @param {string} filePath - Path to the file to convert
     */
    async showConversionDialog(filePath) {
        const dialog = document.createElement('div');
        dialog.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]';
        dialog.innerHTML = `
            <div class="bg-[#2a2a2a] rounded-lg p-6 max-w-md w-full mx-4">
                <h3 class="text-white text-lg font-semibold mb-4">Convert GeoTIFF</h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-[#ababab] text-sm mb-1">Conversion Type</label>
                        <select id="conversion-type" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]">
                            <option value="png">Convert to PNG</option>
                            <option value="base64">Convert to Base64 PNG</option>
                        </select>
                    </div>
                    <div id="output-path-section">
                        <label class="block text-[#ababab] text-sm mb-1">Output Path (optional)</label>
                        <input type="text" id="conversion-output-path" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" placeholder="Leave empty for auto-generated">
                    </div>
                </div>
                <div class="flex gap-3 mt-6">
                    <button id="conversion-cancel" class="flex-1 bg-[#3a3a3a] text-white px-4 py-2 rounded hover:bg-[#4a4a4a]">Cancel</button>
                    <button id="conversion-submit" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Convert</button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // Update UI based on conversion type
        const conversionType = dialog.querySelector('#conversion-type');
        const outputPathSection = dialog.querySelector('#output-path-section');
        
        conversionType.addEventListener('change', () => {
            if (conversionType.value === 'base64') {
                outputPathSection.style.display = 'none';
            } else {
                outputPathSection.style.display = 'block';
            }
        });

        // Event listeners
        dialog.querySelector('#conversion-cancel').addEventListener('click', () => {
            document.body.removeChild(dialog);
        });

        dialog.querySelector('#conversion-submit').addEventListener('click', async () => {
            const type = conversionType.value;
            const outputPath = document.getElementById('conversion-output-path').value || null;

            try {
                let result;
                if (type === 'png') {
                    result = await geotiff().convertGeotiffToPng(filePath, outputPath);
                } else if (type === 'base64') {
                    result = await geotiff().convertToBase64(filePath);
                }
                
                console.log('Conversion result:', result);
                this.showSuccessMessage(`File converted to ${type.toUpperCase()} successfully`);
                document.body.removeChild(dialog);
            } catch (error) {
                console.error('Conversion error:', error);
                this.showErrorMessage(`Conversion failed: ${error.message}`);
            }
        });
    }

    /**
     * Show file info with enhanced details using the new service
     * @param {string} filePath - Path to the file
     */
    async showFileInfo(filePath) {
        try {
            // Get comprehensive file information
            const [info, metadata, statistics] = await Promise.all([
                geotiff().getGeotiffInfo(filePath),
                geotiff().getGeotiffMetadata(filePath),
                geotiff().getGeotiffStatistics(filePath).catch(() => null) // Statistics might not be available for all files
            ]);

            const canvas = document.getElementById('geotiff-main-canvas');
            if (canvas) {
                canvas.innerHTML = `
                    <div class="p-6">
                        <h2 class="text-white text-xl font-semibold mb-4">File Information</h2>
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div class="bg-[#2a2a2a] rounded-lg p-4">
                                <h3 class="text-white font-semibold mb-3">Basic Info</h3>
                                <div class="space-y-2 text-sm">
                                    ${Object.entries(info).map(([key, value]) => 
                                        `<div class="flex justify-between">
                                            <span class="text-[#ababab]">${key}:</span>
                                            <span class="text-white">${value}</span>
                                        </div>`
                                    ).join('')}
                                </div>
                            </div>
                            <div class="bg-[#2a2a2a] rounded-lg p-4">
                                <h3 class="text-white font-semibold mb-3">Metadata</h3>
                                <div class="space-y-2 text-sm max-h-64 overflow-y-auto">
                                    ${Object.entries(metadata).map(([key, value]) => 
                                        `<div class="flex justify-between">
                                            <span class="text-[#ababab]">${key}:</span>
                                            <span class="text-white">${typeof value === 'object' ? JSON.stringify(value) : value}</span>
                                        </div>`
                                    ).join('')}
                                </div>
                            </div>
                            ${statistics ? `
                                <div class="bg-[#2a2a2a] rounded-lg p-4 lg:col-span-2">
                                    <h3 class="text-white font-semibold mb-3">Statistics</h3>
                                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                                        ${Object.entries(statistics).map(([key, value]) => 
                                            `<div class="text-center">
                                                <div class="text-[#ababab]">${key}</div>
                                                <div class="text-white font-semibold">${typeof value === 'number' ? value.toFixed(4) : value}</div>
                                            </div>`
                                        ).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading file info:', error);
            this.showErrorMessage(`Failed to load file information: ${error.message}`);
        }
    }

    /**
     * Show resample dialog for a GeoTIFF file
     * @param {string} filePath - Path to the file to resample
     */
    async showResampleDialog(filePath) {
        const dialog = document.createElement('div');
        dialog.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]';
        dialog.innerHTML = `
            <div class="bg-[#2a2a2a] rounded-lg p-6 max-w-md w-full mx-4">
                <h3 class="text-white text-lg font-semibold mb-4">Resample GeoTIFF</h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-[#ababab] text-sm mb-1">Target Resolution</label>
                        <input type="number" id="resample-resolution" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" step="any" placeholder="e.g., 30.0">
                    </div>
                    <div>
                        <label class="block text-[#ababab] text-sm mb-1">Output Path (optional)</label>
                        <input type="text" id="resample-output-path" class="w-full bg-[#1e1e1e] text-white p-2 rounded border border-[#3a3a3a]" placeholder="Leave empty for auto-generated">
                    </div>
                </div>
                <div class="flex gap-3 mt-6">
                    <button id="resample-cancel" class="flex-1 bg-[#3a3a3a] text-white px-4 py-2 rounded hover:bg-[#4a4a4a]">Cancel</button>
                    <button id="resample-submit" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Resample</button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // Event listeners
        dialog.querySelector('#resample-cancel').addEventListener('click', () => {
            document.body.removeChild(dialog);
        });

        dialog.querySelector('#resample-submit').addEventListener('click', async () => {
            const resolution = parseFloat(document.getElementById('resample-resolution').value);
            const outputPath = document.getElementById('resample-output-path').value || null;

            if (isNaN(resolution) || resolution <= 0) {
                this.showErrorMessage('Please enter a valid resolution');
                return;
            }

            try {
                const result = await geotiff().resampleGeotiff(filePath, resolution, outputPath);
                console.log('Resample result:', result);
                this.showSuccessMessage('File resampled successfully');
                document.body.removeChild(dialog);
            } catch (error) {
                console.error('Resample error:', error);
                this.showErrorMessage(`Resample failed: ${error.message}`);
            }
        });
    }

    /**
     * Show success message
     * @param {string} message - Success message to display
     */
    showSuccessMessage(message) {
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-600 text-white px-4 py-2 rounded shadow-lg z-[9999]';
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 3000);
    }

    /**
     * Show error message
     * @param {string} message - Error message to display
     */
    showErrorMessage(message) {
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-red-600 text-white px-4 py-2 rounded shadow-lg z-[9999]';
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 5000);
    }

}

// Initialize GeoTiff Main Canvas when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('geotiff-main-canvas')) {
        window.geoTiffMainCanvas = new GeoTiffMainCanvas();
    }
});

// Export for use by other modules
window.GeoTiffMainCanvas = GeoTiffMainCanvas;
