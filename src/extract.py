from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from dateutil import parser as date_parser


MANUFACTURER_KEYWORDS = [
    "rheem",
    "ruud",
    "ao smith",
    "a. o. smith",
    "bradford white",
    "state water heaters",
    "state industries",
    "ge",
    "general electric",
    "whirlpool",
    "kenmore",
    "american water heater",
    "navien",
    "noritz",
    "rinnai",
    "bosch",
]


MODEL_HINTS = [
    r"model\s*(no\.?|number|#)?\s*[:]?\s*([\w\-/\.]+)",
    r"m/?n\.?\s*[:]?\s*([\w\-/\.]+)",
    r"mdl\.?\s*[:]?\s*([\w\-/\.]+)",
]


SERIAL_HINTS = [
    r"serial\s*(no\.?|number|#)?\s*[:]?\s*([\w\-/]+)",
    r"s/?n\.?\s*[:]?\s*([\w\-/]+)",
]


CAPACITY_HINTS = [
    r"(\d{2,3})\s*(gal|gallon|gallons)\b",
    r"(\d{2,3})\s*(l|litre|litres|liter|liters)\b",
]


DATE_HINTS = [
    r"(manufactured|mfg\.?\s*date|date\s*of\s*manufacture|dom)\s*[:\-]?\s*([\w\-/,. ]{6,})",
]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"[\t\x0b\x0c\r]+", " ", text)


def find_first_group(patterns: List[str], text: str, group_index: int = -1) -> Optional[str]:
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            try:
                if group_index == -1:
                    # Default to last captured group
                    return m.group(m.lastindex or 0).strip()
                return m.group(group_index).strip()
            except Exception:  # noqa: BLE001
                continue
    return None


def detect_manufacturer(text: str) -> Optional[str]:
    lowered = text.lower()
    for brand in MANUFACTURER_KEYWORDS:
        if brand in lowered:
            # Title-case each token for nicer output
            return " ".join(token.capitalize() for token in brand.split())
    return None


def parse_capacity(text: str) -> Optional[str]:
    for pat in CAPACITY_HINTS:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            number = m.group(1)
            unit = m.group(2).lower()
            if unit.startswith("gal"):
                return f"{number} gal"
            if unit.startswith("l"):
                return f"{number} L"
    return None


def parse_date_of_manufacture(text: str) -> Optional[str]:
    # Try to parse after known labels
    label_capture = find_first_group(DATE_HINTS, text)
    candidates: List[str] = []
    if label_capture:
        candidates.append(label_capture)
    # Also look for generic date-like strings
    candidates.extend(re.findall(r"\b(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})\b", text))
    candidates.extend(re.findall(r"\b(\d{4}[\-/]\d{1,2}[\-/]\d{1,2})\b", text))

    for cand in candidates:
        try:
            dt = date_parser.parse(cand, fuzzy=True, default=None)
            if dt is not None:
                return dt.date().isoformat()
        except Exception:  # noqa: BLE001
            continue
    return None


def post_clean(value: Optional[str]) -> str:
    if not value:
        return ""
    # Trim trailing punctuation and stray characters
    cleaned = value.strip().strip("-:;,.# ")
    # Remove very long tokens that are likely noise
    if len(cleaned) > 120:
        cleaned = cleaned[:120]
    return cleaned


def parse_fields(ocr_text: str) -> Dict[str, str]:
    text = normalize_whitespace(ocr_text or "")

    manufacturer = detect_manufacturer(text)
    model = find_first_group(MODEL_HINTS, text)
    serial = find_first_group(SERIAL_HINTS, text)
    capacity = parse_capacity(text)
    date_of_mfg = parse_date_of_manufacture(text)

    return {
        "manufacturer": post_clean(manufacturer),
        "model_number": post_clean(model),
        "serial_number": post_clean(serial),
        "capacity": post_clean(capacity),
        "date_of_manufacture": post_clean(date_of_mfg),
    }


