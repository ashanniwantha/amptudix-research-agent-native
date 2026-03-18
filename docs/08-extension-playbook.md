# 08. Extension Playbook

This playbook describes how to extend the project safely without regressing current behavior.

## Add a New Tool

1. Implement tool function in `src/tools/` with deterministic return shape.
2. Register schema in `src/core/tools_registry.py`.
3. Update `ResearcherAgent` tool handling branch:
   - parse tool args,
   - execute function,
   - convert output to prompt-safe string,
   - optionally map to `SourceCitation` entries.
4. Add tests for:
   - success path,
   - malformed args,
   - provider failure fallback.

## Add a New Source Category

1. Update classification hints in `src/agents/agent_helpers.py`.
2. Ensure category is preserved in `SourceCitation`.
3. Confirm Supervisor source mix logic still works.
4. Add tests for classification and final bibliography behavior.

## Modify Memory Budget Behavior

1. Adjust defaults in Supervisor constructor.
2. Keep `_read_int_env(...)` fallback semantics.
3. Update `.env` comments and README/docs.
4. Extend tests in `tests/test_supervisor.py` for new clipping rules.

## Change Research Routing Rules

1. Update `_should_research(...)` heuristic list and/or classifier prompt.
2. Validate with tests for both direct and research routes.
3. Log decision reason for diagnostics.

## Preserve Invariants (Do Not Break)

- Final response must stream to terminal for user-visible outputs.
- Invalid citations must be stripped.
- Bibliography must contain only validated sources.
- Memory retrieval/storage should pass through Summarizer path when available.
- Budget clipping must bound memory payload size.

## Recommended Engineering Guardrails

- Add mypy and ruff to CI before larger refactors.
- Keep tool outputs typed via `TypedDict` or dataclasses.
- Avoid silent broad `except Exception` where specific exceptions are possible.
- Prefer explicit integration boundaries over hidden side effects.

## Quick Checklist Before Merging Changes

- Tests pass locally (`uv run pytest -q`).
- Non-LLM tests pass in CI lane.
- New behavior has at least one regression test.
- Docs are updated in `docs/` and top-level README if user-facing behavior changed.
