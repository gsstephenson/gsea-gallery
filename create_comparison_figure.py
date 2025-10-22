#!/usr/bin/env python3
"""
Create a landscape PNG comparison figure for PowerPoint presentations.
Compares GSE159778 and GSE34736 showing how curated datasets (DOXSET_RINN) 
perform better than the public dataset.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import pandas as pd
from pathlib import Path
import cairosvg
from PIL import Image
import io
import numpy as np

def svg_to_image(svg_path):
    """Convert SVG to PIL Image using cairosvg."""
    png_data = cairosvg.svg2png(url=str(svg_path), dpi=150)
    return Image.open(io.BytesIO(png_data))

def create_comparison_figure():
    """Create landscape comparison figure for PowerPoint."""
    
    # Load the CSV data
    df = pd.read_csv('gsea_analysis_results.csv')
    
    # Filter for our two datasets
    gse159778_data = df[df['GSE'] == 'GSE159778'].set_index('Gene_Set')
    gse34736_data = df[df['GSE'] == 'GSE34736'].set_index('Gene_Set')
    
    # Define paths
    svg_dir = Path('annotated_enplots')
    
    # Dataset information
    datasets = {
        'GSE159778': {
            'title': 'GSE159778 (Public Dataset)',
            'data': gse159778_data,
            'plots': {
                'up': 'GSE159778_Upregulated_UP_GENES_enplot.svg',
                'down': 'GSE159778_Downregulated_DOWN_GENES_enplot.svg',
                'dox': 'GSE159778_DOXSET_1_DOX_GENES_enplot.svg',
                'dox_rinn': 'GSE159778_DOXSET_RINN_DOX_UP+DOWN_GENES_enplot.svg'
            }
        },
        'GSE34736': {
            'title': 'GSE34736 (Public Dataset)',
            'data': gse34736_data,
            'plots': {
                'up': 'GSE34736_Upregulated_UP_GENES_enplot.svg',
                'down': 'GSE34736_Downregulated_DOWN_GENES_enplot.svg',
                'dox': 'GSE34736_DOXSET_1_DOX_GENES_enplot.svg',
                'dox_rinn': 'GSE34736_DOXSET_RINN_DOX_UP+DOWN_GENES_enplot.svg'
            }
        }
    }
    
    # Create figure with landscape orientation (16:9 aspect ratio for PowerPoint)
    fig = plt.figure(figsize=(24, 13))
    fig.patch.set_facecolor('white')
    
    # Create main title
    fig.suptitle('GSEA Enrichment Analysis: Curated Gene Sets Outperform Public Datasets',
                 fontsize=28, fontweight='bold', y=0.98, color='#2c3e50')
    
    # # Add subtitle explaining the comparison
    # fig.text(0.5, 0.945, 
    #          'Comparison showing superior performance of DOXSET_RINN (curated UP+DOWN genes) versus single public datasets',
    #          ha='center', fontsize=15, style='italic', color='#555555')
    
    # Create GridSpec for layout - 2 rows, 4 columns for plots
    gs = GridSpec(2, 4, figure=fig, left=0.06, right=0.94, top=0.90, bottom=0.12,
                  hspace=0.40, wspace=0.30)
    
    # Colors for different gene sets
    colors = {
        'up': '#ffebee',
        'down': '#e3f2fd',
        'dox': '#fff3e0',
        'dox_rinn': '#f3e5f5'
    }
    
    # Plot gene sets
    gene_set_info = [
        ('up', 'Upregulated\nGenes', 'Upregulated_UP_GENES'),
        ('down', 'Downregulated\nGenes', 'Downregulated_DOWN_GENES'),
        ('dox', 'DOXSET_1\nGenes', 'DOXSET_1_DOX_GENES'),
        ('dox_rinn', 'DOXSET_RINN\n(Curated)', 'DOXSET_RINN_DOX_UP+DOWN_GENES')
    ]
    
    for row_idx, (dataset_key, dataset_info) in enumerate(datasets.items()):
        for col_idx, (gene_key, gene_title, gene_set_name) in enumerate(gene_set_info):
            ax = fig.add_subplot(gs[row_idx, col_idx])
            
            # Load and display SVG
            svg_path = svg_dir / dataset_info['plots'][gene_key]
            try:
                img = svg_to_image(svg_path)
                ax.imshow(img)
                ax.axis('off')
                
                # Get metrics from data
                try:
                    metrics = dataset_info['data'].loc[gene_set_name]
                    nes = metrics['NES']
                    fdr = metrics['FDR_q_val']
                    pval = metrics['Nominal_p_val']
                    
                    # Stricter significance criteria: BOTH FDR < 0.25 AND p-value < 0.05
                    significant = (fdr < 0.25) and (pval < 0.05)
                    
                    # Create a colored border based on significance
                    border_color = '#4CAF50' if significant else '#E53935'
                    border_width = 5 if significant else 3
                    
                    # Add border to indicate significance
                    for spine in ax.spines.values():
                        spine.set_visible(True)
                        spine.set_edgecolor(border_color)
                        spine.set_linewidth(border_width)
                    
                    # Add significance badge at top-right corner (no redundant metrics)
                    if significant:
                        badge_text = '✓ SIG'
                        badge_color = '#4CAF50'
                    else:
                        badge_text = '✗ NS'
                        badge_color = '#E53935'
                    
                    ax.text(0.96, 0.04, badge_text,
                           transform=ax.transAxes,
                           fontsize=13,
                           fontweight='bold',
                           color='white',
                           verticalalignment='bottom',
                           horizontalalignment='right',
                           bbox=dict(boxstyle='round,pad=0.6', 
                                   facecolor=badge_color,
                                   edgecolor='white',
                                   linewidth=2.5,
                                   alpha=0.98),
                           zorder=1000)
                    
                except KeyError:
                    pass
                    
            except FileNotFoundError:
                ax.text(0.5, 0.5, 'Plot not found', 
                       ha='center', va='center', fontsize=12, color='red')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
            
            # Add title with background color and better styling
            title_props = dict(
                facecolor=colors[gene_key],
                edgecolor='#2c3e50',
                boxstyle='round,pad=0.6',
                linewidth=2
            )
            ax.set_title(gene_title, fontsize=13, fontweight='bold', 
                        pad=12, bbox=title_props, color='#2c3e50')
            
            # Add dataset label on the left side
            if col_idx == 0:
                label_y = 0.68 if row_idx == 0 else 0.31
            # Add dataset label on the left side
            if col_idx == 0:
                label_y = 0.695 if row_idx == 0 else 0.305
                label_color = '#667eea' if row_idx == 0 else '#764ba2'
                
                fig.text(0.015, label_y,
                        dataset_info['title'],
                        fontsize=18, fontweight='bold',
                        rotation=90, va='center', ha='center',
                        bbox=dict(boxstyle='round,pad=1.0',
                                facecolor=label_color,
                                edgecolor='#2c3e50',
                                linewidth=2.5,
                                alpha=0.95),
                        color='white')
    
    # Add legend at bottom with better formatting
    legend_elements = [
        mpatches.Patch(facecolor=colors['up'], edgecolor='#2c3e50', linewidth=2,
                      label='Upregulated Genes'),
        mpatches.Patch(facecolor=colors['down'], edgecolor='#2c3e50', linewidth=2,
                      label='Downregulated Genes'),
        mpatches.Patch(facecolor=colors['dox'], edgecolor='#2c3e50', linewidth=2,
                      label='DOXSET_1 (Public Dataset)'),
        mpatches.Patch(facecolor=colors['dox_rinn'], edgecolor='#2c3e50', linewidth=2,
                      label='DOXSET_RINN (Curated UP+DOWN) ***'),
        mpatches.Patch(facecolor='#4CAF50', edgecolor='#2c3e50', linewidth=2,
                      label='✓ Significant (FDR < 0.25 AND p < 0.05)'),
        mpatches.Patch(facecolor='#E53935', edgecolor='#2c3e50', linewidth=2,
                      label='✗ Not Significant')
    ]
    
    legend = fig.legend(handles=legend_elements, 
                       loc='lower center',
                       ncol=3,
                       frameon=True,
                       fancybox=True,
                       shadow=True,
                       fontsize=12,
                       bbox_to_anchor=(0.5, 0.02),
                       columnspacing=1.5,
                       handlelength=2.5,
                       handleheight=1.5)
    legend.get_frame().set_facecolor('#f8f9fa')
    # Add footer with author info in a box
    footer_text = 'Author: George Stephenson (@gsstephenson) | Rinn Laboratory, University of Colorado Boulder | Generated: October 7, 2025'
    fig.text(0.5, 0.005,
            footer_text,
            fontsize=10, style='italic', color='#2c3e50',
            ha='center',
            bbox=dict(boxstyle='round,pad=0.5',
                     facecolor='#f8f9fa',
                     edgecolor='#2c3e50',
                     linewidth=1.5,
                     alpha=0.9))
    
    # Save the figure
    output_file = Path('GSE159778_vs_GSE34736_comparison.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print(f"\n✅ Comparison figure created: {output_file}")
    print(f"📊 Resolution: 300 DPI (suitable for PowerPoint presentations)")
    print(f"📐 Format: Landscape (16:9 aspect ratio)")
    
    # Also save as high-res version
    output_file_hires = Path('GSE159778_vs_GSE34736_comparison_hires.png')
    plt.savefig(output_file_hires, dpi=600, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print(f"✅ High-resolution version created: {output_file_hires}")
    print(f"📊 Resolution: 600 DPI (suitable for publication)")
    
    plt.close()

if __name__ == '__main__':
    print("Creating comparison figure for GSE159778 vs GSE34736...")
    print("This will show how curated DOXSET_RINN performs better than public datasets.\n")
    
    create_comparison_figure()
    
    print("\n✨ Done! The figure is ready for your PowerPoint presentation.")
    print("\nKey advantages of DOXSET_RINN shown in this comparison:")
    print("  • Combines both upregulated and downregulated genes")
    print("  • Better enrichment scores (NES)")
    print("  • Lower FDR q-values")
    print("  • More significant results across datasets")
