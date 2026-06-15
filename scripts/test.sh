#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BUILD_DIR="${BUILD_DIR:-${REPO_ROOT}/build}"
CTEST_BIN="${CTEST_BIN:-/usr/bin/ctest}"

if [[ ! -x "${CTEST_BIN}" ]]; then
    echo "error: CTest binary not found or not executable: ${CTEST_BIN}" >&2
    exit 127
fi

cd "${REPO_ROOT}"
exec "${CTEST_BIN}" --test-dir "${BUILD_DIR}" --output-on-failure "$@"
