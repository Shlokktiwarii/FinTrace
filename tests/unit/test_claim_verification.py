import json

from fintrace.generation.models import (
    Citation,
    Evidence,
    GeneratedAnswer,
)
from fintrace.verification.claim_extractor import ClaimExtractor
from fintrace.verification.claim_verifier import LLMClaimVerifier
from fintrace.verification.models import (
    Claim,
    ClaimStatus,
    VerificationDecision,
    VerificationPolicy,
)
from fintrace.verification.service import VerificationService


class FakeLLMProvider:
    def __init__(self, response: str):
        self.response = response
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def make_evidence(
    evidence_id: str = "E1",
    text: str = "Revenue increased from 1000 crore to 1100 crore.",
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        chunk_id="chunk-1",
        document_id="doc-1",
        company="Example Industries Ltd",
        source_url="https://example.com/report.pdf",
        page_number=10,
        section="Financial Highlights",
        text=text,
    )


def make_answer(
    text: str,
    *,
    citations: tuple[Citation, ...] = (Citation("E1"),),
    abstained: bool = False,
) -> GeneratedAnswer:
    return GeneratedAnswer(
        question="What happened to revenue?",
        answer=text,
        citations=citations,
        abstained=abstained,
    )


def test_claim_extractor_splits_sentences_and_extracts_citations():
    answer = make_answer(
        "Revenue increased [E1]. "
        "Profit declined [E2].",
        citations=(Citation("E1"), Citation("E2")),
    )

    claims = ClaimExtractor().extract(answer)

    assert len(claims) == 2
    assert claims[0].text == "Revenue increased"
    assert claims[0].citation_ids == ("E1",)
    assert claims[1].text == "Profit declined"
    assert claims[1].citation_ids == ("E2",)


def test_claim_extractor_returns_no_claims_for_abstention():
    answer = make_answer(
        "Insufficient evidence.",
        citations=(),
        abstained=True,
    )

    assert ClaimExtractor().extract(answer) == ()


def test_llm_claim_verifier_accepts_supported_claim():
    provider = FakeLLMProvider(
        json.dumps(
            {
                "status": "supported",
                "explanation": "The evidence directly supports the claim.",
                "supporting_evidence_ids": ["E1"],
                "contradicting_evidence_ids": [],
            }
        )
    )

    claim = Claim(
        claim_id="C1",
        text="Revenue increased.",
        citation_ids=("E1",),
    )

    result = LLMClaimVerifier(provider).verify(
        claim,
        [make_evidence()],
    )

    assert result.status == ClaimStatus.SUPPORTED
    assert result.supporting_evidence_ids == ("E1",)


def test_llm_claim_verifier_rejects_unknown_evidence_reference():
    provider = FakeLLMProvider(
        json.dumps(
            {
                "status": "supported",
                "explanation": "The evidence supports the claim.",
                "supporting_evidence_ids": ["E999"],
                "contradicting_evidence_ids": [],
            }
        )
    )

    claim = Claim(
        claim_id="C1",
        text="Revenue increased.",
        citation_ids=("E1",),
    )

    result = LLMClaimVerifier(provider).verify(
        claim,
        [make_evidence()],
    )

    assert result.status == ClaimStatus.NOT_CHECKED
    assert "not supplied" in result.explanation


def test_llm_claim_verifier_handles_invalid_json():
    provider = FakeLLMProvider("This is not JSON.")

    claim = Claim(
        claim_id="C1",
        text="Revenue increased.",
        citation_ids=("E1",),
    )

    result = LLMClaimVerifier(provider).verify(
        claim,
        [make_evidence()],
    )

    assert result.status == ClaimStatus.NOT_CHECKED


def test_llm_claim_verifier_reports_missing_evidence():
    provider = FakeLLMProvider("{}")

    claim = Claim(
        claim_id="C1",
        text="Revenue increased.",
        citation_ids=("E1",),
    )

    result = LLMClaimVerifier(provider).verify(claim, [])

    assert result.status == ClaimStatus.INSUFFICIENT_EVIDENCE
    assert not provider.prompts


def test_llm_claim_verifier_does_not_accept_supported_without_evidence_id():
    provider = FakeLLMProvider(
        json.dumps(
            {
                "status": "supported",
                "explanation": "The claim is correct.",
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
            }
        )
    )

    claim = Claim(
        claim_id="C1",
        text="Revenue increased.",
        citation_ids=("E1",),
    )

    result = LLMClaimVerifier(provider).verify(
        claim,
        [make_evidence()],
    )

    assert result.status == ClaimStatus.NOT_CHECKED


def test_service_flags_claims_when_no_semantic_verifier_is_configured():
    service = VerificationService(
        policy=VerificationPolicy(
            require_semantic_verification=True,
        )
    )

    report = service.verify(
        make_answer("Revenue increased [E1]."),
        [make_evidence()],
    )

    assert report.decision == VerificationDecision.FLAG

def test_service_accepts_supported_claims():
    provider = FakeLLMProvider(
        json.dumps(
            {
                "status": "supported",
                "explanation": "The evidence directly supports the claim.",
                "supporting_evidence_ids": ["E1"],
                "contradicting_evidence_ids": [],
            }
        )
    )

    service = VerificationService(
        claim_verifier=LLMClaimVerifier(provider)
    )

    report = service.verify(
        make_answer("Revenue increased [E1]."),
        [make_evidence()],
    )

    assert report.decision == VerificationDecision.ACCEPT
    assert report.passed
    assert len(report.claim_verifications) == 1
    assert (
        report.claim_verifications[0].status
        == ClaimStatus.SUPPORTED
    )


def test_service_rejects_contradicted_claim():
    provider = FakeLLMProvider(
        json.dumps(
            {
                "status": "contradicted",
                "explanation": "The evidence says revenue declined.",
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": ["E1"],
            }
        )
    )

    service = VerificationService(
        claim_verifier=LLMClaimVerifier(provider)
    )

    report = service.verify(
        make_answer("Revenue increased [E1]."),
        [
            make_evidence(
                text="Revenue declined from 1100 crore to 1000 crore."
            )
        ],
    )

    assert report.decision == VerificationDecision.REJECT
    assert not report.passed
    assert report.claim_verifications[0].status == ClaimStatus.CONTRADICTED


def test_service_flags_unsupported_claim_by_default():
    provider = FakeLLMProvider(
        json.dumps(
            {
                "status": "unsupported",
                "explanation": "The evidence does not mention operating costs.",
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
            }
        )
    )

    service = VerificationService(
        claim_verifier=LLMClaimVerifier(provider)
    )

    report = service.verify(
        make_answer("Operating costs declined [E1]."),
        [make_evidence()],
    )

    assert report.decision == VerificationDecision.FLAG


def test_policy_can_reject_unsupported_claims():
    provider = FakeLLMProvider(
        json.dumps(
            {
                "status": "unsupported",
                "explanation": "The evidence does not establish this claim.",
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
            }
        )
    )

    service = VerificationService(
        claim_verifier=LLMClaimVerifier(provider),
        policy=VerificationPolicy(reject_on_unsupported=True),
    )

    report = service.verify(
        make_answer("Operating costs declined [E1]."),
        [make_evidence()],
    )

    assert report.decision == VerificationDecision.REJECT


def test_service_abstention_is_not_treated_as_accepted_answer():
    service = VerificationService()

    report = service.verify(
        make_answer(
            "The available evidence is insufficient.",
            citations=(),
            abstained=True,
        ),
        [],
    )

    assert report.decision == VerificationDecision.ABSTAIN
    assert report.claim_verifications == ()