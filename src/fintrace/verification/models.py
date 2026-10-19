from dataclasses import dataclass
from enum import StrEnum


class VerificationStatus(StrEnum):
    """Possible outcomes for an individual verification check."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_CHECKED = "not_checked"


@dataclass(frozen=True)
class VerificationCheck:
    """Result of one verification check."""

    name: str
    status: VerificationStatus
    message: str
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class VerificationReport:
    """Combined results of the verification pipeline."""

    passed: bool
    checks: tuple[VerificationCheck, ...]

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