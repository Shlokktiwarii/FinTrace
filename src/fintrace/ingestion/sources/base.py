from collections.abc import Iterable
from typing import Protocol

from fintrace.ingestion.models import DiscoveredDocument


class DocumentSourceClient(Protocol):
    """Interface implemented by financial document source connectors."""

    async def discover_documents(
        self,
    ) -> Iterable[DiscoveredDocument]:
        """Discover financial documents available from the source."""
        ...