from datetime import datetime
from typing import Dict, List, Any
from wiki_agent_mcp.domain.models import SessionStats

class SessionMemory:
    """Tracks exploration within current session."""
    def __init__(self):
        self.visited_nodes: List[str] = []  # paths explored
        self.generated_level1: Dict[str, Any] = {}  # topic -> level1 data
        self.generated_level2: Dict[str, Dict] = {}  # "topic:section" -> level2 list
        self.generated_level3: Dict[str, str] = {}  # "topic:subtopic" -> content
        self.user_queries: List[str] = []
        self.start_time = datetime.now()

    def record_visit(self, node_path: str):
        if node_path not in self.visited_nodes:
            self.visited_nodes.append(node_path)

    def get_summary(self) -> Dict:
        return {
            "nodes_visited": len(self.visited_nodes),
            "paths": self.visited_nodes[:20],  # limit for display
            "level1_topics": list(self.generated_level1.keys()),
            "level2_sections": list(self.generated_level2.keys()),
            "level3_articles": len(self.generated_level3),
            "session_duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
            "user_queries": self.user_queries[-5:]  # last 5
        }
