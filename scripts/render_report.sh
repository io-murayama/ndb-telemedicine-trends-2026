#!/usr/bin/env bash
# Render analysis report (Quarto → HTML)
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

QUARTO="${QUARTO:-$HOME/.local/quarto/bin/quarto}"
if [[ ! -x "$QUARTO" ]]; then
  echo "Quarto not found at $QUARTO"
  echo "Install: https://quarto.org/docs/get-started/"
  exit 1
fi

mkdir -p output/reports
"$QUARTO" render reports/analysis_report.qmd --output-dir "$ROOT_DIR/output/reports"
echo "[render_report] output/reports/analysis_report.html"
