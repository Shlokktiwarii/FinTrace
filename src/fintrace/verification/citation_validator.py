import re
from collections.abc import Sequence

from fintrace.generation.models import Evidence, GeneratedAnswer
from fintrace.verification.models import (
    VerificationCheck,
    VerificationStatus,
)


_INLINE_CITATION_PATTERN = re.compile(
    r"\[([A-Za-z][A-Za-z0-9_-]*)\]"
)


def validate_citations(
    answer: GeneratedAnswer,
    evidence: Sequence[Evidence],
) -> VerificationCheck:
    """Validate that answer citations refer to supplied evidence.

    This checks reference integrity, not whether the evidence
    semantically supports the answer.
    """

    evidence_ids = {
        item.evidence_id
        for item in evidence
    }

    structured_ids = [
        citation.evidence_id
        for citation in answer.citations
    ]

    inline_ids = _INLINE_CITATION_PATTERN.findall(
        answer.answer
    )

    problems: list[str] = []

    # Duplicate structured citations.
    if len(structured_ids) != len(set(structured_ids)):
        problems.append(
            "The structured citation list contains duplicates."
        )

    # Unknown structured citations.
    unknown_structured = (
        set(structured_ids) - evidence_ids
    )

    if unknown_structured:
        problems.append(
            "Unknown structured evidence IDs: "
            + ", ".join(sorted(unknown_structured))
        )

    # Unknown inline citations.
    unknown_inline = set(inline_ids) - evidence_ids

    if unknown_inline:
        problems.append(
            "Unknown inline evidence IDs: "
            + ", ".join(sorted(unknown_inline))
        )

    # Abstained answers should not cite evidence.
    if answer.abstained and (
        structured_ids or inline_ids
    ):
        problems.append(
            "An abstained answer must not contain citations."
        )

    if problems:
        return VerificationCheck(
            name="citation_integrity",
            status=VerificationStatus.FAIL,
            message="Citation integrity checks failed.",
            details=tuple(problems),
        )

    return VerificationCheck(
        name="citation_integrity",
        status=VerificationStatus.PASS,
        message=(
            "All citation references point to supplied evidence."
        ),
    )