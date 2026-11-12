from pathlib import Path

import pikepdf
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PDF = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "reliance"
    / "reliance_fy2025.pdf"
)

OUTPUT_PDF = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "reliance"
    / "reliance_fy2025_repaired.pdf"
)


def main() -> None:
    print("Starting PDF repair...")

    if not INPUT_PDF.exists():
        raise FileNotFoundError(INPUT_PDF)

    try:
        with pikepdf.open(INPUT_PDF) as pdf:
            print(f"Original pages: {len(pdf.pages)}")

            pdf.save(OUTPUT_PDF)

        print(f"Repaired PDF saved: {OUTPUT_PDF}")

        # Verify repaired PDF using pypdf
        reader = PdfReader(OUTPUT_PDF)

        print(f"Verified pages: {len(reader.pages)}")
        print("PDF repair successful.")

    except Exception as exc:
        print(f"PDF repair failed: {exc}")
        raise


if __name__ == "__main__":
    main()