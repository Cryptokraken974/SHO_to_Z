// Anomalies Dashboard Component
// Integrated into the main SHO_to_Z application

window.AnomaliesDashboard = {
    // Render the anomalies dashboard with provided data
    render(containerElement, jsonData) {
        if (!containerElement) {
            Utils.log('error', 'AnomaliesDashboard: Container element not provided');
            return;
        }

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

        anomalies.forEach(anomaly => {
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
        });
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
