from fintrace.retrieval.hybrid import HybridRetrievalService
from fintrace.retrieval.models import SearchResult
from fintrace.retrieval.reranker import Reranker


class RerankedRetrievalService:
    """Retrieve hybrid candidates and return reranked evidence."""

    def __init__(
        self,
        hybrid_retriever: HybridRetrievalService,
        reranker: Reranker,
    ) -> None:
        self._hybrid_retriever = hybrid_retriever
        self._reranker = reranker

    def search(
        self,
        query: str,
        limit: int = 5,
        candidate_limit: int = 20,
    ) -> list[SearchResult]:
        """Run hybrid retrieval followed by cross-encoder reranking."""
        if not query.strip():
            raise ValueError("Query must not be empty")

        if limit < 1:
            raise ValueError("Limit must be at least 1")

        if candidate_limit < 1:
            raise ValueError("Candidate limit must be at least 1")

        if limit > candidate_limit:
            raise ValueError(
                "Result limit cannot exceed candidate limit"
            )

        candidates = self._hybrid_retriever.search(
            query=query,
            limit=candidate_limit,
            candidate_limit=candidate_limit,
        )

        return self._reranker.rerank(
            query=query,
            candidates=candidates,
            limit=limit,
        )