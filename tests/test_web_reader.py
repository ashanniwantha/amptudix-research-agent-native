import respx
import httpx
import pytest
from src.tools.web_reader import fetch_web_content


@respx.mock
def test_web_content_fetch_success(monkeypatch):
    url = "https://example.com/article"
    html = "<html><body>Hello</body></html>"

    respx.get(url).respond(200, text=html)

    monkeypatch.setattr(
        "trafilatura.extract",
        lambda downloaded, include_links, output_format: "Extracted Article text",
    )

    result = fetch_web_content(url)
    assert isinstance(result, str)
    assert "Extracted Article text" in result
