from collections.abc import Iterable

from fintrace.ingestion.models import RawDocument
from fintrace.ingestion.sources.base import DocumentSourceClient


class FakeSource:
    def fetch_documents(self) -> Iterable[RawDocument]:
        return []


def test_source_client_contract() -> None:
    source: DocumentSourceClient = FakeSource()

    documents = source.fetch_documents()

    assert list(documents) == []