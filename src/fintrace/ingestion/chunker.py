from fintrace.ingestion.models import DocumentChunk, NormalizedPage
from fintrace.ingestion.structure import DocumentStructureExtractor


class DocumentChunker:
    """Create retrieval-ready chunks from structured document pages."""

    def __init__(
        self,
        max_characters: int = 1500,
    ) -> None:
        if max_characters < 100:
            raise ValueError(
                "max_characters must be at least 100"
            )

        self.max_characters = max_characters

    def chunk(
        self,
        document_id: str,
        company: str,
        source_url: str,
        structured_pages: list[
            tuple[NormalizedPage, str | None]
        ],
    ) -> list[DocumentChunk]:
        """Split pages into bounded retrieval chunks."""

        chunks: list[DocumentChunk] = []
        chunk_number = 0

        for page, section in structured_pages:
            text = page.text

            for start in range(
                0,
                len(text),
                self.max_characters,
            ):
                chunk_text = text[
                    start : start + self.max_characters
                ].strip()

                if not chunk_text:
                    continue

                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document_id}-{chunk_number}",
                        document_id=document_id,
                        company=company,
                        source_url=source_url,
                        page_number=page.page_number,
                        section=section,
                        text=chunk_text,
                    )
                )

                chunk_number += 1

        return chunks