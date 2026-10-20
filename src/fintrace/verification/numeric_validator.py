import re
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from fintrace.generation.models import Evidence, GeneratedAnswer
from fintrace.verification.models import (
    VerificationCheck,
    VerificationStatus,
)


# Recognizes patterns such as:
# increased from 1,116 to 1,250, approximately 12%
# grew from 100 to 120 by 20%
CHANGE_PATTERN = re.compile(
    r"(?P<direction>increase|increased|growth|grew|rise|rose|up|"
    r"decrease|decreased|decline|declined|fell|fall|down|drop|dropped)?"
    r".{0,50}?"
    r"(?:from\s+)?"
    r"(?P<old>-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)"
    r"\s+to\s+"
    r"(?P<new>-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)"
    r".{0,100}?"
    r"(?P<pct>\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE | re.DOTALL,
)


def _to_decimal(value: str) -> Decimal:
    """Convert a formatted number to Decimal."""
    return Decimal(value.replace(",", ""))


def _normalize_numbers(text: str) -> str:
    """Normalize thousands separators for literal number matching."""
    return re.sub(
        r"(?<=\d),(?=\d{3}(?:\D|$))",
        "",
        text,
    )


def validate_numeric_consistency(
    answer: GeneratedAnswer,
    evidence: Sequence[Evidence],
    *,
    tolerance_percentage_points: Decimal = Decimal("1.0"),
    ) -> VerificationCheck:
    """Validate recognizable percentage-change claims."""

    matches = list(CHANGE_PATTERN.finditer(answer.answer))

    if answer.abstained:
        return VerificationCheck(
            name="numeric_consistency",
            status=VerificationStatus.NOT_CHECKED,
            message=(
                "Numeric consistency was not checked "
                "because the answer abstained."
            ),
        )

    if not matches:
        return VerificationCheck(
            name="numeric_consistency",
            status=VerificationStatus.WARNING,
            message=(
                "No recognizable percentage-change pattern was found. "
                "Numerical claims were not comprehensively checked."
            ),
        )
    evidence_text = "\n".join(
        item.text for item in evidence
    ).casefold()

    normalized_evidence = _normalize_numbers(evidence_text)

    problems: list[str] = []

    for match in matches:
        claim = match.group(0)

        try:
            old_value = _to_decimal(match.group("old"))
            new_value = _to_decimal(match.group("new"))
            stated_percentage = _to_decimal(match.group("pct"))
        except InvalidOperation:
            problems.append(
                f"Could not parse numeric claim: {claim!r}"
            )
            continue

        if old_value == 0:
            problems.append(
                f"Cannot calculate percentage change from zero: {claim!r}"
            )
            continue

        # Percentage change relative to the original value.
        calculated_percentage = (
            (new_value - old_value)
            / abs(old_value)
            * Decimal("100")
        )

        direction = (match.group("direction") or "").casefold()

        says_increase = direction in {
            "increase",
            "increased",
            "growth",
            "grew",
            "rise",
            "rose",
            "up",
        }

        says_decrease = direction in {
            "decrease",
            "decreased",
            "decline",
            "declined",
            "fell",
            "fall",
            "down",
            "drop",
            "dropped",
        }

        direction_invalid = (
            (says_increase and new_value < old_value)
            or (says_decrease and new_value > old_value)
        )

        # Compare magnitudes: "12% increase" means positive 12%;
        # "12% decrease" means negative 12%.
        expected_percentage = abs(calculated_percentage)

        percentage_invalid = (
            abs(expected_percentage - stated_percentage)
            > tolerance_percentage_points
        )

        if percentage_invalid or direction_invalid:
            problems.append(
                f"Claim {claim!r}: calculated change is "
                f"{calculated_percentage.quantize(Decimal('0.01'))}%, "
                f"but the answer states {stated_percentage}%."
            )

        old_literal = _normalize_numbers(match.group("old"))
        new_literal = _normalize_numbers(match.group("new"))

        if (
            old_literal not in normalized_evidence
            or new_literal not in normalized_evidence
        ):
            problems.append(
                f"Claim {claim!r}: one or both figures were not found "
                "in the supplied evidence."
            )

    if problems:
        return VerificationCheck(
            name="numeric_consistency",
            status=VerificationStatus.FAIL,
            message=(
                "One or more numerical consistency checks failed."
            ),
            details=tuple(problems),
        )

    return VerificationCheck(
        name="numeric_consistency",
        status=VerificationStatus.PASS,
        message=(
            "Recognized percentage-change claims passed "
            "the implemented arithmetic and evidence checks."
        ),
    )