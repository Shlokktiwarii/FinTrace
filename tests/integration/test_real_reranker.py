import os

import pytest

from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.models import SearchResult
from fintrace.retrieval.reranker import CrossEncoderReranker


@pytest.mark.skipif(
    os.getenv("RUN_REAL_MODEL_TESTS") != "1",
    reason="Set RUN_REAL_MODEL_TESTS=1 to run model integration tests",
)
def test_real_cross_encoder_ranks_relevant_financial_passage_first():
    candidates = [
        SearchResult(
            chunk=DocumentChunk(
                chunk_id="governance",
                document_id="report-2025",
                company="Example Limited",
                source_url="https://example.com/report.pdf",
                page_number=30,
                section="Corporate Governance",
                text=(
                    "The board reviewed governance policies "
                    "and director independence."
                ),
            ),
            score=0.90,
        ),
        SearchResult(
            chunk=DocumentChunk(
                chunk_id="revenue",
                document_id="report-2025",
                company="Example Limited",
                source_url="https://example.com/report.pdf",
                page_number=10,
                section="Financial Performance",
                text=(
                    "Revenue from operations was 1200 crore rupees "
                    "during FY2025."
                ),
            ),
            score=0.80,
        ),
        SearchResult(
            chunk=DocumentChunk(
                chunk_id="environment",
                document_id="report-2025",
                company="Example Limited",
                source_url="https://example.com/report.pdf",
                page_number=40,
                section="Sustainability",
                text=(
                    "The company discussed renewable energy "
                    "and water conservation."
                ),
            ),
            score=0.70,
        ),
    ]

    reranker = CrossEncoderReranker(
        model_name="BAAI/bge-reranker-base",
        device="cpu",
    )

    results = reranker.rerank(
        query="What was revenue from operations in FY2025?",
        candidates=candidates,
        limit=3,
    )

    assert results
    assert results[0].chunk.chunk_id == "revenue"
    assert results[0].chunk.page_number == 10