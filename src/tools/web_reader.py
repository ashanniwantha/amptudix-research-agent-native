import httpx
import trafilatura
from rich.console import Console

console = Console()


def fetch_web_content(url: str) -> str:
    """
    This functions takes url as a parameter.
    Then takes that url to fetch content belongs to it.
    If the website is rather complex to fetch text, it returns an error message
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    console.print(
        f"[bold magenta]->[/bold magenta] Downloading: [underline cyan]{url[:60]}...[/underline cyan]\n"
    )

    try:
        response = httpx.get(
            url=url, headers=headers, timeout=10.0, follow_redirects=True
        )
        response.raise_for_status()

        console.print(f"⏳ Status {response.status_code}. Extracting text...\n")

        downloaded = response.text
        result = trafilatura.extract(
            downloaded, include_links=True, output_format="markdown"
        )

        if not result:
            console.print(f"❌ Extracting failed: No meaningful text found\n")
            return "Error: Could not extract meaningful text form this url"

        word_count = len(result.split())
        console.print(f" ✅ Suceess! Processed [bold]{word_count}[/bold] words.\n")

        return result

    except httpx.HTTPStatusError as e:
        console.print(f" ❌ HTTP Error: {e.response.status_code}\n")
        return f"Error fetching content: HTTP {e.response.status_code}"

    except Exception as e:
        console.print(f" ❌ Error: {str(e)}\n")
        return f"Error fetching content: {str(e)}"


if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/Model_Context_Protocol"
    print(f"Testing scrapper on {url}...")
    content = fetch_web_content(url)
    print(content[:500])
