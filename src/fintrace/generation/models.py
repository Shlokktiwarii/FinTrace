from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
    """A retrieved passage available to support an answer."""

    evidence_id: str
    chunk_id: str
    document_id: str
    company: str
    source_url: str
    page_number: int
    section: str | None
    text: str


@dataclass(frozen=True)
class Citation:
    """A reference to a supplied evidence passage."""

    evidence_id: str


@dataclass(frozen=True)
class GeneratedAnswer:
    """An answer and its citations returned by the generation layer."""

    question: str
    answer: str
    citations: tuple[Citation, ...]
    abstained: bool = False