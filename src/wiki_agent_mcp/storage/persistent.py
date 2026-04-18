import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Optional
from wiki_agent_mcp.utils.config import DB_PATH

class PersistentMemory:
    """Long-term storage per topic (SQLite)."""
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_summaries (
                topic TEXT,
                node_path TEXT,
                summary TEXT,
                last_accessed TIMESTAMP,
                PRIMARY KEY (topic, node_path)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_recommendations (
                topic TEXT,
                recommended_path TEXT,
                reason TEXT,
                generated_at TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save_summary(self, topic: str, node_path: str, summary: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO topic_summaries (topic, node_path, summary, last_accessed)
            VALUES (?, ?, ?, ?)
        """, (topic, node_path, summary, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_summary(self, topic: str, node_path: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT summary FROM topic_summaries WHERE topic=? AND node_path=?", (topic, node_path))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_all_summaries_for_topic(self, topic: str) -> Dict[str, str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT node_path, summary FROM topic_summaries WHERE topic=?", (topic,))
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def save_recommendation(self, topic: str, recommended_path: str, reason: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_recommendations (topic, recommended_path, reason, generated_at)
            VALUES (?, ?, ?, ?)
        """, (topic, recommended_path, reason, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_recommendations(self, topic: str, limit: int = 10) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT recommended_path, reason, generated_at FROM user_recommendations
            WHERE topic=? ORDER BY generated_at DESC LIMIT ?
        """, (topic, limit))
        rows = cursor.fetchall()
        conn.close()
        return [{"path": r[0], "reason": r[1], "timestamp": r[2]} for r in rows]
