import pytest

from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.fusion import reciprocal_rank_fusion
from fintrace.retrieval.hybrid import HybridRetrievalService
from fintrace.retrieval.models import SearchResult
from fintrace.retrieval.sparse import BM25SparseRetriever


def make_chunk(
    chunk_id: str,
    text: str,
    page_number: int,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id="report-2025",
        company="Example Limited",
        source_url="https://example.com/report.pdf",
        page_number=page_number,
        section="Financial Statements",
        text=text,
    )


class FakeDenseRetriever:
    """Predictable dense results for hybrid integration tests."""

    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results
        self.received_query: str | None = None
        self.received_limit: int | None = None

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[SearchResult]:
        self.received_query = query
        self.received_limit = limit
        return self.results[:limit]


def test_bm25_retrieves_relevant_financial_chunks() -> None:
    revenue = make_chunk(
        "revenue",
        "Revenue from operations increased during FY2025.",
        10,
    )

    debt = make_chunk(
        "debt",
        "Outstanding borrowings and total debt increased.",
        20,
    )

    governance = make_chunk(
        "governance",
        "The board reviewed corporate governance policies.",
        30,
    )

    retriever = BM25SparseRetriever()

    assert retriever.index([revenue, debt, governance]) == 3

    results = retriever.search(
        "revenue operations FY2025",
        limit=3,
    )

    assert results
    assert results[0].chunk.chunk_id == "revenue"
    assert results[0].chunk.page_number == 10
    assert results[0].chunk.source_url == (
        "https://example.com/report.pdf"
    )


def test_bm25_returns_no_results_for_unmatched_terms() -> None:
    retriever = BM25SparseRetriever()

    retriever.index(
        [
            make_chunk(
                "revenue",
                "Revenue increased during FY2025.",
                10,
            )
        ]
    )

    results = retriever.search(
        "quantum spacecraft",
        limit=5,
    )

    assert results == []


def test_rrf_combines_rankings_and_deduplicates_chunks() -> None:
    chunk_a = make_chunk("a", "Revenue increased.", 10)
    chunk_b = make_chunk("b", "Debt increased.", 20)
    chunk_c = make_chunk("c", "Cash flow improved.", 30)

    dense_results = [
        SearchResult(chunk=chunk_a, score=0.95),
        SearchResult(chunk=chunk_b, score=0.80),
    ]

    sparse_results = [
        SearchResult(chunk=chunk_b, score=8.5),
        SearchResult(chunk=chunk_c, score=5.0),
    ]

    fused = reciprocal_rank_fusion(
        [dense_results, sparse_results],
        limit=3,
    )

    assert len(fused) == 3
    assert fused[0].chunk.chunk_id == "b"
    assert len({result.chunk.chunk_id for result in fused}) == 3

    # Chunk B ranks second in dense retrieval and first in sparse retrieval.
    expected_score = (1 / 62) + (1 / 61)

    assert fused[0].score == pytest.approx(expected_score)


def test_hybrid_retrieval_combines_dense_and_bm25() -> None:
    revenue = make_chunk(
        "revenue",
        "Revenue from operations increased during FY2025.",
        10,
    )

    debt = make_chunk(
        "debt",
        "Outstanding borrowings and total debt increased.",
        20,
    )

    cash_flow = make_chunk(
        "cash-flow",
        "Operating cash flow improved during the year.",
        25,
    )

    governance = make_chunk(
        "governance",
        "The board reviewed corporate governance policies.",
        30,
    )

    sparse = BM25SparseRetriever()
    sparse.index([revenue, debt, cash_flow, governance])

    dense = FakeDenseRetriever(
        [
            SearchResult(chunk=debt, score=0.95),
            SearchResult(chunk=revenue, score=0.85),
            SearchResult(chunk=cash_flow, score=0.70),
        ]
    )

    hybrid = HybridRetrievalService(
        dense_retriever=dense,
        sparse_retriever=sparse,
    )

    results = hybrid.search(
        "revenue from operations FY2025",
        limit=3,
        candidate_limit=4,
    )

    assert results
    assert len(results) <= 3
    assert len({
        result.chunk.chunk_id
        for result in results
    }) == len(results)

    assert dense.received_query == "revenue from operations FY2025"
    assert dense.received_limit == 4

    result_ids = [result.chunk.chunk_id for result in results]

    assert "revenue" in result_ids
    assert all(result.score > 0 for result in results)