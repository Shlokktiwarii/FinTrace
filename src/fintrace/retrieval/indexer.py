from collections.abc import Iterable

from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.embeddings import EmbeddingProvider
from fintrace.retrieval.models import IndexedChunk


class ChunkIndexer:
    """Prepare document chunks for vector indexing."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.embedding_provider = embedding_provider

    def index(
        self,
        chunks: Iterable[DocumentChunk],
    ) -> list[IndexedChunk]:
        """Generate embeddings for document chunks."""

        indexed_chunks: list[IndexedChunk] = []

        for chunk in chunks:
            embedding = self.embedding_provider.embed(
                chunk.text
            )

            indexed_chunks.append(
                IndexedChunk(
                    chunk=chunk,
                    embedding=tuple(embedding),
                )
            )

        return indexed_chunks