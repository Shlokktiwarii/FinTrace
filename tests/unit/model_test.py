from datetime import datetime, timezone

from fintrace.ingestion.models import (
    DocumentSource,
    DocumentType,
    RawDocument,
)


def test_raw_document_creation() -> None:
    document = RawDocument(
        document_id="reliance-2026-ar",
        company="Reliance Industries Limited",
        ticker="RELIANCE",
        exchange="NSE",
        document_type=DocumentType.ANNUAL_REPORT,
        source=DocumentSource.NSE,
        source_url="https://example.com/report.pdf",
        content=b"raw document bytes",
        fetched_at=datetime.now(timezone.utc),
    )

    assert document.company == "Reliance Industries Limited"
    assert document.ticker == "RELIANCE"
    assert document.source == DocumentSource.NSE
    assert document.document_type == DocumentType.ANNUAL_REPORT