from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbeddingProvider:
    """Generate normalized embeddings with a local Sentence Transformer."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        device: str = "cpu",
        batch_size: int = 32,
    ) -> None:
        if batch_size < 1:
            raise ValueError("Batch size must be at least 1")

        self._model = SentenceTransformer(
            model_name,
            device=device,
        )
        self._batch_size = batch_size
        self._dimension = self._model.get_sentence_embedding_dimension()

        if self._dimension is None:
            raise ValueError("Embedding model has no known output dimension")

    @property
    def dimension(self) -> int:
        """Return the model's embedding dimension."""
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        if not text.strip():
            raise ValueError("Text must not be empty")

        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        if any(not text.strip() for text in texts):
            raise ValueError("Texts must not contain empty strings")

        vectors = self._model.encode(
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return vectors.tolist()