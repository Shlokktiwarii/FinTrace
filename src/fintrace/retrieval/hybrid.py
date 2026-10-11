from fintrace.retrieval.fusion import reciprocal_rank_fusion
from fintrace.retrieval.models import SearchResult
from fintrace.retrieval.service import DenseRetrievalService
from fintrace.retrieval.sparse import BM25SparseRetriever


class HybridRetrievalService:
    """Combine dense and sparse retrieval using RRF."""

    def __init__(
        self,
        dense_retriever: DenseRetrievalService,
        sparse_retriever: BM25SparseRetriever,
        rrf_k: int = 60,
    ) -> None:
        if rrf_k < 1:
            raise ValueError("RRF k must be at least 1")

        self._dense_retriever = dense_retriever
        self._sparse_retriever = sparse_retriever
        self._rrf_k = rrf_k

    def search(
        self,
        query: str,
        limit: int = 5,
        candidate_limit: int = 20,
    ) -> list[SearchResult]:
        """Retrieve candidates from both systems and fuse their rankings."""
        if not query.strip():
            raise ValueError("Query must not be empty")

        if limit < 1:
            raise ValueError("Limit must be at least 1")

        if candidate_limit < 1:
            raise ValueError("Candidate limit must be at least 1")

        dense_results = self._dense_retriever.search(
            query=query,
            limit=candidate_limit,
        )

        sparse_results = self._sparse_retriever.search(
            query=query,
            limit=candidate_limit,
        )

        return reciprocal_rank_fusion(
            result_lists=[
                dense_results,
                sparse_results,
            ],
            limit=limit,
            k=self._rrf_k,
        )