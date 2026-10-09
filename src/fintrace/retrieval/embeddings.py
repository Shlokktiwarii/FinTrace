from typing import Protocol


class EmbeddingProvider(Protocol):
    """Interface for text embedding providers."""

    @property
    def dimension(self) -> int:
        ...

    def embed(self, text: str) -> list[float]:
        ...

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        ...