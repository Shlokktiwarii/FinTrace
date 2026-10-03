import pytest

from fintrace.ingestion.assembler import DocumentAssembler
from fintrace.ingestion.downloader import AsyncDocumentDownloader
from fintrace.ingestion.fetcher import AsyncHttpFetcher
from fintrace.ingestion.pipeline import IngestionPipeline
from fintrace.ingestion.sources.company_reports import CompanyReportSource
from fintrace.ingestion.sources.parsers.report_links import ReportLinkParser


class FakeFetcher(AsyncHttpFetcher):
    async def fetch(self, url: str) -> bytes:
        if url.endswith("/investor/"):
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

        return b"%PDF-fake-financial-document%"


@pytest.mark.asyncio
async def test_company_ingestion_flow() -> None:
    fetcher = FakeFetcher()

    source = CompanyReportSource(
        company="Reliance Industries Limited",
        ticker="RELIANCE",
        exchange="NSE",
        reports_url="https://example.com/investor/",
        fetcher=fetcher,
        parser=ReportLinkParser(),
    )

    pipeline = IngestionPipeline(
        source=source,
        downloader=AsyncDocumentDownloader(
            fetcher=fetcher,
            max_concurrency=2,
        ),
        assembler=DocumentAssembler(),
    )

    documents = await pipeline.run()

    assert len(documents) == 2

    assert documents[0].company == "Reliance Industries Limited"
    assert documents[0].ticker == "RELIANCE"
    assert documents[0].content == b"%PDF-fake-financial-document%"