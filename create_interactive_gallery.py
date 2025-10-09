#!/usr/bin/env python3
"""
Create interactive HTML galleries (SVG + PNG variants) with dataset selection.
Users can multi-select which GSE datasets to view before displaying the plots.

Outputs:
1. `enrichment_plots_gallery_interactive.html` — embeds SVG plots (best for local use).
2. `enrichment_plots_gallery_interactive_png.html` — embeds PNG plots (lighter for web).
3. PNG versions of each SVG written to `annotated_enplots_png/` and mirrored to
   `docs/annotated_enplots_png/` for GitHub Pages hosting.
"""

import base64
import shutil
from datetime import date
from pathlib import Path

try:
    import cairosvg  # type: ignore
except ImportError as exc:  # pragma: no cover - dependency check
    raise SystemExit(
        "cairosvg is required. Install with `pip install cairosvg`."
    ) from exc

def svg_to_base64(svg_path):
    """Convert SVG file to base64 data URI."""
    with open(svg_path, 'rb') as f:
        svg_data = f.read()
    b64_data = base64.b64encode(svg_data).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64_data}"


def png_to_base64(png_path):
    """Convert PNG file to base64 data URI."""
    with open(png_path, 'rb') as f:
        png_data = f.read()
    b64_data = base64.b64encode(png_data).decode('utf-8')
    return f"data:image/png;base64,{b64_data}"


