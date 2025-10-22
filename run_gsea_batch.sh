#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${BASE_DIR}/Input_for_GSEA"
OUTPUT_DIR="${BASE_DIR}/GSEA_outputs"
LOG_DIR="${OUTPUT_DIR}/logs"
GSEA_HOME="/opt/GSEA_Linux_4.4.0"
GSEA_CLI="${GSEA_HOME}/gsea-cli.sh"
ENSEMBL_CHIP="ftp.broadinstitute.org://pub/gsea/msigdb/human/annotations/Human_Ensembl_Gene_ID_MSigDB.v2025.1.Hs.chip"
NCBI_CHIP="ftp.broadinstitute.org://pub/gsea/msigdb/human/annotations/Human_NCBI_Gene_ID_MSigDB.v2025.1.Hs.chip"

CLS_SUFFIX_OVERRIDE="${CLS_SUFFIX_OVERRIDE:-${CLS_SUFFIX:-}}"
MAX_JOBS="${MAX_JOBS:-4}"

ANALYSES=(
	"Downregulated|dox_downl2f1.gmt"
	"Upregulated|dox_upl2f1.gmt"
	"DOXSET_1|DOX_RESPONSIVE_GENESET_1_msigdb.gmt"
	"DOXSET_RINN|Dox_Up+Down_l2f1.gmt"
)

DATASET_LIST=()
declare -A DATASET_GCT=()
declare -A DATASET_CLS=()
declare -A DATASET_SUFFIX=()
declare -A DATASET_ATTEMPTS=()
declare -A DATASET_IDTYPE=()

derive_cls_suffix() {
	local cls_path="$1"
	local line phen1 phen2

	if ! line="$(sed -n '2p' "${cls_path}" | tr -d '\r')"; then
		abort "Unable to read second line from ${cls_path}."
	fi

	line="${line#\#}"
	line="$(echo "${line}" | tr -s '[:space:]' ' ' | xargs)"

	read -r phen1 phen2 _ <<<"${line}"

	if [[ -z "${phen1:-}" || -z "${phen2:-}" ]]; then
		abort "Unable to derive phenotype labels from ${cls_path}."
	fi

	printf '#%s_versus_%s' "${phen2}" "${phen1}"
}

detect_identifier_type() {
	local gct_path="$1"
	local sample_size=200
	local ensembl_count=0
	local numeric_count=0
	local symbol_like_count=0
	local total=0
	local gene

	while IFS=$'\t' read -r gene _; do
		[[ -z "${gene:-}" || "${gene}" == "NA" ]] && continue
		((total++))

		if [[ "${gene}" =~ ^ENS[A-Z]*[0-9]+(\.[0-9]+)?$ ]]; then
			((ensembl_count++))
		elif [[ "${gene}" =~ ^[0-9]+$ ]]; then
			((numeric_count++))
		else
			((symbol_like_count++))
		fi

		(( total >= sample_size )) && break
	done < <(tail -n +4 "${gct_path}" 2>/dev/null | head -n "${sample_size}")

	(( total > 0 )) || abort "Unable to sample identifiers from ${gct_path}."

	if (( ensembl_count >= 3 && ensembl_count >= numeric_count && ensembl_count >= symbol_like_count )); then
		echo "ENSEMBL"
	elif (( numeric_count >= 3 && numeric_count > ensembl_count )); then
		echo "NCBI"
	else
		echo "SYMBOL"
	fi
}

build_attempt_list() {
	local identifier_type="$1"
	local attempts=()

	case "${identifier_type}" in
		"ENSEMBL")
			attempts=(
				"Collapse|${ENSEMBL_CHIP}|ENSEMBL"
				"Collapse|${NCBI_CHIP}|NCBI"
				"No_Collapse||NO_CHIP"
			)
			;;
		"NCBI")
			attempts=(
				"Collapse|${NCBI_CHIP}|NCBI"
				"Collapse|${ENSEMBL_CHIP}|ENSEMBL"
				"No_Collapse||NO_CHIP"
			)
			;;
		*)
			attempts=(
				"No_Collapse||NO_CHIP"
				"Collapse|${ENSEMBL_CHIP}|ENSEMBL"
				"Collapse|${NCBI_CHIP}|NCBI"
			)
			;;
	esac

	local attempt_string=""
	for attempt in "${attempts[@]}"; do
		if [[ -z "${attempt_string}" ]]; then
			attempt_string="${attempt}"
		else
			attempt_string+=";${attempt}"
		fi
	done

	printf '%s' "${attempt_string}"
}

