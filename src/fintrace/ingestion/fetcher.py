from typing import Final

import httpx


RETRYABLE_STATUS_CODES: Final = {408, 429, 500, 502, 503, 504}


class FetchError(Exception):
    """Raised when a document cannot be fetched."""


class HttpFetcher:
    """Fetch raw document bytes from an HTTP URL."""

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries

    def fetch(self, url: str) -> bytes:
        """Fetch and return the raw response bytes."""

        last_error: Exception | None = None

        with httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = client.get(url)

                    if response.status_code in RETRYABLE_STATUS_CODES:
                        if attempt < self.max_retries:
                            continue

                    response.raise_for_status()
                    return response.content

                except httpx.TimeoutException as exc:
                    last_error = exc

                    if attempt == self.max_retries:
                        break

                except httpx.HTTPError as exc:
                    last_error = exc
                    break

        raise FetchError(f"Failed to fetch document from {url}") from last_error