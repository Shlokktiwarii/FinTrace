import re

from fintrace.ingestion.models import (
    NormalizedDocument,
    NormalizedPage,
    ParsedDocument,
)


class DocumentNormalizer:
    """Normalize extracted document text."""

    def normalize(
        self,
        document: ParsedDocument,
    ) -> NormalizedDocument:
        """Normalize page text while preserving page boundaries."""

        pages: list[NormalizedPage] = []

        for page in document.pages:
            text = self._normalize_text(page.text)

            if not text:
                continue

            pages.append(
                NormalizedPage(
                    page_number=page.page_number,
                    text=text,
                )
            )

        return NormalizedDocument(
            document_id=document.document_id,
            company=document.company,
            source_url=document.source_url,
            pages=tuple(pages),
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Clean whitespace without changing meaningful content."""

        text = text.replace("\x00", " ")

        text = re.sub(r"[ \t]+", " ", text)

        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()