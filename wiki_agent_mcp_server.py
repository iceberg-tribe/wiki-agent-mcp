#!/usr/bin/env python3
"""
MCP Server for Progressive Wiki Generation with Multi-Agent LLM and Memory Layers
- Level 1: Outline Architect agent
- Level 2: Subtopic Expander agent  
- Level 3: Article Writer agent
- Memory: Session (visited nodes) + Persistent (summaries per topic)
- Report generation based on exploration
"""

import json
import os
import sqlite3
import hashlib
from datetime import datetime
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field, asdict
import difflib

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# -------------------------------
# Robust Data Directory Selection
# -------------------------------
print("[wiki-agent] Script started", file=sys.stderr)
sys.stderr.flush()

def get_data_root() -> Path:
    """Determine a writable directory for wiki data (database, cache)."""
    # 1. Environment variable (highest priority)
    env_dir = os.environ.get("WIKI_DATA_DIR")
    if env_dir:
        path = Path(env_dir)
        try:
            path.mkdir(parents=True, exist_ok=True)
            # Test writability
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return path
        except Exception as e:
            print(f"WARNING: Cannot use WIKI_DATA_DIR={env_dir}: {e}", file=sys.stderr)
    
    # 2. User's Downloads folder
    downloads = Path.home() / "Downloads" / "wikis"
    try:
        downloads.mkdir(parents=True, exist_ok=True)
        test_file = downloads / ".write_test"
        test_file.touch()
        test_file.unlink()
        return downloads
    except Exception as e:
        print(f"WARNING: Cannot use Downloads folder: {e}", file=sys.stderr)
    
    # 3. AppData\Local (Windows) or ~/.local (Unix)
    appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local")) / "wiki_mcp"
    try:
        appdata.mkdir(parents=True, exist_ok=True)
        test_file = appdata / ".write_test"
        test_file.touch()
        test_file.unlink()
        return appdata
    except Exception as e:
        print(f"WARNING: Cannot use AppData: {e}", file=sys.stderr)
    
    # 4. Temp directory (last resort)
    import tempfile
    temp_dir = Path(tempfile.gettempdir()) / "wiki_mcp_data"
    temp_dir.mkdir(exist_ok=True)
    print(f"Using temporary directory: {temp_dir}", file=sys.stderr)
    return temp_dir

DATA_ROOT = get_data_root()
DB_PATH = DATA_ROOT / "wiki_memory.db"
CACHE_DIR = DATA_ROOT / "wiki_cache"
CACHE_DIR.mkdir(exist_ok=True)

# Log the actual paths to stderr (visible in Claude Desktop logs)
print(f"[wiki-agent] Data directory: {DATA_ROOT}", file=sys.stderr)
print(f"[wiki-agent] Database path: {DB_PATH}", file=sys.stderr)
print(f"[wiki-agent] DATA_ROOT = {DATA_ROOT}", file=sys.stderr)
print(f"[wiki-agent] DB_PATH = {DB_PATH}", file=sys.stderr)
print(f"[wiki-agent] CACHE_DIR = {CACHE_DIR}", file=sys.stderr)
sys.stderr.flush()



# -------------------------------
# LLM Client (supports multiple providers)
# -------------------------------

class LLMClient:
    def __init__(self, provider: str = "openai", model: str = None, api_key: str = None, base_url: str = None):
        self.provider = provider.lower()
        self.model = model or self._default_model()
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        self.base_url = base_url

    def _default_model(self):
        if self.provider == "openai":
            return "gpt-4-turbo-preview"
        elif self.provider == "anthropic":
            return "claude-3-opus-20240229"
        elif self.provider == "ollama":
            return "llama3"
        return "gpt-3.5-turbo"

    def generate(self, prompt: str, system: str = None, temperature: float = 0.3) -> str:
        if self.provider == "openai":
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        elif self.provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            # Anthropic uses system param separately
            response = client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=temperature,
                system=system or "",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        elif self.provider == "ollama":
            import requests
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            resp = requests.post(
                f"{self.base_url or 'http://localhost:11434'}/api/generate",
                json={"model": self.model, "prompt": full_prompt, "stream": False}
            )
            return resp.json()["response"]
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

# -------------------------------
# Memory Layers
# -------------------------------

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

class PersistentMemory:
    """Long-term storage per topic (SQLite)."""
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        print(f"[wiki-agent] PersistentMemory init, db_path = {self.db_path}", file=sys.stderr)
        sys.stderr.flush()
        self._init_db()

    def _init_db(self):
        print(f"[wiki-agent] Attempting to connect to {self.db_path}", file=sys.stderr)
        sys.stderr.flush()
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

# -------------------------------
# Multi-Agent Wiki Generator
# -------------------------------

