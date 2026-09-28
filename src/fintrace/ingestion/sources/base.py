from collections.abc import Iterable
from typing import Protocol

from fintrace.ingestion.models import DiscoveredDocument


class DocumentSourceClient(Protocol):
    """Interface implemented by financial document source connectors."""

    def discovered_documents(self) -> Iterable[DiscoveredDocument]:
        """Discover documents available from the source."""
        ...