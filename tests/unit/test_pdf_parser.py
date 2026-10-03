from io import BytesIO

from reportlab.pdfgen import canvas

from fintrace.ingestion.models import (
    DocumentType,
    DocumentSource,
    RawDocument,
)
from fintrace.ingestion.parsers.pdf import PdfParser


def create_test_pdf() -> bytes:
    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, "Revenue increased by 12 percent.")
    pdf.showPage()
    pdf.drawString(100, 750, "Operating profit increased.")
    pdf.showPage()
    pdf.save()

    return buffer.getvalue()


def test_pdf_parser_extracts_page_text() -> None:
    document = RawDocument(
        document_id="test-document",
        company="Test Company",
        ticker="TEST",
        exchange="NSE",
        document_type=DocumentType.ANNUAL_REPORT,
        source=DocumentSource.COMPANY,
        source_url="https://example.com/report.pdf",
        content=create_test_pdf(),
        fetched_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
    )

    parsed = PdfParser().parse(document)

    assert len(parsed.pages) == 2

    assert parsed.pages[0].page_number == 1
    assert "Revenue increased" in parsed.pages[0].text

    assert parsed.pages[1].page_number == 2
    assert "Operating profit increased" in parsed.pages[1].text