#!/usr/bin/env bash
# Install scaffold dependencies (DESCRIPTION Imports) and run structure check.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[bootstrap] project root: ${ROOT_DIR}"
echo "[bootstrap] installing DESCRIPTION Imports (yaml) if needed..."
Rscript -e 'if (!requireNamespace("yaml", quietly = TRUE)) install.packages("yaml", repos = "https://cloud.r-project.org")'

echo "[bootstrap] running scaffold check..."
Rscript scripts/00_check_scaffold.R
echo "[bootstrap] done."
