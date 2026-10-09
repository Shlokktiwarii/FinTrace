from fintrace.retrieval.embeddings import EmbeddingProvider
from fintrace.retrieval.models import SearchResult
from fintrace.retrieval.vector_store import VectorStore


class DenseRetrievalService:
    """Retrieve relevant document chunks using dense vectors."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Embed a query and retrieve similar document chunks."""

        if not query.strip():
            raise ValueError("Query must not be empty")

        if limit < 1:
            raise ValueError("Limit must be at least 1")

        query_embedding = self.embedding_provider.embed(query)

        return self.vector_store.search(
            query_embedding=query_embedding,
            limit=limit,
        )

        query_embedding = self._embedding_provider.embed(query)

        if len(query_embedding) != self._embedding_provider.dimension:
            raise ValueError("Query embedding has an unexpected dimension")

        return self._vector_store.search(
            query_embedding=query_embedding,
            limit=limit,
            )