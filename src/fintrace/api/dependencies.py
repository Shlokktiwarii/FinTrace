from fintrace.core.config import Settings
from fintrace.generation.provider_factory import create_llm_provider
from fintrace.generation.service import GenerationService
from fintrace.ingestion.models import DocumentChunk
from fintrace.ingestion.indexing_pipeline import DocumentIndexingPipeline
from fintrace.ingestion.parsers.pdf import PdfParser
from fintrace.ingestion.normalizer import DocumentNormalizer
from fintrace.ingestion.structure import DocumentStructureExtractor
from fintrace.ingestion.chunker import DocumentChunker

from fintrace.retrieval.hybrid import HybridRetrievalService
from fintrace.retrieval.qdrant_store import QdrantVectorStore
from fintrace.retrieval.reranker import CrossEncoderReranker
from fintrace.retrieval.reranking_service import RerankedRetrievalService
from fintrace.retrieval.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)
from fintrace.retrieval.service import DenseRetrievalService
from fintrace.retrieval.sparse import BM25SparseRetriever
from fintrace.verification.service import VerificationService
from fintrace.retrieval.indexer import ChunkIndexer


def load_all_chunks(store: QdrantVectorStore) -> list[DocumentChunk]:
    """Load all indexed chunks from Qdrant for the BM25 index."""

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


def initialize_services(settings: Settings) -> dict:
    """Initialize FinTrace application services."""

    # 1. Initialize embedding model.
    embedding_provider = SentenceTransformerEmbeddingProvider(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        batch_size=settings.embedding_batch_size,
    )

    # 2. Connect to Qdrant.
    vector_store = QdrantVectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection,
        vector_size=embedding_provider.dimension,
    )

    # Initialize document indexing pipeline.
    indexing_pipeline = DocumentIndexingPipeline(
    parser=PdfParser(),
    normalizer=DocumentNormalizer(),
    structure_extractor=DocumentStructureExtractor(),
    chunker=DocumentChunker(),
    indexer=ChunkIndexer(embedding_provider),
    vector_store=vector_store,
)

    # 3. Load indexed chunks.
    chunks = load_all_chunks(vector_store)

    if not chunks:
        raise RuntimeError("No indexed chunks found in Qdrant.")

    # 4. Initialize dense retrieval.
    dense_retriever = DenseRetrievalService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    # 5. Build BM25 index.
    sparse_retriever = BM25SparseRetriever()
    sparse_retriever.index(chunks)

    # 6. Initialize hybrid retrieval.
    hybrid_retriever = HybridRetrievalService(
        dense_retriever=dense_retriever,
        sparse_retriever=sparse_retriever,
        rrf_k=60,
    )

    # 7. Initialize reranker.
    reranker = CrossEncoderReranker(
        model_name="BAAI/bge-reranker-base",
        device=settings.embedding_device,
        batch_size=16,
    )

    retrieval_service = RerankedRetrievalService(
        hybrid_retriever=hybrid_retriever,
        reranker=reranker,
    )

    # 8. Initialize LLM provider.
    llm_provider = create_llm_provider(settings)

    generation_service = GenerationService(
        provider=llm_provider,
    )

    # 9. Initialize verification.
    verification_service = VerificationService()

    return {
        "embedding_provider": embedding_provider,
        "vector_store": vector_store,
        "chunks": chunks,
        "sparse_retriever": sparse_retriever,
        "indexing_pipeline": indexing_pipeline,
        "retrieval": retrieval_service,
        "generation": generation_service,
        "verification": verification_service,
    }