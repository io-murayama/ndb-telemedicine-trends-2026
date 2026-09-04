"""Publication-oriented figures for the patient-side geography analysis."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib

# The analysis runs non-interactively; forcing Agg avoids macOS GUI backends.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib import font_manager
from matplotlib.colors import Colormap, LinearSegmentedColormap, LogNorm, Normalize, TwoSlopeNorm
from scipy.stats import spearmanr
from shapely import affinity

JAPANESE_FONTS = ["Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo", "Noto Sans CJK JP", "IPAexGothic"]
ROOT = Path(__file__).resolve().parents[2]
PREFECTURE_GEOJSON = ROOT / "data" / "reference" / "prefectures.geojson"
JAPAN_XLIM = (122.5, 154.5)
JAPAN_YLIM = (20.0, 46.0)
PRESENTATION_BLUE_RED = LinearSegmentedColormap.from_list(
    "presentation_blue_red", ["#3182ce", "#f7f7f7", "#e34a33"]
)


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


def _save(fig: plt.Figure, path: Path, *, apply_tight_layout: bool = True) -> None:
    if apply_tight_layout and not fig.get_constrained_layout():
        fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _prefecture_geometry(values: pd.DataFrame) -> gpd.GeoDataFrame:
    """Join a prefecture-level table to the repository's fixed boundary file."""
    geo = gpd.read_file(PREFECTURE_GEOJSON)
    geo["prefecture_code"] = geo["id"].astype(int)
    values = values.copy()
    values["prefecture_code"] = values["prefecture_code"].astype(int)
    return geo.merge(values, on="prefecture_code", how="left", validate="one_to_one")


def _draw_prefecture_map(
    frame: gpd.GeoDataFrame,
    column: str,
    axis: plt.Axes,
    *,
    cmap: str | Colormap,
    norm: Normalize,
    xlim: tuple[float, float] = JAPAN_XLIM,
    ylim: tuple[float, float] = JAPAN_YLIM,
) -> None:
    frame.plot(
        column=column,
        ax=axis,
        cmap=cmap,
        norm=norm,
        linewidth=0.35,
        edgecolor="white",
        missing_kwds={"color": "#e5e7eb"},
    )
    axis.set_xlim(*xlim)
    axis.set_ylim(*ylim)
    axis.set_axis_off()


