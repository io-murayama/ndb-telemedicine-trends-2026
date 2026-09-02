"""Publication-oriented figures for the patient-side geography analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib

# The analysis runs non-interactively; forcing Agg avoids macOS GUI backends.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib import font_manager
from scipy.stats import spearmanr

JAPANESE_FONTS = ["Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo", "Noto Sans CJK JP", "IPAexGothic"]


def setup_style() -> None:
    available = {font.name for font in font_manager.fontManager.ttflist}
    selected = next((font for font in JAPANESE_FONTS if font in available), "DejaVu Sans")
    plt.rcParams.update(
        {
            "font.family": selected,
            "axes.unicode_minus": False,
            "figure.dpi": 140,
            "savefig.dpi": 180,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    sns.set_theme(style="whitegrid", font=selected, rc={"axes.spines.top": False, "axes.spines.right": False})


def _save(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_prefecture_heatmap(patient: pd.DataFrame, output: Path) -> None:
    mean_rate = patient.groupby("prefecture_code")["patient_online_rate_pct"].mean().sort_values()
    order = mean_rate.index.tolist()
    names = patient.drop_duplicates("prefecture_code").set_index("prefecture_code")["prefecture_name"]
    matrix = patient.pivot(index="prefecture_code", columns="year", values="patient_online_rate_pct").loc[order]
    event_proxy = patient.pivot(index="prefecture_code", columns="year", values="estimated_events_proxy").loc[order]
    annotations = matrix.copy().astype(str)
    for row in matrix.index:
        for year in matrix.columns:
            dagger = "†" if event_proxy.loc[row, year] < 10 else ""
            annotations.loc[row, year] = f"{matrix.loc[row, year]:.1f}{dagger}"

    fig, axis = plt.subplots(figsize=(7.2, 14.5))
    sns.heatmap(
        matrix,
        cmap="YlOrRd",
        linewidths=0.4,
        linecolor="white",
        annot=annotations,
        fmt="",
        cbar_kws={"label": "オンライン診療利用率（インターネット利用者中、%）"},
        ax=axis,
    )
    axis.set_yticklabels([names[code] for code in matrix.index], rotation=0, fontsize=9)
    axis.set_xticklabels([f"{year}年" for year in matrix.columns], rotation=0)
    axis.set_xlabel("")
    axis.set_ylabel("")
    axis.set_title("図4　患者側の自己申告オンライン診療利用率：都道府県・年次別")
    fig.text(0.01, 0.002, "† 推定利用者数の目安（公表標本数×公表率）が10人未満のセル。複雑標本のため信頼区間は算出していない。", fontsize=8)
    _save(fig, output)


def plot_region_heatmap(region: pd.DataFrame, output: Path) -> None:
    matrix = region.pivot(index="region", columns="year", values="patient_online_rate_pct")
    fig, axis = plt.subplots(figsize=(7.2, 6.4))
    sns.heatmap(
        matrix,
        cmap="YlGnBu",
        linewidths=0.6,
        linecolor="white",
        annot=True,
        fmt=".1f",
        cbar_kws={"label": "オンライン診療利用率（インターネット利用者中、%）"},
        ax=axis,
    )
    axis.set_xticklabels([f"{year}年" for year in matrix.columns], rotation=0)
    axis.set_xlabel("")
    axis.set_ylabel("")
    axis.set_title("図5　患者側の自己申告オンライン診療利用率：地方別")
    _save(fig, output)


def plot_yearly_supply_scatter(comparison: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.8), sharex=True)
    for axis, year in zip(axes, sorted(comparison["year"].unique())):
        part = comparison[comparison["year"] == year].copy()
        rho, _ = spearmanr(part["patient_online_rate_pct"], part["supply_standardized_rate_pct"])
        axis.scatter(
            part["patient_online_rate_pct"],
            part["supply_standardized_rate_pct"],
            s=36,
            color="#277da1",
            alpha=0.8,
            edgecolor="white",
            linewidth=0.4,
        )
        for _, row in part.nlargest(4, "abs_rank_gap").iterrows():
            axis.annotate(row["prefecture_name"], (row["patient_online_rate_pct"], row["supply_standardized_rate_pct"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
        axis.set_yscale("log")
        axis.set_title(f"{year}年（Spearman ρ={rho:.2f}）")
        axis.set_xlabel("患者側：自己申告利用率（%）")
        axis.grid(True, which="both", alpha=0.25)
    axes[0].set_ylabel("供給側：NDB標準化割合（医療機関所在地、対数目盛、%）")
    fig.suptitle("図6　患者側の自己申告利用と医療機関所在地ベースのNDB供給指標")
    fig.text(0.5, 0.01, "単位・期間・分母が異なるため、相関は地域順位の探索的な一致度であり、利用量の直接比較ではない。", ha="center", fontsize=8)
    _save(fig, output)


def plot_quadrant(pooled: pd.DataFrame, output: Path) -> None:
    x_median = pooled["patient_online_rate_mean_pct"].median()
    y_median = pooled["supply_standardized_mean_pct"].median()
    fig, axis = plt.subplots(figsize=(8.8, 6.2))
    palette = {
        "患者側・供給側とも高い": "#d1495b",
        "患者側高・供給側低い": "#00798c",
        "患者側低い・供給側高": "#edae49",
        "患者側・供給側とも低い": "#6c757d",
    }
    for category, part in pooled.groupby("patient_supply_type"):
        axis.scatter(part["patient_online_rate_mean_pct"], part["supply_standardized_mean_pct"], label=category, color=palette[category], s=52, alpha=0.85)
    for _, row in pooled.nlargest(8, "abs_rank_gap_mean").iterrows():
        axis.annotate(row["prefecture_name"], (row["patient_online_rate_mean_pct"], row["supply_standardized_mean_pct"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
    axis.axvline(x_median, color="black", linestyle="--", linewidth=0.8)
    axis.axhline(y_median, color="black", linestyle="--", linewidth=0.8)
    axis.set_yscale("log")
    axis.set_xlabel("患者側：2022–2024年平均の自己申告利用率（%）")
    axis.set_ylabel("供給側：2022–2024年度平均のNDB標準化割合（対数目盛、%）")
    axis.set_title("図7　患者側利用と供給側集中の乖離（探索的4象限）")
    axis.legend(fontsize=8, loc="best")
    fig.text(0.5, 0.01, "高低は各指標の都道府県中央値で分類。患者流出入を直接示すものではない。", ha="center", fontsize=8)
    _save(fig, output)


def plot_internet_access_scatter(patient: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.6), sharey=True)
    for axis, year in zip(axes, sorted(patient["year"].unique())):
        part = patient[patient["year"] == year]
        rho, _ = spearmanr(part["internet_use_rate_pct"], part["patient_online_rate_pct"])
        axis.scatter(part["internet_use_rate_pct"], part["patient_online_rate_pct"], color="#5a189a", s=36, alpha=0.8)
        for _, row in part.nlargest(3, "patient_online_rate_pct").iterrows():
            axis.annotate(row["prefecture_name"], (row["internet_use_rate_pct"], row["patient_online_rate_pct"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
        axis.set_title(f"{year}年（Spearman ρ={rho:.2f}）")
        axis.set_xlabel("過去1年のインターネット利用率（%）")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("オンライン診療利用率（インターネット利用者中、%）")
    fig.suptitle("図8　デジタル接続とオンライン診療の条件付き利用")
    _save(fig, output)
