# 04. Research Tools and Source Handling

## Tool Registry Contract

`src/core/tools_registry.py` exposes OpenAI-tool-compatible schemas:
- `search_web(query: string)`
- `fetch_web_content(url: string)`

Researcher passes these schemas to model tool-calling with `tool_choice="auto"`.

## search_web Tool (`src/tools/search_engine.py`)

Implementation:
- provider: `ddgs` (DuckDuckGo Search)
- output schema (`SearchResult` TypedDict):
  - `source`, `title`, `url`, `snippet`, `domain`, `rank`

Operational behavior:
- Emits Rich progress logs for discovered domains.
- Returns empty list on errors.

## fetch_web_content Tool (`src/tools/web_reader.py`)

Implementation:
- network: `httpx.get(..., follow_redirects=True)`
- extraction: `trafilatura.extract(..., output_format="markdown", include_links=True)`

Operational behavior:
- Returns extracted markdown text on success.
- Returns explicit string-form error messages on HTTP/extraction failures.

## Source Construction and Classification

`src/agents/agent_helpers.py`:
- Defines `SourceCitation` typed shape.
- Validates strict inclusion (title + URL required).
- Classifies URL host into:
  - `official`
  - `community`
  - `other`

Classification uses domain-hint lists (`OFFICIAL_HINTS`, `COMMUNITY_HINTS`).

## Validation and Bibliography Enforcement

Final source quality is ensured in Supervisor:
- sanitize list from Researcher,
- remove missing fields and duplicates,
- reindex citation numbers,
- strip invalid inline references,
- append verified bibliography block.

## Practical Reliability Considerations

- Prompt-level instructions alone are not sufficient for citation correctness.
- Post-processing safeguards are required for deterministic source integrity.
- Current approach already implements this layered defense.

## Improvement Opportunities

- Introduce URL normalization before dedupe (canonicalization).
- Add trust scoring beyond domain hints (publisher-level confidence).
- Cache fetched page content by URL hash to avoid repeated downloads.
- Add language/region filtering for query results.
