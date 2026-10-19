import json
import os

import pytest
from dotenv import load_dotenv
from pathlib import Path

from fintrace.generation.gemini_provider import (
    GeminiProvider,
)
from fintrace.generation.service import GenerationService
from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.models import SearchResult


# Load local development environment variables.
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)

pytestmark = pytest.mark.integration


@pytest.fixture
def financial_evidence() -> list[SearchResult]:
    """
    Provide deterministic financial evidence.

    These figures are synthetic test data, not actual company results.
    """

    chunk = DocumentChunk(
        chunk_id="reliance-fy2025-financial-summary",
        document_id="reliance-annual-report-2025",
        company="Example Industries Ltd",
        source_url="https://example.com/annual-report-2025.pdf",
        page_number=42,
        section="Financial Highlights",
        text=(
            "Example Industries Ltd reported revenue of "
            "INR 1,250 crore for FY2025, compared with "
            "INR 1,116 crore in FY2024. Revenue increased "
            "by approximately 12% year over year. "
            "These figures are from the financial highlights "
            "section of the annual report."
        ),
    )

    return [
        SearchResult(
            chunk=chunk,
            score=0.95,
        )
    ]


@pytest.mark.skipif(
    os.getenv("RUN_GEMINI_LIVE_TESTS") != "1",
    reason=(
        "Set RUN_GEMINI_LIVE_TESTS=1 to run tests "
        "that call the real Gemini API."
    ),
)
def test_gemini_generation_pipeline(
    financial_evidence: list[SearchResult],
) -> None:
    """
    Integration test:
    evidence -> prompt builder -> Gemini -> answer parser.
    """

    api_key = os.getenv("FINTRACE_LLM_API_KEY")
    model = os.getenv("FINTRACE_LLM_MODEL")
    base_url = os.getenv("FINTRACE_LLM_BASE_URL")

    if not api_key:
        pytest.fail("FINTRACE_LLM_API_KEY is not configured.")

    if not model:
        pytest.fail("FINTRACE_LLM_MODEL is not configured.")

    if not base_url:
        pytest.fail("FINTRACE_LLM_BASE_URL is not configured.")

    provider = GeminiProvider(
        api_key=api_key,
        model=model,
        timeout=90.0,
    )

    service = GenerationService(provider=provider)

    question = (
        "What was Example Industries Ltd's revenue in FY2025, "
        "and how much did it grow compared with FY2024? "
        "Cite the supplied evidence."
    )

    result = service.answer(
        question=question,
        results=financial_evidence,
    )

    # 1. Verify the answer object was constructed successfully.
    assert result.question == question
    assert isinstance(result.answer, str)
    assert result.answer.strip()

    # 2. The supplied evidence is sufficient for this question.
    assert result.abstained is False

    # 3. At least one citation must be returned.
    assert result.citations

    # 4. Every citation must refer to evidence supplied to the model.
    valid_evidence_ids = {"E1"}

    for citation in result.citations:
        assert citation.evidence_id in valid_evidence_ids

    # 5. The answer should contain the correct financial figures.
    # Allow for common formatting differences.
    normalized_answer = (
        result.answer.lower()
        .replace(",", "")
        .replace("₹", "")
    )

    assert "1250" in normalized_answer or "1.25" in normalized_answer
    assert "12%" in normalized_answer or "12 percent" in normalized_answer

    # 6. Print a useful summary without exposing the API key.
    print("\n--- FinTrace Gemini Integration Test ---")
    print(f"Model: {model}")
    print(f"Question: {result.question}")
    print(f"Answer: {result.answer}")
    print(
        "Citations:",
        json.dumps(
            [
                citation.evidence_id
                for citation in result.citations
            ],
            ensure_ascii=False,
        ),
    )
    print(f"Abstained: {result.abstained}")

