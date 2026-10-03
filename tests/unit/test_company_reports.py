from fintrace.ingestion.models import (
    DiscoveredDocument,
    DocumentSource,
    DocumentType,
)
from fintrace.ingestion.sources.company_reports import CompanyReportSource


def test_company_report_source_discovers_reports() -> None:
    report = DiscoveredDocument(
        document_id="reliance-2026-ar",
        company="Reliance Industries Limited",
        ticker="RELIANCE",
        exchange="NSE",
        document_type=DocumentType.ANNUAL_REPORT,
        source=DocumentSource.COMPANY,
        source_url="https://example.com/reliance-2026.pdf",
    )

    source = CompanyReportSource(
        company="Reliance Industries Limited",
        ticker="RELIANCE",
        exchange="NSE",
        reports=[report],
    )

    documents = list(source.discover_documents())

    assert len(documents) == 1
    assert documents[0] == report