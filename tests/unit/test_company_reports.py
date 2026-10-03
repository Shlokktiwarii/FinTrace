import pytest

from fintrace.ingestion.sources.company_reports import CompanyReportSource
from fintrace.ingestion.sources.parsers.report_links import ReportLinkParser


class FakeFetcher:
    async def fetch(self, url: str) -> bytes:
        return b"""
        <html>
            <body>
                <a href="/reports/annual-2026.pdf">
                    Annual Report 2026
                </a>
                <a href="/reports/results-2026.pdf">
                    Financial Results 2026
                </a>
            </body>
        </html>
        """


@pytest.mark.asyncio
async def test_company_report_source_discovers_documents() -> None:
    source = CompanyReportSource(
        company="Reliance Industries Limited",
        ticker="RELIANCE",
        exchange="NSE",
        reports_url="https://example.com/investor/",
        fetcher=FakeFetcher(),
        parser=ReportLinkParser(),
    )

    documents = list(await source.discover_documents())

    assert len(documents) == 2

    assert documents[0].ticker == "RELIANCE"
    assert documents[0].exchange == "NSE"

    assert documents[0].source_url == (
        "https://example.com/reports/annual-2026.pdf"
    )