class WikiAgentGenerator:
    def __init__(self, llm_client: LLMClient, session_memory: SessionMemory, persistent_memory: PersistentMemory):
        self.llm = llm_client
        self.session = session_memory
        self.persistent = persistent_memory

    # Agent 1: Outline Architect (Level 1)
    def generate_level1_toc(self, topic: str) -> List[Dict[str, Any]]:
        """Generate main Level 1 headings for the topic."""
        # Check session cache
        if topic in self.session.generated_level1:
            return self.session.generated_level1[topic]

        system = "You are an expert Outline Architect. Your task is to create a comprehensive, well-structured Table of Contents (Level 1 headings) for a wiki article on a given topic. Output only valid JSON."
        prompt = f"""Create a Level 1 Table of Contents for a wiki article on "{topic}".

Requirements:
- 8 to 15 main sections (number them 1, 2, 3...)
- Each section should have a clear, descriptive title (e.g., "Introduction & Core Definition", "History & Evolution", "Key Methodologies")
- Ensure logical flow from introductory to advanced topics
- Include practical sections like "Tools & Techniques", "Legal & Ethical Considerations", "Case Studies", "Future Trends"

Output format (JSON array):
[
  {{"number": 1, "title": "Introduction & Core Definition", "path": "{topic} > 1"}},
  {{"number": 2, "title": "...", "path": "{topic} > 2"}},
  ...
]

Return ONLY the JSON array, no extra text."""
        
        response = self.llm.generate(prompt, system=system, temperature=0.4)
        try:
            # Extract JSON from response (in case LLM adds markdown)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            level1 = json.loads(response)
            # Ensure each has path field
            for item in level1:
                if "path" not in item:
                    item["path"] = f"{topic} > {item['number']}"
            self.session.generated_level1[topic] = level1
            return level1
        except Exception as e:
            # Fallback generic TOC
            fallback = [
                {"number": 1, "title": "Introduction & Core Definition", "path": f"{topic} > 1"},
                {"number": 2, "title": "History & Evolution", "path": f"{topic} > 2"},
                {"number": 3, "title": "Core Methodologies & Frameworks", "path": f"{topic} > 3"},
                {"number": 4, "title": "Key Tools & Technologies", "path": f"{topic} > 4"},
                {"number": 5, "title": "Legal & Ethical Landscape", "path": f"{topic} > 5"},
                {"number": 6, "title": "Case Studies & Real-World Applications", "path": f"{topic} > 6"},
                {"number": 7, "title": "Future Trajectories & Challenges", "path": f"{topic} > 7"},
            ]
            self.session.generated_level1[topic] = fallback
            return fallback

    # Agent 2: Subtopic Expander (Level 2)
    def generate_level2_subtopics(self, topic: str, section_number: str, section_title: str) -> List[Dict[str, Any]]:
        """Generate Level 2 subtopics under a given Level 1 section."""
        cache_key = f"{topic}:{section_number}"
        if cache_key in self.session.generated_level2:
            return self.session.generated_level2[cache_key]

        system = "You are a Subtopic Expander. Given a main section title, generate 4-8 relevant Level 2 subtopics. Output JSON only."
        prompt = f"""For the wiki topic "{topic}", the Level 1 section "{section_number}. {section_title}" needs Level 2 subtopics.

Generate a numbered list of subtopics (e.g., 3.1, 3.2, ...) that logically expand this section.

Output format (JSON array):
[
  {{"number": "{section_number}.1", "title": "Specific Subtopic Title", "path": "{topic} > {section_number} > {section_number}.1"}},
  {{"number": "{section_number}.2", "title": "...", "path": "..."}}
]

Ensure subtopics are distinct, informative, and cover the key aspects of the main section.
Return ONLY the JSON array."""
        
        response = self.llm.generate(prompt, system=system, temperature=0.4)
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            level2 = json.loads(response)
            self.session.generated_level2[cache_key] = level2
            return level2
        except:
            # Fallback generic subtopics
            fallback = [
                {"number": f"{section_number}.1", "title": "Foundational Concepts", "path": f"{topic} > {section_number} > {section_number}.1"},
                {"number": f"{section_number}.2", "title": "Key Principles", "path": f"{topic} > {section_number} > {section_number}.2"},
                {"number": f"{section_number}.3", "title": "Practical Applications", "path": f"{topic} > {section_number} > {section_number}.3"},
                {"number": f"{section_number}.4", "title": "Common Challenges", "path": f"{topic} > {section_number} > {section_number}.4"},
            ]
            self.session.generated_level2[cache_key] = fallback
            return fallback

    # Agent 3: Article Writer (Level 3)
    def generate_level3_article(self, topic: str, subtopic_number: str, subtopic_title: str, parent_section_title: str = "") -> str:
        """Generate dense, wiki-style article for a Level 3 subtopic."""
        cache_key = f"{topic}:{subtopic_number} {subtopic_title}"
        if cache_key in self.session.generated_level3:
            return self.session.generated_level3[cache_key]

        # Check persistent memory for previously generated summary? 
        # For article, we want full content, but we can use persistent to store summary after generation.
        
        system = "You are an expert Wiki Article Writer. Produce dense, factual, well-structured content (500-1500 words) suitable for a technical encyclopedia entry."
        prompt = f"""Write a detailed wiki-style article for the following subtopic:

Topic: "{topic}"
Section: "{parent_section_title}" (if provided)
Subtopic: "{subtopic_number} {subtopic_title}"

Requirements:
- Start with a clear definition or overview paragraph.
- Use subheadings (##, ###) for structure.
- Include technical details, examples, historical context where relevant.
- Cite key facts, dates, methodologies, or tools.
- End with a "See Also" or "Further Reading" section with 2-4 related subtopics (suggest cross-references).
- Length: approximately 800-1200 words.

Output in Markdown format."""
        
        response = self.llm.generate(prompt, system=system, temperature=0.5)
        # Store in session cache
        self.session.generated_level3[cache_key] = response
        # Also store a summary in persistent memory for future report generation
        summary = self._summarize_article(response, max_chars=300)
        self.persistent.save_summary(topic, cache_key, summary)
        return response

    def _summarize_article(self, article: str, max_chars: int = 300) -> str:
        """Extract first few sentences or use LLM to summarize."""
        # Simple truncation: take first non-header paragraph
        lines = article.splitlines()
        text = []
        for line in lines:
            if line.startswith('#'):
                continue
            if line.strip():
                text.append(line.strip())
            if len(' '.join(text)) > max_chars:
                break
        summary = ' '.join(text)[:max_chars]
        if len(summary) >= max_chars:
            summary = summary.rsplit(' ', 1)[0] + "..."
        return summary

    # Report Generator
    def generate_exploration_report(self, topic: str) -> str:
        """Create a report summarizing what the user explored and suggest next readings."""
        session_summary = self.session.get_summary()
        persistent_summaries = self.persistent.get_all_summaries_for_topic(topic)
        recommendations = self.persistent.get_recommendations(topic)

        # Build report using LLM for narrative
        system = "You are a research assistant. Create a concise, insightful report based on the user's exploration history and available summaries."
        
        visited_nodes_text = "\n".join(session_summary["paths"]) if session_summary["paths"] else "None yet."
        summaries_text = "\n".join([f"- {path}: {summary[:100]}..." for path, summary in list(persistent_summaries.items())[:5]])
        recs_text = "\n".join([f"- {r['path']}: {r['reason']}" for r in recommendations[:5]]) if recommendations else "No recommendations yet."

        prompt = f"""Generate an exploration report for topic "{topic}".

**User's session exploration:**
Visited nodes: {session_summary['nodes_visited']}
Paths explored:
{visited_nodes_text}

Session duration: {session_summary['session_duration_minutes']:.1f} minutes
Recent queries: {', '.join(session_summary['user_queries'])}

**Persistent memory summaries (top 5):**
{summaries_text}

**Previous recommendations:**
{recs_text}

Your report should include:
1. Summary of what the user has learned (based on visited nodes and summaries)
2. Gaps or missing areas (unexplored important sections)
3. Suggested next readings (specific node paths) with reasons
4. Optional: key takeaways or cross-cutting themes

Output in Markdown format, friendly but professional."""
        
        report = self.llm.generate(prompt, system=system, temperature=0.4)
        # Also generate and store new recommendations based on gaps
        self._generate_smart_recommendations(topic)
        return report

    def _generate_smart_recommendations(self, topic: str):
        """Use LLM to recommend unexplored nodes based on session history and persistent summaries."""
        # Get all available Level 1 and Level 2 paths from session memory
        all_level1 = self.session.generated_level1.get(topic, [])
        all_level2 = []
        for key, l2list in self.session.generated_level2.items():
            if key.startswith(f"{topic}:"):
                all_level2.extend(l2list)
        
        visited = set(self.session.visited_nodes)
        # Find unvisited nodes
        unvisited = []
        for item in all_level1:
            path = item.get("path", f"{topic} > {item['number']}")
            if path not in visited:
                unvisited.append(path)
        for item in all_level2:
            path = item.get("path", "")
            if path and path not in visited:
                unvisited.append(path)
        
        if not unvisited:
            return
        
        system = "You are a recommendation engine. Suggest the most valuable unvisited nodes for the user to explore next."
        prompt = f"""Topic: {topic}
User has already explored: {', '.join(list(visited)[:10])}
Available unvisited nodes: {', '.join(unvisited[:15])}

Recommend up to 3 specific nodes from the unvisited list that would be most valuable to explore next, based on typical learning progression and logical dependencies.
For each, provide a short reason (one sentence).

Output JSON:
[
  {{"path": "exact path string", "reason": "because..."}},
  ...
]"""
        response = self.llm.generate(prompt, system=system, temperature=0.3)
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            recs = json.loads(response)
            for rec in recs:
                self.persistent.save_recommendation(topic, rec["path"], rec["reason"])
        except:
            # Fallback: recommend first unvisited
            if unvisited:
                self.persistent.save_recommendation(topic, unvisited[0], "Logical next step based on your exploration.")
        
