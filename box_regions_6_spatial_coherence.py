#!/usr/bin/env python3
"""
Box_Regions_6 Spatial Coherence Analysis

This script analyzes the spatial coherence between DTM, DSM, CHM, and PNG files
within the Box_Regions_6 dataset to verify consistent spatial properties.
"""

import rasterio
import numpy as np
from pathlib import Path
import json

def analyze_raster_properties(file_path):
    """Extract comprehensive spatial properties from a raster file."""
    try:
        with rasterio.open(file_path) as src:
            # Basic properties
            props = {
                'path': str(file_path),
                'exists': True,
                'crs': src.crs.to_string() if src.crs else None,
                'transform': list(src.transform),
                'width': src.width,
                'height': src.height,
                'count': src.count,
                'dtype': str(src.dtypes[0]) if src.dtypes else 'unknown',
                'nodata': src.nodata,
            }
            
            # Bounds
            bounds = src.bounds
            props.update({
                'bounds': {
                    'left': bounds.left,
                    'bottom': bounds.bottom, 
                    'right': bounds.right,
                    'top': bounds.top
                },
                'center': {
                    'x': (bounds.left + bounds.right) / 2,
                    'y': (bounds.bottom + bounds.top) / 2
                },
                'extent': {
                    'width': bounds.right - bounds.left,
                    'height': bounds.top - bounds.bottom
                }
            })
            
            # Resolution
            props['resolution'] = {
                'x': abs(src.transform[0]),
                'y': abs(src.transform[4])
            }
            
            # Data statistics (if data exists)
            try:
                data = src.read(1, masked=True)
                if data.size > 0 and not data.mask.all():
                    props['data_stats'] = {
                        'min': float(np.min(data.compressed())),
                        'max': float(np.max(data.compressed())),
                        'mean': float(np.mean(data.compressed())),
                        'std': float(np.std(data.compressed())),
                        'valid_pixels': int(np.sum(~data.mask)),
                        'total_pixels': int(data.size),
                        'valid_percentage': float(np.sum(~data.mask) / data.size * 100)
                    }
                else:
                    props['data_stats'] = {'error': 'No valid data found'}
            except Exception as e:
                props['data_stats'] = {'error': str(e)}
                
            return props
            
    except Exception as e:
        return {
            'path': str(file_path),
            'exists': False,
            'error': str(e)
        }

def compare_spatial_properties(props_list, tolerance=1e-6):
    """Compare spatial properties between multiple rasters."""
    comparison = {
        'coherent': True,
        'issues': [],
        'summary': {}
    }
    
    if len(props_list) < 2:
        comparison['issues'].append("Need at least 2 files to compare")
        comparison['coherent'] = False
        return comparison
    
    # Reference properties (first valid file)
    ref = None
    for p in props_list:
        if p.get('exists', False):
            ref = p
            break
    
    if not ref:
        comparison['issues'].append("No valid reference file found")
        comparison['coherent'] = False
        comparison['summary'] = {
            'total_files': len(props_list),
            'valid_files': 0,
            'crs_values': [],
            'dimensions': [],
            'resolutions': [],
        }
        return comparison
    
    comparison['reference'] = ref['path']
    
    # Compare each property
    for props in props_list:
        if not props.get('exists', False):
            comparison['issues'].append(f"File {props['path']} does not exist")
            comparison['coherent'] = False
            continue
        
        file_name = Path(props['path']).name
        
        # CRS comparison
        if props.get('crs') != ref.get('crs'):
            comparison['issues'].append(f"{file_name}: CRS mismatch - {props.get('crs')} vs {ref.get('crs')}")
            comparison['coherent'] = False
        
        # Dimensions comparison
        if props.get('width') != ref.get('width') or props.get('height') != ref.get('height'):
            comparison['issues'].append(f"{file_name}: Dimension mismatch - {props.get('width')}x{props.get('height')} vs {ref.get('width')}x{ref.get('height')}")
            comparison['coherent'] = False
        
        # Resolution comparison
        if props.get('resolution'):
            ref_res = ref.get('resolution', {})
            if (abs(props['resolution'].get('x', 0) - ref_res.get('x', 0)) > tolerance or
                abs(props['resolution'].get('y', 0) - ref_res.get('y', 0)) > tolerance):
                comparison['issues'].append(f"{file_name}: Resolution mismatch - {props['resolution']} vs {ref_res}")
                comparison['coherent'] = False
        
        # Bounds comparison  
        if props.get('bounds'):
            ref_bounds = ref.get('bounds', {})
            for key in ['left', 'bottom', 'right', 'top']:
                if abs(props['bounds'].get(key, 0) - ref_bounds.get(key, 0)) > tolerance:
                    comparison['issues'].append(f"{file_name}: Bounds mismatch - {key}: {props['bounds'].get(key)} vs {ref_bounds.get(key)}")
                    comparison['coherent'] = False
    
    # Summary statistics
    valid_files = [p for p in props_list if p.get('exists', False)]
    comparison['summary'] = {
        'total_files': len(props_list),
        'valid_files': len(valid_files),
        'crs_values': list(set(p.get('crs') for p in valid_files if p.get('crs'))),
        'dimensions': list(set(f"{p.get('width')}x{p.get('height')}" for p in valid_files if p.get('width'))),
        'resolutions': list(set(f"{p.get('resolution', {}).get('x'):.6f}" for p in valid_files if p.get('resolution'))),
    }
    
    return comparison

