"""Analyze patient-side geography using public communications-survey data.

Run after scripts/07_fetch_communications_survey.py. It creates tidy source
tables, exploratory comparisons with the repository's NDB supply-side table,
figures, and a report under output/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from patient_geography.io import (
    load_ndb_supply,
    load_survey,
    rank_stability,
    spearman_by_year,
)
from patient_geography.plots import (
    plot_internet_access_scatter,
    plot_prefecture_heatmap,
    plot_quadrant,
    plot_region_heatmap,
    plot_yearly_supply_scatter,
    setup_style,
)
from patient_geography.report import write_report


def build_comparison(patient: pd.DataFrame, supply: pd.DataFrame) -> pd.DataFrame:
    comparison = patient.merge(
        supply.drop(columns="prefecture_name"),
        on=["year", "prefecture_code"],
        validate="one_to_one",
    )
    for column in ("patient_online_rate_pct", "supply_standardized_rate_pct"):
        comparison[f"{column}_rank"] = comparison.groupby("year")[column].rank(method="average")
    comparison = comparison.rename(
        columns={
            "patient_online_rate_pct_rank": "patient_rank",
            "supply_standardized_rate_pct_rank": "supply_rank",
        }
    )
    comparison["rank_gap_supply_minus_patient"] = comparison["supply_rank"] - comparison["patient_rank"]
    comparison["abs_rank_gap"] = comparison["rank_gap_supply_minus_patient"].abs()
    return comparison


def build_pooled_summary(comparison: pd.DataFrame) -> pd.DataFrame:
    pooled = comparison.groupby(["prefecture_code", "prefecture_name"], as_index=False).agg(
        patient_online_rate_mean_pct=("patient_online_rate_pct", "mean"),
        patient_rate_range_pct=("patient_online_rate_pct", lambda values: values.max() - values.min()),
        internet_use_mean_pct=("internet_use_rate_pct", "mean"),
        supply_standardized_mean_pct=("supply_standardized_rate_pct", "mean"),
        rank_gap_mean=("rank_gap_supply_minus_patient", "mean"),
        low_event_proxy_years=("low_event_proxy", "sum"),
        estimated_events_proxy_min=("estimated_events_proxy", "min"),
    )
    pooled["patient_mean_rank"] = pooled["patient_online_rate_mean_pct"].rank(method="average")
    pooled["supply_mean_rank"] = pooled["supply_standardized_mean_pct"].rank(method="average")
    pooled["abs_rank_gap_mean"] = pooled["rank_gap_mean"].abs()
    patient_median = pooled["patient_online_rate_mean_pct"].median()
    supply_median = pooled["supply_standardized_mean_pct"].median()

    def category(row: pd.Series) -> str:
        patient_high = row["patient_online_rate_mean_pct"] >= patient_median
        supply_high = row["supply_standardized_mean_pct"] >= supply_median
        if patient_high and supply_high:
            return "患者側・供給側とも高い"
        if patient_high:
            return "患者側高・供給側低い"
        if supply_high:
            return "患者側低い・供給側高"
        return "患者側・供給側とも低い"

    pooled["patient_supply_type"] = pooled.apply(category, axis=1)
    return pooled.sort_values("patient_online_rate_mean_pct", ascending=False)


def main() -> int:
    table_dir = ROOT / "output" / "tables"
    figure_dir = ROOT / "output" / "figures"
    report_dir = ROOT / "output" / "reports"
    for directory in (table_dir, figure_dir, report_dir):
        directory.mkdir(parents=True, exist_ok=True)

    patient, region, national = load_survey(ROOT)
    supply = load_ndb_supply(ROOT)
    comparison = build_comparison(patient, supply)
    pooled = build_pooled_summary(comparison)

    correlations = pd.concat(
        [
            spearman_by_year(comparison, "patient_online_rate_pct", "supply_standardized_rate_pct", "患者側利用率 vs 供給側NDB標準化割合"),
            spearman_by_year(comparison, "patient_online_rate_pct", "internet_use_rate_pct", "患者側利用率 vs インターネット利用率"),
        ],
        ignore_index=True,
    )
    stability = pd.concat(
        [
            rank_stability(patient, "patient_online_rate_pct", "患者側自己申告利用率"),
            rank_stability(supply, "supply_standardized_rate_pct", "供給側NDB標準化割合"),
        ],
        ignore_index=True,
    )

    patient.to_csv(table_dir / "patient_survey_prefecture.csv", index=False, encoding="utf-8-sig")
    region.to_csv(table_dir / "patient_survey_region.csv", index=False, encoding="utf-8-sig")
    national.to_csv(table_dir / "patient_survey_national.csv", index=False, encoding="utf-8-sig")
    comparison.to_csv(table_dir / "patient_supply_comparison.csv", index=False, encoding="utf-8-sig")
    pooled.to_csv(table_dir / "patient_supply_pooled_summary.csv", index=False, encoding="utf-8-sig")
    correlations.to_csv(table_dir / "patient_geography_associations.csv", index=False, encoding="utf-8-sig")
    stability.to_csv(table_dir / "patient_geography_rank_stability.csv", index=False, encoding="utf-8-sig")

    setup_style()
    plot_prefecture_heatmap(patient, figure_dir / "figure4_patient_prefecture_heatmap.png")
    plot_region_heatmap(region, figure_dir / "figure5_patient_region_heatmap.png")
    plot_yearly_supply_scatter(comparison, figure_dir / "figure6_patient_supply_scatter.png")
    plot_quadrant(pooled, figure_dir / "figure7_patient_supply_quadrant.png")
    plot_internet_access_scatter(patient, figure_dir / "figure8_patient_internet_access.png")
    write_report(report_dir, national, region, correlations, stability, pooled, comparison)

    print(f"patient rows={patient.shape[0]}, comparison rows={comparison.shape[0]}")
    print(f"tables: {table_dir}")
    print(f"figures: {figure_dir}")
    print(f"report: {report_dir / 'patient_geography_report.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
