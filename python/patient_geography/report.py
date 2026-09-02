"""Write a compact Markdown and HTML report from the calculated geography tables."""

from __future__ import annotations

import html
import re
from pathlib import Path

import pandas as pd


def _table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(lines)


def _pct(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}%"


def _inline(markdown: str) -> str:
    escaped = html.escape(markdown)
    escaped = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', escaped)
    escaped = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)


def _markdown_to_html(markdown: str) -> str:
    """Render the small, predictable report subset without adding a dependency."""
    lines = markdown.splitlines()
    if lines[:1] == ["---"]:
        end = lines.index("---", 1)
        lines = lines[end + 1 :]
    output, paragraph = [], []

    def flush_paragraph() -> None:
        if paragraph:
            output.append("<p>" + _inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        if not line:
            flush_paragraph()
        elif line.startswith("### "):
            flush_paragraph()
            output.append("<h3>" + _inline(line[4:]) + "</h3>")
        elif line.startswith("## "):
            flush_paragraph()
            output.append("<h2>" + _inline(line[3:]) + "</h2>")
        elif line.startswith("# "):
            flush_paragraph()
            output.append("<h1>" + _inline(line[2:]) + "</h1>")
        elif line.startswith("|"):
            flush_paragraph()
            table_lines = []
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            rows = [[cell.strip() for cell in row.strip("|").split("|")] for row in table_lines]
            header, body = rows[0], rows[2:]
            output.append("<table><thead><tr>" + "".join(f"<th>{_inline(cell)}</th>" for cell in header) + "</tr></thead><tbody>")
            output.extend("<tr>" + "".join(f"<td>{_inline(cell)}</td>" for cell in row) + "</tr>" for row in body)
            output.append("</tbody></table>")
            continue
        elif line.startswith("- "):
            flush_paragraph()
            items = []
            while index < len(lines) and lines[index].startswith("- "):
                items.append(lines[index][2:])
                index += 1
            output.append("<ul>" + "".join(f"<li>{_inline(item)}</li>" for item in items) + "</ul>")
            continue
        elif re.match(r"\d+\. ", line):
            flush_paragraph()
            items = []
            while index < len(lines) and re.match(r"\d+\. ", lines[index]):
                items.append(re.sub(r"^\d+\. ", "", lines[index]))
                index += 1
            output.append("<ol>" + "".join(f"<li>{_inline(item)}</li>" for item in items) + "</ol>")
            continue
        else:
            paragraph.append(line)
        index += 1
    flush_paragraph()
    return "\n".join(output)


def _national_table(national: pd.DataFrame) -> pd.DataFrame:
    table = national[["year", "patient_sample_n", "patient_online_rate_pct", "internet_use_rate_pct"]].copy()
    table.columns = ["調査年", "表15の集計人数", "オンライン診療利用率", "インターネット利用率"]
    table["オンライン診療利用率"] = table["オンライン診療利用率"].map(_pct)
    table["インターネット利用率"] = table["インターネット利用率"].map(_pct)
    return table


def _region_table(region: pd.DataFrame) -> pd.DataFrame:
    values = region.pivot(index="region", columns="year", values="patient_online_rate_pct")
    table = pd.DataFrame({"地方": values.index, "利用率3年平均": values.mean(axis=1), "利用率2024年": values[2024]}).reset_index(drop=True)
    table = table.sort_values("利用率3年平均", ascending=False)
    table["利用率3年平均"] = table["利用率3年平均"].map(_pct)
    table["利用率2024年"] = table["利用率2024年"].map(_pct)
    return table


def _change_table(change: pd.DataFrame) -> pd.DataFrame:
    table = change.loc[change["increase_at_least_1_5_points"]].copy()
    table = table[
        [
            "prefecture_name",
            "rate_2022_pct",
            "rate_2024_pct",
            "change_2022_2024_pct_points",
            "event_proxy_2022",
            "event_proxy_2024",
            "both_endpoints_event_proxy_ge10",
        ]
    ]
    table.columns = [
        "居住都道府県",
        "2022年",
        "2024年",
        "変化",
        "利用者数目安 2022",
        "利用者数目安 2024",
        "両端10人以上",
    ]
    for column in ["2022年", "2024年"]:
        table[column] = table[column].map(_pct)
    table["変化"] = table["変化"].map(lambda value: f"{value:+.1f}ポイント")
    for column in ["利用者数目安 2022", "利用者数目安 2024"]:
        table[column] = table[column].map(lambda value: f"{value:.1f}")
    table["両端10人以上"] = table["両端10人以上"].map(lambda value: "はい" if value else "いいえ")
    return table


def write_report(
    output_dir: Path,
    national: pd.DataFrame,
    region: pd.DataFrame,
    correlations: pd.DataFrame,
    stability: pd.DataFrame,
    pooled: pd.DataFrame,
    comparison: pd.DataFrame,
    patient_location_change: pd.DataFrame,
) -> None:
    """Create a readable, self-contained report plus a Markdown source file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    patient_stability = stability.loc[stability["outcome"] == "患者側自己申告利用率", "spearman_rho"].mean()
    supply_stability = stability.loc[stability["outcome"] == "供給側NDB標準化割合", "spearman_rho"].mean()
    supply_match = correlations.loc[correlations["comparison"] == "患者側利用率 vs 供給側NDB標準化割合", "spearman_rho"].mean()
    internet_match = correlations.loc[correlations["comparison"] == "患者側利用率 vs インターネット利用率", "spearman_rho"].mean()
    low_proxy = (comparison["estimated_events_proxy"] < 10).mean() * 100
    large_increase = patient_location_change.loc[patient_location_change["increase_at_least_1_5_points"]]
    large_increase_with_both_endpoints = large_increase.loc[
        large_increase["both_endpoints_event_proxy_ge10"]
    ]

    cases = pooled.nlargest(8, "abs_rank_gap_mean")[
        [
            "prefecture_name",
            "patient_online_rate_mean_pct",
            "supply_standardized_mean_pct",
            "rank_gap_mean",
            "patient_rate_range_pct",
            "low_event_proxy_years",
            "patient_supply_type",
        ]
    ].copy()
    cases.columns = ["都道府県", "患者側利用率3年平均", "供給側NDB割合3年平均", "供給順位－患者順位", "患者側年次幅", "低精度目安年数", "探索的類型"]
    for column in ["患者側利用率3年平均", "患者側年次幅"]:
        cases[column] = cases[column].map(_pct)
    cases["供給側NDB割合3年平均"] = cases["供給側NDB割合3年平均"].map(lambda value: _pct(value, digits=3))
    cases["供給順位－患者順位"] = cases["供給順位－患者順位"].map(lambda value: f"{value:+.1f}")

    lines = [
        "---",
        'title: "通信利用動向調査を用いたオンライン診療の患者側地域分布"',
        'subtitle: "都道府県・地方別の探索的分析とNDB医療機関所在地指標との比較"',
        "date: 2026-09-02",
        "---",
        "",
        "## 結論",
        "",
        f"通信利用動向調査の「オンライン診療の利用」は、医療機関所在地ベースのNDB指標とは別の地域像を与えた。両者の都道府県順位の年平均Spearman相関は **{supply_match:.2f}** で、供給側の集中だけから自己申告利用を推測するのは難しい。公開中医協資料でも、情報通信機器を用いた初・再診料等の **51.1%** が患者と医療機関で異なる都道府県にまたがると報告されており、この解釈と整合する。表15は保険診療と自由診療を区別しないため、NDB保険診療の需要量や需給比を示す指標には使わない。",
        "",
        f"都道府県別の自己申告率には標本誤差の問題が大きい。公表された集計人数と率からの目安では、都道府県×年セルの **{low_proxy:.1f}%** が「利用者10人未満」に相当する。このため、単年ランキングを主結果にせず、3年平均・年次の再現性・地方別結果を併記した。",
        "",
        "## データと定義",
        "",
        "- 自己申告の補助指標：総務省「通信利用動向調査」世帯構成員編・表15（2022–2024年）。質問対象は**過去1年間にインターネットを利用した者**であり、過去1年にオンライン診療を利用した割合（複数回答）。人口全体の利用率ではなく、**保険診療と自由診療を区別しない**。したがってNDB保険診療の需要・需給比には用いず、一般的なデジタル利用の補助指標としてのみ扱う。",
        "- デジタル接続：同じ調査の問1「過去1年間のインターネット利用経験（対象：全員）」。",
        "- 供給側：このリポジトリに既存のNDBオープンデータ集計。都道府県は**医療機関所在地**で、年齢・性別で直接標準化した外来診療に占めるICT診療割合。",
        "- 通信利用動向調査は暦年・過去1年の自己申告、NDBは年度の算定回数であり、対応年同士の比較も探索的である。",
        "",
        "### 全国値",
        "",
        _table(_national_table(national)),
        "",
        "e-Stat表15の全国値は2022年1.8%、2023年2.5%、2024年2.5%だった。これは今回ダウンロードした公式CSVを直接読んだ値である。",
        "",
        "## 結果",
        "",
        "![居住都道府県別・年次別の自己申告利用率（地図）](../figures/figure4_patient_prefecture_map.png)",
        "",
        f"都道府県順位の年次間Spearman相関の平均は、患者側で **{patient_stability:.2f}**、供給側NDBで **{supply_stability:.2f}** だった。患者側の県別順位には偶然変動が大きいため、以下の乖離は仮説生成として扱う。",
        "",
        "### 居住都道府県別の2022→2024年変化",
        "",
        "![居住都道府県別の自己申告利用率の変化（地図）](../figures/figure18_patient_location_change_map.png)",
        "",
        f"利用率が1.5ポイント以上上昇した県は {len(large_increase)} 県だった。ただし、公表標本数×公表率による利用者数目安が2022年・2024年とも10人以上なのは {len(large_increase_with_both_endpoints)} 県のみである。したがって、地図は増加候補を探すための記述であり、各県での真の増加の検定結果ではない。",
        "",
        _table(_change_table(patient_location_change)),
        "",
        "この表・図の地域は回答者の居住都道府県である。保険診療と自由診療を分けない自己申告であり、NDBの患者住所地集計の代替ではない。",
        "",
        "![地方別患者側利用率の推移](../figures/figure5_patient_region_trend.png)",
        "",
        "### 地方別（3年平均）",
        "",
        _table(_region_table(region)),
        "",
        "![患者側と供給側の年別比較](../figures/figure6_patient_supply_scatter.png)",
        "",
        f"患者側利用率と地域のインターネット利用率の年平均Spearman相関は **{internet_match:.2f}** であり、接続率だけで患者側の条件付き利用を説明できるわけではない。",
        "",
        "![患者側と供給側の4象限](../figures/figure7_patient_supply_quadrant.png)",
        "",
        "![患者居住地と医療機関所在地でみた地域分布の比較（地図）](../figures/figure20_patient_provider_rank_maps.png)",
        "",
        "### 乖離が大きい県（3年平均の順位差）",
        "",
        _table(cases),
        "",
        "順位差が正は「患者側利用率に比べて供給側が高い」、負は「供給側に比べて患者側が高い」ことを示す。単位が違うため、ここでは大小そのものではなく県内での相対順位だけを比べた。",
        "",
        "![インターネット利用率との比較](../figures/figure8_patient_internet_access.png)",
        "",
        "## 解釈と仮説の検証",
        "",
        "この比較は保険診療の需給不均衡の判定ではない。自己申告値には自由診療も混在し得るため、ここでは地域像がどの程度異なるかを確かめる補助的な感度分析として扱う。自己申告が高くNDB供給側が低い県では、住民が県外の医療機関を利用している、あるいは自己申告とレセプト算定の対象・期間が異なる、という仮説がある。供給側が高く自己申告が低い県では、専門施設や大規模なオンライン診療提供者が域外患者を診ている可能性がある。",
        "",
        "このうち「患者所在地と医療機関所在地の乖離」という機序自体は、無料で公開されている中医協資料で検証できる。同資料はNDBの2024年9–11月診療分について、都道府県が異なる患者・医療機関の組合せが51.1%（72,659/142,174回）と報告し、東京都所在医療機関では県外患者の割合が初診68.1%、再診等65.3%と示す。したがって、NDBの医療機関所在地を患者側分布の代替として扱わない判断には直接の根拠がある。",
        "",
        "ただし、この公開資料だけでは今回の各乖離県の患者流出入を直接検証できない。個別県の結論を強めるには、次の検証が必要である。",
        "",
        "1. 公開可能な患者住所地NDB集計の都道府県別数値を取得し、同時期の供給側NDBとの流入・流出差を計算する。",
        "2. 通信利用動向調査の都道府県別推計に標準誤差または設計情報が利用できる場合、調査設計に対応した区間推定または縮約推定を行う。",
        "3. 年齢別の患者側利用率が入手できる範囲で、都道府県の年齢構成を調整し、年齢構成による差を切り分ける。",
        "",
        "## 限界",
        "",
        "- 表15の分母はインターネット利用者であり、全住民の利用率には変換していない。インターネット利用率との単純な積も推定していない。",
        "- 複雑標本・比重調整後の公表率であり、単純無作為抽出の信頼区間は不適切である。ここで示す利用者数目安は不確実性の警告であって推定標準誤差ではない。",
        "- 自己申告の利用経験、NDBの保険診療の算定回数、期間、年齢対象は異なる。相関や4象限を患者移動の直接証拠としては解釈しない。",
        "- 表15は保険診療と自由診療を区別しない。このため、本レポートの自己申告値をNDB保険診療の需要量、未充足需要、供給・需要比の分母には用いない。",
        "",
        "## 出典",
        "",
        "- 総務省・e-Stat：2022 [表15](https://www.e-stat.go.jp/stat-search/files?layout=dataset&stat_infid=000040057188)、[インターネット利用経験](https://www.e-stat.go.jp/stat-search/files?layout=dataset&stat_infid=000040057181)、2023 [表15](https://www.e-stat.go.jp/stat-search/files?layout=dataset&stat_infid=000040185454)、[インターネット利用経験](https://www.e-stat.go.jp/stat-search/files?layout=dataset&stat_infid=000040185447)、2024 [表15](https://www.e-stat.go.jp/stat-search/files?layout=dataset&stat_infid=000040278952)、[インターネット利用経験](https://www.e-stat.go.jp/stat-search/files?layout=dataset&stat_infid=000040278945)。",
        "- 厚生労働省・中医協 [情報通信機器を用いた診療の患者・医療機関住所地集計](https://www.mhlw.go.jp/content/10808000/001591982.pdf)（NDB 2024年9–11月診療分）。",
        "- 厚生労働省・中医協 [医療機関住所地と患者住所地の地域分布に関する資料](https://www.mhlw.go.jp/content/12404000/001506683.pdf)。",
        "- 供給側の作成手順と定義：このリポジトリの `reports/analysis_report.qmd`、`output/tables/prefecture_standardized.csv`。",
    ]
    markdown = "\n".join(lines) + "\n"
    (output_dir / "patient_geography_report.md").write_text(markdown, encoding="utf-8")

    body = _markdown_to_html(markdown)
    html = (
        "<html><head><meta charset='utf-8'><title>患者側地域分布</title>"
        "<style>body{max-width:1000px;margin:32px auto;font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans',sans-serif;line-height:1.65}"
        "img{max-width:100%;height:auto}code{background:#f4f4f4;padding:2px 4px}table{border-collapse:collapse;margin:1em 0}"
        "th,td{border:1px solid #ccc;padding:5px 8px}</style></head><body>"
        + body
        + "</body></html>"
    )
    (output_dir / "patient_geography_report.html").write_text(html, encoding="utf-8")