def _relocate_okinawa_to_inset(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Move Okinawa into the Japan Sea margin for a compact presentation map."""
    inset = frame.copy()
    okinawa = inset["prefecture_code"].eq(47)
    inset.loc[okinawa, "geometry"] = inset.loc[okinawa, "geometry"].apply(
        lambda geometry: affinity.translate(geometry, xoff=2.0, yoff=11.0)
    )
    return inset


def _annotate_extremes(
    frame: gpd.GeoDataFrame,
    column: str,
    axis: plt.Axes,
    *,
    n: int = 2,
    high: bool = True,
    suffix: str = "%",
) -> None:
    part = frame.dropna(subset=[column]).nlargest(n, column) if high else frame.dropna(subset=[column]).nsmallest(n, column)
    points = part.geometry.representative_point()
    for (_, row), point in zip(part.iterrows(), points):
        axis.annotate(
            f"{row['prefecture_name']}\n{row[column]:.1f}{suffix}",
            (point.x, point.y),
            ha="center",
            va="center",
            fontsize=6.5,
            fontweight="bold",
            bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.72},
        )


def plot_prefecture_year_maps(
    patient: pd.DataFrame,
    output: Path,
    title: str = "図4　患者居住地別・自己申告オンライン診療利用率（地図）",
) -> None:
    """Map self-reported residence-prefecture rates for all three survey years."""
    vmax = float(patient["patient_online_rate_pct"].max())
    norm = Normalize(vmin=0, vmax=vmax)
    figure, axes = plt.subplots(1, 3, figsize=(16.5, 7.2), layout="constrained")
    for axis, year in zip(axes, sorted(patient["year"].unique())):
        values = patient.loc[patient["year"] == year, ["prefecture_code", "prefecture_name", "patient_online_rate_pct"]]
        frame = _prefecture_geometry(values)
        _draw_prefecture_map(frame, "patient_online_rate_pct", axis, cmap="YlOrRd", norm=norm)
        _annotate_extremes(frame, "patient_online_rate_pct", axis)
        axis.set_title(f"{year}年", fontweight="bold")
    colorbar = figure.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap="YlOrRd"),
        ax=axes,
        shrink=0.65,
        pad=0.02,
    )
    colorbar.set_label("自己申告のオンライン診療利用率（インターネット利用者中、%）")
    figure.suptitle(title, fontweight="bold")
    figure.text(
        0.5,
        0.02,
        "回答者の居住都道府県。保険／自由診療を区別しない自己申告であり、NDB患者住所地集計ではない。",
        ha="center",
        fontsize=8,
    )
    _save(figure, output)


def plot_prefecture_change_map(
    patient: pd.DataFrame,
    output: Path,
    title: str = "図18　患者居住地別・自己申告オンライン診療利用率の変化（地図）",
) -> None:
    """Map the 2022–2024 change; it remains an exploratory precision-limited view."""
    rates = patient.pivot(index=["prefecture_code", "prefecture_name"], columns="year", values="patient_online_rate_pct")
    change = (rates[2024] - rates[2022]).rename("change_pct_points").reset_index()
    max_abs = float(change["change_pct_points"].abs().max())
    norm = TwoSlopeNorm(vmin=-max_abs, vcenter=0, vmax=max_abs)
    frame = _prefecture_geometry(change)
    figure, axis = plt.subplots(figsize=(7.8, 8.8), layout="constrained")
    _draw_prefecture_map(frame, "change_pct_points", axis, cmap="RdBu_r", norm=norm)
    _annotate_extremes(frame, "change_pct_points", axis, high=True, suffix="pt")
    _annotate_extremes(frame, "change_pct_points", axis, high=False, suffix="pt")
    colorbar = figure.colorbar(plt.cm.ScalarMappable(norm=norm, cmap="RdBu_r"), ax=axis, shrink=0.72, pad=0.02)
    colorbar.set_label("利用率の変化（2022年→2024年、ポイント）")
    axis.set_title(title, fontweight="bold")
    figure.text(
        0.5,
        0.02,
        "都道府県別の見かけの変化。小さい公表標本セルが多いため、差の検定結果ではない。",
        ha="center",
        fontsize=8,
    )
    _save(figure, output)


def plot_patient_provider_prefecture_map(
    patient: pd.DataFrame,
    provider: pd.DataFrame,
    output: Path,
) -> None:
    """Compare 2024 patient-residence and provider-location distributions.

    The two panels intentionally share a sequential blue palette and map extent,
    while retaining indicator-specific colour scales: the patient survey is a
    percentage and the NDB per-capita rate has a large right tail.
    """
    patient_2024 = patient.loc[
        patient["year"].eq(2024),
        ["prefecture_code", "prefecture_name", "patient_online_rate_pct"],
    ].copy()
    provider_2024 = provider.loc[
        provider["fiscal_year"].eq(2024),
        ["prefecture_code", "prefecture_name", "rate_per_population"],
    ].copy()
    if len(patient_2024) != 47 or len(provider_2024) != 47:
        raise ValueError("2024年の患者側・医療機関側データは各47都道府県必要です")
    if patient_2024["prefecture_code"].nunique() != 47 or provider_2024["prefecture_code"].nunique() != 47:
        raise ValueError("2024年の都道府県コードに重複があります")
    if (provider_2024["rate_per_population"] <= 0).any():
        raise ValueError("医療機関側の人口あたり算定回数は正の値である必要があります")

    patient_frame = _relocate_okinawa_to_inset(_prefecture_geometry(patient_2024))
    provider_frame = _relocate_okinawa_to_inset(_prefecture_geometry(provider_2024))
    patient_norm = Normalize(vmin=0, vmax=float(patient_2024["patient_online_rate_pct"].max()))
    provider_norm = LogNorm(
        vmin=float(provider_2024["rate_per_population"].min()),
        vmax=float(provider_2024["rate_per_population"].max()),
    )

    figure = plt.figure(figsize=(15.8, 6.8))
    grid = figure.add_gridspec(
        2,
        4,
        height_ratios=(1, 0.035),
        width_ratios=(0.055, 1, 1, 0.055),
        wspace=0.02,
        hspace=0.04,
        left=0.065,
        right=0.935,
        top=0.96,
        bottom=0.07,
    )
    axes = [figure.add_subplot(grid[0, 1]), figure.add_subplot(grid[0, 2])]
    left_colorbar_grid = grid[0, 0].subgridspec(3, 1, height_ratios=(0.12, 0.76, 0.12))
    right_colorbar_grid = grid[0, 3].subgridspec(3, 1, height_ratios=(0.12, 0.76, 0.12))
    colorbar_axes = [
        figure.add_subplot(left_colorbar_grid[1]),
        figure.add_subplot(right_colorbar_grid[1]),
    ]
    source_axis = figure.add_subplot(grid[1, :])
    source_axis.set_axis_off()
    panels = [
        (
            patient_frame,
            "patient_online_rate_pct",
            "患者側（居住地）",
            "自己申告のオンライン診療利用率（%）",
            patient_norm,
        ),
        (
            provider_frame,
            "rate_per_population",
            "医療機関側（所在地）",
            "人口10万人あたりNDB算定回数（対数目盛）",
            provider_norm,
        ),
    ]
    for axis, colorbar_axis, (frame, column, title, label, norm) in zip(
        axes, colorbar_axes, panels, strict=True
    ):
        _draw_prefecture_map(
            frame,
            column,
            axis,
            cmap=PRESENTATION_BLUE_RED,
            norm=norm,
            xlim=(124.6, 150.0),
            ylim=(30.0, 46.0),
        )
        axis.set_title(title, fontweight="bold", pad=9)
        colorbar = figure.colorbar(
            plt.cm.ScalarMappable(norm=norm, cmap=PRESENTATION_BLUE_RED),
            cax=colorbar_axis,
            orientation="vertical",
        )
        colorbar.set_label(label, fontsize=9)
        colorbar.ax.tick_params(labelsize=8)

    colorbar_axes[0].yaxis.set_ticks_position("left")
    colorbar_axes[0].yaxis.set_label_position("left")

    source_axis.text(
        0.5,
        0.5,
        "患者側：通信利用動向調査（2024年、インターネット利用者の自己申告）"
        "　｜　医療機関側：NDBオープンデータ（2024年度、ICT関連算定の医療機関所在地）",
        ha="center",
        va="center",
        fontsize=7,
        color="#374151",
    )
    _save(figure, output, apply_tight_layout=False)


def plot_patient_supply_rank_maps(
    pooled: pd.DataFrame,
    output: Path,
    title: str = "図20　患者居住地と医療機関所在地でみた地域分布の比較（地図）",
) -> None:
    """Compare patient and provider geography on a common within-prefecture rank scale."""
    values = pooled[
        [
            "prefecture_code",
            "prefecture_name",
            "patient_mean_rank",
            "supply_mean_rank",
            "rank_gap_mean",
        ]
    ].copy()
    frame = _prefecture_geometry(values)
    rank_norm = Normalize(vmin=1, vmax=len(values))
    gap = float(frame["rank_gap_mean"].abs().max())
    gap_norm = TwoSlopeNorm(vmin=-gap, vcenter=0, vmax=gap)
    figure, axes = plt.subplots(1, 3, figsize=(17.2, 7.2), layout="constrained")

    panels = [
        ("patient_mean_rank", "患者側：自己申告利用率の順位", "YlOrRd", rank_norm),
        ("supply_mean_rank", "供給側：NDB算定割合の順位", "YlOrRd", rank_norm),
        ("rank_gap_mean", "供給順位 − 患者順位", "RdBu_r", gap_norm),
    ]
    for axis, (column, panel_title, cmap, norm) in zip(axes, panels):
        _draw_prefecture_map(frame, column, axis, cmap=cmap, norm=norm)
        axis.set_title(panel_title, fontweight="bold")
    _annotate_extremes(frame, "patient_mean_rank", axes[0], suffix="位")
    _annotate_extremes(frame, "supply_mean_rank", axes[1], suffix="位")
    _annotate_extremes(frame, "rank_gap_mean", axes[2], suffix="位")
    _annotate_extremes(frame, "rank_gap_mean", axes[2], high=False, suffix="位")
    rank_colorbar = figure.colorbar(plt.cm.ScalarMappable(norm=rank_norm, cmap="YlOrRd"), ax=axes[:2], shrink=0.63, pad=0.02)
    rank_colorbar.set_label("都道府県内順位（1=低い、47=高い）")
    gap_colorbar = figure.colorbar(plt.cm.ScalarMappable(norm=gap_norm, cmap="RdBu_r"), ax=axes[2], shrink=0.63, pad=0.02)
    gap_colorbar.set_label("順位差（正=供給側が相対的に高い）")
    figure.suptitle(title, fontweight="bold")
    figure.text(
        0.5,
        0.02,
        "2022〜2024年平均。絶対値ではなく各指標内の都道府県順位を比較。患者側は保険／自由診療を区別しない。",
        ha="center",
        fontsize=8,
    )
    _save(figure, output)


def plot_region_trend(region: pd.DataFrame, output: Path) -> None:
    """Use a line chart for regions instead of a tabular color matrix."""
    figure, axis = plt.subplots(figsize=(9.6, 6.2))
    for name, part in region.groupby("region", observed=True):
        axis.plot(part["year"], part["patient_online_rate_pct"], marker="o", linewidth=1.6, label=name)
    axis.set_xticks(sorted(region["year"].unique()))
    axis.set_ylabel("自己申告のオンライン診療利用率（%）")
    axis.set_xlabel("調査年")
    axis.set_title("図5　患者側の自己申告オンライン診療利用率：地方別推移")
    axis.legend(ncol=2, fontsize=8, frameon=False)
    _save(figure, output)


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
