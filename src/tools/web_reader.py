import httpx
import trafilatura


def fetch_web_content(url: str) -> str:
    """
    This functions takes url as a parameter.
    Then takes that url to fetch content belongs to it.
    If the website is rather complex to fetch text, it returns an error message
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = httpx.get(
            url=url, headers=headers, timeout=10.0, follow_redirects=True
        )
        response.raise_for_status()

        downloaded = response.text
        result = trafilatura.extract(
            downloaded, include_links=True, output_format="markdown"
        )

        if not result:
            return "Error: Could not extract meaningful text form this url"

        return result

    except Exception as e:
        return f"Error fetching content: {str(e)}"


if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/Model_Context_Protocol"
    print(f"Testing scrapper on {url}...")
    content = fetch_web_content(url)
    print(content[:500])
