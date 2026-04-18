import json
from wiki_agent_mcp.infrastructure.llm_client import LLMClient
from wiki_agent_mcp.storage.session import SessionMemory
from wiki_agent_mcp.storage.persistent import PersistentMemory

class BaseAgent:
    def __init__(self, llm_client: LLMClient, session_memory: SessionMemory, persistent_memory: PersistentMemory):
        self.llm = llm_client
        self.session = session_memory
        self.persistent = persistent_memory

    def _parse_json_response(self, response: str):
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            return json.loads(response.strip())
        except Exception:
            return None
