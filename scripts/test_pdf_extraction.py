from pathlib import Path
from pypdf import PdfReader

PDF_PATH = Path(
    "data/raw/reliance/reliance_fy2025_repaired.pdf"
)


def main():
    reader = PdfReader(PDF_PATH)

    total_pages = len(reader.pages)
    successful_pages = 0
    empty_pages = []
    total_characters = 0

    print(f"Total pages: {total_pages}")

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""

            if text.strip():
                successful_pages += 1
                total_characters += len(text)
            else:
                empty_pages.append(page_number)

        except Exception as exc:
            print(f"Page {page_number} failed: {exc}")
            empty_pages.append(page_number)

    print("\n========== EXTRACTION REPORT ==========")
    print(f"Total pages: {total_pages}")
    print(f"Pages with text: {successful_pages}")
    print(f"Empty/failed pages: {len(empty_pages)}")
    print(f"Total extracted characters: {total_characters}")
    print(f"Empty page numbers: {empty_pages[:30]}")


if __name__ == "__main__":
    main()