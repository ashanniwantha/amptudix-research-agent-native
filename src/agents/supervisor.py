import os
import re
from typing import List
from openai.types.chat import ChatCompletionMessageParam
from typing import cast

from rich.panel import Panel

from src.agents.base import BaseAgent
from src.agents.agent_helpers import SourceCitation
from src.agents.researcher import ResearcherAgent
from src.agents.summarizer import SummarizerAgent
from src.memory.vault import MemoryVault


class SamuraiSupervisor(BaseAgent):
    def __init__(self):
        super().__init__(
            role_name="Samurai",
            persona="""You are a elite Samurai Researcher. 
            You provide high-quality intelligence to your Lord. 
            Maintain a tone of honor, discipline, and occasional wit. 
            Always cite your sources using [Source Number].""",
        )
        self.scribe = SummarizerAgent()
        self.scout = ResearcherAgent(scribe=self.scribe)
        self.vault = MemoryVault()
        self.session_history: List[ChatCompletionMessageParam] = []

        # Budget feature:
        # A "budget" is a hard size limit for memory payloads.
        # We measure budget in:
        # 1) characters (total text length), and
        # 2) non-empty lines (structure limit).
        # This keeps retrieval/storage fast and prevents context bloat.
        self.retrieval_summary_char_budget = self._read_int_env(
            "MEMORY_RETRIEVAL_CHAR_BUDGET", 1800
        )
        self.storage_summary_char_budget = self._read_int_env(
            "MEMORY_STORAGE_CHAR_BUDGET", 2200
        )
        self.memory_line_budget = self._read_int_env("MEMORY_LINE_BUDGET", 24)

    @staticmethod
    def _read_int_env(name: str, default: int) -> int:
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            value = int(raw)
            return value if value > 0 else default
        except ValueError:
            return default

    @staticmethod
    def _msg(role: str, content: str) -> ChatCompletionMessageParam:
        return cast(ChatCompletionMessageParam, {"role": role, "content": content})

    def _compact_session_history(self) -> str:
        if len(self.session_history) <= 12:
            return ""

        recent_history = self.session_history[-12:]
        summary = self.scribe.summarize_history(recent_history)
        self.session_history = [
            self._msg("system", f"Conversation summary so far: {summary}")
        ] + self.session_history[-6:]
        return summary

    def _apply_memory_budget(self, text: str, char_budget: int) -> str:
        """Apply memory budgets measured by non-empty line count and total characters."""
        cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
        if not cleaned:
            return ""

        # Keep only the first N meaningful lines to avoid noisy archives.
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        lines = lines[: self.memory_line_budget]
        compact = "\n".join(lines)

        if len(compact) <= char_budget:
            return compact

        clipped = compact[:char_budget].rstrip()
        return clipped + " ..."

    def _summarize_for_memory_retrieval(self, user_input: str, content: str) -> str:
        cleaned = content.strip()
        if not cleaned:
            return ""

        summarized = self.scribe.summarize(
            topic=f"Relevant archived context for: {user_input}",
            content=cleaned,
        ).strip()

        if not summarized or summarized.startswith("Connection error"):
            return self._apply_memory_budget(
                cleaned, char_budget=self.retrieval_summary_char_budget
            )
        return self._apply_memory_budget(
            summarized, char_budget=self.retrieval_summary_char_budget
        )

    def _summarize_for_memory_storage(self, user_input: str, content: str) -> str:
        cleaned = content.strip()
        if not cleaned:
            return ""

        summarized = self.scribe.summarize(
            topic=f"Memory summary for: {user_input}",
            content=cleaned,
        ).strip()

        if not summarized or summarized.startswith("Connection error"):
            return self._apply_memory_budget(
                cleaned, char_budget=self.storage_summary_char_budget
            )
        return self._apply_memory_budget(
            summarized, char_budget=self.storage_summary_char_budget
        )

    def _should_research(self, user_input: str) -> bool:
        urgency_signals = (
            "latest",
            "today",
            "current",
            "recent",
            "new",
            "news",
            "release",
            "price",
            "breaking",
            "202",
            "yesterday",
            "this week",
        )
        lower = user_input.lower()

        if any(signal in lower for signal in urgency_signals):
            return True

        if not self.model:
            return False

        classifier_messages: List[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": (
                    "Decide whether this user request requires web research for up-to-date facts. "
                    "Answer with one word only: YES or NO. "
                    "Return YES only if freshness or external verification is necessary."
                ),
            },
            {"role": "user", "content": user_input},
        ]
        verdict = self.generate_reply(classifier_messages, is_streaming=False).strip()
        return verdict.upper().startswith("YES")

    def _sanitize_and_verify_sources(
        self, sources: List[SourceCitation]
    ) -> List[SourceCitation]:
        seen_urls: set[str] = set()
        clean_sources: List[SourceCitation] = []
        next_index = 1

        for source in sources:
            title = source.get("title", "").strip()
            url = source.get("url", "").strip()
            if not title or not url:
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)

            clean_sources.append(
                {
                    "index": next_index,
                    "title": title,
                    "url": url,
                    "domain": source.get("domain", ""),
                    "category": source.get("category", "other"),
                }
            )
            next_index += 1

        return clean_sources

    def _build_sources_block(self, sources: List[SourceCitation]) -> str:
        if not sources:
            return "No validated sources were retained."

        lines: list[str] = []
        for source in sources:
            lines.append(
                (
                    f"[{source['index']}] {source['title']} - {source['url']} "
                    f"(category: {source['category']})"
                )
            )
        return "\n".join(lines)

    def _strip_invalid_citations(self, text: str, valid_ids: set[int]) -> str:
        def _replace(match: re.Match[str]) -> str:
            citation_id = int(match.group(1))
            return match.group(0) if citation_id in valid_ids else ""

        return re.sub(r"\[(\d+)\]", _replace, text)

    def _append_verified_bibliography(
        self, text: str, sources: List[SourceCitation]
    ) -> str:
        cleaned_text = re.sub(
            r"(?is)\n---\s*📜\s*ARCHIVAL SOURCES\s*---.*$", "", text
        ).rstrip()

        cited_ids = {
            int(match.group(1)) for match in re.finditer(r"\[(\d+)\]", cleaned_text)
        }
        source_map = {source["index"]: source for source in sources}

        selected_ids = sorted(cited_ids.intersection(source_map.keys()))
        if not selected_ids:
            selected_ids = sorted(source_map.keys())[:8]

        bibliography_lines = ["--- 📜 ARCHIVAL SOURCES ---"]
        for source_id in selected_ids:
            src = source_map[source_id]
            bibliography_lines.append(f"[{source_id}] {src['title']} - {src['url']}")

        return cleaned_text + "\n\n" + "\n".join(bibliography_lines)

    def generate_direct_response(
        self, user_query: str, past_context: str, session_summary: str
    ) -> str:
        system_instructions = f"""
        {self.persona}

        Respond directly without web research.
        Use only conversation context and archived memory.
        If you are uncertain, be explicit about uncertainty.
        """

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_instructions},
            {
                "role": "user",
                "content": (
                    f"The Lord's Command: {user_query}\n\n"
                    f"SESSION SUMMARY:\n{session_summary or 'N/A'}\n\n"
                    f"ARCHIVE KNOWLEDGE:\n{past_context or 'N/A'}"
                ),
            },
        ]

        self.console.print(
            "\n[bold cyan]⚔️ Samurai answer mode: no external research required.[/bold cyan]\n"
        )
        return self.generate_reply(messages, is_streaming=True)

    def generate_final_response(
        self,
        user_query: str,
        research_data: str,
        validated_sources: List[SourceCitation],
        session_summary: str,
    ) -> str:
        """
        Refined for Perplexity-style formatting.
        """
        source_mix = {
            "official": sum(
                1 for s in validated_sources if s["category"] == "official"
            ),
            "community": sum(
                1 for s in validated_sources if s["category"] == "community"
            ),
            "other": sum(1 for s in validated_sources if s["category"] == "other"),
        }

        system_instructions = f"""
        {self.persona}
        
        You are an expert at synthesizing research. 
        Using the provided RESEARCH DATA, answer the Lord's command.

        SOURCE POLICY:
        - Use only citation numbers from the VALIDATED SOURCES list.
        - Never cite a source that is missing title or URL.
        - Prefer official sources for factual claims.
        - Include community perspective where helpful (forums/Reddit/practitioner reports).
        - If official and community sources conflict, explain the conflict.

        FORMATTING RULES:
        1. Body: Use clear headings. Cite every fact with [n].
        2. Clarity: If sources conflict, mention the discrepancy.
        3. Bibliography: Create a final section titled '--- 📜 ARCHIVAL SOURCES ---'.
        4. Sources: List them as: [n] Title - URL
        """

        sources_block = self._build_sources_block(validated_sources)

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_instructions},
            {
                "role": "user",
                "content": (
                    f"The Lord's Command: {user_query}\n\n"
                    f"SESSION SUMMARY:\n{session_summary or 'N/A'}\n\n"
                    f"RESEARCH DATA:\n{research_data}\n\n"
                    f"SOURCE MIX: official={source_mix['official']}, community={source_mix['community']}, other={source_mix['other']}\n\n"
                    f"VALIDATED SOURCES:\n{sources_block}"
                ),
            },
        ]

        # We use the stream_response method from BaseAgent (which we should define there)
        self.console.print(
            "\n[bold gold3]⚔️ The Samurai is drafting the scroll...[/bold gold3]\n"
        )
        draft = self.generate_reply(messages, is_streaming=True)
        valid_ids = {source["index"] for source in validated_sources}
        cleaned = self._strip_invalid_citations(draft, valid_ids)
        return self._append_verified_bibliography(cleaned, validated_sources)

    def run(self, user_input: str) -> str:
        """The Orchestration Loop"""

        self.console.print(
            Panel.fit(
                "[bold cyan]Samurai Supervisor[/bold cyan]\n[italic]Coordinating memory, routing, research, and synthesis.[/italic]",
                border_style="cyan",
            )
        )

        self.session_history.append(self._msg("user", user_input))

        # 1. Archive Retrieval
        with self.console.status("[bold yellow]Consulting archives...[/bold yellow]"):
            raw_past_context = self.vault.retrieve_relevant_context(user_input)

        with self.console.status(
            "[bold yellow]Scribe is condensing archived context...[/bold yellow]"
        ):
            past_context = self._summarize_for_memory_retrieval(
                user_input=user_input,
                content=raw_past_context,
            )

        with self.console.status(
            "[bold yellow]Managing session context...[/bold yellow]"
        ):
            session_summary = self._compact_session_history()

        with self.console.status(
            "[bold yellow]Evaluating whether research is required...[/bold yellow]"
        ):
            needs_research = self._should_research(user_input)

        if not needs_research:
            final_report = self.generate_direct_response(
                user_query=user_input,
                past_context=past_context,
                session_summary=session_summary,
            )
            self.session_history.append(self._msg("assistant", final_report))

            with self.console.status(
                "[bold yellow]Scribe is preparing mission memory...[/bold yellow]"
            ):
                memory_summary = self._summarize_for_memory_storage(
                    user_input=user_input,
                    content=final_report,
                )

            with self.console.status(
                "[bold yellow]Archiving mission summary...[/bold yellow]"
            ):
                self.vault.store_research(topic=user_input, content=memory_summary)

            return final_report

        # 2. Scout Execution (This uses your structured search_web/fetch tools)
        self.console.print(
            "[bold magenta]Research mode enabled:[/bold magenta] latest/external verification required."
        )
        raw_research, raw_sources = self.scout.execute_task_bundle(user_input)
        safe_raw_research = raw_research or ""
        validated_sources = self._sanitize_and_verify_sources(raw_sources)

        # 3. Combine context
        context_window = f"ARCHIVE KNOWLEDGE:\n{past_context}\n\nLATEST SCOUT FINDINGS:\n{safe_raw_research}"

        # 4. Final Response (Fixed the missing call!)
        final_report = self.generate_final_response(
            user_query=user_input,
            research_data=context_window,
            validated_sources=validated_sources,
            session_summary=session_summary,
        )
        self.session_history.append(self._msg("assistant", final_report))

        with self.console.status(
            "[bold yellow]Scribe is preparing mission memory...[/bold yellow]"
        ):
            memory_summary = self._summarize_for_memory_storage(
                user_input=user_input,
                content=final_report,
            )

        # 5. Store the successful mission in the Vault
        with self.console.status(
            "[bold yellow]Archiving mission summary...[/bold yellow]"
        ):
            self.vault.store_research(topic=user_input, content=memory_summary)

        return final_report
