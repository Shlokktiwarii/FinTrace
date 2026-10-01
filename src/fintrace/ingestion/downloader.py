import asyncio
from collections.abc import Iterable
from datetime import datetime, timezone
from fintrace.ingestion.fetcher import AsyncHttpFetcher , FetchError
from fintrace.ingestion.models import DownloadResult


class AsyncDocumentDownloader:
    """Download multiple documents with bounded concurrency."""

    def __init__(
        self,
        fetcher: AsyncHttpFetcher,
        max_concurrency: int = 5,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")

        self.fetcher = fetcher
        self.max_concurrency = max_concurrency

    async def download(
        self,
        urls: Iterable[str],
    ) -> list[DownloadResult]:
        """Download documents concurrently and return individual results."""

        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def download_one(url: str) -> DownloadResult:
             async with semaphore:
                try:
                    content = await self.fetcher.fetch(url)

                    return DownloadResult(
                        url=url,
                        content=content,
                        error=None,
                        fetched_at=datetime.now(timezone.utc),
                    )

                except FetchError as exc:
                    return DownloadResult(
                        url=url,
                        content=None,
                        error=str(exc),
                        fetched_at=datetime.now(timezone.utc),
                    )

        return await asyncio.gather(
            *(download_one(url) for url in urls)
        )