from __future__ import annotations

import shutil
from pathlib import Path
from typing import List


IMAGE_EXTENSIONS = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def convert_heic_to_png(heic_path: Path, out_png_path: Path) -> Path:
    """Convert a single HEIC/HEIF file to PNG using pillow-heif + Pillow."""
    # Lazy imports so CLI help works without these deps installed
    import pillow_heif  # type: ignore
    from PIL import Image  # type: ignore

    heif_file = pillow_heif.read_heif(str(heic_path))
    image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
    out_png_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_png_path, format="PNG")
    return out_png_path


def prepare_images(input_dir: Path, converted_dir: Path) -> List[Path]:
    """
    Collects images in input_dir. HEIC/HEIF files are converted to PNG under converted_dir.
    Other image formats are referenced directly.
    Returns a list of image paths suitable for OCR.
    """
    input_dir = Path(input_dir)
    converted_dir = Path(converted_dir)

    ready: List[Path] = []
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file() or not is_image_file(path):
            continue

        suffix = path.suffix.lower()
        if suffix in {".heic", ".heif"}:
            out_png = converted_dir / (path.stem + ".png")
            if not out_png.exists():
                try:
                    convert_heic_to_png(path, out_png)
                except Exception as exc:  # noqa: BLE001
                    print(f"Failed to convert {path}: {exc}")
                    continue
            ready.append(out_png)
        else:
            # Copy non-HEIC images to converted_dir to keep outputs together
            out_copy = converted_dir / path.name
            if not out_copy.exists():
                try:
                    out_copy.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, out_copy)
                except Exception as exc:  # noqa: BLE001
                    print(f"Failed to copy {path}: {exc}")
                    continue
            ready.append(out_copy)

    return ready


