from __future__ import annotations

from enum import Enum
from typing import List, Tuple

import numpy as np


class OCREngineType(Enum):
    EASYOCR = "easyocr"
    TESSERACT = "tesseract"


class OCREngine:
    """Thin wrapper over EasyOCR or Tesseract, returning (text, mean_confidence)."""

    def __init__(self, engine_type: OCREngineType, languages: List[str] | None = None) -> None:
        self.engine_type = engine_type
        self.languages = languages or ["en"]
        self._easyocr_reader = None

        if self.engine_type == OCREngineType.EASYOCR:
            try:
                import easyocr  # type: ignore

                self._easyocr_reader = easyocr.Reader(self.languages, gpu=False, verbose=False)
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(
                    "EasyOCR initialization failed. Ensure dependencies are installed or choose --engine tesseract."
                ) from exc
        elif self.engine_type == OCREngineType.TESSERACT:
            try:
                import pytesseract  # type: ignore  # noqa: F401
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(
                    "pytesseract not available. Install Tesseract OCR and pytesseract, or choose --engine easyocr."
                ) from exc

    def run(self, image_bgr: np.ndarray) -> Tuple[str, float]:
        if self.engine_type == OCREngineType.EASYOCR:
            return self._run_easyocr(image_bgr)
        return self._run_tesseract(image_bgr)

    def _run_easyocr(self, image_bgr: np.ndarray) -> Tuple[str, float]:
        assert self._easyocr_reader is not None
        # EasyOCR expects RGB; convert from BGR
        import cv2

        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        results = self._easyocr_reader.readtext(rgb)
        # results: list of [bbox, text, confidence]
        texts = []
        confidences: List[float] = []
        for _bbox, text, conf in results:
            if text is None or not str(text).strip():
                continue
            texts.append(str(text))
            try:
                confidences.append(float(conf))
            except Exception:  # noqa: BLE001
                pass
        joined = "\n".join(texts)
        mean_conf = float(np.mean(confidences)) if confidences else -1.0
        return joined, mean_conf

    def _run_tesseract(self, image_bgr: np.ndarray) -> Tuple[str, float]:
        import cv2
        import pytesseract

        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        text = pytesseract.image_to_string(rgb, lang="+".join(self.languages))
        # pytesseract basic API does not expose confidences here; return sentinel
        return text, -1.0


