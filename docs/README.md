# AMPTUDIX Technical Documentation

This folder contains a full technical analysis of the project, organized by subsystem.

## Document Map

1. [01-system-overview.md](01-system-overview.md)
   - Purpose, current capabilities, request lifecycle, and repository map.
2. [02-agent-orchestration.md](02-agent-orchestration.md)
   - Detailed behavior of Supervisor, Researcher, Summarizer, and BaseAgent.
3. [03-memory-vector-vault.md](03-memory-vector-vault.md)
   - Chroma storage model, hybrid retrieval, budgeting, and summarizer-gated memory flow.
4. [04-research-tools-and-sources.md](04-research-tools-and-sources.md)
   - Search and web extraction tools, source validation/classification, and citation pipeline.
5. [05-configuration-and-runtime.md](05-configuration-and-runtime.md)
   - Environment variables, startup flow, dependencies, and runtime behavior.
6. [06-testing-and-ci.md](06-testing-and-ci.md)
   - Current test coverage, CI behavior, and testing strategy.
7. [07-known-gaps-and-improvements.md](07-known-gaps-and-improvements.md)
   - Risks, constraints, and prioritized improvement roadmap.
8. [08-extension-playbook.md](08-extension-playbook.md)
   - How to safely add tools, policies, and new agent capabilities.
9. [09-architecture-diagram.md](09-architecture-diagram.md)
   - End-to-end system flow and component interactions as a Mermaid diagram.

## Reader Guidance

- Start with `01-system-overview.md` if you are new to the codebase.
- Open [09-architecture-diagram.md](09-architecture-diagram.md) for a visual system map first if you prefer diagram-led onboarding.
- Read `02-agent-orchestration.md` + `03-memory-vector-vault.md` for behavior and data flow.
- Use `07-known-gaps-and-improvements.md` for planning next milestones.
