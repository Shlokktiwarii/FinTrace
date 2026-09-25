from collections.abc import Iterable
from typing import Protocol

from fintrace.ingestion.models import RawDocument


class DocumentSourceClient(Protocol):
    """Interface implemented by financial document source connectors."""

    def fetch_documents(self) -> Iterable[RawDocument]:
        """Fetch documents from the external source."""
        ...