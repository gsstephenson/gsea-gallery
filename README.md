# GSEA Rotation Workflow

Automated Gene Set Enrichment Analysis (GSEA) pipeline that was developed during the Rinn Lab rotation. The repository bundles the shell scripts, Python utilities, and gallery builders used to process ~20 GEO RNA-seq cohorts against curated doxycycline response signatures. Use this project as the canonical reference for rerunning the analysis or integrating the workflow into a dissertation chapter.

## Highlights
- Covers the full lifecycle: GCT/CLS inputs → GSEA CLI batching → enrichment plot post-processing → figure generation → GitHub Pages delivery.
- CLI wrapper automatically tests symbol, Ensembl, and Entrez chip strategies per dataset and parallelises workloads across CPU cores.
- Plot staging scripts annotate NES/FDR statistics, generate portable galleries, and ship an interactive viewer under `docs/` for easy sharing.
- Downstream utilities concatenate leading-edge tables, build UpSet intersections, and create publication-ready comparison figures.
- Includes a curated `Input_for_GSEA/` template plus environment and gallery assets needed to reproduce the rotation results.

## Repository Tour
- `run_gsea_batch.sh` — orchestrates classical GSEA runs for every `GSE*` cohort, handling chip selection, concurrency, and logging.
- `stage_enplots.sh` — normalises report file names and syncs SVG plots into `ensplot_svgs_uncompressed/` for annotation.
- `annotate_enplots.py` — injects NES, FDR q-value, and p-value callouts into each SVG enrichment plot and saves them to `annotated_enplots/`.
- `create_interactive_gallery.py` / `create_embedded_gallery.py` — build self-contained HTML galleries (interactive PNG+SVG variants) and publish them to `docs/` for GitHub Pages.
- `analyze_gsea_results.py`, `concatenate_gsea_tsvs.py`, `create_doxset_rinn_*` — summarise statistics, aggregate leading-edge tables, and produce UpSet/figure outputs used in presentations.
- `docs/` — Pages-ready site hosting the interactive gallery plus supporting assets. Point GitHub Pages at this folder to publish the results.

## Quick Start
1. Clone the repository and position yourself at the root (`log1/`).
2. Install the GSEA CLI (v4.4.0) and update `GSEA_HOME` inside `run_gsea_batch.sh` if your install lives elsewhere.
3. Create a Python environment (3.10+) and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Populate `Input_for_GSEA/` with paired `.gct` and `.cls` files per dataset and the `.gmt` gene set libraries to test.
5. Run the batch analysis:
   ```bash
   ./run_gsea_batch.sh
   ```
   Adjust `MAX_JOBS` or export `CLS_SUFFIX_OVERRIDE` as needed before launching.
6. Stage and annotate enrichment plots:
   ```bash
   ./stage_enplots.sh
   python annotate_enplots.py
   ```
7. Regenerate galleries and summary artefacts as required:
   ```bash
   python create_interactive_gallery.py
   python create_embedded_gallery.py
   python analyze_gsea_results.py
   python concatenate_gsea_tsvs.py
   python create_doxset_rinn_intersections.py
   python create_doxset_rinn_upset.py --min-degree 5
   python create_comparison_figure.py
   ```

## Workflow Overview
```
Input_for_GSEA/ (.gct + .cls + .gmt)
        │
        ├─▶ run_gsea_batch.sh (parallel CLI jobs) → GSEA_outputs/
        │        │
        │        └─▶ stage_enplots.sh → ensplot_svgs_uncompressed/
        │                 └─▶ annotate_enplots.py → annotated_enplots/
        │                          ├─▶ create_interactive_gallery.py → docs/index.html
        │                          └─▶ create_embedded_gallery.py → enrichment_plots_gallery_gsstephenson.html
        │
        └─▶ concatenate_gsea_tsvs.py / analyze_gsea_results.py → aggregated CSVs
                    └─▶ create_doxset_rinn_* / create_comparison_figure.py → figures & reports
```

## Sharing Results
- Regenerate the interactive gallery (`python create_interactive_gallery.py`) before pushing updates; this writes `docs/index.html`, which GitHub Pages can host directly.
- `enrichment_plots_gallery_gsstephenson.html` is a self-contained offline archive suitable for collaborators without web access.
- Leading-edge summaries and UpSet plots land under `concatenated_gsea_results/` and can be cited in presentations or manuscripts.

## Data Notes
- `Input_for_GSEA/` currently contains the curated doxycycline response signatures (`dox_*` GMT files) and DESeq2-normalised counts/phenotype labels used during the rotation.
- `GSEA_outputs/` retains raw CLI reports; zipped archives are included for reproducibility.
- Annotated SVGs and exported PNGs live under `annotated_enplots/` and `annotated_enplots_png/`, respectively. These assets back the galleries and figures.

## Questions
Reach out to George Stephenson (@gsstephenson) or the Rinn Lab informatics team for dataset refreshes, new gene-set additions, or integration guidance.
