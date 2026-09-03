"""Write the facility-level Izumo concentration report."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from patient_geography.report import _markdown_to_html, _table


def _format(value: float, digits: int = 1) -> str:
    return f"{value:,.{digits}f}"


def _concentration_table(values: pd.DataFrame) -> pd.DataFrame:
    table = values[
        [
            "year",
            "reporting_facilities",
            "facilities_with_observed_online_use",
            "observed_online_patient_days",
            "top1_share_observed_pct",
            "top2_share_observed_pct",
            "facilities_with_suppressed_online_component",
        ]
    ].copy()
    table.columns = [
        "年",
        "報告施設数",
        "オンライン利用あり（観測値）",
        "患者延べ数（観測値）",
        "上位1施設シェア",
        "上位2施設シェア",
        "*等を含む施設数",
    ]
    for column in ["報告施設数", "オンライン利用あり（観測値）", "*等を含む施設数"]:
        table[column] = table[column].map(lambda value: _format(value, 0))
    table["患者延べ数（観測値）"] = table["患者延べ数（観測値）"].map(lambda value: _format(value, 0))
    for column in ["上位1施設シェア", "上位2施設シェア"]:
        table[column] = table[column].map(lambda value: _format(value) + "%" if pd.notna(value) else "—")
    return table


def _facility_table(values: pd.DataFrame) -> pd.DataFrame:
    table = values[
        [
            "facility_name",
            "municipality_name",
            "online_initial_patient_days",
            "online_repeat_patient_days",
            "online_observed_patient_days",
            "share_of_area_observed_pct",
            "cumulative_share_of_area_observed_pct",
            "any_online_component_suppressed",
        ]
    ].copy()
    table.columns = [
        "施設名",
        "市区町村",
        "オンライン初診",
        "オンライン再診",
        "合計（観測値）",
        "医療圏内シェア",
        "累積シェア",
        "*等あり",
    ]
    for column in ["オンライン初診", "オンライン再診", "合計（観測値）"]:
        table[column] = table[column].map(lambda value: _format(value, 0) if pd.notna(value) else "*")
    for column in ["医療圏内シェア", "累積シェア"]:
        table[column] = table[column].map(lambda value: _format(value) + "%")
    table["*等あり"] = table["*等あり"].map(lambda value: "あり" if value else "なし")
    return table


def _regional_table(values: pd.DataFrame) -> pd.DataFrame:
    table = values[
        [
            "prefecture_name",
            "sma_name",
            "reporting_facilities",
            "facilities_with_observed_online_use",
            "observed_online_patient_days",
            "top1_share_observed_pct",
            "top2_share_observed_pct",
            "facilities_with_suppressed_online_component",
        ]
    ].copy()
    table.columns = [
        "都道府県",
        "二次医療圏",
        "報告施設数",
        "利用あり施設（観測値）",
        "患者延べ数（観測値）",
        "上位1施設シェア",
        "上位2施設シェア",
        "*等を含む施設数",
    ]
    for column in ["報告施設数", "利用あり施設（観測値）", "*等を含む施設数"]:
        table[column] = table[column].map(lambda value: _format(value, 0))
    table["患者延べ数（観測値）"] = table["患者延べ数（観測値）"].map(lambda value: _format(value, 0))
    for column in ["上位1施設シェア", "上位2施設シェア"]:
        table[column] = table[column].map(lambda value: _format(value) + "%")
    return table


def write_report(
    output_dir: Path,
    izumo_summary: pd.DataFrame,
    izumo_top: pd.DataFrame,
    izumo_trend: pd.DataFrame,
    regional_comparison: pd.DataFrame,
    izumo_benchmark: pd.DataFrame,
    izumo_ndb_comparison: pd.DataFrame,
    izumo_ndb_benchmark: pd.DataFrame,
) -> None:
    """Create Markdown and standalone HTML reports with explicit source limits."""
    output_dir.mkdir(parents=True, exist_ok=True)
    latest = izumo_summary.loc[izumo_summary["year"] == 2024].iloc[0]
    top = izumo_top.iloc[0]
    second_share = latest["top2_share_observed_pct"]

    if izumo_benchmark.empty:
        benchmark_sentence = (
            "2024年の出雲は * 等の非数値セルを含むため、完全観測の医療圏だけに限定した全国順位には含めない。"
        )
    else:
        benchmark = izumo_benchmark.iloc[0]
        benchmark_sentence = (
            f"完全観測かつ患者延べ数100以上の全国{int(benchmark['benchmark_sma_count'])}医療圏との比較では、"
            f"上位1施設シェアは高い順{int(benchmark['top1_share_rank_desc'])}位である。"
        )

    ndb_2023 = izumo_ndb_comparison.loc[izumo_ndb_comparison["year"] == 2023].iloc[0]
    ndb_benchmark = izumo_ndb_benchmark.iloc[0]
    ndb_sentence = (
        f"2023年は、外来機能報告の観測患者延べ数 {_format(ndb_2023['observed_online_patient_days'], 0)} は、"
        f"同じ医療圏のNDB主要3項目 {_format(ndb_2023['online_primary_count'], 0)} の"
        f"{_format(ndb_2023['facility_report_to_ndb_ratio'] * 100, 2)}%にとどまった。"
        f"NDB主要3項目が100回以上で欠測のない{int(ndb_benchmark['ndb_ratio_benchmark_sma_count'])}医療圏中では、"
        f"この比率は小さい順{int(ndb_benchmark['ndb_ratio_rank_ascending'])}位である。"
    )

    lines = [
        "# 出雲の施設集中：外来機能報告による補助検証",
        "",
        "## 結論",
        "",
        (
            f"2024年の出雲二次医療圏では、オンライン外来の観測患者延べ数 {_format(latest['observed_online_patient_days'], 0)} のうち、"
            f"最大の1施設が {_format(top['online_observed_patient_days'], 0)}（{_format(latest['top1_share_observed_pct'])}%）、"
            f"上位2施設で {_format(second_share)}% を占めた。これは**外来機能報告の対象になった施設に限れば**少数施設集中である。"
        ),
        "",
        (
            "一方、2023年の同データはNDB地域集計の0.84%にしか相当しない規模であり、公開外来機能報告だけでは、"
            "NDBで見えた出雲の約9千回を「1〜2施設が担う」ことも「地域全体に広がる」ことも判定できない。"
            "むしろ、無床診療所の報告が任意であるという制度上の報告枠と、保険請求をほぼ全数捕捉するNDBとの間に大きな観測枠の差があることが、"
            "今回の定量検証で明確になった。"
        ),
        "",
        "## 何を検証したか",
        "",
        "- 厚生労働省『外来機能報告』オープンデータの2022–2024年ファイルから、各施設の年次レコード（報告月=0）を抽出した。病院・有床診療所等が主たる対象で、無床診療所は任意報告である。",
        "- 指標は「初診（情報通信機器を用いた場合）」と「再診（情報通信機器を用いた場合）」の外来患者延べ数の和。NDBの算定回数とは定義が異なるため、施設集中の有無を確かめる目的に限定した。",
        "- `*` 等の非数値セルは0へ置換せず、表の「*等を含む施設数」として別に示した。以下のシェアは数値として観測できた患者延べ数に対するシェアである。",
        "",
        "## 出雲での集中度",
        "",
        _table(_concentration_table(izumo_summary)),
        "",
        "![出雲の上位施設](../figures/figure15_izumo_facility_concentration_2024.png)",
        "",
        _table(_facility_table(izumo_top)),
        "",
        f"{benchmark_sentence} この順位は「利用率が高い」ことの順位ではなく、利用がある地域の中で少数施設へ偏る程度の比較である。",
        "",
        "## 鳥取・広島を含む地域比較",
        "",
        "出雲の極端さが規模だけなのか、施設集中も伴うのかを確認するため、島根・鳥取・広島の全二次医療圏を同じ年次・同じ外来機能報告で比較した。",
        "",
        "![中国地方3県の二次医療圏比較](../figures/figure16_chugoku_sma_facility_concentration_2024.png)",
        "",
        _table(_regional_table(regional_comparison)),
        "",
        "## 上位施設の年次推移",
        "",
        "![出雲の上位施設の推移](../figures/figure17_izumo_top_facility_trend.png)",
        "",
        "この図は2024年の上位施設を遡って描いたものであり、各年の全上位施設を網羅するものではない。施設コードを用いて年次を結んでいるが、施設統合・移転や報告範囲の変化は区別できない。",
        "",
        "## NDB地域集計との位置づけ：仮説を検証できなかった理由",
        "",
        ndb_sentence,
        "",
        "この乖離は、単位の違いだけでは説明できないほど大きい。外来機能報告の上位施設が、NDB地域集計の主要な算定主体であると推論してはならない。無床診療所が任意報告であるため、NDBの大部分が公開外来機能報告に現れない無床診療所から来ている可能性、または両制度の報告範囲・時点・計上ルールの差が考えられる。ただし、公開データだけではいずれを区別できない。",
        "",
        "したがって、今回の施設別データが与える答えは二段階である。(1) 報告対象施設内には明瞭な少数施設集中がある。(2) しかしその部分はNDBの出雲集計を説明するには小さすぎる。NDBの極端値の供給主体を確認するには、施設別NDB特別抽出で、各施設の保険請求実数・診療科・患者住所地・継続診療の別を確認する必要がある。",
        "",
        "## 限界",
        "",
        "- 外来機能報告は施設報告の患者延べ数であり、NDBのレセプト算定回数ではない。両データの差は、期間・集計単位・対象報告施設・診療区分の差を含む。特に無床診療所は任意報告である。",
        "- 外来機能報告のみから、保険診療か自由診療か、NDB地域集計に占める施設別寄与、患者の居住地・流入を判定できない。",
        "- 小さい値が `*` 等で非数値となる場合があるため、ここでの施設シェアは観測部分に対する値である。特に小規模な医療圏同士の集中度比較は慎重に扱う。",
        "- 施設名・コードの年次照合は公開コードに依存しており、組織再編等による連続性までは検証していない。",
        "",
        "## 出典",
        "",
        "- 厚生労働省 [令和6年度外来機能報告公表データ](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/open_data_00019.html)（本リポジトリ `data/raw/gairaikinouhoukoku/2022.xlsx`、`2023.xlsx`、`2024.xlsx`）。同ページに、報告対象が病床機能報告対象医療機関等と意向確認済みの無床診療所である旨が示されている。",
        "- NDB供給地集計との比較：本リポジトリ `output/tables/ndb_provider_sma_year.csv`。NDBの定義・患者住所地との区別は `output/reports/ndb_supply_geography_report.html` を参照。",
    ]
    markdown = "\n".join(lines) + "\n"
    (output_dir / "izumo_facility_concentration_report.md").write_text(markdown, encoding="utf-8")

    body = _markdown_to_html(markdown)
    html = (
        "<html><head><meta charset='utf-8'><title>出雲の施設集中</title>"
        "<style>body{max-width:1080px;margin:32px auto;font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans',sans-serif;line-height:1.65}"
        "img{max-width:100%;height:auto}code{background:#f4f4f4;padding:2px 4px}table{border-collapse:collapse;margin:1em 0;font-size:0.92em}"
        "th,td{border:1px solid #ccc;padding:5px 8px;text-align:right}th:first-child,td:first-child{text-align:left}</style></head><body>"
        + body
        + "</body></html>"
    )
    (output_dir / "izumo_facility_concentration_report.html").write_text(html, encoding="utf-8")
