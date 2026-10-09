import os
from uuid import uuid4

import pytest
from qdrant_client import QdrantClient

from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.indexing_service import IndexingService
from fintrace.retrieval.qdrant_store import QdrantVectorStore
from fintrace.retrieval.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)
from fintrace.retrieval.service import DenseRetrievalService


@pytest.mark.skipif(
    os.getenv("RUN_REAL_MODEL_TESTS") != "1",
    reason="Set RUN_REAL_MODEL_TESTS=1 to run model integration tests",
)
def test_real_dense_retrieval_finds_relevant_financial_chunk() -> None:
    provider = SentenceTransformerEmbeddingProvider(
        model_name="BAAI/bge-small-en-v1.5",
        device="cpu",
    )

    client = QdrantClient(":memory:")

    store = QdrantVectorStore(
        url=":memory:",
        collection_name=f"real_test_{uuid4().hex}",
        vector_size=provider.dimension,
        client=client,
    )

    indexer = IndexingService(provider, store)
    retriever = DenseRetrievalService(provider, store)

    chunks = [
        DocumentChunk(
            chunk_id="revenue",
            document_id="report-2025",
            company="Example Limited",
            source_url="https://example.com/report.pdf",
            page_number=10,
            section="Financial Performance",
            text=(
                "Revenue from operations increased to "
                "1200 crore rupees in financial year 2025."
            ),
        ),
        DocumentChunk(
            chunk_id="governance",
            document_id="report-2025",
            company="Example Limited",
            source_url="https://example.com/report.pdf",
            page_number=30,
            section="Corporate Governance",
            text=(
                "The board reviewed governance policies, "
                "director independence, and committee responsibilities."
            ),
        ),
        DocumentChunk(
            chunk_id="environment",
            document_id="report-2025",
            company="Example Limited",
            source_url="https://example.com/report.pdf",
            page_number=40,
            section="Sustainability",
            text=(
                "The company discussed water conservation, "
                "renewable energy, and waste reduction initiatives."
            ),
        ),
    ]

    try:
        indexer.index_chunks(chunks)

        results = retriever.search(
            "What was the company's revenue from operations in FY2025?",
            limit=3,
        )

        assert results

        result_ids = [result.chunk.chunk_id for result in results]

        assert result_ids[0] == "revenue"
        assert results[0].chunk.page_number == 10
        assert results[0].chunk.source_url == (
            "https://example.com/report.pdf"
        )
    finally:
        client.close()