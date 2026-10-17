import numpy as np
import pytest

from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.hybrid import HybridRetrievalService
from fintrace.retrieval.models import SearchResult
from fintrace.retrieval.reranker import CrossEncoderReranker
from fintrace.retrieval.reranking_service import RerankedRetrievalService


def make_result(
    chunk_id: str,
    text: str,
    page_number: int,
    score: float,
) -> SearchResult:
    chunk = DocumentChunk(
        chunk_id=chunk_id,
        document_id="report-2025",
        company="Example Limited",
        source_url="https://example.com/report.pdf",
        page_number=page_number,
        section="Financial Statements",
        text=text,
    )

    return SearchResult(chunk=chunk, score=score)


class FakeCrossEncoder:
    """Return deterministic scores based on passage content."""

    def predict(
        self,
        sentences,
        *,
        batch_size: int,
        show_progress_bar: bool,
    ) -> np.ndarray:
        assert batch_size == 16
        assert show_progress_bar is False

        scores = []

        for query, passage in sentences:
            passage = passage.lower()

            if "revenue from operations" in passage:
                scores.append(0.95)
            elif "cash flow" in passage:
                scores.append(0.65)
            else:
                scores.append(0.10)

        return np.array(scores)


class FakeHybridRetriever:
    """Return controlled candidates for integration tests."""

    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results
        self.received_query = None
        self.received_limit = None

    def search(
        self,
        query: str,
        limit: int = 5,
        candidate_limit: int = 20,
    ) -> list[SearchResult]:
        self.received_query = query
        self.received_limit = limit
        return self.results[:limit]


def test_cross_encoder_reranks_candidates_and_preserves_metadata():
    candidates = [
        make_result(
            "governance",
            "The board reviewed governance policies.",
            30,
            0.90,
        ),
        make_result(
            "cash-flow",
            "Operating cash flow improved during FY2025.",
            25,
            0.85,
        ),
        make_result(
            "revenue",
            "Revenue from operations increased during FY2025.",
            10,
            0.80,
        ),
    ]

    reranker = CrossEncoderReranker(
        model=FakeCrossEncoder(),
    )

    results = reranker.rerank(
        query="What happened to revenue from operations?",
        candidates=candidates,
        limit=2,
    )

    assert [result.chunk.chunk_id for result in results] == [
        "revenue",
        "cash-flow",
    ]

    assert results[0].score == pytest.approx(0.95)
    assert results[0].chunk.page_number == 10
    assert results[0].chunk.source_url == (
        "https://example.com/report.pdf"
    )


def test_reranker_handles_empty_candidates():
    reranker = CrossEncoderReranker(
        model=FakeCrossEncoder(),
    )

    assert reranker.rerank(
        query="What was the revenue?",
        candidates=[],
    ) == []


def test_reranker_rejects_invalid_input():
    reranker = CrossEncoderReranker(
        model=FakeCrossEncoder(),
    )

    with pytest.raises(ValueError, match="Query must not be empty"):
        reranker.rerank("   ", [])

    with pytest.raises(ValueError, match="Limit must be at least 1"):
        reranker.rerank("revenue", [], limit=0)


def test_hybrid_candidates_are_reranked_end_to_end():
    candidates = [
        make_result(
            "governance",
            "The board reviewed governance policies.",
            30,
            0.90,
        ),
        make_result(
            "revenue",
            "Revenue from operations increased during FY2025.",
            10,
            0.80,
        ),
        make_result(
            "cash-flow",
            "Operating cash flow improved during FY2025.",
            25,
            0.70,
        ),
    ]

    hybrid = FakeHybridRetriever(candidates)

    reranker = CrossEncoderReranker(
        model=FakeCrossEncoder(),
    )

    pipeline = RerankedRetrievalService(
        hybrid_retriever=hybrid,
        reranker=reranker,
    )

    results = pipeline.search(
        query="What happened to revenue from operations?",
        limit=2,
        candidate_limit=3,
    )

    assert len(results) == 2
    assert results[0].chunk.chunk_id == "revenue"
    assert results[1].chunk.chunk_id == "cash-flow"

    assert hybrid.received_query == (
        "What happened to revenue from operations?"
    )
    assert hybrid.received_limit == 3