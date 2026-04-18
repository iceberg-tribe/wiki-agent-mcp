# 🏗️ Architecture

Wiki Agent MCP follows a modular, domain-driven design to ensure maintainability and scalability. The project is split into several specialized layers.

## 📂 Project Structure

```text
src/wiki_agent_mcp/
├── main.py              # Entry point: handles server initialization and stdio
├── server.py            # MCP Interface: registers tools and coordinates components
├── agents/              # AI Logic: specialized agents for different wiki depths
│   ├── base.py          # Shared agent abstractions and prompt helpers
│   ├── architect.py     # Level 1: Conceptualizes high-level outlines
│   ├── expander.py      # Level 2: Breaks down sections into subtopics
│   └── writer.py        # Level 3: Writes comprehensive markdown articles
├── storage/             # Persistence: manages session and long-term data
│   ├── session.py       # In-memory tracking of current user exploration
│   └── persistent.py    # SQLite-backed storage for summaries and recommendations
├── domain/              # Business Logic: core types and reporting services
│   ├── models.py        # Dataclasses and shared types
│   └── reporting.py     # Generates gap analysis and research reports
├── infrastructure/      # External Clients: LLM provider abstractions
│   └── llm_client.py    # Handles OpenAI, Anthropic, and Ollama communication
└── utils/               # Utilities: configuration and directory management
    └── config.py        # Manages paths, env vars, and data root selection
```

---

## 🔄 Core Workflow

1. **Initialization**: `main.py` starts the server and initializes the data directories defined in `utils/config.py`.
2. **Tool Call**: When a tool (e.g., `generate_level1`) is called via `server.py`, it delegates the task to the appropriate agent in the `agents/` directory.
3. **LLM Interaction**: Agents use the `LLMClient` in `infrastructure/` to communicate with the chosen AI provider.
4. **Memory Update**: Results are cached in `storage/session.py` and summarized in the `storage/persistent.py` database.
5. **Reporting**: The `ReportingService` in `domain/` periodically analyzes the `SessionMemory` and `PersistentMemory` to provide research insights.

---

## 🛠️ Technology Stack

- **[MCP (Model Context Protocol)](https://modelcontextprotocol.io)**: For standardizing communication with LLM hosts.
- **Python 3.12+**: Utilizing modern features and typing.
- **SQLite**: For lightweight, file-based persistence.
- **[uv](https://github.com/astral-sh/uv)**: For fast, reliable dependency and environment management.
