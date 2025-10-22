#!/usr/bin/env python3
"""
Create a full (unfiltered) UpSet plot of leading-edge (CORE ENRICHMENT == Yes) genes across GEO datasets
from the concatenated GSEA results file: concatenated_gsea_results/DOXSET_RINN.tsv

Outputs a single SVG that includes the entire UpSet (no min_degree filtering), sorted by -degree.
Saves to: concatenated_gsea_results/DOXSET_RINN_upset_full/DOXSET_RINN_upset_full.svg
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Set

import matplotlib.pyplot as plt
from upsetplot import UpSet, from_contents


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


def make_upset_svg(datasets_to_genes: Dict[str, Set[str]], outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    contents = from_contents(datasets_to_genes)
    upset = UpSet(contents, sort_by="-degree", show_counts=True, sort_categories_by="-cardinality")

    # Bigger canvas since it's the full set
    fig = plt.figure(figsize=(14, 8), dpi=200)
    upset.plot(fig=fig)
    # tight_layout can warn with UpSet, but helps reduce whitespace
    try:
        plt.tight_layout()
    except Exception:
        pass

    out_path = outdir / "DOXSET_RINN_upset_full.svg"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create full (unfiltered) UpSet SVG for DOXSET_RINN.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("concatenated_gsea_results/DOXSET_RINN.tsv"),
        help="Path to concatenated DOXSET_RINN TSV file.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("concatenated_gsea_results/DOXSET_RINN_upset_full"),
        help="Directory to write the full SVG output.",
    )
    args = parser.parse_args()

    datasets_to_genes = parse_doxset_rinn_tsv(args.input)
    if not datasets_to_genes:
        raise SystemExit("No leading-edge genes found in input; nothing to plot.")

    out_path = make_upset_svg(datasets_to_genes, args.outdir)
    print("Wrote:", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
