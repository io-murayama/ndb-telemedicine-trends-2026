#!/usr/bin/env python3
"""Download NDB open-data files for ndb06_2019 .. ndb11_2024 into data/raw/."""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

ROUNDS = {
    "ndb06_2019": "00010",
    "ndb07_2020": "00011",
    "ndb08_2021": "00012",
    "ndb09_2022": "00014",
    "ndb10_2023": "00016",
}

FILE_SPECS = [
    ("cross_initial_prefecture_sex_age.xlsx", "【初診】都道府県性年齢別算定回数"),
    ("cross_followup_prefecture_sex_age.xlsx", "【再診】都道府県性年齢別算定回数"),
    ("cross_outpatient_prefecture_sex_age.xlsx", "【外来診療料】都道府県性年齢別算定回数"),
    ("cross_online_prefecture_sex_age.xlsx", "【オンライン診療】都道府県性年齢別算定回数"),
    ("basic_initial_followup_sex_age.xlsx", "初再診料_性年齢別算定回数"),
    ("basic_initial_followup_prefecture.xlsx", "初再診料_都道府県別算定回数"),
    ("basic_initial_followup_month.xlsx", "初再診料_診療月別算定回数"),
    ("basic_initial_followup_sma.xlsx", "初再診料_二次医療圏別算定回数"),
]

NDB11_ZIP = "https://www.mhlw.go.jp/content/12400000/001742573.zip"


def fetch_html(page_id: str) -> str:
    url = f"https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000177221_{page_id}.html"
    with urllib.request.urlopen(url) as resp:
        return resp.read().decode("utf-8", "ignore")


def find_xlsx_url(html: str, label: str) -> str | None:
    patterns = [
        rf'href="(/content/12400000/\d+\.xlsx)"[^>]*>{re.escape(label)}',
        rf'href="(/content/12400000/\d+\.xlsx)" target="_blank">{label}',
        rf'href="(/content/12400000/\d+\.xlsx)" target="_blank">{label}［',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            return "https://www.mhlw.go.jp" + m.group(1)
    return None


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)


def decode_zip_name(name: str) -> str:
    try:
        return name.encode("cp437").decode("cp932")
    except Exception:
        return name


def fetch_round(folder: str, page_id: str) -> list[str]:
    html = fetch_html(page_id)
    out_dir = RAW / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    missing: list[str] = []

    for filename, label in FILE_SPECS:
        url = find_xlsx_url(html, label)
        dest = out_dir / filename
        if url is None:
            missing.append(label)
            continue
        print(f"  download {filename} <- {url}")
        download(url, dest)

    return missing


def fetch_ndb11() -> list[str]:
    folder = "ndb11_2024"
    out_dir = RAW / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    missing: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "ndb11.zip"
        print(f"  download zip <- {NDB11_ZIP}")
        download(NDB11_ZIP, zip_path)

        label_to_filename = {label: fname for fname, label in FILE_SPECS}
        extracted: set[str] = set()
        with zipfile.ZipFile(zip_path) as zf:
            for info in zf.infolist():
                decoded = decode_zip_name(info.filename)
                if not decoded.endswith(".xlsx"):
                    continue
                if "/クロス/" not in decoded and "/A_基本診療料/" not in decoded:
                    continue
                if "歯科" in decoded:
                    continue
                for label, fname in label_to_filename.items():
                    if label in decoded and fname not in extracted:
                        target = out_dir / fname
                        print(f"  extract {fname} <- {decoded}")
                        with zf.open(info) as src, target.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
                        extracted.add(fname)

        missing = [label for label, fname in label_to_filename.items() if fname not in extracted]

    return missing


def write_readme(folder: str, round_no: int, fiscal_year: int, source_url: str) -> None:
    readme = RAW / folder / "README.md"
    readme.write_text(
        f"""# {folder}

第 {round_no} 回 NDB オープンデータ（{fiscal_year} 年度）の解析用ファイル置き場。

## 出典

- {source_url}

## ファイル

| ファイル | 内容 |
|----------|------|
| `cross_initial_prefecture_sex_age.xlsx` | 【初診】都道府県性年齢別算定回数 |
| `cross_followup_prefecture_sex_age.xlsx` | 【再診】都道府県性年齢別算定回数 |
| `cross_outpatient_prefecture_sex_age.xlsx` | 【外来診療料】都道府県性年齢別算定回数 |
| `cross_online_prefecture_sex_age.xlsx` | 【オンライン診療】都道府県性年齢別算定回数 |
| `basic_initial_followup_sex_age.xlsx` | 初再診料_性年齢別算定回数 |
| `basic_initial_followup_prefecture.xlsx` | 初再診料_都道府県別算定回数 |
| `basic_initial_followup_month.xlsx` | 初再診料_診療月別算定回数 |
| `basic_initial_followup_sma.xlsx` | 初再診料_二次医療圏別算定回数 |

再取得: `python3 scripts/01_fetch_ndb_opendata.py`
""",
        encoding="utf-8",
    )


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    meta = {
        "ndb06_2019": (6, 2019),
        "ndb07_2020": (7, 2020),
        "ndb08_2021": (8, 2021),
        "ndb09_2022": (9, 2022),
        "ndb10_2023": (10, 2023),
        "ndb11_2024": (11, 2024),
    }

    errors: list[str] = []

    for folder, page_id in ROUNDS.items():
        round_no, fiscal_year = meta[folder]
        source = f"https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000177221_{page_id}.html"
        print(f"[{folder}]")
        missing = fetch_round(folder, page_id)
        write_readme(folder, round_no, fiscal_year, source)
        if missing:
            errors.append(f"{folder}: missing {', '.join(missing)}")

    print("[ndb11_2024]")
    missing11 = fetch_ndb11()
    write_readme(
        "ndb11_2024",
        11,
        2024,
        "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000177221_00017.html",
    )
    if missing11:
        errors.append(f"ndb11_2024: missing {', '.join(missing11)}")

    if errors:
        print("\nWarnings:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