def ensure_png(svg_path: Path, target_path: Path) -> Path:
    """Render `svg_path` to `target_path` if missing or stale."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if not target_path.exists() or target_path.stat().st_mtime < svg_path.stat().st_mtime:
        cairosvg.svg2png(url=str(svg_path), write_to=str(target_path))
    return target_path


def build_dataset_js(datasets, diff_of_classes, data_lookup):
    """Return JavaScript object literal string for the dataset image mapping."""
    lines = ["const datasetImages = {"]
    for dataset in datasets:
        diff_suffix = " (Diff of Classes)" if dataset in diff_of_classes else ""
        lines.append(f"    '{dataset}': {{")
        lines.append(f"        up: '{data_lookup.get(f'{dataset}_up', '')}',")
        lines.append(f"        down: '{data_lookup.get(f'{dataset}_down', '')}',")
        lines.append(f"        dox: '{data_lookup.get(f'{dataset}_dox', '')}',")
        lines.append(f"        dox_rinn: '{data_lookup.get(f'{dataset}_dox_rinn', '')}',")
        lines.append(f"        diffSuffix: '{diff_suffix}'")
        lines.append("    },")
    lines.append("};")
    return "\n".join(lines)


def build_html(dataset_js: str, datasets, subtitle: str, footer_note: str, title_emoji: str) -> str:
    """Return full HTML string for the interactive gallery."""
    dataset_options_markup = ''.join(
        f'<div class="dataset-option"><input type="checkbox" id="gse_{ds}" value="{ds}"><label for="gse_{ds}">{ds}</label></div>'
        for ds in datasets
    )
    dataset_count = len(datasets)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GSEA Enrichment Plots - Interactive Gallery</title>
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
        
        .selection-panel {{
            background: #f8f9fa;
            padding: 30px;
            border-bottom: 3px solid #667eea;
        }}
        
        .selection-panel h2 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}
        
        .selection-controls {{
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .dataset-selector {{
            background: white;
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 15px;
        }}
        
        .dataset-selector label {{
            display: block;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
            font-size: 1.1em;
        }}
        
        .dataset-options {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            max-height: 300px;
            overflow-y: auto;
            padding: 10px;
            background: #fafafa;
            border-radius: 5px;
        }}
        
        .dataset-option {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .dataset-option:hover {{
            background: #e3f2fd;
            border-color: #667eea;
        }}
        
        .dataset-option input[type="checkbox"] {{
            cursor: pointer;
            width: 18px;
            height: 18px;
        }}
        
        .dataset-option label {{
            cursor: pointer;
            margin: 0;
            font-weight: normal;
            font-size: 0.95em;
        }}
        
        .button-group {{
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 12px 30px;
            font-size: 1.1em;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        }}
        
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        
        .btn-secondary:hover {{
            background: #5a6268;
            transform: translateY(-2px);
        }}
        
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        
        .btn-success:hover {{
            background: #218838;
        }}
        
        .btn-warning {{
            background: #ffc107;
            color: #212529;
        }}
        
        .btn-warning:hover {{
            background: #e0a800;
        }}
        
        .selection-info {{
            text-align: center;
            padding: 15px;
            background: #e3f2fd;
            border-radius: 8px;
            margin-top: 15px;
        }}
        
        .selection-info .count {{
            font-size: 1.2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 2px solid #e0e0e0;
            display: none;
        }}
        
        .legend.visible {{
            display: flex;
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
            display: none;
        }}
        
        .gallery.visible {{
            display: block;
        }}
        
        .no-selection-message {{
            text-align: center;
            padding: 60px 20px;
            display: none;
        }}
        
        .no-selection-message.visible {{
            display: block;
        }}
        
        .no-selection-message h2 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 15px;
        }}
        
        .no-selection-message p {{
            color: #666;
            font-size: 1.2em;
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
        
        .back-to-top {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #667eea;
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: none;
            align-items: center;
            justify-content: center;
            font-size: 1.5em;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s;
            z-index: 1000;
        }}
        
        .back-to-top:hover {{
            background: #764ba2;
            transform: translateY(-5px);
        }}
        
        .back-to-top.visible {{
            display: flex;
        }}
        
        @media (max-width: 1200px) {{
            .plots-container {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .dataset-options {{
                grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            }}
        }}
        
        @media (max-width: 768px) {{
            .plots-container {{
                grid-template-columns: 1fr;
            }}
            
            .legend {{
                flex-direction: column;
                gap: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title_emoji} GSEA Enrichment Plots - Interactive Gallery</h1>
            <p>{subtitle}</p>
        </header>
        
        <div class="selection-panel">
            <h2>📊 Select Datasets to Display</h2>
            <div class="selection-controls">
                <div class="dataset-selector">
                    <label>Choose GSE Datasets ({dataset_count} available):</label>
                    <div class="dataset-options" id="datasetOptions">
                        {dataset_options_markup}
                    </div>
                </div>
                
                <div class="button-group">
                    <button class="btn btn-success" onclick="selectAll()">✓ Select All</button>
                    <button class="btn btn-warning" onclick="clearAll()">✗ Clear All</button>
                    <button class="btn btn-secondary" onclick="toggleSelection()">⇄ Invert Selection</button>
                </div>
                
                <div class="selection-info">
                    <span class="count" id="selectionCount">0 datasets selected</span>
                </div>
                
                <button class="btn btn-primary" onclick="displaySelected()" style="font-size: 1.3em; padding: 15px 40px;">
                    🔍 Display Selected Datasets
                </button>
            </div>
        </div>
        
        <div class="legend" id="legend">
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
        
        <div class="no-selection-message" id="noSelectionMessage">
            <h2>👆 Select datasets above to begin</h2>
            <p>Choose one or more GSE datasets from the selection panel, then click "Display Selected Datasets"</p>
        </div>
        
        <div class="gallery" id="gallery"></div>
        
        <footer>
            <p><strong>GSEA Enrichment Plots Gallery - Interactive Version</strong></p>
            <p>{footer_note}</p>
            <p style="margin-top: 10px; opacity: 0.8;">Each plot includes NES (Normalized Enrichment Score), NOM p-value, and FDR q-value annotations</p>
            <hr style="margin: 20px auto; width: 80%; border: none; border-top: 1px solid rgba(255,255,255,0.3);">
            <div style="margin-top: 20px; padding: 15px; background: rgba(0,0,0,0.1); border-radius: 8px;">
                <p style="font-size: 0.95em; margin-bottom: 8px;">
                    <strong>Author:</strong> George Stephenenson 
                    <a href="https://github.com/gsstephenson" target="_blank" style="color: #4CAF50; text-decoration: none; margin-left: 5px;">
                        @gsstephenson
                    </a>
                </p>
                <p style="font-size: 0.9em; opacity: 0.9;">
                    <strong>Data Source:</strong> Rinn Laboratory, University of Colorado Boulder
                </p>
            </div>
        </footer>
    </div>
    
    <div class="back-to-top" id="backToTop" onclick="scrollToTop()">↑</div>
    
    <script>
        {dataset_js}
        
        // Update selection count
        function updateSelectionCount() {{
            const checkboxes = document.querySelectorAll('#datasetOptions input[type="checkbox"]');
            const checked = Array.from(checkboxes).filter(cb => cb.checked).length;
            document.getElementById('selectionCount').textContent = `${{checked}} dataset${{checked !== 1 ? 's' : ''}} selected`;
        }}
        
        // Select all datasets
        function selectAll() {{
            const checkboxes = document.querySelectorAll('#datasetOptions input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = true);
            updateSelectionCount();
        }}
        
        // Clear all selections
        function clearAll() {{
            const checkboxes = document.querySelectorAll('#datasetOptions input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = false);
            updateSelectionCount();
            
            // Hide gallery and show message
            document.getElementById('gallery').classList.remove('visible');
            document.getElementById('legend').classList.remove('visible');
            document.getElementById('noSelectionMessage').classList.add('visible');
        }}
        
        // Toggle selection
        function toggleSelection() {{
            const checkboxes = document.querySelectorAll('#datasetOptions input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = !cb.checked);
            updateSelectionCount();
        }}
        
        // Display selected datasets
        function displaySelected() {{
            const checkboxes = document.querySelectorAll('#datasetOptions input[type="checkbox"]:checked');
            const selectedDatasets = Array.from(checkboxes).map(cb => cb.value);
            
            if (selectedDatasets.length === 0) {{
                alert('Please select at least one dataset to display.');
                return;
            }}
            
            // Build gallery HTML
            let galleryHTML = '';
            
            selectedDatasets.forEach(dataset => {{
                const images = datasetImages[dataset];
                if (!images) return;
                
                galleryHTML += `
                    <div class="dataset-row">
                        <div class="dataset-header">${{dataset}}</div>
                        <div class="plots-container">
                            <div class="plot-wrapper upregulated">
                                <div class="plot-title">Upregulated Genes${{images.diffSuffix}}</div>
                                <img src="${{images.up}}" alt="${{dataset}} Upregulated" loading="lazy">
                            </div>
                            <div class="plot-wrapper downregulated">
                                <div class="plot-title">Downregulated Genes${{images.diffSuffix}}</div>
                                <img src="${{images.down}}" alt="${{dataset}} Downregulated" loading="lazy">
                            </div>
                            <div class="plot-wrapper dox">
                                <div class="plot-title">DOXSET_1 Genes</div>
                                <img src="${{images.dox}}" alt="${{dataset}} DOXSET_1" loading="lazy">
                            </div>
                            <div class="plot-wrapper dox-rinn">
                                <div class="plot-title">DOXSET_RINN Genes</div>
                                <img src="${{images.dox_rinn}}" alt="${{dataset}} DOXSET_RINN" loading="lazy">
                            </div>
                        </div>
                    </div>
                `;
            }});
            
            // Update gallery
            document.getElementById('gallery').innerHTML = galleryHTML;
            document.getElementById('gallery').classList.add('visible');
            document.getElementById('legend').classList.add('visible');
            document.getElementById('noSelectionMessage').classList.remove('visible');
            
            // Scroll to gallery
            document.getElementById('legend').scrollIntoView({{ behavior: 'smooth' }});
        }}
        
        // Scroll to top
        function scrollToTop() {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
        
        // Show/hide back to top button
        window.addEventListener('scroll', function() {{
            const backToTop = document.getElementById('backToTop');
            if (window.pageYOffset > 300) {{
                backToTop.classList.add('visible');
            }} else {{
                backToTop.classList.remove('visible');
            }}
        }});
        
        // Add event listeners to checkboxes
        document.querySelectorAll('#datasetOptions input[type="checkbox"]').forEach(checkbox => {{
            checkbox.addEventListener('change', updateSelectionCount);
        }});
        
        // Initialize
        updateSelectionCount();
    </script>
</body>
</html>
'''

def create_interactive_gallery():
    """Create interactive HTML gallery with dataset selection."""
    
    svg_dir = Path('annotated_enplots')
    png_dir = Path('annotated_enplots_png')
    docs_png_dir = Path('docs/annotated_enplots_png')
    
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
    
    print("Encoding SVG and PNG files to Base64...")
    png_dir.mkdir(exist_ok=True)
    docs_png_dir.mkdir(parents=True, exist_ok=True)
    
    # Build the embedded data dictionary
    embedded_svgs = {}
    embedded_pngs = {}
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
            up_svg_path = svg_dir / up_pattern
            down_svg_path = svg_dir / down_pattern
            dox_svg_path = svg_dir / dox_pattern
            dox_rinn_svg_path = svg_dir / dox_rinn_pattern

            embedded_svgs[f"{dataset}_up"] = svg_to_base64(up_svg_path)
            embedded_svgs[f"{dataset}_down"] = svg_to_base64(down_svg_path)
            embedded_svgs[f"{dataset}_dox"] = svg_to_base64(dox_svg_path)

            # Render PNGs (one central place)
            up_png = ensure_png(up_svg_path, png_dir / up_pattern.replace('.svg', '.png'))
            down_png = ensure_png(down_svg_path, png_dir / down_pattern.replace('.svg', '.png'))
            dox_png = ensure_png(dox_svg_path, png_dir / dox_pattern.replace('.svg', '.png'))

            for png_path in (up_png, down_png, dox_png):
                shutil.copy2(png_path, docs_png_dir / png_path.name)

            embedded_pngs[f"{dataset}_up"] = png_to_base64(up_png)
            embedded_pngs[f"{dataset}_down"] = png_to_base64(down_png)
            embedded_pngs[f"{dataset}_dox"] = png_to_base64(dox_png)
            # Try to add DOXSET_RINN if it exists
            try:
                embedded_svgs[f"{dataset}_dox_rinn"] = svg_to_base64(dox_rinn_svg_path)
                dox_rinn_png = ensure_png(dox_rinn_svg_path, png_dir / dox_rinn_pattern.replace('.svg', '.png'))
                shutil.copy2(dox_rinn_png, docs_png_dir / dox_rinn_png.name)
                embedded_pngs[f"{dataset}_dox_rinn"] = png_to_base64(dox_rinn_png)
            except FileNotFoundError:
                print(f"  Note: No DOXSET_RINN plot for {dataset}")
                embedded_svgs[f"{dataset}_dox_rinn"] = ''
                embedded_pngs[f"{dataset}_dox_rinn"] = ''
        except FileNotFoundError as e:
            print(f"Warning: {e}")
            continue
    
    print(f"\nSuccessfully encoded {len(embedded_svgs)} SVG files")
    print(f"Successfully encoded {len(embedded_pngs)} PNG files")
    
    svg_js = build_dataset_js(datasets, diff_of_classes, embedded_svgs)
    png_js = build_dataset_js(datasets, diff_of_classes, embedded_pngs)

    generated_on = date.today().strftime('%B %d, %Y')

    svg_html = build_html(
        dataset_js=svg_js,
        datasets=datasets,
        subtitle="Select datasets to compare and analyze",
        footer_note=(
            f"Generated on {generated_on} | {len(datasets)} Datasets Available | "
            f"{len(embedded_svgs)} Total SVG Plots"
        ),
        title_emoji="🧬"
    )
    png_html = build_html(
        dataset_js=png_js,
        datasets=datasets,
        subtitle="PNG-optimized version for web streaming",
        footer_note=(
            f"Generated on {generated_on} | {len(datasets)} Datasets Available | "
            f"{len(embedded_pngs)} Total PNG Plots"
        ),
        title_emoji="🧬"
    )

    svg_output = Path('enrichment_plots_gallery_interactive.html')
    svg_output.write_text(svg_html, encoding='utf-8')
    png_output = Path('enrichment_plots_gallery_interactive_png.html')
    png_output.write_text(png_html, encoding='utf-8')

    docs_dir = Path('docs')
    docs_dir.mkdir(exist_ok=True)
    docs_index = docs_dir / 'index.html'
    docs_png = docs_dir / 'enrichment_plots_gallery_interactive_png.html'
    docs_index.write_text(png_html, encoding='utf-8')
    docs_png.write_text(png_html, encoding='utf-8')

    def report(path: Path, label: str) -> None:
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"\n✅ {label} created: {path}")
        print(f"📦 File size: {size_mb:.2f} MB")
        print("✨ Features:")
        print("   • Multi-select dataset filter")
        print("   • Select All / Clear All / Invert Selection buttons")
        print("   • Dynamic display of selected datasets only")
        print("   • Back-to-top button for easy navigation")

    report(svg_output, "Interactive SVG gallery")
    report(png_output, "Interactive PNG gallery")

if __name__ == '__main__':
    create_interactive_gallery()
