import json

from fintrace.generation.service import GenerationService
from fintrace.retrieval.models import SearchResult
from fintrace.ingestion.models import DocumentChunk


class FakeLLMProvider:
    """Deterministic provider for testing the generation pipeline."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt: str | None = None
        self.call_count = 0

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        self.call_count += 1
        return self.response


def make_search_result() -> SearchResult:
    chunk = DocumentChunk(
        chunk_id="example-fy2025-summary",
        document_id="example-annual-report-2025",
        company="Example Industries Ltd",
        source_url="https://example.com/annual-report.pdf",
        page_number=12,
        section="Financial Highlights",
        text=(
            "Example Industries Ltd reported revenue of "
            "INR 1,250 crore in FY2025, compared with "
            "INR 1,116 crore in FY2024, representing "
            "approximately 12% year-over-year growth."
        ),
    )

    return SearchResult(chunk=chunk, score=0.95)


def test_generation_service_returns_cited_answer() -> None:
    response = json.dumps(
        {
            "answer": (
                "Revenue was INR 1,250 crore in FY2025, "
                "up approximately 12% from FY2024 [E1]."
            ),
            "citation_ids": ["E1"],
            "abstained": False,
        }
    )

    provider = FakeLLMProvider(response)
    service = GenerationService(provider=provider)

    result = service.answer(
        question="What was the FY2025 revenue and its growth?",
        results=[make_search_result()],
    )

    assert result.abstained is False
    assert "1,250 crore" in result.answer
    assert "12%" in result.answer
    assert result.citations
    assert provider.call_count == 1
    assert provider.last_prompt is not None
    assert "1,250 crore" in provider.last_prompt


def test_generation_service_abstains_without_evidence() -> None:
    provider = FakeLLMProvider("")
    service = GenerationService(provider=provider)

    result = service.answer(
        question="What was the company's revenue?",
        results=[],
    )

    assert result.abstained is True
    assert result.citations == ()
    assert provider.call_count == 0