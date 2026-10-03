from collections.abc import Iterable

from fintrace.ingestion.models import (
    DiscoveredDocument,
    DocumentSource,
    DocumentType,
)


class CompanyReportSource:
    """Discover financial reports published by a company."""

    def __init__(
        self,
        company: str,
        ticker: str,
        exchange: str,
        reports: Iterable[DiscoveredDocument],
    ) -> None:
        self.company = company
        self.ticker = ticker
        self.exchange = exchange
        self._reports = list(reports)

    def discover_documents(self) -> Iterable[DiscoveredDocument]:
        """Return discovered company financial reports."""

        return self._reports