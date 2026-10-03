from collections.abc import Iterable

from fintrace.ingestion.fetcher import AsyncHttpFetcher
from fintrace.ingestion.models import (
    DiscoveredDocument,
    DocumentSource,
    DocumentType,
)
from fintrace.ingestion.sources.parsers.report_links import ReportLinkParser


class CompanyReportSource:
    """Discover financial reports from a company's investor-relations page."""

    def __init__(
        self,
        company: str,
        ticker: str,
        exchange: str,
        reports_url: str,
        fetcher: AsyncHttpFetcher,
        parser: ReportLinkParser,
    ) -> None:
        self.company = company
        self.ticker = ticker
        self.exchange = exchange
        self.reports_url = reports_url
        self.fetcher = fetcher
        self.parser = parser

    async def discover_documents(self) -> Iterable[DiscoveredDocument]:
        """Discover financial reports from the company's reports page."""

        html_bytes = await self.fetcher.fetch(self.reports_url)
        html = html_bytes.decode("utf-8", errors="replace")

        report_links = self.parser.parse(
            html=html,
            base_url=self.reports_url,
        )

        documents: list[DiscoveredDocument] = []

        for index, report in enumerate(report_links):
            documents.append(
                DiscoveredDocument(
                    document_id=f"{self.ticker.lower()}-report-{index}",
                    company=self.company,
                    ticker=self.ticker,
                    exchange=self.exchange,
                    document_type=DocumentType.ANNUAL_REPORT,
                    source=DocumentSource.COMPANY,
                    source_url=report.url,
                )
            )

        return documents