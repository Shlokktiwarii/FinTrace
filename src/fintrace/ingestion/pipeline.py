from collections.abc import Iterable

from fintrace.ingestion.assembler import DocumentAssembler
from fintrace.ingestion.downloader import AsyncDocumentDownloader
from fintrace.ingestion.models import (
    DiscoveredDocument,
    RawDocument,
)
from fintrace.ingestion.sources.base import DocumentSourceClient


class IngestionPipeline:
    """Orchestrate document discovery, downloading, and assembly."""

    def __init__(
        self,
        source: DocumentSourceClient,
        downloader: AsyncDocumentDownloader,
        assembler: DocumentAssembler,
    ) -> None:
        self.source = source
        self.downloader = downloader
        self.assembler = assembler

    async def run(self) -> list[RawDocument]:
        """Run the ingestion pipeline."""

        documents: Iterable[DiscoveredDocument] = (
            await self.source.discover_documents()
        )

        documents = list(documents)

        results = await self.downloader.download(
            document.source_url for document in documents
        )

        raw_documents: list[RawDocument] = []

        for document, result in zip(documents, results, strict=True):
            if result.error is not None:
                continue

            raw_documents.append(
                self.assembler.assemble(document, result)
            )

        return raw_documents