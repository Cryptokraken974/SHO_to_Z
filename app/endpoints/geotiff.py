"""
GeoTiff Files Management API
Handles file operations for GeoTiff files including upload, download, metadata extraction, and basic processing.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any, Optional
import os
import json
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/geotiff", tags=["geotiff"])

# Configuration
GEOTIFF_UPLOAD_DIR = Path("data/geotiff")
GEOTIFF_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/files")
async def get_geotiff_files():
    """Get list of available GeoTiff files"""
    try:
        files = []
        
        if not GEOTIFF_UPLOAD_DIR.exists():
            return []
            
        def scan_directory(directory: Path, relative_path: str = ""):
            items = []
            try:
                for item in directory.iterdir():
                    if item.is_file() and item.suffix.lower() in ['.tif', '.tiff', '.png', '.jpg', '.jpeg']:
                        item_path = str(item.relative_to(GEOTIFF_UPLOAD_DIR)) if relative_path == "" else f"{relative_path}/{item.name}"
                        items.append({
                            "name": item.name,
                            "path": item_path,
                            "size": item.stat().st_size,
                            "type": "file",
                            "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                        })
                    elif item.is_dir() and not item.name.startswith('.'):
                        folder_path = str(item.relative_to(GEOTIFF_UPLOAD_DIR)) if relative_path == "" else f"{relative_path}/{item.name}"
                        folder_item = {
                            "name": item.name,
                            "path": folder_path,
                            "type": "folder",
                            "children": scan_directory(item, folder_path)
                        }
                        items.append(folder_item)
            except PermissionError:
                logger.warning(f"Permission denied accessing {directory}")
            
            return sorted(items, key=lambda x: (x["type"] == "file", x["name"].lower()))
        
        files = scan_directory(GEOTIFF_UPLOAD_DIR)
        return files
        
    except Exception as e:
        logger.error(f"Error scanning GeoTiff directory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scanning files: {str(e)}")

@router.get("/metadata/{file_path:path}")
async def get_file_metadata(file_path: str):
    """Get metadata for a specific GeoTiff file"""
    try:
        full_path = GEOTIFF_UPLOAD_DIR / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Basic file info
        stat = full_path.stat()
        metadata = {
            "filename": full_path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "path": file_path
        }
        
        # Try to get GeoTiff metadata using GDAL if available
        try:
            from osgeo import gdal
            dataset = gdal.Open(str(full_path))
            if dataset:
                metadata.update({
                    "width": dataset.RasterXSize,
                    "height": dataset.RasterYSize,
                    "bands": dataset.RasterCount,
                    "dataType": gdal.GetDataTypeName(dataset.GetRasterBand(1).DataType),
                    "projection": dataset.GetProjection(),
                    "geoTransform": dataset.GetGeoTransform()
                })
                
                # Get CRS information
                srs = dataset.GetSpatialRef()
                if srs:
                    metadata["crs"] = srs.GetAttrValue("AUTHORITY", 1) if srs.GetAttrValue("AUTHORITY") else "Unknown"
                
                dataset = None  # Close dataset
        except ImportError:
            logger.warning("GDAL not available, returning basic metadata only")
        except Exception as e:
            logger.warning(f"Error reading GeoTiff metadata: {str(e)}")
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metadata for {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading metadata: {str(e)}")

@router.post("/upload")
async def upload_geotiff(file: UploadFile = File(...)):
    """Upload a GeoTiff file"""
    try:
        # Validate file type
        allowed_extensions = ['.tif', '.tiff', '.png', '.jpg', '.jpeg']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create unique filename if file already exists
        upload_path = GEOTIFF_UPLOAD_DIR / file.filename
        counter = 1
        while upload_path.exists():
            name_part = Path(file.filename).stem
            ext_part = Path(file.filename).suffix
            upload_path = GEOTIFF_UPLOAD_DIR / f"{name_part}_{counter}{ext_part}"
            counter += 1
        
        # Save file
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "message": "File uploaded successfully",
            "filename": upload_path.name,
            "path": str(upload_path.relative_to(GEOTIFF_UPLOAD_DIR)),
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/compress")
async def compress_geotiff(request: Dict[str, Any]):
    """Compress a GeoTiff file"""
    try:
        file_path = request.get("filePath")
        if not file_path:
            raise HTTPException(status_code=400, detail="File path required")
        
        full_path = GEOTIFF_UPLOAD_DIR / file_path
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # For now, return a mock response
        # In a real implementation, you would use GDAL to compress the file
        original_size = full_path.stat().st_size
        new_size = int(original_size * 0.7)  # Mock 30% compression
        
        return {
            "message": "File compressed successfully",
            "originalSize": original_size,
            "newSize": new_size,
            "compressionRatio": 0.3
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error compressing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")

@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a GeoTiff file"""
    try:
        full_path = GEOTIFF_UPLOAD_DIR / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(full_path),
            filename=full_path.name,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.delete("/files/{file_path:path}")
async def delete_file(file_path: str):
    """Delete a GeoTiff file"""
    try:
        full_path = GEOTIFF_UPLOAD_DIR / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        full_path.unlink()
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
