# ndb-telemedicine-trends-2026

**2026年度公衆衛生学実習（M3）** 向けの解析リポジトリ。厚生労働省 **NDB オープンデータ** を用いて、**オンライン診療料**（診療行為コード `112023210`）の算定動向を集計・可視化する。

- **データ**: NDB オープンデータ（匿名化・集計済み）
- **対象**: オンライン診療料の算定回数
- **集計軸**: 都道府県別、性・年齢別、二次医療圏別、診療月別 など（公表形式に準拠）

---

## クイックスタート

### 1. クローンと依存関係

```bash
git clone git@github.com:io-murayama/ndb-telemedicine-trends-2026.git
cd ndb-telemedicine-trends-2026
bash scripts/bootstrap.sh   # yaml インストール + 構成チェック
```

| 層 | パッケージ |
|----|------------|
| 必須（土台） | `yaml`（`DESCRIPTION` Imports） |
| 解析用（予定） | `data.table`, `dplyr`, `tidyr`, `readr`, `ggplot2`, `readxl`（Suggests） |

R は 4.2 以降を想定。

### 2. データの配置

1. [NDB オープンデータ分析サイト](https://www.mhlw.go.jp/ndb/opendatasite/) から、オンライン診療料を含む集計表をダウンロード
2. `data/raw/` に配置（生ファイルは git 管理外）

### 3. 解析（今後追加予定）

```bash
Rscript scripts/00_setup.R
# Rscript scripts/01_load_opendata.R   # TODO
# Rscript scripts/02_summarize.R       # TODO
# Rscript scripts/03_figures.R         # TODO
```

---

## ディレクトリ構成

```text
ndb-telemedicine-trends-2026/
├── README.md
├── DESCRIPTION
├── LICENSE
├── config/
│   └── defaults.yml          # プロジェクト設定・NDB 対象コード
├── R/                          # 共通関数
│   ├── paths.R
│   ├── config.R
│   └── bootstrap.R
├── scripts/
│   ├── bootstrap.sh            # 初期セットアップ
│   ├── 00_setup.R
│   └── 00_check_scaffold.R
├── data/
│   └── raw/                    # NDB 生データ（gitignore）
└── output/                     # 図表・集計結果（gitignore）
    └── logs/
```

---

## 参照

| 項目 | 内容 |
|------|------|
| 診療行為コード | `112023210`（オンライン診療料） |
| データソース | [NDB オープンデータ分析サイト](https://www.mhlw.go.jp/ndb/opendatasite/) |
| NDB 概要 | [厚生労働省 NDB ホームページ](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/reseputo/index.html) |

第 6 回以降の NDB オープンデータでは、一部診療行為について「都道府県別／性・年齢別」のクロス集計が公表されており、オンライン診療料も対象に含まれる。

---

## ライセンス

MIT License（`LICENSE` 参照）。

---

## 関連リポジトリ

- [io-murayama/ndb-telemedicine-trends](https://github.com/io-murayama/ndb-telemedicine-trends) — 同名テーマの別リポジトリ
