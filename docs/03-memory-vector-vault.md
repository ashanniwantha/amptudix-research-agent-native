# 03. Memory and Vector Vault

## Storage Backend

`MemoryVault` uses ChromaDB persistent storage:
- client: `chromadb.PersistentClient(path=...)`
- default path: `data/vault_db`
- collection default: `agent_research`

## Embedding Strategy

- Primary embedding: `OllamaEmbeddingFunction` using `EMBEDDING_MODEL`.
- Fallback embedding: `DefaultEmbeddingFunction` if Ollama embedding init fails.

This fallback keeps tests/dev flow operational even if local embedding service is unavailable.

## Ingestion Pipeline

`store_research(topic, content)` flow:
1. Normalize whitespace.
2. Chunk content (default size 1000 chars).
3. Attach metadata per chunk:
   - `topic`
   - `chunk_index`
   - `stored_at` (epoch)
   - `char_count`
4. Write via `collection.add(...)`.
5. If add fails, fallback to `collection.upsert(...)`.

## Retrieval Pipeline

`retrieve_relevant_context(query, n_results=3)`:
1. Normalize query text.
2. Get hybrid-ranked docs via `_hybrid_rank(...)`.
3. Join selected chunks using `\n---\n` separators.

### Hybrid Ranking Mechanics

- Semantic signal:
  - `collection.query(include=[documents, distances])`
  - converts distance to score: $score = 1 / (1 + distance)$
  - weighted at 0.7
- Lexical signal:
  - token overlap score after stopword filtering
  - weighted at 0.3
- Final score:
  - blended by document key, then descending sort.

This approach improves robustness vs pure semantic retrieval, especially for exact technical terms.

## Summarizer-Gated Memory I/O

In supervisor flow, memory text is not used raw:
- retrieval context is condensed by Summarizer before prompt injection,
- storage payload is condensed by Summarizer before persistence.

Fallback behavior:
- if Summarizer returns empty or connection error, raw cleaned text is budget-clipped.

## Memory Budgets

Runtime-configurable budget controls:
- `MEMORY_RETRIEVAL_CHAR_BUDGET` (default 1800)
- `MEMORY_STORAGE_CHAR_BUDGET` (default 2200)
- `MEMORY_LINE_BUDGET` (default 24)

Budget algorithm:
1. collapse excessive blank lines,
2. keep first N non-empty lines,
3. enforce char cap,
4. append `...` on clipping.

## Current Strengths

- Persistent memory survives process restart.
- Retrieval combines meaning and lexical specificity.
- Storage includes useful metadata for future filtering.
- Budget constraints prevent context explosion.

## Current Constraints

- Chunking is fixed-length, not semantic-boundary aware.
- No recency/importance decay scoring yet.
- No topic-level namespace/tenant partitioning.
- No periodic dedupe/pruning job for stale chunks.
