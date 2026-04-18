# 🧠 Storage & Memory Architecture

[**🏗️ Architecture**](architecture.md) | [**🛠️ Tools**](tools.md) | [**🧪 Testing**](testing.md)

## ⚡ Session Memory (Volatile)

The Session Memory layer lives in the server's RAM during a running session. It is designed for fast access to currently explored content.

- **Purpose:** Caching generated outlines, articles, and tracking current progress.
- **Data Tracked:**
    - `visited_nodes`: A list of all paths you have explored.
    - `generated_content`: Temporary cache for Level 1, 2, and 3 content to avoid redundant LLM calls.
    - `user_queries`: A log of questions asked during the session.
    - `session_timer`: Tracks the duration of your research session.

> [!NOTE]
> Session memory is cleared when the MCP server restarts.

---

## 💾 Persistent Memory (SQLite)

Persistent Memory ensures that the "soul" of your research is saved across sessions. It uses a lightweight SQLite database.

- **File Name:** `wiki_memory.db`
- **Tables:**
    - `topic_summaries`: Stores condensed summaries of every article you've generated. This allows the system to generate reports even if the full article content was from a previous session.
    - `user_recommendations`: Stores historically generated suggestions and the logic behind them.

### Database Schema
- **`topic_summaries`**: `(topic, node_path, summary, last_accessed)`
- **`user_recommendations`**: `(topic, recommended_path, reason, generated_at)`

---

## 📂 Data Directory Selection

The server automatically determines the best place to store your database and caches. It follows this priority:

1. **Environment Variable:** `WIKI_DATA_DIR` (if set and writable).
2. **User Downloads:** `~/Downloads/wikis`.
3. **Local AppData:** `%LOCALAPPDATA%\wiki_mcp` (Windows) or `~/.local/wiki_mcp` (Linux/macOS).
4. **Temporary Directory:** System temp folder (last resort).

### Troubleshooting Path Issues
You can see exactly where your data is being stored by checking the Claude Desktop logs or running the server in a terminal. Look for the `[wiki-agent] Data directory` log line.
