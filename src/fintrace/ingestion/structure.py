import re

from fintrace.ingestion.models import (
    NormalizedDocument,
    NormalizedPage,
)


class DocumentStructureExtractor:
    """Identify section headings in normalized financial documents."""

    HEADING_PATTERN = re.compile(
        r"^(?:"
        r"management discussion|"
        r"management's discussion|"
        r"financial statements|"
        r"balance sheet|"
        r"profit and loss|"
        r"cash flow statement|"
        r"notes to accounts|"
        r"risk factors|"
        r"business overview|"
        r"corporate governance"
        r")$",
        re.IGNORECASE,
    )

    def extract(
        self,
        document: NormalizedDocument,
    ) -> list[tuple[NormalizedPage, str | None]]:
        """Associate pages with detected section headings."""

        results: list[tuple[NormalizedPage, str | None]] = []

        current_section: str | None = None

        for page in document.pages:
            for line in page.text.splitlines():
                candidate = line.strip()

                if self.HEADING_PATTERN.match(candidate):
                    current_section = candidate

            results.append((page, current_section))

        return results