from typing import Protocol

from sentence_transformers import CrossEncoder

from fintrace.retrieval.models import SearchResult


class Reranker(Protocol):
    """Interface for reranking retrieved document chunks."""

    def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
        limit: int | None = None,
    ) -> list[SearchResult]:
        ...


class CrossEncoderReranker:
    """Rerank candidate chunks using a cross-encoder model."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: str = "cpu",
        batch_size: int = 16,
        model: CrossEncoder | None = None,
    ) -> None:
        if batch_size < 1:
            raise ValueError("Batch size must be at least 1")

        self._model = model or CrossEncoder(
            model_name,
            device=device,
        )
        self._batch_size = batch_size

    def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
        limit: int | None = None,
    ) -> list[SearchResult]:
        """Return candidates ordered by cross-encoder relevance."""
        if not query.strip():
            raise ValueError("Query must not be empty")

        if limit is not None and limit < 1:
            raise ValueError("Limit must be at least 1")

        if not candidates:
            return []

        pairs = [
            (query, candidate.chunk.text)
            for candidate in candidates
        ]

        scores = self._model.predict(
            pairs,
            batch_size=self._batch_size,
            show_progress_bar=False,
        )

        if len(scores) != len(candidates):
            raise ValueError(
                "Reranker returned an unexpected number of scores"
            )

        reranked = [
            SearchResult(
                chunk=candidate.chunk,
                score=float(score),
            )
            for candidate, score in zip(
                candidates,
                scores,
                strict=True,
            )
        ]

        reranked.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        if limit is not None:
            reranked = reranked[:limit]

        return reranked