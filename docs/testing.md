# 🧪 Testing Guide

There are several ways to test the Wiki Agent MCP server locally, ranging from automated unit tests to interactive manual testing.

## 1. Automated Testing (Pytest)

The project uses `pytest` for unit testing core logic like memory management and database operations.

```powershell
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v
```

---

## 2. Interactive Testing (MCP Inspector)

The **MCP Inspector** is the recommended way to test tool calls interactively without needing a full client like Claude Desktop.

```powershell
npx @modelcontextprotocol/inspector uv run python -m wiki_agent_mcp.main
```

This will:
1. Start the server.
2. Open a web interface (usually at `http://localhost:3000`).
3. Allow you to see available tools and trigger them with custom arguments.

---

## 3. Manual JSON-RPC Testing

Since MCP uses JSON-RPC over `stdio`, you can manually pipe commands into the server to verify the handshake and tool list.

### List Tools
```powershell
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | uv run python -m wiki_agent_mcp.main
```

### Call a Tool (Example: generate_level1)
```powershell
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"generate_level1","arguments":{"topic":"Quantum Computing"}}}' | uv run python -m wiki_agent_mcp.main
```

---

## 4. Claude Desktop Testing

To test the server in a real-world scenario with Claude:

1. Configure your `%APPDATA%\Roaming\Claude\claude_desktop_config.json` as described in the [README](../README.md#-claude-desktop-integration).
2. Restart Claude Desktop.
3. Look for the 🔌 icon to confirm the server is connected.
4. Try asking:
   - *"Generate a wiki outline for 'The History of Space Exploration'"*
   - *"Expand section 1"*
   - *"Write the article for subtopic 1.1"*
   - *"Show me an exploration report"*

---

## 🔍 Debugging

If the server fails to start or tools return errors:

1. **Check Logs**: Claude Desktop logs are located at `%APPDATA%\Roaming\Claude\logs\mcp.log`.
2. **Environment Variables**: Ensure `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is correctly set in your environment or Claude config.
3. **Data Directory**: Check if the data directory (default `~/Downloads/wikis`) is writable. You can verify the path in the server startup logs.
