"""Fast, minimal readers for the annual outpatient function report workbooks.

The raw workbooks contain roughly 150,000 rows each.  Reading the worksheet XML
directly avoids loading the full workbook into memory while retaining the original
facility-level values, including suppressed cells (``*``).
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pandas as pd
from lxml import etree

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_COLUMN_RE = re.compile(r"([A-Z]+)")


def _column_index(cell_reference: str) -> int:
    """Return the zero-based Excel column index from a cell reference."""
    match = _COLUMN_RE.match(cell_reference)
    if match is None:
        raise ValueError(f"Invalid Excel cell reference: {cell_reference}")
    index = 0
    for character in match.group(1):
        index = index * 26 + ord(character) - ord("A") + 1
    return index - 1


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    """Read the shared-string table, preserving line breaks in header labels."""
    try:
        source = archive.open("xl/sharedStrings.xml")
    except KeyError:
        return []

    strings: list[str] = []
    with source:
        for _, element in etree.iterparse(source, events=("end",), tag=f"{_NS}si"):
            strings.append("".join(element.itertext()))
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]
    return strings


def _cell_value(cell: etree._Element, shared_strings: list[str]) -> str | None:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        return "".join(cell.itertext())

    value = cell.findtext(f"{_NS}v")
    if value is None:
        return None
    if cell_type == "s":
        return shared_strings[int(value)]
    return value


def _normalise_code(value: str | None, width: int) -> str | None:
    if value is None or value == "":
        return None
    value = str(value).strip()
    value = value.removesuffix(".0")
    return value.zfill(width)


def _parse_count(value: str | None) -> float | None:
    """Convert a published count; return None for a suppressed/non-numeric cell."""
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def _required_column_indexes(headers: dict[int, str]) -> dict[str, int]:
    """Find fields by their published Japanese labels, allowing line breaks."""
    clean_headers = {index: header.replace("\n", "") for index, header in headers.items()}

    expected = {
        "facility_code": "オープンデータ医療機関コード",
        "facility_name": "医療機関名",
        "prefecture_code": "都道府県コード",
        "sma_code": "二次医療圏コード",
        "sma_name": "二次医療圏名",
        "municipality_code": "市区町村コード",
        "municipality_name": "市区町村名称",
        "medical_institution_code": "医療機関コード（医科）",
        "report_month": "報告月",
        "online_initial_raw": "初診（情報通信機器を用いた場合）の外来の患者延べ数",
        "online_repeat_raw": "再診（情報通信機器を用いた場合）の外来の患者延べ数",
    }
    indexes: dict[str, int] = {}
    for field, label in expected.items():
        matching = [index for index, header in clean_headers.items() if header == label]
        if len(matching) != 1:
            raise ValueError(f"Could not uniquely identify column {label!r}: {matching}")
        indexes[field] = matching[0]
    return indexes


def read_annual_online_outpatient_facilities(path: Path, year: int) -> pd.DataFrame:
    """Read annual facility-level online outpatient counts from one workbook.

    Only the published annual record (``報告月 = 0``) is retained.  The two online
    fields are *patient-days*, not claims.  Asterisks and other non-numeric values
    are retained as a suppression flag rather than converted to zero.
    """
    rows: list[dict[str, object]] = []
    headers: dict[int, str] | None = None
    column_indexes: dict[str, int] | None = None

    with zipfile.ZipFile(path) as archive:
        shared_strings = _read_shared_strings(archive)
        worksheet_names = sorted(
            name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )
        if len(worksheet_names) != 1:
            raise ValueError(f"Expected one worksheet in {path.name}, found {worksheet_names}")

        with archive.open(worksheet_names[0]) as source:
            for _, row in etree.iterparse(source, events=("end",), tag=f"{_NS}row"):
                row_number = int(row.get("r", "0"))
                values = {
                    _column_index(cell.get("r", "A1")): _cell_value(cell, shared_strings)
                    for cell in row.findall(f"{_NS}c")
                }
                if row_number == 5:
                    headers = {index: value for index, value in values.items() if value is not None}
                    column_indexes = _required_column_indexes(headers)
                elif row_number >= 7 and column_indexes is not None:
                    raw = {field: values.get(index) for field, index in column_indexes.items()}
                    if raw["report_month"] not in {"0", 0}:
                        row.clear()
                        continue
                    if raw["facility_code"] in {None, ""}:
                        row.clear()
                        continue

                    initial = _parse_count(raw["online_initial_raw"])
                    repeat = _parse_count(raw["online_repeat_raw"])
                    rows.append(
                        {
                            "year": year,
                            "facility_code": _normalise_code(raw["facility_code"], 10),
                            "medical_institution_code": _normalise_code(raw["medical_institution_code"], 10),
                            "facility_name": raw["facility_name"],
                            "prefecture_code": _normalise_code(raw["prefecture_code"], 2),
                            "sma_code": _normalise_code(raw["sma_code"], 4),
                            "sma_name": raw["sma_name"],
                            "municipality_code": _normalise_code(raw["municipality_code"], 5),
                            "municipality_name": raw["municipality_name"],
                            "online_initial_patient_days": initial,
                            "online_repeat_patient_days": repeat,
                            "initial_suppressed": initial is None and raw["online_initial_raw"] not in {None, ""},
                            "repeat_suppressed": repeat is None and raw["online_repeat_raw"] not in {None, ""},
                        }
                    )

                row.clear()
                while row.getprevious() is not None:
                    del row.getparent()[0]

    if headers is None:
        raise ValueError(f"Header row was not found in {path.name}")

    data = pd.DataFrame(rows)
    data["online_observed_patient_days"] = data[
        ["online_initial_patient_days", "online_repeat_patient_days"]
    ].fillna(0).sum(axis=1)
    data["online_components_complete"] = data[
        ["online_initial_patient_days", "online_repeat_patient_days"]
    ].notna().all(axis=1)
    data["any_online_component_suppressed"] = data[["initial_suppressed", "repeat_suppressed"]].any(axis=1)
    return data


def read_all_annual_online_outpatient_facilities(raw_directory: Path) -> pd.DataFrame:
    """Read the three user-supplied annual outpatient-function-report workbooks."""
    frames = [
        read_annual_online_outpatient_facilities(raw_directory / f"{year}.xlsx", year)
        for year in (2022, 2023, 2024)
    ]
    return pd.concat(frames, ignore_index=True)
