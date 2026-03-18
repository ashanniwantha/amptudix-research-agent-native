# 05. Configuration and Runtime

## Python and Dependency Baseline

From `pyproject.toml`:
- Python: `>=3.12`
- Core dependencies:
  - `openai`
  - `chromadb`
  - `ddgs`
  - `httpx`
  - `trafilatura`
  - `rich`
  - `python-dotenv`
- Test dependencies currently listed in main dependency set:
  - `pytest`
  - `pytest-cov`
  - `pytest-mock`
  - `respx`

## Environment Variables

Current `.env` categories:

### LLM Runtime
- `MODEL_NAME`
- `OLLAMA_BASE_URL`

### Embeddings / Vector Memory
- `EMBEDDING_MODEL`

### Memory Budget Controls
- `MEMORY_RETRIEVAL_CHAR_BUDGET`
- `MEMORY_STORAGE_CHAR_BUDGET`
- `MEMORY_LINE_BUDGET`

Supervisor safely parses budget values:
- invalid or non-positive values fall back to defaults.

## Entrypoints

- Primary CLI entrypoint: `main.py`
  - creates `SamuraiSupervisor`
  - loops on user commands until `exit/quit/q`
- Secondary file: `src/main.py` is present but empty.

## Runtime Behavior Summary

1. `dotenv` loads configuration.
2. BaseAgent initializes OpenAI-compatible client.
3. Supervisor initializes nested agents and MemoryVault.
4. User command triggers orchestration flow.
5. Final answer is streamed in terminal (for visible responses).

## Operational Assumptions

- Local Ollama-style endpoint is available for chat model.
- Embedding model endpoint is available unless fallback path is used.
- Persistent disk path for Chroma (`data/vault_db`) is writable.

## Configuration Hygiene Recommendations

- Add `.env.example` to document safe defaults without secrets.
- Keep production and local configs separated via profile files.
- Consider validating mandatory env vars at startup with clear fail-fast messages.
- Add optional `LOG_LEVEL` and structured logging config to improve observability.
