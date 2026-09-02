"""Test Izumo's facility concentration using annual outpatient-function reports."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from outpatient_function_report.analysis import (
    attach_prefecture_names,
    benchmark_ndb_ratio,
    benchmark_sma_concentration,
    compare_with_ndb_sma,
    facility_trend,
    prefecture_patient_day_rates,
    summarise_area_concentration,
    top_facilities,
)
from outpatient_function_report.io import read_all_annual_online_outpatient_facilities
from outpatient_function_report.plots import (
    plot_izumo_facility_trend,
    plot_izumo_top_facilities,
    plot_regional_sma_concentration,
)
from outpatient_function_report.report import write_report


def main() -> int:
    table_dir = ROOT / "output" / "tables"
    figure_dir = ROOT / "output" / "figures"
    report_dir = ROOT / "output" / "reports"
    for directory in (table_dir, figure_dir, report_dir):
        directory.mkdir(parents=True, exist_ok=True)

    facilities = read_all_annual_online_outpatient_facilities(ROOT / "data" / "raw" / "gairaikinouhoukoku")
    population = pd.read_csv(ROOT / "data" / "reference" / "prefecture_population.csv")
    facilities = attach_prefecture_names(facilities, population)

    sma_summary = summarise_area_concentration(
        facilities, ["prefecture_code", "prefecture_name", "sma_code", "sma_name"]
    )
    prefecture_summary = summarise_area_concentration(facilities, ["prefecture_code", "prefecture_name"])
    prefecture_summary = prefecture_patient_day_rates(prefecture_summary, population)
    benchmark_2024 = benchmark_sma_concentration(sma_summary, 2024)

    izumo_summary = sma_summary.loc[
        (sma_summary["prefecture_code"] == "32") & (sma_summary["sma_code"] == "3203")
    ].sort_values("year")
    izumo_top = top_facilities(facilities, "32", "出雲", 2024, n=10)
    izumo_trend = facility_trend(facilities, izumo_top["facility_code"].tolist())
    regional_comparison = sma_summary.loc[
        (sma_summary["year"] == 2024)
        & (sma_summary["prefecture_code"].isin(["31", "32", "34"]))
        & (sma_summary["observed_online_patient_days"] > 0)
    ].sort_values(["prefecture_code", "observed_online_patient_days"], ascending=[True, False])
    izumo_benchmark = benchmark_2024.loc[
        (benchmark_2024["prefecture_code"] == "32") & (benchmark_2024["sma_code"] == "3203")
    ]

    ndb_sma = pd.read_csv(ROOT / "output" / "tables" / "ndb_provider_sma_year.csv")
    ndb_comparison = compare_with_ndb_sma(sma_summary, ndb_sma)
    ndb_ratio_benchmark_2023 = benchmark_ndb_ratio(ndb_comparison, 2023)
    izumo_ndb_comparison = ndb_comparison.loc[
        (ndb_comparison["prefecture_code"] == "32") & (ndb_comparison["sma_code"] == "3203")
    ].sort_values("year")
    izumo_ndb_benchmark = ndb_ratio_benchmark_2023.loc[
        (ndb_ratio_benchmark_2023["prefecture_code"] == "32")
        & (ndb_ratio_benchmark_2023["sma_code"] == "3203")
    ]

    facilities.to_csv(table_dir / "outpatient_function_online_facility_annual.csv", index=False, encoding="utf-8-sig")
    sma_summary.to_csv(table_dir / "outpatient_function_sma_concentration.csv", index=False, encoding="utf-8-sig")
    prefecture_summary.to_csv(
        table_dir / "outpatient_function_prefecture_concentration.csv", index=False, encoding="utf-8-sig"
    )
    benchmark_2024.to_csv(
        table_dir / "outpatient_function_sma_concentration_benchmark_2024.csv", index=False, encoding="utf-8-sig"
    )
    izumo_top.to_csv(table_dir / "outpatient_function_izumo_top_facilities_2024.csv", index=False, encoding="utf-8-sig")
    izumo_trend.to_csv(table_dir / "outpatient_function_izumo_top_facility_trend.csv", index=False, encoding="utf-8-sig")
    regional_comparison.to_csv(
        table_dir / "outpatient_function_chugoku_sma_comparison_2024.csv", index=False, encoding="utf-8-sig"
    )
    ndb_comparison.to_csv(
        table_dir / "outpatient_function_ndb_sma_comparison.csv", index=False, encoding="utf-8-sig"
    )
    ndb_ratio_benchmark_2023.to_csv(
        table_dir / "outpatient_function_ndb_ratio_benchmark_2023.csv", index=False, encoding="utf-8-sig"
    )

    plot_izumo_top_facilities(izumo_top, figure_dir / "figure15_izumo_facility_concentration_2024.png")
    plot_regional_sma_concentration(sma_summary, figure_dir / "figure16_chugoku_sma_facility_concentration_2024.png")
    plot_izumo_facility_trend(izumo_trend, figure_dir / "figure17_izumo_top_facility_trend.png")
    write_report(
        report_dir,
        izumo_summary,
        izumo_top,
        izumo_trend,
        regional_comparison,
        izumo_benchmark,
        izumo_ndb_comparison,
        izumo_ndb_benchmark,
    )

    print(f"annual facility records={len(facilities):,}")
    print(f"2024 Izumo observed patient-days={izumo_summary.iloc[-1]['observed_online_patient_days']:,.0f}")
    print(f"report: {report_dir / 'izumo_facility_concentration_report.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
