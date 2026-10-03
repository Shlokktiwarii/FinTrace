import pytest

from fintrace.ingestion.downloader import AsyncDocumentDownloader
from fintrace.ingestion.fetcher import FetchError
from fintrace.ingestion.models import (
    DiscoveredDocument,
    DocumentSource,
    DocumentType,
)
from fintrace.ingestion.sources.base import DocumentSourceClient


class FakeSource:
    async def discover_documents(self) -> list[DiscoveredDocument]:
        return [
            DiscoveredDocument(
                document_id="reliance-2026-ar",
                company="Reliance Industries Limited",
                ticker="RELIANCE",
                exchange="NSE",
                document_type=DocumentType.ANNUAL_REPORT,
                source=DocumentSource.NSE,
                source_url="https://example.com/reliance-2026.pdf",
            ),
            DiscoveredDocument(
                document_id="tcs-2026-ar",
                company="Tata Consultancy Services Limited",
                ticker="TCS",
                exchange="NSE",
                document_type=DocumentType.ANNUAL_REPORT,
                source=DocumentSource.NSE,
                source_url="https://example.com/tcs-2026.pdf",
            ),
        ]


class FakeFetcher:
    async def fetch(self, url: str) -> bytes:
        return f"content for {url}".encode()


@pytest.mark.asyncio
async def test_source_discovery_to_download() -> None:
    source: DocumentSourceClient = FakeSource()
    fetcher = FakeFetcher()

    documents = list(await source.discover_documents())

    downloader = AsyncDocumentDownloader(
        fetcher=fetcher,
        max_concurrency=2,
    )

    results = await downloader.download(
        document.source_url for document in documents
    )

    assert len(results) == 2

    assert results[0].url == documents[0].source_url
    assert results[0].content == (
        b"content for https://example.com/reliance-2026.pdf"
    )
    assert results[0].error is None

    assert results[1].url == documents[1].source_url
    assert results[1].content == (
        b"content for https://example.com/tcs-2026.pdf"
    )
    assert results[1].error is None