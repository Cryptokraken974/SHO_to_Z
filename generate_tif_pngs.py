#!/usr/bin/env python3
"""
Generate PNG visualizations for TIF files with visual hints for masked/dead pixels
This script creates enhanced PNG visualizations that clearly show:
1. Valid data areas in natural colors
2. Masked/dead pixels in contrasting colors (red/magenta)
3. NoData areas in transparent or distinctive colors
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "app"))

try:
    import rasterio
    from rasterio.plot import show
    from rasterio.mask import mask
    RASTERIO_AVAILABLE = True
    print("✅ Rasterio available for advanced PNG generation")
except ImportError:
    RASTERIO_AVAILABLE = False
    print("⚠️ Rasterio not available - using GDAL fallback")

class TifPngGenerator:
    """Generate enhanced PNG visualizations from TIF files"""
    
    def __init__(self, output_quality: str = "high", show_masked_pixels: bool = True):
        """
        Initialize PNG generator
        
        Args:
            output_quality: PNG quality ("high", "medium", "low")
            show_masked_pixels: Whether to highlight masked/dead pixels
        """
        self.output_quality = output_quality
        self.show_masked_pixels = show_masked_pixels
        self.dpi_settings = {
            "high": 300,
            "medium": 150,
            "low": 75
        }
        
    def generate_png_for_tif(
        self, 
        tif_path: str, 
        output_dir: str = None,
        colormap: str = "auto",
        highlight_masked: bool = True
    ) -> Dict[str, str]:
        """
        Generate PNG visualization for a single TIF file
        
        Args:
            tif_path: Path to TIF file
            output_dir: Output directory (defaults to same as TIF)
            colormap: Colormap to use ("auto", "viridis", "terrain", "gray", etc.)
            highlight_masked: Whether to highlight masked pixels
            
        Returns:
            Dictionary with PNG generation results
        """
        try:
            tif_file = Path(tif_path)
            if not tif_file.exists():
                return {"success": False, "error": f"TIF file not found: {tif_path}"}
            
            # Determine output directory and PNG path
            if output_dir is None:
                output_dir = tif_file.parent
            else:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            
            png_path = output_dir / f"{tif_file.stem}_enhanced.png"
            
            print(f"🎨 Generating enhanced PNG: {tif_file.name}")
            print(f"   Output: {png_path.name}")
            
            if RASTERIO_AVAILABLE:
                return self._generate_png_rasterio(tif_path, png_path, colormap, highlight_masked)
            else:
                return self._generate_png_gdal(tif_path, png_path, colormap)
                
        except Exception as e:
            error_msg = f"PNG generation failed for {tif_path}: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def _generate_png_rasterio(
        self, 
        tif_path: str, 
        png_path: Path, 
        colormap: str,
        highlight_masked: bool
    ) -> Dict[str, str]:
        """Generate PNG using rasterio and matplotlib"""
        try:
            with rasterio.open(tif_path) as src:
                # Read data
                data = src.read(1)
                nodata = src.nodata
                
                print(f"   Data shape: {data.shape}")
                print(f"   Data range: {np.nanmin(data):.2f} to {np.nanmax(data):.2f}")
                print(f"   NoData value: {nodata}")
                
                # Determine colormap based on file type
                if colormap == "auto":
                    colormap = self._auto_select_colormap(tif_path, data)
                
                # Create figure
                fig, ax = plt.subplots(figsize=(12, 10))
                
                # Create enhanced visualization
                if highlight_masked and nodata is not None:
                    # Create custom colormap that highlights NoData/masked pixels
                    display_data, custom_cmap, norm = self._create_masked_visualization(
                        data, nodata, colormap
                    )
                    
                    im = ax.imshow(display_data, cmap=custom_cmap, norm=norm, aspect='equal')
                    
                    # Add colorbar with custom labels
                    cbar = plt.colorbar(im, ax=ax, shrink=0.6)
                    cbar.set_label(self._get_data_label(tif_path), rotation=270, labelpad=20)
                    
                else:
                    # Standard visualization
                    masked_data = np.ma.masked_equal(data, nodata) if nodata is not None else data
                    im = ax.imshow(masked_data, cmap=colormap, aspect='equal')
                    plt.colorbar(im, ax=ax, shrink=0.6)
                
                # Set title and labels
                ax.set_title(f"{Path(tif_path).stem}", fontsize=14, fontweight='bold')
                ax.set_xlabel("Pixels (East)")
                ax.set_ylabel("Pixels (North)")
                
                # Add metadata text
                self._add_metadata_text(ax, data, nodata, tif_path)
                
                # Save PNG
                plt.tight_layout()
                plt.savefig(
                    png_path, 
                    dpi=self.dpi_settings[self.output_quality],
                    bbox_inches='tight',
                    facecolor='white',
                    edgecolor='none'
                )
                plt.close()
                
                print(f"   ✅ Enhanced PNG saved: {png_path.name}")
                
                return {
                    "success": True,
                    "png_path": str(png_path),
                    "method": "rasterio_matplotlib",
                    "colormap": colormap,
                    "highlighted_masked": highlight_masked,
                    "data_stats": {
                        "min": float(np.nanmin(data)),
                        "max": float(np.nanmax(data)),
                        "mean": float(np.nanmean(data)),
                        "nodata_value": nodata,
                        "masked_pixels": int(np.sum(data == nodata)) if nodata is not None else 0
                    }
                }
                
        except Exception as e:
            raise RuntimeError(f"Rasterio PNG generation failed: {str(e)}")
    
    def _create_masked_visualization(
        self, 
        data: np.ndarray, 
        nodata: float,
        base_colormap: str
    ) -> Tuple[np.ndarray, mcolors.ListedColormap, mcolors.Normalize]:
        """Create visualization that highlights masked/dead pixels"""
        
        # Create a copy for display
        display_data = data.copy().astype(float)
        
        # Identify masked pixels
        if nodata is not None:
            masked_pixels = (data == nodata)
            num_masked = np.sum(masked_pixels)
            total_pixels = data.size
            masked_percentage = (num_masked / total_pixels) * 100
            
            print(f"   Masked pixels: {num_masked:,} ({masked_percentage:.1f}%)")
            
            # Set masked pixels to a special value for visualization
            display_data[masked_pixels] = -9999
        
        # Get valid data statistics
        valid_data = display_data[display_data != -9999]
        if len(valid_data) > 0:
            vmin, vmax = np.nanmin(valid_data), np.nanmax(valid_data)
        else:
            vmin, vmax = 0, 1
        
        # Create custom colormap
        base_cmap = plt.cm.get_cmap(base_colormap)
        colors = base_cmap(np.linspace(0, 1, 256))
        
        # Add special color for masked pixels (bright magenta/red)
        masked_color = [1.0, 0.0, 1.0, 1.0]  # Bright magenta
        colors = np.vstack([[masked_color], colors])
        
        custom_cmap = mcolors.ListedColormap(colors)
        
        # Create normalization that handles the special masked value
        class MaskedNormalize(mcolors.Normalize):
            def __init__(self, vmin, vmax):
                super().__init__(vmin, vmax)
                
            def __call__(self, value, clip=None):
                # Handle masked values specially
                result = np.ma.masked_array(np.empty_like(value, dtype=float))
                
                # Masked pixels get value 0 (maps to special color)
                masked_indices = (value == -9999)
                result[masked_indices] = 0
                
                # Valid pixels get normalized values from 1 to 255 (maps to base colormap)
                valid_indices = ~masked_indices
                if np.any(valid_indices):
                    valid_normalized = super().__call__(value[valid_indices], clip)
                    # Map to range [1/256, 1] to use the base colormap portion
                    result[valid_indices] = (valid_normalized * 255 + 1) / 256
                
                return result
        
        norm = MaskedNormalize(vmin, vmax)
        
        return display_data, custom_cmap, norm
    
    def _auto_select_colormap(self, tif_path: str, data: np.ndarray) -> str:
        """Automatically select appropriate colormap based on file type and data"""
        path_lower = str(tif_path).lower()
        
        # Determine colormap based on raster type
        if any(term in path_lower for term in ['dtm', 'dem', 'elevation']):
            return 'terrain'
        elif any(term in path_lower for term in ['dsm']):
            return 'viridis'
        elif any(term in path_lower for term in ['chm', 'height']):
            return 'YlGn'
        elif any(term in path_lower for term in ['slope']):
            return 'Reds'
        elif any(term in path_lower for term in ['aspect']):
            return 'hsv'
        elif any(term in path_lower for term in ['hillshade']):
            return 'gray'
        elif any(term in path_lower for term in ['density']):
            return 'plasma'
        elif any(term in path_lower for term in ['mask']):
            return 'RdYlGn'
        else:
            # Default colormap based on data characteristics
            data_range = np.nanmax(data) - np.nanmin(data)
            if np.nanmin(data) >= 0 and data_range < 100:
                return 'viridis'  # Good for positive data with small range
            else:
                return 'RdBu_r'   # Good for data with positive/negative values
    
    def _get_data_label(self, tif_path: str) -> str:
        """Get appropriate label for the data based on file type"""
        path_lower = str(tif_path).lower()
        
        if any(term in path_lower for term in ['dtm', 'dem']):
            return 'Elevation (m)'
        elif 'dsm' in path_lower:
            return 'Surface Height (m)'
        elif 'chm' in path_lower:
            return 'Canopy Height (m)'
        elif 'slope' in path_lower:
            return 'Slope (degrees)'
        elif 'aspect' in path_lower:
            return 'Aspect (degrees)'
        elif 'density' in path_lower:
            return 'Point Density (points/m²)'
        elif 'mask' in path_lower:
            return 'Valid Data (1=Valid, 0=Invalid)'
        else:
            return 'Values'
    
    def _add_metadata_text(self, ax, data: np.ndarray, nodata: float, tif_path: str):
        """Add metadata text to the plot"""
        valid_data = data[data != nodata] if nodata is not None else data
        
        if len(valid_data) > 0:
            stats_text = f"Min: {np.nanmin(valid_data):.2f}\n"
            stats_text += f"Max: {np.nanmax(valid_data):.2f}\n"
            stats_text += f"Mean: {np.nanmean(valid_data):.2f}\n"
            
            if nodata is not None:
                masked_count = np.sum(data == nodata)
                total_count = data.size
                masked_pct = (masked_count / total_count) * 100
                stats_text += f"Masked: {masked_pct:.1f}%"
            
            # Add text box with statistics
            ax.text(0.02, 0.98, stats_text, 
                   transform=ax.transAxes,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                   fontsize=10)
    
    def _generate_png_gdal(self, tif_path: str, png_path: Path, colormap: str) -> Dict[str, str]:
        """Fallback PNG generation using GDAL"""
        try:
            print(f"   Using GDAL for PNG generation...")
            
            # Use gdaldem for color relief if it's elevation data
            if any(term in str(tif_path).lower() for term in ['dtm', 'dem', 'dsm', 'elevation']):
                # Create color relief
                color_table = self._create_gdal_color_table(colormap)
                
                cmd = [
                    'gdaldem', 'color-relief',
                    str(tif_path),
                    color_table,
                    str(png_path),
                    '-alpha'
                ]
                
                import subprocess
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                # Clean up temporary color table
                os.unlink(color_table)
                
                if result.returncode == 0:
                    print(f"   ✅ GDAL PNG saved: {png_path.name}")
                    return {
                        "success": True,
                        "png_path": str(png_path),
                        "method": "gdal_color_relief"
                    }
            
            # Fallback to gdal_translate
            cmd = [
                'gdal_translate',
                '-of', 'PNG',
                '-scale',
                str(tif_path),
                str(png_path)
            ]
            
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"   ✅ GDAL PNG saved: {png_path.name}")
                return {
                    "success": True,
                    "png_path": str(png_path),
                    "method": "gdal_translate"
                }
            else:
                raise RuntimeError(f"GDAL PNG generation failed: {result.stderr}")
                
        except Exception as e:
            raise RuntimeError(f"GDAL PNG generation failed: {str(e)}")
    
    def _create_gdal_color_table(self, colormap: str) -> str:
        """Create GDAL color table file"""
        import tempfile
        
        # Simple terrain color table
        color_table_content = """0 0 0 255 0
