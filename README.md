# amptudix-research-agent-native

An experimental native Python research agent that can search the web, read page content, and use an LLM to produce structured research responses.

## Status

This project is **still under development**.

- APIs and module structure may change.
- Main entry points are not finalized yet.
- Expect breaking changes while features are evolving.

## Current Capabilities

- Web search via DuckDuckGo (`ddgs`)
- Web content extraction via `httpx` + `trafilatura`
- LLM integration through `openai`-compatible chat completions
- Rich terminal output for research workflow feedback
- Basic automated tests for search and web-reader tools

## Requirements

- Python 3.12+
- `uv` for dependency management and running commands

## Setup

```bash
uv sync
```

Create a `.env` file in the project root (example):

```env
OLLAMA_BASE_URL=http://localhost:11434/v1
MODEL_NAME=your-model-name
```

## Run Tests

```bash
uv run pytest
```

## Run a Manual Research Flow

There is no stable CLI command yet. For now, run the module directly:

```bash
uv run python -m src.core.llm
```

## Project Layout

```text
src/
	core/
		llm.py            # Brain/research orchestration
		tools_registry.py # Tool schemas for the model
	tools/
		search_engine.py  # Web search tool
		web_reader.py     # Web page fetch and extraction
tests/
	test_search_engine.py
	test_web_reader.py
```

## Notes for Contributors

- Keep changes small and tested.
- Prefer typed return values for tool outputs.
- Update tests whenever you change tool contracts.
