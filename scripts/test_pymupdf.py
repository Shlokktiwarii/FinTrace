from pathlib import Path
import fitz

PDF_PATH = Path(
    "data/raw/reliance/reliance_fy2025_repaired.pdf"
)


def main():
    doc = fitz.open(PDF_PATH)

    total_pages = len(doc)
    successful_pages = 0
    total_characters = 0
    empty_pages = []

    print(f"Total pages: {total_pages}")

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text("text")

        if text.strip():
            successful_pages += 1
            total_characters += len(text)
        else:
            empty_pages.append(page_number)

    print("\n========== PYMuPDF EXTRACTION REPORT ==========")
    print(f"Total pages: {total_pages}")
    print(f"Pages with text: {successful_pages}")
    print(f"Empty pages: {len(empty_pages)}")
    print(f"Total characters: {total_characters}")
    print(f"First 30 empty pages: {empty_pages[:30]}")

    if successful_pages:
        print("\nSample extracted text:\n")
        print(doc[0].get_text("text")[:1000])

    doc.close()


if __name__ == "__main__":
    main()