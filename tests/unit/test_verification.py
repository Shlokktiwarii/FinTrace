from fintrace.generation.models import (
    Citation,
    Evidence,
    GeneratedAnswer,
)
from fintrace.verification import (
    VerificationService,
    VerificationStatus,
)


def make_evidence() -> Evidence:
    return Evidence(
        evidence_id="E1",
        chunk_id="chunk-1",
        document_id="doc-1",
        company="Example Industries Ltd",
        source_url="https://example.com/report.pdf",
        page_number=10,
        section="Revenue",
        text=(
            "Revenue increased from 1,116 to 1,250 crore."
        ),
    )


def test_valid_citation_passes():
    evidence = [make_evidence()]

    answer = GeneratedAnswer(
        question="What happened to revenue?",
        answer=(
            "Revenue increased from 1,116 to 1,250 crore [E1]."
        ),
        citations=(
            Citation(evidence_id="E1"),
        ),
    )

    report = VerificationService().verify(
        answer,
        evidence,
    )

    assert report.passed is True

    citation_check = report.checks[0]

    assert (
        citation_check.status
        == VerificationStatus.PASS
    )


def test_unknown_structured_citation_fails():
    answer = GeneratedAnswer(
        question="What was revenue?",
        answer="Revenue was 1,250 crore [E9].",
        citations=(
            Citation(evidence_id="E9"),
        ),
    )

    report = VerificationService().verify(
        answer,
        [make_evidence()],
    )

    assert report.passed is False

    citation_check = report.checks[0]

    assert (
        citation_check.status
        == VerificationStatus.FAIL
    )


def test_unknown_inline_citation_fails():
    answer = GeneratedAnswer(
        question="What was revenue?",
        answer="Revenue was 1,250 crore [E2].",
        citations=(
            Citation(evidence_id="E1"),
        ),
    )

    report = VerificationService().verify(
        answer,
        [make_evidence()],
    )

    assert report.passed is False

    assert "E2" in " ".join(
        report.checks[0].details
    )


def test_abstained_answer_is_supported_by_empty_evidence_state():
    answer = GeneratedAnswer(
        question="What was revenue?",
        answer=(
            "The available evidence is insufficient "
            "to answer this question."
        ),
        citations=(),
        abstained=True,
    )

    report = VerificationService().verify(
        answer,
        [],
    )

    assert report.passed is True

    assert (
        report.checks[0].status
        == VerificationStatus.PASS
    )

    assert (
        report.checks[1].status
        == VerificationStatus.NOT_CHECKED
    )


def test_incorrect_percentage_change_fails():
    answer = GeneratedAnswer(
        question="What was revenue growth?",
        answer=(
            "Revenue increased from 1,116 to 1,250 crore, "
            "a 20% increase [E1]."
        ),
        citations=(
            Citation(evidence_id="E1"),
        ),
    )

    report = VerificationService().verify(
        answer,
        [make_evidence()],
    )

    numeric_check = next(
        check
        for check in report.checks
        if check.name == "numeric_consistency"
    )

    assert (
        numeric_check.status
        == VerificationStatus.FAIL
    )

    assert report.passed is False


def test_correct_percentage_change_passes():
    answer = GeneratedAnswer(
        question="What was revenue growth?",
        answer=(
            "Revenue increased from 1,116 to 1,250 crore, "
            "approximately 12% [E1]."
        ),
        citations=(
            Citation(evidence_id="E1"),
        ),
    )

    report = VerificationService().verify(
        answer,
        [make_evidence()],
    )

    numeric_check = next(
        check
        for check in report.checks
        if check.name == "numeric_consistency"
    )

    assert (
        numeric_check.status
        == VerificationStatus.PASS
    )