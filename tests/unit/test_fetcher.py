import httpx
import pytest

from fintrace.ingestion.fetcher import AsyncHttpFetcher, FetchError


@pytest.mark.asyncio
async def test_fetch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_get(
        self: httpx.AsyncClient,
        url: str,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=b"financial document",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    fetcher = AsyncHttpFetcher()

    result = await fetcher.fetch("https://example.com/report.pdf")

    assert result == b"financial document"


@pytest.mark.asyncio
async def test_fetch_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_get(
        self: httpx.AsyncClient,
        url: str,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=404,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    fetcher = AsyncHttpFetcher(max_retries=3)

    with pytest.raises(FetchError):
        await fetcher.fetch("https://example.com/missing.pdf")


@pytest.mark.asyncio
async def test_fetch_retries_retryable_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def mock_get(
        self: httpx.AsyncClient,
        url: str,
    ) -> httpx.Response:
        nonlocal calls
        calls += 1

        if calls < 3:
            return httpx.Response(
                status_code=503,
                request=httpx.Request("GET", url),
            )

        return httpx.Response(
            status_code=200,
            content=b"financial document",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    fetcher = AsyncHttpFetcher(max_retries=3)

    result = await fetcher.fetch("https://example.com/report.pdf")

    assert result == b"financial document"
    assert calls == 3