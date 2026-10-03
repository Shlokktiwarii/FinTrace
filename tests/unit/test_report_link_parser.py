from fintrace.ingestion.sources.parsers.report_links import (
    ReportLinkParser,
)


def test_report_link_parser_extracts_pdf_links() -> None:
    html = """
    <html>
        <body>
            <a href="/reports/annual-report-2026.pdf">
                Annual Report 2026
            </a>
            <a href="/about">About Us</a>
            <a href="/reports/results-2026.pdf">
                Financial Results 2026
            </a>
        </body>
    </html>
    """

    parser = ReportLinkParser()

    reports = parser.parse(
        html=html,
        base_url="https://example.com/investor/",
    )

    assert len(reports) == 2

    assert reports[0].url == (
        "https://example.com/reports/annual-report-2026.pdf"
    )

    assert reports[0].title == "Annual Report 2026"

    assert reports[1].url == (
        "https://example.com/reports/results-2026.pdf"
    )