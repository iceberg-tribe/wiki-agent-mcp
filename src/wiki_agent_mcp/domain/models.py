from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class SessionStats:
    nodes_visited: int
    paths: List[str]
    level1_topics: List[str]
    level2_sections: List[str]
    level3_articles: int
    session_duration_minutes: float
    user_queries: List[str]

@dataclass
class Recommendation:
    path: str
    reason: str
    timestamp: str

@dataclass
class TopicSummary:
    topic: str
    node_path: str
    summary: str
    last_accessed: str
