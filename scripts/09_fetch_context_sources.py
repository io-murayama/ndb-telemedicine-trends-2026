"""Fetch reproducible, official context data for NDB supply-geography analyses."""

from __future__ import annotations

import base64
import gzip
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "context"
POPULATION_URL = "https://www.stat.go.jp/data/jinsui/2021np/zuhyou/05k2021-3.xlsx"
ESTAT_SID = "0004024904"  # 2023 Medical Facility Survey, prefectural table 105.


def post_json(url: str, form: dict[str, object]) -> dict[str, object]:
    body = urllib.parse.urlencode(form).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read())


def pack(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
    return base64.b64encode(gzip.compress(text)).decode()


def selected_values(matter: dict[str, object]) -> tuple[list[dict[str, object]], int]:
    values = []
    all_selected = 1
    for value in dict(matter["listData"]).values():
        value = dict(value)
        if value.get("selected"):
            values.append(
                {
                    "name": value["name"],
                    "code": value["code"],
                    "unit": value.get("unitName", ""),
                    "explanation": value.get("explanation", ""),
                }
            )
        else:
            all_selected = 0
    return values, all_selected


def matter_payload(matter: dict[str, object]) -> dict[str, object]:
    values, all_selected = selected_values(matter)
    if matter["position"] == "top":
        values = values[:1]
    return {
        "matterId": matter["matterId"],
        "tableName": matter["tableName"],
        "dispTableName": matter["dispTableName"],
        "positionNum": matter["positionNum"],
        "listData": values,
        "allSelected": all_selected,
    }


def fetch_estat_table105() -> dict[str, object]:
    base = "https://www.e-stat.go.jp/dbview"
    model = post_json(f"{base}/api_get_model?sid={ESTAT_SID}", {})
    grouped = {"row": [], "col": [], "top": []}
    for matter in dict(model["matters"]).values():
        matter = dict(matter)
        grouped[str(matter["position"])].append(matter_payload(matter))

    request_data = {
        "rows": grouped["row"],
        "cols": grouped["col"],
        "tops": grouped["top"],
        "apiTops": [],
        "annotationFlg": model["annotationFlg"],
        "rowNoDataDispFlg": model["rowNoDataDispFlg"],
        "colNoDataDispFlg": model["colNoDataDispFlg"],
        "commaType": model["commaType"],
        "replaceSpChars": model["replaceSpChars"],
        "graphAxis": model["graphAxis"],
        "graphBasis": model["graphBasis"],
        "graphSort": model["graphSort"],
        "graphTitle": model["graphTitle"],
        "graphType": model["graphType"],
        "inputNumberOfCols": 99999,
        "inputNumberOfRows": 99999,
        "movementId": 0,
        "leftMoveFlg": model["leftMoveFlg"],
        "rightMoveFlg": model["rightMoveFlg"],
        "underMoveFlg": model["underMoveFlg"],
        "upMoveFlg": model["upMoveFlg"],
        "currentCols": None,
        "currentRows": None,
        "mode": "table",
    }
    form = request_data.copy()
    for key in ("rows", "cols", "tops", "apiTops"):
        form[key] = pack(form[key])
    return post_json(f"{base}/api_get_result?sid={ESTAT_SID}", form)


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=90) as response:
        destination.write_bytes(response.read())


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    population_path = RAW / "population_2021_prefecture_age3.xlsx"
    print(f"[download] {population_path.name}")
    download(POPULATION_URL, population_path)

    estat_path = RAW / "medical_facilities_2023_table105.json"
    print(f"[download] {estat_path.name}")
    estat_path.write_text(
        json.dumps(fetch_estat_table105(), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    (RAW / "README.md").write_text(
        """# Context data for supply-geography analysis

* `population_2021_prefecture_age3.xlsx`: Statistics Bureau, Population Estimates
  (1 October 2021), Table 3: prefectural population by three broad age groups.
  Source: https://www.stat.go.jp/data/jinsui/2021np/index.html
* `medical_facilities_2023_table105.json`: e-Stat, 2023 Medical Facility Survey,
  prefectural Table 105. The first numeric column is the number of general clinics.
  Source: https://www.e-stat.go.jp/dbview?sid=0004024904
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
