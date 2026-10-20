from collections.abc import Sequence

from fintrace.generation.models import Evidence, GeneratedAnswer
from fintrace.verification.citation_validator import validate_citations
from fintrace.verification.claim_extractor import ClaimExtractor
from fintrace.verification.claim_verifier import ClaimVerifier
from fintrace.verification.models import (
    ClaimStatus,
    ClaimVerification,
    VerificationCheck,
    VerificationDecision,
    VerificationPolicy,
    VerificationReport,
    VerificationStatus,
)
from fintrace.verification.numeric_validator import (
    validate_numeric_consistency,
)


class VerificationService:
    """Coordinate citation, numeric, and semantic claim verification."""

    def __init__(
        self,
        claim_verifier: ClaimVerifier | None = None,
        policy: VerificationPolicy | None = None,
    ) -> None:
        self._claim_extractor = ClaimExtractor()
        self._claim_verifier = claim_verifier
        self._policy = policy or VerificationPolicy()

    def verify(
        self,
        answer: GeneratedAnswer,
        evidence: Sequence[Evidence],
    ) -> VerificationReport:
        checks: list[VerificationCheck] = []
        claim_results: list[ClaimVerification] = []

        # 1. Validate citation reference integrity.
        checks.append(validate_citations(answer, evidence))

        # 2. Validate numerical consistency.
        checks.append(
            validate_numeric_consistency(
                answer=answer,
                evidence=evidence,
            )
        )

        # 3. Abstentions do not require claim extraction.
        if answer.abstained:
            return VerificationReport(
                passed=not any(
                    check.status == VerificationStatus.FAIL
                    for check in checks
                ),
                checks=tuple(checks),
                claim_verifications=(),
                decision=VerificationDecision.ABSTAIN,
            )

        # 4. Extract answer claims.
        claims = self._claim_extractor.extract(answer)

        if not claims:
            checks.append(
                VerificationCheck(
                    name="claim_extraction",
                    status=VerificationStatus.WARNING,
                    message="No factual claims could be extracted.",
                )
            )

        # 5. Verify each claim against its cited evidence.
        if self._claim_verifier is None:
            checks.append(
                VerificationCheck(
                    name="semantic_claim_verification",
                    status=VerificationStatus.NOT_CHECKED,
                    message=(
                        "No claim verifier was configured; "
                        "semantic support has not been established."
                    ),
                )
            )
        else:
            evidence_by_id = {
                item.evidence_id: item
                for item in evidence
            }

            for claim in claims:
                claim_evidence = [
                    evidence_by_id[evidence_id]
                    for evidence_id in claim.citation_ids
                    if evidence_id in evidence_by_id
                ]

                result = self._claim_verifier.verify(
                    claim=claim,
                    evidence=claim_evidence,
                )
                claim_results.append(result)

            unchecked = sum(
                result.status == ClaimStatus.NOT_CHECKED
                for result in claim_results
            )

            needs_attention = sum(
                result.status
                in {
                    ClaimStatus.PARTIAL,
                    ClaimStatus.UNSUPPORTED,
                    ClaimStatus.CONTRADICTED,
                    ClaimStatus.INSUFFICIENT_EVIDENCE,
                }
                for result in claim_results
            )

            if unchecked:
                semantic_status = VerificationStatus.NOT_CHECKED
            elif needs_attention:
                semantic_status = VerificationStatus.WARNING
            else:
                semantic_status = VerificationStatus.PASS

            checks.append(
                VerificationCheck(
                    name="semantic_claim_verification",
                    status=semantic_status,
                    message=(
                        f"Verified {len(claim_results)} claims; "
                        f"{needs_attention} require attention; "
                        f"{unchecked} could not be checked."
                    ),
                    details=tuple(
                        f"{result.claim.claim_id}: "
                        f"{result.status.value} — {result.explanation}"
                        for result in claim_results
                    ),
                )
            )

        decision = self._decide(checks, claim_results)

        return VerificationReport(
            passed=decision == VerificationDecision.ACCEPT,
            checks=tuple(checks),
            claim_verifications=tuple(claim_results),
            decision=decision,
        )

    def _decide(
    self,
    checks: Sequence[VerificationCheck],
    claim_results: Sequence[ClaimVerification],
) -> VerificationDecision:
    # Reject configured hard failures first.
      for check in checks:
        if check.status != VerificationStatus.FAIL:
            continue

        if (
            check.name == "citation_integrity"
            and self._policy.reject_on_citation_failure
        ):
            return VerificationDecision.REJECT

        if (
            check.name == "numeric_consistency"
            and self._policy.reject_on_numeric_failure
        ):
            return VerificationDecision.REJECT

    # Without a semantic verifier, use the configured basic checks.
      if self._claim_verifier is None:
         if self._policy.require_semantic_verification:
            return VerificationDecision.FLAG


         return VerificationDecision.ACCEPT

      statuses = {result.status for result in claim_results}

      if ClaimStatus.CONTRADICTED in statuses:
         return VerificationDecision.REJECT

      if ClaimStatus.NOT_CHECKED in statuses:
         return VerificationDecision.FLAG

      if ClaimStatus.UNSUPPORTED in statuses:
         return (
            VerificationDecision.REJECT
            if self._policy.reject_on_unsupported
            else VerificationDecision.FLAG
         )

      if ClaimStatus.INSUFFICIENT_EVIDENCE in statuses:
         return VerificationDecision.FLAG

      if ClaimStatus.PARTIAL in statuses:
         return (
            VerificationDecision.REJECT
            if self._policy.reject_on_partial
            else VerificationDecision.FLAG
        )

      if not claim_results:
         return VerificationDecision.FLAG

      if any(
         check.status == VerificationStatus.FAIL
         for check in checks
        ):
         return VerificationDecision.REJECT

      return VerificationDecision.ACCEPT