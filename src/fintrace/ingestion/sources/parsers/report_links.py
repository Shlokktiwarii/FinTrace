from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ReportLink:
    """A financial report link discovered on a webpage."""

    url: str
    title: str


class ReportLinkParser:
    """Extract financial report links from HTML."""

    def parse(
        self,
        html: str,
        base_url: str,
    ) -> list[ReportLink]:
        """Parse PDF report links from an HTML document."""

        soup = BeautifulSoup(html, "html.parser")

        reports: list[ReportLink] = []

        for link in soup.find_all("a", href=True):
            href = link["href"]

            if not isinstance(href, str):
                continue

            if ".pdf" not in href.lower():
                continue

            title = link.get_text(" ", strip=True)

            reports.append(
                ReportLink(
                    url=urljoin(base_url, href),
                    title=title,
                )
            )

        return reports