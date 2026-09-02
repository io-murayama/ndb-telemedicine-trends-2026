#!/usr/bin/env bash
# Install scaffold dependencies (DESCRIPTION Imports) and run structure check.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[bootstrap] project root: ${ROOT_DIR}"
echo "[bootstrap] installing DESCRIPTION Imports (yaml) if needed..."
Rscript -e 'pkgs <- c("yaml"); for (p in pkgs) if (!requireNamespace(p, quietly = TRUE)) install.packages(p, repos = "https://cloud.r-project.org")'

echo "[bootstrap] installing analysis packages if needed..."
Rscript -e 'pkgs <- c("readxl", "ggplot2", "sf"); for (p in pkgs) if (!requireNamespace(p, quietly = TRUE)) install.packages(p, repos = "https://cloud.r-project.org")'

echo "[bootstrap] running scaffold check..."
Rscript scripts/00_check_scaffold.R
echo "[bootstrap] done."
