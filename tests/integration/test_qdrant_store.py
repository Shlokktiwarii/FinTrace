from fintrace.retrieval.models import IndexedChunk
from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.qdrant_store import QdrantVectorStore
from qdrant_client import QdrantClient

def test_qdrant_vector_store() -> None:
    client = QdrantClient(":memory:")
    store = QdrantVectorStore(
        url=":memory:",
        collection_name="test_chunks",
        vector_size=3,
        client = client,
    )

    chunk = DocumentChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        company="Test Company",
        source_url="https://example.com/report.pdf",
        page_number=10,
        section="Financial Statements",
        text="Revenue increased significantly.",
    )

    indexed = IndexedChunk(
        chunk=chunk,
        embedding=(0.1, 0.2, 0.3),
    )

    store.upsert([indexed])

    results = store.search(
        query_embedding=[0.1, 0.2, 0.3],
        limit=1,
    )

    assert len(results) == 1
    assert results[0].chunk.chunk_id == "chunk-1"