from collections.abc import Sequence

from fintrace.generation.models import (
    Evidence,
    GeneratedAnswer,
)
from fintrace.verification.citation_validator import (
    validate_citations,
)
from fintrace.verification.models import (
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)
from fintrace.verification.numeric_validator import (
    validate_numeric_consistency,
)


class VerificationService:
    """Run deterministic checks on a generated answer."""

    def verify(
        self,
        answer: GeneratedAnswer,
        evidence: Sequence[Evidence],
    ) -> VerificationReport:
        checks: list[VerificationCheck] = []

        # Layer 1: citation reference integrity.
        checks.append(
            validate_citations(
                answer=answer,
                evidence=evidence,
            )
        )

        # Layer 2: numerical consistency.
        if answer.abstained:
            checks.append(
                VerificationCheck(
                    name="numeric_consistency",
                    status=VerificationStatus.NOT_CHECKED,
                    message=(
                        "Numerical checks were skipped because "
                        "the answer abstained."
                    ),
                )
            )
        else:
            checks.append(
                validate_numeric_consistency(
                    answer=answer,
                    evidence=evidence,
                )
            )

        # A warning or a skipped check is not a failure, but it
        # should remain visible in the report.
        passed = all(
            check.status != VerificationStatus.FAIL
            for check in checks
        )

        return VerificationReport(
            passed=passed,
            checks=tuple(checks),
        )