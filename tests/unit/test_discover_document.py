from fintrace.ingestion.models import (
    DiscoveredDocument,
    DocumentSource,
    DocumentType,
)


def test_discovered_document_creation() -> None:
    document = DiscoveredDocument(
        document_id="reliance-2026-ar",
        company="Reliance Industries Limited",
        ticker="RELIANCE",
        exchange="NSE",
        document_type=DocumentType.ANNUAL_REPORT,
        source=DocumentSource.NSE,
        source_url="https://example.com/report.pdf",
    )

    assert document.document_id == "reliance-2026-ar"
    assert document.company == "Reliance Industries Limited"
    assert document.ticker == "RELIANCE"
    assert document.exchange == "NSE"
    assert document.document_type == DocumentType.ANNUAL_REPORT
    assert document.source == DocumentSource.NSE
    assert document.source_url == "https://example.com/report.pdf"