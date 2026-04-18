# Wiki Agent MCP Server

**Progressive, multi-agent wiki generator using Model Context Protocol (MCP).**  
Generate detailed, hierarchical wikis on **any topic** on-demand using LLM agents.  
Features session memory, persistent storage, exploration reports, and smart recommendations.

![MCP Badge](https://img.shields.io/badge/MCP-Protocol-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- **Three Agent Skills** – Different LLM personas for Level 1 (Outline Architect), Level 2 (Subtopic Expander), Level 3 (Article Writer)
- **Progressive Generation** – Generate content only when needed, not all at once
- **Session Memory** – Tracks visited nodes, queries, and session duration
- **Persistent Memory** – SQLite database stores summaries and recommendations
- **Exploration Reports** – Auto‑generated summaries with gaps and smart next‑read suggestions
- **Search & Bookmarks** – Full‑text search and bookmarking of nodes
- **Works with Any LLM** – OpenAI, Anthropic, Ollama (local), or any OpenAI‑compatible endpoint

---

## 🚀 Quick Start

### 1. Install `uv` (recommended) or pip

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
