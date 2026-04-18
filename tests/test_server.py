import pytest
from wiki_agent_mcp.server import SessionMemory, PersistentMemory

def test_session_memory():
    mem = SessionMemory()
    mem.record_visit("test > 1")
    assert "test > 1" in mem.visited_nodes
    summary = mem.get_summary()
    assert summary["nodes_visited"] == 1

def test_persistent_memory(tmp_path):
    db_path = tmp_path / "test.db"
    mem = PersistentMemory(db_path=db_path)
    mem.save_summary("topic", "node", "summary text")
    retrieved = mem.get_summary("topic", "node")
    assert retrieved == "summary text"