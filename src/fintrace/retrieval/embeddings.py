from typing import Protocol


class EmbeddingProvider(Protocol):
    """Interface for generating text embeddings."""

    def embed(self, text: str) -> list[float]:
        """Generate an embedding for text."""
        ...