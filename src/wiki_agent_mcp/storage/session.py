import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class SessionMemory:
    """Tracks exploration within current session with disk persistence."""
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir
        self.visited_nodes: List[str] = []
        self.generated_level1: Dict[str, Any] = {}
        self.generated_level2: Dict[str, List] = {}
        self.generated_level3: Dict[str, str] = {}
        self.user_queries: List[str] = []
        self.start_time = datetime.now()
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()

    def record_visit(self, node_path: str):
        if node_path not in self.visited_nodes:
            self.visited_nodes.append(node_path)
            self._save_session_state()

    def add_query(self, query: str):
        self.user_queries.append(query)
        self._save_session_state()

    def _save_session_state(self):
        """Save the structural state (visited nodes, queries)."""
        if not self.cache_dir: return
        state = {
            "visited_nodes": self.visited_nodes,
            "user_queries": self.user_queries,
            "level1_topics": list(self.generated_level1.keys()),
            "level2_keys": list(self.generated_level2.keys())
        }
        with open(self.cache_dir / "session_state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def save_level1(self, topic: str, data: List[Dict]):
        self.generated_level1[topic] = data
        if self.cache_dir:
            path = self.cache_dir / f"l1_{self._safe_name(topic)}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self._save_session_state()

    def save_level2(self, cache_key: str, data: List[Dict]):
        self.generated_level2[cache_key] = data
        if self.cache_dir:
            path = self.cache_dir / f"l2_{self._safe_name(cache_key)}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self._save_session_state()

    def save_level3(self, cache_key: str, content: str):
        self.generated_level3[cache_key] = content
        if self.cache_dir:
            path = self.cache_dir / f"l3_{self._safe_name(cache_key)}.md"
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self._save_session_state()

    def _load_from_disk(self):
        """Rehydrate memory from disk files."""
        if not self.cache_dir: return
        
        # Load state
        state_path = self.cache_dir / "session_state.json"
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
                self.visited_nodes = state.get("visited_nodes", [])
                self.user_queries = state.get("user_queries", [])

        # Load all JSON files for L1 and L2
        for p in self.cache_dir.glob("l1_*.json"):
            topic = p.stem.replace("l1_", "")
            with open(p, "r", encoding="utf-8") as f:
                self.generated_level1[topic] = json.load(f)

        for p in self.cache_dir.glob("l2_*.json"):
            key = p.stem.replace("l2_", "")
            with open(p, "r", encoding="utf-8") as f:
                self.generated_level2[key] = json.load(f)

        # Load all MD files for L3
        for p in self.cache_dir.glob("l3_*.md"):
            key = p.stem.replace("l3_", "")
            with open(p, "r", encoding="utf-8") as f:
                self.generated_level3[key] = f.read()

    def _safe_name(self, name: str) -> str:
        return "".join([c if c.isalnum() else "_" for c in name])

    def get_summary(self) -> Dict:
        return {
            "nodes_visited": len(self.visited_nodes),
            "paths": self.visited_nodes[-20:], 
            "level1_topics": list(self.generated_level1.keys()),
            "level2_sections": list(self.generated_level2.keys()),
            "level3_articles": len(self.generated_level3),
            "session_duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
            "user_queries": self.user_queries[-10:]
        }
