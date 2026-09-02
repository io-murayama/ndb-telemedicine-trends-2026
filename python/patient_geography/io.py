"""Read the public e-Stat CSVs and the repository's NDB supply-side table."""

from __future__ import annotations

import csv
import re
from itertools import combinations
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

YEARS = (2022, 2023, 2024)
SURVEY_FILES = {
    2022: {"patient": "2022_table15.csv", "internet": "2022_internet_use.csv"},
    2023: {"patient": "2023_table15.csv", "internet": "2023_internet_use.csv"},
    2024: {"patient": "2024_table15.csv", "internet": "2024_internet_use.csv"},
}
STAT_INFOS = {
    2022: {"patient": "000040057188", "internet": "000040057181"},
    2023: {"patient": "000040185454", "internet": "000040185447"},
    2024: {"patient": "000040278952", "internet": "000040278945"},
}
REGION_ORDER = [
    "北海道", "東北", "北関東", "南関東", "北陸", "甲信越", "東海", "近畿", "中国", "四国", "九州・沖縄"
]


def read_estat_csv(path: Path) -> list[list[str]]:
    """Read an e-Stat CSV, which is currently published in CP932."""
    with path.open(encoding="cp932", newline="") as stream:
        return list(csv.reader(stream))


def _find_header(rows: list[list[str]], value_fragment: str) -> list[str]:
    for row in rows:
        if any("集計人数" in cell for cell in row) and any(value_fragment in cell for cell in row):
            return row
    raise ValueError(f"Could not find the column header for {value_fragment!r}")


def _column_index(header: list[str], value_fragment: str) -> int:
    matches = [index for index, cell in enumerate(header) if cell == value_fragment]
    if not matches:
        matches = [index for index, cell in enumerate(header) if value_fragment in cell]
    if len(matches) != 1:
        raise ValueError(f"Expected one column containing {value_fragment!r}, found {matches}")
    return matches[0]


def _number(value: str) -> float:
    value = value.strip().replace(",", "")
    if value in {"", "-", "－"}:
        return float("nan")
    return float(value)


def _location_rows(path: Path, value_fragment: str, value_name: str, year: int) -> pd.DataFrame:
    rows = read_estat_csv(path)
    header = _find_header(rows, value_fragment)
    sample_index = _column_index(header, "集計人数")
    weighted_index = _column_index(header, "比重調整後集計人数")
    value_index = _column_index(header, value_fragment)

    extracted = []
    for row in rows:
        if len(row) <= value_index or row[0] not in {"全体", "地方", "都道府県"}:
            continue
        extracted.append(
            {
                "year": year,
                "level": row[0],
                "area_label": row[1].strip(),
                "sample_n": _number(row[sample_index]),
                "weighted_n": _number(row[weighted_index]),
                value_name: _number(row[value_index]),
            }
        )
    return pd.DataFrame(extracted)


def _split_prefecture(label: str) -> tuple[str, str]:
    matched = re.fullmatch(r"(\d{2})(.+)", label)
    if matched is None:
        raise ValueError(f"Unexpected prefecture label: {label!r}")
    return matched.group(1), matched.group(2)


