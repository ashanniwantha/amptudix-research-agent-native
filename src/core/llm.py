import os
from typing import Any, cast, List
import json
from openai import OpenAI
from dotenv import load_dotenv
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolUnionParam,
)
from src.core.tools_registry import get_tools_definition
from src.tools.web_reader import fetch_web_content
from src.tools.search_engine import search_web
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.status import Status

load_dotenv()
console = Console()


class Brain:
    def __init__(self) -> None:
        self.client = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")
        self.model: str | None = os.getenv("MODEL_NAME")

    def stream_response(self, messages: List[ChatCompletionMessageParam]) -> str:
        """
        Send a streaming chat completion, print token in real-time, and return full response.
        """
        model = self.model
        if not model:
            return "Sorry! Try again please!"

        stream = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )

        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                text_chunk = chunk.choices[0].delta.content
                print(text_chunk, end="", flush=True)
                full_response += text_chunk

        print()
        return full_response

    def consult(
        self,
        prompt: str,
        system_prompt: str = """
                You're an helpful AI assistant that has a personality of a ancient japanese samurai with a hugh sense of humor!
                """,
    ) -> str:
        model = self.model
        if not model:
            return "Sorry! Try again please!"

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        return self.stream_response(messages=messages)

    def researcher(self, user_prompt: str, max_iterations: int = 5) -> str:
        system_prompt: str = """
        You are a professional Research Agent. Your goal is to provide a focused, data-driven report.

        Follow these rules:
        1. Relevance Filter: ONLY use information directly related to the user's topic. If a search result is about an unrelated topic (e.g., economics or health when the topic is music), ignore it completely.
        2. Verified Citations: Every claim must be followed by a [Source Number] from the search results.
        3. Analysis: Clearly separate critical acclaim (from professional reviewers) from public sentiment (social media/fans).
        4. Sources: At the very end, provide a 'Bibliography' section. Each entry MUST follow this format: [n] Title - URL
        """
        console.print(
            Panel.fit(
                "[bold cyan]Agentic Researcher Active[/bold cyan]", border_style="blue"
            )
        )

        model = self.model
        if not model:
            return "Sorry! Try again please!"

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        source_index = 0

        tools = cast(list[ChatCompletionToolUnionParam], get_tools_definition())

        for i in range(max_iterations):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
            except Exception as e:
                return (
                    f"Forgive me, my lord. The connection to the brain has failed: {e}"
                )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                if response_message.content:
                    print(response_message.content)
                    return response_message.content

                return self.stream_response(messages=messages)

            messages.append(
                cast(ChatCompletionMessageParam, response_message.model_dump())
            )

            with console.status("[bold green]Thinking...[/bold green]") as status:
                for tool_call in tool_calls:
                    if tool_call.type == "function":
                        t_name = tool_call.function.name
                        t_id = tool_call.id

                        print(f"DEBUG [Iteration {i+1}]: Using {t_name}")

                        try:
                            args = json.loads(tool_call.function.arguments)

                            if t_name == "search_web":
                                status.update(
                                    f"[bold yellow]Searching Web:[/bold yellow] {args.get('query')}"
                                )
                                result = search_web(args.get("query", ""))

                            elif t_name == "fetch_web_content":
                                status.update(
                                    f"[bold magenta]Scraping URL:[/bold magenta] {args.get('url')[:50]}.."
                                )
                                result = fetch_web_content(args.get("url", ""))
                            else:
                                result = f"Error: The tool '{t_name} is not in my inventory!'"

                        except json.JSONDecodeError:
                            result = "Error: The brain provided invalid JSON for the tool arguments"
                        except Exception as e:
                            result = f"Error: An unexpected event occured while using the tool: {e}"

                        source_index += 1
                        result_with_id = f"SOURCE [{source_index}]: {result}"

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": t_id,
                                "content": result_with_id,
                            }
                        )
        print("DEBUG: Max Iterations Reached. Summarizing findings....")
        return self.stream_response(messages=messages)


if __name__ == "__main__":
    agent = Brain()
    agent.researcher(
        "What was the latest Rosalia album and how was the public preception towards it?"
    )
