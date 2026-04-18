# 🛠️ MCP Tools Reference

[**🏗️ Architecture**](architecture.md) | [**🧠 Storage & Memory**](storage.md)

## 🤖 Generation Tools

These tools leverage specialized AI agents to build the wiki in a structured, hierarchical manner.

### `generate_level1`
- **Agent:** Outline Architect
- **Description:** Conceptualizes the high-level structure of a new topic.
- **Input:** `topic` (string)
- **Output:** A JSON array of Level 1 sections (titles and paths).

### `generate_level2`
- **Agent:** Subtopic Expander
- **Description:** Breaks down a specific Level 1 section into more granular subtopics.
- **Input:** `topic`, `section_number`, `section_title`
- **Output:** A JSON array of Level 2 subtopics.

### `generate_level3`
- **Agent:** Article Writer
- **Description:** Produces a comprehensive, wiki-style article for a specific subtopic.
- **Input:** `topic`, `subtopic_number`, `subtopic_title`, `parent_section_title` (optional)
- **Output:** The full article in Markdown format.

---

## 🧠 Memory & Tracking Tools

Tools for managing the user's progress and exploration history.

### `record_visit`
- **Description:** Marks a specific node path as "explored". This is used by the recommendation engine to avoid suggesting things you've already read.
- **Input:** `node_path` (string)

### `get_session_summary`
- **Description:** Returns statistics about the current exploration session, including time elapsed and nodes visited.
- **Output:** JSON summary of session stats.

### `add_user_query`
- **Description:** Logs a specific question or query from the user. These queries are analyzed during report generation to identify knowledge gaps.
- **Input:** `query` (string)

---

## 📊 Analytics & Utility Tools

### `generate_report`
- **Description:** Generates a comprehensive Exploration Report. It analyzes your session history, identifies gaps in your research, and suggests the next logical steps.
- **Input:** `topic` (string)
- **Output:** A Markdown report.

### `search_level3`
- **Description:** Performs a full-text search across all generated Level 3 articles in the current session.
- **Input:** `keyword` (string)
- **Output:** A list of matching article paths.

### `get_level1`
- **Description:** Quickly retrieves the Level 1 Table of Contents if it has already been generated in the current session.
- **Input:** `topic` (string)
