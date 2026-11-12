import os
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client.models import Filter, FieldCondition, MatchValue

from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)
from fintrace.retrieval.qdrant_store import QdrantVectorStore
from fintrace.retrieval.service import DenseRetrievalService
from fintrace.retrieval.sparse import BM25SparseRetriever
from fintrace.retrieval.hybrid import HybridRetrievalService
from fintrace.retrieval.reranker import CrossEncoderReranker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=True)

QUERY = "What was Reliance Industries' revenue from operations in FY2025?"

DOCUMENT_ID = "bd088224-81f0-59e6-b14b-7449e65f9278"

TOP_K = 10
CANDIDATE_LIMIT = 20


def load_document_chunks(store: QdrantVectorStore) -> list[DocumentChunk]:
    """Load chunks for the selected document without server-side filtering."""

    chunks = []
    offset = None

    while True:
        points, next_offset = store.client.scroll(
            collection_name=store.collection_name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            payload = point.payload

            if payload["document_id"] != DOCUMENT_ID:
                continue

            chunks.append(
                DocumentChunk(
                    chunk_id=str(payload["chunk_id"]),
                    document_id=str(payload["document_id"]),
                    company=str(payload["company"]),
                    source_url=str(payload["source_url"]),
                    page_number=int(payload["page_number"]),
                    section=payload.get("section"),
                    text=str(payload["text"]),
                )
            )

        if next_offset is None:
            break

        offset = next_offset

    return chunks



def print_results(name, results):
    print("\n" + "=" * 90)
    print(name)
    print("=" * 90)

    if not results:
        print("No results found.")
        return

    for rank, result in enumerate(results, start=1):
        chunk = result.chunk

        print(f"\nRank: {rank} | Score: {result.score:.5f}")
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"Page: {chunk.page_number}")
        print(f"Section: {chunk.section}")
        print(f"Text: {chunk.text[:700]}")
        print("-" * 80)


def main():
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv(
        "QDRANT_COLLECTION",
        "fintrace_chunks",
    )

    if not qdrant_url or not qdrant_api_key:
        raise ValueError("QDRANT_URL or QDRANT_API_KEY is missing.")

    print("Initializing embedding model...")

    embedding_provider = SentenceTransformerEmbeddingProvider(
        model_name="BAAI/bge-small-en-v1.5",
        device="cpu",
    )

    store = QdrantVectorStore(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=collection_name,
        vector_size=384,
    )

    print("Loading Reliance document chunks...")

    chunks = load_document_chunks(store)

    print(f"Loaded {len(chunks)} chunks.")

    if not chunks:
        raise RuntimeError("No chunks found for the selected document.")

    # 1. Dense retrieval
    dense_retriever = DenseRetrievalService(
        embedding_provider=embedding_provider,
        vector_store=store,
    )

    dense_results = dense_retriever.search(
        QUERY,
        limit=TOP_K,
    )

    print_results("1. DENSE RETRIEVAL", dense_results)

    # 2. BM25 sparse retrieval
    sparse_retriever = BM25SparseRetriever()

    indexed_count = sparse_retriever.index(chunks)

    print(f"\nBM25 indexed {indexed_count} chunks.")

    sparse_results = sparse_retriever.search(
        QUERY,
        limit=TOP_K,
    )

    print_results("2. BM25 SPARSE RETRIEVAL", sparse_results)

    # 3. Hybrid retrieval: Dense + BM25 + RRF
    hybrid_retriever = HybridRetrievalService(
        dense_retriever=dense_retriever,
        sparse_retriever=sparse_retriever,
        rrf_k=60,
    )

    hybrid_results = hybrid_retriever.search(
        QUERY,
        limit=TOP_K,
        candidate_limit=CANDIDATE_LIMIT,
    )

    print_results("3. HYBRID RETRIEVAL (RRF)", hybrid_results)

    # 4. Hybrid retrieval + Cross-Encoder reranking
    print("\nLoading cross-encoder reranker...")

    reranker = CrossEncoderReranker(
        model_name="BAAI/bge-reranker-base",
        device="cpu",
        batch_size=16,
    )

    candidates = hybrid_retriever.search(
        QUERY,
        limit=CANDIDATE_LIMIT,
        candidate_limit=CANDIDATE_LIMIT,
    )

    reranked_results = reranker.rerank(
        query=QUERY,
        candidates=candidates,
        limit=TOP_K,
    )

    print_results(
        "4. HYBRID + CROSS-ENCODER RERANKING",
        reranked_results,
    )


if __name__ == "__main__":
    main()
