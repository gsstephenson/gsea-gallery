#!/usr/bin/env python3
"""
Extract and analyze GSEA statistics from SVG enrichment plots.
Evaluates each gene set against significance cutoffs:
- NES (Normalized Enrichment Score): |NES| >= 1.0 for significance
- FDR (False Discovery Rate): <= 0.25 (25%) for significance
- Nominal p-value: <= 0.05 for significance
"""

import os
import re
import pandas as pd
from pathlib import Path

def extract_stats_from_svg(svg_file):
    """Extract NES, FDR q-val, and nominal p-val from SVG file."""
    try:
        with open(svg_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract statistics using regex
        nes_match = re.search(r'NES:\s*([-+]?\d*\.?\d+)', content)
        fdr_match = re.search(r'FDR q-val:\s*([-+]?\d*\.?\d+)', content)
        pval_match = re.search(r'NOM p-val:\s*([-+]?\d*\.?\d+)', content)
        
        nes = float(nes_match.group(1)) if nes_match else None
        fdr = float(fdr_match.group(1)) if fdr_match else None
        pval = float(pval_match.group(1)) if pval_match else None
        
        return nes, fdr, pval
    
    except Exception as e:
        print(f"Error processing {svg_file}: {e}")
        return None, None, None

def evaluate_significance(nes, fdr, pval):
    """Evaluate if gene set meets significance cutoffs."""
    # NES: |NES| >= 1.0 for significance
    nes_significant = abs(nes) >= 1.0 if nes is not None else False
    
    # FDR: <= 0.25 (25%) for significance
    fdr_significant = fdr <= 0.25 if fdr is not None else False
    
    # Nominal p-value: <= 0.05 for significance
    pval_significant = pval <= 0.05 if pval is not None else False
    
    # Overall significance: meets FDR cutoff (primary criterion)
    overall_significant = fdr_significant
    
    return nes_significant, fdr_significant, pval_significant, overall_significant

def analyze_gsea_results():
    """Analyze all GSEA results from SVG files."""
    svg_dir = Path("/mnt/work_1/gest9386/CU_Boulder/rotations/RINN/log1/annotated_enplots")
    
    results = []
    
    # Process all SVG files
    for svg_file in sorted(svg_dir.glob("*.svg")):
        filename = svg_file.name
        
        # Parse filename to extract GSE, gene set type
        parts = filename.replace("_enplot.svg", "").split("_")
        if len(parts) >= 2:
            gse = parts[0]
            gene_set = "_".join(parts[1:])
        else:
            continue
        
        # Extract statistics
        nes, fdr, pval = extract_stats_from_svg(svg_file)
        
        if nes is not None and fdr is not None and pval is not None:
            # Evaluate significance
            nes_sig, fdr_sig, pval_sig, overall_sig = evaluate_significance(nes, fdr, pval)
            
            results.append({
                'GSE': gse,
                'Gene_Set': gene_set,
                'NES': nes,
                'FDR_q_val': fdr,
                'Nominal_p_val': pval,
                'NES_Significant': nes_sig,
                'FDR_Significant': fdr_sig,
                'PVal_Significant': pval_sig,
                'Overall_Significant': overall_sig,
                'Filename': filename
            })
    
    return pd.DataFrame(results)

def main():
    """Main analysis function."""
    print("🔬 Analyzing GSEA Enrichment Results")
    print("=" * 50)
    
    # Analyze results
    df = analyze_gsea_results()
    
    if df.empty:
        print("❌ No valid GSEA results found!")
        return
    
    print(f"📊 Analyzed {len(df)} enrichment analyses")
    print(f"📁 From {df['GSE'].nunique()} datasets")
    print(f"🧬 Testing {df['Gene_Set'].nunique()} gene sets")
    print()
    
    # Significance cutoffs
    print("📋 SIGNIFICANCE CUTOFFS:")
    print("• NES (Normalized Enrichment Score): |NES| ≥ 1.0")
    print("• FDR q-value: ≤ 0.25 (25%)")
    print("• Nominal p-value: ≤ 0.05 (5%)")
    print("• Overall Significance: Based on FDR ≤ 0.25")
    print()
    
    # Summary statistics
    print("📈 SUMMARY STATISTICS:")
    print(f"• NES significant (|NES| ≥ 1.0): {df['NES_Significant'].sum()}/{len(df)} ({df['NES_Significant'].mean()*100:.1f}%)")
    print(f"• FDR significant (≤ 0.25): {df['FDR_Significant'].sum()}/{len(df)} ({df['FDR_Significant'].mean()*100:.1f}%)")
    print(f"• p-value significant (≤ 0.05): {df['PVal_Significant'].sum()}/{len(df)} ({df['PVal_Significant'].mean()*100:.1f}%)")
    print(f"• Overall significant: {df['Overall_Significant'].sum()}/{len(df)} ({df['Overall_Significant'].mean()*100:.1f}%)")
    print()
    
    # Results by gene set
    print("🧬 RESULTS BY GENE SET:")
    gene_set_summary = df.groupby('Gene_Set').agg({
        'Overall_Significant': ['count', 'sum'],
        'NES': 'mean',
        'FDR_q_val': 'mean'
    }).round(4)
    
    gene_set_summary.columns = ['Total_Tests', 'Significant_Tests', 'Mean_NES', 'Mean_FDR']
    gene_set_summary['Success_Rate'] = (gene_set_summary['Significant_Tests'] / gene_set_summary['Total_Tests'] * 100).round(1)
    
    for idx, row in gene_set_summary.iterrows():
        print(f"• {idx}:")
        print(f"  - Significant: {row['Significant_Tests']}/{row['Total_Tests']} ({row['Success_Rate']}%)")
        print(f"  - Mean NES: {row['Mean_NES']:.3f}")
        print(f"  - Mean FDR: {row['Mean_FDR']:.3f}")
    print()
    
    # Detailed results for significant enrichments
    significant_results = df[df['Overall_Significant']].copy()
    if not significant_results.empty:
        print(f"🎯 SIGNIFICANT ENRICHMENTS (FDR ≤ 0.25): {len(significant_results)} total")
        print()
        
        for gene_set in significant_results['Gene_Set'].unique():
            subset = significant_results[significant_results['Gene_Set'] == gene_set]
            print(f"📌 {gene_set} ({len(subset)} significant):")
            
            for _, row in subset.iterrows():
                direction = "↑" if row['NES'] > 0 else "↓"
                print(f"   {direction} {row['GSE']}: NES={row['NES']:.3f}, FDR={row['FDR_q_val']:.4f}, p={row['Nominal_p_val']:.4f}")
            print()
    
    # Results that don't meet cutoffs
    non_significant = df[~df['Overall_Significant']].copy()
    if not non_significant.empty:
        print(f"❌ NON-SIGNIFICANT ENRICHMENTS (FDR > 0.25): {len(non_significant)} total")
        print()
        
        # Show some examples of borderline cases
        borderline = non_significant[(non_significant['FDR_q_val'] > 0.25) & (non_significant['FDR_q_val'] <= 0.5)]
        if not borderline.empty:
            print(f"⚠️  BORDERLINE CASES (0.25 < FDR ≤ 0.5): {len(borderline)} cases")
            for _, row in borderline.head(10).iterrows():
                direction = "↑" if row['NES'] > 0 else "↓"
                print(f"   {direction} {row['GSE']} - {row['Gene_Set']}: NES={row['NES']:.3f}, FDR={row['FDR_q_val']:.4f}, p={row['Nominal_p_val']:.4f}")
            if len(borderline) > 10:
                print(f"   ... and {len(borderline) - 10} more")
        print()
    
    # Save detailed results
    output_file = "/mnt/work_1/gest9386/CU_Boulder/rotations/RINN/log1/gsea_analysis_results.csv"
    df.to_csv(output_file, index=False)
    print(f"💾 Detailed results saved to: {output_file}")
    
    return df

if __name__ == "__main__":
    results_df = main()
