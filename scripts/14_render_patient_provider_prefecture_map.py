"""Render a presentation-ready 2024 prefecture comparison map.

This is deliberately separate from the legacy patient and supplementary
provider figures so those outputs remain reproducible without being replaced.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from patient_geography.plots import plot_patient_provider_prefecture_map, setup_style


def build_rank_table(patient: pd.DataFrame, provider: pd.DataFrame) -> pd.DataFrame:
    """Return one 47-prefecture comparison table with both descending ranks."""
    patient_2024 = patient.loc[
        patient["year"].eq(2024),
        ["prefecture_code", "prefecture_name", "patient_online_rate_pct"],
    ].copy()
    provider_2024 = provider.loc[
        provider["fiscal_year"].eq(2024),
        ["prefecture_code", "rate_per_population"],
    ].copy()
    table = patient_2024.merge(provider_2024, on="prefecture_code", validate="one_to_one")
    table["patient_rank"] = table["patient_online_rate_pct"].rank(method="min", ascending=False).astype(int)
    table["provider_rank"] = table["rate_per_population"].rank(method="min", ascending=False).astype(int)
    table = table.rename(
        columns={
            "prefecture_code": "prefecture_code",
            "prefecture_name": "prefecture_name",
            "patient_online_rate_pct": "patient_online_rate_pct",
            "rate_per_population": "provider_rate_per_100k",
        }
    )
    return table[
        [
            "patient_rank",
            "provider_rank",
            "prefecture_code",
            "prefecture_name",
            "patient_online_rate_pct",
            "provider_rate_per_100k",
        ]
    ].sort_values(["patient_rank", "provider_rank", "prefecture_code"])


def plot_rank_table(rank_table: pd.DataFrame, output: Path) -> None:
    """Render a slide-ready image of the top and bottom five rankings."""
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}
    font = next(
        (name for name in ("Yu Gothic", "Hiragino Sans", "Noto Sans CJK JP", "IPAexGothic") if name in available_fonts),
        "DejaVu Sans",
    )
    plt.rcParams["font.family"] = font
    plt.rcParams["axes.unicode_minus"] = False

    figure, axes = plt.subplots(1, 2, figsize=(16, 6.8))
    figure.subplots_adjust(left=0.035, right=0.965, top=0.92, bottom=0.04, wspace=0.065)
    panels = [
        (axes[0], "患者側（居住地）", "patient_rank", "patient_online_rate_pct", "自己申告の利用率", "%"),
        (axes[1], "医療機関側（所在地）", "provider_rank", "provider_rate_per_100k", "人口10万人あたりNDB算定回数", "回"),
    ]
    for axis, title, rank_col, value_col, value_label, suffix in panels:
        axis.set_facecolor("#f8fafc")
        axis.set_axis_off()
        axis.text(0.5, 1.02, title, transform=axis.transAxes, ha="center", va="bottom", fontsize=20, fontweight="bold", color="#1f2937")
        axis.text(0.03, 0.94, "上位5", transform=axis.transAxes, ha="left", va="center", fontsize=16, fontweight="bold", color="#c23b22")
        axis.text(0.03, 0.46, "下位5", transform=axis.transAxes, ha="left", va="center", fontsize=16, fontweight="bold", color="#2166ac")

        top = rank_table.nsmallest(5, rank_col)
        bottom = rank_table.nlargest(5, rank_col).sort_values(rank_col)
        for subset, bbox, accent in ((top, [0.03, 0.60, 0.94, 0.29], "#e34a33"), (bottom, [0.03, 0.13, 0.94, 0.29], "#3182ce")):
            rows = [[str(int(row[rank_col])), row["prefecture_name"], f"{row[value_col]:,.1f}{suffix}"] for _, row in subset.iterrows()]
            table = axis.table(
                cellText=rows,
                colLabels=["順位", "都道府県", value_label],
                colWidths=[0.16, 0.34, 0.50],
                cellLoc="center",
                colLoc="center",
                bbox=bbox,
            )
            table.auto_set_font_size(False)
            table.set_fontsize(16)
            for (row_index, column_index), cell in table.get_celld().items():
                cell.set_edgecolor("#d1d5db")
                cell.set_linewidth(0.6)
                if row_index == 0:
                    cell.set_facecolor(accent)
                    cell.get_text().set_color("white")
                    cell.get_text().set_weight("bold")
                else:
                    cell.set_facecolor("white" if row_index % 2 else "#f1f5f9")
                    if column_index == 2:
                        cell.get_text().set_weight("bold")

    figure.savefig(output, dpi=200, facecolor="white")
    plt.close(figure)


def main() -> int:
    table_dir = ROOT / "output" / "tables"
    output = ROOT / "output" / "figures" / "patient_provider_prefecture_map_2024.png"
    patient_path = table_dir / "patient_survey_prefecture.csv"
    provider_path = table_dir / "prefecture_per_capita.csv"

    for path in (patient_path, provider_path):
        if not path.exists():
            raise FileNotFoundError(f"Required table is missing: {path}")

    patient = pd.read_csv(patient_path, dtype={"prefecture_code": str})
    provider = pd.read_csv(provider_path, dtype={"prefecture_code": str})
    output.parent.mkdir(parents=True, exist_ok=True)

    rank_table = build_rank_table(patient, provider)
    rank_output = table_dir / "patient_provider_prefecture_rank_2024.csv"
    rank_table.to_csv(rank_output, index=False, encoding="utf-8-sig", float_format="%.1f")
    rank_figure_output = ROOT / "output" / "figures" / "patient_provider_prefecture_rank_top_bottom_2024.png"

    setup_style()
    plot_patient_provider_prefecture_map(patient, provider, output)
    plot_rank_table(rank_table, rank_figure_output)
    print(f"figure: {output}")
    print(f"rank figure: {rank_figure_output}")
    print(f"rank table: {rank_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
