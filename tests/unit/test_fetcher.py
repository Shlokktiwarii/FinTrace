import httpx
import pytest

from fintrace.ingestion.fetcher import FetchError, HttpFetcher


def test_fetch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_get(
        self: httpx.Client,
        url: str,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=b"financial document",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    fetcher = HttpFetcher()

    result = fetcher.fetch("https://example.com/report.pdf")

    assert result == b"financial document"


def test_fetch_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_get(
        self: httpx.Client,
        url: str,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=404,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    fetcher = HttpFetcher(max_retries=3)

    with pytest.raises(FetchError):
        fetcher.fetch("https://example.com/missing.pdf")