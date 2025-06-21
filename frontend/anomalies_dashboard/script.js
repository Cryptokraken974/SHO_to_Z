document.addEventListener('DOMContentLoaded', function () {
    const jsonData = {
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

    // Populate Analysis Summary
    document.getElementById('targetAreaId').textContent = jsonData.analysis_summary.target_area_id;
    document.getElementById('anomaliesDetected').textContent = jsonData.analysis_summary.anomalies_detected ? 'Yes' : 'No';
    document.getElementById('numberOfAnomalies').textContent = jsonData.analysis_summary.number_of_anomalies;

    // Populate Identified Anomalies
    const anomaliesContainer = document.getElementById('identifiedAnomalies');
    if (jsonData.identified_anomalies && jsonData.identified_anomalies.length > 0) {
        jsonData.identified_anomalies.forEach(anomaly => {
            const anomalyItem = document.createElement('article');
            anomalyItem.classList.add('anomaly-item');

            let classificationType = anomaly.classification.type || 'N/A';
            let classificationSubtype = anomaly.classification.subtype || 'N/A';

            let individualScoresHtml = '<p>No individual scores available.</p>';
            if (anomaly.confidence && anomaly.confidence.individual_scores) {
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
            if (anomaly.bounding_box_pixels && anomaly.bounding_box_pixels.length > 0) {
                boundingBoxHtml = anomaly.bounding_box_pixels
                    .map(bb => `<p>X: ${bb.x_min}-${bb.x_max}, Y: ${bb.y_min}-${bb.y_max}</p>`)
                    .join('');
            }

            anomalyItem.innerHTML = `
                <h3>${anomaly.anomaly_id}</h3>
                <p><strong>Type:</strong> ${classificationType}</p>
                <p><strong>Subtype:</strong> ${classificationSubtype}</p>

                <div class="confidence-section">
                    <h4>Confidence:</h4>
                    <p class="global-score">Global Score: ${anomaly.confidence ? anomaly.confidence.global_score : 'N/A'}</p>
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
            anomaliesContainer.appendChild(anomalyItem);
        });
    } else {
        anomaliesContainer.innerHTML = '<p>No anomalies identified.</p>';
    }
});
