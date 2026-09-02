"""Standalone report for the patient residence-location trend maps."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from patient_geography.report import _markdown_to_html, _table


def _increase_table(change: pd.DataFrame) -> pd.DataFrame:
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
        table[column] = table[column].map(lambda value: f"{value:.1f}%")
    table["変化"] = table["変化"].map(lambda value: f"{value:+.1f}ポイント")
    for column in ["利用者数目安 2022", "利用者数目安 2024"]:
        table[column] = table[column].map(lambda value: f"{value:.1f}")
    table["両端10人以上"] = table["両端10人以上"].map(lambda value: "はい" if value else "いいえ")
    return table


def write_location_trends_report(
    output_dir: Path,
    patient: pd.DataFrame,
    change: pd.DataFrame,
) -> None:
    """Write a report that keeps the survey geography separate from NDB demand."""
    output_dir.mkdir(parents=True, exist_ok=True)
    high_increase = change.loc[change["increase_at_least_1_5_points"]]
    high_increase_precise = high_increase.loc[high_increase["both_endpoints_event_proxy_ge10"]]
    national = patient.groupby("year", as_index=False).agg(
        online_rate_pct=("patient_online_rate_pct", "mean"),
        # National values are separately published; this line only aids a compact
        # table label and is not used for inference.
        prefecture_count=("prefecture_code", "nunique"),
    )
    national["online_rate_pct"] = national["online_rate_pct"].map(lambda value: f"{value:.1f}%")
    national.columns = ["年", "47都道府県の単純平均", "都道府県数"]

    lines = [
        "# 患者居住地別のオンライン診療利用：2022–2024年地図",
        "",
        "## この図が示すもの・示さないもの",
        "",
        "この分析は、総務省「通信利用動向調査」の回答者の**居住都道府県**別・自己申告による「過去1年間のオンライン診療利用率」を可視化したものである。居住地の患者側地域像を補助的に示すが、NDBの患者住所地集計ではない。また、保険診療と自由診療を区別しないため、NDB保険診療の需要量や都道府県別の需給比を測るものではない。",
        "",
        "## 結果",
        "",
        "![居住都道府県別・年次利用率](../figures/figure18_patient_location_rate_map.png)",
        "",
        "![居住都道府県別・変化](../figures/figure19_patient_location_change_map.png)",
        "",
        _table(national),
        "",
        f"2022年から2024年に1.5ポイント以上上昇したのは {len(high_increase)} 県である。ただし、2022年と2024年の両端で、公表標本数×公表率による利用者数目安が10人以上なのは {len(high_increase_precise)} 県のみだった。以下の『増加』は、仮説生成のための記述であり、複雑標本設計を反映した差の検定ではない。",
        "",
        _table(_increase_table(change)),
        "",
        "2024年の調査では神奈川県が、1.9ポイント増かつ両端の利用者数目安が10人以上という条件を満たす。一方、宮城・兵庫・北海道・滋賀・和歌山・鳥取などの大きな見かけ上の増加は、2022年側の利用者数目安が10人未満であるため、都道府県順位や前年差として強く解釈しない。",
        "",
        "## 限界",
        "",
        "- 分母は過去1年間にインターネットを利用した者であり、全住民に対する利用率ではない。",
        "- 自己申告データは保険診療と自由診療を区別せず、NDBの保険請求とは対象・期間・単位が異なる。",
        "- 公表率と公表標本数から作る利用者数目安は、複雑標本の標準誤差・信頼区間ではない。小さい値の警告として用いる。",
        "- 公開された患者住所地NDB資料は全国集計であり、この調査の都道府県別結果を保険診療患者の流出入として検証することはできない。",
        "",
        "## 出典",
        "",
        "- 総務省・e-Stat：2022 [表15](https://www.e-stat.go.jp/stat-search/files?layout=dataset&stat_infid=000040057188)、2023 [表15](https://www.e-stat.go.jp/stat-search/files?layout=dataset&stat_infid=000040185454)、2024 [表15](https://www.e-stat.go.jp/stat-search/files?layout=dataset&stat_infid=000040278952)。",
        "- NDB患者住所地の全国集計・定義：厚生労働省・中医協 [情報通信機器を用いた診療の患者・医療機関住所地集計](https://www.mhlw.go.jp/content/10808000/001591982.pdf)（NDB 2024年9–11月診療分）。",
    ]
    markdown = "\n".join(lines) + "\n"
    (output_dir / "patient_location_trends_report.md").write_text(markdown, encoding="utf-8")
    body = _markdown_to_html(markdown)
    html = (
        "<html><head><meta charset='utf-8'><title>患者居住地別トレンド</title>"
        "<style>body{max-width:1050px;margin:32px auto;font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans',sans-serif;line-height:1.65}"
        "img{max-width:100%;height:auto}table{border-collapse:collapse;margin:1em 0}th,td{border:1px solid #ccc;padding:5px 8px}</style></head><body>"
        + body
        + "</body></html>"
    )
    (output_dir / "patient_location_trends_report.html").write_text(html, encoding="utf-8")
