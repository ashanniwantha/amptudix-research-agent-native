# AMPTUDIX Research Agent (Native Python)

A multi-agent, terminal-first research system built in Python.

AMPTUDIX is designed to:
- answer directly when research is not needed,
- trigger structured web research when freshness is required,
- summarize findings with strict source validation,
- and persist compact, high-signal memory in a vector database.

---

## Highlights

- Multi-agent orchestration:
	- Samurai Supervisor: decision-making and final response
	- Scout Researcher: tool-calling web research
	- Scribe Summarizer: context compression and memory hygiene
- Research-aware routing:
	- skips research when not needed
	- enables research for freshness-sensitive prompts
- Strict citation policy:
	- invalid citations are removed
	- only sources with both title and URL are retained
- Hybrid memory retrieval:
	- semantic vector search + lexical overlap reranking
- Rich terminal UX:
	- streaming responses
	- live progress/status updates for long-running operations

---

## Architecture

Request lifecycle:

1. Supervisor receives user input.
2. Vault retrieves relevant archived context.
3. Scribe condenses retrieved context using memory budgets.
4. Supervisor decides if web research is required.
5. If required, Scout uses tools:
	 - search_web
	 - fetch_web_content
6. Scribe summarizes retrieved web content.
7. Supervisor synthesizes final response with verified bibliography.
8. Scribe condenses final mission memory.
9. Vault stores compact memory chunks for future retrieval.

---

## Requirements

- Python 3.12+
- uv (dependency and environment manager)
- Ollama running locally (or any OpenAI-compatible endpoint)

---

## Installation

```bash
uv sync
```

---

## Configuration

Create a .env file at project root.

Example:

```env
# LLM Runtime
MODEL_NAME=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434/v1

# Embeddings / Vector Memory
EMBEDDING_MODEL=nomic-embed-text

# Memory Budget Controls
MEMORY_RETRIEVAL_CHAR_BUDGET=1800
MEMORY_STORAGE_CHAR_BUDGET=2200
MEMORY_LINE_BUDGET=24
```

Budget definitions:
- MEMORY_RETRIEVAL_CHAR_BUDGET: max characters used when injecting archived memory into current reasoning.
- MEMORY_STORAGE_CHAR_BUDGET: max characters stored for each finalized mission memory summary.
- MEMORY_LINE_BUDGET: max non-empty lines preserved in memory payloads.

---

## Run

Start the interactive terminal experience:

```bash
uv run python main.py
```

Exit commands inside the prompt:
- exit
- quit
- q

---

## Testing

Run all tests:

```bash
uv run pytest -q
```

Run only supervisor tests:

```bash
uv run pytest -q tests/test_supervisor.py
```

---

## Project Structure

```text
main.py
src/
	agents/
		base.py
		supervisor.py
		researcher.py
		summarizer.py
		agent_helpers.py
	core/
		tools_registry.py
		llm.py
	tools/
		search_engine.py
		web_reader.py
	memory/
		vault.py
tests/
	test_brain.py
	test_memory_vault.py
	test_search_engine.py
	test_supervisor.py
	test_web_reader.py
```

---

## Design Principles

- Prefer high-signal memory over raw transcript dumps.
- Keep user wait time low using streaming and Rich status indicators.
- Prefer official sources for factual claims while still incorporating community evidence.
- Reject weak citations by construction.
- Keep behavior testable and deterministic where possible.

---

## Contributing

- Keep changes focused and test-backed.
- Preserve type safety and clear interfaces.
- Update tests when behavior changes.
- Keep prompt and citation policies consistent across agents.

---

## License

No license file is currently included in this repository.
Add a LICENSE file before publishing for open-source use.
