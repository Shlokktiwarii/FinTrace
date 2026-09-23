from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class DocumentSource(StrEnum):
    """Origin of a financial document."""

    NSE = "nse"
    BSE = "bse"
    COMPANY = "company"


class DocumentType(StrEnum):
    """Type of financial document."""

    ANNUAL_REPORT = "annual_report"
    FINANCIAL_RESULT = "financial_result"
    CORPORATE_FILING = "corporate_filing"
    EARNINGS_PRESENTATION = "earnings_presentation"


@dataclass(frozen=True)
class RawDocument:
    """A document fetched from an external financial source."""

    document_id: str
    company: str
    ticker: str | None
    exchange: str | None
    document_type: DocumentType
    source: DocumentSource
    source_url: str
    content: bytes
    fetched_at: datetime