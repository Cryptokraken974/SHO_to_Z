"""
Anomaly Report Export Endpoint
Handles exporting anomaly analysis reports as HTML files
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import shutil
import re
from typing import Dict, Any, Optional, List

router = APIRouter()

class ExportReportRequest(BaseModel):
    htmlContent: str
    fileName: str
    metadata: Dict[str, Any]

class ImageMetadata(BaseModel):
    name: str
    path: str
    filename: str
    size: int

class ReportMetadata(BaseModel):
    regionName: str
    coordinates: Optional[Dict[str, float]]
    sentDate: str
    sentPrompt: str
    uid: str
    images: List[ImageMetadata]

@router.post("/api/anomalies/export-report")
async def export_anomaly_report(request: ExportReportRequest):
    """
    Export anomaly analysis report as HTML file
    Saves to llm/reports folder with structured naming
    Copies images to a relative location and updates paths
    """
    try:
        # Ensure reports directory exists
        reports_dir = Path("llm/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Create report-specific directory for images
        report_name = request.fileName.replace('.html', '')
        report_images_dir = reports_dir / f"{report_name}_images"
        report_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Process HTML content to fix image paths and copy images
        html_content = request.htmlContent
        
        # Extract image metadata from request
        if 'images' in request.metadata and request.metadata['images']:
            for img in request.metadata['images']:
                original_path = img['path']
                filename = img['filename']
                
                # Source path (absolute)
                source_path = Path(original_path)
                
                # Destination path (relative to report)
                dest_path = report_images_dir / filename
                
                # Copy image if source exists
                if source_path.exists():
                    try:
                        shutil.copy2(source_path, dest_path)
                        print(f"📷 Copied image: {filename}")
                    except Exception as e:
                        print(f"⚠️ Failed to copy {filename}: {e}")
                        continue
                
                # Update HTML content to use relative paths
                # Replace both absolute paths: /original/path and original/path
                old_path_absolute = f'src="/{original_path}"'
                old_path_relative = f'src="{original_path}"'
                new_path = f'src="{report_name}_images/{filename}"'
                
                html_content = html_content.replace(old_path_absolute, new_path)
                html_content = html_content.replace(old_path_relative, new_path)
        
        # Generate file path
        report_path = reports_dir / request.fileName
        
        # Save processed HTML content to file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Also save metadata as JSON for potential future use
        metadata_path = reports_dir / f"{request.fileName.replace('.html', '')}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(request.metadata, f, indent=2)
        
        print(f"✅ Exported anomaly report: {report_path}")
        print(f"📄 Report size: {len(html_content)} characters")
        print(f"📊 Metadata saved: {metadata_path}")
        print(f"🖼️ Images directory: {report_images_dir}")
        
        return {
            "success": True,
            "filePath": str(report_path),
            "fileName": request.fileName,
            "metadataPath": str(metadata_path),
            "imagesPath": str(report_images_dir),
            "size": len(html_content)
        }
        
    except Exception as e:
        print(f"❌ Error exporting report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export report: {str(e)}"
        )

@router.get("/api/anomalies/reports")
async def list_reports():
    """
    List all available anomaly reports
    """
    try:
        reports_dir = Path("llm/reports")
        if not reports_dir.exists():
            return {"reports": []}
        
        reports = []
        for html_file in reports_dir.glob("*.html"):
            metadata_file = reports_dir / f"{html_file.stem}_metadata.json"
            
            report_info = {
                "fileName": html_file.name,
                "filePath": str(html_file),
                "size": html_file.stat().st_size,
                "created": html_file.stat().st_mtime,
                "hasMetadata": metadata_file.exists()
            }
            
            # Load metadata if available
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        report_info["metadata"] = metadata
                except Exception as e:
                    print(f"⚠️ Could not load metadata for {html_file.name}: {e}")
            
            reports.append(report_info)
        
        # Sort by creation time (newest first)
        reports.sort(key=lambda x: x["created"], reverse=True)
        
        return {"reports": reports}
        
    except Exception as e:
        print(f"❌ Error listing reports: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list reports: {str(e)}"
        )

@router.get("/api/anomalies/reports/{fileName}")
async def get_report(fileName: str):
    """
    Get a specific anomaly report
    """
    try:
        reports_dir = Path("llm/reports")
        report_path = reports_dir / fileName
        
        if not report_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Report not found: {fileName}"
            )
        
        # Read HTML content
        with open(report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Try to load metadata
        metadata_path = reports_dir / f"{report_path.stem}_metadata.json"
        metadata = None
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                print(f"⚠️ Could not load metadata: {e}")
        
        return {
            "fileName": fileName,
            "htmlContent": html_content,
            "metadata": metadata,
            "size": len(html_content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get report: {str(e)}"
        )

@router.delete("/api/anomalies/reports/{fileName}")
async def delete_report(fileName: str):
    """
    Delete a specific anomaly report and its metadata
    """
    try:
        reports_dir = Path("llm/reports")
        report_path = reports_dir / fileName
        
        if not report_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Report not found: {fileName}"
            )
        
        # Delete HTML file
        report_path.unlink()
        
        # Delete metadata file if exists
        metadata_path = reports_dir / f"{report_path.stem}_metadata.json"
        if metadata_path.exists():
            metadata_path.unlink()
        
        # Delete images directory if exists
        images_dir = reports_dir / f"{report_path.stem}_images"
        if images_dir.exists():
            try:
                shutil.rmtree(images_dir)
                print(f"🗑️ Deleted images directory: {images_dir}")
            except Exception as e:
                print(f"⚠️ Could not delete images directory: {e}")
        
        print(f"🗑️ Deleted report: {fileName}")
        
        return {
            "success": True,
            "message": f"Report {fileName} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete report: {str(e)}"
        )
