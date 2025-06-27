# GeoArchaeology Terrain Processor

**A powerful, AI-enhanced web application for archaeological remote sensing and landscape analysis.**

This application provides a comprehensive suite of tools designed for archaeologists and researchers to discover, investigate, and document archaeological sites. It streamlines the process of analyzing terrain and satellite imagery by integrating LiDAR data processing, automated raster generation, and cutting-edge AI-powered feature detection.

---

## ✨ Core Features

* **Dual Data Input Workflows:**
    * **Bring Your Own Data:** Upload your own high-resolution LiDAR (`.laz`/`.las`) files.
    * **Explore New Areas:** Define regions of interest directly on an interactive map by point, path, or bounding box.
* **Automated Data Acquisition:**
    * Fetches high-resolution Digital Terrain Models (DTMs) from public datasets like USGS 3DEP for regions in the USA.
    * Acquires global Digital Surface Models (DSMs) from sources like the Copernicus DEM.
    * Downloads Sentinel-2 satellite imagery for NDVI analysis.
* **Comprehensive Raster Generation:** Automatically generates a full suite of archaeologically relevant raster visualizations from elevation data, including:
    * Digital Terrain Model (DTM) & Digital Surface Model (DSM)
    * Multi-directional Hillshades
    * Slope & Aspect
    * Color Relief (Hypsometric Tinting)
    * Topographic Position Index (TPI) & Terrain Ruggedness Index (TRI)
    * Sky View Factor (SVF) / Openness
    * Composite RGB Hillshades
* **Vegetation Analysis (NDVI):** Calculates and visualizes the Normalized Difference Vegetation Index (NDVI) from Sentinel-2 data to identify crop marks and vegetation anomalies.
* **AI-Powered Anomaly Detection:**
    * Leverages OpenAI's vision models (e.g., GPT-4o) to analyze raster imagery for potential archaeological features.
    * Utilizes a sophisticated **modular prompt system** for precise and repeatable AI analysis.
    * Delivers structured JSON reports detailing detected anomalies, confidence scores, and visual evidence.
* **Interactive Analysis & Reporting:**
    * View, filter, and explore AI analysis results.
    * Visually verify AI detections with bounding box overlays on source images.
    * Export comprehensive analysis reports in HTML and PDF formats.

---

## ⚙️ Technical Stack

* **Backend:** Python with **FastAPI** for a high-performance API.
* **Geospatial Processing:**
    * **PDAL (Point Data Abstraction Library):** For reading, analyzing, and processing LAZ/LAS point cloud data.
    * **GDAL (Geospatial Data Abstraction Library):** For all raster operations, including generation, warping, and analysis.
* **AI & Machine Learning:**
    * **OpenAI API:** For multimodal analysis of raster imagery.
* **Data Sources:**
    * **OpenTopography (USGS 3DEP):** For high-resolution LiDAR data (USA).
    * **Copernicus Data Space Ecosystem (CDSE):** For Sentinel-2 satellite imagery and global DEMs.
* **Frontend:** HTML, CSS, JavaScript with a web mapping library.
* **Server:** Uvicorn ASGI server.

---

## 🚀 Getting Started

### 1. Prerequisites

This application relies on the powerful GDAL and PDAL libraries. You must have them installed on your system before proceeding.

**On Debian/Ubuntu:**
```bash
# Install GDAL
sudo apt-get update
sudo apt-get install -y gdal-bin libgdal-dev

# Install PDAL
sudo apt-get install -y pdal
```
For other operating systems, please refer to the official installation guides for [GDAL](https://gdal.org/download.html) and [PDAL](https://pdal.io/en/latest/install.html).

### 2. Installation

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd <repository-folder>
    ```

2.  **Create and Activate a Python Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python Dependencies**
    The project's dependencies are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    You will need to set up credentials for the services used by the application. Create a `.env` file in the project root and add the following, replacing the placeholder values:
    ```
    # OpenAI API Key
    OPENAI_API_KEY="sk-..."

    # Copernicus Data Space Ecosystem Credentials
    CDSE_CLIENT_ID="..."
    CDSE_CLIENT_SECRET="..."
    ```

### 3. Running the Application

Once the installation is complete, run the application using Uvicorn:
```bash
# Ensure your virtual environment is active
source venv/bin/activate

# Run the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
You can now access the GeoArchaeology Terrain Processor by navigating to `http://localhost:8000` in your web browser.

---

## 🗺️ Application Workflow

The application is built around a logical workflow from data input to final analysis:

1.  **Define a Region:** Start by either uploading your own LAZ/LAS files or by drawing a region of interest (point, path, or box) on the map. You can enable NDVI processing at this stage.
2.  **Acquire Data:**
    * For **LAZ files**, metadata is extracted, and if NDVI is enabled, Sentinel-2 imagery is automatically fetched.
    * For **map-defined regions**, use the "Get Data" function. This fetches a DTM/DSM and, if enabled, Sentinel-2 imagery.
3.  **Automatic Raster Generation:** Upon acquiring a DTM, the backend automatically generates the full suite of raster products (Hillshades, Slope, SVF, etc.).
4.  **Perform Analysis:**
    * **NDVI:** If satellite data was acquired, run the NDVI analysis to generate a vegetation index map.
    * **OpenAI Analysis:** Navigate to the "OpenAI Analysis" tab. Select your region(s), customize the modular prompt if needed, and send the raster imagery for AI interpretation.
5.  **Review and Export:** Go to the "Results" tab to explore the AI's findings. View the detected anomalies, inspect the visual evidence with overlays, and export the final report as HTML or PDF.

---

## 📁 Project Structure

A brief overview of the key directories:

* `/app`: Contains the core backend FastAPI application logic.
    * `/app/main.py`: The main application entry point.
    * `/app/processing/`: Modules for geospatial processing (raster generation, NDVI, etc.).
    * `/app/data_acquisition/`: Modules for fetching data from external sources.
* `/input`: Default directory where user-uploaded data and fetched source data (LAZ, Sentinel-2 bands, external DEMs) are stored.
* `/output`: Directory where all generated files for a region are stored, including rasters, PNG previews, and metadata.
* `/llm`: Contains all resources related to the AI analysis feature.
    * `/llm/prompts/`: The modular JSON prompts that guide the AI.
    * `/llm/logs/`: Detailed logs of every request sent to the OpenAI API.
    * `/llm/responses/`: The raw JSON responses received from the AI.
    * `/llm/reports/`: The exported HTML and PDF analysis reports.
* `/static`: Frontend assets (HTML, CSS, JavaScript).

---

## License

[Add your license information here, e.g., MIT, GPL-3.0]
