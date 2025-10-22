#!/usr/bin/env python3
"""
Create an UpSet plot of leading-edge (CORE ENRICHMENT == Yes) genes across GEO datasets
from the concatenated GSEA results file: concatenated_gsea_results/DOXSET_RINN.tsv

Requirements:
- Sort intersections by -degree
- Filter to min_degree = 5 so it fits on slides
- Save outputs (PNG and SVG) into concatenated_gsea_results/DOXSET_RINN_upset/

Input format notes:
- The TSV contains multiple dataset blocks. Each block starts with a line like "GSE123456"
  followed by a header line with columns including 'SYMBOL' and 'CORE ENRICHMENT'.
- Rows follow with tab-separated fields (first column like row_0), and a trailing tab
  may be present, so we robustly parse columns per-block using the header.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Set

import matplotlib.pyplot as plt

try:
	from upsetplot import UpSet, from_contents
except Exception as e:  # pragma: no cover - handled at runtime
	# Defer import error to runtime with better message
	print(
		"Error: The 'upsetplot' package is required. Install it in your environment (e.g., pip install upsetplot).",
		file=sys.stderr,
	)
	raise


def parse_doxset_rinn_tsv(tsv_path: Path) -> Dict[str, Set[str]]:
	"""Parse the concatenated DOXSET_RINN.tsv and return mapping dataset -> set of leading-edge genes.

	We detect dataset blocks by lines that contain a single token starting with 'GSE'. For each block,
	we read the following header to determine column indices, then gather rows where CORE ENRICHMENT == 'Yes'.
	We extract gene symbols from the 'SYMBOL' column.
	"""

	datasets_to_genes: Dict[str, Set[str]] = {}
	current_dataset: str | None = None
	header_cols: List[str] | None = None
	symbol_idx: int | None = None
	core_idx: int | None = None

	with tsv_path.open("r", encoding="utf-8") as f:
		for raw_line in f:
			line = raw_line.rstrip("\n")

			if not line.strip():
				# Skip empty lines between blocks
				continue

			# Dataset line (single column, starts with GSE...)
			if "\t" not in line and line.strip().startswith("GSE"):
				current_dataset = line.strip()
				datasets_to_genes.setdefault(current_dataset, set())
				# Reset header tracking for new block
				header_cols = None
				symbol_idx = None
				core_idx = None
				continue

			# Header line for a block
			if header_cols is None and line.startswith("NAME\t"):
				header_cols = [c.strip() for c in line.split("\t") if c.strip()]
				# Identify required columns
				try:
					symbol_idx = header_cols.index("SYMBOL")
					core_idx = header_cols.index("CORE ENRICHMENT")
				except ValueError as e:
					raise RuntimeError(
						"Expected 'SYMBOL' and 'CORE ENRICHMENT' in header, got: " + ", ".join(header_cols)
					) from e
				continue

			# Data rows
			if current_dataset is None or header_cols is None:
				# Not within a valid block yet
				continue

			# Some lines may have trailing tabs; keep empty fields to align indices, but
			# also guard if fewer fields appear than expected.
			parts = line.split("\t")
			# Remove trailing empty fields due to trailing tabs for safer indexing length
			while parts and parts[-1] == "":
				parts.pop()

			# We expect first column to be row id (e.g., row_0). Ensure we have enough columns.
			if len(parts) < max(symbol_idx or 0, core_idx or 0) + 1:
				# Malformed line; skip gracefully
				continue

			core_val = parts[core_idx].strip()
			if core_val.lower() == "yes":
				symbol = parts[symbol_idx].strip()
				if symbol:
					datasets_to_genes[current_dataset].add(symbol)

	# Drop datasets with no genes captured (if any)
	datasets_to_genes = {k: v for k, v in datasets_to_genes.items() if v}
	if not datasets_to_genes:
		raise RuntimeError("No leading-edge genes parsed from the TSV. Check file format and path.")

	return datasets_to_genes


def make_upset_plot(datasets_to_genes: Dict[str, Set[str]], outdir: Path, min_degree: int = 5) -> List[Path]:
	"""Render and save UpSet plot (PNG and SVG) sorted by -degree with the given min_degree.

	Returns a list of output file paths written.
	"""
	outdir.mkdir(parents=True, exist_ok=True)

	contents = from_contents(datasets_to_genes)
	upset = UpSet(
		contents,
		sort_by="-degree",
		min_degree=min_degree,
		show_counts=True,
		sort_categories_by="-cardinality",
	)

	# Make a reasonably compact figure for slides
	fig = plt.figure(figsize=(12, 6), dpi=200)
	upset.plot(fig=fig)
	plt.tight_layout()

	out_files: List[Path] = []
	for ext in ("png", "svg"):
		out_path = outdir / f"DOXSET_RINN_upset_minDegree{min_degree}.{ext}"
		fig.savefig(out_path)
		out_files.append(out_path)

	plt.close(fig)
	return out_files


def main(argv: List[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Create UpSet plot for DOXSET_RINN leading-edge genes.")
	parser.add_argument(
		"--input",
		type=Path,
		default=Path("concatenated_gsea_results/DOXSET_RINN.tsv"),
		help="Path to concatenated DOXSET_RINN TSV file.",
	)
	parser.add_argument(
		"--outdir",
		type=Path,
		default=Path("concatenated_gsea_results/DOXSET_RINN_upset"),
		help="Directory to write UpSet plot outputs.",
	)
	parser.add_argument(
		"--min-degree",
		type=int,
		default=5,
		help="Minimum degree for intersections to display.",
	)

	args = parser.parse_args(argv)

	datasets_to_genes = parse_doxset_rinn_tsv(args.input)

	out_files = make_upset_plot(datasets_to_genes, args.outdir, min_degree=args.min_degree)

	print("Wrote:")
	for p in out_files:
		print(" -", p)

	return 0


if __name__ == "__main__":
	raise SystemExit(main())

