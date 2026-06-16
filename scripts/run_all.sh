#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SMOKE=0
SKIP_BUILD=0

usage() {
    cat <<'EOF'
Usage: bash scripts/run_all.sh [--smoke] [--skip-build]

Run the implemented reproduction sweeps:
  - Case 1: homogeneous isotropic channel
  - Case 2: planar diffused isotropic guide
  - Case 3: circular diffused isotropic channel
  - Case 4: Gaussian-Gaussian diffused channel sanity point
  - Case 5: APE LiNbO3 anisotropic sanity point
  - Case 6: Ti:LiNbO3 anisotropic sanity point

By default, outputs are written to the final reproducible folders under out/.
Use --smoke to write a reduced run under build/test_output/run_all_smoke/.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --smoke)
            SMOKE=1
            ;;
        --skip-build)
            SKIP_BUILD=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "error: unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

if [[ "${SMOKE}" -eq 1 ]]; then
    CASE1_ROOT="${REPO_ROOT}/build/test_output/run_all_smoke/case1_homogeneous_channel"
    CASE2_ROOT="${REPO_ROOT}/build/test_output/run_all_smoke/planar_diffuse_sweep"
    CASE3_ROOT="${REPO_ROOT}/build/test_output/run_all_smoke/case3_channel_diffused_isotropic"
    CASE4_ROOT="${REPO_ROOT}/build/test_output/run_all_smoke/case4_gaussian_gaussian_channel"
    CASE5_ROOT="${REPO_ROOT}/build/test_output/run_all_smoke/case5_ape_linbo3"
    CASE6_ROOT="${REPO_ROOT}/build/test_output/run_all_smoke/case6_ti_linbo3"
    SWEEP_MODE_ARGS=(--smoke)
else
    CASE1_ROOT="${REPO_ROOT}/out/case1_homogeneous_channel/final_run"
    CASE2_ROOT="${REPO_ROOT}/out/planar_diffuse_sweep/final_run"
    CASE3_ROOT="${REPO_ROOT}/out/case3_channel_diffused_isotropic/final_run"
    CASE4_ROOT="${REPO_ROOT}/out/case4_gaussian_gaussian_channel/final_point"
    CASE5_ROOT="${REPO_ROOT}/out/case5_ape_linbo3/final_point"
    CASE6_ROOT="${REPO_ROOT}/out/case6_ti_linbo3/final_point"
    SWEEP_MODE_ARGS=()
fi

cd "${REPO_ROOT}"

if [[ "${SKIP_BUILD}" -eq 0 ]]; then
    "${SCRIPT_DIR}/build.sh"
fi

echo "Running implemented reproduction sweeps"
echo "  Case 1 -> ${CASE1_ROOT}"
python3 "${SCRIPT_DIR}/run_case1_homogeneous_channel_sweep.py" \
    --skip-build \
    "${SWEEP_MODE_ARGS[@]}" \
    --output-root "${CASE1_ROOT}"

echo "  Case 2 -> ${CASE2_ROOT}"
python3 "${SCRIPT_DIR}/run_planar_diffuse_sweep.py" \
    --skip-build \
    "${SWEEP_MODE_ARGS[@]}" \
    --output-root "${CASE2_ROOT}"

echo "  Case 3 -> ${CASE3_ROOT}"
python3 "${SCRIPT_DIR}/run_case3_channel_diffused_sweep.py" \
    --skip-build \
    "${SWEEP_MODE_ARGS[@]}" \
    --output-root "${CASE3_ROOT}"

echo "  Case 4 -> ${CASE4_ROOT}"
"${REPO_ROOT}/build/waveguide_solver" \
    --case "${REPO_ROOT}/cases/case4_gaussian_gaussian_channel.yaml" \
    --output "${CASE4_ROOT}" \
    --run-label case4_gaussian_gaussian_point

echo "  Case 5 -> ${CASE5_ROOT}"
"${REPO_ROOT}/build/waveguide_solver" \
    --case "${REPO_ROOT}/cases/case5_ape_linbo3.yaml" \
    --output "${CASE5_ROOT}" \
    --run-label case5_ape_linbo3_point

echo "  Case 6 -> ${CASE6_ROOT}"
"${REPO_ROOT}/build/waveguide_solver" \
    --case "${REPO_ROOT}/cases/case6_ti_linbo3.yaml" \
    --output "${CASE6_ROOT}" \
    --run-label case6_ti_linbo3_point

echo
echo "Run phase complete."
echo "Next: python3 scripts/plot_all.py$([[ "${SMOKE}" -eq 1 ]] && echo ' --smoke')"
