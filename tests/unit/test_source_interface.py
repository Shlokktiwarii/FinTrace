import pytest

from fintrace.ingestion.models import DiscoveredDocument
from fintrace.ingestion.sources.base import DocumentSourceClient


class FakeSource:
    async def discover_documents(self) -> list[DiscoveredDocument]:
        return []


@pytest.mark.asyncio
async def test_source_client_contract() -> None:
    source: DocumentSourceClient = FakeSource()

    documents = await source.discover_documents()

    assert list(documents) == []