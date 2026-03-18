# 06. Testing and CI

## Test Configuration

`pytest.ini` currently defines:
- markers:
  - `needs_llm`
  - `memory`
- default options: `-v -ra`
- test path: `tests`
- python path: project root (`.`)

## Existing Test Coverage

### `tests/test_supervisor.py`
Covers:
- research skip routing,
- citation sanitization and bibliography integrity,
- summarizer-mediated memory retrieval/storage,
- memory budget clipping,
- budget values loaded from environment.

### `tests/test_memory_vault.py`
Covers:
- store and retrieve happy path,
- chunking behavior,
- hybrid retrieval blend behavior (mocked candidates),
- empty-query retrieval behavior.

### `tests/test_search_engine.py`
Covers:
- search results mapping and field extraction,
- error fallback behavior.

### `tests/test_web_reader.py`
Covers:
- successful extraction path,
- extraction failure path,
- HTTP error path.

### `tests/test_brain.py`
Covers compatibility layer expectations for `Brain` adapter.

## CI Workflow

`.github/workflows/tests.yml`:
- triggers on push (`main`, `develop`) and PR (`main`),
- installs `uv`, installs Python 3.12,
- runs `uv sync --all-extras --dev`,
- executes `uv run pytest -m "not needs_llm"`.

This keeps CI stable without requiring local Ollama service.

## Current Strengths

- Deterministic non-LLM CI lane.
- Good unit-level coverage on new supervisor and memory behaviors.
- Tool tests use mocks to avoid flaky network dependency.

## Coverage Gaps to Address

- No end-to-end test for full Supervisor research path with streamed output.
- No regression tests for source category balancing expectations.
- No contract tests asserting exact prompt protocol for each agent.
- No performance tests for vector retrieval under larger datasets.

## Recommended Next Test Milestones

1. Add integration test that runs full `SamuraiSupervisor.run(...)` with mocked model/tool responses in both direct and research modes.
2. Add golden-file tests for final bibliography formatting and invalid-citation stripping edge cases.
3. Add stress test for `MemoryVault` retrieval with thousands of chunks.
4. Add static checks (ruff/mypy) into CI alongside pytest.
