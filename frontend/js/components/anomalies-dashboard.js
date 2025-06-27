// Anomalies Dashboard Component
// Integrated into the main SHO_to_Z application

window.AnomaliesDashboard = {
    // Store the current analysis folder for image paths
    currentAnalysisFolder: null,
    
    // Store the original anomalies data for filtering
    originalAnomaliesData: null,
    
    // Store current filter settings
    activeFilters: new Set(),

    // Render the anomalies dashboard with provided data
    render(containerElement, jsonData, analysisFolder = null) {
        if (!containerElement) {
            Utils.log('error', 'AnomaliesDashboard: Container element not provided');
            return;
        }

        // Store the analysis folder name for image loading
        this.currentAnalysisFolder = analysisFolder;

        // Clear container
        containerElement.innerHTML = '';

        // Create dashboard structure
        const dashboardHTML = `
            <div id="anomaliesDashboard" class="anomalies-dashboard">
                <header class="anomalies-header">
                    <h1 class="anomalies-title">Anomaly Analysis Report</h1>
                    <div class="export-buttons">
                        <button id="anomalies-export-btn" class="anomalies-export-btn">Export HTML</button>
                        <button id="anomalies-pdf-btn" class="anomalies-export-btn anomalies-pdf-btn">Download PDF</button>
                    </div>
                </header>
                
                <section id="analysisSummary" class="analysis-summary-section">
                    <h2 class="section-title">Analysis Summary</h2>
                    <div class="summary-content">
                        <p><strong>Target Area ID:</strong> <span id="targetAreaId"></span></p>
                        <p><strong>Anomalies Detected:</strong> <span id="anomaliesDetected"></span></p>
                        <p><strong>Number of Anomalies:</strong> <span id="numberOfAnomalies"></span></p>
                    </div>
                </section>
                
                <section id="identifiedAnomalies" class="identified-anomalies-section">
                    <h2 class="section-title">Identified Anomalies</h2>
                    <div id="anomaliesContainer">
                        <!-- Anomalies will be dynamically injected here -->
                    </div>
                </section>
            </div>
        `;

        containerElement.innerHTML = dashboardHTML;

        // Populate with data
        this.populateData(jsonData);
    },

    populateData(jsonData) {
        // Use test data if no data provided
        if (!jsonData) {
            jsonData = this.getTestData();
        }

        // Store original data for filtering
        this.originalAnomaliesData = jsonData;

        // Populate Analysis Summary
        const targetAreaElement = document.getElementById('targetAreaId');
        const anomaliesDetectedElement = document.getElementById('anomaliesDetected');
        const numberOfAnomaliesElement = document.getElementById('numberOfAnomalies');

        if (jsonData.analysis_summary) {
            const summary = jsonData.analysis_summary;
            if (targetAreaElement) targetAreaElement.textContent = summary.target_area_id || 'Unknown';
            if (anomaliesDetectedElement) anomaliesDetectedElement.textContent = summary.anomalies_detected ? 'Yes' : 'No';
            if (numberOfAnomaliesElement) numberOfAnomaliesElement.textContent = summary.number_of_anomalies || 0;
        }

        // Populate Identified Anomalies
        this.populateAnomalies(jsonData.identified_anomalies || []);
    },

    /**
     * Apply current filters to the anomalies data
     */
    applyFilters() {
        if (!this.originalAnomaliesData || !this.originalAnomaliesData.identified_anomalies) {
            return;
        }

        let filteredAnomalies;

        // If no filters are active, show NO anomalies (empty result)
        if (this.activeFilters.size === 0) {
            filteredAnomalies = [];
        } else {
            // Apply type filters - only show anomalies matching active filters
            filteredAnomalies = this.originalAnomaliesData.identified_anomalies.filter(anomaly => {
                const anomalyType = anomaly.classification?.type || 'Unknown';
                return this.activeFilters.has(anomalyType);
            });
        }

        // Update the display
        this.populateAnomalies(filteredAnomalies);
        
        // Update summary count
        const numberOfAnomaliesElement = document.getElementById('numberOfAnomalies');
        if (numberOfAnomaliesElement) {
            numberOfAnomaliesElement.textContent = filteredAnomalies.length;
        }
    },

    /**
     * Set active filters and refresh display
     * @param {Set} filterSet - Set of anomaly types to show
     */
    setFilters(filterSet) {
        this.activeFilters = new Set(filterSet);
        this.applyFilters();
    },

    /**
     * Add a filter and refresh display
     * @param {string} anomalyType - Anomaly type to add to filter
     */
    addFilter(anomalyType) {
        this.activeFilters.add(anomalyType);
        this.applyFilters();
    },

    /**
     * Remove a filter and refresh display
     * @param {string} anomalyType - Anomaly type to remove from filter
     */
    removeFilter(anomalyType) {
        this.activeFilters.delete(anomalyType);
        this.applyFilters();
    },

    /**
     * Clear all filters and show all anomalies
     */
    clearAllFilters() {
        this.activeFilters.clear();
        this.applyFilters();
    },

    populateAnomalies(anomalies) {
        const anomaliesContainer = document.getElementById('anomaliesContainer');
        if (!anomaliesContainer) return;

        if (anomalies.length === 0) {
            // Determine appropriate message based on filter state
            let message;
            if (this.activeFilters.size === 0) {
                message = 'No anomaly types selected. Use the filter controls to select anomaly types to display.';
            } else if (this.originalAnomaliesData && this.originalAnomaliesData.identified_anomalies && this.originalAnomaliesData.identified_anomalies.length > 0) {
                message = 'No anomalies match the selected filter criteria.';
            } else {
                message = 'No anomalies identified.';
            }
            anomaliesContainer.innerHTML = `<p class="no-anomalies">${message}</p>`;
            return;
        }

        anomaliesContainer.innerHTML = '';

        anomalies.forEach((anomaly, index) => {
            const anomalyElement = document.createElement('article');
            anomalyElement.className = 'anomaly-item';

            const classificationType = anomaly.classification?.type || 'N/A';
            const classificationSubtype = anomaly.classification?.subtype || 'N/A';

            let individualScoresHtml = '<p>No individual scores available.</p>';
            if (anomaly.confidence?.individual_scores) {
                individualScoresHtml = Object.entries(anomaly.confidence.individual_scores)
                    .map(([key, value]) => `<p><strong>${key.toUpperCase()}:</strong> ${value}</p>`)
                    .join('');
            }

            let evidenceHtml = '<p>No evidence details available.</p>';
            if (anomaly.evidence_per_image) {
                evidenceHtml = '<ul class="evidence-list">';
                evidenceHtml += Object.entries(anomaly.evidence_per_image)
                    .map(([key, value]) => `<li><strong>${key.toUpperCase()}:</strong> ${value}</li>`)
                    .join('');
                evidenceHtml += '</ul>';
            }

            let boundingBoxHtml = '<p>No bounding box data available.</p>';
            if (anomaly.bounding_box_pixels?.length > 0) {
                boundingBoxHtml = anomaly.bounding_box_pixels
                    .map(bb => `<p>X: ${bb.x_min}-${bb.x_max}, Y: ${bb.y_min}-${bb.y_max}</p>`)
                    .join('');
            }

            anomalyElement.innerHTML = `
                <h3 class="anomaly-title">${anomaly.anomaly_id}</h3>
                <p><strong>Type:</strong> ${classificationType}</p>
                <p><strong>Subtype:</strong> ${classificationSubtype}</p>

                <div class="image-gallery-section">
                    <h4>Image Evidence Gallery:</h4>
                    <div class="image-gallery-container" id="gallery-${index}">
                        <div class="gallery-navigation">
                            <button class="gallery-nav-btn prev-btn" data-gallery="${index}" data-direction="prev">
                                ← Previous
                            </button>
                            <span class="gallery-counter" id="counter-${index}">1 / 1</span>
                            <button class="gallery-nav-btn next-btn" data-gallery="${index}" data-direction="next">
                                Next →
                            </button>
                        </div>
                        <div class="gallery-display">
                            <canvas id="canvas-${index}" class="anomaly-image-canvas"></canvas>
                            <div class="image-info" id="info-${index}">
                                <span class="image-type"></span>
                                <span class="mouse-coordinates" id="coords-${index}">Canvas: (0, 0) | Original: {"x": 0, "y": 0}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="confidence-section">
                    <h4>Confidence:</h4>
                    <p class="global-score">Global Score: ${anomaly.confidence?.global_score || 'N/A'}</p>
                    <div class="individual-scores">
                        <h5>Individual Scores:</h5>
                        ${individualScoresHtml}
                    </div>
                </div>

                <div class="evidence-section">
                    <h4>Evidence per Image:</h4>
                    ${evidenceHtml}
                </div>

                <div class="interpretation-section">
                    <h4>Archaeological Interpretation:</h4>
                    <p>${anomaly.archaeological_interpretation || 'N/A'}</p>
                </div>

                <div class="bounding-box-section">
                    <h4>Bounding Box Pixels:</h4>
                    ${boundingBoxHtml}
                </div>
            `;
            
            anomaliesContainer.appendChild(anomalyElement);

            // Initialize the image gallery for this anomaly
            this.initializeImageGallery(index, anomaly);
        });

        // Set up navigation event listeners
        this.setupGalleryNavigation();
        
        // Set up export button event listener
        this.setupExportButton();
    },

    /**
     * Set up export button functionality
     */
    setupExportButton() {
        // HTML Export button
        const exportBtn = document.getElementById('anomalies-export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                // Disable button during export
                exportBtn.disabled = true;
                exportBtn.textContent = 'Exporting...';
                
                this.showExportModal();
                this.exportReport().finally(() => {
                    // Re-enable button when export is complete
                    exportBtn.disabled = false;
                    exportBtn.textContent = 'Export HTML';
                });
            });
        }

        // PDF Export button
        const pdfBtn = document.getElementById('anomalies-pdf-btn');
        if (pdfBtn) {
            pdfBtn.addEventListener('click', () => {
                // Disable button during export
                pdfBtn.disabled = true;
                pdfBtn.textContent = 'Generating...';
                
                this.showExportModal();
                this.exportPDF().finally(() => {
                    // Re-enable button when export is complete
                    pdfBtn.disabled = false;
                    pdfBtn.textContent = 'Download PDF';
                });
            });
        }
    },

    /**
     * Show export loading modal
     */
    showExportModal() {
        // Remove existing modal if any
        this.hideExportModal();
        
        const modal = document.createElement('div');
        modal.id = 'export-modal';
        modal.className = 'export-modal-overlay';
        modal.innerHTML = `
            <div class="export-modal-content">
                <div class="export-spinner"></div>
                <h3 class="export-modal-title">Generating Report</h3>
                <p class="export-modal-message">Please wait while we generate your comprehensive anomaly analysis report...</p>
                <div class="export-progress-dots">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add styles dynamically if not already added
        if (!document.getElementById('export-modal-styles')) {
            const styles = document.createElement('style');
            styles.id = 'export-modal-styles';
            styles.textContent = `
                .export-modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: rgba(0, 0, 0, 0.7);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 10000;
                    backdrop-filter: blur(3px);
                }
                
                .export-modal-content {
                    background-color: #1f2937;
                    border: 1px solid #374151;
                    border-radius: 12px;
                    padding: 40px 30px;
                    text-align: center;
                    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
                    max-width: 400px;
                    width: 90%;
                }
                
                .export-spinner {
                    width: 50px;
                    height: 50px;
                    border: 4px solid #374151;
                    border-top: 4px solid #3b82f6;
                    border-radius: 50%;
                    animation: export-spin 1s linear infinite;
                    margin: 0 auto 20px;
                }
                
                @keyframes export-spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .export-modal-title {
                    color: #f3f4f6;
                    font-size: 1.25rem;
                    font-weight: 600;
                    margin: 0 0 10px 0;
                }
                
                .export-modal-message {
                    color: #d1d5db;
                    font-size: 0.95rem;
                    line-height: 1.5;
                    margin: 0 0 20px 0;
                }
                
                .export-progress-dots {
                    display: flex;
                    justify-content: center;
                    gap: 8px;
                }
                
                .export-progress-dots .dot {
                    width: 8px;
                    height: 8px;
                    background-color: #3b82f6;
                    border-radius: 50%;
                    animation: export-bounce 1.4s infinite ease-in-out both;
                }
                
                .export-progress-dots .dot:nth-child(1) { animation-delay: -0.32s; }
                .export-progress-dots .dot:nth-child(2) { animation-delay: -0.16s; }
                .export-progress-dots .dot:nth-child(3) { animation-delay: 0s; }
                
                @keyframes export-bounce {
                    0%, 80%, 100% {
                        transform: scale(0);
                    }
                    40% {
                        transform: scale(1);
                    }
                }
            `;
            document.head.appendChild(styles);
        }
    },

    /**
     * Hide export loading modal
     */
    hideExportModal() {
        const modal = document.getElementById('export-modal');
        if (modal) {
            modal.remove();
        }
    },

    /**
     * Export the anomaly analysis as a comprehensive HTML report
     */
    async exportReport() {
        try {
            if (!this.originalAnomaliesData) {
                this.hideExportModal();
                window.Utils?.showNotification('No data available to export', 'warning');
                return;
            }

            // Extract metadata from current analysis folder
            const metadata = await this.extractAnalysisMetadata();
            
            // Generate the HTML report
            const htmlContent = await this.generateHTMLReport(this.originalAnomaliesData, metadata);
            
            // Save the report to llm/reports folder
            const reportFileName = this.generateReportFileName(metadata);
            
            // Send to backend to save the file
            const response = await fetch('/api/anomalies/export-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    htmlContent: htmlContent,
                    fileName: reportFileName,
                    metadata: metadata
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.hideExportModal();
                window.Utils?.showNotification(
                    `Report exported successfully: ${reportFileName}`, 
                    'success'
                );
                
                // Optionally open the report in a new tab
                this.showReportPreview(htmlContent);
            } else {
                const errorText = await response.text();
                console.error('Export response error:', {
                    status: response.status,
                    statusText: response.statusText,
                    body: errorText
                });
                throw new Error(`Export failed: ${response.status} ${response.statusText} - ${errorText}`);
            }
        } catch (error) {
            console.error('Export error:', error);
            this.hideExportModal();
            window.Utils?.showNotification(`Export failed: ${error.message}`, 'error');
        }
    },

    /**
     * Extract metadata from the current analysis folder
     */
    async extractAnalysisMetadata() {
        const metadata = {
            regionName: 'Unknown Region',
            coordinates: null,
            sentDate: new Date().toISOString(),
            sentPrompt: 'Analysis prompt not available',
            uid: this.generateUID(),
            images: []
        };

        // Try to extract from current analysis folder name
        if (this.currentAnalysisFolder) {
            // Parse folder name format: REGION_MODEL_YYYYMMDD_HHMMSS_UID
            const parts = this.currentAnalysisFolder.split('_');
            if (parts.length >= 4) {
                metadata.regionName = parts[0];
                metadata.uid = parts[parts.length - 1];
                
                // Parse date from folder name
                const datePart = parts[parts.length - 3];
                const timePart = parts[parts.length - 2];
                if (datePart && timePart) {
                    const dateStr = `${datePart.substring(0, 4)}-${datePart.substring(4, 6)}-${datePart.substring(6, 8)}`;
                    const timeStr = `${timePart.substring(0, 2)}:${timePart.substring(2, 4)}:${timePart.substring(4, 6)}`;
                    metadata.sentDate = `${dateStr}T${timeStr}`;
                }
            }
            
            // Try to load request log for more details
            try {
                const logResponse = await fetch(`/llm/logs/${this.currentAnalysisFolder}/request_log.json`);
                if (logResponse.ok) {
                    const logData = await logResponse.json();
                    metadata.coordinates = logData.coordinates;
                    metadata.sentPrompt = logData.prompt || metadata.sentPrompt;
                    metadata.images = logData.images || [];
                }
            } catch (error) {
                console.warn('Could not load request log:', error);
            }
        }

        return metadata;
    },

    /**
     * Generate unique ID for report
     */
    generateUID() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    /**
     * Generate report file name
     */
    generateReportFileName(metadata) {
        const regionName = metadata.regionName.replace(/[^a-zA-Z0-9_-]/g, '_');
        const dateStr = new Date(metadata.sentDate).toISOString().split('T')[0].replace(/-/g, '');
        return `${regionName}_${dateStr}_${metadata.uid}_anomaly_report.html`;
    },

    /**
     * Generate comprehensive HTML report
     */
    async generateHTMLReport(anomalyData, metadata) {
        const reportDate = new Date().toLocaleDateString();
        const sentDate = new Date(metadata.sentDate).toLocaleDateString();
        
        // Generate images with bounding boxes for all anomalies
        const anomaliesWithImages = await Promise.all(
            (anomalyData.identified_anomalies || []).map(async (anomaly, index) => {
                const imagesWithBoundingBoxes = [];
                
                // Standard image types in sent_images folder
                const standardImageTypes = [
                    'CHM.png',
                    'HillshadeRGB.png', 
                    'LRM.png',
                    'Slope.png',
                    'SVF.png'
                ];
                
                // Generate images with bounding boxes for each image type
                for (const imageType of standardImageTypes) {
                    const imagePath = `/llm/logs/${this.currentAnalysisFolder}/sent_images/${imageType}`;
                    console.log(`Processing image: ${imageType} for anomaly ${index + 1}`);
                    console.log(`Image path: ${imagePath}`);
                    console.log(`Anomaly bounding boxes:`, anomaly.bounding_box_pixels);
                    
                    const imageWithBoundingBox = await this.generateImageWithBoundingBoxes(imagePath, anomaly);
                    
                    if (imageWithBoundingBox) {
                        console.log(`Successfully generated image with bounding box for: ${imageType}`);
                        imagesWithBoundingBoxes.push({
                            name: imageType.replace('.png', ''),
                            dataUrl: imageWithBoundingBox,
                            description: this.getImageDescription(imageType.replace('.png', ''))
                        });
                    } else {
                        console.warn(`Failed to generate image with bounding box for: ${imageType}`);
                    }
                }
                
                return {
                    ...anomaly,
                    imagesWithBoundingBoxes
                };
            })
        );
        
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anomaly Analysis Report - ${metadata.regionName}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: white;
            border-radius: 15px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .header h1 {
            color: #2c3e50;
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: 700;
        }
        
        .header .subtitle {
            color: #7f8c8d;
            font-size: 1.2em;
            margin-bottom: 20px;
        }
        
        .metadata {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .metadata-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        
        .metadata-label {
            font-weight: 600;
            color: #2c3e50;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metadata-value {
            margin-top: 5px;
            font-size: 1.1em;
            color: #34495e;
        }
        
        .section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        }
        
        .section h2 {
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3);
        }
        
        .summary-number {
            font-size: 3em;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .summary-label {
            font-size: 0.9em;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .images-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .image-card {
            background: #f8f9fa;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .image-card:hover {
            transform: translateY(-5px);
        }
        
        .image-card img {
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-bottom: 2px solid #e9ecef;
        }
        
        .image-info {
            padding: 15px;
        }
        
        .image-title {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .image-description {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        .anomaly-card {
            background: #fff;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
            border-left: 5px solid #e74c3c;
        }
        
        .anomaly-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .anomaly-title {
            color: #e74c3c;
            font-size: 1.3em;
            font-weight: 600;
            margin: 0;
        }
        
        .confidence-badge {
            background: linear-gradient(135deg, #27ae60, #2ecc71);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        .anomaly-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }
        
        .detail-section h4 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .evidence-list {
            list-style: none;
            padding: 0;
        }
        
        .evidence-item {
            background: #f8f9fa;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            border-left: 3px solid #3498db;
        }
        
        .evidence-label {
            font-weight: 600;
            color: #2c3e50;
            text-transform: uppercase;
            font-size: 0.8em;
        }
        
        .coordinates-display {
            background: #2c3e50;
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .prompt-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #9b59b6;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: white;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header { padding: 20px; }
            .section { padding: 20px; }
            .anomaly-details { grid-template-columns: 1fr; }
            .header h1 { font-size: 2em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🔍 Anomaly Analysis Report</h1>
            <p class="subtitle">AI-Powered Archaeological Feature Detection</p>
            
            <div class="metadata">
                <div class="metadata-item">
                    <div class="metadata-label">Region</div>
                    <div class="metadata-value">${metadata.regionName}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Analysis Date</div>
                    <div class="metadata-value">${sentDate}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Report ID</div>
                    <div class="metadata-value">${metadata.uid}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Generated</div>
                    <div class="metadata-value">${reportDate}</div>
                </div>
            </div>
            
            ${metadata.coordinates ? `
            <div class="coordinates-display">
                <strong>📍 Coordinates:</strong> 
                Lat: ${metadata.coordinates.lat?.toFixed(6) || 'N/A'}, 
                Lng: ${metadata.coordinates.lng?.toFixed(6) || 'N/A'}
            </div>
            ` : ''}
        </header>

        <section class="section">
            <h2>📊 Analysis Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-number">${anomalyData.analysis_summary?.number_of_anomalies || 0}</div>
                    <div class="summary-label">Anomalies Detected</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">${metadata.images?.length || 0}</div>
                    <div class="summary-label">Images Analyzed</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">${anomalyData.analysis_summary?.anomalies_detected ? 'YES' : 'NO'}</div>
                    <div class="summary-label">Features Found</div>
                </div>
            </div>
        </section>

        <section class="section">
            <h2>🖼️ Source Images</h2>
            <div class="images-grid">
                ${metadata.images?.map(img => `
                <div class="image-card">
                    <img src="/${img.path}" alt="${img.name}" onerror="this.style.display='none'">
                    <div class="image-info">
                        <div class="image-title">${img.name.toUpperCase()}</div>
                        <div class="image-description">${this.getImageDescription(img.name)}</div>
                    </div>
                </div>
                `).join('') || '<p>No images available</p>'}
            </div>
        </section>

        <section class="section">
            <h2>🚨 Identified Anomalies</h2>
            ${anomaliesWithImages?.map((anomaly, index) => `
            <div class="anomaly-card">
                <div class="anomaly-header">
                    <h3 class="anomaly-title">${anomaly.anomaly_id || `Anomaly ${index + 1}`}</h3>
                    <div class="confidence-badge">
                        ${((anomaly.confidence?.global_score || 0) * 100).toFixed(0)}% Confidence
                    </div>
                </div>
                
                <div class="anomaly-details">
                    <div class="detail-section">
                        <h4>Classification</h4>
                        <p><strong>Type:</strong> ${anomaly.classification?.type || 'Unknown'}</p>
                        <p><strong>Subtype:</strong> ${anomaly.classification?.subtype || 'N/A'}</p>
                        
                        <h4>Confidence Scores</h4>
                        ${Object.entries(anomaly.confidence?.individual_scores || {}).map(([key, value]) => `
                        <div class="evidence-item">
                            <div class="evidence-label">${key.toUpperCase()}</div>
                            <div>${(value * 100).toFixed(0)}%</div>
                        </div>
                        `).join('')}
                        
                        <h4>Bounding Box Coordinates</h4>
                        ${anomaly.bounding_box_pixels?.map(bb => `
                        <div class="evidence-item">
                            <div class="evidence-label">Detection Area</div>
                            <div>X: ${bb.x_min}-${bb.x_max}, Y: ${bb.y_min}-${bb.y_max}</div>
                        </div>
                        `).join('') || '<p>No bounding box data available.</p>'}
                    </div>
                    
                    <div class="detail-section">
                        <h4>Evidence per Image</h4>
                        <ul class="evidence-list">
                            ${Object.entries(anomaly.evidence_per_image || {}).map(([key, value]) => `
                            <li class="evidence-item">
                                <div class="evidence-label">${key.toUpperCase()}</div>
                                <div>${value}</div>
                            </li>
                            `).join('')}
                        </ul>
                        
                        <h4>Archaeological Interpretation</h4>
                        <p>${anomaly.archaeological_interpretation || 'No interpretation provided'}</p>
                    </div>
                </div>
                
                ${anomaly.imagesWithBoundingBoxes && anomaly.imagesWithBoundingBoxes.length > 0 ? `
                <div class="anomaly-images-section">
                    <h4>📸 Detection Evidence Images</h4>
                    <p class="image-section-description">Images showing the detected anomaly with white bounding box overlays indicating the precise location of archaeological features.</p>
                    <div class="images-grid">
                        ${anomaly.imagesWithBoundingBoxes.map(img => `
                        <div class="image-card">
                            <img src="${img.dataUrl}" alt="${img.name} with anomaly detection overlay" style="width: 100%; height: 250px; object-fit: contain; border: 2px solid #3498db;">
                            <div class="image-info">
                                <div class="image-title">${img.name.toUpperCase()}</div>
                                <div class="image-description">${img.description}</div>
                                <div class="detection-note">🎯 White boxes show detected anomaly locations</div>
                            </div>
                        </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
            `).join('') || '<p>No anomalies identified in this analysis.</p>'}
        </section>

        <section class="section">
            <h2>📝 Analysis Prompt</h2>
            <div class="prompt-section">${metadata.sentPrompt}</div>
        </section>
    </div>

    <footer class="footer">
        <p>Generated by SHO_to_Z Anomaly Detection System | ${reportDate}</p>
        <p>Report ID: ${metadata.uid} | Region: ${metadata.regionName}</p>
    </footer>
</body>
</html>`;
},