def load_survey(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return prefecture, region, and national values from official source files."""
    raw_dir = root / "data" / "raw" / "communications_survey"
    patient_pieces = []
    internet_pieces = []
    for year in YEARS:
        patient_path = raw_dir / SURVEY_FILES[year]["patient"]
        internet_path = raw_dir / SURVEY_FILES[year]["internet"]
        if not patient_path.exists() or not internet_path.exists():
            missing = [str(path) for path in (patient_path, internet_path) if not path.exists()]
            raise FileNotFoundError("Missing public survey file(s): " + ", ".join(missing))
        patient_pieces.append(_location_rows(patient_path, "オンライン診療の利用", "patient_online_rate_pct", year))
        internet_pieces.append(_location_rows(internet_path, "はい", "internet_use_rate_pct", year))

    patient = pd.concat(patient_pieces, ignore_index=True)
    internet = pd.concat(internet_pieces, ignore_index=True)
    keys = ["year", "level", "area_label"]
    merged = patient.merge(internet, on=keys, suffixes=("_patient", "_internet"), validate="one_to_one")
    merged = merged.rename(
        columns={
            "sample_n_patient": "patient_sample_n",
            "weighted_n_patient": "patient_weighted_n",
            "sample_n_internet": "internet_sample_n",
            "weighted_n_internet": "internet_weighted_n",
        }
    )

    prefecture = merged[merged["level"] == "都道府県"].copy()
    prefecture[["prefecture_code", "prefecture_name"]] = prefecture["area_label"].apply(
        lambda label: pd.Series(_split_prefecture(label))
    )
    prefecture["estimated_events_proxy"] = (
        prefecture["patient_sample_n"] * prefecture["patient_online_rate_pct"] / 100
    )
    prefecture["low_event_proxy"] = prefecture["estimated_events_proxy"] < 10
    prefecture["source_table15_stat_infid"] = prefecture["year"].map(lambda year: STAT_INFOS[year]["patient"])
    prefecture["source_internet_stat_infid"] = prefecture["year"].map(lambda year: STAT_INFOS[year]["internet"])

    region = merged[merged["level"] == "地方"].copy()
    region["region"] = pd.Categorical(region["area_label"], categories=REGION_ORDER, ordered=True)
    national = merged[merged["level"] == "全体"].copy()
    validate_survey(prefecture, region, national)
    return prefecture, region, national


def validate_survey(prefecture: pd.DataFrame, region: pd.DataFrame, national: pd.DataFrame) -> None:
    if prefecture.shape[0] != len(YEARS) * 47:
        raise ValueError(f"Expected 141 prefecture rows, found {prefecture.shape[0]}")
    if region.shape[0] != len(YEARS) * len(REGION_ORDER):
        raise ValueError(f"Unexpected number of region rows: {region.shape[0]}")
    if national.shape[0] != len(YEARS):
        raise ValueError(f"Expected one national row per year, found {national.shape[0]}")
    expected_codes = {f"{code:02d}" for code in range(1, 48)}
    for year, part in prefecture.groupby("year"):
        if set(part["prefecture_code"]) != expected_codes:
            raise ValueError(f"Prefecture coverage is incomplete for {year}")
    for column in ("patient_online_rate_pct", "internet_use_rate_pct"):
        if not prefecture[column].between(0, 100).all():
            raise ValueError(f"Out-of-range value in {column}")


def load_ndb_supply(root: Path) -> pd.DataFrame:
    """Load the existing NDB medical-institution-location standardized table."""
    path = root / "output" / "tables" / "prefecture_standardized.csv"
    if not path.exists():
        raise FileNotFoundError(f"NDB supply-side table is missing: {path}")
    supply = pd.read_csv(path, dtype={"prefecture_code": str})
    supply["prefecture_code"] = supply["prefecture_code"].str.zfill(2)
    supply = supply.rename(columns={"fiscal_year": "year", "standardized_proportion_pct": "supply_standardized_rate_pct"})
    supply = supply[["year", "prefecture_code", "prefecture_name", "supply_standardized_rate_pct"]]
    if supply.shape[0] != len(YEARS) * 47:
        raise ValueError(f"Expected 141 NDB supply rows, found {supply.shape[0]}")
    return supply


def spearman_by_year(frame: pd.DataFrame, left: str, right: str, comparison: str) -> pd.DataFrame:
    rows = []
    for year, part in frame.groupby("year"):
        rho, _ = spearmanr(part[left], part[right])
        rows.append({"comparison": comparison, "year": year, "spearman_rho": rho, "n_prefectures": part.shape[0]})
    return pd.DataFrame(rows)


def rank_stability(frame: pd.DataFrame, value: str, outcome: str) -> pd.DataFrame:
    values = frame.pivot(index="prefecture_code", columns="year", values=value)
    rows = []
    for left, right in combinations(YEARS, 2):
        rho, _ = spearmanr(values[left], values[right])
        rows.append(
            {
                "outcome": outcome,
                "year_left": left,
                "year_right": right,
                "spearman_rho": rho,
                "n_prefectures": values.shape[0],
            }
        )
    return pd.DataFrame(rows)
