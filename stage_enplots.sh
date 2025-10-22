#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${BASE_DIR}/ensplot_svgs_uncompressed"

mkdir -p "${OUTPUT_DIR}"

# Clear any existing staged plots to avoid stale or duplicate entries
find "${OUTPUT_DIR}" -type f -name '*.svg.gz' -delete

while IFS= read -r -d '' svg_path; do
	dataset_dir="$(basename "$(dirname "${svg_path}")")"
	gse="${dataset_dir%%_*}"
	rest="${dataset_dir#${gse}_}"
	analysis="${rest%%.Gsea*}"

	filename="$(basename "${svg_path}")"
	gene="${filename#enplot_}"
	gene="${gene%.svg.gz}"
	gene="${gene%_*}"

	# Construct destination filename: GSEXXXX_Analysis_GENESET_enplot.svg.gz
	dest_name="${gse}_${analysis}_${gene}_enplot.svg.gz"
	cp -f "${svg_path}" "${OUTPUT_DIR}/${dest_name}"
done < <(find "${BASE_DIR}" -maxdepth 2 -type f -name 'enplot_*.svg.gz' -print0)
