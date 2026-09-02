# 都道府県人口（参照データ）

副次解析（Supplementary Figure C）の **人口あたり ICT 算定回数** の分母に使用する。

## 都道府県人口（参照データ）

副次解析（Supplementary Figure C / D）の **人口あたり ICT 算定回数** の分母に使用する。

## 都道府県境界（地図用）

| 項目 | 内容 |
|------|------|
| ファイル | `prefectures.geojson` |
| ソース | [dataofjapan/land](https://github.com/dataofjapan/land)（MIT） |
| 用途 | Supplementary Figure D（choropleth） |

## 必要なデータ

| 項目 | 内容 |
|------|------|
| ソース | [総務省統計局 人口推計](https://www.stat.go.jp/data/jinsui/) |
| 推奨表 | 第2表「都道府県、男女別人口－総人口（各年10月1日現在）」 |
| 対象年度 | 2022, 2023, 2024（主解析期間に対応） |
| 単位 | 人（総人口） |

## ファイル形式

`prefecture_population.csv`（UTF-8）:

```csv
prefecture_code,prefecture_name,fiscal_year,population,source
01,北海道,2022,5224614,総務省統計局 人口推計
...
```

- `prefecture_code`: 2桁コード（NDB 都道府県コードと一致）
- `fiscal_year`: 年度（2022–2024）
- `population`: 都道府県総人口

## 現在の同梱データ

リポジトリ同梱の `prefecture_population.csv` は、国勢調査2020の都道府県別構成を各年度の人口推計全国総人口に合わせて按分した暫定値です。**公式の都道府県別人口推計表（第2表）で差し替えることを推奨**します。

## 更新手順

1. e-Stat または統計局サイトから都道府県別総人口を取得
2. 本 CSV を上書き
3. `Rscript scripts/06_prefecture_per_capita.R` を再実行
