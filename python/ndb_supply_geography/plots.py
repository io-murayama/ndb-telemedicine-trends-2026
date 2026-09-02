"""Figures for provider-location geography."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Hiragino Sans", "Yu Gothic", "Noto Sans CJK JP", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.facecolor": "white",
        }
    )


def plot_prefecture_hypotheses(pooled: pd.DataFrame, path: str) -> None:
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), constrained_layout=True)
    specs = [
        ("share_65plus", "65歳以上人口割合（2021年）", "高齢化との関係"),
        ("clinic_per_100k", "一般診療所数（人口10万人当たり、2023年）", "診療所密度との関係"),
    ]
    for ax, (x, xlabel, title) in zip(axes, specs, strict=True):
        ax.scatter(
            pooled[x] * (100 if x == "share_65plus" else 1),
            pooled["online_per_10000_standard_base"],
            s=42,
            color="#1976a3",
            alpha=0.8,
        )
        for _, row in pooled.iterrows():
            if row["prefecture_name"] in {"東京都", "香川県", "島根県", "岡山県", "和歌山県"}:
                x_value = row[x] * (100 if x == "share_65plus" else 1)
                ax.annotate(row["prefecture_name"], (x_value, row["online_per_10000_standard_base"]), xytext=(4, 4), textcoords="offset points", fontsize=9)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("標準基本料1万回当たり\n主要オンライン算定回数（供給地）")
        ax.set_title(title)
        ax.grid(alpha=0.2)
    fig.suptitle("NDBの供給地指標と人口・一般診療所構成（2022–2024年度平均）", fontsize=15)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_sma_concentration(sma: pd.DataFrame, path: str) -> None:
    _style()
    years = sorted(sma["fiscal_year"].unique())
    fig, axes = plt.subplots(1, len(years), figsize=(16, 7), sharex=False, constrained_layout=True)
    for ax, fiscal_year in zip(axes, years, strict=True):
        top = sma.loc[sma["fiscal_year"].eq(fiscal_year)].nlargest(15, "online_primary_count").iloc[::-1]
        labels = [f"{code} {name}" for code, name in zip(top["sma_code"], top["area_name"], strict=True)]
        ax.barh(labels, top["online_primary_count"], color="#d95f02")
        total = sma.loc[sma["fiscal_year"].eq(fiscal_year), "online_primary_count"].sum()
        share = top.tail(5)["online_primary_count"].sum() / total * 100
        ax.set_title(f"{fiscal_year}年度\n上位5圏で {share:.1f}%")
        ax.set_xlabel("主要オンライン算定回数（医療機関所在地）")
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle("二次医療圏別の主要オンライン診療算定の集中", fontsize=15)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_shimane_case_study(
    neighbors: pd.DataFrame,
    concentration: pd.DataFrame,
    composition: pd.DataFrame,
    residual: pd.DataFrame,
    path: str,
) -> None:
    """Visualize the tests that distinguish the Shimane outlier mechanisms."""
    _style()
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
    years = [2022, 2023, 2024]

    ax = axes[0, 0]
    for name, frame in neighbors.groupby("prefecture_name"):
        frame = frame.sort_values("fiscal_year")
        ax.plot(
            frame["fiscal_year"],
            frame["online_per_10000_standard_base"],
            marker="o",
            linewidth=2.8 if name == "島根県" else 1.7,
            label=name,
        )
    ax.set_xticks(years)
    ax.set_ylabel("標準基本料1万回当たり主要オンライン算定回数")
    ax.set_title("A. 隣県比較：島根だけが2023年度に跳ね上がる")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False, ncols=2)

    ax = axes[0, 1]
    concentration = concentration.sort_values("fiscal_year")
    ax.plot(
        concentration["fiscal_year"],
        concentration["izumo_online_per_10000_standard_base"],
        marker="o",
        linewidth=2.8,
        color="#d95f02",
        label="出雲圏域",
    )
    ax.plot(
        concentration["fiscal_year"],
        concentration["rest_of_shimane_online_per_10000_standard_base"],
        marker="o",
        linewidth=2,
        color="#4c78a8",
        label="出雲以外の島根",
    )
    ax.set_xticks(years)
    ax.set_ylabel("標準基本料1万回当たり主要オンライン算定回数")
    ax.set_title("B. 県全体ではなく出雲圏域への集中")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False)

    ax = axes[1, 0]
    composition = composition.sort_values("fiscal_year")
    ax.bar(
        composition["fiscal_year"],
        composition["initial_observed"],
        width=0.65,
        color="#72b7b2",
        label="オンライン初診（観測値）",
    )
    ax.bar(
        composition["fiscal_year"],
        composition["repeat_observed"],
        bottom=composition["initial_observed"],
        width=0.65,
        color="#e45756",
        label="オンライン再診等（観測値）",
    )
    ax.set_xticks(years)
    ax.set_ylabel("出雲圏域の主要オンライン算定回数")
    ax.set_title("C. 出雲の高い算定量の大半は再診等（構成比は特異でない）")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", alpha=0.2)

    ax = axes[1, 1]
    residual = residual.loc[residual["specification"].eq("島根以外の46都道府県")].sort_values("fiscal_year")
    ax.plot(
        residual["fiscal_year"],
        residual["observed_online_per_10000_standard_base"],
        marker="o",
        linewidth=2.8,
        color="#d95f02",
        label="島根の観測値",
    )
    ax.plot(
        residual["fiscal_year"],
        residual["predicted_online_per_10000_standard_base"],
        marker="o",
        linewidth=2,
        color="#4c78a8",
        label="年齢・診療所密度・人口規模からの予測",
    )
    ax.fill_between(
        residual["fiscal_year"],
        residual["bootstrap_predicted_p2_5"],
        residual["bootstrap_predicted_p97_5"],
        color="#4c78a8",
        alpha=0.16,
        label="予測の95%安定区間",
    )
    ax.set_xticks(years)
    ax.set_ylabel("標準基本料1万回当たり主要オンライン算定回数")
    ax.set_title("D. 測定可能な県特性だけでは説明できない残差")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False, fontsize=8)

    fig.suptitle("島根の外れ値を分解する：隣県・圏域・算定類型・測定可能な県特性", fontsize=15)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
