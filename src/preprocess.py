from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np


def read_image_bgr(path: Path) -> np.ndarray:
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"Failed to read image: {path}")
    return img


def save_image(image_bgr: np.ndarray, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Use imencode to support Windows paths with non-ASCII
    ext = out_path.suffix.lower().lstrip(".") or "png"
    _, buf = cv2.imencode(f".{ext}", image_bgr)
    buf.tofile(str(out_path))


def rotate_image(image_bgr: np.ndarray, degrees_ccw: int) -> np.ndarray:
    if degrees_ccw % 360 == 0:
        return image_bgr
    rot_map = {90: cv2.ROTATE_90_COUNTERCLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_CLOCKWISE}
    deg = degrees_ccw % 360
    if deg in rot_map:
        return cv2.rotate(image_bgr, rot_map[deg])
    # Fallback for arbitrary angles (not used in this app)
    h, w = image_bgr.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, degrees_ccw, 1.0)
    return cv2.warpAffine(image_bgr, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def preprocess_for_ocr(image_bgr: np.ndarray, rotate_deg: int = 0) -> np.ndarray:
    """
    Lightweight preprocessing: rotate, grayscale, CLAHE contrast, mild sharpening, and denoise.
    Returns BGR image suitable for OCR engines that accept BGR/RGB.
    """
    img = rotate_image(image_bgr, rotate_deg)

    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Contrast Limited Adaptive Histogram Equalization
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)

    # Unsharp masking for mild sharpening
    blurred = cv2.GaussianBlur(equalized, (0, 0), sigmaX=1.0)
    sharpened = cv2.addWeighted(equalized, 1.5, blurred, -0.5, 0)

    # Bilateral filter to reduce noise while keeping edges
    denoised = cv2.bilateralFilter(sharpened, d=7, sigmaColor=50, sigmaSpace=50)

    # Return as 3-channel BGR for OCR engines that expect color
    processed_bgr = cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)
    return processed_bgr


