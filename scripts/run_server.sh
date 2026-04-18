#!/bin/bash
# Run the MCP server directly (for development)

cd "$(dirname "$0")/.."
source .venv/bin/activate
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export WIKI_DATA_DIR="./wiki_data"

python -m wiki_agent_mcp.server