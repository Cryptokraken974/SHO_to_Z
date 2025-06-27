<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoArchaeology Terrain Processor - README</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
            line-height: 1.7;
        }
        h1, h2, h3, h4, h5, h6 {
            font-weight: 600;
            border-bottom-width: 1px;
            border-color: #e5e7eb; /* gray-200 */
            padding-bottom: 0.5rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        h1 { font-size: 2.25rem; } /* text-4xl */
        h2 { font-size: 1.875rem; } /* text-3xl */
        h3 { font-size: 1.5rem; } /* text-2xl */
        hr {
            margin-top: 2rem;
            margin-bottom: 2rem;
            border-top-width: 4px;
        }
        ul {
            list-style-type: disc;
            padding-left: 2rem;
        }
        li {
            margin-bottom: 0.5rem;
        }
        code {
            background-color: #f3f4f6; /* gray-100 */
            color: #111827; /* gray-900 */
            padding: 0.2rem 0.4rem;
            border-radius: 0.25rem;
            font-size: 0.9em;
        }
        pre {
            background-color: #1f2937; /* gray-800 */
            color: #f9fafb; /* gray-50 */
            padding: 1rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }
        pre code {
            background-color: transparent;
            color: inherit;
            padding: 0;
        }
        strong {
            font-weight: 600;
        }
        a {
            color: #3b82f6; /* blue-500 */
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body class="bg-white text-gray-800">
    <main class="max-w-4xl mx-auto p-6 sm:p-8 md:p-12">

        <h1>GeoArchaeology Terrain Processor</h1>
        <p><strong>A powerful, AI-enhanced web application for archaeological remote sensing and landscape analysis.</strong></p>
        <p>This application provides a comprehensive suite of tools designed for archaeologists and researchers to discover, investigate, and document archaeological sites. It streamlines the process of analyzing terrain and satellite imagery by integrating LiDAR data processing, automated raster generation, and cutting-edge AI-powered feature detection.</p>

        <hr>

        <h2>✨ Core Features</h2>
        <ul>
            <li><strong>Dual Data Input Workflows:</strong>
                <ul>
                    <li><strong>Bring Your Own Data:</strong> Upload your own high-resolution LiDAR (<code>.laz</code>/<code>.las</code>) files.</li>
                    <li><strong>Explore New Areas:</strong> Define regions of interest directly on an interactive map by point, path, or bounding box.</li>
                </ul>
            </li>
            <li><strong>Automated Data Acquisition:</strong>
                <ul>
                    <li>Fetches high-resolution Digital Terrain Models (DTMs) from public datasets like USGS 3DEP for regions in the USA.</li>
                    <li>Acquires global Digital Surface Models (DSMs) from sources like the Copernicus DEM.</li>
                    <li>Downloads Sentinel-2 satellite imagery for NDVI analysis.</li>
                </ul>
            </li>
            <li><strong>Comprehensive Raster Generation:</strong> Automatically generates a full suite of archaeologically relevant raster visualizations from elevation data, including:
                <ul>
                    <li>Digital Terrain Model (DTM) & Digital Surface Model (DSM)</li>
                    <li>Multi-directional Hillshades</li>
                    <li>Slope & Aspect</li>
                    <li>Color Relief (Hypsometric Tinting)</li>
                    <li>Topographic Position Index (TPI) & Terrain Ruggedness Index (TRI)</li>
                    <li>Sky View Factor (SVF) / Openness</li>
                    <li>Composite RGB Hillshades</li>
                </ul>
            </li>
            <li><strong>Vegetation Analysis (NDVI):</strong> Calculates and visualizes the Normalized Difference Vegetation Index (NDVI) from Sentinel-2 data to identify crop marks and vegetation anomalies.</li>
            <li><strong>AI-Powered Anomaly Detection:</strong>
                <ul>
                    <li>Leverages OpenAI's vision models (e.g., GPT-4o) to analyze raster imagery for potential archaeological features.</li>
                    <li>Utilizes a sophisticated <strong>modular prompt system</strong> for precise and repeatable AI analysis.</li>
                    <li>Delivers structured JSON reports detailing detected anomalies, confidence scores, and visual evidence.</li>
                </ul>
            </li>
            <li><strong>Interactive Analysis & Reporting:</strong>
                <ul>
                    <li>View, filter, and explore AI analysis results.</li>
                    <li>Visually verify AI detections with bounding box overlays on source images.</li>
                    <li>Export comprehensive analysis reports in HTML and PDF formats.</li>
                </ul>
            </li>
        </ul>

        <hr>

        <h2>⚙️ Technical Stack</h2>
        <ul>
            <li><strong>Backend:</strong> Python with <strong>FastAPI</strong> for a high-performance API.</li>
            <li><strong>Geospatial Processing:</strong>
                <ul>
                    <li><strong>PDAL (Point Data Abstraction Library):</strong> For reading, analyzing, and processing LAZ/LAS point cloud data.</li>
                    <li><strong>GDAL (Geospatial Data Abstraction Library):</strong> For all raster operations, including generation, warping, and analysis.</li>
                </ul>
            </li>
            <li><strong>AI & Machine Learning:</strong>
                <ul>
                    <li><strong>OpenAI API:</strong> For multimodal analysis of raster imagery.</li>
                </ul>
            </li>
            <li><strong>Data Sources:</strong>
                <ul>
                    <li><strong>OpenTopography (USGS 3DEP):</strong> For high-resolution LiDAR data (USA).</li>
                    <li><strong>Copernicus Data Space Ecosystem (CDSE):</strong> For Sentinel-2 satellite imagery and global DEMs.</li>
                </ul>
            </li>
            <li><strong>Frontend:</strong> HTML, CSS, JavaScript with a web mapping library.</li>
            <li><strong>Server:</strong> Uvicorn ASGI server.</li>
        </ul>

        <hr>

        <h2>🚀 Getting Started</h2>
        <h3>1. Prerequisites</h3>
        <p>This application relies on the powerful GDAL and PDAL libraries. You must have them installed on your system before proceeding.</p>
        <p><strong>On Debian/Ubuntu:</strong></p>
        <pre><code># Install GDAL
sudo apt-get update
sudo apt-get install -y gdal-bin libgdal-dev

# Install PDAL
sudo apt-get install -y pdal</code></pre>
        <p>For other operating systems, please refer to the official installation guides for <a href="https://gdal.org/download.html">GDAL</a> and <a href="https://pdal.io/en/latest/install.html">PDAL</a>.</p>

        <h3>2. Installation</h3>
        <ol class="list-decimal pl-5">
            <li class="mb-4">
                <strong>Clone the Repository</strong>
                <pre><code>git clone &lt;your-repository-url&gt;
cd &lt;repository-folder&gt;</code></pre>
            </li>
            <li class="mb-4">
                <strong>Create and Activate a Python Virtual Environment</strong>
                <pre><code>python3 -m venv venv
source venv/bin/activate</code></pre>
            </li>
            <li class="mb-4">
                <strong>Install Python Dependencies</strong>
                <p>The project's dependencies are listed in <code>requirements.txt</code>.</p>
                <pre><code>pip install -r requirements.txt</code></pre>
            </li>
            <li class="mb-4">
                <strong>Configure Environment Variables</strong>
                <p>You will need to set up credentials for the services used by the application. Create a <code>.env</code> file in the project root and add the following, replacing the placeholder values:</p>
                <pre><code># OpenAI API Key
OPENAI_API_KEY="sk-..."

# Copernicus Data Space Ecosystem Credentials
CDSE_CLIENT_ID="..."
CDSE_CLIENT_SECRET="..."</code></pre>
            </li>
        </ol>

        <h3>3. Running the Application</h3>
        <p>Once the installation is complete, run the application using Uvicorn:</p>
        <pre><code># Ensure your virtual environment is active
source venv/bin/activate

# Run the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload</code></pre>
        <p>You can now access the GeoArchaeology Terrain Processor by navigating to <a href="http://localhost:8000">http://localhost:8000</a> in your web browser.</p>
        
        <hr>

        <h2>🗺️ Application Workflow</h2>
        <p>The application is built around a logical workflow from data input to final analysis:</p>
        <ol class="list-decimal pl-5">
            <li><strong>Define a Region:</strong> Start by either uploading your own LAZ/LAS files or by drawing a region of interest (point, path, or box) on the map. You can enable NDVI processing at this stage.</li>
            <li><strong>Acquire Data:</strong>
                <ul>
                    <li>For <strong>LAZ files</strong>, metadata is extracted, and if NDVI is enabled, Sentinel-2 imagery is automatically fetched.</li>
                    <li>For <strong>map-defined regions</strong>, use the "Get Data" function. This fetches a DTM/DSM and, if enabled, Sentinel-2 imagery.</li>
                </ul>
            </li>
            <li><strong>Automatic Raster Generation:</strong> Upon acquiring a DTM, the backend automatically generates the full suite of raster products (Hillshades, Slope, SVF, etc.).</li>
            <li><strong>Perform Analysis:</strong>
                <ul>
                    <li><strong>NDVI:</strong> If satellite data was acquired, run the NDVI analysis to generate a vegetation index map.</li>
                    <li><strong>OpenAI Analysis:</strong> Navigate to the "OpenAI Analysis" tab. Select your region(s), customize the modular prompt if needed, and send the raster imagery for AI interpretation.</li>
                </ul>
            </li>
            <li><strong>Review and Export:</strong> Go to the "Results" tab to explore the AI's findings. View the detected anomalies, inspect the visual evidence with overlays, and export the final report as HTML or PDF.</li>
        </ol>

        <hr>

        <h2>📁 Project Structure</h2>
        <p>A brief overview of the key directories:</p>
        <ul>
            <li><code>/app</code>: Contains the core backend FastAPI application logic.
                <ul>
                    <li><code>/app/main.py</code>: The main application entry point.</li>
                    <li><code>/app/processing/</code>: Modules for geospatial processing (raster generation, NDVI, etc.).</li>
                    <li><code>/app/data_acquisition/</code>: Modules for fetching data from external sources.</li>
                </ul>
            </li>
            <li><code>/input</code>: Default directory where user-uploaded data and fetched source data (LAZ, Sentinel-2 bands, external DEMs) are stored.</li>
            <li><code>/output</code>: Directory where all generated files for a region are stored, including rasters, PNG previews, and metadata.</li>
            <li><code>/llm</code>: Contains all resources related to the AI analysis feature.
                <ul>
                    <li><code>/llm/prompts/</code>: The modular JSON prompts that guide the AI.</li>
                    <li><code>/llm/logs/</code>: Detailed logs of every request sent to the OpenAI API.</li>
                    <li><code>/llm/responses/</code>: The raw JSON responses received from the AI.</li>
                    <li><code>/llm/reports/</code>: The exported HTML and PDF analysis reports.</li>
                </ul>
            </li>
            <li><code>/static</code>: Frontend assets (HTML, CSS, JavaScript).</li>
        </ul>

        <hr>

        <h2>License</h2>
        <p>[Add your license information here, e.g., MIT, GPL-3.0]</p>

    </main>
</body>
</html>
