#!/usr/bin/env python3
"""
Compute which genes are leading-edge (CORE ENRICHMENT == Yes) across the most GEO datasets
from the concatenated GSEA results file: concatenated_gsea_results/DOXSET_RINN.tsv

Outputs:
- Full sorted CSV with columns: SYMBOL, datasets_count, datasets (semicolon-separated)
- Max-only CSV containing only genes with the maximum datasets_count

Files are saved under: concatenated_gsea_results/DOXSET_RINN_intersections/
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

import csv


def parse_doxset_rinn_tsv(tsv_path: Path) -> Dict[str, Set[str]]:
    datasets_to_genes: Dict[str, Set[str]] = {}
    current_dataset: str | None = None
    header_cols: List[str] | None = None
    symbol_idx: int | None = None
    core_idx: int | None = None

    with tsv_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue
            if "\t" not in line and line.strip().startswith("GSE"):
                current_dataset = line.strip()
                datasets_to_genes.setdefault(current_dataset, set())
                header_cols = None
                symbol_idx = None
                core_idx = None
                continue
            if header_cols is None and line.startswith("NAME\t"):
                header_cols = [c.strip() for c in line.split("\t") if c.strip()]
                symbol_idx = header_cols.index("SYMBOL")
                core_idx = header_cols.index("CORE ENRICHMENT")
                continue
            if current_dataset is None or header_cols is None:
                continue
            parts = line.split("\t")
            while parts and parts[-1] == "":
                parts.pop()
            if len(parts) < max(symbol_idx or 0, core_idx or 0) + 1:
                continue
            if parts[core_idx].strip().lower() == "yes":
                symbol = parts[symbol_idx].strip()
                if symbol:
                    datasets_to_genes[current_dataset].add(symbol)

    # remove empty datasets
    return {k: v for k, v in datasets_to_genes.items() if v}


def invert_to_gene_counts(datasets_to_genes: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    gene_to_datasets: Dict[str, Set[str]] = defaultdict(set)
    for ds, genes in datasets_to_genes.items():
        for g in genes:
            gene_to_datasets[g].add(ds)
    return dict(gene_to_datasets)


def write_csvs(
    gene_to_datasets: Dict[str, Set[str]],
    outdir: Path,
) -> Tuple[Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)

    # Prepare sorted entries by count desc, then gene asc for determinism
    rows = [
        (gene, len(ds_set), sorted(ds_set))
        for gene, ds_set in gene_to_datasets.items()
    ]
    rows.sort(key=lambda x: (-x[1], x[0]))

    full_csv = outdir / "DOXSET_RINN_intersections_full.csv"
    with full_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["SYMBOL", "datasets_count", "datasets"])
        for gene, count, ds_list in rows:
            writer.writerow([gene, count, ";".join(ds_list)])

    # Max-only
    max_count = rows[0][1] if rows else 0
    max_csv = outdir / "DOXSET_RINN_intersections_max_only.csv"
    with max_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["SYMBOL", "datasets_count", "datasets"])
        for gene, count, ds_list in rows:
            if count == max_count:
                writer.writerow([gene, count, ";".join(ds_list)])

    return full_csv, max_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute genes intersecting the most datasets (leading-edge).")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("concatenated_gsea_results/DOXSET_RINN.tsv"),
        help="Path to concatenated DOXSET_RINN TSV file.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("concatenated_gsea_results/DOXSET_RINN_intersections"),
        help="Directory to write CSV outputs.",
    )
    args = parser.parse_args()

    datasets_to_genes = parse_doxset_rinn_tsv(args.input)
    if not datasets_to_genes:
        print("No leading-edge genes found in input.")
        return 1

    gene_to_datasets = invert_to_gene_counts(datasets_to_genes)
    full_csv, max_csv = write_csvs(gene_to_datasets, args.outdir)
    print("Wrote:")
    print(" -", full_csv)
    print(" -", max_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
