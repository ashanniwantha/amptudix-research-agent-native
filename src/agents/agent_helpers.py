from typing import TypedDict
from collections.abc import Sequence
from urllib.parse import urlparse
from src.tools.search_engine import SearchResult


class SourceCitation(TypedDict):
    index: int
    title: str
    url: str
    domain: str
    category: str


OFFICIAL_HINTS = (
    ".gov",
    ".edu",
    "wikipedia.org",
    "docs.",
    "developer.",
    "api.",
    "openai.com",
    "anthropic.com",
    "google.com",
    "microsoft.com",
    "github.com",
)

COMMUNITY_HINTS = (
    "reddit.com",
    "stackexchange.com",
    "stackoverflow.com",
    "news.ycombinator.com",
    "medium.com",
    "dev.to",
    "substack.com",
)


def classify_source(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if any(hint in host for hint in OFFICIAL_HINTS):
        return "official"
    if any(hint in host for hint in COMMUNITY_HINTS):
        return "community"
    return "other"


def format_source_block(source: SourceCitation, snippet: str = "") -> str:
    return (
        f"SOURCE [{source['index']}]\n"
        f"Title: {source['title']}\n"
        f"URL: {source['url']}\n"
        f"Category: {source['category']}\n"
        f"Snippet: {snippet}\n"
        "---"
    )


def build_sources_from_search_results(
    results: Sequence[SearchResult], start_index: int = 1
) -> tuple[str, list[SourceCitation]]:
    """Create prompt-ready source blocks and strict source metadata from search results."""
    if not results:
        return ("No web results found in this scout attempt.", [])

    lines: list[str] = []
    sources: list[SourceCitation] = []
    next_index = start_index

    for item in results:
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        snippet = (item.get("snippet") or "").strip()

        # Strict policy: only include sources that have both a title and URL.
        if not title or not url:
            continue

        source: SourceCitation = {
            "index": next_index,
            "title": title,
            "url": url,
            "domain": item.get("domain", ""),
            "category": classify_source(url),
        }
        sources.append(source)
        lines.append(format_source_block(source=source, snippet=snippet))
        next_index += 1

    if not sources:
        return (
            "No valid sources found in this scout attempt (missing title or URL).",
            [],
        )

    return ("\n".join(lines), sources)


def _format_search_results(results: Sequence[SearchResult], start_index=1) -> str:
    """
    Format search results into indexed blocks for the LLM.
    'start_index' allows us to keep numbering consistent across multiple searches.
    """

    formatted, _ = build_sources_from_search_results(
        results=results, start_index=start_index
    )
    return formatted
