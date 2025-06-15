# Image Processing App

This project contains a very small example web application built with FastAPI and a simple HTML/JavaScript frontend. The UI uses an electric blue color scheme and provides buttons for single image processing steps. When a button is clicked an endpoint is called which would normally run PDAL/GDAL processing and output a TIF. The TIF is converted to PNG and displayed in the corresponding cell.

#install
pip install -r requirements.txt

## Usage

```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

Open `http://localhost:8000` in a browser.

## Frontend Tests

To run the small unit tests for the gallery components:

```bash
cd frontend
npm test
```
