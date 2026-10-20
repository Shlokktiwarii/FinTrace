from dataclasses import dataclass
from enum import StrEnum


class VerificationStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_CHECKED = "not_checked"


class ClaimStatus(StrEnum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_CHECKED = "not_checked"


class VerificationDecision(StrEnum):
    ACCEPT = "accept"
    FLAG = "flag"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class VerificationCheck:
    name: str
    status: VerificationStatus
    message: str
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    citation_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ClaimVerification:
    claim: Claim
    status: ClaimStatus
    explanation: str
    supporting_evidence_ids: tuple[str, ...] = ()
    contradicting_evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class VerificationPolicy:
    """Controls how verification outcomes affect answer acceptance."""

    reject_on_unsupported: bool = False
    reject_on_partial: bool = False
    reject_on_numeric_failure: bool = True
    reject_on_citation_failure: bool = True

    # If False, basic checks can accept an answer when no semantic
    # claim verifier is configured.
    require_semantic_verification: bool = False


@dataclass(frozen=True)
class VerificationReport:
    passed: bool
    checks: tuple[VerificationCheck, ...]
    claim_verifications: tuple[ClaimVerification, ...] = ()
    decision: VerificationDecision = VerificationDecision.FLAG

    @property
    def failures(self) -> tuple[VerificationCheck, ...]:
        return tuple(
            check
            for check in self.checks
            if check.status == VerificationStatus.FAIL
        )

    @property
    def warnings(self) -> tuple[VerificationCheck, ...]:
        return tuple(
            check
            for check in self.checks
            if check.status == VerificationStatus.WARNING
        )

    @property
    def unsupported_claims(self) -> tuple[ClaimVerification, ...]:
        return tuple(
            result
            for result in self.claim_verifications
            if result.status
            in {
                ClaimStatus.UNSUPPORTED,
                ClaimStatus.CONTRADICTED,
                ClaimStatus.INSUFFICIENT_EVIDENCE,
            }
        )