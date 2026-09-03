"""Build residence-prefecture patient-side maps without using NDB as demand."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from patient_geography.analysis import build_patient_location_change
from patient_geography.io import load_survey
from patient_geography.plots import (
    plot_prefecture_change_map,
    plot_prefecture_year_maps,
    setup_style,
)
from patient_geography.trends_report import write_location_trends_report


def main() -> int:
    table_dir = ROOT / "output" / "tables"
    figure_dir = ROOT / "output" / "figures"
    report_dir = ROOT / "output" / "reports"
    for directory in (table_dir, figure_dir, report_dir):
        directory.mkdir(parents=True, exist_ok=True)

    patient, _, _ = load_survey(ROOT)
    change = build_patient_location_change(patient)
    change.to_csv(table_dir / "patient_location_change_2022_2024.csv", index=False, encoding="utf-8-sig")

    setup_style()
    plot_prefecture_year_maps(
        patient,
        figure_dir / "figure18_patient_location_rate_map.png",
        title="図18　居住都道府県別・自己申告オンライン診療利用率（地図）",
    )
    plot_prefecture_change_map(
        patient,
        figure_dir / "figure19_patient_location_change_map.png",
        title="図19　居住都道府県別・自己申告オンライン診療利用率の変化（地図）",
    )
    write_location_trends_report(report_dir, patient, change)

    print(f"patient rows={len(patient)}")
    print(f"report: {report_dir / 'patient_location_trends_report.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
