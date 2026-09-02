# ndb-telemedicine-trends-2026

**2026年度公衆衛生学実習（M3）** 向けの解析リポジトリ。厚生労働省 **NDB オープンデータ** を用いて、**情報通信機器（ICT）を用いた診療**の利用動向を集計・可視化する。

- **研究デザイン**: NDB オープンデータを用いた **2022～2024 年度の全国反復横断研究**
- **データ**: NDB オープンデータ（匿名化・集計済み）
- **主アウトカム**: ICT 初診・再診・外来の利用割合（2022～2024）
- **補足**: 2019～2021 年度の旧オンライン診療料（定義が異なるため Supplementary）

詳細は [統計解析計画書（SAP）](docs/statistical-analysis-plan.md) を参照。

---

## クイックスタート

### 1. クローンと依存関係

```bash
git clone git@github.com:io-murayama/ndb-telemedicine-trends-2026.git
cd ndb-telemedicine-trends-2026
bash scripts/bootstrap.sh   # 依存パッケージ + 構成チェック
```

| 層 | パッケージ |
|----|------------|
| 必須（土台） | `yaml`（`DESCRIPTION` Imports） |
| 解析用 | `readxl`, `ggplot2`, `patchwork`（Suggests） |

R は 4.2 以降を想定。

### 2. データの配置

1. [NDB オープンデータ分析サイト](https://www.mhlw.go.jp/ndb/opendatasite/) から、対象年度の集計表をダウンロード
2. `data/raw/ndbXX_YYYY/` に配置（生ファイルは git 管理外）

### 3. 解析パイプライン

```bash
python3 scripts/01_fetch_ndb_opendata.py   # データ取得（任意）
Rscript scripts/02_load_opendata.R
Rscript scripts/03_build_tables.R
Rscript scripts/04_figures.R
Rscript scripts/05_model_binomial.R
Rscript scripts/06_prefecture_per_capita.R
bash scripts/render_report.sh              # HTML レポート生成
```

---

## ディレクトリ構成

```text
ndb-telemedicine-trends-2026/
├── README.md
├── DESCRIPTION
├── docs/
│   └── statistical-analysis-plan.md   # SAP
├── config/
│   ├── defaults.yml
│   ├── ndb_rounds.yml
│   └── procedure_codes.yml
├── R/                                 # 共通関数
├── scripts/                           # 解析スクリプト（00–06）
├── reports/
│   └── analysis_report.qmd
├── data/raw/                          # NDB 生データ（gitignore）
└── output/                            # 図表・集計結果
    ├── tables/
    ├── figures/
    └── reports/
```

---

## 主な出力

| 種別 | パス |
|------|------|
| トレンド | `output/tables/national_trend.csv` |
| 主解析セル | `output/tables/main_analysis_cells.csv` |
| モデル | `output/tables/model_fixed_effects.csv` |
| 都道府県（人口あたり） | `output/tables/prefecture_per_capita.csv` |
| Figure 1–4 | `output/figures/figure*.png` |
| Supplementary | `output/figures/supplementary_*.png` |
| レポート | `output/reports/analysis_report.html` |

---

## 参照

| 項目 | 内容 |
|------|------|
| データソース | [NDB オープンデータ分析サイト](https://www.mhlw.go.jp/ndb/opendatasite/) |
| NDB 概要 | [厚生労働省 NDB ホームページ](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/reseputo/index.html) |

---

## ライセンス

MIT License（`LICENSE` 参照）。
