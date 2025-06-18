window.ResultsManager = {
    logListContainerId: 'results-log-list', // ID of the div in results-tab's left panel
    selectAllButtonId: 'results-select-all-btn',
    mainDashboardContainerId: 'results-main-panel', // ID of the div for the dashboard
    initialized: false,

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
                this.handleLogItemClick(event.target.getAttribute('data-logfile'));
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
            dashboardContainer.innerHTML = `
                <h2 class="text-white text-lg font-semibold mb-3">Details for ${logFile.replace('.json', '')}</h2>
                <p class="text-gray-300 mb-2">Fetching details for ${logFile}...</p>
                <div class="bg-gray-800 p-4 rounded-md text-sm">
                    <h3 class="text-sky-400 font-semibold">Expected Data:</h3>
                    <ul class="list-disc list-inside text-gray-400 mt-1">
                        <li>Full OpenAI Response</li>
                        <li>Original Prompt</li>
                        <li>Input Image Details (paths, sizes)</li>
                        <li>LAZ File Name (if applicable)</li>
                        <li>Coordinates (if applicable)</li>
                        <li>OpenAI Model Used</li>
                    </ul>
                </div>
                <p class="text-yellow-400 mt-4">(Backend endpoint <code>/api/results/get/${logFile}</code> will provide this data. Currently mocked.)</p>
            `;
        }
        // TODO: Implement fetch and display logic for single log details
        // This will call something like: this.fetchAndDisplayLogDetails(logFile);
        // TODO: Uncomment and implement when backend endpoint is ready
        // try {
        //     const response = await fetch(`/api/results/get/${logFile}`);
        //     if (!response.ok) {
        //         throw new Error(`HTTP error! status: ${response.status}`);
        //     }
        //     const resultData = await response.json();
        //     this.displaySingleResultDashboard(resultData); // New function to be created later
        // } catch (error) {
        //     Utils.log('error', `Failed to fetch details for ${logFile}:`, error);
        //     dashboardContainer.innerHTML += `<p class="text-red-500 mt-2">Error fetching details: ${error.message}</p>`;
        // }
    },

    handleSelectAll() {
        Utils.log('info', '"Select All" clicked.');
        const dashboardContainer = document.getElementById(this.mainDashboardContainerId);
        if (dashboardContainer) {
            dashboardContainer.innerHTML = `
                <h2 class="text-white text-lg font-semibold mb-3">Aggregated Archaeological Insights Dashboard</h2>
                <p class="text-gray-300 mb-2">Fetching and aggregating all OpenAI results...</p>
                <div class="bg-gray-800 p-4 rounded-md text-sm">
                    <h3 class="text-sky-400 font-semibold">Expected Aggregated Data:</h3>
                    <ul class="list-disc list-inside text-gray-400 mt-1">
                        <li>Total number of analyses performed.</li>
                        <li>Summary of identified anomalies (count, types, locations if possible).</li>
                        <li>List of unique regions/sites analyzed.</li>
                        <li>Breakdown of OpenAI models used.</li>
                        <li>Commonly identified features or interpretations relevant to archaeology.</li>
                        <li>Potentially, a timeline or frequency of specific keywords (e.g., "pottery", "structure", "burial").</li>
                    </ul>
                </div>
                <p class="text-yellow-400 mt-4">(Backend endpoint <code>/api/results/get_all</code> will provide this data. Currently mocked.)</p>
            `;
        }
        // TODO: Implement fetch and display logic for all results
        // This will call something like: this.fetchAndDisplayAllResultsDashboard();
        // TODO: Uncomment and implement when backend endpoint is ready
        // try {
        //     const response = await fetch('/api/results/get_all');
        //     if (!response.ok) {
        //         throw new Error(`HTTP error! status: ${response.status}`);
        //     }
        //     const aggregatedData = await response.json();
        //     this.displayAggregatedResultsDashboard(aggregatedData); // New function to be created later
        // } catch (error) {
        //     Utils.log('error', 'Failed to fetch aggregated results:', error);
        //     dashboardContainer.innerHTML += `<p class="text-red-500 mt-2">Error fetching aggregated data: ${error.message}</p>`;
        // }
    }
};
