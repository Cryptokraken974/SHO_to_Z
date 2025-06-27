window.ResultsManager = {
    logListContainerId: 'results-log-list', // ID of the div in results-tab's left panel
    deleteButtonId: 'results-delete-btn',
    mainDashboardContainerId: 'results-main-panel', // ID of the div for the dashboard
    initialized: false,
    selectedLogFile: null, // Track the currently selected log file
    availableAnomalyTypes: [], // Store available anomaly types from visual lexicon
    activeAnomalyFilters: new Set(), // Store active filters

    init() {
        if (this.initialized) {
            // If already initialized, refresh everything including anomaly filters
            this.attachEventListeners();
            this.fetchResultsList();
            this.loadAnomalyTypes(); // Always reload anomaly types on re-init
            Utils.log('info', 'ResultsManager re-initialized - refreshed filters and results list.');
            return;
        }
        Utils.log('info', 'Initializing ResultsManager...');
        this.fetchResultsList();
        this.loadAnomalyTypes();
        this.attachEventListeners();
        this.initialized = true;
        Utils.log('info', 'ResultsManager initialized.');
    },

    attachEventListeners() {
        const deleteButton = document.getElementById(this.deleteButtonId);
        if (deleteButton) {
            deleteButton.addEventListener('click', () => {
                this.handleDeleteSelected();
            });
        }

        // Anomaly filter event listeners
        const filterSelectAllBtn = document.getElementById('anomaly-filter-select-all');
        if (filterSelectAllBtn) {
            filterSelectAllBtn.addEventListener('click', () => {
                this.selectAllAnomalyFilters();
            });
        }

        const filterClearAllBtn = document.getElementById('anomaly-filter-clear-all');
        if (filterClearAllBtn) {
            filterClearAllBtn.addEventListener('click', () => {
                this.clearAllAnomalyFilters();
            });
        }
        // Event listener for individual log item clicks will be added in displayResultsList
    },

    /**
     * Load available anomaly types from the visual lexicon
     */
    async loadAnomalyTypes() {
        try {
            Utils.log('info', 'Loading anomaly types from visual lexicon...');
            const response = await visualLexicon().getAnomalyTypes();
            
            if (response.success) {
                this.availableAnomalyTypes = response.anomaly_types;
                this.renderAnomalyFilter();
                Utils.log('info', `Loaded ${this.availableAnomalyTypes.length} anomaly types`);
            } else {
                Utils.log('error', 'Failed to load anomaly types:', response.error);
                this.showAnomalyFilterError('Failed to load anomaly types');
            }
        } catch (error) {
            Utils.log('error', 'Error loading anomaly types:', error);
            this.showAnomalyFilterError('Error loading filter options');
        }
    },

    /**
     * Render the anomaly filter checkboxes
     */
    renderAnomalyFilter() {
        const filterContainer = document.getElementById('anomaly-filter-container');
        if (!filterContainer) return;

        if (this.availableAnomalyTypes.length === 0) {
            filterContainer.innerHTML = '<div class="text-[#ababab] text-xs">No anomaly types available</div>';
            return;
        }

        const checkboxesHtml = this.availableAnomalyTypes.map(anomalyType => `
            <label class="flex items-center space-x-2 text-xs cursor-pointer hover:bg-[#3a3a3a] p-1 rounded">
                <input type="checkbox" 
                       class="anomaly-filter-checkbox" 
                       data-anomaly-type="${anomalyType}"
                       checked>
                <span class="text-white">${anomalyType}</span>
            </label>
        `).join('');

        filterContainer.innerHTML = checkboxesHtml;

        // Initialize all filters as active (checked by default)
        this.activeAnomalyFilters = new Set(this.availableAnomalyTypes);

        // Add change event listeners to checkboxes
        const checkboxes = filterContainer.querySelectorAll('.anomaly-filter-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const anomalyType = e.target.getAttribute('data-anomaly-type');
                if (e.target.checked) {
                    this.activeAnomalyFilters.add(anomalyType);
                } else {
                    this.activeAnomalyFilters.delete(anomalyType);
                }
                this.applyAnomalyFilters();
            });
        });
    },

    /**
     * Show error message in the filter container
     */
    showAnomalyFilterError(message) {
        const filterContainer = document.getElementById('anomaly-filter-container');
        if (filterContainer) {
            filterContainer.innerHTML = `<div class="text-red-400 text-xs">${message}</div>`;
        }
    },

    /**
     * Select all anomaly filters - just clear all filters to show everything
     */
    selectAllAnomalyFilters() {
        // Clear all filters to show all anomalies
        this.activeAnomalyFilters.clear();
        
        // Update checkbox states to all checked
        const checkboxes = document.querySelectorAll('.anomaly-filter-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
        
        this.applyAnomalyFilters();
    },

    /**
     * Clear all anomaly filters - hide ALL anomalies
     */
    clearAllAnomalyFilters() {
        // Set a dummy filter that will match nothing to hide all anomalies
        this.activeAnomalyFilters = new Set(['__HIDE_ALL__']);
        
        // Update checkbox states to all unchecked
        const checkboxes = document.querySelectorAll('.anomaly-filter-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        this.applyAnomalyFilters();
    },

    /**
     * Apply current anomaly filters to the dashboard
     */
    applyAnomalyFilters() {
        if (window.AnomaliesDashboard && window.AnomaliesDashboard.setFilters) {
            window.AnomaliesDashboard.setFilters(this.activeAnomalyFilters);
        }
    },

    /**
     * Force refresh anomaly types and filters
     */
    async refreshAnomalyFilters() {
        Utils.log('info', 'Force refreshing anomaly filters...');
        await this.loadAnomalyTypes();
    },

    async fetchResultsList() {
        Utils.log('info', 'Fetching OpenAI result logs list...');
        
        // Clear any existing selection when refreshing the list
        this.hideDeleteButton();
        
        // Clear the main dashboard
        const dashboardContainer = document.getElementById(this.mainDashboardContainerId);
        if (dashboardContainer) {
            dashboardContainer.innerHTML = `
                <h1 class="text-white text-xl font-bold">Results Dashboard</h1>
                <p class="text-gray-300">Select a result from the left panel to view details, or click "Select All" for a summary.</p>
            `;
        }
        
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
                    await this.displayResultsList(data.logs);
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

    async displayResultsList(logs) {
        const logListContainer = document.getElementById(this.logListContainerId);
        if (!logs || logs.length === 0) {
            logListContainer.innerHTML = '<p class="text-gray-400">No results found.</p>';
            return;
        }

        const ul = document.createElement('ul');
        ul.className = 'space-y-2';
        
        // Store anomaly status for each log file
        const anomalyStatusMap = new Map();
        
        // Process each log file to determine anomaly status
        for (const logFile of logs) {
            const li = document.createElement('li');
            li.className = 'p-2 rounded-md cursor-pointer text-white text-sm';
            li.textContent = logFile.replace('.json', ''); // Display cleaner name
            li.setAttribute('data-logfile', logFile);
            
            // Check anomaly status and set background color
            const hasAnomalies = await this.checkAnomalyStatus(logFile);
            anomalyStatusMap.set(logFile, hasAnomalies);
            this.setListItemBackground(li, hasAnomalies);
            
            li.addEventListener('click', (event) => {
                // Remove selection from other items and restore their original backgrounds
                ul.querySelectorAll('li').forEach((item) => {
                    item.classList.remove('log-item-selected');
                    // Restore original background based on stored anomaly status
                    const itemLogFile = item.getAttribute('data-logfile');
                    const itemHasAnomalies = anomalyStatusMap.get(itemLogFile);
                    this.setListItemBackground(item, itemHasAnomalies);
                });
                
                // Add selection to clicked item
                li.classList.remove('log-item-with-anomalies', 'log-item-no-anomalies', 'log-item-unknown');
                li.classList.add('log-item-selected');
                
                // Track selected file and show delete button
                this.selectedLogFile = event.target.getAttribute('data-logfile');
                this.showDeleteButton();
                
                this.handleLogItemClick(this.selectedLogFile);
            });
            ul.appendChild(li);
        }
        
        logListContainer.innerHTML = ''; // Clear loading message
        logListContainer.appendChild(ul);
        Utils.log('info', `Displayed ${logs.length} result logs with anomaly status indicators.`);
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
            
            // Extract the analysis folder name from the logFile
            // Remove the '_response.json' suffix to get the actual folder name
            let analysisFolder = logFile;
            if (logFile && logFile.endsWith('_response.json')) {
                analysisFolder = logFile.replace('_response.json', '');
            }
            
            // Pass the corrected analysis folder name to the dashboard for image loading
            window.AnomaliesDashboard.render(containerElement, anomalyData, analysisFolder);
            
            // Apply current filters after rendering
            setTimeout(() => {
                this.applyAnomalyFilters();
            }, 100); // Small delay to ensure dashboard is fully rendered
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
    },

    /**
     * Check if a log file contains anomalies by reading the response
     * @param {string} logFile - The log file name
     * @returns {Promise<boolean|null>} - true if anomalies detected, false if not, null if unknown
     */
    async checkAnomalyStatus(logFile) {
        try {
            const response = await fetch(`/api/results/get/${logFile}`);
            if (!response.ok) {
                return null; // Unknown status
            }
            
            const data = await response.json();
            
            // The response contains JSON wrapped in a string in the openai_response field
            const parsedData = this.extractJsonFromResponse(data.openai_response || '');
            
            if (parsedData && parsedData.analysis_summary) {
                const anomaliesDetected = parsedData.analysis_summary.anomalies_detected;
                
                // Handle both boolean and string "true"/"false" values
                if (typeof anomaliesDetected === 'boolean') {
                    return anomaliesDetected;
                } else if (typeof anomaliesDetected === 'string') {
                    return anomaliesDetected.toLowerCase() === 'true';
                }
            }
            
            return null; // Unknown status
        } catch (error) {
            Utils.log('error', `Failed to check anomaly status for ${logFile}:`, error);
            return null; // Unknown status
        }
    },

    /**
     * Set the background color of a list item based on anomaly status
     * @param {HTMLElement} listItem - The list item element
     * @param {boolean|null} hasAnomalies - true for anomalies (green), false for none (red), null for unknown (gray)
     */
    setListItemBackground(listItem, hasAnomalies) {
        // Remove all anomaly status classes
        listItem.classList.remove(
            'log-item-with-anomalies', 
            'log-item-no-anomalies', 
            'log-item-unknown',
            'log-item-selected'
        );
        
        if (hasAnomalies === true) {
            // Green background for anomalies detected
            listItem.classList.add('log-item-with-anomalies');
        } else if (hasAnomalies === false) {
            // Red background for no anomalies
            listItem.classList.add('log-item-no-anomalies');
        } else {
            // Gray background for unknown status
            listItem.classList.add('log-item-unknown');
        }
    },
};
