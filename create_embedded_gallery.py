#!/usr/bin/env python3
"""
Create a self-contained HTML gallery with all SVG files embedded as Base64.
This creates a single portable HTML file that can be opened on any computer.
"""

import base64
from pathlib import Path

def svg_to_base64(svg_path):
    """Convert SVG file to base64 data URI."""
    with open(svg_path, 'rb') as f:
        svg_data = f.read()
    b64_data = base64.b64encode(svg_data).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64_data}"

def create_embedded_gallery():
    """Create self-contained HTML gallery with embedded SVGs."""
    
    svg_dir = Path('annotated_enplots')
    
    # Automatically detect all datasets from the directory
    all_files = list(svg_dir.glob('*.svg'))
    datasets = sorted(set(f.name.split('_')[0] for f in all_files))
    
    print(f"Found {len(datasets)} datasets: {', '.join(datasets)}")
    
    # Detect which datasets have "Diff of Classes" naming
    diff_of_classes = []
    for dataset in datasets:
        diff_files = list(svg_dir.glob(f'{dataset}_*Diff_of_Classes*.svg'))
        if diff_files:
            diff_of_classes.append(dataset)
    
    print("Encoding SVG files to Base64...")
    
    # Build the embedded data dictionary
    embedded_svgs = {}
    for dataset in datasets:
        print(f"Processing {dataset}...")
        
        # Determine file patterns
        if dataset in diff_of_classes:
            up_pattern = f"{dataset}_Upregulated_Diff_of_Classes_UP_GENES_enplot.svg"
            down_pattern = f"{dataset}_Downregulated_Diff_of_Classes_DOWN_GENES_enplot.svg"
        else:
            up_pattern = f"{dataset}_Upregulated_UP_GENES_enplot.svg"
            down_pattern = f"{dataset}_Downregulated_DOWN_GENES_enplot.svg"
        
        dox_pattern = f"{dataset}_DOXSET_1_DOX_GENES_enplot.svg"
        dox_rinn_pattern = f"{dataset}_DOXSET_RINN_DOX_UP+DOWN_GENES_enplot.svg"
        
        # Convert to base64
        try:
            embedded_svgs[f"{dataset}_up"] = svg_to_base64(svg_dir / up_pattern)
            embedded_svgs[f"{dataset}_down"] = svg_to_base64(svg_dir / down_pattern)
            embedded_svgs[f"{dataset}_dox"] = svg_to_base64(svg_dir / dox_pattern)
            # Try to add DOXSET_RINN if it exists
            try:
                embedded_svgs[f"{dataset}_dox_rinn"] = svg_to_base64(svg_dir / dox_rinn_pattern)
            except FileNotFoundError:
                print(f"  Note: No DOXSET_RINN plot for {dataset}")
        except FileNotFoundError as e:
            print(f"Warning: {e}")
            continue
    
    print(f"\nSuccessfully encoded {len(embedded_svgs)} SVG files")
    
    # Generate HTML with embedded SVGs
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GSEA Enrichment Plots Gallery (Self-Contained)</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        header p {{
            font-size: 1.2em;
            opacity: 0.95;
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
            font-size: 1.1em;
        }}
        
        .legend-box {{
            width: 30px;
            height: 30px;
            border-radius: 5px;
            border: 2px solid #333;
        }}
        
        .legend-upregulated {{ background: #ffebee; }}
        .legend-downregulated {{ background: #e3f2fd; }}
        .legend-dox {{ background: #fff3e0; }}
        .legend-dox-rinn {{ background: #f3e5f5; }}
        
        .gallery {{
            padding: 30px;
        }}
        
        .dataset-row {{
            margin-bottom: 40px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            background: #fafafa;
        }}
        
        .dataset-header {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            font-size: 1.3em;
            font-weight: bold;
            letter-spacing: 1px;
        }}
        
        .plots-container {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0;
            background: white;
        }}
        
        .plot-wrapper {{
            border: 1px solid #e0e0e0;
            padding: 15px;
            background: white;
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .plot-wrapper:hover {{
            transform: scale(1.02);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            z-index: 10;
        }}
        
        .plot-wrapper.upregulated {{
            background: #ffebee;
        }}
        
        .plot-wrapper.downregulated {{
            background: #e3f2fd;
        }}
        
        .plot-wrapper.dox {{
            background: #fff3e0;
        }}
        
        .plot-wrapper.dox-rinn {{
            background: #f3e5f5;
        }}
        
        .plot-title {{
            font-weight: bold;
            margin-bottom: 10px;
            padding: 8px;
            background: rgba(255,255,255,0.9);
            border-radius: 5px;
            text-align: center;
            font-size: 0.95em;
            color: #333;
        }}
        
        .plot-wrapper img {{
            width: 100%;
            height: auto;
            display: block;
            border-radius: 5px;
            border: 1px solid #ddd;
        }}
        
        footer {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }}
        
        .stats-badge {{
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        
        .portable-badge {{
            display: inline-block;
            background: #FF9800;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
            margin-left: 10px;
        }}
        
        @media (max-width: 1200px) {{
            .plots-container {{
                grid-template-columns: 1fr;
            }}
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .plot-wrapper:hover {{
                transform: none;
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧬 GSEA Enrichment Plots Gallery</h1>
            <p>Comprehensive Analysis of {len(datasets)} GEO Datasets</p>
            <div class="stats-badge">{len(embedded_svgs)} Total Plots | {len(datasets)} Datasets | Up to 4 Gene Sets Each</div>
            <div class="portable-badge">📦 Self-Contained | Fully Portable</div>
        </header>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-box legend-upregulated"></div>
                <span>Upregulated Genes</span>
            </div>
            <div class="legend-item">
                <div class="legend-box legend-downregulated"></div>
                <span>Downregulated Genes</span>
            </div>
            <div class="legend-item">
                <div class="legend-box legend-dox"></div>
                <span>DOXSET_1 Genes</span>
            </div>
            <div class="legend-item">
                <div class="legend-box legend-dox-rinn"></div>
                <span>DOXSET_RINN Genes</span>
            </div>
        </div>
        
        <div class="gallery">
'''
    
    # Generate dataset rows
    for dataset in datasets:
        diff_suffix = " (Diff of Classes)" if dataset in diff_of_classes else ""
        
        html_content += f'''
            <!-- {dataset} -->
            <div class="dataset-row">
                <div class="dataset-header">{dataset}</div>
                <div class="plots-container">
                    <div class="plot-wrapper upregulated">
                        <div class="plot-title">Upregulated Genes{diff_suffix}</div>
                        <img src="{embedded_svgs.get(f'{dataset}_up', '')}" alt="{dataset} Upregulated">
                    </div>
                    <div class="plot-wrapper downregulated">
                        <div class="plot-title">Downregulated Genes{diff_suffix}</div>
                        <img src="{embedded_svgs.get(f'{dataset}_down', '')}" alt="{dataset} Downregulated">
                    </div>
                    <div class="plot-wrapper dox">
                        <div class="plot-title">DOXSET_1 Genes</div>
                        <img src="{embedded_svgs.get(f'{dataset}_dox', '')}" alt="{dataset} DOXSET_1">
                    </div>
                    <div class="plot-wrapper dox-rinn">
                        <div class="plot-title">DOXSET_RINN Genes</div>
                        <img src="{embedded_svgs.get(f'{dataset}_dox_rinn', '')}" alt="{dataset} DOXSET_RINN">
                    </div>
                </div>
            </div>
'''
    
    # Close HTML
    html_content += '''
        </div>
        
        <footer>
            <p><strong>GSEA Enrichment Plots Gallery - Self-Contained Version</strong></p>
            <p>Generated on October 1, 2025 | Total Datasets: ''' + str(len(datasets)) + ''' | Total Plots: ''' + str(len(embedded_svgs)) + '''</p>
            <p style="margin-top: 10px; opacity: 0.8;">Each plot includes NES (Normalized Enrichment Score), NOM p-value, and FDR q-value annotations</p>
            <p style="margin-top: 10px; opacity: 0.8;"><em>This file is fully self-contained and can be opened on any computer without external dependencies</em></p>
            <hr style="margin: 20px auto; width: 80%; border: none; border-top: 1px solid rgba(255,255,255,0.3);">
            <div style="margin-top: 20px; padding: 15px; background: rgba(0,0,0,0.1); border-radius: 8px;">
                <p style="font-size: 0.95em; margin-bottom: 8px;">
                    <strong>Author:</strong> George Stephenenson 
                    <a href="https://github.com/gsstephenson" target="_blank" style="color: #4CAF50; text-decoration: none; margin-left: 5px;">
                        <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z'/%3E%3C/svg%3E" alt="GitHub" style="vertical-align: middle;">
                        @gsstephenson
                    </a>
                </p>
                <p style="font-size: 0.9em; opacity: 0.9;">
                    <strong>Data Source:</strong> Rinn Laboratory, University of Colorado Boulder
                </p>
                <p style="font-size: 0.85em; margin-top: 10px; opacity: 0.8; font-style: italic;">
                    All data and analyses are property of the Rinn Laboratory. For inquiries regarding data usage, please contact the Rinn Lab.
                </p>
            </div>
        </footer>
    </div>
</body>
</html>
'''
    
    # Write the self-contained HTML file
    output_file = Path('enrichment_plots_gallery_gsstephenson.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"\n✅ Self-contained HTML gallery created: {output_file}")
    print(f"📦 File size: {file_size_mb:.2f} MB")
    print(f"✨ This file can be opened on any computer without external dependencies!")

if __name__ == '__main__':
    create_embedded_gallery()
