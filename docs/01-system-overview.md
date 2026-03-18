# 01. System Overview

## Mission

AMPTUDIX is a terminal-first multi-agent research system that balances:
- fast direct answers when external research is not required,
- structured web research when freshness or verification is required,
- compact long-term memory using vector storage,
- strict citation hygiene.

## Core Runtime Components

- `main.py`: interactive CLI entrypoint.
- `src/agents/supervisor.py`: top-level orchestrator (`SamuraiSupervisor`).
- `src/agents/researcher.py`: tool-calling web investigator (`ResearcherAgent`).
- `src/agents/summarizer.py`: compression and relevance filtering (`SummarizerAgent`).
- `src/memory/vault.py`: persistent vector memory (`MemoryVault`, ChromaDB).
- `src/tools/search_engine.py`: web search via DuckDuckGo (`ddgs`).
- `src/tools/web_reader.py`: URL fetch + extraction (`httpx` + `trafilatura`).
- `src/core/tools_registry.py`: tool schemas exposed to model tool-calling.

## Request Lifecycle (Current Implementation)

1. User enters command in terminal.
2. Supervisor retrieves archived context from `MemoryVault`.
3. Supervisor asks Summarizer to condense retrieved context.
4. Supervisor routes request:
   - direct path if no fresh research is needed,
   - research path if freshness/verification signals are detected.
5. Research path:
   - Researcher loops with model tool-calls,
   - executes `search_web` and optional `fetch_web_content`,
   - asks Summarizer to condense fetched page content,
   - returns raw research payload + structured source list.
6. Supervisor validates/deduplicates sources and enforces citation mapping.
7. Supervisor generates final answer (streaming in terminal UI).
8. Supervisor removes invalid citations and appends verified bibliography.
9. Supervisor asks Summarizer to condense memory payload.
10. MemoryVault stores chunked summaries with metadata.

## Policy Features Already Present

- Conditional research routing (`_should_research`).
- Strict source acceptance (title + URL required).
- Source deduplication by URL.
- Invalid citation stripping (`[n]` without validated source removed).
- Verified bibliography appended post-generation.
- Memory budgets by character count and line count.

## Compatibility Layer

- `src/core/llm.py` exposes `Brain` adapter for older imports/tests.
- Adapter delegates to modern Researcher/Summarizer architecture.

## Repository Notes

- `src/main.py` exists but is currently empty.
- `promptssystem_prompt.txt` exists but is currently empty.
- Persistent vector data defaults to `data/vault_db`.
