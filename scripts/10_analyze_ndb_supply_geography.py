"""Analyze insured online-care supply geography from NDB open data."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from ndb_supply_geography.analysis import (
    add_prefecture_context,
    capture_table,
    concentration_table,
    correlation_table,
    online_code_composition_by_area,
    outlier_table,
    pooled_prefecture,
    pooled_sma,
    repeat_share_benchmark,
    shimane_code_composition,
    shimane_context_residual,
    shimane_neighbor_comparison,
    shimane_sma_concentration,
    split_area_and_national,
)
from ndb_supply_geography.io import (
    PRIMARY_ONLINE_CODES,
    read_medical_facility_table105,
    read_ndb_geography,
    read_ndb_procedure_details,
    read_population_age3,
)
from ndb_supply_geography.plots import (
    plot_prefecture_hypotheses,
    plot_shimane_case_study,
    plot_sma_concentration,
)
from ndb_supply_geography.report import write_report

ROUNDS = {2022: "ndb09_2022", 2023: "ndb10_2023", 2024: "ndb11_2024"}


def read_all(level: str) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    pieces, national = [], []
    filename = "basic_initial_followup_prefecture.xlsx" if level == "prefecture" else "basic_initial_followup_sma.xlsx"
    for fiscal_year, folder in ROUNDS.items():
        records = read_ndb_geography(ROOT / "data" / "raw" / folder / filename, fiscal_year, level)  # type: ignore[arg-type]
        areas, total = split_area_and_national(records)
        pieces.append(areas)
        national.append(total)
    return pd.concat(pieces, ignore_index=True), national


def read_primary_code_details(level: str) -> pd.DataFrame:
    """Read the three primary online procedures separately for a geographic level."""
    pieces = []
    filename = "basic_initial_followup_prefecture.xlsx" if level == "prefecture" else "basic_initial_followup_sma.xlsx"
    for fiscal_year, folder in ROUNDS.items():
        pieces.append(
            pd.DataFrame(
                read_ndb_procedure_details(
                    ROOT / "data" / "raw" / folder / filename,
                    fiscal_year,
                    level,  # type: ignore[arg-type]
                    PRIMARY_ONLINE_CODES,
                )
            )
        )
    return pd.concat(pieces, ignore_index=True)


def main() -> int:
    table_dir = ROOT / "output" / "tables"
    figure_dir = ROOT / "output" / "figures"
    report_dir = ROOT / "output" / "reports"
    for directory in (table_dir, figure_dir, report_dir):
        directory.mkdir(parents=True, exist_ok=True)

    prefecture, national = read_all("prefecture")
    sma, _ = read_all("sma")
    prefecture_primary_code_details = read_primary_code_details("prefecture")
    sma_primary_code_details = read_primary_code_details("sma")
    population = pd.DataFrame(read_population_age3(ROOT / "data" / "raw" / "context" / "population_2021_prefecture_age3.xlsx"))
    facilities = pd.DataFrame(read_medical_facility_table105(ROOT / "data" / "raw" / "context" / "medical_facilities_2023_table105.json"))

    prefecture = add_prefecture_context(prefecture, population, facilities)
    prefecture_pooled = pooled_prefecture(prefecture)
    sma_pooled = pooled_sma(sma)
    associations = correlation_table(prefecture)
    concentration = concentration_table(sma)
    capture = capture_table(national)
    outliers = outlier_table(prefecture_pooled)
    shimane_neighbors = shimane_neighbor_comparison(prefecture)
    shimane_concentration = shimane_sma_concentration(sma)
    shimane_composition = shimane_code_composition(sma_primary_code_details)
    shimane_residual = shimane_context_residual(prefecture)
    prefecture_composition = online_code_composition_by_area(prefecture_primary_code_details)
    sma_composition = online_code_composition_by_area(sma_primary_code_details)
    repeat_share_benchmarks = pd.concat(
        [
            repeat_share_benchmark(
                sma_composition,
                sma_composition["sma_code"].eq("3203"),
                "二次医療圏（出雲）",
            ),
            repeat_share_benchmark(
                prefecture_composition,
                prefecture_composition["prefecture_code"].eq("32"),
                "都道府県（島根）",
            ),
        ],
        ignore_index=True,
    )

    prefecture.to_csv(table_dir / "ndb_provider_prefecture_year.csv", index=False, encoding="utf-8-sig")
    prefecture_pooled.to_csv(table_dir / "ndb_provider_prefecture_pooled.csv", index=False, encoding="utf-8-sig")
    sma.to_csv(table_dir / "ndb_provider_sma_year.csv", index=False, encoding="utf-8-sig")
    sma_pooled.to_csv(table_dir / "ndb_provider_sma_pooled.csv", index=False, encoding="utf-8-sig")
    associations.to_csv(table_dir / "ndb_provider_associations.csv", index=False, encoding="utf-8-sig")
    concentration.to_csv(table_dir / "ndb_provider_concentration.csv", index=False, encoding="utf-8-sig")
    capture.to_csv(table_dir / "ndb_provider_capture.csv", index=False, encoding="utf-8-sig")
    outliers.to_csv(table_dir / "ndb_provider_outliers.csv", index=False, encoding="utf-8-sig")
    sma_primary_code_details.to_csv(
        table_dir / "ndb_sma_primary_online_code_details.csv", index=False, encoding="utf-8-sig"
    )
    prefecture_primary_code_details.to_csv(
        table_dir / "ndb_prefecture_primary_online_code_details.csv", index=False, encoding="utf-8-sig"
    )
    repeat_share_benchmarks.to_csv(
        table_dir / "ndb_shimane_repeat_share_benchmarks.csv", index=False, encoding="utf-8-sig"
    )
    shimane_neighbors.to_csv(table_dir / "ndb_shimane_neighbor_comparison.csv", index=False, encoding="utf-8-sig")
    shimane_concentration.to_csv(table_dir / "ndb_shimane_sma_concentration.csv", index=False, encoding="utf-8-sig")
    shimane_composition.to_csv(table_dir / "ndb_shimane_izumo_code_composition.csv", index=False, encoding="utf-8-sig")
    shimane_residual.to_csv(table_dir / "ndb_shimane_context_residual.csv", index=False, encoding="utf-8-sig")

    plot_prefecture_hypotheses(prefecture_pooled, str(figure_dir / "figure9_ndb_prefecture_hypotheses.png"))
    plot_sma_concentration(sma, str(figure_dir / "figure10_ndb_sma_concentration.png"))
    plot_shimane_case_study(
        shimane_neighbors,
        shimane_concentration,
        shimane_composition,
        shimane_residual,
        str(figure_dir / "figure11_shimane_case_study.png"),
    )
    write_report(
        report_dir,
        capture,
        concentration,
        associations,
        prefecture_pooled,
        sma,
        shimane_neighbors,
        shimane_concentration,
        shimane_composition,
        shimane_residual,
        repeat_share_benchmarks,
    )

    print(f"prefecture rows={len(prefecture)} | sma rows={len(sma)}")
    print(f"report: {report_dir / 'ndb_supply_geography_report.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