/**
 * Get description for image type
 */
getImageDescription(imageName) {
    const descriptions = {
        'hillshadergb': 'RGB Hillshade visualization showing terrain relief',
        'hillshade': 'Terrain relief visualization',
        'slope': 'Slope analysis showing gradient steepness',
        'aspect': 'Aspect analysis showing slope direction',
        'chm': 'Canopy Height Model showing vegetation heights',
        'lrm': 'Local Relief Model highlighting topographic features',
        'svf': 'Sky View Factor indicating terrain openness',
        'ndvi': 'Vegetation index from satellite imagery',
        'dtm': 'Digital Terrain Model showing ground elevation',
        'dsm': 'Digital Surface Model including all features'
    };
    
    const key = imageName.toLowerCase().replace(/[^a-z]/g, '');
    return descriptions[key] || 'Geospatial analysis layer';
},

/**
 * Show report preview in a new window
 */
showReportPreview(htmlContent) {
    const previewWindow = window.open('', '_blank');
    previewWindow.document.write(htmlContent);
    previewWindow.document.close();
},

    /**
     * Initialize image gallery for an individual anomaly
     * @param {number} anomalyIndex - Index of the anomaly
     * @param {Object} anomaly - The anomaly data
     */
    initializeImageGallery(anomalyIndex, anomaly) {
        // Store the anomaly data for this gallery
        this.galleryAnomalies = this.galleryAnomalies || {};
        this.galleryAnomalies[anomalyIndex] = anomaly;
        
        // Get list of available images from the analysis folder
        this.loadImagesForGallery(anomalyIndex);
    },

    /**
     * Load images for the gallery from the sent_images folder
     * @param {number} anomalyIndex - Index of the anomaly
     */
    async loadImagesForGallery(anomalyIndex) {
        if (!this.currentAnalysisFolder) {
            console.warn('No current analysis folder set for loading images');
            return;
        }

        const canvas = document.getElementById(`canvas-${anomalyIndex}`);
        const counter = document.getElementById(`counter-${anomalyIndex}`);
        const info = document.getElementById(`info-${anomalyIndex}`);
        
        if (!canvas || !counter || !info) {
            console.warn(`Gallery elements not found for anomaly ${anomalyIndex}`);
            return;
        }

        try {
            // Define the standard image types that should be in sent_images folder
            const standardImageTypes = [
                'CHM.png',
                'HillshadeRGB.png', 
                'LRM.png',
                'Slope.png',
                'SVF.png'
            ];

            // Create image objects for each standard image type
            const images = standardImageTypes.map(filename => ({
                name: filename.replace('.png', ''), // Remove .png extension for display
                path: `llm/logs/${this.currentAnalysisFolder}/sent_images/${filename}`,
                url: `/llm/logs/${this.currentAnalysisFolder}/sent_images/${filename}`
            }));

            if (images.length === 0) {
                this.showNoImagesMessage(canvas, info);
                return;
            }

            // Store images data for this gallery
            this.galleryImages = this.galleryImages || {};
            this.galleryImages[anomalyIndex] = images;
            this.currentImageIndex = this.currentImageIndex || {};
            this.currentImageIndex[anomalyIndex] = 0;

            // Update counter
            counter.textContent = `1 / ${images.length}`;

            // Load and display the first image
            await this.displayImageInGallery(anomalyIndex, 0);
            
        } catch (error) {
            console.error('Error loading images for gallery:', error);
            this.showErrorMessage(canvas, info, 'Failed to load images');
        }
    },

    /**
     * Display a specific image in the gallery
     * @param {number} anomalyIndex - Index of the anomaly
     * @param {number} imageIndex - Index of the image to display
     */
    async displayImageInGallery(anomalyIndex, imageIndex) {
        const canvas = document.getElementById(`canvas-${anomalyIndex}`);
        const info = document.getElementById(`info-${anomalyIndex}`);
        const counter = document.getElementById(`counter-${anomalyIndex}`);

        if (!this.galleryImages || !this.galleryImages[anomalyIndex]) {
            return;
        }

        const images = this.galleryImages[anomalyIndex];
        const image = images[imageIndex];

        if (!image) {
            return;
        }

        try {
            // Construct the image path
            const imagePath = `/${image.path}`;
            
            // Create and load the image
            const img = new Image();
            img.onload = () => {
                // Set canvas size to match image aspect ratio
                const maxWidth = canvas.parentElement.clientWidth - 20;
                const maxHeight = 400;
                
                let width = img.width;
                let height = img.height;
                
                // Scale down if too large
                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }
                if (height > maxHeight) {
                    width = (width * maxHeight) / height;
                    height = maxHeight;
                }
                
                canvas.width = width;
                canvas.height = height;
                
                // Draw the image on canvas
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, width, height);
                ctx.drawImage(img, 0, 0, width, height);
                
                // Draw bounding boxes if available
                this.drawBoundingBoxes(ctx, anomalyIndex, width, height, img.width, img.height);
                
                // Update info display
                const imageType = info.querySelector('.image-type');
                if (imageType) {
                    imageType.textContent = this.getImageDescription(image.name);
                }
                
                // Update counter
                if (counter) {
                    counter.textContent = `${imageIndex + 1} / ${images.length}`;
                }
                
                // Set up mouse tracking
                this.setupMouseTracking(canvas, anomalyIndex, img.width, img.height);
            };
            
            img.onerror = () => {
                this.showErrorMessage(canvas, info, `Failed to load image: ${image.name}`);
            };
            
            img.src = imagePath;
            
        } catch (error) {
            console.error('Error displaying image:', error);
            this.showErrorMessage(canvas, info, 'Error displaying image');
        }
    },

    /**
     * Draw bounding boxes on the canvas for detected anomalies
     * @param {CanvasRenderingContext2D} ctx - The canvas rendering context
     * @param {number} anomalyIndex - Index of the anomaly
     * @param {number} canvasWidth - Canvas width (scaled)
     * @param {number} canvasHeight - Canvas height (scaled)
     * @param {number} originalWidth - Original image width
     * @param {number} originalHeight - Original image height
     */
    drawBoundingBoxes(ctx, anomalyIndex, canvasWidth, canvasHeight, originalWidth, originalHeight) {
        // Get the anomaly data for this gallery
        if (!this.galleryAnomalies || !this.galleryAnomalies[anomalyIndex]) {
            return;
        }

        const anomaly = this.galleryAnomalies[anomalyIndex];
        
        // Check if bounding box data exists
        if (!anomaly.bounding_box_pixels || anomaly.bounding_box_pixels.length === 0) {
            return;
        }

        // Calculate scale factors from original image to canvas
        const scaleX = canvasWidth / originalWidth;
        const scaleY = canvasHeight / originalHeight;

        // Set up drawing style for bounding boxes
        ctx.strokeStyle = '#ffffff'; // White color for visibility
        ctx.lineWidth = 2;
        ctx.setLineDash([]); // Solid line
        
        // Draw each bounding box
        anomaly.bounding_box_pixels.forEach((bbox, index) => {
            // Scale bounding box coordinates to canvas size
            const x = bbox.x_min * scaleX;
            const y = bbox.y_min * scaleY;
            const width = (bbox.x_max - bbox.x_min) * scaleX;
            const height = (bbox.y_max - bbox.y_min) * scaleY;
            
            // Draw the bounding box rectangle
            ctx.strokeRect(x, y, width, height);
            
            // Add a label for the bounding box
            ctx.fillStyle = '#ffffff';
            ctx.font = '12px Arial';
            ctx.fillText(`Anomaly ${index + 1}`, x + 2, y - 4);
        });
    },

    /**
     * Setup mouse tracking for coordinate display
     * @param {HTMLCanvasElement} canvas - The canvas element
     * @param {number} anomalyIndex - Index of the anomaly
     * @param {number} originalWidth - Original image width
     * @param {number} originalHeight - Original image height
     */
    setupMouseTracking(canvas, anomalyIndex, originalWidth, originalHeight) {
        const coords = document.getElementById(`coords-${anomalyIndex}`);
        if (!coords) return;

        const handleMouseMove = (e) => {
            const rect = canvas.getBoundingClientRect();
            const canvasX = e.clientX - rect.left;
            const canvasY = e.clientY - rect.top;
            
            // Convert canvas coordinates to original image coordinates
            const scaleX = originalWidth / canvas.width;
            const scaleY = originalHeight / canvas.height;
            const originalX = Math.round(canvasX * scaleX);
            const originalY = Math.round(canvasY * scaleY);
            
            coords.textContent = `Canvas: (${Math.round(canvasX)}, ${Math.round(canvasY)}) | Original: (${originalX}, ${originalY})`;
        };

        const handleMouseLeave = () => {
            coords.textContent = 'Canvas: (0, 0) | Original: (0, 0)';
        };

        // Remove existing listeners
        canvas.removeEventListener('mousemove', handleMouseMove);
        canvas.removeEventListener('mouseleave', handleMouseLeave);
        
        // Add new listeners
        canvas.addEventListener('mousemove', handleMouseMove);
        canvas.addEventListener('mouseleave', handleMouseLeave);
    },

    /**
     * Show "no images" message
     * @param {HTMLCanvasElement} canvas - The canvas element
     * @param {HTMLElement} info - The info element
     */
    showNoImagesMessage(canvas, info) {
        canvas.width = 400;
        canvas.height = 200;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#374151';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#9ca3af';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('No images available', canvas.width / 2, canvas.height / 2);
        
        const imageType = info.querySelector('.image-type');
        if (imageType) {
            imageType.textContent = 'No images found';
        }
    },

    /**
     * Show error message
     * @param {HTMLCanvasElement} canvas - The canvas element
     * @param {HTMLElement} info - The info element
     * @param {string} message - Error message to display
     */
    showErrorMessage(canvas, info, message) {
        canvas.width = 400;
        canvas.height = 200;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#dc2626';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#ffffff';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Error loading image', canvas.width / 2, canvas.height / 2 - 10);
        ctx.fillText(message, canvas.width / 2, canvas.height / 2 + 10);
        
        const imageType = info.querySelector('.image-type');
        if (imageType) {
            imageType.textContent = 'Error';
        }
    },

    /**
     * Set up gallery navigation event listeners
     */
    setupGalleryNavigation() {
        // Remove existing listeners to prevent duplicates
        document.removeEventListener('click', this.galleryNavigationHandler);
        
        // Create bound handler for reuse
        this.galleryNavigationHandler = this.handleGalleryNavigation.bind(this);
        
        // Add event listener
        document.addEventListener('click', this.galleryNavigationHandler);
    },

    /**
     * Handle gallery navigation button clicks
     * @param {Event} e - Click event
     */
    handleGalleryNavigation(e) {
        if (!e.target.classList.contains('gallery-nav-btn')) {
            return;
        }

        const galleryIndex = parseInt(e.target.dataset.gallery);
        const direction = e.target.dataset.direction;

        if (isNaN(galleryIndex) || !direction) {
            return;
        }

        if (!this.galleryImages || !this.galleryImages[galleryIndex]) {
            return;
        }

        const images = this.galleryImages[galleryIndex];
        let currentIndex = this.currentImageIndex[galleryIndex] || 0;

        if (direction === 'prev') {
            currentIndex = currentIndex > 0 ? currentIndex - 1 : images.length - 1;
        } else if (direction === 'next') {
            currentIndex = currentIndex < images.length - 1 ? currentIndex + 1 : 0;
        }

        this.currentImageIndex[galleryIndex] = currentIndex;
        this.displayImageInGallery(galleryIndex, currentIndex);

        // Update button states
        this.updateNavigationButtons(galleryIndex, currentIndex, images.length);
    },

    /**
     * Update navigation button states
     * @param {number} galleryIndex - Index of the gallery
     * @param {number} currentIndex - Current image index
     * @param {number} totalImages - Total number of images
     */
    updateNavigationButtons(galleryIndex, currentIndex, totalImages) {
        const prevBtn = document.querySelector(`[data-gallery="${galleryIndex}"][data-direction="prev"]`);
        const nextBtn = document.querySelector(`[data-gallery="${galleryIndex}"][data-direction="next"]`);

        if (prevBtn && nextBtn) {
            // Enable/disable buttons (for single image, you might want to disable)
            if (totalImages <= 1) {
                prevBtn.disabled = true;
                nextBtn.disabled = true;
            } else {
                prevBtn.disabled = false;
                nextBtn.disabled = false;
            }
        }
    },

    /**
     * Generate base64 image with bounding boxes drawn for report
     * @param {string} imagePath - Path to the source image
     * @param {Object} anomaly - Anomaly data containing bounding box information
     * @returns {Promise<string>} - Base64 data URL of image with bounding boxes
     */
    async generateImageWithBoundingBoxes(imagePath, anomaly) {
        return new Promise((resolve, reject) => {
            console.log(`Generating image with bounding boxes for: ${imagePath}`);
            console.log(`Anomaly bounding boxes:`, anomaly.bounding_box_pixels);
            
            const img = new Image();
            img.crossOrigin = 'anonymous'; // Handle CORS issues
            
            img.onload = () => {
                console.log(`Image loaded successfully: ${imagePath} (${img.width}x${img.height})`);
                
                // Create canvas
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                // Set canvas size to match image
                canvas.width = img.width;
                canvas.height = img.height;
                
                // Draw the original image
                ctx.drawImage(img, 0, 0);
                
                // Draw bounding boxes if available
                if (anomaly.bounding_box_pixels && anomaly.bounding_box_pixels.length > 0) {
                    console.log(`Drawing ${anomaly.bounding_box_pixels.length} bounding boxes`);
                    
                    // Set up drawing style for bounding boxes
                    ctx.strokeStyle = '#ffffff'; // White color for visibility
                    ctx.lineWidth = Math.max(3, Math.min(img.width, img.height) / 200); // Adaptive line width
                    ctx.setLineDash([]); // Solid line
                    ctx.shadowColor = '#000000'; // Black shadow for better visibility
                    ctx.shadowBlur = 2;
                    ctx.shadowOffsetX = 1;
                    ctx.shadowOffsetY = 1;
                    
                    // Draw each bounding box
                    anomaly.bounding_box_pixels.forEach((bbox, index) => {
                        const x = bbox.x_min;
                        const y = bbox.y_min;
                        const width = bbox.x_max - bbox.x_min;
                        const height = bbox.y_max - bbox.y_min;
                        
                        console.log(`Drawing bounding box ${index + 1}: x=${x}, y=${y}, w=${width}, h=${height}`);
                        
                        // Validate bounding box coordinates
                        if (x >= 0 && y >= 0 && width > 0 && height > 0 && 
                            x + width <= img.width && y + height <= img.height) {
                            
                            // Draw the bounding box rectangle
                            ctx.strokeRect(x, y, width, height);
                            
                            // Add a label for the bounding box
                            const fontSize = Math.max(12, Math.min(img.width, img.height) / 40);
                            ctx.font = `bold ${fontSize}px Arial`;
                            const labelText = `Anomaly ${index + 1}`;
                            const labelWidth = ctx.measureText(labelText).width;
                            
                            // Draw label background
                            ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
                            ctx.fillRect(x, y - fontSize - 8, labelWidth + 12, fontSize + 8);
                            
                            // Draw label text
                            ctx.fillStyle = '#ffffff';
                            ctx.fillText(labelText, x + 6, y - 6);
                        } else {
                            console.warn(`Invalid bounding box coordinates for box ${index + 1}:`, bbox);
                        }
                    });
                    
                    // Reset shadow
                    ctx.shadowColor = 'transparent';
                    ctx.shadowBlur = 0;
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                } else {
                    console.log('No bounding boxes to draw for this anomaly');
                }
                
                // Convert canvas to base64
                const base64DataUrl = canvas.toDataURL('image/png', 0.9);
                console.log(`Successfully generated image with bounding boxes for: ${imagePath}`);
                resolve(base64DataUrl);
            };
            
            img.onerror = (error) => {
                console.error(`Failed to load image for bounding box generation: ${imagePath}`, error);
                console.log('Attempting to load image without CORS...');
                
                // Try loading without CORS as fallback
                const fallbackImg = new Image();
                fallbackImg.onload = () => {
                    console.log(`Fallback image loaded: ${imagePath}`);
                    
                    // Create canvas and draw without bounding boxes as last resort
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    canvas.width = fallbackImg.width;
                    canvas.height = fallbackImg.height;
                    ctx.drawImage(fallbackImg, 0, 0);
                    
                    const base64DataUrl = canvas.toDataURL('image/png', 0.9);
                    console.warn(`Returning image without bounding boxes for: ${imagePath}`);
                    resolve(base64DataUrl);
                };
                
                fallbackImg.onerror = () => {
                    console.error(`Complete failure to load image: ${imagePath}`);
                    resolve(null);
                };
                
                fallbackImg.src = imagePath;
            };
            
            // Try loading the image
            img.src = imagePath;
        });
    },

    /**
     * Export PDF report - generates HTML first if needed, then converts to PDF
     */
    async exportPDF() {
        try {
            if (!this.originalAnomaliesData) {
                this.hideExportModal();
                window.Utils?.showNotification('No data available to export', 'warning');
                return;
            }

            // Extract metadata from current analysis folder
            const metadata = await this.extractAnalysisMetadata();
            const reportFileName = this.generateReportFileName(metadata);
            
            // Check if HTML report already exists
            let htmlExists = false;
            try {
                const checkResponse = await fetch(`/api/anomalies/reports/${reportFileName}`);
                htmlExists = checkResponse.ok;
            } catch (error) {
                console.log('HTML report does not exist, will generate it first');
            }

            // Generate HTML report if it doesn't exist
            if (!htmlExists) {
                console.log('Generating HTML report first...');
                const htmlContent = await this.generateHTMLReport(this.originalAnomaliesData, metadata);
                
                // Save HTML report
                const htmlResponse = await fetch('/api/anomalies/export-report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        htmlContent: htmlContent,
                        fileName: reportFileName,
                        metadata: metadata
                    })
                });

                if (!htmlResponse.ok) {
                    const errorText = await htmlResponse.text();
                    throw new Error(`Failed to generate HTML report: ${htmlResponse.status} ${htmlResponse.statusText} - ${errorText}`);
                }
            }

            // Generate PDF from HTML
            console.log('Converting HTML to PDF...');
            const pdfResponse = await fetch(`/api/anomalies/generate-pdf/${reportFileName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (pdfResponse.ok) {
                const result = await pdfResponse.json();
                const pdfFileName = result.pdfFileName;
                
                // Download the PDF
                const downloadResponse = await fetch(`/api/anomalies/download-pdf/${pdfFileName}`);
                if (downloadResponse.ok) {
                    const blob = await downloadResponse.blob();
                    
                    // Create download link
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = pdfFileName;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    this.hideExportModal();
                    window.Utils?.showNotification(
                        `PDF report downloaded successfully: ${pdfFileName}`, 
                        'success'
                    );
                } else {
                    throw new Error(`Failed to download PDF: ${downloadResponse.statusText}`);
                }
            } else {
                const errorText = await pdfResponse.text();
                console.error('PDF generation response error:', {
                    status: pdfResponse.status,
                    statusText: pdfResponse.statusText,
                    body: errorText
                });
                
                // Check if it's a WeasyPrint availability issue
                if (pdfResponse.status === 503) {
                    throw new Error('PDF generation is not available on this server. Please try the HTML export instead.');
                } else {
                    throw new Error(`PDF generation failed: ${pdfResponse.status} ${pdfResponse.statusText} - ${errorText}`);
                }
            }
        } catch (error) {
            console.error('PDF export error:', error);
            this.hideExportModal();
            window.Utils?.showNotification(`PDF export failed: ${error.message}`, 'error');
        }
    },
};
