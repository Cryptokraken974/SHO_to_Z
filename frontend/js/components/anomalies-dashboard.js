// Anomalies Dashboard Component
// Integrated into the main SHO_to_Z application

window.AnomaliesDashboard = {
    // Store the current analysis folder for image paths
    currentAnalysisFolder: null,

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

    populateAnomalies(anomalies) {
        const anomaliesContainer = document.getElementById('anomaliesContainer');
        if (!anomaliesContainer) return;

        if (anomalies.length === 0) {
            anomaliesContainer.innerHTML = '<p class="no-anomalies">No anomalies identified.</p>';
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
    },

    async initializeImageGallery(anomalyIndex, anomaly) {
        const canvas = document.getElementById(`canvas-${anomalyIndex}`);
        const ctx = canvas.getContext('2d');
        
        // Get available images for the analysis
        const images = await this.getAnalysisImages();
        
        if (images.length === 0) {
            canvas.width = 400;
            canvas.height = 200;
            ctx.fillStyle = '#374151';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#9CA3AF';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('No images available', canvas.width / 2, canvas.height / 2);
            return;
        }

        // Store gallery data
        if (!this.galleries) this.galleries = {};
        this.galleries[anomalyIndex] = {
            images: images,
            currentIndex: 0,
            anomaly: anomaly,
            canvas: canvas,
            ctx: ctx
        };

        // Load first image
        this.loadGalleryImage(anomalyIndex, 0);
        this.updateGalleryCounter(anomalyIndex);
    },

    async getAnalysisImages() {
        // If we don't have the analysis folder, we can't get the images
        if (!this.currentAnalysisFolder) {
            console.warn('No analysis folder specified, cannot load images');
            return [];
        }

        // Extract the base folder name without _response.json suffix
        const folderName = this.currentAnalysisFolder.replace('_response.json', '');
        
        // Define the expected image types and their paths in the sent_images folder
        const imageTypes = [
            { type: 'CHM', filename: 'CHM.png', name: 'Canopy Height Model' },
            { type: 'LRM', filename: 'LRM.png', name: 'Local Relief Model' },
            { type: 'SVF', filename: 'SVF.png', name: 'Sky View Factor' },
            { type: 'Slope', filename: 'Slope.png', name: 'Slope' },
            { type: 'HillshadeRGB', filename: 'HillshadeRGB.png', name: 'RGB Hillshade' },
            { type: 'TintOverlay', filename: 'TintOverlay.png', name: 'Tint Overlay' }
        ];

        // Check for NDVI with dynamic naming pattern
        // Extract region name: OR_WizardIsland_gpt4visionpreview_... -> OR_WizardIsland
        const regionMatch = folderName.match(/^([^_]+_[^_]+)/);
        if (regionMatch) {
            const regionName = regionMatch[1];
            imageTypes.push({
                type: 'NDVI', 
                filename: `${regionName}_20250531_sentinel2_NDVI.png`, 
                name: 'NDVI'
            });
        }

        // Build paths to the sent_images folder
        const availableImages = [];
        for (const imageType of imageTypes) {
            const imagePath = `/llm/logs/${folderName}/sent_images/${imageType.filename}`;
            
            try {
                // Test if image loads
                const img = new Image();
                await new Promise((resolve, reject) => {
                    img.onload = resolve;
                    img.onerror = reject;
                    img.src = imagePath;
                });
                
                availableImages.push({
                    type: imageType.type,
                    path: imagePath,
                    name: imageType.name
                });
                
            } catch (error) {
                console.log(`Image not available: ${imagePath}`);
            }
        }

        console.log(`Found ${availableImages.length} available images for analysis: ${folderName}`);
        return availableImages;
    },

    async loadGalleryImage(anomalyIndex, imageIndex) {
        const gallery = this.galleries[anomalyIndex];
        if (!gallery || !gallery.images[imageIndex]) return;

        const imageInfo = gallery.images[imageIndex];
        const canvas = gallery.canvas;
        const ctx = gallery.ctx;

        try {
            const img = new Image();
            img.crossOrigin = 'anonymous'; // Handle CORS if needed
            
            await new Promise((resolve, reject) => {
                img.onload = () => {
                    // Set canvas size to match image (max width 600px for display)
                    const maxDisplayWidth = 600;
                    canvas.width = Math.min(img.width, maxDisplayWidth);
                    canvas.height = (canvas.width / img.width) * img.height;
                    
                    // Store scaling factors in the gallery object
                    gallery.scaleX = canvas.width / img.width;
                    gallery.scaleY = canvas.height / img.height;
                    gallery.originalWidth = img.width;
                    gallery.originalHeight = img.height;
                    
                    // Debug logging
                    console.log(`Image loaded: ${imageInfo.name}`);
                    console.log(`Original size: ${img.width}x${img.height}`);
                    console.log(`Canvas size: ${canvas.width}x${canvas.height}`);
                    console.log(`Scale factors: scaleX=${gallery.scaleX.toFixed(3)}, scaleY=${gallery.scaleY.toFixed(3)}`);
                    
                    // Draw the image
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    
                    // Draw bounding boxes
                    this.drawBoundingBoxes(ctx, gallery.anomaly, gallery.scaleX, gallery.scaleY);
                    
                    // Optional: Draw debug markers (uncomment to enable)
                    // this.drawDebugMarkers(ctx, gallery.scaleX, gallery.scaleY, img.width, img.height);
                    
                    resolve();
                };
                img.onerror = reject;
                img.src = imageInfo.path;
            });

            // Set up mouse tracking for this canvas
            this.setupMouseTracking(anomalyIndex);

            // Update image info
            const infoElement = document.getElementById(`info-${anomalyIndex}`);
            if (infoElement) {
                infoElement.querySelector('.image-type').textContent = imageInfo.name;
            }

        } catch (error) {
            console.error('Failed to load image:', imageInfo.path, error);
            
            // Draw error state
            canvas.width = 400;
            canvas.height = 200;
            ctx.fillStyle = '#374151';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#EF4444';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('Failed to load image', canvas.width / 2, canvas.height / 2);
        }
    },

    drawBoundingBoxes(ctx, anomaly, scaleX, scaleY) {
        if (!anomaly.bounding_box_pixels || anomaly.bounding_box_pixels.length === 0) return;

        console.log(`Drawing bounding boxes for ${anomaly.anomaly_id}:`);
        console.log(`Scale factors: scaleX=${scaleX.toFixed(3)}, scaleY=${scaleY.toFixed(3)}`);

        // Set bounding box style
        ctx.strokeStyle = '#FFFFFF'; // White color
        ctx.lineWidth = 2;
        ctx.setLineDash([]); // Continuous line (no dashes)

        anomaly.bounding_box_pixels.forEach((bbox, index) => {
            const x = bbox.x_min * scaleX;
            const y = bbox.y_min * scaleY;
            const width = (bbox.x_max - bbox.x_min) * scaleX;
            const height = (bbox.y_max - bbox.y_min) * scaleY;

            console.log(`  Bbox ${index + 1}:`);
            console.log(`    Original: x_min=${bbox.x_min}, y_min=${bbox.y_min}, x_max=${bbox.x_max}, y_max=${bbox.y_max}`);
            console.log(`    Scaled: x=${x.toFixed(1)}, y=${y.toFixed(1)}, width=${width.toFixed(1)}, height=${height.toFixed(1)}`);

            // Draw bounding box
            ctx.strokeRect(x, y, width, height);

            // Draw corner markers for precise coordinate verification
            ctx.fillStyle = '#00FF00'; // Bright green for corners
            const cornerSize = 3;
            
            // Top-left corner (x_min, y_min)
            ctx.fillRect(x - cornerSize/2, y - cornerSize/2, cornerSize, cornerSize);
            
            // Top-right corner (x_max, y_min) 
            ctx.fillRect(x + width - cornerSize/2, y - cornerSize/2, cornerSize, cornerSize);
            
            // Bottom-left corner (x_min, y_max)
            ctx.fillRect(x - cornerSize/2, y + height - cornerSize/2, cornerSize, cornerSize);
            
            // Bottom-right corner (x_max, y_max)
            ctx.fillRect(x + width - cornerSize/2, y + height - cornerSize/2, cornerSize, cornerSize);

            // Draw label background
            const label = anomaly.anomaly_id;
            ctx.font = '12px Arial';
            const labelWidth = ctx.measureText(label).width;
            
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(x, y - 20, labelWidth + 8, 16);
            
            // Draw label text
            ctx.fillStyle = '#FFFFFF';
            ctx.fillText(label, x + 4, y - 8);
        });

        // Reset line dash
        ctx.setLineDash([]);
    },

    // Debug method to verify coordinate system
    drawDebugMarkers(ctx, scaleX, scaleY, originalWidth, originalHeight) {
        ctx.fillStyle = '#FF00FF'; // Magenta for debug markers
        const markerSize = 5;
        
        // Draw markers at known positions with labels
        const debugPoints = [
            { x: 0, y: 0, label: '(0,0)' },
            { x: 100, y: 100, label: '(100,100)' },
            { x: originalWidth - 1, y: 0, label: `(${originalWidth-1},0)` },
            { x: 0, y: originalHeight - 1, label: `(0,${originalHeight-1})` },
            { x: originalWidth - 1, y: originalHeight - 1, label: `(${originalWidth-1},${originalHeight-1})` }
        ];
        
        debugPoints.forEach(point => {
            const scaledX = point.x * scaleX;
            const scaledY = point.y * scaleY;
            
            // Draw marker
            ctx.fillRect(scaledX - markerSize/2, scaledY - markerSize/2, markerSize, markerSize);
            
            // Draw label
            ctx.fillStyle = '#FFFFFF';
            ctx.font = '10px Arial';
            ctx.fillText(point.label, scaledX + 5, scaledY - 5);
            ctx.fillStyle = '#FF00FF';
        });
    },

    setupMouseTracking(anomalyIndex) {
        const gallery = this.galleries[anomalyIndex];
        if (!gallery) return;

        const canvas = gallery.canvas;
        const coordsElement = document.getElementById(`coords-${anomalyIndex}`);
        
        if (!coordsElement) return;

        // Remove existing mouse listeners to avoid duplicates
        canvas.removeEventListener('mousemove', gallery.mouseMoveHandler);
        canvas.removeEventListener('mouseleave', gallery.mouseLeaveHandler);

        // Create mouse move handler
        gallery.mouseMoveHandler = (event) => {
            const rect = canvas.getBoundingClientRect();
            const canvasX = event.clientX - rect.left;
            const canvasY = event.clientY - rect.top;
            
            // Convert canvas coordinates to original image coordinates
            const originalX = Math.round(canvasX / gallery.scaleX);
            const originalY = Math.round(canvasY / gallery.scaleY);
            
            // Update coordinates display in JSON format
            coordsElement.textContent = `Canvas: (${Math.round(canvasX)}, ${Math.round(canvasY)}) | Original: {"x": ${originalX}, "y": ${originalY}}`;
        };

        // Create mouse leave handler
        gallery.mouseLeaveHandler = () => {
            coordsElement.textContent = `Canvas: (0, 0) | Original: {"x": 0, "y": 0}`;
        };

        // Add event listeners
        canvas.addEventListener('mousemove', gallery.mouseMoveHandler);
        canvas.addEventListener('mouseleave', gallery.mouseLeaveHandler);
    },

    updateGalleryCounter(anomalyIndex) {
        const gallery = this.galleries[anomalyIndex];
        if (!gallery) return;

        const counter = document.getElementById(`counter-${anomalyIndex}`);
        if (counter) {
            counter.textContent = `${gallery.currentIndex + 1} / ${gallery.images.length}`;
        }
    },

    setupGalleryNavigation() {
        // Remove existing listeners first
        document.removeEventListener('click', this.galleryNavigationHandler);
        
        // Add new listener
        this.galleryNavigationHandler = (event) => {
            if (event.target.classList.contains('gallery-nav-btn')) {
                const galleryIndex = parseInt(event.target.dataset.gallery);
                const direction = event.target.dataset.direction;
                
                const gallery = this.galleries[galleryIndex];
                if (!gallery) return;

                if (direction === 'next') {
                    gallery.currentIndex = (gallery.currentIndex + 1) % gallery.images.length;
                } else if (direction === 'prev') {
                    gallery.currentIndex = (gallery.currentIndex - 1 + gallery.images.length) % gallery.images.length;
                }

                this.loadGalleryImage(galleryIndex, gallery.currentIndex);
                this.updateGalleryCounter(galleryIndex);
            }
        };

        document.addEventListener('click', this.galleryNavigationHandler);
    },

    // Test data (same as original script.js)
    getTestData() {
        return {
            "analysis_summary": {
                "target_area_id": "WizardIsland_20250621",
                "anomalies_detected": true,
                "number_of_anomalies": 3
            },
            "identified_anomalies": [
                {
                    "anomaly_id": "WizardIsland_Circle_01",
                    "classification": {
                        "type": "Settlement Platform",
                        "subtype": "N/A"
                    },
                    "confidence": {
                        "global_score": 0.95,
                        "individual_scores": {
                            "lrm": 0.9,
                            "svf": 0.8,
                            "slope": 1.0,
                            "chm": 0.9,
                            "ndvi": 0.2
                        }
                    },
                    "evidence_per_image": {
                        "lrm": "Bright, regular circular embanked ring with strong positive relief; inner depression subtle but present.",
                        "svf": "High SVF values along the rim, indicating raised, open structure; rim clearly defined.",
                        "slope": "Exceptionally sharp, continuous high-slope band forms a perfect ring; steep faces are unambiguous.",
                        "chm": "Notably lower and more uniform canopy height within the ring, abrupt transition at rim.",
                        "ndvi": "Slight vegetation anomaly inside ring; pattern is faint but detectable."
                    },
                    "archaeological_interpretation": "This is a large constructed earthen platform or mound, likely for settlement or ceremonial use, due to its regularity, topographic prominence, and vegetation modification.",
                    "bounding_box_pixels": [
                        { "x_min": 300, "y_min": 600, "x_max": 750, "y_max": 1050 }
                    ]
                },
                {
                    "anomaly_id": "WizardIsland_Arc_02",
                    "classification": {
                        "type": "Causeway",
                        "subtype": "Curvilinear"
                    },
                    "confidence": {
                        "global_score": 0.7,
                        "individual_scores": {
                            "lrm": 0.8,
                            "svf": 0.6,
                            "slope": 0.7,
                            "chm": 0.5,
                            "ndvi": 0.2
                        }
                    },
                    "evidence_per_image": {
                        "lrm": "Curving positive-relief line south/southwest of main circle, visible as a continuous arc.",
                        "svf": "The arc is subtly defined; SVF contrast is weaker than the main circle but present.",
                        "slope": "The arc shows as a moderately steep, continuous band, distinct from the background.",
                        "chm": "Canopy is slightly lower and more uniform along the arc, especially toward the circle.",
                        "ndvi": "Very faint vegetation anomaly, barely above background noise."
                    },
                    "archaeological_interpretation": "This is likely a causeway or raised path, connecting or encircling the main platform. Its geometry and continuity suggest intentional construction.",
                    "bounding_box_pixels": [
                        { "x_min": 120, "y_min": 900, "x_max": 700, "y_max": 1200 }
                    ]
                },
                {
                    "anomaly_id": "WizardIsland_Escarpment_03",
                    "classification": {
                        "type": "Settlement Platform",
                        "subtype": "Edge/Escarpment"
                    },
                    "confidence": {
                        "global_score": 0.8,
                        "individual_scores": {
                            "lrm": 0.7,
                            "svf": 0.7,
                            "slope": 0.95,
                            "chm": 0.7,
                            "ndvi": 0.1
                        }
                    },
                    "evidence_per_image": {
                        "lrm": "Sharp, elongated positive-relief feature along the eastern edge of the area; unnatural linearity.",
                        "svf": "Strong SVF contrast at the scarp; open sky above the break.",
                        "slope": "Very strong, continuous steep slope delineating the escarpment; stands out sharply.",
                        "chm": "Lower canopy at the edge; abrupt transition visible.",
                        "ndvi": "Virtually no vegetation anomaly detected."
                    },
                    "archaeological_interpretation": "This feature could be an artificial terrace, edge of a constructed settlement, or defensive earthwork, as shown by the abrupt topography and clear vegetation boundary.",
                    "bounding_box_pixels": [
                        { "x_min": 830, "y_min": 600, "x_max": 1100, "y_max": 1200 }
                    ]
                }
            ]
        };
    }
};
