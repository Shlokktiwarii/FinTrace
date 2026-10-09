from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.models import SearchResult
from fintrace.retrieval.service import DenseRetrievalService


class FakeEmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeVectorStore:
    def __init__(self) -> None:
        self.received_embedding: list[float] | None = None
        self.received_limit: int | None = None

    def upsert(self, chunks: list) -> None:
        pass

    def search(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[SearchResult]:
        self.received_embedding = query_embedding
        self.received_limit = limit

        return [
            SearchResult(
                chunk=DocumentChunk(
                    chunk_id="reliance-2026-ar-0",
                    document_id="reliance-2026-ar",
                    company="Reliance Industries Limited",
                    source_url="https://example.com/report.pdf",
                    page_number=42,
                    section="Financial Statements",
                    text="Revenue increased during the financial year.",
                ),
                score=0.95,
            )
        ]


def test_dense_retrieval_flow() -> None:
    embedding_provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()

    retrieval = DenseRetrievalService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    results = retrieval.search(
        query="What happened to revenue?",
        limit=3,
    )

    assert vector_store.received_embedding == [0.1, 0.2, 0.3]
    assert vector_store.received_limit == 3

    assert len(results) == 1
    assert results[0].chunk.company == "Reliance Industries Limited"
    assert results[0].chunk.page_number == 42
    assert results[0].score == 0.95