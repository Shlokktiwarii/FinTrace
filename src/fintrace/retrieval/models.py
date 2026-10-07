from dataclasses import dataclass

from fintrace.ingestion.models import DocumentChunk


@dataclass(frozen=True)
class IndexedChunk:
    """A document chunk prepared for retrieval."""

    chunk: DocumentChunk
    embedding: tuple[float, ...]