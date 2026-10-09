from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.embeddings import EmbeddingProvider
from fintrace.retrieval.models import IndexedChunk
from fintrace.retrieval.vector_store import VectorStore


class IndexingService:
    """Embed document chunks and store them in the vector database."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def index_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> int:
        """Index chunks and return the number successfully submitted."""
        if not chunks:
            return 0

        if any(not chunk.text.strip() for chunk in chunks):
            raise ValueError("Chunks must not contain empty text")

        vectors = self._embedding_provider.embed_many(
            [chunk.text for chunk in chunks]
        )

        if len(vectors) != len(chunks):
            raise ValueError(
                "Embedding provider returned an unexpected number of vectors"
            )

        expected_dimension = self._embedding_provider.dimension

        indexed_chunks: list[IndexedChunk] = []

        for chunk, vector in zip(chunks, vectors, strict=True):
            if len(vector) != expected_dimension:
                raise ValueError(
                    f"Expected embedding dimension {expected_dimension}, "
                    f"received {len(vector)}"
                )

            indexed_chunks.append(
                IndexedChunk(
                    chunk=chunk,
                    embedding=tuple(vector),
                )
            )

        self._vector_store.upsert(indexed_chunks)

        return len(indexed_chunks)