abort() {
	echo "[ERROR] $*" >&2
	exit 1
}

check_prereqs() {
	[[ -x "${GSEA_CLI}" ]] || abort "GSEA CLI not found or not executable at ${GSEA_CLI}."
	[[ -d "${INPUT_DIR}" ]] || abort "Input directory not found at ${INPUT_DIR}."

	mkdir -p "${OUTPUT_DIR}" "${LOG_DIR}"

	for analysis in "${ANALYSES[@]}"; do
		IFS='|' read -r _label gmt_name <<<"${analysis}"
		[[ -f "${INPUT_DIR}/${gmt_name}" ]] || abort "GMT file ${gmt_name} is missing in ${INPUT_DIR}."
	done

	mapfile -t gct_files < <(find "${INPUT_DIR}" -maxdepth 1 -type f -name 'GSE*.gct' | sort)
	((${#gct_files[@]} > 0)) || abort "No GCT files found in ${INPUT_DIR}."

	for gct_path in "${gct_files[@]}"; do
		local gct_file dataset cls_candidates cls_suffix identifier_type attempts
		gct_file="$(basename "${gct_path}")"
		dataset="${gct_file%%[_\.]*}"
		cls_candidates=("${INPUT_DIR}/${dataset}"*.cls)

		if [[ ! -f "${cls_candidates[0]}" ]]; then
			abort "Missing CLS file for dataset ${dataset}."
		fi

		if [[ -n "${CLS_SUFFIX_OVERRIDE}" ]]; then
			cls_suffix="${CLS_SUFFIX_OVERRIDE}"
		else
			cls_suffix="$(derive_cls_suffix "${cls_candidates[0]}")"
		fi

		identifier_type="$(detect_identifier_type "${gct_path}")"
		attempts="$(build_attempt_list "${identifier_type}")"

		DATASET_LIST+=("${dataset}")
		DATASET_GCT["${dataset}"]="${gct_path}"
		DATASET_CLS["${dataset}"]="${cls_candidates[0]}"
		DATASET_SUFFIX["${dataset}"]="${cls_suffix}"
		DATASET_ATTEMPTS["${dataset}"]="${attempts}"
		DATASET_IDTYPE["${dataset}"]="${identifier_type}"

		printf '[%s] Prepared dataset %s (identifiers=%s)\n' "$(date --iso-8601=seconds)" "${dataset}" "${identifier_type}"
	done
}

run_analysis() {
	local dataset="$1"
	local gct_path="${DATASET_GCT[${dataset}]:-}"
	local cls_path="${DATASET_CLS[${dataset}]:-}"
	local cls_suffix="${DATASET_SUFFIX[${dataset}]:-}"
	local attempts_str="${DATASET_ATTEMPTS[${dataset}]:-}"
	local identifier_type="${DATASET_IDTYPE[${dataset}]:-}"
	local log_file="${LOG_DIR}/${dataset}.log"
	local dataset_failed=0
	local status=0

	[[ -n "${gct_path}" && -n "${cls_path}" && -n "${cls_suffix}" && -n "${attempts_str}" ]] || \
		abort "Incomplete metadata for dataset ${dataset}."

	local -a attempt_list=()
	IFS=';' read -r -a attempt_list <<<"${attempts_str}"
	(( ${#attempt_list[@]} > 0 )) || abort "No chip attempts computed for dataset ${dataset}."

	{
		printf '[%s] Starting dataset %s (identifiers=%s)\n' "$(date --iso-8601=seconds)" "${dataset}" "${identifier_type}"
		local cls_template="${cls_path}${cls_suffix}"

		for analysis in "${ANALYSES[@]}"; do
			IFS='|' read -r label gmt_name <<<"${analysis}"
			local gmt_path="${INPUT_DIR}/${gmt_name}"
			local analysis_success=0
			local attempt_index=0

			for attempt in "${attempt_list[@]}"; do
				IFS='|' read -r collapse chip chip_tag <<<"${attempt}"
				attempt_index=$((attempt_index + 1))

				printf '[%s] %s -> %s (attempt %d: collapse=%s, chip=%s)\n' \
					"$(date --iso-8601=seconds)" "${dataset}" "${label}" \
					"${attempt_index}" "${collapse}" "${chip:-none}"

				local -a cmd=(
					"${GSEA_CLI}" GSEA
					-res "${gct_path}"
					-cls "${cls_template}"
					-gmx "${gmt_path}"
					-collapse "${collapse}"
					-mode Max_probe
					-norm meandiv
					-nperm 1000
					-permute gene_set
					-rnd_seed timestamp
					-rnd_type no_balance
					-scoring_scheme weighted
					-rpt_label "${dataset}_${label}"
					-metric Signal2Noise
					-sort real
					-order descending
					-create_gcts false
					-create_svgs true
					-include_only_symbols true
					-make_sets true
					-median false
					-num 100
					-plot_top_x 20
					-save_rnd_lists true
					-set_max 500
					-set_min 15
					-zip_report false
					-out "${OUTPUT_DIR}"
				)

				if [[ -n "${chip}" ]]; then
					cmd+=( -chip "${chip}" )
				fi

				if "${cmd[@]}"; then
					printf '[%s] %s -> %s succeeded with %s (collapse=%s).\n' \
						"$(date --iso-8601=seconds)" "${dataset}" "${label}" \
						"${chip_tag}" "${collapse}"
					analysis_success=1
					break
				else
					status=$?
					printf '[%s] %s -> %s failed (status=%d) with %s (collapse=%s).\n' \
						"$(date --iso-8601=seconds)" "${dataset}" "${label}" \
						"${status}" "${chip_tag}" "${collapse}"
				fi
			done

			if (( analysis_success == 0 )); then
				printf '[%s] %s -> %s exhausted chip attempts without success.\n' \
					"$(date --iso-8601=seconds)" "${dataset}" "${label}"
				dataset_failed=1
			fi
		done

		if (( dataset_failed == 0 )); then
			printf '[%s] Completed dataset %s\n' "$(date --iso-8601=seconds)" "${dataset}"
		else
			printf '[%s] Dataset %s completed with failures.\n' "$(date --iso-8601=seconds)" "${dataset}"
		fi
	} &>"${log_file}"

	if (( dataset_failed == 0 )); then
		return 0
	else
		return 1
	fi
}

main() {
	check_prereqs

	declare -a pids=()
	declare -A pid_to_dataset=()

	for dataset in "${DATASET_LIST[@]}"; do

		while (( $(jobs -pr | wc -l) >= MAX_JOBS )); do
			sleep 1
		done

		run_analysis "${dataset}" &
		pid=$!
		pids+=("${pid}")
		pid_to_dataset["${pid}"]="${dataset}"
	done

	local failures=0

	for pid in "${pids[@]}"; do
		if wait "${pid}"; then
			printf '[%s] Dataset %s finished successfully.\n' "$(date --iso-8601=seconds)" "${pid_to_dataset[${pid}]}"
		else
			printf '[%s] Dataset %s failed. Check %s for details.\n' "$(date --iso-8601=seconds)" "${pid_to_dataset[${pid}]}" "${LOG_DIR}/${pid_to_dataset[${pid}]}.log" >&2
			((failures++))
		fi
	done

	if (( failures > 0 )); then
		abort "${failures} dataset(s) encountered errors."
	fi

	printf 'All GSEA analyses completed. Reports are in %s\n' "${OUTPUT_DIR}"
}

main "$@"
