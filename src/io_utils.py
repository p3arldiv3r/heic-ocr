from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content or "", encoding="utf-8", errors="ignore")


def write_json_records(path: Path, records: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv_records(path: Path, records: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = infer_fieldnames(records)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in records:
            writer.writerow(row)


def infer_fieldnames(records: Iterable[Dict[str, str]]) -> List[str]:
    # Preserve a sensible order if present
    preferred = [
        "source_file",
        "manufacturer",
        "model_number",
        "serial_number",
        "capacity",
        "date_of_manufacture",
        "ocr_confidence",
        "rotation_deg",
    ]
    fields = list(preferred)
    existing = set(fields)
    for rec in records:
        for key in rec.keys():
            if key not in existing:
                fields.append(key)
                existing.add(key)
    return fields


