#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Uso: $0 <cases/arquivo.yaml> [run_label]" >&2
    exit 1
fi

CASE_ARG="$1"
RUN_LABEL="${2:-$(date +%Y%m%d-%H%M%S)}"

CASE_DIR="$(cd "$(dirname "${CASE_ARG}")" && pwd)"
CASE_FILE="${CASE_DIR}/$(basename "${CASE_ARG}")"
CASE_NAME="$(basename "${CASE_FILE}")"
CASE_STEM="${CASE_NAME%.*}"

"${SCRIPT_DIR}/build.sh"

OUTPUT_DIR="${REPO_ROOT}/out/${CASE_STEM}/${RUN_LABEL}"
mkdir -p "${OUTPUT_DIR}/logs"

"${REPO_ROOT}/build/waveguide_solver" \
    --case "${CASE_FILE}" \
    --output "${OUTPUT_DIR}" | tee "${OUTPUT_DIR}/logs/solver.stdout.log"

echo
echo "Execução concluída."
echo "Saída disponível em: ${OUTPUT_DIR}"