def main():
    """Main analysis function."""
    print("🔍 Box_Regions_6 Spatial Coherence Analysis")
    print("=" * 60)
    
    # Define file paths to analyze
    base_path = Path("/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z")
    
    files_to_analyze = [
        # DTM (from input)
        base_path / "input/Box_Regions_6/3.787S_63.734W_elevation/Original/3.787S_63.734W_elevation.tiff",
        base_path / "input/Box_Regions_6/lidar/3.787S_63.734W_elevation.tiff",
        
        # DSM (from output)
        base_path / "output/Box_Regions_6/lidar/DSM/Box_Regions_6_copernicus_dsm_30m.tif",
        
        # CHM (from output)
        base_path / "output/Box_Regions_6/lidar/Chm/3.787S_63.734W_elevation_CHM.tif",
        
        # Derivatives (from input)
        base_path / "input/Box_Regions_6/3.787S_63.734W_elevation/Visualization/3.787S_63.734W_elevation_color_relief.tif",
        base_path / "input/Box_Regions_6/3.787S_63.734W_elevation/Terrain_Analysis/3.787S_63.734W_elevation_Sky_View_Factor.tif",
        base_path / "input/Box_Regions_6/3.787S_63.734W_elevation/Terrain_Analysis/3.787S_63.734W_elevation_slope_relief.tif",
        base_path / "input/Box_Regions_6/3.787S_63.734W_elevation/Terrain_Analysis/3.787S_63.734W_elevation_LRM_adaptive.tif",
    ]
    
    print(f"📁 Analyzing {len(files_to_analyze)} files from Box_Regions_6...")
    print()
    
    # Analyze each file
    all_properties = []
    for file_path in files_to_analyze:
        print(f"📊 Analyzing: {file_path.name}")
        props = analyze_raster_properties(file_path)
        all_properties.append(props)
        
        if props.get('exists', False):
            print(f"   ✅ Valid raster")
            print(f"   📐 CRS: {props.get('crs', 'Unknown')}")
            print(f"   📏 Dimensions: {props.get('width')}x{props.get('height')}")
            print(f"   🎯 Resolution: {props.get('resolution', {}).get('x', 'Unknown'):.6f} x {props.get('resolution', {}).get('y', 'Unknown'):.6f}")
            print(f"   🗺️  Center: {props.get('center', {}).get('x', 'Unknown'):.6f}, {props.get('center', {}).get('y', 'Unknown'):.6f}")
            
            if 'data_stats' in props and 'error' not in props['data_stats']:
                stats = props['data_stats']
                print(f"   📊 Data range: {stats.get('min', 'N/A'):.2f} to {stats.get('max', 'N/A'):.2f}")
                print(f"   ✨ Valid pixels: {stats.get('valid_percentage', 0):.1f}%")
        else:
            print(f"   ❌ File not found or invalid: {props.get('error', 'Unknown error')}")
        print()
    
    # Compare spatial coherence
    print("🔗 SPATIAL COHERENCE ANALYSIS")
    print("-" * 40)
    
    comparison = compare_spatial_properties(all_properties)
    
    if comparison['coherent']:
        print("✅ All files are spatially coherent!")
    else:
        print("❌ Spatial coherence issues detected:")
        for issue in comparison['issues']:
            print(f"   ⚠️  {issue}")
    
    print()
    print("📋 SUMMARY:")
    print(f"   📁 Total files analyzed: {comparison['summary']['total_files']}")
    print(f"   ✅ Valid files found: {comparison['summary']['valid_files']}")
    print(f"   🗺️  CRS values: {', '.join(comparison['summary']['crs_values'])}")
    print(f"   📐 Dimensions: {', '.join(comparison['summary']['dimensions'])}")
    print(f"   📏 Resolutions: {', '.join(comparison['summary']['resolutions'])}")
    
    # Group analysis by file type
    print()
    print("📊 ANALYSIS BY FILE TYPE:")
    print("-" * 30)
    
    dtm_files = [p for p in all_properties if 'elevation' in p['path'] and ('DTM' in p['path'] or 'Original' in p['path'])]
    dsm_files = [p for p in all_properties if 'DSM' in p['path'] or 'dsm' in p['path']]
    chm_files = [p for p in all_properties if 'CHM' in p['path'] or 'Chm' in p['path']]
    derivative_files = [p for p in all_properties if any(x in p['path'] for x in ['SVF', 'slope', 'LRM', 'color_relief'])]
    
    print(f"🏔️  DTM files: {len([p for p in dtm_files if p.get('exists')])}/{len(dtm_files)} valid")
    print(f"🌍 DSM files: {len([p for p in dsm_files if p.get('exists')])}/{len(dsm_files)} valid") 
    print(f"🌳 CHM files: {len([p for p in chm_files if p.get('exists')])}/{len(chm_files)} valid")
    print(f"📈 Derivative files: {len([p for p in derivative_files if p.get('exists')])}/{len(derivative_files)} valid")
    
    # Check for specific mismatches
    print()
    print("🔍 SPECIFIC MISMATCH ANALYSIS:")
    print("-" * 35)
    
    valid_files = [p for p in all_properties if p.get('exists', False)]
    if len(valid_files) >= 2:
        # Group by location
        south_america_files = [p for p in valid_files if p.get('center', {}).get('y', 0) < 0]
        north_america_files = [p for p in valid_files if p.get('center', {}).get('y', 0) > 0]
        
        print(f"🌎 South America location: {len(south_america_files)} files")
        print(f"🌍 North America location: {len(north_america_files)} files")
        
        if len(south_america_files) > 0 and len(north_america_files) > 0:
            print("⚠️  WARNING: Files span multiple continents!")
        
        # Check resolution consistency
        resolutions = [p.get('resolution', {}).get('x', 0) for p in valid_files if p.get('resolution')]
        unique_resolutions = set(f"{r:.6f}" for r in resolutions)
        if len(unique_resolutions) > 1:
            print(f"⚠️  WARNING: Multiple resolutions detected: {', '.join(unique_resolutions)}")
        else:
            print(f"✅ Consistent resolution: {list(unique_resolutions)[0] if unique_resolutions else 'Unknown'}")
    
    # Save detailed results
    output_file = base_path / "box_regions_6_coherence_analysis.json"
    with open(output_file, 'w') as f:
        json.dump({
            'file_properties': all_properties,
            'coherence_analysis': comparison,
            'analysis_timestamp': str(Path(__file__).stat().st_mtime)
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
