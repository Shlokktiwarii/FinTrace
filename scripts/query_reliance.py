import os
from pathlib import Path

from dotenv import load_dotenv

from fintrace.retrieval.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)
from fintrace.retrieval.qdrant_store import QdrantVectorStore


# Load project environment
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=True)


def main() -> None:
    query = "What was Reliance Industries' revenue in FY2025?"

    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv(
        "QDRANT_COLLECTION",
        "fintrace_chunks",
    )

    if not qdrant_url or not qdrant_api_key:
        raise RuntimeError("Missing Qdrant environment variables.")

    print("\nInitializing embedding model...")

    embedding_provider = SentenceTransformerEmbeddingProvider(
        model_name="BAAI/bge-small-en-v1.5",
        device="cpu",
    )

    print("Connecting to Qdrant...")

    vector_store = QdrantVectorStore(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=collection_name,
        vector_size=384,
    )

    print(f"\nQuery: {query}")
    print("Retrieving top 10 chunks...\n")

    query_embedding = embedding_provider.embed(query)

    results = vector_store.search(
        query_embedding=query_embedding,
        limit=10,
    )

    if not results:
        print("No results found.")
        return

    for rank, result in enumerate(results, start=1):
        chunk = result.chunk

        print("=" * 90)
        print(f"RANK: {rank}")
        print(f"SCORE: {result.score:.4f}")
        print(f"CHUNK ID: {chunk.chunk_id}")
        print(f"DOCUMENT ID: {chunk.document_id}")
        print(f"COMPANY: {chunk.company}")
        print(f"PAGE: {chunk.page_number}")
        print(f"SECTION: {chunk.section}")
        print("\nTEXT:")
        print(chunk.text)
        print()


if __name__ == "__main__":
    main()