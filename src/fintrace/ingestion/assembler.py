from fintrace.ingestion.models import (
    DiscoveredDocument,
    DownloadResult,
    RawDocument,
)


class DocumentAssembler:
    """Assemble downloaded content and discovery metadata into RawDocument."""

    def assemble(
        self,
        document: DiscoveredDocument,
        result: DownloadResult,
    ) -> RawDocument:
        """Create a RawDocument from a successful download."""

        if result.error is not None:
            raise ValueError(
                f"Cannot assemble failed download: {result.url}"
            )

        if result.content is None:
            raise ValueError(
                f"Download has no content: {result.url}"
            )

        return RawDocument(
            document_id=document.document_id,
            company=document.company,
            ticker=document.ticker,
            exchange=document.exchange,
            document_type=document.document_type,
            source=document.source,
            source_url=document.source_url,
            content=result.content,
            fetched_at=result.fetched_at,
        )