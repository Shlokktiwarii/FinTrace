import json

import pytest

from fintrace.generation.service import GenerationService
from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.models import SearchResult


class FakeLLMProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.received_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.received_prompt = prompt
        return self.response


def make_result() -> SearchResult:
    return SearchResult(
        chunk=DocumentChunk(
            chunk_id="revenue-2025",
            document_id="annual-report-2025",
            company="Example Limited",
            source_url="https://example.com/report.pdf",
            page_number=12,
            section="Financial Performance",
            text=(
                "Revenue from operations was ₹1,200 crore "
                "in FY2025."
            ),
        ),
        score=0.95,
    )


def test_generation_produces_answer_with_valid_evidence_citation():
    provider = FakeLLMProvider(
        json.dumps(
            {
                "answer": (
                    "Revenue from operations was ₹1,200 crore "
                    "in FY2025 [E1]."
                ),
                "citation_ids": ["E1"],
                "abstained": False,
            }
        )
    )

    service = GenerationService(provider)

    result = service.answer(
        "What was revenue from operations in FY2025?",
        [make_result()],
    )

    assert "₹1,200 crore" in result.answer
    assert result.abstained is False
    assert [citation.evidence_id for citation in result.citations] == [
        "E1"
    ]

    assert provider.received_prompt is not None
    assert "Revenue from operations was ₹1,200 crore" in (
        provider.received_prompt
    )


def test_generation_abstains_when_no_evidence_is_available():
    provider = FakeLLMProvider("This should not be called.")
    service = GenerationService(provider)

    result = service.answer(
        "What was the company's revenue?",
        [],
    )

    assert result.abstained is True
    assert result.citations == ()
    assert provider.received_prompt is None


def test_generation_rejects_fabricated_citation_ids():
    provider = FakeLLMProvider(
        json.dumps(
            {
                "answer": "Revenue was ₹1,200 crore [E99].",
                "citation_ids": ["E99"],
                "abstained": False,
            }
        )
    )

    service = GenerationService(provider)

    with pytest.raises(ValueError, match="Unknown evidence IDs"):
        service.answer(
            "What was revenue?",
            [make_result()],
        )


def test_generation_rejects_malformed_json():
    provider = FakeLLMProvider(
        '{"answer": "Revenue was ₹1,200 crore",'
    )

    service = GenerationService(provider)

    with pytest.raises(ValueError, match="valid JSON"):
        service.answer(
            "What was revenue?",
            [make_result()],
        )


def test_generation_prompt_includes_grounding_rules():
    provider = FakeLLMProvider(
        json.dumps(
            {
                "answer": "The evidence supports ₹1,200 crore [E1].",
                "citation_ids": ["E1"],
                "abstained": False,
            }
        )
    )

    service = GenerationService(provider)

    service.answer("What was revenue?", [make_result()])

    assert provider.received_prompt is not None
    assert "available evidence is insufficient" in (
        provider.received_prompt
    )
    assert "Evidence JSON:" in provider.received_prompt