import json
import os
from pathlib import Path

from dotenv import load_dotenv

from fintrace.evaluation.dataset import load_golden_dataset
from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.service import DenseRetrievalService
from fintrace.retrieval.sparse import BM25SparseRetriever
from fintrace.retrieval.fusion import reciprocal_rank_fusion
from fintrace.retrieval.reranker import CrossEncoderReranker
from fintrace.retrieval.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)
from fintrace.retrieval.qdrant_store import QdrantVectorStore

from fintrace.evaluation.benchmark import (
    run_retrieval_benchmark,
    write_benchmark_reports,
    validate_dataset_labels,
)


ROOT = Path(__file__).resolve().parents[1]

load_dotenv(ROOT / ".env")


def load_dataset():
    dataset_path = ROOT / "data" / "golden_questions.jsonl"

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}"
        )

    examples = load_golden_dataset(dataset_path)

    print(f"Loaded {len(examples)} evaluation questions.")

    if len(examples) != 80:
        raise ValueError(
            f"Expected 80 evaluation questions, got {len(examples)}"
        )

    return examples


def load_all_chunks(store):
    chunks = []
    offset = None

    while True:
        records, next_offset = store.client.scroll(
            collection_name=store.collection_name,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in records:
            payload = point.payload

            if not payload:
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


def main():
    examples = load_dataset()

    print(f"Loaded {len(examples)} evaluation questions.")

    qdrant_url = os.environ["QDRANT_URL"]
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv(
        "QDRANT_COLLECTION",
        "fintrace_chunks",
    )

    print("Connecting to Qdrant...")

    embedding_provider = SentenceTransformerEmbeddingProvider(
        model_name="BAAI/bge-small-en-v1.5",
        device="cpu",
    )

    vector_store = QdrantVectorStore(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=collection_name,
        vector_size=embedding_provider.dimension,
    )

    chunks = load_all_chunks(vector_store)

    print(f"Loaded {len(chunks)} chunks from Qdrant.")

    if not chunks:
        raise RuntimeError("Qdrant returned no indexed chunks.")

    indexed_ids = {
        chunk.chunk_id
        for chunk in chunks
    }

    validate_dataset_labels(examples, indexed_ids)

    print("Dataset labels validated successfully.")

    # Dense retrieval
    dense = DenseRetrievalService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    # BM25 retrieval
    sparse = BM25SparseRetriever()
    sparse.index(chunks)

    # Hybrid retrieval
    def hybrid_search(query, limit):
        dense_results = dense.search(
            query=query,
            limit=limit,
        )

        sparse_results = sparse.search(
            query=query,
            limit=limit,
        )

        return reciprocal_rank_fusion(
            result_lists=[
                dense_results,
                sparse_results,
            ],
            limit=limit,
            k=60,
        )

    # CrossEncoder reranker
    print("Loading CrossEncoder reranker...")

    reranker = CrossEncoderReranker(
        model_name="BAAI/bge-reranker-base",
        device="cpu",
        batch_size=16,
    )

    def reranked_search(query, limit):
        candidates = hybrid_search(
            query,
            limit,
        )

        return reranker.rerank(
            query=query,
            candidates=candidates,
            limit=limit,
        )

    retrievers = {
        "Dense": lambda query, limit: dense.search(
            query,
            limit=limit,
        ),
        "BM25": lambda query, limit: sparse.search(
            query,
            limit=limit,
        ),
        "Hybrid_RRF": hybrid_search,
        "Hybrid_RRF_Reranked": reranked_search,
    }

    print("\nRunning retrieval benchmark...")

    report = run_retrieval_benchmark(
        examples=examples,
        retrievers=retrievers,
        indexed_chunk_ids=indexed_ids,
        ks=(1, 3, 5, 10),
        candidate_limit=10,
    )

    json_path, markdown_path = write_benchmark_reports(
        report,
        ROOT / "reports" / "retrieval",
    )

    print("\nBenchmark completed successfully.")

    print("\nSUMMARY")

    for method, summary in report["summary"].items():
        print(f"\n{method}")
        print(f"Mean latency: {summary['mean_latency_ms']} ms")

        for metric, value in summary["metrics"].items():
            print(f"{metric}: {value}")

    print("\nReports saved:")
    print(json_path)
    print(markdown_path)


if __name__ == "__main__":
    main()