from osgeo import gdal
import os
import time
from typing import Optional
import base64
import subprocess

def convert_geotiff_to_png(tif_path: str, png_path: Optional[str] = None, enhanced_resolution: bool = True, save_to_consolidated: bool = True) -> str:
    """
    Convert GeoTIFF file to PNG file with proper scaling and worldfile preservation
    Enhanced version preserves high-resolution detail for better visualization
    
    Args:
        tif_path: Path to the input TIF file
        png_path: Optional path for output PNG file. If None, will be generated from tif_path
        enhanced_resolution: If True, use enhanced settings for better quality
        save_to_consolidated: If True, save a copy to the consolidated png_outputs directory
        
    Returns:
        Path to the generated PNG file
    """
    print(f"\n🎨 GEOTIFF TO PNG: Starting {'ENHANCED RESOLUTION' if enhanced_resolution else 'standard'} conversion")
    print(f"📁 Input TIF: {tif_path}")
    
    start_time = time.time()
    
    try:
        # Generate output PNG filename if not provided
        if png_path is None:
            tif_basename = os.path.splitext(tif_path)[0]  # Remove .tif extension
            png_path = f"{tif_basename}.png"
        
        print(f"📁 Output PNG: {png_path}")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(png_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"CREATED FOLDER (convert_geotiff_to_png): {output_dir}") # LOGGING ADDED
            print(f"📁 Created output directory: {output_dir}")
        
        # Open GeoTIFF with GDAL to get statistics and information
        ds = gdal.Open(tif_path)
        if ds is None:
            error_msg = f"GDAL failed to open TIF file: {tif_path}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        # Get raster information
        width = ds.RasterXSize
        height = ds.RasterYSize
        pixel_size_x = ds.GetGeoTransform()[1]
        pixel_size_y = abs(ds.GetGeoTransform()[5])
        
        print(f"📏 Raster dimensions: {width}x{height} pixels")
        print(f"📐 Pixel size: {pixel_size_x:.6f} x {pixel_size_y:.6f} degrees")
        
        # Get band statistics for proper scaling
        band = ds.GetRasterBand(1)
        band.ComputeStatistics(False)
        
        # Get min/max values for scaling
        min_val, max_val, mean_val, std_val = band.GetStatistics(True, True)
        print(f"📊 Data range: Min={min_val:.0f}, Max={max_val:.0f}, Mean={mean_val:.1f}, StdDev={std_val:.1f}")
        
        # For consistency with test script, we'll skip the enhanced histogram analysis
        stretch_min = min_val
        stretch_max = max_val
        
        # Enhanced PNG conversion options
        if enhanced_resolution:
            # Get band statistics for proper scaling (matching test script approach)
            band = ds.GetRasterBand(1)
            band.ComputeStatistics(False)
            min_val, max_val, mean_val, std_val = band.GetStatistics(True, True)
            
            # High-quality PNG conversion with test script compatible options
            scale_options = [
                "-scale", str(min_val), str(max_val), "0", "255",
                "-ot", "Byte",  # Output as 8-bit for PNG
                "-co", "WORLDFILE=YES"
            ]
            print(f"🎨 Enhanced PNG conversion: {min_val:.0f}-{max_val:.0f} → 0-255")
        else:
            # Standard conversion options
            scale_options = [
                "-scale", str(stretch_min), str(stretch_max), "0", "255",
                "-ot", "Byte",  # Output as 8-bit for PNG
                "-co", "WORLDFILE=YES"
            ]
            print(f"🎨 Standard PNG conversion: {stretch_min:.0f}-{stretch_max:.0f} → 0-255...")
        
        gdal.Translate(png_path, ds, format="PNG", options=scale_options)
        
        # Close dataset
        ds = None
        
        # Handle consolidated PNG outputs directory if requested
        if save_to_consolidated:
            try:
                # Extract region name from the path (assumes tif_path format like "output/RegionName/lidar/ProcessingType/...")
                path_parts = tif_path.split(os.sep)
                region_idx = path_parts.index("output") + 1 if "output" in path_parts else -1
                
                if region_idx > 0 and region_idx < len(path_parts):
                    region_name = path_parts[region_idx]
                    processing_type = path_parts[region_idx + 2] if len(path_parts) > region_idx + 2 else None
                    
                    # Only proceed if we successfully identified the region and processing type
                    if region_name and processing_type:
                        # Create the consolidated png_outputs directory path
                        consolidated_dir = os.path.join("output", region_name, "lidar", "png_outputs")
                        os.makedirs(consolidated_dir, exist_ok=True)
                        
                        # Create the consolidated PNG path
                        processing_type_lower = processing_type.lower()
                        
                        # Special handling for hillshade with specific parameters
                        if "hillshade" in processing_type_lower and "315_45_08" in tif_path:
                            consolidated_png_path = os.path.join(consolidated_dir, f"{region_name}_elevation_hillshade_315_45_08.png")
                        else:
                            consolidated_png_path = os.path.join(consolidated_dir, f"{region_name}_elevation_{processing_type_lower}.png")
                        
                        # Copy the PNG file to the consolidated directory
                        import shutil
                        shutil.copy2(png_path, consolidated_png_path)
                        
                        # Copy the corresponding TIFF file to the consolidated directory
                        consolidated_tiff_path = os.path.splitext(consolidated_png_path)[0] + ".tif"
                        if os.path.exists(tif_path) and not os.path.exists(consolidated_tiff_path):
                            shutil.copy2(tif_path, consolidated_tiff_path)
                            print(f"📋 Copied TIFF to consolidated directory: {os.path.basename(consolidated_tiff_path)}")
                        
                        # Copy the worldfile if it exists (.pgw format from PNG conversion)
                        worldfile_path = os.path.splitext(png_path)[0] + ".pgw"
                        consolidated_worldfile_path = os.path.splitext(consolidated_png_path)[0] + ".pgw"
                        if os.path.exists(worldfile_path):
                            shutil.copy2(worldfile_path, consolidated_worldfile_path)
                            print(f"🌍 Copied worldfile to consolidated directory: {os.path.basename(consolidated_worldfile_path)}")
                        
                        # Also check for .wld file alongside PNG (GDAL sometimes creates .wld instead of .pgw)
                        png_wld_path = os.path.splitext(png_path)[0] + ".wld"
                        consolidated_wld_from_png_path = os.path.splitext(consolidated_png_path)[0] + ".wld"
                        if os.path.exists(png_wld_path) and not os.path.exists(consolidated_wld_from_png_path):
                            shutil.copy2(png_wld_path, consolidated_wld_from_png_path)
                            print(f"🌍 Copied PNG .wld file to consolidated directory: {os.path.basename(consolidated_wld_from_png_path)}")
                        
                        # Also copy the original .wld file if it exists (from TIFF processing)
                        original_wld_path = os.path.splitext(tif_path)[0] + ".wld"
                        consolidated_wld_path = os.path.splitext(consolidated_png_path)[0] + ".wld"
                        if os.path.exists(original_wld_path) and not os.path.exists(consolidated_wld_path):
                            shutil.copy2(original_wld_path, consolidated_wld_path)
                            print(f"🌍 Copied TIFF .wld file to consolidated directory: {os.path.basename(consolidated_wld_path)}")
                        
                        print(f"✅ Copied PNG and associated files to consolidated directory: {consolidated_png_path}")
            except Exception as e:
                print(f"⚠️ Warning: Failed to save PNG to consolidated directory: {str(e)}")
        
        processing_time = time.time() - start_time
        
        if enhanced_resolution:
            print(f"✅ ENHANCED GeoTIFF to PNG conversion completed in {processing_time:.2f} seconds")
        else:
            print(f"✅ GeoTIFF to PNG conversion completed in {processing_time:.2f} seconds")
        print(f"📄 PNG saved: {png_path}")
        
        # Check for worldfile
        worldfile_path = os.path.splitext(png_path)[0] + ".pgw"
        if os.path.exists(worldfile_path):
            print(f"✅ Worldfile created: {worldfile_path}")
        
        return png_path
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"GeoTIFF to PNG conversion failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Processing time before error: {processing_time:.2f} seconds")
        raise Exception(error_msg)

