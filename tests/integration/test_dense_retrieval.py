from uuid import uuid4

from qdrant_client import QdrantClient

from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.indexing_service import IndexingService
from fintrace.retrieval.models import SearchResult
from fintrace.retrieval.qdrant_store import QdrantVectorStore
from fintrace.retrieval.service import DenseRetrievalService


class FakeEmbeddingProvider:
    """Deterministic embedding provider for integration tests."""

    dimension = 3

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Text must not be empty")

        return [1.0, 0.0, 0.0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def test_index_and_retrieve_document_chunks() -> None:
    client = QdrantClient(":memory:")

    store = QdrantVectorStore(
        url=":memory:",
        collection_name=f"test_{uuid4().hex}",
        vector_size=3,
        client=client,
    )

    embeddings = FakeEmbeddingProvider()
    indexer = IndexingService(embeddings, store)
    retriever = DenseRetrievalService(embeddings, store)

    chunks = [
        DocumentChunk(
            chunk_id="revenue-chunk",
            document_id="annual-report-2025",
            company="Example Limited",
            source_url="https://example.com/report.pdf",
            page_number=12,
            section="Financial Statements",
            text="Revenue from operations increased during FY2025.",
        ),
        DocumentChunk(
            chunk_id="risk-chunk",
            document_id="annual-report-2025",
            company="Example Limited",
            source_url="https://example.com/report.pdf",
            page_number=28,
            section="Risk Factors",
            text="The company faces market and operational risks.",
        ),
    ]

    try:
        indexed_count = indexer.index_chunks(chunks)

        assert indexed_count == 2

        results = retriever.search(
            "What happened to revenue?",
            limit=2,
        )

        assert len(results) == 2

        revenue_result = next(
            result
            for result in results
            if result.chunk.chunk_id == "revenue-chunk"
        )

        assert isinstance(revenue_result, SearchResult)
        assert revenue_result.chunk.document_id == "annual-report-2025"
        assert revenue_result.chunk.page_number == 12
        assert revenue_result.chunk.section == "Financial Statements"
        assert revenue_result.chunk.source_url == (
            "https://example.com/report.pdf"
        )
    finally:
        client.close()