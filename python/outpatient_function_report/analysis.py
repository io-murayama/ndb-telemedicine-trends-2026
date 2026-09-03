"""Facility concentration summaries for online outpatient patient-days."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


def attach_prefecture_names(
    facilities: pd.DataFrame, prefecture_population: pd.DataFrame
) -> pd.DataFrame:
    """Attach stable prefecture names from the project reference table."""
    names = prefecture_population[["prefecture_code", "prefecture_name"]].drop_duplicates().copy()
    names["prefecture_code"] = names["prefecture_code"].astype(str).str.zfill(2)
    return facilities.merge(names, how="left", on="prefecture_code", validate="many_to_one")


def _concentration_metrics(group: pd.DataFrame) -> pd.Series:
    values = group.loc[group["online_observed_patient_days"] > 0, "online_observed_patient_days"].sort_values(
        ascending=False
    )
    total = values.sum()
    shares = values / total if total > 0 else pd.Series(dtype=float)
    return pd.Series(
        {
            "reporting_facilities": len(group),
            "facilities_with_observed_online_use": len(values),
            "facilities_with_suppressed_online_component": int(group["any_online_component_suppressed"].sum()),
            "observed_online_patient_days": total,
            "top1_share_observed_pct": shares.iloc[0] * 100 if len(shares) >= 1 else np.nan,
            "top2_share_observed_pct": shares.iloc[:2].sum() * 100 if len(shares) >= 1 else np.nan,
            "top5_share_observed_pct": shares.iloc[:5].sum() * 100 if len(shares) >= 1 else np.nan,
            "hhi_observed": (shares.pow(2).sum() * 10_000) if len(shares) else np.nan,
        }
    )


def summarise_area_concentration(
    facilities: pd.DataFrame, area_columns: Sequence[str]
) -> pd.DataFrame:
    """Summarise observed online patient-days and facility concentration by area."""
    summary = (
        facilities.groupby(["year", *area_columns], dropna=False, observed=True)
        .apply(_concentration_metrics, include_groups=False)
        .reset_index()
    )
    return summary.sort_values(["year", "observed_online_patient_days"], ascending=[True, False]).reset_index(drop=True)


def top_facilities(
    facilities: pd.DataFrame, prefecture_code: str, sma_name: str, year: int, n: int = 10
) -> pd.DataFrame:
    """Return the facilities contributing the most observed online patient-days."""
    selected = facilities.loc[
        (facilities["year"] == year)
        & (facilities["prefecture_code"] == prefecture_code)
        & (facilities["sma_name"] == sma_name)
        & (facilities["online_observed_patient_days"] > 0)
    ].copy()
    selected = selected.sort_values("online_observed_patient_days", ascending=False).head(n)
    total = selected["online_observed_patient_days"].sum()
    all_total = facilities.loc[
        (facilities["year"] == year)
        & (facilities["prefecture_code"] == prefecture_code)
        & (facilities["sma_name"] == sma_name),
        "online_observed_patient_days",
    ].sum()
    selected["share_of_area_observed_pct"] = selected["online_observed_patient_days"] / all_total * 100
    selected["cumulative_share_of_area_observed_pct"] = selected["share_of_area_observed_pct"].cumsum()
    selected["top_n_observed_patient_days"] = total
    return selected.reset_index(drop=True)


def facility_trend(
    facilities: pd.DataFrame, facility_codes: Sequence[str]
) -> pd.DataFrame:
    """Create a facility-by-year panel for specified facilities."""
    columns = [
        "year",
        "facility_code",
        "facility_name",
        "municipality_name",
        "online_initial_patient_days",
        "online_repeat_patient_days",
        "online_observed_patient_days",
        "any_online_component_suppressed",
    ]
    return facilities.loc[facilities["facility_code"].isin(facility_codes), columns].sort_values(
        ["facility_name", "year"]
    )


def benchmark_sma_concentration(sma_summary: pd.DataFrame, year: int) -> pd.DataFrame:
    """Rank SMAs with substantial, fully observed values by their top-facility share.

    The threshold of 100 patient-days removes very small denominators whose share is
    necessarily volatile.  The output retains the threshold so it is not hidden in
    the prose.
    """
    selected = sma_summary.loc[
        (sma_summary["year"] == year)
        & (sma_summary["observed_online_patient_days"] >= 100)
        & (sma_summary["facilities_with_suppressed_online_component"] == 0)
    ].copy()
    selected["top1_share_rank_desc"] = selected["top1_share_observed_pct"].rank(
        method="min", ascending=False
    ).astype(int)
    selected["top2_share_rank_desc"] = selected["top2_share_observed_pct"].rank(
        method="min", ascending=False
    ).astype(int)
    selected["benchmark_sma_count"] = len(selected)
    selected["benchmark_min_observed_patient_days"] = 100
    return selected.sort_values("top1_share_rank_desc").reset_index(drop=True)


def prefecture_patient_day_rates(
    prefecture_summary: pd.DataFrame, prefecture_population: pd.DataFrame
) -> pd.DataFrame:
    """Calculate observed facility-report patient-days per 10,000 residents."""
    population = prefecture_population[["prefecture_code", "fiscal_year", "population"]].copy()
    population["prefecture_code"] = population["prefecture_code"].astype(str).str.zfill(2)
    population = population.rename(columns={"fiscal_year": "year"})
    output = prefecture_summary.merge(
        population, how="left", on=["year", "prefecture_code"], validate="many_to_one"
    )
    output["observed_online_patient_days_per_10k"] = (
        output["observed_online_patient_days"] / output["population"] * 10_000
    )
    return output


def compare_with_ndb_sma(sma_summary: pd.DataFrame, ndb_sma_year: pd.DataFrame) -> pd.DataFrame:
    """Join like-for-like geographies without treating patient-days as claims."""
    ndb = ndb_sma_year.loc[
        ndb_sma_year["area_type"] == "secondary_medical_area",
        ["prefecture_code", "sma_code", "area_name", "fiscal_year", "online_primary_count", "online_primary_missing_components"],
    ].copy()
    ndb["prefecture_code"] = ndb["prefecture_code"].astype(str).str.zfill(2)
    ndb["sma_code"] = ndb["sma_code"].astype(str).str.zfill(4)
    ndb = ndb.rename(columns={"fiscal_year": "year", "area_name": "ndb_sma_name"})
    joined = sma_summary.merge(
        ndb,
        how="left",
        on=["year", "prefecture_code", "sma_code"],
        validate="one_to_one",
    )
    joined["facility_report_to_ndb_ratio"] = (
        joined["observed_online_patient_days"] / joined["online_primary_count"]
    )
    return joined


def benchmark_ndb_ratio(joined: pd.DataFrame, year: int) -> pd.DataFrame:
    """Rank the observed facility-report/NDB magnitude ratio for one year.

    This is deliberately a diagnostic of incompatible published aggregates, not a
    coverage estimate: outpatient-function-report patient-days and NDB claim counts
    do not share the same reporting frame or unit.
    """
    selected = joined.loc[
        (joined["year"] == year)
        & (joined["online_primary_missing_components"] == 0)
        & (joined["online_primary_count"] >= 100)
    ].copy()
    selected["ndb_ratio_rank_ascending"] = selected["facility_report_to_ndb_ratio"].rank(
        method="min", ascending=True
    ).astype(int)
    selected["ndb_ratio_benchmark_sma_count"] = len(selected)
    selected["ndb_ratio_benchmark_min_ndb_claims"] = 100
    return selected.sort_values("ndb_ratio_rank_ascending").reset_index(drop=True)
