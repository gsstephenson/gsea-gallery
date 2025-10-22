#!/usr/bin/env python3
"""
Script to annotate GSEA enrichment plots with statistics from HTML files.
- Decompresses .svg.gz files
- Extracts NES, Nominal p-value, and FDR from corresponding HTML files
- Updates SVG titles to be left-justified with GSE accession and gene set
- Adds statistical annotations to the SVG
"""

import os
import gzip
import re
from pathlib import Path
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# Paths
BASE_DIR = Path("/mnt/work_1/gest9386/CU_Boulder/rotations/RINN/log1")
INPUT_DIR = BASE_DIR / "ensplot_svgs_uncompressed"
OUTPUT_DIR = BASE_DIR / "annotated_enplots"

# Create output directory
OUTPUT_DIR.mkdir(exist_ok=True)

def extract_stats_from_html(html_path):
    """Extract NES, Nominal p-value, and FDR q-value from HTML file."""
    try:
        with open(html_path, 'r') as f:
            content = f.read()
        
        # Use regex to extract values - more reliable than BeautifulSoup for this format
        nes_match = re.search(r'Normalized Enrichment Score \(NES\)</td><td>([\d\.-]+)</td>', content)
        pval_match = re.search(r'Nominal p-value</td><td>([\d\.-]+)</td>', content)
        fdr_match = re.search(r'FDR q-value</td><td>([\d\.-]+)</td>', content)
        
        nes = nes_match.group(1) if nes_match else "N/A"
        pval = pval_match.group(1) if pval_match else "N/A"
        fdr = fdr_match.group(1) if fdr_match else "N/A"
        
        return {
            'NES': nes,
            'NOM_pval': pval,
            'FDR_qval': fdr
        }
    except Exception as e:
        print(f"Error extracting stats from {html_path}: {e}")
        return None

def find_html_file(gse_accession, regulation_type, geneset):
    """Find the corresponding HTML file for a given SVG."""
    # Map the regulation type to folder pattern
    if "DOXSET_RINN" in regulation_type:
        folder_pattern = f"{gse_accession}_DOXSET_RINN.Gsea.*"
    elif "DOXSET_1" in regulation_type or "DOXSET" in regulation_type:
        folder_pattern = f"{gse_accession}_DOXSET_1.Gsea.*"
    elif "Upregulated" in regulation_type:
        if "Diff_of_Classes" in regulation_type:
            folder_pattern = f"{gse_accession}_Upregulated_Diff_of_Classes.Gsea.*"
        else:
            folder_pattern = f"{gse_accession}_Upregulated.Gsea.*"
    elif "Downregulated" in regulation_type:
        if "Diff_of_Classes" in regulation_type:
            folder_pattern = f"{gse_accession}_Downregulated_Diff_of_Classes.Gsea.*"
        else:
            folder_pattern = f"{gse_accession}_Downregulated.Gsea.*"
    else:
        return None
    
    # Find matching directories
    import glob
    matching_dirs = glob.glob(str(BASE_DIR / folder_pattern))
    
    if not matching_dirs:
        print(f"No directory found for pattern: {folder_pattern}")
        return None
    
    dir_path = Path(matching_dirs[0])
    
    # Map geneset to HTML filename
    html_filename = f"{geneset}.html"
    html_path = dir_path / html_filename
    
    if html_path.exists():
        return html_path
    else:
        print(f"HTML file not found: {html_path}")
        return None

