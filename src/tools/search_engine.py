# We use the new 'ddgs' library you just installed
from ddgs import DDGS


def search_web(query: str, max_results: int = 10) -> str:
    """
    This search_web function takes a 'query' as it's parameter.
    It query the web using the duckduckgo search engine and the provided query
    And it returns a list of title and their URLs so the agent can use them
    """
    try:
        results = []
        # 'with DDGS()' creates a temporary session with DuckDuckGo
        with DDGS() as ddgs:
            # .text() is the primary method for web search
            # max_results keeps the context window from getting too cluttered
            search_gen = ddgs.text(query, max_results=max_results)

            for i, r in enumerate(search_gen, start=1):
                # We build a 'card' for each result so the LLM can easily see:
                # 1. What the page is about (Title)
                # 2. Where it is (URL)
                # 3. A quick preview (Snippet)
                formatted = (
                    f"SOURCE: [{i}]\n"
                    f"Title: {r['title']}\n"
                    f"URL: {r['href']}\n"
                    f"Snippet: {r['body']}\n"
                    "---"
                )
                results.append(formatted)

        if not results:
            return "My lord, the scout found nothing in the mist for that query."

        return "\n".join(results)

    except Exception as e:
        # If the search fails, we must tell the LLM so it can try a different query
        return f"Scout Error: {str(e)}"


if __name__ == "__main__":
    # Manual test to see it in action
    print(search_web("Model Context Protocol latest news"))
