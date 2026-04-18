# ADR 001: Premium Session-Oriented Architecture

## Status
Accepted (2026-04-18)

## Context
The initial implementation of the Wiki Agent was a reactive tool that generated content on-demand but lacked a professional "research workflow." Users would often generate content and lose it upon server restart, or struggle to know which section to explore next. We wanted to move towards a "Premium Research Assistant" experience.

## Decision
We decided to adopt a **Session-Oriented Managed Lifecycle** combined with **Zero-Loss Persistence**.

### Key Components:
1.  **Managed Lifecycle**: Defined in `SKILL.md`, enforcing a strict Initiation → Exploration → Closure workflow.
2.  **Dual-Layer Storage**:
    - **Session Cache (Disk)**: Storing full Markdown/JSON blobs in a `wiki_cache/` folder to ensure zero-loss across restarts.
    - **Analytical DB (SQLite)**: Storing metadata and summaries for cross-session intelligence and gap analysis.
3.  **Proactive Guidance**: Introducing a `suggest_next_steps` tool that uses historical context to guide the user, moving from a "reactive" to a "proactive" agent model.

## Consequences

### Positive:
- **Economy**: Drastic reduction in LLM tokens by serving cached content locally.
- **UX**: The agent behaves like a professional tutor/assistant with a clear beginning, middle, and end.
- **Reliability**: Research is persistent and recoverable.

### Negative:
- **Disk Usage**: Increased local storage for full article blobs.
- **Complexity**: Agents must now coordinate with a multi-layer storage system instead of a simple in-memory dict.

## Alternatives Considered
- **Pure Vector DB (RAG)**: Rejected for the initial version due to increased setup complexity for the user. The current hierarchical structure (L1/L2/L3) provides enough context without needing a vector index yet.
- **In-Memory Only**: Rejected as it failed the "Premium" requirement of data reliability.
