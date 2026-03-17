def get_tools_definition():
    """
    Returns a list of available tools for the LLM to use.
    This follows the OpenAI Tools Specification format.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "fetch_web_content",
                "description": "Use this tool to read text content from a specified URL. Helpful for researching topics, reading articles, or fetching up-to-date information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The full URL of a website to read (e.g., https://en.wikipedia.org/wiki/Model_Context_Protocol)",
                        }
                    },
                    "required": ["url"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the internet for topics you don't know or require the latest updates to stay relevant.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query for the search engine to find relevant websites (e.g., 'latest AI news 2026')",
                        }
                    },
                    "required": ["query"],
                },
            },
        },
    ]
