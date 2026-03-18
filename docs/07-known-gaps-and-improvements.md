# 07. Known Gaps and Improvement Roadmap

## High Priority

### 1) Prompt/Policy Externalization
Current state:
- Policy logic is mixed in code and inline prompt strings.

Risk:
- Harder to version, review, and A/B test behavioral policies.

Recommendation:
- Move system prompts and policy templates into dedicated prompt files under `src/prompts/` with version tags.

### 2) Observability and Diagnostics
Current state:
- Rich console output exists, but no structured logs/trace IDs.

Risk:
- Hard to debug production incidents or evaluate routing quality over time.

Recommendation:
- Add structured event logging for route decisions, tool call counts, source counts, and memory budget clipping events.

### 3) Retrieval Quality Controls
Current state:
- Hybrid semantic + lexical ranking exists.

Risk:
- No quality metrics or offline eval set to validate retrieval improvements.

Recommendation:
- Build a small benchmark set of queries and expected memory snippets; track retrieval precision/recall over changes.

## Medium Priority

### 4) Source Trust Model Upgrade
Current state:
- Domain-hint based source classification.

Risk:
- Domain heuristics can over/under-classify reliability.

Recommendation:
- Add trust scoring layer (publisher metadata, HTTPS enforcement, recency, duplicate corroboration).

### 5) Chunking and Memory Lifecycle
Current state:
- Fixed-size chunking and no pruning policy.

Risk:
- Long-term storage growth and relevance drift.

Recommendation:
- Adopt sentence/paragraph-aware chunking and implement periodic cleanup (dedupe + decay + archive).

### 6) Runtime Validation and Health Checks
Current state:
- Environment assumptions are implicit.

Risk:
- Failures discovered late during requests.

Recommendation:
- Add startup health checks for model endpoint, embedding endpoint, and DB write path.

## Lower Priority but Valuable

### 7) Packaging and Distribution Hygiene
Current state:
- `description` in `pyproject.toml` is placeholder.
- no `LICENSE` file yet.

Recommendation:
- Finalize project metadata and licensing before open publication.

### 8) API Surface Clarity
Current state:
- Internal methods are clear but not formally documented as contracts.

Recommendation:
- Add protocol docs for agent input/output types and expected invariants.

## Suggested Delivery Plan

1. Milestone A: prompts externalization + startup validation + structured logging.
2. Milestone B: retrieval evaluation harness + memory lifecycle controls.
3. Milestone C: trust model improvements + integration/performance testing.
4. Milestone D: packaging polish and release readiness.
