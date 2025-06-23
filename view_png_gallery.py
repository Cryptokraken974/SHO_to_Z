#!/usr/bin/env python3
"""
Quick PNG viewer to examine the generated TIF visualizations
Shows before/after comparisons and highlights masked pixel visualization
"""

import os
from pathlib import Path
import webbrowser
import tempfile

def create_png_gallery_html(png_dir: str) -> str:
    """Create an HTML gallery to view the generated PNGs"""
    
    png_directory = Path(png_dir)
    if not png_directory.exists():
        print(f"❌ PNG directory not found: {png_dir}")
        return None
    
    # Collect all PNG files organized by type
    png_files = {}
    for subdir in png_directory.iterdir():
        if subdir.is_dir():
            raster_type = subdir.name
            pngs = list(subdir.glob("*.png"))
            if pngs:
                png_files[raster_type] = sorted([str(p) for p in pngs])
    
    if not png_files:
        print(f"❌ No PNG files found in {png_dir}")
        return None
    
    # Create HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced TIF Visualizations - Masked Pixel Analysis</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .masking-info {{
            background: #e8f4fd;
            border: 2px solid #2196F3;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .masking-info h3 {{
            color: #1976D2;
            margin-top: 0;
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: bold;
        }}
        
        .color-box {{
            width: 20px;
            height: 20px;
            border: 2px solid #333;
            border-radius: 3px;
        }}
        
        .masked-color {{ background-color: #ff00ff; }}
        .valid-color {{ background: linear-gradient(45deg, #00ff00, #0000ff); }}
        
        .section {{
            margin: 30px 0;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        .png-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .png-item {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .png-item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .png-item img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        
        .png-caption {{
            padding: 15px;
            background: #f8f9fa;
        }}
        
        .png-title {{
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .png-details {{
            font-size: 0.9em;
            color: #666;
        }}
        
        .mask-highlight {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 8px;
            margin-top: 8px;
        }}
        
        .mask-stats {{
            color: #d63031;
            font-weight: bold;
        }}
        
        .quality-comparison {{
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 15px;
        }}
        
        .comparison-item {{
            background: rgba(255,255,255,0.8);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .comparison-item h4 {{
            margin-top: 0;
            color: #333;
        }}
        
        @media (max-width: 768px) {{
            .png-grid {{
                grid-template-columns: 1fr;
            }}
            
            .comparison-grid {{
                grid-template-columns: 1fr;
            }}
            
            .legend {{
                flex-direction: column;
                align-items: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 Enhanced TIF Visualizations</h1>
        <p>Quality Mode LAZ Processing - Masked Pixel Analysis</p>
    </div>
    
    <div class="masking-info">
        <h3>🔍 How to Read These Visualizations</h3>
        <p><strong>Our enhanced PNGs clearly show data quality by highlighting problematic areas:</strong></p>
        
        <div class="legend">
            <div class="legend-item">
                <div class="color-box valid-color"></div>
                <span>Valid Data (Natural Colors)</span>
            </div>
            <div class="legend-item">
                <div class="color-box masked-color"></div>
                <span>Masked/Dead Pixels (Bright Magenta)</span>
            </div>
        </div>
        
        <p><strong>Key Insights:</strong></p>
        <ul>
            <li><strong>Density Rasters:</strong> Show original point distribution - magenta areas had no/few LiDAR points</li>
            <li><strong>Binary Masks:</strong> Green = valid areas to keep, Red = artifact areas to remove</li>
            <li><strong>DTM/DSM/CHM:</strong> Generated from clean LAZ show magenta where no clean data exists</li>
            <li><strong>Quality Mode Advantage:</strong> Clean rasters have NO interpolated artifacts in magenta areas</li>
        </ul>
    </div>
"""

    # Add sections for each raster type
    for raster_type, png_list in png_files.items():
        html_content += f"""
    <div class="section">
        <h2>📊 {raster_type} Rasters</h2>
"""
        
        # Special handling for density and mask types
        if raster_type.lower() == 'density':
            html_content += """
        <div class="quality-comparison">
            <h3>🌟 Quality Mode Workflow Demonstration</h3>
            <div class="comparison-grid">
                <div class="comparison-item">
                    <h4>Standard Mode</h4>
                    <p>Generate rasters → Clean with mask<br>
                    <em>(Removes interpolated artifacts)</em></p>
                </div>
                <div class="comparison-item">
                    <h4>Quality Mode</h4>
                    <p>Generate mask → Crop LAZ → Generate clean rasters<br>
                    <em>(No artifacts to begin with)</em></p>
                </div>
            </div>
        </div>
"""
        
        html_content += f"""
        <div class="png-grid">
"""
        
        for png_path in png_list:
            png_file = Path(png_path)
            filename = png_file.name
            
            # Extract information from filename
            is_mask = 'mask' in filename.lower()
            is_density = 'density' in filename.lower()
            is_quality_mode = 'quality' in filename.lower()
            
            # Determine description and masking info
            description = ""
            mask_info = ""
            
            if is_mask:
                description = "Binary mask showing valid data areas (green) vs artifact areas (red)"
                if is_quality_mode:
                    description += " - Generated in Quality Mode workflow"
            elif is_density:
                description = "Point density raster - magenta shows areas with no/few LiDAR points"
                if is_quality_mode:
                    description += " - Used to generate clean LAZ crop polygon"
            elif 'DTM' in filename:
                description = "Digital Terrain Model (ground elevation)"
                if is_quality_mode:
                    description += " - Generated from clean LAZ (no interpolated artifacts)"
                    mask_info = "Magenta areas: No clean ground points available"
            elif 'DSM' in filename:
                description = "Digital Surface Model (surface heights)"
                if is_quality_mode:
                    description += " - Generated from clean LAZ (no interpolated artifacts)"
                    mask_info = "Magenta areas: No clean surface points available"
            elif 'CHM' in filename:
                description = "Canopy Height Model (vegetation heights)"
                if is_quality_mode:
                    description += " - Generated from clean LAZ (no interpolated artifacts)"
                    mask_info = "Magenta areas: No clean vegetation data available"
            elif 'Slope' in filename:
                description = "Slope analysis (degrees)"
                if is_quality_mode:
                    description += " - Derived from clean DTM"
                    mask_info = "Magenta areas: No slope data (flat or no data)"
            elif 'Aspect' in filename:
                description = "Aspect analysis (direction of slope)"
                if is_quality_mode:
                    description += " - Derived from clean DTM"
                    mask_info = "Magenta areas: No aspect data (flat or no data)"
            elif 'Hillshade' in filename:
                description = "Hillshade visualization"
                if is_quality_mode:
                    description += " - Generated from clean DTM"
                    mask_info = "Dark areas: No hillshade data available"
            
            html_content += f"""
            <div class="png-item">
                <img src="file://{png_path}" alt="{filename}">
                <div class="png-caption">
                    <div class="png-title">{filename.replace('_enhanced.png', '').replace('_', ' ').title()}</div>
                    <div class="png-details">{description}</div>
"""
            
            if mask_info:
                html_content += f"""
                    <div class="mask-highlight">
                        <div class="mask-stats">🔍 {mask_info}</div>
                    </div>
"""
            
            html_content += """
                </div>
            </div>
"""
        
        html_content += """
        </div>
    </div>
"""
    
    # Add footer
    html_content += """
    <div class="section">
        <h2>📋 Summary</h2>
        <p><strong>The visualizations clearly demonstrate the effectiveness of the Quality Mode workflow:</strong></p>
        <ul>
            <li><strong>Artifact Detection:</strong> Density analysis and binary masks identify problematic areas</li>
            <li><strong>Clean Data Generation:</strong> Quality mode rasters show natural NoData (magenta) instead of interpolated artifacts</li>
            <li><strong>Data Integrity:</strong> Clean LAZ ensures no false interpolation in areas with insufficient point coverage</li>
            <li><strong>Visual Validation:</strong> The bright magenta highlighting makes it easy to assess data quality</li>
        </ul>
        
        <div class="quality-comparison">
            <h3>🎯 Key Takeaway</h3>
            <p><strong>Quality Mode produces superior results by eliminating interpolated artifacts at the source, 
            ensuring that all generated rasters contain only authentic data derived from actual LiDAR measurements.</strong></p>
        </div>
    </div>
    
    <div style="text-align: center; margin-top: 40px; padding: 20px; color: #666;">
        <p>Generated by Enhanced TIF Visualization Tool</p>
        <p>Date: """ + str(Path().resolve()) + """</p>
    </div>

</body>
</html>
"""
    
    return html_content

def main():
    """Main function to create and open the PNG gallery"""
    
    png_dir = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/png_visualizations"
    
    print("🎨 Creating PNG Gallery HTML...")
    html_content = create_png_gallery_html(png_dir)
    
    if html_content:
        # Save HTML to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            html_path = f.name
        
        print(f"✅ HTML gallery created: {html_path}")
        print("🌐 Opening in web browser...")
        
        # Open in web browser
        webbrowser.open(f'file://{html_path}')
        
        print(f"🎉 Gallery opened! You can also manually open: {html_path}")
        
        # Also save a permanent copy
        permanent_path = Path(png_dir) / "png_gallery.html"
        with open(permanent_path, 'w') as f:
            f.write(html_content)
        print(f"📄 Saved permanent copy: {permanent_path}")
        
        return html_path
    else:
        print("❌ Failed to create HTML gallery")
        return None

if __name__ == "__main__":
    main()
