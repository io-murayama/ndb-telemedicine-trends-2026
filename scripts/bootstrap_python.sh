#!/usr/bin/env bash
# Create/update the repository-local Python environment.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  echo "[python] creating ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo "[python] installing requirements"
"${VENV_DIR}/bin/python" -m pip install -r "${ROOT_DIR}/requirements-dev.txt"

echo "[python] registering Jupyter kernel"
"${VENV_DIR}/bin/python" -m ipykernel install \
  --sys-prefix \
  --name public-health-analysis \
  --display-name "Python (public-health-analysis)"

echo "[python] done"
