from datetime import datetime, timezone

from fintrace.ingestion.chunker import DocumentChunker
from fintrace.ingestion.models import (
    DocumentPage,
    DocumentSource,
    DocumentType,
    ParsedDocument,
    RawDocument,
)
from fintrace.ingestion.normalizer import DocumentNormalizer
from fintrace.ingestion.structure import DocumentStructureExtractor


def test_document_processing_pipeline() -> None:
    raw_document = RawDocument(
        document_id="reliance-2026-ar",
        company="Reliance Industries Limited",
        ticker="RELIANCE",
        exchange="NSE",
        document_type=DocumentType.ANNUAL_REPORT,
        source=DocumentSource.COMPANY,
        source_url="https://example.com/report.pdf",
        content=b"unused-for-this-test",
        fetched_at=datetime.now(timezone.utc),
    )

    parsed_document = ParsedDocument(
        document_id=raw_document.document_id,
        company=raw_document.company,
        source_url=raw_document.source_url,
        pages=(
            DocumentPage(
                page_number=1,
                text="""
                    Business Overview


                    Reliance Industries Limited
                    operates across multiple sectors.
                """,
            ),
            DocumentPage(
                page_number=2,
                text="""
                    Financial Statements

                    Revenue increased significantly during
                    the financial year.
                """,
            ),
        ),
    )

    normalized = DocumentNormalizer().normalize(
        parsed_document
    )

    assert len(normalized.pages) == 2

    structured = DocumentStructureExtractor().extract(
        normalized
    )

    chunks = DocumentChunker(
        max_characters=500,
    ).chunk(
        document_id=normalized.document_id,
        company=normalized.company,
        source_url=normalized.source_url,
        structured_pages=structured,
    )

    assert len(chunks) == 2

    assert chunks[0].document_id == "reliance-2026-ar"
    assert chunks[0].company == "Reliance Industries Limited"
    assert chunks[0].page_number == 1
    assert chunks[0].section == "Business Overview"

    assert chunks[1].page_number == 2
    assert chunks[1].section == "Financial Statements"

    assert "Revenue increased" in chunks[1].text