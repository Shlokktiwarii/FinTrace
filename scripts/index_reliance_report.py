import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from dotenv import load_dotenv

from fintrace.ingestion.chunker import DocumentChunker
from fintrace.ingestion.indexing_pipeline import DocumentIndexingPipeline
from fintrace.ingestion.models import (
    DocumentSource,
    DocumentType,
    RawDocument,
)
from fintrace.ingestion.normalizer import DocumentNormalizer
from fintrace.ingestion.parsers.pdf import PdfParser
from fintrace.ingestion.structure import DocumentStructureExtractor

from fintrace.retrieval.indexer import ChunkIndexer
from fintrace.retrieval.qdrant_store import QdrantVectorStore
from fintrace.retrieval.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Explicitly load .env from the project root.
load_dotenv(PROJECT_ROOT / ".env", override=True)

PDF_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "reliance"
    / "reliance_fy2025_fresh.pdf"
)

SOURCE_URL = (
    "https://www.ril.com/ar2024-25/pdf/"
    "RIL-Integrated-Annual-Report-2024-25.pdf"
)

COMPANY = "Reliance Industries Limited"
TICKER = "RELIANCE"


# --------------------------------------------------
# Main indexing function
# --------------------------------------------------

def main() -> None:

    print("\n========== FINTRACE DOCUMENT INDEXING ==========\n")

    # 1. Validate environment variables

    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    collection_name = os.getenv(
        "QDRANT_COLLECTION",
        "fintrace_chunks",
    )

    if not qdrant_url:
        raise ValueError("QDRANT_URL is missing from .env")

    if not qdrant_api_key:
        raise ValueError("QDRANT_API_KEY is missing from .env")

    print(f"Qdrant URL: {qdrant_url}")
    print(f"Collection: {collection_name}")

    # 2. Validate PDF

    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"Annual report not found: {PDF_PATH}"
        )

    pdf_content = PDF_PATH.read_bytes()

    print(f"\nPDF found: {PDF_PATH.name}")
    print(f"PDF size: {len(pdf_content) / (1024 * 1024):.2f} MB")

    # 3. Create a stable document ID

    document_id = str(
        uuid5(
            NAMESPACE_URL,
            "RELIANCE-FY2025-ANNUAL-REPORT",
        )
    )

    # 4. Create RawDocument

    document = RawDocument(
        document_id=document_id,
        company=COMPANY,
        ticker=TICKER,
        exchange="NSE",
        document_type=DocumentType.ANNUAL_REPORT,
        source=DocumentSource.COMPANY,
        source_url=SOURCE_URL,
        content=pdf_content,
        fetched_at=datetime.now(timezone.utc),
    )

    print("\nRaw document created.")

    # 5. Initialize embedding provider

    print("\nLoading embedding model...")

    embedding_provider = SentenceTransformerEmbeddingProvider(
        model_name="BAAI/bge-small-en-v1.5",
        device="cpu",
    )

    print(f"Embedding dimension: {embedding_provider.dimension}")

    # 6. Initialize Qdrant vector store

    print("\nConnecting to Qdrant Cloud...")

    vector_store = QdrantVectorStore(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=collection_name,
        vector_size=embedding_provider.dimension,
    )

    print("Qdrant connection initialized.")

    # 7. Initialize indexing pipeline

    pipeline = DocumentIndexingPipeline(
        parser=PdfParser(),
        normalizer=DocumentNormalizer(),
        structure_extractor=DocumentStructureExtractor(),
        chunker=DocumentChunker(max_characters=1500),
        indexer=ChunkIndexer(embedding_provider),
        vector_store=vector_store,
    )

    print("\nIndexing pipeline initialized.")

    # 8. Execute indexing

    print("\nStarting document indexing...")

    indexed_count = pipeline.index_document(document)

    # 9. Display results

    print("\n========== INDEXING COMPLETE ==========\n")

    print(f"Company: {COMPANY}")
    print(f"Document: FY2024-25 Annual Report")
    print(f"Document ID: {document_id}")
    print(f"Collection: {collection_name}")
    print(f"Chunks indexed: {indexed_count}")

    print("\n========================================")


if __name__ == "__main__":
    main()