50 139 69 19 255
100 205 133 63 255
200 255 255 224 255
500 255 255 255 255
nv 255 0 255 0"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(color_table_content)
            return f.name
    
    def batch_generate_pngs(
        self, 
        tif_files: List[str], 
        output_base_dir: str = None,
        organize_by_type: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Generate PNGs for multiple TIF files
        
        Args:
            tif_files: List of TIF file paths
            output_base_dir: Base output directory
            organize_by_type: Whether to organize outputs by raster type
            
        Returns:
            Dictionary with generation results
        """
        results = {
            "successful": [],
            "failed": [],
            "summary": {}
        }
        
        print(f"\n🎨 BATCH PNG GENERATION")
        print(f"   Files to process: {len(tif_files)}")
        print(f"   Output directory: {output_base_dir or 'Same as source'}")
        print(f"   Organize by type: {organize_by_type}")
        print()
        
        for i, tif_file in enumerate(tif_files, 1):
            print(f"[{i}/{len(tif_files)}] Processing: {Path(tif_file).name}")
            
            try:
                # Determine output directory
                if output_base_dir:
                    if organize_by_type:
                        raster_type = self._extract_raster_type(tif_file)
                        output_dir = Path(output_base_dir) / raster_type
                    else:
                        output_dir = Path(output_base_dir)
                else:
                    output_dir = None
                
                # Generate PNG
                result = self.generate_png_for_tif(
                    tif_file, 
                    output_dir, 
                    colormap="auto",
                    highlight_masked=self.show_masked_pixels
                )
                
                if result.get("success"):
                    results["successful"].append(result)
                    print(f"   ✅ Success")
                else:
                    results["failed"].append({
                        "tif_path": tif_file,
                        "error": result.get("error", "Unknown error")
                    })
                    print(f"   ❌ Failed: {result.get('error')}")
                
            except Exception as e:
                error_msg = f"Batch processing failed for {tif_file}: {str(e)}"
                results["failed"].append({
                    "tif_path": tif_file,
                    "error": error_msg
                })
                print(f"   ❌ Error: {error_msg}")
            
            print()
        
        # Generate summary
        results["summary"] = {
            "total_files": len(tif_files),
            "successful_count": len(results["successful"]),
            "failed_count": len(results["failed"]),
            "success_rate": len(results["successful"]) / len(tif_files) * 100 if tif_files else 0
        }
        
        print(f"📊 BATCH GENERATION SUMMARY")
        print(f"   Total files: {results['summary']['total_files']}")
        print(f"   Successful: {results['summary']['successful_count']}")
        print(f"   Failed: {results['summary']['failed_count']}")
        print(f"   Success rate: {results['summary']['success_rate']:.1f}%")
        
        return results
    
    def _extract_raster_type(self, tif_path: str) -> str:
        """Extract raster type from file path for organization"""
        path_lower = str(tif_path).lower()
        
        if 'dtm' in path_lower:
            return 'DTM'
        elif 'dsm' in path_lower:
            return 'DSM'
        elif 'chm' in path_lower:
            return 'CHM'
        elif 'slope' in path_lower:
            return 'Slope'
        elif 'aspect' in path_lower:
            return 'Aspect'
        elif 'hillshade' in path_lower:
            return 'Hillshade'
        elif 'density' in path_lower:
            return 'Density'
        elif 'mask' in path_lower:
            return 'Masks'
        else:
            return 'Other'


def find_tif_files(search_paths: List[str], include_patterns: List[str] = None) -> List[str]:
    """Find TIF files in specified paths"""
    tif_files = []
    
    for search_path in search_paths:
        search_dir = Path(search_path)
        if search_dir.exists():
            # Find all TIF files recursively
            found_files = list(search_dir.rglob("*.tif"))
            found_files.extend(list(search_dir.rglob("*.tiff")))
            
            # Filter by patterns if specified
            if include_patterns:
                filtered_files = []
                for file in found_files:
                    file_str = str(file).lower()
                    if any(pattern.lower() in file_str for pattern in include_patterns):
                        filtered_files.append(file)
                found_files = filtered_files
            
            tif_files.extend([str(f) for f in found_files])
    
    return sorted(list(set(tif_files)))  # Remove duplicates and sort


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Generate enhanced PNG visualizations from TIF files")
    parser.add_argument("--search-paths", nargs="+", 
                       default=["/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output"],
                       help="Directories to search for TIF files")
    parser.add_argument("--output-dir", 
                       default="/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/png_visualizations",
                       help="Output directory for PNG files")
    parser.add_argument("--include-patterns", nargs="+",
                       help="Patterns to include (e.g., DTM DSM CHM density mask)")
    parser.add_argument("--quality", choices=["high", "medium", "low"], default="high",
                       help="PNG output quality")
    parser.add_argument("--highlight-masked", action="store_true", default=True,
                       help="Highlight masked/dead pixels in bright colors")
    parser.add_argument("--organize-by-type", action="store_true", default=True,
                       help="Organize output PNGs by raster type")
    
    args = parser.parse_args()
    
    print("🎨 TIF TO PNG GENERATOR")
    print("=" * 50)
    
    # Find TIF files
    print("🔍 Searching for TIF files...")
    tif_files = find_tif_files(args.search_paths, args.include_patterns)
    
    if not tif_files:
        print("❌ No TIF files found matching criteria")
        return
    
    print(f"   Found {len(tif_files)} TIF files")
    
    # Show some examples
    print("   Examples:")
    for tif_file in tif_files[:5]:
        print(f"     - {Path(tif_file).name}")
    if len(tif_files) > 5:
        print(f"     ... and {len(tif_files) - 5} more")
    print()
    
    # Initialize PNG generator
    generator = TifPngGenerator(
        output_quality=args.quality,
        show_masked_pixels=args.highlight_masked
    )
    
    # Generate PNGs
    results = generator.batch_generate_pngs(
        tif_files=tif_files,
        output_base_dir=args.output_dir,
        organize_by_type=args.organize_by_type
    )
    
    # Show successful results
    if results["successful"]:
        print(f"\n✅ SUCCESSFUL PNG GENERATIONS:")
        for result in results["successful"][:10]:  # Show first 10
            print(f"   📄 {Path(result['png_path']).name}")
            if result.get("data_stats", {}).get("masked_pixels", 0) > 0:
                masked_pct = (result["data_stats"]["masked_pixels"] / 
                            (result["data_stats"].get("total_pixels", 1))) * 100
                print(f"      🔍 Masked pixels highlighted: {masked_pct:.1f}%")
        
        if len(results["successful"]) > 10:
            print(f"   ... and {len(results['successful']) - 10} more")
    
    # Show failed results
    if results["failed"]:
        print(f"\n❌ FAILED GENERATIONS:")
        for failed in results["failed"][:5]:  # Show first 5
            print(f"   📄 {Path(failed['tif_path']).name}")
            print(f"      Error: {failed['error']}")
    
    print(f"\n🎉 PNG generation completed!")
    print(f"   Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