def convert_geotiff_to_png_base64(tif_path: str) -> str:
    """
    Convert GeoTIFF file to PNG and return as base64 encoded string
    
    Args:
        tif_path: Path to the input TIF file
        
    Returns:
        Base64 encoded PNG image string
    """
    print(f"\n🖼️ CONVERT: Starting TIF to PNG base64 conversion")
    print(f"📁 Input TIF: {tif_path}")
    
    start_time = time.time()
    
    try:
        # First convert to PNG file
        png_path = convert_geotiff_to_png(tif_path)
        
        # Convert PNG to base64
        print(f"🔄 Converting PNG to base64...")
        base64_start = time.time()
        
        with open(png_path, 'rb') as png_file:
            png_data = png_file.read()
            base64_data = base64.b64encode(png_data).decode('utf-8')
        
        base64_time = time.time() - base64_start
        total_time = time.time() - start_time
        
        print(f"✅ Base64 conversion completed in {base64_time:.2f} seconds")
        print(f"📊 Base64 string length: {len(base64_data):,} characters")
        print(f"⏱️ Total conversion time: {total_time:.2f} seconds")
        print(f"✅ TIF to PNG base64 conversion successful!\n")
        
        return base64_data
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"TIF to PNG base64 conversion failed: {str(e)}"
        print(f"❌ Error in TIF to PNG base64 conversion: {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Processing time before error: {processing_time:.2f} seconds")
        raise Exception(error_msg)

