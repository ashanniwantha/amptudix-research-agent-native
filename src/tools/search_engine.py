# We use the new 'ddgs' library you just installed
from typing import TypedDict
from ddgs import DDGS
from rich.console import Console

console = Console()


class SearchResult(TypedDict):
    source: str
    title: str
    url: str
    snippet: str
    domain: str
    rank: int


def search_web(query: str, max_results: int = 10) -> list[SearchResult]:
    """
    This search_web function takes a 'query' as it's parameter.
    It query the web using the duckduckgo search engine and the provided query
    And it returns structured search results as a list of dicts:
    {'source', 'title', 'url', 'snippet', 'domain', 'rank'}
    """
    results: list[SearchResult] = []
    console.print(f"[italic cyan]Scouting the web for:[/italic cyan] '{query}'...\n")

    try:
        # 'with DDGS()' creates a temporary session with DuckDuckGo
        with DDGS() as ddgs:
            # .text() is the primary method for web search
            # max_results keeps the context window from getting too cluttered
            search_gen = ddgs.text(query, max_results=max_results)

            for i, r in enumerate(search_gen, start=1):
                href = r.get("href", "")
                title = r.get("title", "")
                body = r.get("body", "")
                domain = href.split("/")[2] if href and "/" in href else ""
                # UI Reporting: Show which website was found
                console.print(f" ✅ Found: [underline]{domain}[/underline]")

                # We build a 'card' for each result so the LLM can easily see:
                # 1. What the page is about (Title)
                # 2. Where it is (URL)
                # 3. A quick preview (Snippet)
                results.append(
                    {
                        "source": f"S{i}",
                        "title": title,
                        "url": href,
                        "snippet": body,
                        "domain": domain,
                        "rank": i,
                    }
                )

        if not results:
            console.print(
                f" ⚠️ My lord, the scout found nothing in the mist for that query."
            )
            return []

        console.print(
            f"[bold blue]Scout returned {len(results)} sources. [/bold blue]\n"
        )
        return results

    except Exception as e:
        console.print(f" ❌ Error during search: {e}\n")
        return []


if __name__ == "__main__":
    # Manual test to see it in action
    print(search_web("Model Context Protocol latest news"))
