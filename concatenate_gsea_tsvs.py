#!/usr/bin/env python3
"""
Script to concatenate GSEA TSV files from different conditions into 4 output files.
"""

import os
import glob
from pathlib import Path

# Define base directory
BASE_DIR = Path("/mnt/work_1/gest9386/CU_Boulder/rotations/RINN/log1")
OUTPUT_DIR = BASE_DIR / "concatenated_gsea_results"

# Define the mapping of output files to their source patterns
FILE_MAPPINGS = {
    "DOXSET_RINN.tsv": {
        "folder_pattern": "*_DOXSET_RINN.Gsea.*",
        "file_name": "DOX_UP+DOWN_GENES.tsv"
    },
    "Public_DOXSET.tsv": {
        "folder_pattern": "*_DOXSET_1.Gsea.*",
        "file_name": "DOX_GENES.tsv"
    },
    "Upregulated_DOXSET.tsv": {
        "folder_pattern": "*_Upregulated.Gsea.*",
        "file_name": "UP_GENES.tsv"
    },
    "Downregulated_DOXSET.tsv": {
        "folder_pattern": "*_Downregulated.Gsea.*",
        "file_name": "DOWN_GENES.tsv"
    }
}

def concatenate_tsv_files(output_filename, folder_pattern, file_name):
    """
    Concatenate TSV files from matching folders into a single output file.
    
    Args:
        output_filename: Name of the output file
        folder_pattern: Pattern to match GSEA folders
        file_name: Name of the TSV file to look for in each folder
    """
    output_path = OUTPUT_DIR / output_filename
    
    # Find all matching folders
    folders = sorted(glob.glob(str(BASE_DIR / folder_pattern)))
    
    print(f"\nProcessing {output_filename}:")
    print(f"  Found {len(folders)} folders matching pattern '{folder_pattern}'")
    
    if not folders:
        print(f"  WARNING: No folders found!")
        return
    
    with open(output_path, 'w') as outfile:
        files_processed = 0
        
        for folder in folders:
            folder_path = Path(folder)
            tsv_file = folder_path / file_name
            
            if tsv_file.exists():
                # Extract GSE accession number from folder name (e.g., GSE100132)
                folder_name = folder_path.name
                gse_accession = folder_name.split('_')[0]
                
                print(f"  - Adding: {folder_path.name}/{file_name}")
                
                # Add separator row with GSE accession before each file
                if files_processed > 0:
                    # Add blank line before GSE accession (except for the first file)
                    outfile.write("\n")
                
                # Write GSE accession number
                outfile.write(f"{gse_accession}\n")
                
                # Read and write the TSV content
                with open(tsv_file, 'r') as infile:
                    content = infile.read()
                    outfile.write(content)
                    # Ensure file ends with newline
                    if not content.endswith('\n'):
                        outfile.write('\n')
                
                files_processed += 1
            else:
                print(f"  - WARNING: File not found in {folder_path.name}")
        
        print(f"  Successfully concatenated {files_processed} files into {output_filename}")

def main():
    """Main execution function."""
    print(f"Starting TSV concatenation process...")
    print(f"Base directory: {BASE_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Process each output file
    for output_file, config in FILE_MAPPINGS.items():
        concatenate_tsv_files(
            output_file,
            config["folder_pattern"],
            config["file_name"]
        )
    
    print("\n" + "="*60)
    print("Concatenation complete!")
    print(f"Output files created in: {OUTPUT_DIR}")
    print("="*60)

if __name__ == "__main__":
    main()