def convert_sentinel2_to_png(data_dir: str, region_name: str) -> dict:
    """
    Convert Sentinel-2 TIF files to PNG with proper output structure
    
    Args:
        data_dir: Path to the input/<region_name>/ directory containing TIF files
        region_name: Unique region name for the output directory
        
    Returns:
        Dictionary with conversion results and paths
    """
    print(f"\n🛰️ SENTINEL-2 TO PNG: Starting conversion")
    print(f"📁 Input directory: {data_dir}")
    print(f"🏷️ Region name: {region_name}")
    
    results = {
        'success': False,
        'files': [],
        'errors': []
    }
    
    try:
        from pathlib import Path
        
        # Input directory with TIF files - now look in sentinel2 subfolder
        input_dir = Path(data_dir) / "sentinel2"
        if not input_dir.exists():
            print(f"⚠️ Sentinel2 subfolder not found, checking directly in input directory")
            input_dir = Path(data_dir)  # Fallback for backward compatibility
            if not input_dir.exists():
                results['errors'].append(f"Input directory does not exist: {data_dir}")
                return results
        
        # Create output directory: output/<region_name>/sentinel2/
        output_dir = Path("output") / region_name / "sentinel2"
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"CREATED FOLDER (convert_sentinel2_to_png): {output_dir}") # LOGGING ADDED
        print(f"📁 Output directory: {output_dir}")
        
        # Get all TIF files and sort by modification time to get the most recent
        tif_files = list(input_dir.glob("*.tif"))
        if not tif_files:
            results['errors'].append(f"No TIF files found in {input_dir}")
            return results
        
        # Sort by modification time (most recent first) and take only the latest
        tif_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_tif = tif_files[0]
        
        print(f"📊 Found {len(tif_files)} TIF files, processing most recent: {latest_tif.name}")
        if len(tif_files) > 1:
            print(f"⚠️ Skipping {len(tif_files) - 1} older TIF files:")
            for older_tif in tif_files[1:]:
                print(f"   - {older_tif.name}")
        
        # Process only the latest 4-band Sentinel-2 TIF file (RED, GREEN, BLUE, NIR bands)
        tif_file = latest_tif
        try:
            base_name = tif_file.stem  # Get filename without extension
            print(f"🛰️ Processing 4-band Sentinel-2 TIF: {tif_file}")
            
            # Extract RED band (Band 1 = B04 RED)
            red_tif_path = output_dir / f"{base_name}_RED_B04.tif"
            red_png_path = output_dir / f"{base_name}_RED_B04.png"
            
            print(f"🔴 Extracting RED band (B04): Band 1 -> {red_tif_path}")
            extract_result = extract_sentinel2_band(str(tif_file), str(red_tif_path), 1)
            
            if extract_result:
                # Convert RED TIF to PNG
                print(f"🎨 Converting RED band to PNG: {red_tif_path} -> {red_png_path}")
                actual_red_png = convert_geotiff_to_png(str(red_tif_path), str(red_png_path))
                
                if os.path.exists(actual_red_png):
                    results['files'].append({
                        'band': 'RED_B04',
                        'tif_path': str(red_tif_path),
                        'png_path': actual_red_png,
                        'size_mb': os.path.getsize(actual_red_png) / (1024 * 1024)
                    })
                    print(f"✅ Successfully converted RED band")
                else:
                    results['errors'].append(f"Failed to create PNG for RED band")
            else:
                results['errors'].append(f"Failed to extract RED band from {tif_file.name}")

            # Extract NIR band (Band 4 = B08 NIR)  
            nir_tif_path = output_dir / f"{base_name}_NIR_B08.tif"
            nir_png_path = output_dir / f"{base_name}_NIR_B08.png"
            
            print(f"🌿 Extracting NIR band (B08): Band 4 -> {nir_tif_path}")
            extract_result = extract_sentinel2_band(str(tif_file), str(nir_tif_path), 4)
            
            if extract_result:
                # Convert NIR TIF to PNG
                print(f"🎨 Converting NIR band to PNG: {nir_tif_path} -> {nir_png_path}")
                actual_nir_png = convert_geotiff_to_png(str(nir_tif_path), str(nir_png_path))
                
                if os.path.exists(actual_nir_png):
                    results['files'].append({
                        'band': 'NIR_B08',
                        'tif_path': str(nir_tif_path),
                        'png_path': actual_nir_png,
                        'size_mb': os.path.getsize(actual_nir_png) / (1024 * 1024)
                    })
                    print(f"✅ Successfully converted NIR band")
                    
                    # Check if we have both RED and NIR bands for NDVI calculation
                    red_band_extracted = any(f['band'] == 'RED_B04' for f in results['files'] if f.get('tif_path') and base_name in f['tif_path'])
                    nir_band_extracted = True  # We just successfully extracted NIR
                    
                    if red_band_extracted and nir_band_extracted:
                        try:
                            print(f"\n🌱 BOTH RED AND NIR BANDS AVAILABLE - GENERATING NDVI")
                            
                            # Import NDVI processor
                            from .processing.ndvi_processing import NDVIProcessor
                            
                            # Generate NDVI
                            ndvi_processor = NDVIProcessor()
                            
                            # Create NDVI output path
                            ndvi_tif_path = output_dir / f"{base_name}_NDVI.tif"
                            
                            # Calculate NDVI using the extracted band files
                            ndvi_success = ndvi_processor.calculate_ndvi(
                                str(red_tif_path), 
                                str(nir_tif_path), 
                                str(ndvi_tif_path)
                            )
                            
                            if ndvi_success and os.path.exists(ndvi_tif_path):
                                # Convert NDVI TIF to PNG
                                ndvi_png_path = output_dir / f"{base_name}_NDVI.png"
                                print(f"🎨 Converting NDVI to PNG: {ndvi_tif_path} -> {ndvi_png_path}")
                                actual_ndvi_png = convert_geotiff_to_png(str(ndvi_tif_path), str(ndvi_png_path))
                                
                                if os.path.exists(actual_ndvi_png):
                                    results['files'].append({
                                        'band': 'NDVI',
                                        'tif_path': str(ndvi_tif_path),
                                        'png_path': actual_ndvi_png,
                                        'size_mb': os.path.getsize(actual_ndvi_png) / (1024 * 1024)
                                    })
                                    print(f"✅ Successfully generated and converted NDVI")
                                else:
                                    results['errors'].append(f"Failed to create PNG for NDVI")
                                    print(f"❌ Failed to create NDVI PNG")
                            else:
                                results['errors'].append(f"Failed to calculate NDVI from {base_name}")
                                print(f"❌ Failed to calculate NDVI")
                                
                        except Exception as ndvi_e:
                            error_msg = f"Error generating NDVI for {base_name}: {str(ndvi_e)}"
                            print(f"❌ {error_msg}")
                            results['errors'].append(error_msg)
                    
                else:
                    results['errors'].append(f"Failed to create PNG for NIR band")
            else:
                results['errors'].append(f"Failed to extract NIR band from {tif_file.name}")
                
        except Exception as e:
            error_msg = f"Error processing {tif_file.name}: {str(e)}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        results['success'] = len(results['files']) > 0
        print(f"✅ Conversion complete: {len(results['files'])} files converted")
        
    except Exception as e:
        error_msg = f"Sentinel-2 conversion failed: {str(e)}"
        print(f"❌ {error_msg}")
        results['errors'].append(error_msg)
    
    return results

def extract_sentinel2_band(input_tif: str, output_tif: str, band_number: int) -> bool:
    """
    Extract a specific band from a multi-band Sentinel-2 TIF file using gdal_translate
    
    Args:
        input_tif: Path to the input multi-band TIF file
        output_tif: Path for the output single-band TIF file
        band_number: Band number to extract (1-based indexing)
        
    Returns:
        True if extraction successful, False otherwise
    """
    try:
        print(f"🔧 Extracting band {band_number} from {input_tif}")
        
        # Use gdal_translate to extract specific band
        cmd = [
            'gdal_translate',
            '-b', str(band_number),  # Select specific band
            input_tif,
            output_tif
        ]
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully extracted band {band_number} to {output_tif}")
            return True
        else:
            print(f"❌ Error extracting band {band_number}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during band extraction: {str(e)}")
        return False