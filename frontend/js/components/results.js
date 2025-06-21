window.ResultsManager = {
    logListContainerId: 'results-log-list', // ID of the div in results-tab's left panel
    selectAllButtonId: 'results-select-all-btn',
    deleteButtonId: 'results-delete-btn',
    mainDashboardContainerId: 'results-main-panel', // ID of the div for the dashboard
    initialized: false,
    selectedLogFile: null, // Track the currently selected log file

    init() {
        if (this.initialized) {
            return;
        }
        Utils.log('info', 'Initializing ResultsManager...');
        this.fetchResultsList();
        this.attachEventListeners();
        this.initialized = true;
        Utils.log('info', 'ResultsManager initialized.');
    },

    attachEventListeners() {
        const selectAllButton = document.getElementById(this.selectAllButtonId);
        if (selectAllButton) {
            selectAllButton.addEventListener('click', () => {
                this.handleSelectAll();
            });
        }
        
        const deleteButton = document.getElementById(this.deleteButtonId);
        if (deleteButton) {
            deleteButton.addEventListener('click', () => {
                this.handleDeleteSelected();
            });
        }
        // Event listener for individual log item clicks will be added in displayResultsList
    },

    async fetchResultsList() {
        Utils.log('info', 'Fetching OpenAI result logs list...');
        const logListContainer = document.getElementById(this.logListContainerId);
        if (!logListContainer) {
            Utils.log('error', `Element with ID ${this.logListContainerId} not found.`);
            return;
        }
        logListContainer.innerHTML = '<p class="text-gray-400">Loading results...</p>';

        try {
            const response = await fetch('/api/results/list'); // Actual endpoint

            if (response.ok) {
                const data = await response.json();
                if (data.logs) {
                    this.displayResultsList(data.logs);
                } else {
                    // Handle cases where data.logs might be missing even if response is ok
                    logListContainer.innerHTML = '<p class="text-red-500">Error: Response from server is missing "logs" data.</p>';
                    Utils.log('error', 'Failed to fetch results list: "logs" field missing in response.');
                }
            } else {
                const errorText = await response.text(); // Get error message from server
                logListContainer.innerHTML = `<p class="text-red-500">Error fetching results: ${response.status} ${errorText}</p>`;
                Utils.log('error', `Failed to fetch results list: ${response.status} ${errorText}`);
            }
        } catch (error) {
            logListContainer.innerHTML = `<p class="text-red-500">Exception fetching results: ${error.message}</p>`;
            Utils.log('error', 'Exception in fetchResultsList:', error);
        }
    },

    displayResultsList(logs) {
        const logListContainer = document.getElementById(this.logListContainerId);
        if (!logs || logs.length === 0) {
            logListContainer.innerHTML = '<p class="text-gray-400">No results found.</p>';
            return;
        }

        const ul = document.createElement('ul');
        ul.className = 'space-y-2';
        logs.forEach(logFile => {
            const li = document.createElement('li');
            li.className = 'p-2 bg-gray-700 hover:bg-gray-600 rounded-md cursor-pointer text-white text-sm';
            li.textContent = logFile.replace('.json', ''); // Display cleaner name
            li.setAttribute('data-logfile', logFile);
            li.addEventListener('click', (event) => {
                // Remove selection from other items
                ul.querySelectorAll('li').forEach(item => {
                    item.classList.remove('bg-blue-600', 'bg-blue-700');
                    item.classList.add('bg-gray-700');
                });
                
                // Add selection to clicked item
                li.classList.remove('bg-gray-700');
                li.classList.add('bg-blue-600');
                
                // Track selected file and show delete button
                this.selectedLogFile = event.target.getAttribute('data-logfile');
                this.showDeleteButton();
                
                this.handleLogItemClick(this.selectedLogFile);
            });
            ul.appendChild(li);
        });
        logListContainer.innerHTML = ''; // Clear loading message
        logListContainer.appendChild(ul);
        Utils.log('info', `Displayed ${logs.length} result logs.`);
    },

    handleLogItemClick(logFile) {
        Utils.log('info', `Log item clicked: ${logFile}`);
        const dashboardContainer = document.getElementById(this.mainDashboardContainerId);
        if (dashboardContainer) {
            // Clear container and show loading state
            dashboardContainer.innerHTML = `
                <h2 class="text-white text-lg font-semibold mb-3">Archaeological Analysis: ${logFile.replace('.json', '')}</h2>
                <p class="text-gray-300 mb-2">Loading anomaly analysis results...</p>
            `;

            // Try to fetch actual results from the API
            this.fetchAndDisplayAnomalyResults(logFile, dashboardContainer);
        }
    },

    async fetchAndDisplayAnomalyResults(logFile, containerElement) {
        try {
            // Try to fetch real data first
            const response = await fetch(`/api/results/get/${logFile}`);
            if (response.ok) {
                const resultData = await response.json();
                
                // Extract the actual OpenAI response
                let openaiResponse = resultData.openai_response;
                if (typeof openaiResponse === 'string') {
                    // Try to extract JSON from markdown code blocks
                    openaiResponse = this.extractJsonFromResponse(openaiResponse);
                }
                
                // Check if the data contains anomaly analysis results
                if (this.isAnomalyData(openaiResponse)) {
                    this.displayAnomalyDashboard(containerElement, openaiResponse, logFile);
                } else {
                    // Fall back to regular results display
                    this.displayRegularResults(containerElement, resultData, logFile);
                }
            } else {
                const errorText = await response.text();
                Utils.log('error', `HTTP ${response.status}: ${errorText}`);
                // API endpoint not available, show demo dashboard with test data
                this.displayAnomalyDashboard(containerElement, null, logFile);
            }
        } catch (error) {
            Utils.log('warn', `Could not fetch results for ${logFile}, showing demo dashboard:`, error);
            // Show demo dashboard with test data
            this.displayAnomalyDashboard(containerElement, null, logFile);
        }
    },

    extractJsonFromResponse(responseText) {
        // Extract JSON from markdown code blocks
        // Pattern: ```json\n{...}\n```
        const jsonMatch = responseText.match(/```json\s*\n([\s\S]*?)\n```/);
        if (jsonMatch) {
            try {
                return JSON.parse(jsonMatch[1]);
            } catch (e) {
                Utils.log('error', 'Failed to parse JSON from response:', e);
                return null;
            }
        }
        
        // Try to parse the response directly as JSON
        try {
            return JSON.parse(responseText);
        } catch (e) {
            Utils.log('warn', 'Response is not valid JSON:', e);
            return null;
        }
    },

    displayAnomalyDashboard(containerElement, data, logFile = null) {
        if (window.AnomaliesDashboard) {
            // The anomaly data is now stored directly in the response
            const anomalyData = data;
            
            // Pass the log file name to the dashboard for image loading
            window.AnomaliesDashboard.render(containerElement, anomalyData, logFile);
        } else {
            Utils.log('error', 'AnomaliesDashboard component not loaded');
            containerElement.innerHTML = `
                <p class="text-red-500">Error: Anomalies Dashboard component not available</p>
            `;
        }
    },

    displayRegularResults(containerElement, resultData, logFile) {
        // Display regular OpenAI results (non-anomaly format)
        containerElement.innerHTML = `
            <h2 class="text-white text-lg font-semibold mb-3">OpenAI Analysis: ${logFile.replace('.json', '')}</h2>
            <div class="bg-gray-800 p-4 rounded-md text-sm">
                <h3 class="text-sky-400 font-semibold mb-2">Analysis Results:</h3>
                <pre class="text-gray-300 whitespace-pre-wrap overflow-x-auto">${JSON.stringify(resultData, null, 2)}</pre>
            </div>
        `;
    },

    isAnomalyData(data) {
        // Check if the data structure matches anomaly analysis format
        // The response is now stored directly without wrapper
        return data && 
               (data.analysis_summary || data.identified_anomalies) ||
               (data.anomalies_detected !== undefined) ||
               (data.number_of_anomalies !== undefined);
    },

    handleSelectAll() {
        Utils.log('info', '"Select All" clicked.');
        
        // Clear selection and hide delete button
        this.hideDeleteButton();
        
        // Remove selection styling from all items
        const logListContainer = document.getElementById(this.logListContainerId);
        if (logListContainer) {
            logListContainer.querySelectorAll('li').forEach(item => {
                item.classList.remove('bg-blue-600', 'bg-blue-700');
                item.classList.add('bg-gray-700');
            });
        }
        
        const dashboardContainer = document.getElementById(this.mainDashboardContainerId);
        if (dashboardContainer) {
            dashboardContainer.innerHTML = `
                <h2 class="text-white text-lg font-semibold mb-3">Aggregated Archaeological Analysis Dashboard</h2>
                <p class="text-gray-300 mb-2">Loading aggregated anomaly analysis results...</p>
            `;

            // Try to fetch aggregated results
            this.fetchAndDisplayAggregatedResults(dashboardContainer);
        }
    },

    showDeleteButton() {
        const deleteButton = document.getElementById(this.deleteButtonId);
        if (deleteButton) {
            deleteButton.classList.remove('hidden');
        }
    },

    hideDeleteButton() {
        const deleteButton = document.getElementById(this.deleteButtonId);
        if (deleteButton) {
            deleteButton.classList.add('hidden');
        }
        this.selectedLogFile = null;
    },

    async handleDeleteSelected() {
        if (!this.selectedLogFile) {
            Utils.showNotification('No log file selected for deletion', 'warning');
            return;
        }

        // Show confirmation dialog
        const confirmed = confirm(
            `Are you sure you want to delete the result log "${this.selectedLogFile.replace('.json', '')}" and all its associated files?\n\n` +
            `This will delete:\n` +
            `• The response log file\n` +
            `• The associated request log file\n` +
            `• Any related directories\n\n` +
            `This action cannot be undone.`
        );

        if (!confirmed) {
            return;
        }

        try {
            Utils.showNotification('Deleting files...', 'info');
            
            const response = await fetch(`/api/results/delete/${encodeURIComponent(this.selectedLogFile)}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                const result = await response.json();
                Utils.showNotification(
                    `Successfully deleted ${result.files_deleted?.length || 0} files` + 
                    (result.directories_deleted?.length > 0 ? ` and ${result.directories_deleted.length} directories` : ''),
                    'success'
                );
                
                // Hide delete button and clear selection
                this.hideDeleteButton();
                
                // Clear the main panel
                const dashboardContainer = document.getElementById(this.mainDashboardContainerId);
                if (dashboardContainer) {
                    dashboardContainer.innerHTML = `
                        <h1 class="text-white text-xl font-bold">Results Dashboard</h1>
                        <p class="text-gray-300">Select a result from the left panel to view details, or click "Select All" for a summary.</p>
                    `;
                }
                
                // Refresh the results list
                this.fetchResultsList();
                
            } else {
                const errorText = await response.text();
                throw new Error(`${response.status}: ${errorText}`);
            }
        } catch (error) {
            Utils.log('error', 'Failed to delete result log:', error);
            Utils.showNotification(`Failed to delete result log: ${error.message}`, 'error');
        }
    },

    async fetchAndDisplayAggregatedResults(containerElement) {
        try {
            // Try to fetch aggregated data
            const response = await fetch('/api/results/get_all');
            if (response.ok) {
                const aggregatedData = await response.json();
                this.displayAggregatedAnomalyDashboard(containerElement, aggregatedData);
            } else {
                // API endpoint not available, show demo aggregated dashboard
                this.displayAggregatedAnomalyDashboard(containerElement, null);
            }
        } catch (error) {
            Utils.log('warn', 'Could not fetch aggregated results, showing demo dashboard:', error);
            // Show demo aggregated dashboard
            this.displayAggregatedAnomalyDashboard(containerElement, null);
        }
    },

    displayAggregatedAnomalyDashboard(containerElement, aggregatedData) {
        // Create a combined anomaly dataset from multiple analyses for demo
        if (!aggregatedData) {
            aggregatedData = this.createDemoAggregatedData();
        }

        if (window.AnomaliesDashboard) {
            // For aggregated data, we don't have a specific log file, so pass null
            window.AnomaliesDashboard.render(containerElement, aggregatedData, null);
        } else {
            Utils.log('error', 'AnomaliesDashboard component not loaded');
            containerElement.innerHTML = `
                <p class="text-red-500">Error: Anomalies Dashboard component not available</p>
            `;
        }
    },

    createDemoAggregatedData() {
        // Create demo data showing multiple regions analyzed
        return {
            "analysis_summary": {
                "target_area_id": "Multiple_Regions_Analysis",
                "anomalies_detected": true,
                "number_of_anomalies": 7,
                "regions_analyzed": 4,
                "total_analyses": 8
            },
            "identified_anomalies": [
                {
                    "anomaly_id": "WizardIsland_Circle_01",
                    "classification": { "type": "Settlement Platform", "subtype": "N/A" },
                    "confidence": { "global_score": 0.95, "individual_scores": { "lrm": 0.9, "svf": 0.8, "slope": 1.0, "chm": 0.9, "ndvi": 0.2 } },
                    "evidence_per_image": {
                        "lrm": "Bright, regular circular embanked ring with strong positive relief; inner depression subtle but present.",
                        "svf": "High SVF values along the rim, indicating raised, open structure; rim clearly defined."
                    },
                    "archaeological_interpretation": "Large constructed earthen platform or mound, likely for settlement or ceremonial use.",
                    "bounding_box_pixels": [{ "x_min": 300, "y_min": 600, "x_max": 750, "y_max": 1050 }]
                },
                {
                    "anomaly_id": "PRE_A05_Terrace_01",
                    "classification": { "type": "Agricultural Terrace", "subtype": "Linear" },
                    "confidence": { "global_score": 0.82, "individual_scores": { "lrm": 0.85, "svf": 0.75, "slope": 0.9, "chm": 0.8, "ndvi": 0.8 } },
                    "evidence_per_image": {
                        "lrm": "Linear raised features following contour lines, consistent with terracing.",
                        "slope": "Regular slope breaks indicating constructed terraces."
                    },
                    "archaeological_interpretation": "Ancient agricultural terracing system, likely pre-Columbian in origin.",
                    "bounding_box_pixels": [{ "x_min": 120, "y_min": 200, "x_max": 800, "y_max": 400 }]
                },
                {
                    "anomaly_id": "ANDL_Mound_Complex_01",
                    "classification": { "type": "Mound Complex", "subtype": "Ceremonial" },
                    "confidence": { "global_score": 0.88, "individual_scores": { "lrm": 0.9, "svf": 0.85, "slope": 0.92, "chm": 0.85, "ndvi": 0.8 } },
                    "evidence_per_image": {
                        "lrm": "Multiple elevated circular and rectangular features in organized pattern.",
                        "chm": "Distinct vegetation patterns over constructed mounds."
                    },
                    "archaeological_interpretation": "Complex of ceremonial mounds arranged in formal pattern, suggesting significant cultural site.",
                    "bounding_box_pixels": [{ "x_min": 200, "y_min": 300, "x_max": 600, "y_max": 700 }]
                }
            ]
        };
    }
};
