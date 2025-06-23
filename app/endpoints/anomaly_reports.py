"""
Anomaly Report Export Endpoint
Handles exporting anomaly analysis reports as HTML files
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import json
import shutil
import re
from typing import Dict, Any, Optional, List

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("⚠️ WeasyPrint not available - PDF generation will be disabled")

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
    Saves to the same folder as report_images (sent_images folder)
    Copies images to a relative location and updates paths
    """
    try:
        # Extract analysis folder name from metadata
        analysis_folder = None
        if 'uid' in request.metadata and request.metadata['uid']:
            # Try to find the analysis folder by searching for the UID
            logs_dir = Path("llm/logs")
            if logs_dir.exists():
                for folder in logs_dir.iterdir():
                    if folder.is_dir() and request.metadata['uid'] in folder.name:
                        analysis_folder = folder.name
                        break
        
        # If we found the analysis folder, use it; otherwise use reports folder as fallback
        if analysis_folder:
            reports_dir = Path("llm/logs") / analysis_folder
            print(f"📁 Using analysis folder for reports: {reports_dir}")
        else:
            reports_dir = Path("llm/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Using fallback reports folder: {reports_dir}")
        
        # Create report-specific directory for images (next to sent_images)
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
    Searches in both analysis folders and reports folder
    """
    try:
        reports = []
        
        # Search in llm/logs analysis folders first
        logs_dir = Path("llm/logs")
        if logs_dir.exists():
            for folder in logs_dir.iterdir():
                if folder.is_dir():
                    # Look for HTML files in each analysis folder
                    for html_file in folder.glob("*.html"):
                        # Skip if it's not a report file (basic filter)
                        if "report" in html_file.name.lower() or "anomaly" in html_file.name.lower():
                            metadata_file = folder / f"{html_file.stem}_metadata.json"
                            
                            report_info = {
                                "fileName": html_file.name,
                                "filePath": str(html_file),
                                "size": html_file.stat().st_size,
                                "created": html_file.stat().st_mtime,
                                "hasMetadata": metadata_file.exists(),
                                "location": "analysis_folder",
                                "analysisFolder": folder.name
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
        
        # Also check the fallback reports folder
        reports_dir = Path("llm/reports")
        if reports_dir.exists():
            for html_file in reports_dir.glob("*.html"):
                metadata_file = reports_dir / f"{html_file.stem}_metadata.json"
                
                report_info = {
                    "fileName": html_file.name,
                    "filePath": str(html_file),
                    "size": html_file.stat().st_size,
                    "created": html_file.stat().st_mtime,
                    "hasMetadata": metadata_file.exists(),
                    "location": "reports_folder",
                    "analysisFolder": None
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
    Searches in analysis folders first, then falls back to reports folder
    """
    try:
        # First try to find the HTML file in analysis folders
        report_path = None
        metadata_path = None
        
        # Search in llm/logs folders first
        logs_dir = Path("llm/logs")
        if logs_dir.exists():
            for folder in logs_dir.iterdir():
                if folder.is_dir():
                    potential_report = folder / fileName
                    if potential_report.exists():
                        report_path = potential_report
                        metadata_path = folder / f"{potential_report.stem}_metadata.json"
                        print(f"📄 Found report in analysis folder: {report_path}")
                        break
        
        # Fallback to reports folder
        if not report_path:
            reports_dir = Path("llm/reports")
            report_path = reports_dir / fileName
            metadata_path = reports_dir / f"{report_path.stem}_metadata.json"
            if not report_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Report not found: {fileName}"
                )
            print(f"📄 Using report from reports folder: {report_path}")
        
        # Read HTML content
        with open(report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Try to load metadata
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
    Searches in analysis folders first, then falls back to reports folder
    """
    try:
        # First try to find the file in analysis folders
        report_path = None
        metadata_path = None
        images_dir = None
        
        # Search in llm/logs folders first
        logs_dir = Path("llm/logs")
        if logs_dir.exists():
            for folder in logs_dir.iterdir():
                if folder.is_dir():
                    potential_report = folder / fileName
                    if potential_report.exists():
                        report_path = potential_report
                        metadata_path = folder / f"{potential_report.stem}_metadata.json"
                        images_dir = folder / f"{potential_report.stem}_images"
                        print(f"📄 Found report in analysis folder: {report_path}")
                        break
        
        # Fallback to reports folder
        if not report_path:
            reports_dir = Path("llm/reports")
            report_path = reports_dir / fileName
            metadata_path = reports_dir / f"{report_path.stem}_metadata.json"
            images_dir = reports_dir / f"{report_path.stem}_images"
            if not report_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Report not found: {fileName}"
                )
            print(f"📄 Using report from reports folder: {report_path}")
        
        # Delete HTML file
        report_path.unlink()
        
        # Delete metadata file if exists
        if metadata_path.exists():
            metadata_path.unlink()
        
        # Delete images directory if exists
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

@router.post("/api/anomalies/generate-pdf/{fileName}")
async def generate_pdf_report(fileName: str):
    """
    Generate PDF from existing HTML report
    Searches in analysis folders first, then falls back to reports folder
    """
    try:
        # Check if WeasyPrint is available
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="PDF generation not available - WeasyPrint not installed"
            )
        
        # First try to find the HTML file in analysis folders
        html_file = None
        reports_dir = None
        
        # Search in llm/logs folders first
        logs_dir = Path("llm/logs")
        if logs_dir.exists():
            for folder in logs_dir.iterdir():
                if folder.is_dir():
                    potential_html = folder / fileName
                    if potential_html.exists():
                        html_file = potential_html
                        reports_dir = folder
                        print(f"📄 Found HTML report in analysis folder: {html_file}")
                        break
        
        # Fallback to reports folder
        if not html_file:
            reports_dir = Path("llm/reports")
            html_file = reports_dir / fileName
            if not html_file.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"HTML report not found: {fileName}"
                )
            print(f"📄 Using HTML report from reports folder: {html_file}")
        
        # Generate PDF filename
        pdf_filename = fileName.replace('.html', '.pdf')
        pdf_file = reports_dir / pdf_filename
        
        # Read HTML content
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Create PDF with optimized settings for reports
        html_doc = HTML(string=html_content, base_url=str(reports_dir))
        
        # Custom CSS for PDF optimization
        pdf_css = CSS(string="""
            @page {
                size: A4;
                margin: 1cm;
            }
            body {
                font-size: 10pt;
                line-height: 1.4;
            }
            .header h1 {
                font-size: 20pt;
            }
            .section h2 {
                font-size: 14pt;
                page-break-before: avoid;
                page-break-after: avoid;
            }
            .anomaly-card {
                page-break-inside: avoid;
                margin-bottom: 15px;
            }
            .images-grid {
                display: block;
            }
            .image-card {
                margin-bottom: 10px;
                page-break-inside: avoid;
            }
            .image-card img {
                max-width: 100%;
                height: auto;
            }
            .anomaly-images-section img {
                max-width: 100%;
                height: auto;
                page-break-inside: avoid;
            }
        """)
        
        # Generate PDF
        html_doc.write_pdf(str(pdf_file), stylesheets=[pdf_css])
        
        print(f"✅ Generated PDF report: {pdf_file}")
        print(f"📄 PDF size: {pdf_file.stat().st_size} bytes")
        
        return {
            "success": True,
            "pdfFileName": pdf_filename,
            "pdfPath": str(pdf_file),
            "size": pdf_file.stat().st_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )

@router.get("/api/anomalies/download-pdf/{fileName}")
async def download_pdf_report(fileName: str):
    """
    Download PDF report file
    Searches in analysis folders first, then falls back to reports folder
    """
    try:
        # First try to find the PDF file in analysis folders
        pdf_file = None
        
        # Search in llm/logs folders first
        logs_dir = Path("llm/logs")
        if logs_dir.exists():
            for folder in logs_dir.iterdir():
                if folder.is_dir():
                    potential_pdf = folder / fileName
                    if potential_pdf.exists():
                        pdf_file = potential_pdf
                        print(f"📄 Found PDF report in analysis folder: {pdf_file}")
                        break
        
        # Fallback to reports folder
        if not pdf_file:
            reports_dir = Path("llm/reports")
            pdf_file = reports_dir / fileName
            if not pdf_file.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"PDF report not found: {fileName}"
                )
            print(f"📄 Using PDF report from reports folder: {pdf_file}")
        
        return FileResponse(
            path=str(pdf_file),
            media_type='application/pdf',
            filename=fileName,
            headers={"Content-Disposition": f"attachment; filename={fileName}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error downloading PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download PDF: {str(e)}"
        )
