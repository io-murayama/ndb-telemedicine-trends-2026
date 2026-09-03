"""Download public e-Stat files used for the patient-side geography analysis.

The files are intentionally kept outside version control under data/raw/ because
they are reproducible public-source downloads. The identifiers are table-level
e-Stat statInfId values, rather than search-result URLs, so this script does not
depend on the e-Stat website layout.
"""

from __future__ import annotations

import argparse
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "data" / "raw" / "communications_survey"
BASE_URL = "https://www.e-stat.go.jp/stat-search/file-download?statInfId={stat_id}&fileKind=1"

# 2022 uses table numbers 9 and 15; the later releases use 8 and 15.
FILES = {
    "2022_table15.csv": "000040057188",
    "2023_table15.csv": "000040185454",
    "2024_table15.csv": "000040278952",
    "2022_internet_use.csv": "000040057181",
    "2023_internet_use.csv": "000040185447",
    "2024_internet_use.csv": "000040278945",
}


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="replace files that already exist")
    args = parser.parse_args()

    DESTINATION.mkdir(parents=True, exist_ok=True)
    for filename, stat_id in FILES.items():
        path = DESTINATION / filename
        if path.exists() and not args.force:
            print(f"skip {path.relative_to(ROOT)}")
            continue
        print(f"download {filename} (statInfId={stat_id})")
        download(BASE_URL.format(stat_id=stat_id), path)
        if path.stat().st_size < 1_000:
            raise RuntimeError(f"Downloaded file is unexpectedly small: {path}")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
