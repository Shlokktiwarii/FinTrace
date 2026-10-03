import pytest

from fintrace.ingestion.assembler import DocumentAssembler
from fintrace.ingestion.downloader import AsyncDocumentDownloader
from fintrace.ingestion.models import (
    DiscoveredDocument,
    DocumentSource,
    DocumentType,
)
from fintrace.ingestion.pipeline import IngestionPipeline


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
                source_url="https://example.com/reliance.pdf",
            )
        ]


class FakeFetcher:
    async def fetch(self, url: str) -> bytes:
        return b"financial report"


@pytest.mark.asyncio
async def test_ingestion_pipeline() -> None:
    pipeline = IngestionPipeline(
        source=FakeSource(),
        downloader=AsyncDocumentDownloader(
            fetcher=FakeFetcher(),
            max_concurrency=2,
        ),
        assembler=DocumentAssembler(),
    )

    documents = await pipeline.run()

    assert len(documents) == 1
    assert documents[0].document_id == "reliance-2026-ar"
    assert documents[0].content == b"financial report"