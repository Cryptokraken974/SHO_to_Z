# Agent Guide: SHO to Z Repository

This document provides an overview of the codebase and conventions used across the project. It is intended for automated agents and developers working with the repository.

## 1. Repository Structure

```
app/                # FastAPI backend and supporting modules
frontend/           # JavaScript frontend (see AGENTS/AGENTS_JS.md)
Tests/              # Automated tests
cache/              # Metadata caches
input/              # Raw downloads (LiDAR, Sentinel-2, etc.)
output/             # Processed products and overlays
AGENTS/             # Additional agent documentation
```

### Key Backend Modules (under `app/`)
- **main.py** – FastAPI application setup and router inclusion.
- **endpoints/** – Collections of route modules (e.g., `laz_processing.py`, `overlays.py`, `sentinel2.py`).
- **api/** – Service layer for programmatic access to endpoints. Services like `RegionService`, `GeotiffService`, `ProcessingService` etc. provide async and sync helpers.
- **processing/** – Core raster/point‑cloud processing logic using GDAL/PDAL.
- **data_acquisition/** – Download managers and data source classes.
- **region_config/** – Region mapping utilities.
- **services/** – Shared utilities such as the `laz_metadata_cache`.

### Frontend
The `frontend/js` directory hosts modular JavaScript files documented in `AGENTS/AGENTS_JS.md` and `AGENTS/MODULAR_SYSTEM_GUIDE.md`. These scripts interact with the API via the service classes from `app/api`.

### Tests
All automated tests reside in `Tests/`. Subdirectories (e.g., `enhanced_api_tests`) group related suites. When new functionality is added, create or update tests in an appropriate subfolder to keep the structure organized.

## 2. API Endpoints
Routes are defined in files within `app/endpoints/`. Examples include:
- `laz_processing.py` – endpoints like `/api/dtm`, `/api/dsm`, `/api/hillshade_225_45_08`.
- `overlays.py` – overlay retrieval routes such as `/api/overlay/{processing_type}/{filename}` and raster versions for region‑based products.
- `sentinel2.py` – `/api/download-sentinel2` and `/api/convert-sentinel2`.
- `geotiff.py` – upload, metadata, and compression operations for GeoTIFF files.
- `chat.py`, `cache_management.py`, `region_management.py`, etc.

Routers are included in `app/main.py` so each module remains self‑contained.

## 3. Service Layer
The `app/api` package contains classes that mirror backend endpoints. `ServiceFactory` (`app/api/factory.py`) creates instances for these services. Frontend code should call a service method instead of hitting endpoints directly. When adding a new endpoint, provide a matching service method so the front end can remain decoupled from URL details.

Example service usage:
```python
from app.api.factory import processing
result = await processing().run_dtm(region_name="demo_region")
```

## 4. Data Flow Overview
1. **Frontend Interaction** – UI events trigger service calls (JavaScript modules under `frontend/js`).
2. **Service Call** – Service layer constructs HTTP requests to FastAPI endpoints.
3. **Endpoint Processing** – Route handlers invoke functions from `app/processing` or `app/data_acquisition` and return JSON data or base64 images.
4. **Overlay/Results** – Images are written to `output/<region>` and may be optimized via `overlay_optimization.py`. Frontend retrieves overlays or raster products for display.

## 5. Best Practices
- **Tests**: place new tests under `Tests/` in a descriptive subfolder. Mirror the backend module name when possible.
- **Endpoints & Services**: any new endpoint in `app/endpoints` should have a corresponding service class or method in `app/api`. This keeps the frontend and other clients consistent.
- **Folder Structure**: raw downloads go to `input/<region>/` and processed outputs to `output/<region>/subfolder`. Follow existing patterns (see `FOLDER_STRUCTURE_UPDATE.md`).
- **Overlay Optimization**: large images are automatically resized for browser display using `OverlayOptimizer`.
- **Metadata Cache**: use `services/laz_metadata_cache.py` to store LAZ file metadata for quick region lookup.

## 6. Additional Documentation
- `AGENTS/AGENTS_JS.md` – detailed description of JavaScript modules and frontend architecture.
- `AGENTS/MODULAR_SYSTEM_GUIDE.md` – notes on the custom component system for modular HTML/JS.
- Various `*_SUMMARY.md` files record integration steps and implementation notes for specific features.

This guide should help automated agents and contributors navigate the project, understand how major pieces connect, and apply consistent conventions when extending the system.
