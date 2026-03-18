# 09. Architecture Diagram

This page provides a visual map of the runtime architecture and request lifecycle.

## End-to-End Flow

```mermaid
flowchart TD
    U[User Terminal Input] --> M[main.py CLI Loop]
    M --> S[SamuraiSupervisor.run]

    S --> VR[Vault Retrieve Context]
    VR --> V[(ChromaDB Persistent Collection)]

    S --> SR[Summarizer Condense Retrieval Context]
    SR --> RGate{Should Research?}

    RGate -->|No| DResp[Generate Direct Response]
    RGate -->|Yes| Scout[ResearcherAgent Tool Loop]

    Scout --> TR[Tool Registry Definitions]
    Scout --> SW[search_web via DDGS]
    Scout --> FW[fetch_web_content via HTTPX + Trafilatura]
    FW --> SS[Summarizer Condense Fetched Content]

    Scout --> Src[Collected Sources]
    Src --> San[Supervisor Source Sanitize + Reindex]

    DResp --> Final[Final Answer Draft]
    San --> RF[Generate Research Final Answer]
    RF --> Final

    Final --> CI[Strip Invalid Citations]
    CI --> Bib[Append Verified Bibliography]
    Bib --> Out[Streamed Terminal Output]

    Bib --> MS[Summarizer Condense Storage Memory]
    MS --> MB[Apply Memory Budgets]
    MB --> VW[Vault Store Research Chunks]
    VW --> V

    style S fill:#f5f0ff,stroke:#5a3ea8,stroke-width:1.5px
    style Scout fill:#e9f8ff,stroke:#1c6ea4,stroke-width:1.5px
    style V fill:#f0fff3,stroke:#2f7d32,stroke-width:1.5px
```

## Key Boundaries

- Orchestration boundary: `SamuraiSupervisor` is the single control plane for routing, memory, and source policy.
- Research boundary: `ResearcherAgent` performs tool-calling and source gathering only.
- Compression boundary: `SummarizerAgent` is used for context and memory compaction.
- Persistence boundary: `MemoryVault` owns vector ingestion and retrieval.

## Policy Enforcement Points

- Research routing gate: decides direct answer vs external research mode.
- Source validation gate: removes invalid or duplicate sources and reindexes citation IDs.
- Citation cleanup gate: strips references that do not map to validated sources.
- Memory budget gate: caps storage and retrieval payload sizes by lines and characters.

## Diagram Notes

- The direct path and research path converge before final citation cleanup.
- Storage writes occur after final synthesis and memory summarization.
- Retrieval and storage both pass through summarization to keep context high signal.