def modify_svg(svg_content, gse_accession, geneset, stats):
    """Modify SVG to update title and add statistics annotations."""
    # Parse SVG
    # Register namespaces to preserve them
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    
    try:
        root = ET.fromstring(svg_content)
    except Exception as e:
        print(f"Error parsing SVG: {e}")
        return None
    
    # Define namespaces
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    
    # Find and update the title text element
    # Look for text elements containing "Enrichment plot:"
    for text_elem in root.findall('.//svg:text', ns):
        text_content = text_elem.text
        if text_content and "Enrichment plot:" in text_content:
            # Update title to be left-justified with GSE and geneset
            new_title = f"{gse_accession} - {geneset} Enrichment"
            text_elem.text = new_title
            # Change x position to left-align (starting at margin)
            text_elem.set('x', '63')
            # Make it bold if not already
            style = text_elem.get('style', '')
            if 'font-weight:bold' not in style:
                if style:
                    text_elem.set('style', style + '; font-weight:bold')
                else:
                    text_elem.set('style', 'font-weight:bold; font-family:sans-serif; font-size:18px')
            break
    
    # Add statistics text annotations in the upper right corner
    # Find the existing group that contains the main plot
    g_elem = root.find('.//svg:g', ns)
    
    if g_elem is not None and stats:
        # Create text elements for statistics
        stats_y_start = 50
        stats_x = 350  # Right side of the plot
        line_spacing = 18
        
        # Create a new group for statistics
        stats_group = ET.SubElement(g_elem, 'g')
        stats_group.set('style', 'font-family:sans-serif; font-size:12px; fill:black;')
        
        # Add each statistic
        stats_lines = [
            f"NES: {stats['NES']}",
            f"NOM p-val: {stats['NOM_pval']}",
            f"FDR q-val: {stats['FDR_qval']}"
        ]
        
        for i, line in enumerate(stats_lines):
            text_elem = ET.SubElement(stats_group, 'text')
            text_elem.set('x', str(stats_x))
            text_elem.set('y', str(stats_y_start + i * line_spacing))
            text_elem.set('style', 'clip-path:url(#clipPath1); stroke:none;')
            text_elem.text = line
    
    # Convert back to string
    return ET.tostring(root, encoding='unicode', method='xml')

def process_svg_file(svg_gz_path):
    """Process a single compressed SVG file."""
    filename = svg_gz_path.name
    print(f"Processing: {filename}")
    
    # Parse filename: GSE<accession>_<regulation_type>_<geneset>_enplot.svg.gz
    # Example: GSE17580_Downregulated_DOWN_GENES_enplot.svg.gz
    # Example: GSE100132_DOXSET_RINN_DOX_UP+DOWN_GENES_enplot.svg.gz
    match = re.match(r'(GSE\d+)_(.+?)_(DOWN_GENES|UP_GENES|DOX_GENES|DOX_UP\+DOWN_GENES)_enplot\.svg\.gz', filename)
    
    if not match:
        print(f"Could not parse filename: {filename}")
        return False
    
    gse_accession = match.group(1)
    regulation_type = match.group(2)
    geneset = match.group(3)
    
    print(f"  GSE: {gse_accession}, Regulation: {regulation_type}, Geneset: {geneset}")
    
    # Find corresponding HTML file
    html_path = find_html_file(gse_accession, regulation_type, geneset)
    
    if not html_path:
        print(f"  Warning: Could not find HTML file for {filename}")
        return False
    
    # Extract statistics
    stats = extract_stats_from_html(html_path)
    
    if not stats:
        print(f"  Warning: Could not extract stats from {html_path}")
        return False
    
    print(f"  Stats: NES={stats['NES']}, NOM p-val={stats['NOM_pval']}, FDR={stats['FDR_qval']}")
    
    # Decompress SVG
    try:
        with gzip.open(svg_gz_path, 'rt') as f:
            svg_content = f.read()
    except Exception as e:
        print(f"  Error decompressing {filename}: {e}")
        return False
    
    # Modify SVG
    modified_svg = modify_svg(svg_content, gse_accession, geneset, stats)
    
    if not modified_svg:
        print(f"  Error modifying SVG for {filename}")
        return False
    
    # Save modified SVG (uncompressed)
    output_filename = filename.replace('.svg.gz', '.svg')
    output_path = OUTPUT_DIR / output_filename
    
    try:
        with open(output_path, 'w') as f:
            f.write(modified_svg)
        print(f"  ✓ Saved to: {output_filename}")
        return True
    except Exception as e:
        print(f"  Error saving {output_filename}: {e}")
        return False

def main():
    """Main processing function."""
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 80)
    
    # Get all .svg.gz files
    svg_files = sorted(INPUT_DIR.glob("*.svg.gz"))
    
    print(f"Found {len(svg_files)} SVG.GZ files to process\n")
    
    success_count = 0
    failure_count = 0
    
    for svg_file in svg_files:
        if process_svg_file(svg_file):
            success_count += 1
        else:
            failure_count += 1
        print()
    
    print("=" * 80)
    print(f"Processing complete!")
    print(f"Successfully processed: {success_count}")
    print(f"Failed: {failure_count}")
    print(f"Output directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
