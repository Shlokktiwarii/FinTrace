from typing import Protocol

from fintrace.retrieval.models import IndexedChunk


class VectorStore(Protocol):
    """Interface for storing and searching vectorized chunks."""

    def upsert(self, chunks: list[IndexedChunk]) -> None:
        """Store or update indexed chunks."""
        ...

    def search(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[IndexedChunk]:
        """Return the most similar chunks."""
        ...