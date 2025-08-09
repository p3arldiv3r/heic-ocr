from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from tqdm import tqdm

from . import heic_utils
from . import preprocess as pp
from .ocr import OCREngine, OCREngineType
from .extract import parse_fields
from .io_utils import write_json_records, write_csv_records, write_text


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def choose_best_ocr_result(
    engine: OCREngine,
    image_paths: List[Path],
    save_preprocessed_dir: Path | None,
    rotation_mode: str,
) -> Tuple[str, float, int]:
    """
    Runs OCR possibly across multiple rotations and returns (best_text, best_confidence, best_rotation_deg)
    """
    best_text: str = ""
    best_confidence: float = -1.0
    best_rotation: int = 0

    rotation_candidates: List[int]
    if rotation_mode == "auto":
        rotation_candidates = [0, 90, 180, 270]
    else:
        rotation_candidates = [0]

    for image_path in image_paths:
        image_bgr = pp.read_image_bgr(image_path)
        for rot in rotation_candidates:
            processed = pp.preprocess_for_ocr(image_bgr, rotate_deg=rot)

            if save_preprocessed_dir is not None:
                out_name = image_path.stem + (f"_r{rot}" if rot else "") + "_prep.png"
                pp.save_image(processed, save_preprocessed_dir / out_name)

            text, conf = engine.run(processed)
            if conf > best_confidence:
                best_confidence = conf
                best_text = text
                best_rotation = rot

    return best_text, best_confidence, best_rotation


def run_pipeline(
    input_dir: Path,
    output_dir: Path,
    engine_type: OCREngineType,
    languages: List[str],
    write_json: bool,
    write_csv: bool,
    save_preprocessed: bool,
    rotation_mode: str,
) -> None:
    ensure_directory(output_dir)
    converted_dir = output_dir / "converted"
    ensure_directory(converted_dir)
    ocr_raw_dir = output_dir / "ocr_raw"
    ensure_directory(ocr_raw_dir)
    preprocessed_dir = output_dir / "preprocessed" if save_preprocessed else None
    if preprocessed_dir is not None:
        ensure_directory(preprocessed_dir)

    # Prepare images (convert HEIC → PNG) and collect all image paths for OCR
    ready_images: List[Path] = heic_utils.prepare_images(input_dir, converted_dir)
    if not ready_images:
        print("No images found in input folder.")
        return

    engine = OCREngine(engine_type, languages)

    extracted_records: List[Dict[str, str]] = []

    for img_path in tqdm(ready_images, desc="Processing images", unit="img"):
        best_text, best_conf, best_rot = choose_best_ocr_result(
            engine=engine,
            image_paths=[img_path],
            save_preprocessed_dir=preprocessed_dir,
            rotation_mode=rotation_mode,
        )

        # Save raw OCR text
        write_text(ocr_raw_dir / f"{img_path.stem}.txt", best_text)

        fields = parse_fields(best_text)
        fields["source_file"] = str(img_path)
        fields["ocr_confidence"] = f"{best_conf:.3f}" if best_conf >= 0 else ""
        fields["rotation_deg"] = str(best_rot)
        extracted_records.append(fields)

    # Write outputs
    if write_csv:
        write_csv_records(output_dir / "extracted.csv", extracted_records)
    if write_json:
        write_json_records(output_dir / "extracted.json", extracted_records)

    print(f"Done. Processed {len(ready_images)} image(s). Output: {output_dir}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch OCR for water heater labels: HEIC→PNG, OCR, field extraction, CSV/JSON output."
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Path to input folder containing .heic/.heif/.jpg/.png images"
    )
    parser.add_argument(
        "-o", "--output", default="output", help="Path to output folder (default: ./output)"
    )
    parser.add_argument(
        "--engine",
        choices=[e.value for e in OCREngineType],
        default=OCREngineType.EASYOCR.value,
        help="OCR engine to use (default: easyocr)",
    )
    parser.add_argument(
        "--languages",
        default="en",
        help="Comma-separated language codes for OCR (default: en)",
    )
    parser.add_argument("--write-json", action="store_true", help="Write extracted records to JSON")
    parser.add_argument("--write-csv", action="store_true", help="Write extracted records to CSV")
    parser.add_argument(
        "--save-preprocessed",
        action="store_true",
        help="Save preprocessed images to output/preprocessed for inspection",
    )
    parser.add_argument(
        "--rotation",
        choices=["auto", "none"],
        default="auto",
        help="Try multiple rotations to maximize OCR (default: auto)",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    input_dir = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input folder not found: {input_dir}")
        sys.exit(1)

    try:
        engine_type = OCREngineType(args.engine)
    except ValueError:
        print(f"Invalid engine: {args.engine}")
        sys.exit(1)

    # Parse comma-separated languages
    languages = [lang.strip() for lang in str(args.languages).split(",") if lang.strip()]

    run_pipeline(
        input_dir=input_dir,
        output_dir=output_dir,
        engine_type=engine_type,
        languages=languages,
        write_json=args.write_json,
        write_csv=args.write_csv,
        save_preprocessed=args.save_preprocessed,
        rotation_mode=args.rotation,
    )


if __name__ == "__main__":
    main()


