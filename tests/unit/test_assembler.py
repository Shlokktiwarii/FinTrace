from datetime import datetime, timezone

import pytest

from fintrace.ingestion.assembler import DocumentAssembler
from fintrace.ingestion.models import (
    DiscoveredDocument,
    DocumentSource,
    DocumentType,
    DownloadResult,
)


def test_assemble_raw_document() -> None:
    fetched_at = datetime.now(timezone.utc)

    document = DiscoveredDocument(
        document_id="reliance-2026-ar",
        company="Reliance Industries Limited",
        ticker="RELIANCE",
        exchange="NSE",
        document_type=DocumentType.ANNUAL_REPORT,
        source=DocumentSource.NSE,
        source_url="https://example.com/report.pdf",
    )

    result = DownloadResult(
        url=document.source_url,
        content=b"financial report",
        error=None,
        fetched_at=fetched_at,
    )

    raw_document = DocumentAssembler().assemble(document, result)

    assert raw_document.document_id == document.document_id
    assert raw_document.company == document.company
    assert raw_document.ticker == document.ticker
    assert raw_document.exchange == document.exchange
    assert raw_document.document_type == document.document_type
    assert raw_document.source == document.source
    assert raw_document.source_url == document.source_url
    assert raw_document.content == b"financial report"
    assert raw_document.fetched_at == fetched_at

def test_assemble_rejects_failed_download() -> None:
    document = DiscoveredDocument(
        document_id="reliance-2026-ar",
        company="Reliance Industries Limited",
        ticker="RELIANCE",
        exchange="NSE",
        document_type=DocumentType.ANNUAL_REPORT,
        source=DocumentSource.NSE,
        source_url="https://example.com/report.pdf",
    )

    result = DownloadResult(
        url=document.source_url,
        content=None,
        error="download failed",
        fetched_at=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError, match="failed download"):
        DocumentAssembler().assemble(document, result)