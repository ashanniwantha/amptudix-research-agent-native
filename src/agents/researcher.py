import json
from typing import List, cast
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolUnionParam
from rich.panel import Panel
from urllib.parse import urlparse

from src.agents.base import BaseAgent
from src.agents.summarizer import SummarizerAgent  # Import the new agent
from src.core.tools_registry import get_tools_definition
from src.tools.search_engine import search_web
from src.tools.web_reader import fetch_web_content
from src.agents.agent_helpers import (
    SourceCitation,
    build_sources_from_search_results,
    classify_source,
    format_source_block,
)


class ResearcherAgent(BaseAgent):
    def __init__(self, scribe: SummarizerAgent):
        super().__init__(
            role_name="Scout",
            persona="You are a meticulous investigative researcher. Find raw facts and clear sources.",
        )
        self.tools = cast(List[ChatCompletionToolUnionParam], get_tools_definition())
        self.scribe = scribe  # Dependency Injection

    def execute_task_bundle(
        self, task_query: str, max_iterations: int = 5
    ) -> tuple[str, list[SourceCitation]]:
        self.console.print(
            Panel(
                f"[bold blue]🔍 {self.role_name}[/bold blue] is scouting: {task_query}"
            )
        )

        # Note: We removed the 'Vault' logic here.
        # The Supervisor will handle the Vault and pass context if needed.

        system_brief = (
            f"{self.persona}\n"
            "Research policy:\n"
            "1. Prefer official and first-party documentation for core claims.\n"
            "2. Include community sentiment (forums, Reddit, practitioner discussions) when relevant.\n"
            "3. Aggregate both perspectives and mention disagreements.\n"
            "4. Only use sources that contain both a title and URL.\n"
            "5. Reuse prior sources when possible; avoid duplicate searches.\n"
        )

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_brief},
            {"role": "user", "content": f"Research this topic: {task_query}"},
        ]

        source_index = 0
        collected_sources: list[SourceCitation] = []

        if not self.model:
            return ("Model not configured.", [])

        for i in range(max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                # Returns raw research data to the Supervisor
                return (response_message.content or "", collected_sources)

            messages.append(
                cast(ChatCompletionMessageParam, response_message.model_dump())
            )

            with self.console.status("[bold green]Scouting...[/bold green]") as status:
                for tool_call in tool_calls:
                    if tool_call.type != "function":
                        continue

                    result = "Tool call was not handled."
                    t_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    if t_name == "search_web":
                        raw_result = search_web(args.get("query", ""))
                        result, valid_sources = build_sources_from_search_results(
                            raw_result, start_index=source_index + 1
                        )
                        source_index += len(valid_sources)
                        collected_sources.extend(valid_sources)

                    elif t_name == "fetch_web_content":
                        status.update(
                            f"[magenta]Scribing content from URL...[/magenta]"
                        )
                        target_url = (args.get("url") or "").strip()
                        raw_html = fetch_web_content(target_url)

                        # CALLING THE SUMMARIZER AGENT
                        # Instead of doing it itself, it asks the Scribe
                        summary = self.scribe.summarize(
                            topic=task_query, content=raw_html
                        )

                        existing: SourceCitation | None = next(
                            (s for s in collected_sources if s["url"] == target_url),
                            None,
                        )
                        if existing is None and target_url:
                            host = urlparse(target_url).netloc or "unknown source"
                            generated_source: SourceCitation = {
                                "index": source_index + 1,
                                "title": f"Fetched page from {host}",
                                "url": target_url,
                                "domain": host,
                                "category": classify_source(target_url),
                            }
                            collected_sources.append(generated_source)
                            existing = generated_source
                            source_index += 1

                        if existing and existing.get("title") and existing.get("url"):
                            result = (
                                format_source_block(
                                    existing, snippet="Summarized full page"
                                )
                                + "\n"
                                + summary
                            )
                        else:
                            result = summary

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )

        return ("Research concluded (Max iterations reached).", collected_sources)

    def execute_task(self, task_query: str, max_iterations: int = 5) -> str:
        content, _ = self.execute_task_bundle(
            task_query=task_query, max_iterations=max_iterations
        )
        return content
