from io import BytesIO

from pypdf import PdfReader

from fintrace.ingestion.models import (
    DocumentPage,
    ParsedDocument,
    RawDocument,
)


class PdfParser:
    """Extract page-level text from PDF documents."""

    def parse(self, document: RawDocument) -> ParsedDocument:
        """Extract text from every page of a PDF."""

        reader = PdfReader(BytesIO(document.content))

        pages: list[DocumentPage] = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            pages.append(
                DocumentPage(
                    page_number=page_number,
                    text=text,
                )
            )

        return ParsedDocument(
            document_id=document.document_id,
            company=document.company,
            source_url=document.source_url,
            pages=tuple(pages),
        )