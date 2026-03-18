# 02. Agent Orchestration

## Agent Roles

### BaseAgent (`src/agents/base.py`)

Responsibilities:
- OpenAI-compatible client initialization (Ollama endpoint by default).
- Shared `generate_reply(...)` for streaming and non-streaming calls.
- Rich terminal rendering for streamed outputs.

Execution paths:
- Non-streaming path (`stream=False`): used for internal utility calls (Summarizer).
- Streaming path (`stream=True`): used for user-visible final responses.

### SamuraiSupervisor (`src/agents/supervisor.py`)

Responsibilities:
- Owns full mission lifecycle.
- Maintains `session_history` and performs periodic compaction.
- Decides direct vs research mode.
- Performs source sanitation and citation enforcement.
- Coordinates memory retrieval/storage through Summarizer.

Key internal methods:
- `_should_research(...)`: heuristic + LLM classifier gate.
- `_compact_session_history(...)`: summarizes older history when it grows.
- `_summarize_for_memory_retrieval(...)`: condenses retrieved memory.
- `_summarize_for_memory_storage(...)`: condenses final memory payload.
- `_apply_memory_budget(...)`: enforces line and char budgets.
- `_sanitize_and_verify_sources(...)`: drop invalid/duplicate sources and reindex.
- `_strip_invalid_citations(...)`: removes `[n]` references not in validated set.
- `_append_verified_bibliography(...)`: appends clean source list.

### ResearcherAgent (`src/agents/researcher.py`)

Responsibilities:
- Runs model tool-calling loop (`max_iterations` bounded).
- Calls tools from registry (`search_web`, `fetch_web_content`).
- Builds structured source objects with index/title/url/domain/category.
- Uses Summarizer to compress fetched webpage content.

Output contract:
- Returns `(research_content: str, sources: list[SourceCitation])`.

### SummarizerAgent (`src/agents/summarizer.py`)

Responsibilities:
- Topic-focused extraction from large text.
- Conversation-history condensation.
- Internal non-streaming operation for speed and deterministic formatting.

## Supervisor Routing Logic

Routing is triggered by:
- lexical urgency signals in input (`latest`, `today`, `recent`, etc.),
- optional LLM YES/NO classifier if heuristic does not trigger.

Result:
- `False` -> `generate_direct_response(...)`
- `True` -> researcher tool loop + `generate_final_response(...)`

## Citation and Source Integrity Pipeline

1. Researcher collects source candidates.
2. Supervisor sanitizes:
   - remove entries missing title/url,
   - dedupe by URL,
   - reindex sequentially.
3. Model drafts response with citation references.
4. Supervisor strips invalid citation IDs.
5. Supervisor appends authoritative final bibliography.

This two-stage enforcement (pre + post generation) is important because prompt-only citation constraints are not fully reliable.

## Streaming UX Behavior

- Final user-visible response is streamed through `BaseAgent.generate_reply(..., is_streaming=True)`.
- Rich `Live` panel continuously updates rendered markdown.
- Throughput indicator uses approximate `tokens/second` based on chunk count and elapsed time.

## Session Context Strategy

- Full history is maintained initially.
- When history length exceeds threshold, old context is summarized and replaced by a compact system message.
- Prevents context bloat and preserves continuity.
