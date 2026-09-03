"""Figures for the facility-level outpatient-function-report analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Hiragino Sans", "Yu Gothic", "Noto Sans CJK JP", "DejaVu Sans"],
            "axes.unicode_minus": False,
        }
    )


def _save(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def plot_izumo_top_facilities(top: pd.DataFrame, path: Path) -> None:
    """Show the observed 2024 contribution of the largest Izumo facilities."""
    _style()
    values = top.sort_values("online_observed_patient_days")
    figure, axis = plt.subplots(figsize=(9, max(3.8, len(values) * 0.55)))
    axis.barh(values["facility_name"], values["online_observed_patient_days"], color="#6b3b8e")
    axis.set_title("出雲医療圏：報告対象施設のオンライン外来患者延べ数（2024年・観測値）", loc="left", weight="bold")
    axis.set_xlabel("オンライン外来患者延べ数（初診＋再診、観測値）")
    for row_index, (_, row) in enumerate(values.iterrows()):
        axis.text(
            row["online_observed_patient_days"],
            row_index,
            f" {row['online_observed_patient_days']:,.0f}（{row['share_of_area_observed_pct']:.1f}%）",
            va="center",
            fontsize=9,
        )
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.grid(axis="x", alpha=0.2)
    _save(figure, path)


def plot_regional_sma_concentration(
    concentration: pd.DataFrame, path: Path, year: int = 2024
) -> None:
    """Compare Izumo with all SMAs in Shimane, Tottori and Hiroshima."""
    _style()
    values = concentration.loc[
        (concentration["year"] == year)
        & (concentration["prefecture_code"].isin(["31", "32", "34"]))
        & (concentration["observed_online_patient_days"] > 0)
    ].copy()
    figure, axis = plt.subplots(figsize=(9, 6))
    colors = values["prefecture_code"].map({"31": "#4477aa", "32": "#cc6677", "34": "#228833"})
    axis.scatter(
        values["observed_online_patient_days"],
        values["top1_share_observed_pct"],
        s=60,
        c=colors,
        alpha=0.85,
    )
    for _, row in values.iterrows():
        if row["sma_name"] == "出雲" or row["observed_online_patient_days"] >= values["observed_online_patient_days"].quantile(0.75):
            axis.annotate(
                f"{row['prefecture_name']} {row['sma_name']}",
                (row["observed_online_patient_days"], row["top1_share_observed_pct"]),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=9,
            )
    axis.set_xscale("log")
    axis.set_xlabel("オンライン外来患者延べ数（観測値、対数目盛）")
    axis.set_ylabel("上位1施設のシェア（観測値）")
    axis.set_title("島根・鳥取・広島の二次医療圏：報告対象施設の規模と集中度（2024年）", loc="left", weight="bold")
    axis.grid(alpha=0.25)
    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w", label=label, markerfacecolor=color, markersize=8)
        for label, color in [("鳥取", "#4477aa"), ("島根", "#cc6677"), ("広島", "#228833")]
    ]
    axis.legend(handles=legend_handles, title="所在地", frameon=False)
    _save(figure, path)


def plot_izumo_facility_trend(trend: pd.DataFrame, path: Path) -> None:
    """Plot the annual profile for facilities that are top contributors in 2024."""
    _style()
    figure, axis = plt.subplots(figsize=(9, 5))
    for facility_name, group in trend.groupby("facility_name", sort=False):
        axis.plot(
            group["year"],
            group["online_observed_patient_days"],
            marker="o",
            linewidth=2,
            label=facility_name,
        )
    axis.set_xticks([2022, 2023, 2024])
    axis.set_xlabel("年")
    axis.set_ylabel("オンライン外来患者延べ数（観測値）")
    axis.set_title("出雲の2024年上位施設：年次推移", loc="left", weight="bold")
    axis.grid(alpha=0.25)
    axis.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
    _save(figure, path)
