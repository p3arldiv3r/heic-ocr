## Water Heater OCR (HEIC → OCR → Structured Data)

This is a small Python CLI app that:

- Converts `.heic` photos to `.png`
- Preprocesses images to improve OCR
- Runs OCR (EasyOCR by default; Tesseract optional)
- Extracts key fields (Manufacturer, Model, Serial, Capacity, Date of Manufacture)
- Writes CSV/JSON plus raw OCR text files

### 1) Setup (Windows)

Option A — EasyOCR (no external binary, larger pip download):

1. Create a virtual environment and install dependencies:

   ```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
   ```

Option B — Tesseract (small pip, requires installing Tesseract):

1. Install Tesseract OCR for Windows (use the official installer from the Tesseract project). After install, ensure `tesseract.exe` is on your PATH.
2. Create a virtual environment and install dependencies (still needed for the app):

   ```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
   ```

Then run with `--engine tesseract`.

### 2) Usage

Place your `.heic` (and/or `.jpg`, `.png`) images in a folder, then run:

```powershell
python -m src.main --input "C:\\path\\to\\images" --output output --write-csv --write-json --rotation auto
```

Switch OCR engine (optional):

```powershell
python -m src.main -i "C:\\path\\to\\images" -o output --engine tesseract --write-csv
```

Flags:

- `--input` / `-i`: input folder with images
- `--output` / `-o`: output folder (created if missing)
- `--engine`: `easyocr` (default) or `tesseract`
- `--languages`: comma-separated language codes (default: `en`)
- `--write-json`, `--write-csv`: choose output formats
- `--save-preprocessed`: save preprocessed images for inspection
- `--rotation`: `auto` (try 0/90/180/270) or `none`

### 3) Outputs

The app writes to the output folder:

- `converted/`: PNG copies of input images (HEIC converted)
- `ocr_raw/`: raw OCR text per image (`.txt`)
- `preprocessed/`: saved preprocessed images (if `--save-preprocessed`)
- `extracted.csv`: structured table of extracted fields (if `--write-csv`)
- `extracted.json`: JSON array of extracted records (if `--write-json`)

### 4) Notes and Tips

- Image quality matters: hold camera steady, fill the frame with the label, avoid glare.
- Manufacturer detection uses keyword matching; you can extend the list in `src/extract.py`.
- Regex heuristics are conservative. If your labels have consistent layouts, we can tighten them for better accuracy.
- If OCR quality is low, try `--save-preprocessed` and inspect results; also try `--engine tesseract`.


