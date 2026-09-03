"""Focused summaries for residence-prefecture patient-side trends."""

from __future__ import annotations

import pandas as pd


def build_patient_location_change(patient: pd.DataFrame) -> pd.DataFrame:
    """Summarise 2022–2024 residence-prefecture changes with a precision flag."""
    rates = patient.pivot(index=["prefecture_code", "prefecture_name"], columns="year", values="patient_online_rate_pct")
    events = patient.pivot(index=["prefecture_code", "prefecture_name"], columns="year", values="estimated_events_proxy")
    output = pd.DataFrame(
        {
            "rate_2022_pct": rates[2022],
            "rate_2023_pct": rates[2023],
            "rate_2024_pct": rates[2024],
            "change_2022_2024_pct_points": rates[2024] - rates[2022],
            "event_proxy_2022": events[2022],
            "event_proxy_2024": events[2024],
        }
    ).reset_index()
    output["both_endpoints_event_proxy_ge10"] = (
        (output["event_proxy_2022"] >= 10) & (output["event_proxy_2024"] >= 10)
    )
    output["increase_at_least_1_5_points"] = output["change_2022_2024_pct_points"] >= 1.5
    output["increase_rank_desc"] = output["change_2022_2024_pct_points"].rank(
        method="min", ascending=False
    ).astype(int)
    return output.sort_values("change_2022_2024_pct_points", ascending=False).reset_index(drop=True)
