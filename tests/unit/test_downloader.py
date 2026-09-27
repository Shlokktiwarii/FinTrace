import pytest

from fintrace.ingestion.downloader import AsyncDocumentDownloader
from fintrace.ingestion.models import DownloadResult
from fintrace.ingestion.fetcher import FetchError


class FakeFetcher:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def fetch(self, url: str) -> bytes:
        self.calls.append(url)
        return f"content for {url}".encode()


@pytest.mark.asyncio
async def test_downloads_multiple_documents() -> None:
    fetcher = FakeFetcher()

    downloader = AsyncDocumentDownloader(
        fetcher=fetcher,
        max_concurrency=2,
    )

    urls = [
        "https://example.com/one.pdf",
        "https://example.com/two.pdf",
        "https://example.com/three.pdf",
    ]

    results = await downloader.download(urls)

    assert len(results) == 3

    assert results[0].url == urls[0]
    assert results[0].content == b"content for https://example.com/one.pdf"
    assert results[0].error is None

    assert results[1].url == urls[1]
    assert results[1].content == b"content for https://example.com/two.pdf"
    assert results[1].error is None

    assert results[2].url == urls[2]
    assert results[2].content == b"content for https://example.com/three.pdf"
    assert results[2].error is None

class FailingFetcher:
    async def fetch(self, url: str) -> bytes:
        if url.endswith("two.pdf"):
            raise FetchError("download failed")

        return b"document content"
@pytest.mark.asyncio
async def test_download_preserves_individual_failure() -> None:
    class FailingFetcher:
        async def fetch(self, url: str) -> bytes:
            if url.endswith("two.pdf"):
                raise FetchError("download failed")

            return b"document content"

    downloader = AsyncDocumentDownloader(
        fetcher=FailingFetcher(),
        max_concurrency=2,
    )

    urls = [
        "https://example.com/one.pdf",
        "https://example.com/two.pdf",
        "https://example.com/three.pdf",
    ]

    results = await downloader.download(urls)

    assert results[0].content == b"document content"
    assert results[0].error is None

    assert results[1].content is None
    assert results[1].error == "download failed"

    assert results[2].content == b"document content"
    assert results[2].error is None


def test_download_result_success() -> None:
    result = DownloadResult(
        url="https://example.com/report.pdf",
        content=b"financial document",
        error=None,
    )

    assert result.url == "https://example.com/report.pdf"
    assert result.content == b"financial document"
    assert result.error is None


def test_download_result_failure() -> None:
    result = DownloadResult(
        url="https://example.com/report.pdf",
        content=None,
        error="download failed",
    )

    assert result.url == "https://example.com/report.pdf"
    assert result.content is None
    assert result.error == "download failed"