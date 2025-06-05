"""
LAZ/LAS File Processing API
Handles LAZ and LAS point cloud file upload and processing operations.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any, Optional
import os
import shutil
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/laz", tags=["laz"])

# Configuration - Use absolute paths to avoid security issues
BASE_DIR = Path(__file__).parent.parent.parent  # Go up to project root
LAZ_INPUT_DIR = BASE_DIR / "input" / "LAZ"
LAZ_OUTPUT_DIR = BASE_DIR / "output" / "LAZ"
LAZ_INPUT_DIR.mkdir(parents=True, exist_ok=True)
LAZ_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/load")
async def load_laz_file(file: UploadFile = File(...)):
    """Load a LAZ/LAS file into input/LAZ and create output directory"""
    try:
        # Validate file type
        allowed_extensions = ['.laz', '.las']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create unique filename if file already exists
        input_path = LAZ_INPUT_DIR / file.filename
        counter = 1
        while input_path.exists():
            name_part = Path(file.filename).stem
            ext_part = Path(file.filename).suffix
            input_path = LAZ_INPUT_DIR / f"{name_part}_{counter}{ext_part}"
            counter += 1

        # Save uploaded file to input/LAZ
        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"LAZ file loaded: {input_path}")
        
        # Create output directory for this file
        file_stem = input_path.stem
        output_dir = LAZ_OUTPUT_DIR / file_stem
        output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Output directory created: {output_dir}")
        
        return {
            "message": "File loaded successfully",
            "inputFile": input_path.name,
            "outputDirectory": str(output_dir.relative_to(BASE_DIR)),
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading LAZ file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Loading failed: {str(e)}")

@router.post("/upload-and-process")
async def upload_and_process_laz(
    file: UploadFile = File(...),
    processingType: str = Form("dem"),
    resolution: float = Form(1.0)
):
    """Upload and process a LAZ/LAS file"""
    try:
        # Validate file type
        allowed_extensions = ['.laz', '.las']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create unique filename if file already exists
        upload_path = LAZ_INPUT_DIR / file.filename
        counter = 1
        while upload_path.exists():
            name_part = Path(file.filename).stem
            ext_part = Path(file.filename).suffix
            upload_path = LAZ_INPUT_DIR / f"{name_part}_{counter}{ext_part}"
            counter += 1
        
        # Save uploaded file
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"LAZ file uploaded: {upload_path}")
        
        # Process the file (mock processing for now)
        processed_file = await process_laz_file(
            upload_path, 
            processingType, 
            resolution
        )
        
        return {
            "message": "File uploaded and processed successfully",
            "originalFile": upload_path.name,
            "processedFile": processed_file,
            "processingType": processingType,
            "resolution": resolution,
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing LAZ file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

async def process_laz_file(input_path: Path, processing_type: str, resolution: float) -> str:
    """
    Process LAZ file to generate raster products
    This is a mock implementation - in production, this would use actual LAZ processing tools
    """
    try:
        # Generate output filename
        output_name = f"{input_path.stem}_{processing_type}_{resolution}m.tif"
        output_dir = LAZ_OUTPUT_DIR / input_path.stem
        output_path = output_dir / output_name
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock processing - in production, this would use:
        # - PDAL for LAZ/LAS processing
        # - GDAL for raster generation
        # - Actual elevation model generation algorithms
        
        logger.info(f"Mock processing LAZ file: {input_path} -> {output_path}")
        logger.info(f"Processing type: {processing_type}, Resolution: {resolution}m")
        
        # Simulate processing time
        import asyncio
        await asyncio.sleep(1)
        
        # Create a mock output file
        output_path.touch()
        
        # In a real implementation, you would:
        # 1. Use PDAL to read and filter point cloud data
        # 2. Generate raster grids based on processing type:
        #    - DEM: Digital Elevation Model from ground points
        #    - DSM: Digital Surface Model from all points
        #    - DTM: Digital Terrain Model from filtered ground points  
        #    - CHM: Canopy Height Model (DSM - DTM)
        # 3. Use GDAL to write the output raster
        
        return output_name
        
    except Exception as e:
        logger.error(f"Error in LAZ processing: {str(e)}")
        raise

@router.get("/files")
async def get_laz_files():
    """Get list of available LAZ files"""
    try:
        files = []
        
        # Get input files
        if LAZ_INPUT_DIR.exists():
            for file_path in LAZ_INPUT_DIR.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.laz', '.las']:
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(LAZ_INPUT_DIR)),
                        "size": file_path.stat().st_size,
                        "type": "source",
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
        
        # Get processed files from output directories
        if LAZ_OUTPUT_DIR.exists():
            for dir_path in LAZ_OUTPUT_DIR.iterdir():
                if dir_path.is_dir():
                    for file_path in dir_path.glob("*.tif"):
                        if file_path.is_file():
                            files.append({
                                "name": file_path.name,
                                "path": str(file_path.relative_to(LAZ_OUTPUT_DIR)),
                                "size": file_path.stat().st_size,
                                "type": "processed",
                                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })
        
        return sorted(files, key=lambda x: x["modified"], reverse=True)
        
    except Exception as e:
        logger.error(f"Error scanning LAZ directory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scanning files: {str(e)}")

@router.get("/download/{file_path:path}")
async def download_laz_file(file_path: str):
    """Download a LAZ file or processed result"""
    try:
        # Try input directory first, then output directory
        full_path = LAZ_INPUT_DIR / file_path
        if not full_path.exists():
            full_path = LAZ_OUTPUT_DIR / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Ensure the path is absolute and within our allowed directories
        full_path = full_path.resolve()
        
        # Security check - ensure file is within our allowed directories
        input_dir_resolved = LAZ_INPUT_DIR.resolve()
        output_dir_resolved = LAZ_OUTPUT_DIR.resolve()
        
        if not (str(full_path).startswith(str(input_dir_resolved)) or 
                str(full_path).startswith(str(output_dir_resolved))):
            raise HTTPException(status_code=403, detail="Access denied")
        
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
async def delete_laz_file(file_path: str):
    """Delete a LAZ file"""
    try:
        # Try input directory first, then output directory
        full_path = LAZ_INPUT_DIR / file_path
        if not full_path.exists():
            full_path = LAZ_OUTPUT_DIR / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        full_path.unlink()
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.get("/processing-status/{file_name}")
async def get_processing_status(file_name: str):
    """Get processing status for a LAZ file"""
    try:
        # This would typically track actual processing jobs
        # For now, return a mock status
        return {
            "status": "completed",
            "progress": 100,
            "message": "Processing completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