# -------------------------------
# MCP Server Integration
# -------------------------------

# Global state
session_memory = SessionMemory()
persistent_memory = PersistentMemory()
llm_client = LLMClient(provider=os.environ.get("LLM_PROVIDER", "openai"), 
                       model=os.environ.get("LLM_MODEL", None))
wiki_gen = WikiAgentGenerator(llm_client, session_memory, persistent_memory)

server = Server("wiki-agent-server")

# Helper to get topic from arguments or current session
current_topic = None

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_level1",
            description="Generate Level 1 Table of Contents for a topic using Outline Architect agent.",
            inputSchema={
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"]
            }
        ),
        types.Tool(
            name="get_level1",
            description="Retrieve cached Level 1 ToC for a topic (if already generated).",
            inputSchema={"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]}
        ),
        types.Tool(
            name="generate_level2",
            description="Generate Level 2 subtopics for a specific Level 1 section using Subtopic Expander agent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "section_number": {"type": "string"},
                    "section_title": {"type": "string"}
                },
                "required": ["topic", "section_number", "section_title"]
            }
        ),
        types.Tool(
            name="generate_level3",
            description="Generate a dense Level 3 article for a subtopic using Article Writer agent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "subtopic_number": {"type": "string"},
                    "subtopic_title": {"type": "string"},
                    "parent_section_title": {"type": "string"}
                },
                "required": ["topic", "subtopic_number", "subtopic_title"]
            }
        ),
        types.Tool(
            name="record_visit",
            description="Record that the user explored a specific node path (for session memory).",
            inputSchema={
                "type": "object",
                "properties": {"node_path": {"type": "string"}},
                "required": ["node_path"]
            }
        ),
        types.Tool(
            name="generate_report",
            description="Generate an exploration report with summary, gaps, and recommendations.",
            inputSchema={
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"]
            }
        ),
        types.Tool(
            name="get_session_summary",
            description="Get a summary of current session memory.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="add_user_query",
            description="Record a user query for session memory.",
            inputSchema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        ),
        # Reuse previous UX tools (search, bookmark, etc.) – simplified here for brevity
        types.Tool(
            name="search_level3",
            description="Search generated Level 3 articles for keyword.",
            inputSchema={"type": "object", "properties": {"keyword": {"type": "string"}}, "required": ["keyword"]}
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    global current_topic
    try:
        if name == "generate_level1":
            topic = arguments["topic"]
            current_topic = topic
            level1 = wiki_gen.generate_level1_toc(topic)
            result = json.dumps(level1, indent=2)
        elif name == "get_level1":
            topic = arguments["topic"]
            if topic in session_memory.generated_level1:
                result = json.dumps(session_memory.generated_level1[topic], indent=2)
            else:
                result = f"No Level 1 generated for '{topic}'. Use generate_level1 first."
        elif name == "generate_level2":
            topic = arguments["topic"]
            section_num = arguments["section_number"]
            section_title = arguments["section_title"]
            level2 = wiki_gen.generate_level2_subtopics(topic, section_num, section_title)
            result = json.dumps(level2, indent=2)
        elif name == "generate_level3":
            topic = arguments["topic"]
            sub_num = arguments["subtopic_number"]
            sub_title = arguments["subtopic_title"]
            parent_title = arguments.get("parent_section_title", "")
            article = wiki_gen.generate_level3_article(topic, sub_num, sub_title, parent_title)
            result = article
        elif name == "record_visit":
            node_path = arguments["node_path"]
            session_memory.record_visit(node_path)
            result = f"Recorded visit to: {node_path}"
        elif name == "generate_report":
            topic = arguments["topic"]
            report = wiki_gen.generate_exploration_report(topic)
            result = report
        elif name == "get_session_summary":
            result = json.dumps(session_memory.get_summary(), indent=2)
        elif name == "add_user_query":
            query = arguments["query"]
            session_memory.user_queries.append(query)
            result = f"Added query: {query}"
        elif name == "search_level3":
            keyword = arguments["keyword"].lower()
            matches = []
            for key, content in session_memory.generated_level3.items():
                if keyword in content.lower():
                    matches.append(key)
            if matches:
                result = f"Found in Level 3 articles:\n- " + "\n- ".join(matches[:10])
            else:
                result = f"No Level 3 articles contain '{keyword}'."
        else:
            result = f"Unknown tool: {name}"
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="wiki-agent-server",
                server_version="2.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())